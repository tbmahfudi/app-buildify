"""
Runtime Model Generator - Dynamically generates SQLAlchemy models from EntityDefinition

This service reads EntityDefinition metadata from the database and generates
SQLAlchemy ORM models at runtime. Models are cached for performance.
"""

from typing import Type, Optional, Dict, Any
from sqlalchemy import Column, ForeignKey, Table, MetaData, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid
from sqlalchemy.orm import Session, relationship
from sqlalchemy.ext.declarative import declarative_base
from app.models.data_model import EntityDefinition, FieldDefinition, RelationshipDefinition
from app.utils.field_type_mapper import FieldTypeMapper
from app.core.model_cache import get_model_cache, ModelCache
import logging

logger = logging.getLogger(__name__)

# Create a separate declarative base for dynamic models
# This prevents conflicts with static models
DynamicBase = declarative_base()


class RuntimeModelGenerator:
    """
    Generates SQLAlchemy models from EntityDefinition at runtime

    This class is responsible for:
    1. Loading EntityDefinition from database
    2. Converting field definitions to SQLAlchemy columns
    3. Setting up relationships between entities
    4. Caching generated models
    """

    def __init__(self, db: Session):
        """
        Initialize runtime model generator

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.cache: ModelCache = get_model_cache()
        self.field_mapper = FieldTypeMapper()

    def get_model(
        self,
        entity_name: str,
        tenant_id: Optional[str] = None
    ) -> Type:
        """
        Get or generate SQLAlchemy model for entity

        Args:
            entity_name: Name of the entity
            tenant_id: Tenant ID (None for platform-level entities)

        Returns:
            SQLAlchemy model class

        Raises:
            ValueError: If entity not found or not published
        """
        # Load entity definition
        entity_def = self._load_entity_definition(entity_name, tenant_id)

        if not entity_def:
            raise ValueError(
                f"Entity '{entity_name}' not found or not published for tenant '{tenant_id}'"
            )

        # Convert to dict for caching
        entity_dict = self._entity_to_dict(entity_def)

        # Create hash for cache key
        entity_hash = self.cache.hash_entity_definition(entity_dict)

        # Check cache
        cache_tenant_id = str(tenant_id) if tenant_id else 'platform'
        cached_model = self.cache.get(cache_tenant_id, entity_name, entity_hash)

        if cached_model:
            logger.debug(f"Using cached model for {entity_name}")
            return cached_model

        # Generate new model
        logger.info(f"Generating new model for {entity_name}")
        model = self._generate_model(entity_def, entity_dict)

        # Cache it
        self.cache.set(cache_tenant_id, entity_name, entity_hash, model)

        return model

    def invalidate_cache(
        self,
        entity_name: Optional[str] = None,
        tenant_id: Optional[str] = None
    ):
        """
        Invalidate cached models

        Args:
            entity_name: If provided, invalidate only this entity
            tenant_id: If provided, invalidate only this tenant's models
        """
        self.cache.invalidate(tenant_id, entity_name)
        logger.info(f"Cache invalidated for entity={entity_name}, tenant={tenant_id}")

    def _load_entity_definition(
        self,
        entity_name: str,
        tenant_id: Optional[str]
    ) -> Optional[EntityDefinition]:
        """
        Load EntityDefinition from database

        Args:
            entity_name: Name of the entity
            tenant_id: Tenant ID (None for platform-level)

        Returns:
            EntityDefinition object or None
        """
        from sqlalchemy import or_

        query = self.db.query(EntityDefinition).filter(
            EntityDefinition.name == entity_name,
            EntityDefinition.status == 'published'
        )

        # Check tenant-specific first, then platform-level
        if tenant_id:
            query = query.filter(
                or_(
                    EntityDefinition.tenant_id == tenant_id,
                    EntityDefinition.tenant_id.is_(None)
                )
            )
            # Prefer tenant-specific over platform
            query = query.order_by(EntityDefinition.tenant_id.desc())
        else:
            # Only platform-level
            query = query.filter(EntityDefinition.tenant_id.is_(None))

        return query.first()

    def _entity_to_dict(self, entity_def: EntityDefinition) -> dict:
        """
        Convert EntityDefinition to dict for caching

        Args:
            entity_def: EntityDefinition object

        Returns:
            Dictionary representation
        """
        return {
            'id': str(entity_def.id),
            'name': entity_def.name,
            'table_name': entity_def.table_name,
            'schema_name': entity_def.schema_name or 'public',
            'label': entity_def.label,
            'plural_label': entity_def.plural_label,
            'fields': [
                {
                    'id': str(f.id),
                    'name': f.name,
                    'field_type': f.field_type,
                    'db_column_name': f.name,  # Use name as db column name
                    'label': f.label,
                    'is_required': f.is_required,
                    'is_primary_key': f.name == 'id',  # Assume 'id' field is primary key
                    'is_unique': f.is_unique,
                    'is_indexed': f.is_indexed,
                    'max_length': f.max_length,
                    'min_length': f.min_length,
                    'min_value': f.min_value,
                    'max_value': f.max_value,
                    'precision': f.precision,
                    'scale': f.decimal_places,  # Use decimal_places as scale
                    'default_value': f.default_value,
                    'lookup_config': getattr(f, 'lookup_config', None),
                    'validation_rules': f.validation_rules,
                    'order': f.display_order
                }
                for f in sorted(entity_def.fields, key=lambda x: x.display_order or 0)
            ],
            'relationships': [
                {
                    'id': str(r.id),
                    'name': r.name,
                    'relationship_type': r.relationship_type,
                    'target_entity_id': str(r.target_entity_id) if r.target_entity_id else None,
                    'source_field_name': r.source_field_name,
                    'target_field_name': r.target_field_name,
                    'on_delete': r.on_delete,
                    'on_update': r.on_update
                }
                for r in entity_def.source_relationships
            ] if entity_def.source_relationships else []
        }

    def _generate_model(self, entity_def: EntityDefinition, entity_dict: dict) -> Type:
        """
        Generate SQLAlchemy model from EntityDefinition

        Args:
            entity_def: EntityDefinition object
            entity_dict: EntityDefinition as dictionary

        Returns:
            SQLAlchemy model class
        """
        table_name = entity_dict['table_name']
        schema_name = entity_dict['schema_name']

        # Build attributes dict for model class
        attrs = {
            '__tablename__': table_name,
            '__table_args__': {'schema': schema_name, 'extend_existing': True},
            '__entity_definition__': entity_dict,  # Store metadata for reference
        }

        # Determine which field should be the primary key
        # Priority: 1) explicit is_primary_key, 2) field named 'id', 3) first field
        fields = entity_dict['fields']
        pk_field_name = None

        # Check for explicit primary key
        for f in fields:
            if f.get('is_primary_key'):
                pk_field_name = f['db_column_name'] or f['name']
                break

        # If no explicit PK, look for 'id' field
        if not pk_field_name:
            for f in fields:
                field_name = f['db_column_name'] or f['name']
                if field_name == 'id':
                    pk_field_name = 'id'
                    break

        # If still no PK, use the first field
        if not pk_field_name and fields:
            pk_field_name = fields[0]['db_column_name'] or fields[0]['name']

        # Add columns from FieldDefinitions
        for field in fields:
            # Mark the designated field as primary key
            field_name = field['db_column_name'] or field['name']
            if field_name == pk_field_name:
                field = dict(field)  # Copy to avoid modifying original
                field['is_primary_key'] = True

            column = self.field_mapper.to_sqlalchemy_column(
                field,
                include_foreign_key=False  # We'll handle relationships separately
            )
            column_name = field['db_column_name'] or field['name']
            attrs[column_name] = column

        # Create model class dynamically
        model_class_name = self._to_class_name(entity_dict['name'])
        model_class = type(
            model_class_name,
            (DynamicBase,),
            attrs
        )

        # Set up relationships (if any)
        # Note: Relationships are tricky with dynamic models
        # We'll store relationship metadata but actual ORM relationships
        # require all target models to be generated first
        if entity_dict.get('relationships'):
            for rel in entity_dict['relationships']:
                self._add_relationship(model_class, rel, entity_dict)

        return model_class

    def _add_relationship(
        self,
        model_class: Type,
        relationship_def: dict,
        entity_dict: dict
    ):
        """
        Add relationship to model class

        Note: This is a simplified implementation.
        Full relationship support requires a registry of all generated models.

        Args:
            model_class: SQLAlchemy model class
            relationship_def: Relationship definition dict
            entity_dict: Entity definition dict
        """
        rel_name = relationship_def['name']
        rel_type = relationship_def['relationship_type']
        target_entity_id = relationship_def.get('target_entity_id')

        # For now, we'll store the relationship metadata as class attribute
        # Actual SQLAlchemy relationship() calls require target model to exist
        if not hasattr(model_class, '_nocode_relationships'):
            model_class._nocode_relationships = []

        model_class._nocode_relationships.append({
            'name': rel_name,
            'type': rel_type,
            'target_entity_id': target_entity_id,
            'source_field_name': relationship_def.get('source_field_name'),
            'target_field_name': relationship_def.get('target_field_name'),
        })

        # TODO: Implement actual SQLAlchemy relationships
        # This requires:
        # 1. A model registry to lookup target models
        # 2. Proper foreign key constraints
        # 3. Handling of one-to-many, many-to-one, many-to-many
        #
        # For Phase 2, we'll handle relationships at the query level
        # rather than using SQLAlchemy's relationship() feature

    def _to_class_name(self, entity_name: str) -> str:
        """
        Convert entity name to Python class name

        Examples:
            'customer' -> 'Customer'
            'order_item' -> 'OrderItem'
            'sales_order' -> 'SalesOrder'

        Args:
            entity_name: Entity name (snake_case)

        Returns:
            Python class name (PascalCase)
        """
        parts = entity_name.split('_')
        return ''.join(word.capitalize() for word in parts)

    def get_field_definitions(self, entity_name: str, tenant_id: Optional[str] = None) -> list:
        """
        Get field definitions for an entity

        Args:
            entity_name: Name of the entity
            tenant_id: Tenant ID

        Returns:
            List of field definition dicts
        """
        entity_def = self._load_entity_definition(entity_name, tenant_id)

        if not entity_def:
            raise ValueError(f"Entity '{entity_name}' not found")

        entity_dict = self._entity_to_dict(entity_def)
        return entity_dict['fields']

    def get_relationship_definitions(
        self,
        entity_name: str,
        tenant_id: Optional[str] = None
    ) -> list:
        """
        Get relationship definitions for an entity

        Args:
            entity_name: Name of the entity
            tenant_id: Tenant ID

        Returns:
            List of relationship definition dicts
        """
        entity_def = self._load_entity_definition(entity_name, tenant_id)

        if not entity_def:
            raise ValueError(f"Entity '{entity_name}' not found")

        entity_dict = self._entity_to_dict(entity_def)
        return entity_dict.get('relationships', [])
