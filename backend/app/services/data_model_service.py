"""
Data Model Designer Service

Business logic for the Data Model Designer feature.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.data_model import (
    EntityDefinition,
    FieldDefinition,
    RelationshipDefinition,
    IndexDefinition,
    EntityMigration,
)
from app.models.base import generate_uuid
from app.schemas.data_model import (
    EntityDefinitionCreate,
    EntityDefinitionUpdate,
    FieldDefinitionCreate,
    FieldDefinitionUpdate,
    RelationshipDefinitionCreate,
    RelationshipDefinitionUpdate,
)


class DataModelService:
    """Service for managing data model definitions"""

    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user
        self.tenant_id = current_user.tenant_id

    # ==================== Entity Methods ====================

    async def create_entity(self, entity_data: EntityDefinitionCreate, is_platform_level: bool = False):
        """Create a new entity definition (tenant-specific or platform-level)"""
        from sqlalchemy import or_

        # Determine tenant_id: NULL for platform-level, current tenant otherwise
        target_tenant_id = None if is_platform_level else self.tenant_id

        # Only superusers can create platform-level entities
        if is_platform_level and not self.current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers can create platform-level entities"
            )

        # Check if entity name already exists at the target scope
        if is_platform_level:
            # Check platform-level entities only
            existing_filter = EntityDefinition.tenant_id == None
        else:
            # Check both tenant-level and platform-level (to avoid conflicts)
            existing_filter = or_(
                EntityDefinition.tenant_id == self.tenant_id,
                EntityDefinition.tenant_id == None
            )

        existing = self.db.query(EntityDefinition).filter(
            existing_filter,
            EntityDefinition.name == entity_data.name,
            EntityDefinition.is_deleted == False
        ).first()

        if existing:
            scope = "platform-level" if existing.tenant_id is None else "tenant"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Entity with name '{entity_data.name}' already exists at {scope} level"
            )

        # Create entity
        entity = EntityDefinition(
            **entity_data.model_dump(exclude={'fields'}),
            tenant_id=target_tenant_id,
            created_by=self.current_user.id,
            updated_by=self.current_user.id
        )

        self.db.add(entity)
        self.db.flush()

        # Create fields if provided
        if entity_data.fields:
            for field_data in entity_data.fields:
                field = FieldDefinition(
                    **field_data.model_dump(),
                    entity_id=entity.id,
                    tenant_id=self.tenant_id,
                    created_by=self.current_user.id,
                    updated_by=self.current_user.id
                )
                self.db.add(field)

        self.db.commit()
        self.db.refresh(entity)

        return entity

    async def list_entities(
        self,
        category: Optional[str] = None,
        entity_type: Optional[str] = None,
        status: Optional[str] = None,
        include_platform: bool = True
    ):
        """List all entity definitions (tenant-specific and optionally platform-level)"""
        from sqlalchemy import or_

        # Build tenant filter: include current tenant and optionally platform-level (tenant_id=NULL)
        if include_platform:
            tenant_filter = or_(
                EntityDefinition.tenant_id == self.tenant_id,
                EntityDefinition.tenant_id == None  # Platform-level entities
            )
        else:
            tenant_filter = EntityDefinition.tenant_id == self.tenant_id

        query = self.db.query(EntityDefinition).filter(
            tenant_filter,
            EntityDefinition.is_deleted == False
        )

        if category:
            query = query.filter(EntityDefinition.category == category)
        if entity_type:
            query = query.filter(EntityDefinition.entity_type == entity_type)
        if status:
            query = query.filter(EntityDefinition.status == status)

        return query.all()

    async def get_entity(self, entity_id: UUID, include_platform: bool = True):
        """Get entity definition by ID (checks tenant-specific and optionally platform-level)"""
        from sqlalchemy import or_

        # Build tenant filter
        if include_platform:
            tenant_filter = or_(
                EntityDefinition.tenant_id == self.tenant_id,
                EntityDefinition.tenant_id == None  # Platform-level entities
            )
        else:
            tenant_filter = EntityDefinition.tenant_id == self.tenant_id

        entity = self.db.query(EntityDefinition).filter(
            EntityDefinition.id == entity_id,
            tenant_filter,
            EntityDefinition.is_deleted == False
        ).first()

        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entity not found"
            )

        return entity

    async def update_entity(self, entity_id: UUID, entity_data: EntityDefinitionUpdate):
        """Update entity definition"""
        entity = await self.get_entity(entity_id)

        update_data = entity_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(entity, key, value)

        entity.updated_by = self.current_user.id

        self.db.commit()
        self.db.refresh(entity)

        return entity

    async def delete_entity(self, entity_id: UUID):
        """Delete entity definition (soft delete)"""
        entity = await self.get_entity(entity_id)

        entity.is_deleted = True
        entity.updated_by = self.current_user.id

        self.db.commit()

        return {"message": "Entity deleted successfully"}

    # ==================== Field Methods ====================

    async def create_field(self, entity_id: UUID, field_data: FieldDefinitionCreate):
        """Add a field to an entity"""
        entity = await self.get_entity(entity_id)

        # Check if field name already exists (active)
        existing_active = self.db.query(FieldDefinition).filter(
            FieldDefinition.entity_id == entity_id,
            FieldDefinition.name == field_data.name,
            FieldDefinition.is_deleted == False
        ).first()

        if existing_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field with name '{field_data.name}' already exists"
            )

        # Check if field name exists but is soft-deleted
        existing_deleted = self.db.query(FieldDefinition).filter(
            FieldDefinition.entity_id == entity_id,
            FieldDefinition.name == field_data.name,
            FieldDefinition.is_deleted == True
        ).first()

        if existing_deleted:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A field named '{field_data.name}' was previously deleted. Please use a different name (e.g., '{field_data.name}_2') or contact support to restore the deleted field."
            )

        field = FieldDefinition(
            **field_data.model_dump(),
            entity_id=entity_id,
            tenant_id=self.tenant_id,
            created_by=self.current_user.id,
            updated_by=self.current_user.id
        )

        self.db.add(field)
        self.db.commit()
        self.db.refresh(field)

        return field

    async def list_fields(self, entity_id: UUID, include_deleted: bool = False):
        """List all fields for an entity"""
        await self.get_entity(entity_id)  # Verify entity exists

        query = self.db.query(FieldDefinition).filter(
            FieldDefinition.entity_id == entity_id
        )

        if not include_deleted:
            query = query.filter(FieldDefinition.is_deleted == False)

        return query.order_by(FieldDefinition.display_order).all()

    async def update_field(self, entity_id: UUID, field_id: UUID, field_data: FieldDefinitionUpdate):
        """Update a field definition"""
        field = self.db.query(FieldDefinition).filter(
            FieldDefinition.id == field_id,
            FieldDefinition.entity_id == entity_id,
            FieldDefinition.is_deleted == False
        ).first()

        if not field:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Field not found"
            )

        update_data = field_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(field, key, value)

        field.updated_by = self.current_user.id

        self.db.commit()
        self.db.refresh(field)

        return field

    async def delete_field(self, entity_id: UUID, field_id: UUID):
        """Delete a field definition"""
        field = self.db.query(FieldDefinition).filter(
            FieldDefinition.id == field_id,
            FieldDefinition.entity_id == entity_id,
            FieldDefinition.is_deleted == False
        ).first()

        if not field:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Field not found"
            )

        if field.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete system field"
            )

        field.is_deleted = True
        field.updated_by = self.current_user.id

        self.db.commit()

        return {"message": "Field deleted successfully"}

    # ==================== Clone Methods ====================

    async def clone_entity(self, entity_id: UUID, new_name: str = None, new_label: str = None):
        """Clone a platform-level entity to a tenant-specific version."""
        # Get the source entity (must be platform-level)
        source_entity = await self.get_entity(entity_id, include_platform=True)

        if source_entity.tenant_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only clone platform-level entities. Use duplicate for tenant entities."
            )

        # Generate new name/label if not provided
        if not new_name:
            new_name = f"{source_entity.name}_copy"
        if not new_label:
            new_label = f"{source_entity.label} (Copy)"

        # Check if name already exists in tenant
        from sqlalchemy import or_
        existing = self.db.query(EntityDefinition).filter(
            or_(
                EntityDefinition.tenant_id == self.tenant_id,
                EntityDefinition.tenant_id == None
            ),
            EntityDefinition.name == new_name,
            EntityDefinition.is_deleted == False
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Entity with name '{new_name}' already exists"
            )

        # Clone entity
        cloned_entity = EntityDefinition(
            id=str(generate_uuid()),
            tenant_id=self.tenant_id,  # Make it tenant-specific
            name=new_name,
            label=new_label,
            plural_label=source_entity.plural_label,
            description=f"Cloned from platform template: {source_entity.description or ''}",
            icon=source_entity.icon,
            entity_type=source_entity.entity_type,
            category=source_entity.category,
            table_name=f"{new_name}s",  # Generate new table name
            schema_name=source_entity.schema_name,
            is_audited=source_entity.is_audited,
            is_versioned=source_entity.is_versioned,
            supports_soft_delete=source_entity.supports_soft_delete,
            supports_attachments=source_entity.supports_attachments,
            supports_comments=source_entity.supports_comments,
            primary_field=source_entity.primary_field,
            default_sort_field=source_entity.default_sort_field,
            default_sort_order=source_entity.default_sort_order,
            records_per_page=source_entity.records_per_page,
            status="draft",  # Start as draft
            meta_data=source_entity.meta_data,
            created_by=self.current_user.id,
            updated_by=self.current_user.id
        )

        self.db.add(cloned_entity)
        self.db.flush()

        # Clone fields
        source_fields = self.db.query(FieldDefinition).filter(
            FieldDefinition.entity_id == source_entity.id,
            FieldDefinition.is_deleted == False
        ).all()

        for source_field in source_fields:
            cloned_field = FieldDefinition(
                id=str(generate_uuid()),
                entity_id=cloned_entity.id,
                tenant_id=self.tenant_id,
                name=source_field.name,
                label=source_field.label,
                description=source_field.description,
                help_text=source_field.help_text,
                field_type=source_field.field_type,
                data_type=source_field.data_type,
                is_required=source_field.is_required,
                is_unique=source_field.is_unique,
                is_indexed=source_field.is_indexed,
                is_nullable=source_field.is_nullable,
                max_length=source_field.max_length,
                min_length=source_field.min_length,
                max_value=source_field.max_value,
                min_value=source_field.min_value,
                decimal_places=source_field.decimal_places,
                default_value=source_field.default_value,
                default_expression=source_field.default_expression,
                validation_rules=source_field.validation_rules,
                allowed_values=source_field.allowed_values,
                display_order=source_field.display_order,
                is_readonly=source_field.is_readonly,
                is_system=source_field.is_system,
                is_calculated=source_field.is_calculated,
                calculation_formula=source_field.calculation_formula,
                input_type=source_field.input_type,
                placeholder=source_field.placeholder,
                prefix=source_field.prefix,
                suffix=source_field.suffix,
                relationship_type=source_field.relationship_type,
                meta_data=source_field.meta_data,
                created_by=self.current_user.id,
                updated_by=self.current_user.id
            )
            self.db.add(cloned_field)

        self.db.commit()
        self.db.refresh(cloned_entity)

        return cloned_entity

    # ==================== Relationship Methods ====================

    async def create_relationship(self, relationship_data: RelationshipDefinitionCreate):
        """Create a relationship between entities"""
        relationship = RelationshipDefinition(
            **relationship_data.model_dump(),
            tenant_id=self.tenant_id,
            created_by=self.current_user.id,
            updated_by=self.current_user.id
        )

        self.db.add(relationship)
        self.db.commit()
        self.db.refresh(relationship)

        return relationship

    async def list_relationships(self, entity_id: Optional[UUID] = None):
        """List relationships"""
        query = self.db.query(RelationshipDefinition).filter(
            RelationshipDefinition.tenant_id == self.tenant_id,
            RelationshipDefinition.is_deleted == False
        )

        if entity_id:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    RelationshipDefinition.source_entity_id == entity_id,
                    RelationshipDefinition.target_entity_id == entity_id
                )
            )

        return query.all()

    async def delete_relationship(self, relationship_id: UUID):
        """Delete a relationship"""
        relationship = self.db.query(RelationshipDefinition).filter(
            RelationshipDefinition.id == relationship_id,
            RelationshipDefinition.tenant_id == self.tenant_id
        ).first()

        if not relationship:
            raise ValueError("Relationship not found")

        relationship.is_deleted = True
        self.db.commit()
        return {"message": "Relationship deleted"}

    async def create_entity_from_introspection(self, introspected_data: dict):
        """
        Create EntityDefinition and fields from introspected database object

        Takes the output from SchemaIntrospector and creates a complete
        entity definition with all fields, relationships, and indexes.
        """
        from app.schemas.data_model import EntityDefinitionCreate, FieldDefinitionCreate

        # Build EntityDefinitionCreate from introspected data
        entity_create = EntityDefinitionCreate(
            name=introspected_data['name'],
            label=introspected_data['label'],
            description=introspected_data.get('description'),
            table_name=introspected_data['table_name'],
            schema_name=introspected_data.get('schema_name', 'public'),
            entity_type='custom',
            is_audited=introspected_data.get('is_audited', False),
            supports_soft_delete=introspected_data.get('supports_soft_delete', False),
            # Set status to draft for review
            status='draft'
        )

        # Create the entity
        entity = await self.create_entity(entity_create)

        # Create fields
        for field_data in introspected_data.get('fields', []):
            field_create = FieldDefinitionCreate(
                name=field_data['name'],
                label=field_data['label'],
                field_type=field_data['field_type'],
                data_type=field_data['data_type'],
                is_required=field_data.get('is_required', False),
                is_nullable=field_data.get('is_nullable', True),
                is_unique=field_data.get('is_unique', False),
                is_indexed=field_data.get('is_indexed', False),
                is_readonly=field_data.get('is_readonly', False),
                is_system=field_data.get('is_system', False),
                is_computed=field_data.get('is_computed', False),
                max_length=field_data.get('max_length'),
                decimal_places=field_data.get('decimal_places'),
                default_value=field_data.get('default_value'),
                display_order=field_data.get('display_order', 0)
            )

            await self.create_field(entity.id, field_create)

        # Create relationships if any
        # Note: This is complex as we need to resolve target entity IDs
        # For now, we'll skip auto-creating relationships and let users
        # create them manually or in a second pass

        # Create indexes if any
        for index_data in introspected_data.get('indexes', []):
            index = IndexDefinition(
                entity_id=entity.id,
                tenant_id=self.tenant_id,
                name=index_data['name'],
                index_type=index_data.get('index_type', 'btree'),
                field_names=index_data['field_names'],
                is_unique=index_data.get('is_unique', False),
                is_active=True,
                created_by=self.current_user.id
            )
            self.db.add(index)

        self.db.commit()
        self.db.refresh(entity)

        return entity

    # ==================== Migration Methods ====================

    async def preview_migration(self, entity_id: UUID):
        """Preview SQL changes for entity"""
        from app.services.migration_generator import MigrationGenerator
        from sqlalchemy import text

        entity = self.db.query(EntityDefinition).filter(
            EntityDefinition.id == entity_id,
            EntityDefinition.is_deleted == False
        ).first()

        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entity {entity_id} not found"
            )

        # Check permissions
        if entity.tenant_id and entity.tenant_id != self.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to preview this entity"
            )

        # Generate migration SQL
        migration_gen = MigrationGenerator(self.db)
        up_sql, down_sql = await migration_gen.generate_migration(entity)

        # Get change preview
        changes = await migration_gen.preview_changes(entity)

        # Estimate impact
        estimated_impact = await self._estimate_impact(entity)

        return {
            'entity_id': entity.id,
            'entity_name': entity.name,
            'table_name': entity.table_name,
            'operation': changes['operation'],
            'up_script': up_sql,
            'down_script': down_sql,
            'changes': changes.get('changes', {}),
            'estimated_impact': estimated_impact
        }

    async def generate_migration(self, entity_id: UUID, commit_message: str = None):
        """Generate and save migration without executing it"""
        from app.services.migration_generator import MigrationGenerator
        import time

        entity = self.db.query(EntityDefinition).filter(
            EntityDefinition.id == entity_id,
            EntityDefinition.is_deleted == False
        ).first()

        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entity {entity_id} not found"
            )

        # Check permissions
        if entity.tenant_id and entity.tenant_id != self.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to generate migration for this entity"
            )

        # Check if there's already a pending migration for this entity
        existing_pending = self.db.query(EntityMigration).filter(
            EntityMigration.entity_id == entity_id,
            EntityMigration.status == 'pending'
        ).first()

        if existing_pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="There is already a pending migration for this entity. Please run or delete it first."
            )

        # Generate migration SQL
        migration_gen = MigrationGenerator(self.db)
        up_sql, down_sql = await migration_gen.generate_migration(entity)

        # Get changes for logging
        changes = await migration_gen.preview_changes(entity)

        # Determine next version
        next_version = (entity.version or 0) + 1

        # Create migration record with 'pending' status
        migration = EntityMigration(
            entity_id=entity_id,
            tenant_id=entity.tenant_id,
            migration_name=f"{entity.name}_v{next_version}_{int(time.time())}",
            migration_type='create' if entity.version == 0 or entity.version is None else 'alter',
            from_version=entity.version if entity.version else None,
            to_version=next_version,
            up_script=up_sql,
            down_script=down_sql,
            status='pending',
            changes=changes,
            created_by=self.current_user.id,
            commit_message=commit_message
        )

        self.db.add(migration)
        self.db.commit()
        self.db.refresh(migration)

        return {
            'id': migration.id,
            'migration_name': migration.migration_name,
            'migration_type': migration.migration_type,
            'from_version': migration.from_version,
            'to_version': migration.to_version,
            'status': migration.status,
            'up_script': migration.up_script,
            'down_script': migration.down_script,
            'changes': migration.changes,
            'created_at': migration.created_at,
            'entity_name': entity.name,
            'entity_label': entity.label
        }

    async def publish_entity(self, entity_id: UUID, commit_message: str = None):
        """Publish entity and execute migration"""
        from app.services.migration_generator import MigrationGenerator
        from datetime import datetime
        from sqlalchemy import text
        import time

        entity = self.db.query(EntityDefinition).filter(
            EntityDefinition.id == entity_id,
            EntityDefinition.is_deleted == False
        ).first()

        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entity {entity_id} not found"
            )

        # Check permissions
        if entity.tenant_id and entity.tenant_id != self.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to publish this entity"
            )

        if entity.status == 'published':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Entity is already published. Create a new version to make changes."
            )

        # Generate migration
        migration_gen = MigrationGenerator(self.db)
        up_sql, down_sql = await migration_gen.generate_migration(entity)

        # Get changes for logging
        changes = await migration_gen.preview_changes(entity)

        # Increment version
        entity.version = (entity.version or 0) + 1

        # Create migration record
        migration = EntityMigration(
            entity_id=entity_id,
            tenant_id=entity.tenant_id,
            migration_name=f"{entity.name}_v{entity.version}_{int(time.time())}",
            migration_type='create' if entity.version == 1 else 'alter',
            from_version=entity.version - 1 if entity.version > 1 else None,
            to_version=entity.version,
            up_script=up_sql,
            down_script=down_sql,
            status='pending',
            changes=changes,
            created_by=self.current_user.id
        )

        self.db.add(migration)
        self.db.flush()  # Get the migration ID

        # Execute migration
        try:
            migration.status = 'running'
            self.db.commit()

            start_time = time.time()

            # Execute in transaction
            self.db.execute(text(up_sql))

            execution_time = int((time.time() - start_time) * 1000)

            migration.status = 'completed'
            migration.executed_at = datetime.utcnow()
            migration.execution_time_ms = execution_time

            # Update entity status
            entity.status = 'published'

            # Auto-generate EntityMetadata for published entity
            try:
                from app.services.metadata_sync_service import MetadataSyncService
                metadata_sync = MetadataSyncService(self.db)
                metadata_sync.auto_generate_metadata(
                    entity_definition=entity,
                    created_by=str(self.current_user.id)
                )
            except Exception as meta_error:
                # Log error but don't fail the publish
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to auto-generate metadata for {entity.name}: {str(meta_error)}")

            # Auto-create menu item for published nocode entity
            try:
                from app.services.menu_service import MenuService
                import logging
                logger = logging.getLogger(__name__)

                # Create menu item with route to dynamic entity list view
                menu_data = {
                    'code': f'nocode_entity_{entity.name}',
                    'title': entity.label or entity.name.replace('_', ' ').title(),
                    'route': f'dynamic/{entity.name}/list',
                    'icon': entity.icon or 'ph-duotone ph-database',
                    'parent_code': 'nocode_entities',  # Will be created if not exists
                    'permission': None,  # Default permission - will be filtered by entity access control
                    'required_roles': [],
                    'is_system': False,
                    'is_active': True,
                    'extra_data': {
                        'entity_id': str(entity.id),
                        'is_nocode': True
                    }
                }

                # Ensure parent "No-Code Entities" menu exists
                parent_menu = MenuService.get_or_create_nocode_parent(self.db, entity.tenant_id, str(self.current_user.id))

                # Create menu item
                MenuService.create_menu_item(
                    db=self.db,
                    user=self.current_user,
                    menu_data=menu_data
                )

                logger.info(f"✅ Auto-created menu item for nocode entity: {entity.name}")

            except Exception as menu_error:
                # Log error but don't fail the publish
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to auto-create menu item for {entity.name}: {str(menu_error)}")

            self.db.commit()
            self.db.refresh(migration)
            self.db.refresh(entity)

            return migration

        except Exception as e:
            self.db.rollback()

            migration.status = 'failed'
            migration.error_message = str(e)
            self.db.commit()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Migration failed: {str(e)}"
            )

    async def list_migrations(self, entity_id: UUID):
        """List migration history for an entity"""
        entity = self.db.query(EntityDefinition).filter(
            EntityDefinition.id == entity_id,
            EntityDefinition.is_deleted == False
        ).first()

        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entity {entity_id} not found"
            )

        # Check permissions
        if entity.tenant_id and entity.tenant_id != self.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view migrations for this entity"
            )

        migrations = self.db.query(EntityMigration).filter(
            EntityMigration.entity_id == entity_id
        ).order_by(EntityMigration.created_at.desc()).all()

        return {
            'migrations': migrations,
            'total': len(migrations)
        }

    async def execute_migration(self, migration_id: UUID):
        """Execute a pending migration"""
        from datetime import datetime
        from sqlalchemy import text
        import time

        migration = self.db.query(EntityMigration).filter(
            EntityMigration.id == migration_id
        ).first()

        if not migration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Migration {migration_id} not found"
            )

        # Check permissions
        if migration.tenant_id and migration.tenant_id != self.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to execute this migration"
            )

        if migration.status != 'pending':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Can only execute pending migrations. Current status: {migration.status}"
            )

        entity = self.db.query(EntityDefinition).filter(
            EntityDefinition.id == migration.entity_id
        ).first()

        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entity not found for migration {migration_id}"
            )

        # Execute migration
        try:
            migration.status = 'running'
            self.db.commit()

            start_time = time.time()

            # Execute UP script in transaction
            self.db.execute(text(migration.up_script))

            execution_time = int((time.time() - start_time) * 1000)

            migration.status = 'completed'
            migration.executed_at = datetime.utcnow()
            migration.execution_time_ms = execution_time

            # Update entity version and status
            entity.version = migration.to_version
            entity.status = 'published'

            # Auto-generate EntityMetadata for published entity
            try:
                from app.services.metadata_sync_service import MetadataSyncService
                metadata_sync = MetadataSyncService(self.db)
                metadata_sync.auto_generate_metadata(
                    entity_definition=entity,
                    created_by=str(self.current_user.id)
                )
            except Exception as meta_error:
                # Log error but don't fail the execution
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to auto-generate metadata for {entity.name}: {str(meta_error)}")

            # Auto-create menu item for published nocode entity
            try:
                from app.services.menu_service import MenuService
                import logging
                logger = logging.getLogger(__name__)

                # Create menu item with route to dynamic entity list view
                menu_data = {
                    'code': f'nocode_entity_{entity.name}',
                    'title': entity.label or entity.name.replace('_', ' ').title(),
                    'route': f'dynamic/{entity.name}/list',
                    'icon': entity.icon or 'ph-duotone ph-database',
                    'parent_code': 'nocode_entities',
                    'permission': None,
                    'required_roles': [],
                    'is_system': False,
                    'is_active': True,
                    'extra_data': {
                        'entity_id': str(entity.id),
                        'is_nocode': True
                    }
                }

                # Ensure parent "No-Code Entities" menu exists
                parent_menu = MenuService.get_or_create_nocode_parent(self.db, entity.tenant_id, str(self.current_user.id))

                # Create menu item
                MenuService.create_menu_item(
                    db=self.db,
                    user=self.current_user,
                    menu_data=menu_data
                )

                logger.info(f"✅ Auto-created menu item for nocode entity: {entity.name}")

            except Exception as menu_error:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to auto-create menu item for {entity.name}: {str(menu_error)}")

            self.db.commit()
            self.db.refresh(migration)
            self.db.refresh(entity)

            return {
                'id': migration.id,
                'migration_name': migration.migration_name,
                'status': migration.status,
                'executed_at': migration.executed_at,
                'execution_time_ms': execution_time,
                'entity_id': str(entity.id),
                'entity_name': entity.name,
                'entity_label': entity.label,
                'entity_status': entity.status,
                'message': f"Migration executed successfully in {execution_time}ms"
            }

        except Exception as e:
            self.db.rollback()
            migration.status = 'failed'
            migration.error_message = str(e)
            self.db.commit()

            import traceback
            error_details = traceback.format_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Migration execution failed: {str(e)}\n\n{error_details}"
            )

    async def rollback_migration(self, migration_id: UUID):
        """Rollback a migration"""
        from datetime import datetime
        from sqlalchemy import text
        import time

        migration = self.db.query(EntityMigration).filter(
            EntityMigration.id == migration_id
        ).first()

        if not migration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Migration {migration_id} not found"
            )

        # Check permissions
        if migration.tenant_id and migration.tenant_id != self.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to rollback this migration"
            )

        if migration.status != 'completed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only rollback completed migrations"
            )

        if not migration.down_script:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No rollback script available for this migration"
            )

        # Execute rollback
        try:
            start_time = time.time()

            # Execute down script
            self.db.execute(text(migration.down_script))

            execution_time = int((time.time() - start_time) * 1000)

            # Update migration status
            migration.status = 'rolled_back'

            # Update entity version
            entity = self.db.query(EntityDefinition).filter(
                EntityDefinition.id == migration.entity_id
            ).first()

            if entity:
                entity.version = migration.from_version or 0
                if entity.version == 0:
                    entity.status = 'draft'

            self.db.commit()

            return {
                'migration_id': migration.id,
                'status': 'rolled_back',
                'message': 'Migration rolled back successfully',
                'execution_time_ms': execution_time,
                'rolled_back_at': datetime.utcnow()
            }

        except Exception as e:
            self.db.rollback()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Rollback failed: {str(e)}"
            )

    async def _estimate_impact(self, entity: EntityDefinition) -> dict:
        """Estimate the impact of publishing this entity"""
        from app.services.migration_generator import MigrationGenerator
        from sqlalchemy import text

        migration_gen = MigrationGenerator(self.db)
        table_exists = await migration_gen._table_exists(entity.table_name)

        if not table_exists:
            return {
                'risk_level': 'low',
                'affected_records': 0,
                'breaking_changes': [],
                'warnings': []
            }

        # Check for existing data
        try:
            result = self.db.execute(
                text(f"SELECT COUNT(*) FROM {entity.table_name}")
            )
            record_count = result.scalar()
        except:
            record_count = 0

        # Analyze changes for risk
        changes = await migration_gen.preview_changes(entity)
        breaking_changes = []
        warnings = []

        if changes['operation'] == 'ALTER':
            change_details = changes.get('changes', {})

            # Dropping columns is a breaking change
            if change_details.get('removed_columns'):
                breaking_changes.append(
                    f"Dropping columns: {', '.join(change_details['removed_columns'])}"
                )

            # Type changes can be risky
            if change_details.get('modified_columns'):
                for mod in change_details['modified_columns']:
                    warnings.append(
                        f"Column {mod['name']} type changing from {mod['from_type']} to {mod['to_type']}"
                    )

        # Determine risk level
        risk_level = 'low'
        if breaking_changes:
            risk_level = 'high'
        elif warnings or record_count > 1000:
            risk_level = 'medium'

        return {
            'risk_level': risk_level,
            'affected_records': record_count,
            'breaking_changes': breaking_changes,
            'warnings': warnings
        }
