"""
Data Model Designer API Router

API endpoints for the Data Model Designer feature.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.dependencies import get_db, get_current_user
from app.schemas.data_model import (
    EntityDefinitionCreate,
    EntityDefinitionUpdate,
    EntityDefinitionResponse,
    FieldDefinitionCreate,
    FieldDefinitionUpdate,
    FieldDefinitionResponse,
    RelationshipDefinitionCreate,
    RelationshipDefinitionResponse,
)
from app.services.data_model_service import DataModelService


router = APIRouter(prefix="/api/v1/data-model", tags=["Data Model Designer"])


# ==================== Entity Endpoints ====================

@router.post("/entities", response_model=EntityDefinitionResponse)
async def create_entity(
    entity: EntityDefinitionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new entity definition"""
    service = DataModelService(db, current_user)
    return await service.create_entity(entity)


@router.get("/entities", response_model=List[EntityDefinitionResponse])
async def list_entities(
    category: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all entity definitions"""
    service = DataModelService(db, current_user)
    return await service.list_entities(category, entity_type, status)


@router.get("/entities/{entity_id}", response_model=EntityDefinitionResponse)
async def get_entity(
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get entity definition by ID"""
    service = DataModelService(db, current_user)
    return await service.get_entity(entity_id)


@router.put("/entities/{entity_id}", response_model=EntityDefinitionResponse)
async def update_entity(
    entity_id: UUID,
    entity: EntityDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update entity definition"""
    service = DataModelService(db, current_user)
    return await service.update_entity(entity_id, entity)


@router.delete("/entities/{entity_id}")
async def delete_entity(
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete entity definition (soft delete)"""
    service = DataModelService(db, current_user)
    return await service.delete_entity(entity_id)


# ==================== Field Endpoints ====================

@router.post("/entities/{entity_id}/fields", response_model=FieldDefinitionResponse)
async def create_field(
    entity_id: UUID,
    field: FieldDefinitionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Add a field to an entity"""
    service = DataModelService(db, current_user)
    return await service.create_field(entity_id, field)


@router.get("/entities/{entity_id}/fields", response_model=List[FieldDefinitionResponse])
async def list_fields(
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all fields for an entity"""
    service = DataModelService(db, current_user)
    return await service.list_fields(entity_id)


@router.put("/entities/{entity_id}/fields/{field_id}", response_model=FieldDefinitionResponse)
async def update_field(
    entity_id: UUID,
    field_id: UUID,
    field: FieldDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a field definition"""
    service = DataModelService(db, current_user)
    return await service.update_field(entity_id, field_id, field)


@router.delete("/entities/{entity_id}/fields/{field_id}")
async def delete_field(
    entity_id: UUID,
    field_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a field definition"""
    service = DataModelService(db, current_user)
    return await service.delete_field(entity_id, field_id)


# ==================== Relationship Endpoints ====================

@router.post("/relationships", response_model=RelationshipDefinitionResponse)
async def create_relationship(
    relationship: RelationshipDefinitionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a relationship between entities"""
    service = DataModelService(db, current_user)
    return await service.create_relationship(relationship)


@router.get("/relationships", response_model=List[RelationshipDefinitionResponse])
async def list_relationships(
    entity_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List relationships"""
    service = DataModelService(db, current_user)
    return await service.list_relationships(entity_id)
