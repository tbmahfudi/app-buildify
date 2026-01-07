"""
Template Package Service

Handles import/export of template packages for distribution.
"""

import json
import zipfile
import io
from typing import List, Optional, BinaryIO
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile

from app.models.template_category import TemplatePackage
from app.models.data_model import EntityDefinition, FieldDefinition
from app.models.workflow import WorkflowDefinition, WorkflowState, WorkflowTransition
from app.models.automation import AutomationRule
from app.models.lookup import LookupConfiguration
from app.models.base import generate_uuid


class TemplatePackageService:
    """Service for packaging and distributing templates."""

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user

    # ==================== Export Methods ====================

    async def export_entity_template(
        self,
        entity_id: UUID,
        include_fields: bool = True
    ) -> dict:
        """Export an entity template as JSON."""
        entity = self.db.query(EntityDefinition).filter(
            EntityDefinition.id == entity_id
        ).first()

        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")

        # Convert entity to exportable format
        export_data = {
            "type": "entity",
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "exported_by": str(self.current_user.id),
            "template": {
                "name": entity.name,
                "label": entity.label,
                "plural_label": entity.plural_label,
                "description": entity.description,
                "icon": entity.icon,
                "entity_type": entity.entity_type,
                "category": entity.category,
                "is_audited": entity.is_audited,
                "is_versioned": entity.is_versioned,
                "supports_soft_delete": entity.supports_soft_delete,
                "supports_attachments": entity.supports_attachments,
                "supports_comments": entity.supports_comments,
                "primary_field": entity.primary_field,
                "default_sort_field": entity.default_sort_field,
                "default_sort_order": entity.default_sort_order,
                "records_per_page": entity.records_per_page,
                "meta_data": entity.meta_data
            }
        }

        if include_fields:
            fields = self.db.query(FieldDefinition).filter(
                FieldDefinition.entity_id == entity_id,
                FieldDefinition.is_deleted == False
            ).order_by(FieldDefinition.display_order).all()

            export_data["fields"] = []
            for field in fields:
                export_data["fields"].append({
                    "name": field.name,
                    "label": field.label,
                    "description": field.description,
                    "help_text": field.help_text,
                    "field_type": field.field_type,
                    "data_type": field.data_type,
                    "is_required": field.is_required,
                    "is_unique": field.is_unique,
                    "is_indexed": field.is_indexed,
                    "is_nullable": field.is_nullable,
                    "max_length": field.max_length,
                    "min_length": field.min_length,
                    "max_value": str(field.max_value) if field.max_value else None,
                    "min_value": str(field.min_value) if field.min_value else None,
                    "decimal_places": field.decimal_places,
                    "default_value": field.default_value,
                    "default_expression": field.default_expression,
                    "validation_rules": field.validation_rules,
                    "allowed_values": field.allowed_values,
                    "display_order": field.display_order,
                    "is_readonly": field.is_readonly,
                    "is_calculated": field.is_calculated,
                    "calculation_formula": field.calculation_formula,
                    "input_type": field.input_type,
                    "placeholder": field.placeholder,
                    "prefix": field.prefix,
                    "suffix": field.suffix,
                    "meta_data": field.meta_data
                })

        return export_data

    async def create_package(
        self,
        name: str,
        description: str,
        template_ids: List[dict],  # [{"type": "entity", "id": "..."}]
        category_code: str = None,
        version: str = "1.0.0",
        author: str = None,
        license: str = "MIT"
    ) -> TemplatePackage:
        """Create a template package from multiple templates."""
        # Only superusers can create packages
        if not self.current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers can create template packages"
            )

        # Export all templates
        package_templates = []
        dependencies = []

        for template_ref in template_ids:
            template_type = template_ref["type"]
            template_id = UUID(template_ref["id"])

            if template_type == "entity":
                template_data = await self.export_entity_template(template_id)
                package_templates.append(template_data)

            # Add logic for other template types...

        # Create package
        code = name.lower().replace(" ", "_")
        existing = self.db.query(TemplatePackage).filter(
            TemplatePackage.code == code
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Package with code '{code}' already exists"
            )

        package = TemplatePackage(
            id=str(generate_uuid()),
            code=code,
            name=name,
            description=description,
            version=version,
            author=author or f"{self.current_user.email}",
            license=license,
            package_data=json.dumps({
                "templates": package_templates,
                "metadata": {
                    "template_count": len(package_templates),
                    "created_at": datetime.utcnow().isoformat()
                }
            }, indent=2),
            dependencies=json.dumps(dependencies),
            is_published=True,
            is_verified=True,
            created_by=self.current_user.id
        )

        self.db.add(package)
        self.db.commit()
        self.db.refresh(package)

        return package

    async def export_package_as_zip(self, package_id: UUID) -> bytes:
        """Export a package as a ZIP file."""
        package = self.db.query(TemplatePackage).filter(
            TemplatePackage.id == package_id
        ).first()

        if not package:
            raise HTTPException(status_code=404, detail="Package not found")

        # Create ZIP file in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add package metadata
            metadata = {
                "name": package.name,
                "code": package.code,
                "version": package.version,
                "description": package.description,
                "author": package.author,
                "license": package.license,
                "created_at": package.created_at.isoformat() if package.created_at else None
            }
            zip_file.writestr("package.json", json.dumps(metadata, indent=2))

            # Add templates
            package_data = json.loads(package.package_data)
            zip_file.writestr("templates.json", json.dumps(package_data, indent=2))

            # Add README
            readme = f"""# {package.name}

{package.description}

## Version
{package.version}

## Author
{package.author}

## License
{package.license}

## Installation
1. Extract this ZIP file
2. Import through the platform's template import interface
3. Review and customize templates as needed

## Templates Included
{len(package_data.get('templates', []))} template(s)
"""
            zip_file.writestr("README.md", readme)

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    # ==================== Import Methods ====================

    async def import_entity_template(
        self,
        template_data: dict,
        target_tenant_id: UUID = None,
        make_platform_level: bool = False
    ) -> EntityDefinition:
        """Import an entity template from JSON."""
        # Validate template data
        if template_data.get("type") != "entity":
            raise HTTPException(
                status_code=400,
                detail="Invalid template type"
            )

        template = template_data["template"]

        # Check for name conflicts
        existing = self.db.query(EntityDefinition).filter(
            EntityDefinition.name == template["name"],
            EntityDefinition.is_deleted == False
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Entity '{template['name']}' already exists. Please rename or delete the existing entity."
            )

        # Determine tenant_id
        if make_platform_level:
            if not self.current_user.is_superuser:
                raise HTTPException(
                    status_code=403,
                    detail="Only superusers can import as platform-level templates"
                )
            tenant_id = None
        else:
            tenant_id = target_tenant_id or self.current_user.tenant_id

        # Create entity
        entity = EntityDefinition(
            id=str(generate_uuid()),
            tenant_id=tenant_id,
            table_name=f"{template['name']}s",  # Generate table name
            schema_name="public",
            status="draft",
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
            **{k: v for k, v in template.items() if k in [
                "name", "label", "plural_label", "description", "icon",
                "entity_type", "category", "is_audited", "is_versioned",
                "supports_soft_delete", "supports_attachments", "supports_comments",
                "primary_field", "default_sort_field", "default_sort_order",
                "records_per_page", "meta_data"
            ]}
        )

        self.db.add(entity)
        self.db.flush()

        # Import fields
        if "fields" in template_data:
            for field_data in template_data["fields"]:
                field = FieldDefinition(
                    id=str(generate_uuid()),
                    entity_id=entity.id,
                    tenant_id=tenant_id,
                    created_by=self.current_user.id,
                    updated_by=self.current_user.id,
                    **{k: v for k, v in field_data.items() if k in [
                        "name", "label", "description", "help_text", "field_type",
                        "data_type", "is_required", "is_unique", "is_indexed",
                        "is_nullable", "max_length", "min_length", "max_value",
                        "min_value", "decimal_places", "default_value",
                        "default_expression", "validation_rules", "allowed_values",
                        "display_order", "is_readonly", "is_calculated",
                        "calculation_formula", "input_type", "placeholder",
                        "prefix", "suffix", "meta_data"
                    ]}
                )
                self.db.add(field)

        self.db.commit()
        self.db.refresh(entity)

        return entity

    async def import_package(
        self,
        package_data: dict,
        target_tenant_id: UUID = None,
        make_platform_level: bool = False
    ) -> dict:
        """Import a complete template package."""
        imported_templates = []
        errors = []

        templates = package_data.get("templates", [])

        for template_data in templates:
            try:
                if template_data["type"] == "entity":
                    entity = await self.import_entity_template(
                        template_data,
                        target_tenant_id,
                        make_platform_level
                    )
                    imported_templates.append({
                        "type": "entity",
                        "id": str(entity.id),
                        "name": entity.name
                    })
                # Add logic for other template types...

            except Exception as e:
                errors.append({
                    "template": template_data.get("template", {}).get("name", "Unknown"),
                    "error": str(e)
                })

        return {
            "imported": len(imported_templates),
            "failed": len(errors),
            "templates": imported_templates,
            "errors": errors
        }

    async def import_from_zip(
        self,
        zip_file: UploadFile,
        target_tenant_id: UUID = None,
        make_platform_level: bool = False
    ) -> dict:
        """Import templates from a ZIP file."""
        try:
            # Read ZIP file
            zip_content = await zip_file.read()
            zip_buffer = io.BytesIO(zip_content)

            with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
                # Read templates.json
                templates_json = zip_ref.read("templates.json").decode('utf-8')
                package_data = json.loads(templates_json)

                # Import package
                result = await self.import_package(
                    package_data,
                    target_tenant_id,
                    make_platform_level
                )

                return result

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to import package: {str(e)}"
            )

    # ==================== List Methods ====================

    async def list_packages(
        self,
        category_id: UUID = None,
        is_verified: bool = None
    ) -> List[TemplatePackage]:
        """List available template packages."""
        query = self.db.query(TemplatePackage).filter(
            TemplatePackage.is_active == True,
            TemplatePackage.is_published == True
        )

        if category_id:
            query = query.filter(TemplatePackage.category_id == category_id)
        if is_verified is not None:
            query = query.filter(TemplatePackage.is_verified == is_verified)

        return query.all()
