from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class FieldMetadata(BaseModel):
    """Single field metadata"""
    field: str
    title: str
    type: str  # text, number, date, boolean, select, etc.
    required: bool = False
    readonly: bool = False
    default: Optional[Any] = None
    validators: Optional[Dict[str, Any]] = None
    widget: Optional[str] = None  # Custom widget type
    options: Optional[List[Dict[str, Any]]] = None  # For select fields
    rbac_view: Optional[List[str]] = None  # Roles that can view
    rbac_edit: Optional[List[str]] = None  # Roles that can edit

class ColumnMetadata(BaseModel):
    """Table column metadata"""
    field: str
    title: str
    sortable: bool = True
    filterable: bool = True
    width: Optional[int] = None
    format: Optional[str] = None  # date, currency, etc.
    rbac_view: Optional[List[str]] = None

class TableConfig(BaseModel):
    """Table/Grid configuration"""
    columns: List[ColumnMetadata]
    default_sort: Optional[List[List[str]]] = None  # [["field", "asc"]]
    default_filters: Optional[Dict[str, Any]] = None
    page_size: int = 25
    actions: Optional[List[str]] = None  # view, edit, delete

class FormConfig(BaseModel):
    """Form configuration"""
    fields: List[FieldMetadata]
    layout: Optional[str] = "vertical"  # vertical, horizontal, grid
    sections: Optional[List[Dict[str, Any]]] = None
    
class EntityMetadataResponse(BaseModel):
    """Complete entity metadata"""
    entity_name: str
    display_name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    table: TableConfig
    form: FormConfig
    permissions: Optional[Dict[str, List[str]]] = None  # {role: [actions]}
    version: int
    is_active: bool
    
    class Config:
        from_attributes = True

class EntityMetadataCreate(BaseModel):
    entity_name: str
    display_name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    table_config: TableConfig
    form_config: FormConfig
    permissions: Optional[Dict[str, List[str]]] = None

class EntityMetadataUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    table_config: Optional[TableConfig] = None
    form_config: Optional[FormConfig] = None
    permissions: Optional[Dict[str, List[str]]] = None

class EntityListResponse(BaseModel):
    """List of available entities"""
    entities: List[str]
    total: int