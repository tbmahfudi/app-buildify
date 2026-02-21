"""
Lookup Configuration - Pydantic Schemas

Request/Response schemas for the Lookup Configuration API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ==================== Lookup Configuration Schemas ====================

class LookupConfigurationBase(BaseModel):
    """Base schema for lookup configurations"""
    name: str = Field(..., max_length=100)
    label: str = Field(..., max_length=200)
    description: Optional[str] = None
    source_type: str = Field(..., description="entity, custom_query, static_list, api")
    source_entity_id: Optional[UUID] = None
    display_field: Optional[str] = None
    value_field: str = "id"
    additional_display_fields: List[str] = Field(default_factory=list)
    custom_query: Optional[str] = None
    query_parameters: Dict[str, Any] = Field(default_factory=dict)
    static_options: List[Dict[str, Any]] = Field(default_factory=list)
    api_endpoint: Optional[str] = None
    api_method: str = "GET"
    api_headers: Dict[str, str] = Field(default_factory=dict)
    api_response_mapping: Dict[str, Any] = Field(default_factory=dict)
    default_filter: Dict[str, Any] = Field(default_factory=dict)
    allow_user_filter: bool = True
    filter_fields: List[str] = Field(default_factory=list)
    default_sort_field: Optional[str] = None
    default_sort_order: str = "ASC"
    allow_user_sort: bool = True
    display_template: Optional[str] = None
    placeholder_text: Optional[str] = None
    empty_message: str = "No options available"
    enable_search: bool = True
    search_fields: List[str] = Field(default_factory=list)
    min_search_length: int = 3
    search_debounce_ms: int = 300
    enable_autocomplete: bool = False
    autocomplete_min_chars: int = 2
    autocomplete_max_results: int = 10
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    lazy_load: bool = False
    page_size: int = 50
    is_dependent: bool = False
    parent_lookup_id: Optional[UUID] = None
    dependency_mapping: Dict[str, Any] = Field(default_factory=dict)
    allow_create_new: bool = False
    create_entity_id: Optional[UUID] = None
    allow_multiple: bool = False
    max_selections: Optional[int] = None
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class LookupConfigurationCreate(LookupConfigurationBase):
    """Schema for creating a lookup configuration"""
    module_id: Optional[UUID] = None


class LookupConfigurationUpdate(BaseModel):
    """Schema for updating a lookup configuration"""
    module_id: Optional[UUID] = None
    label: Optional[str] = None
    description: Optional[str] = None
    display_field: Optional[str] = None
    value_field: Optional[str] = None
    additional_display_fields: Optional[List[str]] = None
    custom_query: Optional[str] = None
    query_parameters: Optional[Dict[str, Any]] = None
    static_options: Optional[List[Dict[str, Any]]] = None
    default_filter: Optional[Dict[str, Any]] = None
    filter_fields: Optional[List[str]] = None
    default_sort_field: Optional[str] = None
    default_sort_order: Optional[str] = None
    display_template: Optional[str] = None
    placeholder_text: Optional[str] = None
    enable_search: Optional[bool] = None
    search_fields: Optional[List[str]] = None
    enable_caching: Optional[bool] = None
    cache_ttl_seconds: Optional[int] = None
    is_active: Optional[bool] = None
    meta_data: Optional[Dict[str, Any]] = None


class LookupConfigurationResponse(LookupConfigurationBase):
    """Schema for lookup configuration response"""
    id: UUID
    tenant_id: Optional[UUID]  # NULL for platform-level lookup configurations
    module_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    is_deleted: bool

    class Config:
        from_attributes = True


# ==================== Lookup Data Schemas ====================

class LookupDataItem(BaseModel):
    """Schema for a single lookup data item"""
    value: Any
    label: str
    additional_data: Optional[Dict[str, Any]] = None


class LookupDataResponse(BaseModel):
    """Schema for lookup data response"""
    items: List[LookupDataItem]
    total_count: int
    page: int
    page_size: int
    has_more: bool


# ==================== Cascading Lookup Rule Schemas ====================

class CascadingLookupRuleBase(BaseModel):
    """Base schema for cascading lookup rules"""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    parent_lookup_id: UUID
    child_lookup_id: UUID
    filter_type: str = "field_match"
    parent_field: Optional[str] = None
    child_filter_field: Optional[str] = None
    custom_filter_expression: Optional[str] = None
    clear_on_parent_change: bool = True
    auto_select_if_single: bool = False


class CascadingLookupRuleCreate(CascadingLookupRuleBase):
    """Schema for creating a cascading lookup rule"""
    pass


class CascadingLookupRuleUpdate(BaseModel):
    """Schema for updating a cascading lookup rule"""
    description: Optional[str] = None
    filter_type: Optional[str] = None
    parent_field: Optional[str] = None
    child_filter_field: Optional[str] = None
    custom_filter_expression: Optional[str] = None
    clear_on_parent_change: Optional[bool] = None
    auto_select_if_single: Optional[bool] = None
    is_active: Optional[bool] = None


class CascadingLookupRuleResponse(CascadingLookupRuleBase):
    """Schema for cascading lookup rule response"""
    id: UUID
    tenant_id: Optional[UUID]  # NULL for platform-level cascading rules
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]

    class Config:
        from_attributes = True
