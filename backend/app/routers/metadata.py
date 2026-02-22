import json
import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.audit import create_audit_log
from app.core.dependencies import get_current_user, get_db, has_permission
from app.models.data_model import EntityDefinition
from app.models.metadata import EntityMetadata
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

@router.get("/entities", response_model=EntityListResponse)
def list_entities(
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("metadata:read:tenant"))
):
    """
    List all available entities.

    Requires permission: metadata:read:tenant
    """
    entities = db.query(EntityMetadata).filter(
        EntityMetadata.is_active == True
    ).all()
    
    return EntityListResponse(
        entities=[e.entity_name for e in entities],
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
    metadata = db.query(EntityMetadata).filter(
        EntityMetadata.entity_name == entity_name,
        EntityMetadata.is_active == True
    ).first()
    
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' not found")
    
    # Parse JSON fields
    table_config = json.loads(metadata.table_config) if metadata.table_config else {}
    form_config = json.loads(metadata.form_config) if metadata.form_config else {}
    permissions = json.loads(metadata.permissions) if metadata.permissions else {}

    return EntityMetadataResponse(
        id=str(metadata.id),
        entity_name=metadata.entity_name,
        display_name=metadata.display_name,
        description=metadata.description,
        icon=metadata.icon,
        table=TableConfig(**table_config),
        form=FormConfig(**form_config),
        permissions=permissions,
        version=metadata.version,
        is_active=metadata.is_active,
        is_system=metadata.is_system,
        created_at=metadata.created_at,
        updated_at=metadata.updated_at,
        created_by=str(metadata.created_by) if metadata.created_by else None,
        updated_by=str(metadata.updated_by) if metadata.updated_by else None
    )

@router.post("/entities", response_model=EntityMetadataResponse, status_code=status.HTTP_201_CREATED)
def create_entity_metadata(
    entity: EntityMetadataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("metadata:create:tenant"))
):
    """
    Create metadata for a new entity.

    Requires permission: metadata:create:tenant
    """
    
    # Check if entity already exists
    existing = db.query(EntityMetadata).filter(
        EntityMetadata.entity_name == entity.entity_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Entity '{entity.entity_name}' already exists"
        )
    
    # Create metadata
    metadata = EntityMetadata(
        id=str(uuid.uuid4()),
        entity_name=entity.entity_name,
        display_name=entity.display_name,
        description=entity.description,
        icon=entity.icon,
        table_config=json.dumps(entity.table_config.dict()),
        form_config=json.dumps(entity.form_config.dict()),
        permissions=json.dumps(entity.permissions) if entity.permissions else None,
        version=1,
        is_active=True,
        is_system=False,
        created_by=str(current_user.id)
    )
    
    db.add(metadata)
    db.commit()
    db.refresh(metadata)
    
    # Audit
    create_audit_log(
        db=db,
        action="CREATE_METADATA",
        user=current_user,
        entity_type="entity_metadata",
        entity_id=str(metadata.id),
        context_info={"entity_name": entity.entity_name},
        status="success"
    )

    return EntityMetadataResponse(
        id=str(metadata.id),
        entity_name=metadata.entity_name,
        display_name=metadata.display_name,
        description=metadata.description,
        icon=metadata.icon,
        table=entity.table_config,
        form=entity.form_config,
        permissions=entity.permissions or {},
        version=metadata.version,
        is_active=metadata.is_active,
        is_system=metadata.is_system,
        created_at=metadata.created_at,
        updated_at=metadata.updated_at,
        created_by=str(metadata.created_by) if metadata.created_by else None,
        updated_by=str(metadata.updated_by) if metadata.updated_by else None
    )

@router.put("/entities/{entity_name}", response_model=EntityMetadataResponse)
def update_entity_metadata(
    entity_name: str,
    updates: EntityMetadataUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("metadata:update:tenant"))
):
    """
    Update entity metadata.

    Requires permission: metadata:update:tenant
    """
    
    metadata = db.query(EntityMetadata).filter(
        EntityMetadata.entity_name == entity_name
    ).first()
    
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' not found")
    
    if metadata.is_system:
        raise HTTPException(status_code=403, detail="Cannot modify system entity")
    
    # Update fields
    if updates.display_name is not None:
        metadata.display_name = updates.display_name
    if updates.description is not None:
        metadata.description = updates.description
    if updates.icon is not None:
        metadata.icon = updates.icon
    if updates.table_config is not None:
        metadata.table_config = json.dumps(updates.table_config.dict())
    if updates.form_config is not None:
        metadata.form_config = json.dumps(updates.form_config.dict())
    if updates.permissions is not None:
        metadata.permissions = json.dumps(updates.permissions)
    
    metadata.version += 1
    metadata.updated_by = str(current_user.id)
    
    db.commit()
    db.refresh(metadata)
    
    # Audit
    create_audit_log(
        db=db,
        action="UPDATE_METADATA",
        user=current_user,
        entity_type="entity_metadata",
        entity_id=str(metadata.id),
        context_info={"entity_name": entity_name},
        status="success"
    )
    
    # Parse for response
    table_config = json.loads(metadata.table_config) if metadata.table_config else {}
    form_config = json.loads(metadata.form_config) if metadata.form_config else {}
    permissions = json.loads(metadata.permissions) if metadata.permissions else {}

    return EntityMetadataResponse(
        id=str(metadata.id),
        entity_name=metadata.entity_name,
        display_name=metadata.display_name,
        description=metadata.description,
        icon=metadata.icon,
        table=TableConfig(**table_config),
        form=FormConfig(**form_config),
        permissions=permissions,
        version=metadata.version,
        is_active=metadata.is_active,
        is_system=metadata.is_system,
        created_at=metadata.created_at,
        updated_at=metadata.updated_at,
        created_by=str(metadata.created_by) if metadata.created_by else None,
        updated_by=str(metadata.updated_by) if metadata.updated_by else None
    )

@router.delete("/entities/{entity_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entity_metadata(
    entity_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("metadata:delete:tenant"))
):
    """
    Soft delete entity metadata.

    Requires permission: metadata:delete:tenant
    """
    
    metadata = db.query(EntityMetadata).filter(
        EntityMetadata.entity_name == entity_name
    ).first()
    
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' not found")
    
    if metadata.is_system:
        raise HTTPException(status_code=403, detail="Cannot delete system entity")
    
    # Soft delete
    metadata.is_active = False
    metadata.updated_by = str(current_user.id)
    
    db.commit()
    
    # Audit
    create_audit_log(
        db=db,
        action="DELETE_METADATA",
        user=current_user,
        entity_type="entity_metadata",
        entity_id=str(metadata.id),
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
    Force-regenerate metadata for a published entity from scratch.

    Drops the existing stored metadata and rebuilds it entirely from the
    entity definition.  Use this to pick up code-level fixes (e.g. updated
    field-type mappings) without having to re-publish the entity through the
    Data Model Designer.

    Requires permission: metadata:update:tenant
    """
    # Find the published entity definition
    entity_def = db.query(EntityDefinition).filter(
        EntityDefinition.name == entity_name,
        EntityDefinition.status == "published",
        EntityDefinition.is_deleted == False,
    ).first()

    if not entity_def:
        raise HTTPException(
            status_code=404,
            detail=f"No published entity definition found for '{entity_name}'"
        )

    # Hard-delete any existing metadata so auto_generate_metadata starts fresh
    existing = db.query(EntityMetadata).filter(
        EntityMetadata.entity_name == entity_name
    ).first()
    if existing:
        db.delete(existing)
        db.commit()

    # Regenerate
    sync_service = MetadataSyncService(db)
    metadata = sync_service.auto_generate_metadata(entity_def, str(current_user.id))

    # Audit
    create_audit_log(
        db=db,
        action="REGENERATE_METADATA",
        user=current_user,
        entity_type="entity_metadata",
        entity_id=str(metadata.id),
        context_info={"entity_name": entity_name},
        status="success"
    )

    table_config = json.loads(metadata.table_config) if metadata.table_config else {}
    form_config = json.loads(metadata.form_config) if metadata.form_config else {}

    return EntityMetadataResponse(
        id=str(metadata.id),
        entity_name=metadata.entity_name,
        display_name=metadata.display_name,
        description=metadata.description,
        icon=metadata.icon,
        table=TableConfig(**table_config),
        form=FormConfig(**form_config),
        permissions={},
        version=metadata.version,
        is_active=metadata.is_active,
        is_system=metadata.is_system,
        created_at=metadata.created_at,
        updated_at=metadata.updated_at,
        created_by=str(metadata.created_by) if metadata.created_by else None,
        updated_by=str(metadata.updated_by) if metadata.updated_by else None
    )