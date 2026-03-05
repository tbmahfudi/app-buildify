import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.audit import create_audit_log
from app.core.dependencies import get_current_user, get_db, has_permission
from app.models.data_model import EntityDefinition
from app.models.user import User
from app.schemas.metadata import (
    EntityListResponse,
    EntityMetadataCreate,
    EntityMetadataResponse,
    EntityMetadataUpdate,
    FormConfig,
    TableConfig,
)
from app.services.metadata_sync_service import MetadataSyncService

router = APIRouter(prefix="/api/v1/metadata", tags=["metadata"])
logger = logging.getLogger(__name__)


def _build_response(entity: EntityDefinition) -> EntityMetadataResponse:
    """Build EntityMetadataResponse from an EntityDefinition row."""
    table_config = entity.table_config or {}
    form_config = entity.form_config or {}
    permissions = entity.permissions or {}

    return EntityMetadataResponse(
        id=str(entity.id),
        entity_name=entity.name,
        display_name=entity.label,
        description=entity.description,
        icon=entity.icon,
        table=TableConfig(**table_config),
        form=FormConfig(**form_config),
        permissions=permissions,
        version=entity.version,
        is_active=entity.is_active,
        is_system=(entity.entity_type == 'system'),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        created_by=str(entity.created_by) if entity.created_by else None,
        updated_by=str(entity.updated_by) if entity.updated_by else None,
    )


@router.get("/entities", response_model=EntityListResponse)
def list_entities(
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("metadata:read:tenant"))
):
    """
    List all available entities.

    Requires permission: metadata:read:tenant
    """
    entities = db.query(EntityDefinition).filter(
        EntityDefinition.status == 'published',
        EntityDefinition.is_active == True,
        EntityDefinition.is_deleted == False,
        EntityDefinition.table_config.isnot(None),
    ).all()

    return EntityListResponse(
        entities=[e.name for e in entities],
        total=len(entities)
    )


@router.get("/entities/{entity_name}", response_model=EntityMetadataResponse)
def get_entity_metadata(
    entity_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("metadata:read:tenant"))
):
    """
    Get metadata for a specific entity.

    Requires permission: metadata:read:tenant
    """
    entity = db.query(EntityDefinition).filter(
        EntityDefinition.name == entity_name,
        EntityDefinition.is_active == True,
        EntityDefinition.is_deleted == False,
    ).first()

    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' not found")

    return _build_response(entity)


@router.post("/entities", response_model=EntityMetadataResponse, status_code=status.HTTP_201_CREATED)
def create_entity_metadata(
    payload: EntityMetadataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("metadata:create:tenant"))
):
    """
    Seed UI config for an existing published entity.

    Looks up the EntityDefinition by entity_name and stores the provided
    table_config, form_config, and permissions on it.

    Requires permission: metadata:create:tenant
    """
    entity = db.query(EntityDefinition).filter(
        EntityDefinition.name == payload.entity_name,
        EntityDefinition.is_deleted == False,
    ).first()

    if not entity:
        raise HTTPException(
            status_code=404,
            detail=f"Entity definition '{payload.entity_name}' not found"
        )

    if entity.table_config is not None:
        raise HTTPException(
            status_code=400,
            detail=f"UI config for entity '{payload.entity_name}' already exists"
        )

    entity.table_config = payload.table_config.dict()
    entity.form_config = payload.form_config.dict()
    entity.permissions = payload.permissions or {}

    db.commit()
    db.refresh(entity)

    create_audit_log(
        db=db,
        action="CREATE_METADATA",
        user=current_user,
        entity_type="entity_definitions",
        entity_id=str(entity.id),
        context_info={"entity_name": payload.entity_name},
        status="success"
    )

    return _build_response(entity)


@router.put("/entities/{entity_name}", response_model=EntityMetadataResponse)
def update_entity_metadata(
    entity_name: str,
    updates: EntityMetadataUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("metadata:update:tenant"))
):
    """
    Update entity UI configuration.

    Requires permission: metadata:update:tenant
    """
    entity = db.query(EntityDefinition).filter(
        EntityDefinition.name == entity_name,
        EntityDefinition.is_deleted == False,
    ).first()

    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' not found")

    if entity.entity_type == 'system':
        raise HTTPException(status_code=403, detail="Cannot modify system entity")

    if updates.display_name is not None:
        entity.label = updates.display_name
    if updates.description is not None:
        entity.description = updates.description
    if updates.icon is not None:
        entity.icon = updates.icon
    if updates.table_config is not None:
        entity.table_config = updates.table_config.dict()
    if updates.form_config is not None:
        entity.form_config = updates.form_config.dict()
    if updates.permissions is not None:
        entity.permissions = updates.permissions
    if updates.is_active is not None:
        entity.is_active = updates.is_active

    entity.version = (entity.version or 1) + 1
    entity.updated_by = str(current_user.id)

    db.commit()
    db.refresh(entity)

    create_audit_log(
        db=db,
        action="UPDATE_METADATA",
        user=current_user,
        entity_type="entity_definitions",
        entity_id=str(entity.id),
        context_info={"entity_name": entity_name},
        status="success"
    )

    return _build_response(entity)


@router.delete("/entities/{entity_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entity_metadata(
    entity_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("metadata:delete:tenant"))
):
    """
    Deactivate an entity (soft delete).

    Requires permission: metadata:delete:tenant
    """
    entity = db.query(EntityDefinition).filter(
        EntityDefinition.name == entity_name,
        EntityDefinition.is_deleted == False,
    ).first()

    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' not found")

    if entity.entity_type == 'system':
        raise HTTPException(status_code=403, detail="Cannot delete system entity")

    entity.is_active = False
    entity.updated_by = str(current_user.id)

    db.commit()

    create_audit_log(
        db=db,
        action="DELETE_METADATA",
        user=current_user,
        entity_type="entity_definitions",
        entity_id=str(entity.id),
        context_info={"entity_name": entity_name},
        status="success"
    )

    return None


@router.post("/entities/{entity_name}/regenerate", response_model=EntityMetadataResponse)
def regenerate_entity_metadata(
    entity_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("metadata:update:tenant"))
):
    """
    Force-regenerate UI config for a published entity from scratch.

    Drops the existing stored config and rebuilds entirely from the entity
    definition and its field definitions. Use this to pick up code-level fixes
    (e.g. updated field-type mappings) without re-publishing the entity.

    Requires permission: metadata:update:tenant
    """
    entity = db.query(EntityDefinition).filter(
        EntityDefinition.name == entity_name,
        EntityDefinition.status == 'published',
        EntityDefinition.is_deleted == False,
    ).first()

    if not entity:
        raise HTTPException(
            status_code=404,
            detail=f"No published entity definition found for '{entity_name}'"
        )

    # Clear stored config so auto_generate_metadata starts fresh
    entity.table_config = None
    entity.form_config = None
    db.commit()

    sync_service = MetadataSyncService(db)
    entity = sync_service.auto_generate_metadata(entity, str(current_user.id))

    create_audit_log(
        db=db,
        action="REGENERATE_METADATA",
        user=current_user,
        entity_type="entity_definitions",
        entity_id=str(entity.id),
        context_info={"entity_name": entity_name},
        status="success"
    )

    return _build_response(entity)
