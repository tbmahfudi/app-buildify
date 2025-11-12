from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import json
import logging

from app.core.dependencies import get_db, get_current_user, has_role
from app.models.user import User
from app.models.metadata import EntityMetadata
from app.schemas.metadata import (
    EntityMetadataResponse, EntityMetadataCreate, EntityMetadataUpdate,
    EntityListResponse, TableConfig, FormConfig
)
from app.core.audit import create_audit_log

router = APIRouter(prefix="/metadata", tags=["metadata"])
logger = logging.getLogger(__name__)

@router.get("/entities", response_model=EntityListResponse)
def list_entities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all available entities"""
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
    current_user: User = Depends(get_current_user)
):
    """Get metadata for a specific entity"""
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
    current_user: User = Depends(has_role("admin"))
):
    """Create metadata for a new entity (admin only)"""
    
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
    current_user: User = Depends(has_role("admin"))
):
    """Update entity metadata (admin only)"""
    
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
    current_user: User = Depends(has_role("admin"))
):
    """Soft delete entity metadata (admin only)"""
    
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