"""
Data Model Designer - Database Models

Models for the no-code platform's data model designer feature.
Enables users to create and manage database entities without writing code.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import GUID, Base, generate_uuid


class EntityDefinition(Base):
    """
    Entity Definition Model

    Stores metadata for custom entities/tables created through the data model designer.
    Each entity definition represents a table that will be created in the database.
    """
    __tablename__ = "entity_definitions"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    # tenant_id: NULL = platform-level (shared across tenants), specific ID = tenant-specific
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=True, index=True)

    # Basic Info
    name = Column(String(100), nullable=False)  # Technical name (snake_case)
    label = Column(String(200), nullable=False)  # Display name
    plural_label = Column(String(200))
    description = Column(Text)
    icon = Column(String(50))  # Phosphor icon name

    # Type & Category
    entity_type = Column(String(50), default="custom")  # 'system', 'custom', 'virtual'
    category = Column(String(100))  # Grouping for UI

    # Table Info
    table_name = Column(String(100), nullable=False)  # Actual database table name
    schema_name = Column(String(100), default="public")

    # Configuration
    is_audited = Column(Boolean, default=True)
    is_versioned = Column(Boolean, default=False)
    supports_soft_delete = Column(Boolean, default=True)
    supports_attachments = Column(Boolean, default=True)
    supports_comments = Column(Boolean, default=True)

    # Layout & Display
    primary_field = Column(String(100))  # Field to use as record title
    default_sort_field = Column(String(100))
    default_sort_order = Column(String(10), default="ASC")
    records_per_page = Column(Integer, default=25)

    # Status
    status = Column(String(50), default="draft")  # 'draft', 'published', 'migrating', 'archived'
    is_active = Column(Boolean, default=True)

    # Metadata
    meta_data = Column(JSONB, default=dict)  # Extended configuration

    # Versioning
    version = Column(Integer, default=1)
    parent_version_id = Column(GUID, ForeignKey("entity_definitions.id"), nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(GUID, ForeignKey("users.id"))
    updated_by = Column(GUID, ForeignKey("users.id"))
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)

    # Relationships
    fields = relationship("FieldDefinition", foreign_keys="FieldDefinition.entity_id", back_populates="entity", cascade="all, delete-orphan")
    migrations = relationship("EntityMigration", back_populates="entity")
    indexes = relationship("IndexDefinition", back_populates="entity", cascade="all, delete-orphan")
    source_relationships = relationship("RelationshipDefinition", foreign_keys="RelationshipDefinition.source_entity_id", back_populates="source_entity")
    target_relationships = relationship("RelationshipDefinition", foreign_keys="RelationshipDefinition.target_entity_id", back_populates="target_entity")

    # Table constraints
    __table_args__ = (
        Index("idx_entity_definitions_tenant", "tenant_id", postgresql_where=text("is_deleted = false")),
        Index("idx_entity_definitions_status", "status"),
        Index("idx_entity_definitions_type", "entity_type"),
    )


class FieldDefinition(Base):
    """
    Field Definition Model

    Stores metadata for fields within entity definitions.
    Each field represents a column in the database table.
    """
    __tablename__ = "field_definitions"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    entity_id = Column(GUID, ForeignKey("entity_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False)

    # Basic Info
    name = Column(String(100), nullable=False)  # Technical name (snake_case)
    label = Column(String(200), nullable=False)  # Display name
    description = Column(Text)
    help_text = Column(Text)

    # Field Type
    field_type = Column(String(50), nullable=False)  # 'string', 'integer', 'decimal', 'date', etc.
    data_type = Column(String(50), nullable=False)  # Database type: 'VARCHAR', 'INTEGER', 'TIMESTAMP', etc.

    # Constraints
    is_required = Column(Boolean, default=False)
    is_unique = Column(Boolean, default=False)
    is_indexed = Column(Boolean, default=False)
    is_nullable = Column(Boolean, default=True)

    # String Constraints
    max_length = Column(Integer)
    min_length = Column(Integer)

    # Numeric Constraints
    max_value = Column(Numeric)
    min_value = Column(Numeric)
    decimal_places = Column(Integer)

    # Default Value
    default_value = Column(Text)
    default_expression = Column(Text)  # SQL expression for dynamic defaults

    # Validation
    validation_rules = Column(JSONB, default=list)  # Custom validation rules
    allowed_values = Column(JSONB)  # For enum-like fields

    # Display & Behavior
    display_order = Column(Integer, default=0)
    is_readonly = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)  # System fields can't be deleted
    is_calculated = Column(Boolean, default=False)
    calculation_formula = Column(Text)  # Formula for calculated fields

    # UI Configuration
    input_type = Column(String(50))  # 'text', 'textarea', 'select', 'date-picker', etc.
    placeholder = Column(Text)
    prefix = Column(Text)  # e.g., '$' for currency
    suffix = Column(Text)  # e.g., 'kg' for weight

    # Relationship Fields (for lookup/reference fields)
    reference_entity_id = Column(GUID, ForeignKey("entity_definitions.id"), nullable=True)
    reference_field = Column(String(100))  # Field in referenced entity to display
    relationship_type = Column(String(50))  # 'many-to-one', 'one-to-one'

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(GUID, ForeignKey("users.id"))
    updated_by = Column(GUID, ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False)

    # Relationships
    entity = relationship("EntityDefinition", foreign_keys=[entity_id], back_populates="fields")

    # Table constraints
    __table_args__ = (
        Index("idx_field_definitions_entity", "entity_id", postgresql_where=text("is_deleted = false")),
        Index("idx_field_definitions_type", "field_type"),
    )


class RelationshipDefinition(Base):
    """
    Relationship Definition Model

    Stores metadata for relationships between entities.
    Supports one-to-many, many-to-many, and one-to-one relationships.
    """
    __tablename__ = "relationship_definitions"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False)

    # Basic Info
    name = Column(String(100), nullable=False)
    label = Column(String(200), nullable=False)
    description = Column(Text)

    # Relationship Type
    relationship_type = Column(String(50), nullable=False)  # 'one-to-many', 'many-to-many', 'one-to-one'

    # Source Entity
    source_entity_id = Column(GUID, ForeignKey("entity_definitions.id"), nullable=False, index=True)
    source_field_name = Column(String(100))  # Field name to create on source

    # Target Entity
    target_entity_id = Column(GUID, ForeignKey("entity_definitions.id"), nullable=False, index=True)
    target_field_name = Column(String(100))  # Field name to create on target

    # Junction Table (for many-to-many)
    junction_table_name = Column(String(100))
    junction_source_field = Column(String(100))
    junction_target_field = Column(String(100))

    # Cascade Behavior
    on_delete = Column(String(50), default="NO ACTION")  # 'CASCADE', 'SET NULL', 'RESTRICT', 'NO ACTION'
    on_update = Column(String(50), default="NO ACTION")

    # Display Configuration
    is_active = Column(Boolean, default=True)
    display_in_source = Column(Boolean, default=True)
    display_in_target = Column(Boolean, default=True)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(GUID, ForeignKey("users.id"))
    updated_by = Column(GUID, ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False)

    # Relationships
    source_entity = relationship("EntityDefinition", foreign_keys=[source_entity_id], back_populates="source_relationships")
    target_entity = relationship("EntityDefinition", foreign_keys=[target_entity_id], back_populates="target_relationships")

    # Table constraints
    __table_args__ = (
        Index("idx_relationship_definitions_source", "source_entity_id"),
        Index("idx_relationship_definitions_target", "target_entity_id"),
    )


class IndexDefinition(Base):
    """
    Index Definition Model

    Stores metadata for database indexes on entities.
    """
    __tablename__ = "index_definitions"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    entity_id = Column(GUID, ForeignKey("entity_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False)

    # Basic Info
    name = Column(String(100), nullable=False)
    index_type = Column(String(50), default="btree")  # 'btree', 'hash', 'gin', 'gist'

    # Fields (ordered)
    field_names = Column(JSONB, nullable=False)  # Array of field names

    # Configuration
    is_unique = Column(Boolean, default=False)
    is_partial = Column(Boolean, default=False)
    where_clause = Column(Text)  # For partial indexes

    # Status
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(GUID, ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False)

    # Relationships
    entity = relationship("EntityDefinition", back_populates="indexes")

    # Table constraints
    __table_args__ = (
        Index("idx_index_definitions_entity", "entity_id"),
    )


class EntityMigration(Base):
    """
    Entity Migration Model

    Tracks database migrations for entity definitions.
    Stores up/down scripts and execution status.
    """
    __tablename__ = "entity_migrations"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    entity_id = Column(GUID, ForeignKey("entity_definitions.id"), nullable=False, index=True)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False)

    # Migration Info
    migration_name = Column(String(200), nullable=False)
    migration_type = Column(String(50), nullable=False)  # 'create', 'alter', 'drop'

    # Version Info
    from_version = Column(Integer)
    to_version = Column(Integer, nullable=False)

    # SQL Scripts
    up_script = Column(Text, nullable=False)  # SQL to apply migration
    down_script = Column(Text)  # SQL to rollback migration

    # Execution
    status = Column(String(50), default="pending")  # 'pending', 'running', 'completed', 'failed', 'rolled_back'
    executed_at = Column(DateTime)
    execution_time_ms = Column(Integer)
    error_message = Column(Text)

    # Metadata
    changes = Column(JSONB)  # Detailed change log

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(GUID, ForeignKey("users.id"))

    # Relationships
    entity = relationship("EntityDefinition", back_populates="migrations")

    # Table constraints
    __table_args__ = (
        Index("idx_entity_migrations_entity", "entity_id"),
        Index("idx_entity_migrations_status", "status"),
    )
