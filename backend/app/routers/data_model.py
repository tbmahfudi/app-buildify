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
    DatabaseObjectsResponse,
    IntrospectRequest,
    IntrospectedEntityDefinition,
    BatchIntrospectRequest,
    BatchIntrospectResponse,
    MigrationPreviewResponse,
    PublishEntityRequest,
    MigrationResponse,
    MigrationListResponse,
    RollbackResponse,
)
from app.services.data_model_service import DataModelService
from app.services.schema_introspector import SchemaIntrospector


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


@router.post("/entities/{entity_id}/clone", response_model=EntityDefinitionResponse)
async def clone_entity(
    entity_id: UUID,
    new_name: Optional[str] = Query(None, description="Name for the cloned entity"),
    new_label: Optional[str] = Query(None, description="Label for the cloned entity"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Clone a platform-level entity to a tenant-specific version"""
    service = DataModelService(db, current_user)
    return await service.clone_entity(entity_id, new_name, new_label)


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
    include_deleted: bool = Query(False, description="Include soft-deleted fields"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all fields for an entity"""
    service = DataModelService(db, current_user)
    return await service.list_fields(entity_id, include_deleted=include_deleted)


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


@router.post("/entities/{entity_id}/fields/{field_id}/restore", response_model=FieldDefinitionResponse)
async def restore_field(
    entity_id: UUID,
    field_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Restore a soft-deleted field"""
    service = DataModelService(db, current_user)
    return await service.restore_field(entity_id, field_id)


@router.get("/entities/{entity_id}/fields/deleted")
async def list_deleted_fields(
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all soft-deleted fields for an entity"""
    service = DataModelService(db, current_user)
    return await service.list_deleted_fields(entity_id)


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


@router.delete("/relationships/{relationship_id}")
async def delete_relationship(
    relationship_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a relationship"""
    service = DataModelService(db, current_user)
    return await service.delete_relationship(relationship_id)


# ==================== Schema Introspection Endpoints ====================

@router.get("/introspect/objects", response_model=DatabaseObjectsResponse)
async def list_database_objects(
    schema: str = Query('public', description="Database schema to introspect"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List all tables and views available for introspection

    Returns all tables, views, and materialized views in the specified schema.
    System tables and views are automatically filtered out.
    """
    introspector = SchemaIntrospector(db)
    objects = await introspector.list_database_objects(schema)
    return objects


@router.post("/introspect/generate", response_model=IntrospectedEntityDefinition)
async def generate_entity_from_db_object(
    request: IntrospectRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Introspect a database object and generate EntityDefinition

    This endpoint analyzes an existing database table or view and automatically
    generates a complete EntityDefinition with fields, relationships, and indexes.

    If auto_save is True, the entity will be immediately saved to entity_definitions.
    Otherwise, the entity structure is returned for review.
    """
    introspector = SchemaIntrospector(db)

    # Introspect the object
    entity_data = await introspector.introspect_object(
        request.object_name,
        request.object_type,
        request.schema
    )

    # Optionally auto-save
    if request.auto_save:
        service = DataModelService(db, current_user)
        entity = await service.create_entity_from_introspection(entity_data)
        return entity

    # Return for review
    return entity_data


@router.post("/introspect/batch-generate", response_model=BatchIntrospectResponse)
async def batch_generate_entities(
    request: BatchIntrospectRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Generate EntityDefinitions for multiple database objects

    This endpoint processes multiple tables/views in a single request.
    For large batches, processing happens synchronously but returns immediately
    with a status message.

    If auto_save is True, all entities will be saved to entity_definitions.
    """
    introspector = SchemaIntrospector(db)
    service = DataModelService(db, current_user)

    created_count = 0
    failed_count = 0
    errors = []

    for obj in request.objects:
        try:
            # Introspect the object
            entity_data = await introspector.introspect_object(
                obj.name,
                obj.type,
                request.schema
            )

            # Save if requested
            if request.auto_save:
                await service.create_entity_from_introspection(entity_data)
                created_count += 1

        except Exception as e:
            failed_count += 1
            errors.append(f"{obj.name}: {str(e)}")

    return {
        "total": len(request.objects),
        "queued": created_count,
        "message": f"Processed {created_count} objects successfully, {failed_count} failed",
        "status": "completed" if failed_count == 0 else "partial"
    }


# ==================== Migration Endpoints ====================

@router.get("/entities/{entity_id}/preview-migration", response_model=MigrationPreviewResponse)
async def preview_migration(
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Preview schema changes before publishing

    Returns the SQL that will be executed and an estimated impact analysis.
    This allows users to review changes before applying them to the database.
    """
    service = DataModelService(db, current_user)
    return await service.preview_migration(entity_id)


@router.post("/entities/{entity_id}/generate-migration", response_model=MigrationResponse)
async def generate_migration(
    entity_id: UUID,
    request: PublishEntityRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Generate and save migration without executing it

    Creates a migration record with 'pending' status that can be reviewed
    and executed later. This allows users to generate multiple migrations
    and then run them in a specific order.
    """
    service = DataModelService(db, current_user)
    return await service.generate_migration(entity_id, request.commit_message)


@router.post("/migrations/{migration_id}/execute", response_model=MigrationResponse)
async def execute_migration(
    migration_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Execute a pending migration

    Runs the UP script of a migration that was previously generated.
    The migration must be in 'pending' status. After successful execution,
    the entity will be marked as 'published' and the migration status will
    be updated to 'completed'.
    """
    service = DataModelService(db, current_user)
    return await service.execute_migration(migration_id)


@router.post("/entities/{entity_id}/publish", response_model=MigrationResponse)
async def publish_entity(
    entity_id: UUID,
    request: PublishEntityRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Publish entity and execute migration

    Generates and executes SQL migration to create or alter the database table.
    The entity status will be updated to 'published' and a migration record
    will be created for history tracking.
    """
    service = DataModelService(db, current_user)
    return await service.publish_entity(entity_id, request.commit_message)


@router.get("/entities/{entity_id}/migrations", response_model=MigrationListResponse)
async def list_migrations(
    entity_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List migration history for an entity

    Returns all migrations that have been executed for this entity,
    including their status, SQL scripts, and execution details.
    """
    service = DataModelService(db, current_user)
    return await service.list_migrations(entity_id)


@router.post("/migrations/{migration_id}/rollback", response_model=RollbackResponse)
async def rollback_migration(
    migration_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Rollback a migration

    Executes the down script of a migration to revert changes.
    Only completed migrations with down scripts can be rolled back.
    """
    service = DataModelService(db, current_user)
    return await service.rollback_migration(migration_id)
