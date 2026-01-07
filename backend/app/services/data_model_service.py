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

        # Check if field name already exists
        existing = self.db.query(FieldDefinition).filter(
            FieldDefinition.entity_id == entity_id,
            FieldDefinition.name == field_data.name,
            FieldDefinition.is_deleted == False
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field with name '{field_data.name}' already exists"
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

    async def list_fields(self, entity_id: UUID):
        """List all fields for an entity"""
        await self.get_entity(entity_id)  # Verify entity exists

        return self.db.query(FieldDefinition).filter(
            FieldDefinition.entity_id == entity_id,
            FieldDefinition.is_deleted == False
        ).order_by(FieldDefinition.display_order).all()

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
