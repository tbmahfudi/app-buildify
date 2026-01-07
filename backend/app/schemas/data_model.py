"""
Data Model Designer - Pydantic Schemas

Request/Response schemas for the Data Model Designer API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ==================== Field Definition Schemas ====================

class FieldDefinitionBase(BaseModel):
    """Base schema for field definitions"""
    name: str = Field(..., max_length=100, description="Technical field name (snake_case)")
    label: str = Field(..., max_length=200, description="Display label")
    description: Optional[str] = None
    help_text: Optional[str] = None
    field_type: str = Field(..., description="Field type (string, integer, date, etc.)")
    data_type: str = Field(..., description="Database type (VARCHAR, INTEGER, etc.)")
    is_required: bool = False
    is_unique: bool = False
    is_indexed: bool = False
    is_nullable: bool = True
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    max_value: Optional[float] = None
    min_value: Optional[float] = None
    decimal_places: Optional[int] = None
    default_value: Optional[str] = None
    default_expression: Optional[str] = None
    validation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    allowed_values: Optional[Dict[str, Any]] = None
    display_order: int = 0
    is_readonly: bool = False
    is_system: bool = False
    is_calculated: bool = False
    calculation_formula: Optional[str] = None
    input_type: Optional[str] = None
    placeholder: Optional[str] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    reference_entity_id: Optional[UUID] = None
    reference_field: Optional[str] = None
    relationship_type: Optional[str] = None
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class FieldDefinitionCreate(FieldDefinitionBase):
    """Schema for creating a field definition"""
    pass


class FieldDefinitionUpdate(BaseModel):
    """Schema for updating a field definition"""
    label: Optional[str] = None
    description: Optional[str] = None
    help_text: Optional[str] = None
    is_required: Optional[bool] = None
    is_readonly: Optional[bool] = None
    display_order: Optional[int] = None
    validation_rules: Optional[List[Dict[str, Any]]] = None
    allowed_values: Optional[Dict[str, Any]] = None
    input_type: Optional[str] = None
    placeholder: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class FieldDefinitionResponse(FieldDefinitionBase):
    """Schema for field definition response"""
    id: UUID
    entity_id: UUID
    tenant_id: Optional[UUID]  # NULL for platform-level fields
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    is_deleted: bool

    class Config:
        from_attributes = True


# ==================== Entity Definition Schemas ====================

class EntityDefinitionBase(BaseModel):
    """Base schema for entity definitions"""
    name: str = Field(..., max_length=100, description="Technical entity name (snake_case)")
    label: str = Field(..., max_length=200, description="Display label")
    plural_label: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    entity_type: str = "custom"
    category: Optional[str] = None
    table_name: str = Field(..., max_length=100, description="Database table name")
    schema_name: str = "public"
    is_audited: bool = True
    is_versioned: bool = False
    supports_soft_delete: bool = True
    supports_attachments: bool = True
    supports_comments: bool = True
    primary_field: Optional[str] = None
    default_sort_field: Optional[str] = None
    default_sort_order: str = "ASC"
    records_per_page: int = 25
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class EntityDefinitionCreate(EntityDefinitionBase):
    """Schema for creating an entity definition"""
    fields: Optional[List[FieldDefinitionCreate]] = Field(default_factory=list)


class EntityDefinitionUpdate(BaseModel):
    """Schema for updating an entity definition"""
    label: Optional[str] = None
    plural_label: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    is_audited: Optional[bool] = None
    supports_soft_delete: Optional[bool] = None
    supports_attachments: Optional[bool] = None
    supports_comments: Optional[bool] = None
    primary_field: Optional[str] = None
    default_sort_field: Optional[str] = None
    default_sort_order: Optional[str] = None
    records_per_page: Optional[int] = None
    is_active: Optional[bool] = None
    meta_data: Optional[Dict[str, Any]] = None


class EntityDefinitionResponse(EntityDefinitionBase):
    """Schema for entity definition response"""
    id: UUID
    tenant_id: Optional[UUID]  # NULL for platform-level entities
    status: str
    is_active: bool
    version: int
    parent_version_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    deleted_at: Optional[datetime]
    is_deleted: bool
    fields: List[FieldDefinitionResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ==================== Relationship Definition Schemas ====================

class RelationshipDefinitionBase(BaseModel):
    """Base schema for relationship definitions"""
    name: str = Field(..., max_length=100)
    label: str = Field(..., max_length=200)
    description: Optional[str] = None
    relationship_type: str = Field(..., description="one-to-many, many-to-many, one-to-one")
    source_entity_id: UUID
    source_field_name: Optional[str] = None
    target_entity_id: UUID
    target_field_name: Optional[str] = None
    junction_table_name: Optional[str] = None
    junction_source_field: Optional[str] = None
    junction_target_field: Optional[str] = None
    on_delete: str = "NO ACTION"
    on_update: str = "NO ACTION"
    is_active: bool = True
    display_in_source: bool = True
    display_in_target: bool = True
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class RelationshipDefinitionCreate(RelationshipDefinitionBase):
    """Schema for creating a relationship definition"""
    pass


class RelationshipDefinitionUpdate(BaseModel):
    """Schema for updating a relationship definition"""
    label: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    display_in_source: Optional[bool] = None
    display_in_target: Optional[bool] = None
    meta_data: Optional[Dict[str, Any]] = None


class RelationshipDefinitionResponse(RelationshipDefinitionBase):
    """Schema for relationship definition response"""
    id: UUID
    tenant_id: Optional[UUID]  # NULL for platform-level relationships
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    is_deleted: bool

    class Config:
        from_attributes = True


# ==================== Index Definition Schemas ====================

class IndexDefinitionBase(BaseModel):
    """Base schema for index definitions"""
    name: str = Field(..., max_length=100)
    index_type: str = "btree"
    field_names: List[str] = Field(..., description="Array of field names")
    is_unique: bool = False
    is_partial: bool = False
    where_clause: Optional[str] = None
    is_active: bool = True


class IndexDefinitionCreate(IndexDefinitionBase):
    """Schema for creating an index definition"""
    pass


class IndexDefinitionResponse(IndexDefinitionBase):
    """Schema for index definition response"""
    id: UUID
    entity_id: UUID
    tenant_id: Optional[UUID]  # NULL for platform-level indexes
    created_at: datetime
    created_by: Optional[UUID]
    is_deleted: bool

    class Config:
        from_attributes = True


# ==================== Migration Schemas ====================

class MigrationResponse(BaseModel):
    """Schema for migration response"""
    id: UUID
    entity_id: UUID
    tenant_id: Optional[UUID]  # NULL for platform-level migrations
    migration_name: str
    migration_type: str
    from_version: Optional[int]
    to_version: int
    up_script: str
    down_script: Optional[str]
    status: str
    executed_at: Optional[datetime]
    execution_time_ms: Optional[int]
    error_message: Optional[str]
    changes: Optional[Dict[str, Any]]
    created_at: datetime
    created_by: Optional[UUID]

    class Config:
        from_attributes = True


class SchemaPreviewResponse(BaseModel):
    """Schema for schema preview"""
    sql_script: str
    affected_tables: List[str]
    warnings: List[str] = Field(default_factory=list)
    estimated_impact: str


class PublishEntityRequest(BaseModel):
    """Schema for publishing an entity"""
    apply_migration: bool = True
    backup_data: bool = True


class PublishEntityResponse(BaseModel):
    """Schema for publish entity response"""
    entity_id: UUID
    migration_id: UUID
    status: str
    message: str
