"""
Template Version Service

Handles versioning, history tracking, and rollback for platform templates.
"""

import json
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.template_category import TemplateVersion
from app.models.data_model import EntityDefinition, FieldDefinition
from app.models.workflow import WorkflowDefinition, WorkflowState, WorkflowTransition
from app.models.automation import AutomationRule
from app.models.lookup import LookupConfiguration
from app.models.base import generate_uuid


class TemplateVersionService:
    """Service for managing template versions and history."""

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user

    # ==================== Version Methods ====================

    async def create_version(
        self,
        template_type: str,
        template_id: UUID,
        change_summary: str,
        change_type: str = "minor",
        changelog: str = None,
        version_name: str = None
    ):
        """Create a new version snapshot of a template."""
        # Only superusers can version platform templates
        if not self.current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers can create template versions"
            )

        # Get the template
        template_snapshot = await self._get_template_snapshot(template_type, template_id)

        # Get current version number
        latest_version = self.db.query(TemplateVersion).filter(
            TemplateVersion.template_type == template_type,
            TemplateVersion.template_id == template_id
        ).order_by(TemplateVersion.version_number.desc()).first()

        new_version_number = (latest_version.version_number + 1) if latest_version else 1

        # Mark all previous versions as not current
        self.db.query(TemplateVersion).filter(
            TemplateVersion.template_type == template_type,
            TemplateVersion.template_id == template_id,
            TemplateVersion.is_current == True
        ).update({"is_current": False})

        # Create new version
        version = TemplateVersion(
            id=str(generate_uuid()),
            template_type=template_type,
            template_id=str(template_id),
            version_number=new_version_number,
            version_name=version_name or f"v{new_version_number}.0",
            change_summary=change_summary,
            change_type=change_type,
            changelog=changelog,
            template_snapshot=json.dumps(template_snapshot, indent=2),
            is_current=True,
            is_published=True,
            published_at=datetime.utcnow(),
            created_by=self.current_user.id
        )

        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)

        return version

    async def list_versions(
        self,
        template_type: str,
        template_id: UUID
    ) -> List[TemplateVersion]:
        """List all versions of a template."""
        versions = self.db.query(TemplateVersion).filter(
            TemplateVersion.template_type == template_type,
            TemplateVersion.template_id == template_id
        ).order_by(TemplateVersion.version_number.desc()).all()

        return versions

    async def get_version(self, version_id: UUID) -> TemplateVersion:
        """Get a specific version by ID."""
        version = self.db.query(TemplateVersion).filter(
            TemplateVersion.id == version_id
        ).first()

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )

        return version

    async def rollback_to_version(
        self,
        template_type: str,
        template_id: UUID,
        version_number: int
    ):
        """Rollback a template to a previous version."""
        # Only superusers can rollback
        if not self.current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers can rollback templates"
            )

        # Get the version to rollback to
        version = self.db.query(TemplateVersion).filter(
            TemplateVersion.template_type == template_type,
            TemplateVersion.template_id == template_id,
            TemplateVersion.version_number == version_number
        ).first()

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version_number} not found"
            )

        # Restore the template from snapshot
        snapshot_data = json.loads(version.template_snapshot)
        await self._restore_template_snapshot(template_type, template_id, snapshot_data)

        # Create a new version entry for the rollback
        await self.create_version(
            template_type=template_type,
            template_id=template_id,
            change_summary=f"Rolled back to version {version_number}",
            change_type="rollback",
            changelog=f"Restored template state from version {version_number}"
        )

        return {"message": f"Rolled back to version {version_number}"}

    async def compare_versions(
        self,
        template_type: str,
        template_id: UUID,
        from_version: int,
        to_version: int
    ):
        """Compare two versions of a template."""
        # Get both versions
        from_ver = self.db.query(TemplateVersion).filter(
            TemplateVersion.template_type == template_type,
            TemplateVersion.template_id == template_id,
            TemplateVersion.version_number == from_version
        ).first()

        to_ver = self.db.query(TemplateVersion).filter(
            TemplateVersion.template_type == template_type,
            TemplateVersion.template_id == template_id,
            TemplateVersion.version_number == to_version
        ).first()

        if not from_ver or not to_ver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both versions not found"
            )

        # Compare snapshots
        from_snapshot = json.loads(from_ver.template_snapshot)
        to_snapshot = json.loads(to_ver.template_snapshot)

        changes = self._calculate_changes(from_snapshot, to_snapshot)

        return {
            "from_version": from_version,
            "to_version": to_version,
            "changes": changes,
            "from_summary": from_ver.change_summary,
            "to_summary": to_ver.change_summary
        }

    # ==================== Helper Methods ====================

    async def _get_template_snapshot(self, template_type: str, template_id: UUID) -> dict:
        """Get a complete snapshot of a template including all related data."""
        if template_type == "entity":
            entity = self.db.query(EntityDefinition).filter(
                EntityDefinition.id == template_id
            ).first()

            if not entity:
                raise HTTPException(status_code=404, detail="Entity not found")

            # Get fields
            fields = self.db.query(FieldDefinition).filter(
                FieldDefinition.entity_id == template_id,
                FieldDefinition.is_deleted == False
            ).all()

            return {
                "entity": self._model_to_dict(entity),
                "fields": [self._model_to_dict(f) for f in fields]
            }

        elif template_type == "workflow":
            workflow = self.db.query(WorkflowDefinition).filter(
                WorkflowDefinition.id == template_id
            ).first()

            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")

            states = self.db.query(WorkflowState).filter(
                WorkflowState.workflow_id == template_id,
                WorkflowState.is_deleted == False
            ).all()

            transitions = self.db.query(WorkflowTransition).filter(
                WorkflowTransition.workflow_id == template_id,
                WorkflowTransition.is_deleted == False
            ).all()

            return {
                "workflow": self._model_to_dict(workflow),
                "states": [self._model_to_dict(s) for s in states],
                "transitions": [self._model_to_dict(t) for t in transitions]
            }

        elif template_type == "automation":
            rule = self.db.query(AutomationRule).filter(
                AutomationRule.id == template_id
            ).first()

            if not rule:
                raise HTTPException(status_code=404, detail="Automation rule not found")

            return {
                "rule": self._model_to_dict(rule)
            }

        elif template_type == "lookup":
            lookup = self.db.query(LookupConfiguration).filter(
                LookupConfiguration.id == template_id
            ).first()

            if not lookup:
                raise HTTPException(status_code=404, detail="Lookup not found")

            return {
                "lookup": self._model_to_dict(lookup)
            }

        else:
            raise HTTPException(status_code=400, detail=f"Unknown template type: {template_type}")

    async def _restore_template_snapshot(self, template_type: str, template_id: UUID, snapshot: dict):
        """Restore a template from a snapshot."""
        # This is a simplified version - in production you'd want more sophisticated merge logic
        if template_type == "entity":
            entity = self.db.query(EntityDefinition).filter(
                EntityDefinition.id == template_id
            ).first()

            if entity:
                # Update entity fields
                for key, value in snapshot["entity"].items():
                    if hasattr(entity, key) and key not in ["id", "created_at", "created_by"]:
                        setattr(entity, key, value)

                entity.updated_by = self.current_user.id
                entity.updated_at = datetime.utcnow()

        # Add similar logic for other template types...
        self.db.commit()

    def _model_to_dict(self, model) -> dict:
        """Convert SQLAlchemy model to dictionary."""
        result = {}
        for column in model.__table__.columns:
            value = getattr(model, column.name)
            # Convert datetime and UUID to string
            if isinstance(value, (datetime, UUID)):
                value = str(value)
            result[column.name] = value
        return result

    def _calculate_changes(self, from_snapshot: dict, to_snapshot: dict) -> list:
        """Calculate differences between two snapshots."""
        changes = []

        # Simple field-by-field comparison
        for key in from_snapshot.keys():
            if key in to_snapshot:
                if from_snapshot[key] != to_snapshot[key]:
                    changes.append({
                        "type": "modified",
                        "field": key,
                        "from": from_snapshot[key],
                        "to": to_snapshot[key]
                    })
            else:
                changes.append({
                    "type": "removed",
                    "field": key,
                    "from": from_snapshot[key]
                })

        for key in to_snapshot.keys():
            if key not in from_snapshot:
                changes.append({
                    "type": "added",
                    "field": key,
                    "to": to_snapshot[key]
                })

        return changes
