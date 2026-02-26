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
    import logging
    _logger = logging.getLogger(__name__)

    service = DataModelService(db, current_user)
    updated_field = await service.update_field(entity_id, field_id, field)

    # Re-sync EntityMetadata so that changes (e.g. allowed_values) are reflected
    # in the stored form/table config used by the UI.
    try:
        from app.models.data_model import EntityDefinition
        from app.services.metadata_sync_service import MetadataSyncService
        entity_def = db.query(EntityDefinition).filter(
            EntityDefinition.id == entity_id,
            EntityDefinition.is_deleted == False,
        ).first()
        if entity_def and entity_def.status == "published":
            MetadataSyncService(db).auto_generate_metadata(
                entity_definition=entity_def,
                created_by=str(current_user.id),
            )
    except Exception as e:
        _logger.warning(f"Metadata re-sync after field update failed (non-fatal): {e}")

    return updated_field


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


@router.delete("/entities/{entity_id}/fields/{field_id}/permanent")
async def permanently_delete_field(
    entity_id: UUID,
    field_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Permanently delete a soft-deleted field from database"""
    service = DataModelService(db, current_user)
    return await service.permanently_delete_field(entity_id, field_id)


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


@router.post("/entities/regenerate-menus")
async def regenerate_entity_menus(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Regenerate menu items and metadata for all published entities.

    This is a repair endpoint that creates missing menu items and EntityMetadata
    for entities that were published but don't have corresponding entries.
    """
    from app.models.data_model import EntityDefinition
    from app.models.menu_item import MenuItem
    from app.models.metadata import EntityMetadata
    from app.services.menu_service import MenuService
    from app.services.metadata_sync_service import MetadataSyncService
    from sqlalchemy import or_
    import logging

    logger = logging.getLogger(__name__)

    # Get all published entities for current tenant
    published_entities = db.query(EntityDefinition).filter(
        EntityDefinition.status == 'published',
        or_(
            EntityDefinition.tenant_id == current_user.tenant_id,
            EntityDefinition.tenant_id == None
        )
    ).all()

    if not published_entities:
        return {"success": True, "message": "No published entities found", "created": 0}

    # Ensure parent menu exists
    parent_menu = MenuService.get_or_create_nocode_parent(
        db, current_user.tenant_id, str(current_user.id)
    )

    menu_created = 0
    menu_skipped = 0
    metadata_created = 0
    metadata_skipped = 0

    metadata_sync = MetadataSyncService(db)

    for entity in published_entities:
        # --- Create/update EntityMetadata ---
        try:
            existing_metadata = db.query(EntityMetadata).filter(
                EntityMetadata.entity_name == entity.name
            ).first()

            if existing_metadata:
                metadata_skipped += 1
            else:
                metadata_sync.auto_generate_metadata(
                    entity_definition=entity,
                    created_by=str(current_user.id)
                )
                metadata_created += 1
                logger.info(f"Created metadata for entity: {entity.name}")
        except Exception as e:
            logger.error(f"Failed to create metadata for {entity.name}: {str(e)}")

        # --- Create menu item ---
        menu_code = f'nocode_entity_{entity.name}'

        existing_menu = db.query(MenuItem).filter(MenuItem.code == menu_code).first()
        if existing_menu:
            menu_skipped += 1
            continue

        try:
            menu_data = {
                'code': menu_code,
                'title': entity.label or entity.name.replace('_', ' ').title(),
                'route': f'dynamic/{entity.name}/list',
                'icon': entity.icon or 'ph-duotone ph-database',
                'parent_id': parent_menu.id,
                'permission': None,
                'required_roles': [],
                'is_system': False,
                'is_active': True,
                'extra_data': {
                    'entity_id': str(entity.id),
                    'is_nocode': True
                }
            }

            MenuService.create_menu_item(db=db, user=current_user, menu_data=menu_data)
            menu_created += 1
            logger.info(f"Created menu item for entity: {entity.name}")
        except Exception as e:
            logger.error(f"Failed to create menu for {entity.name}: {str(e)}")

    return {
        "success": True,
        "message": f"Created {menu_created} menus, {metadata_created} metadata. Skipped {menu_skipped} menus, {metadata_skipped} metadata.",
        "menus_created": menu_created,
        "menus_skipped": menu_skipped,
        "metadata_created": metadata_created,
        "metadata_skipped": metadata_skipped,
        "parent_menu_id": str(parent_menu.id)
    }
