from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any, Literal, Union
from datetime import datetime

class FieldMetadata(BaseModel):
    """Single field metadata for form configuration"""
    field: str = Field(..., description="Field name/key")
    title: str = Field(..., description="Display title for the field")
    type: str = Field(..., description="Field type: text, number, date, boolean, select, etc.")
    required: bool = Field(default=False, description="Whether field is required")
    readonly: bool = Field(default=False, description="Whether field is read-only")
    default: Optional[Any] = Field(None, description="Default value")
    validators: Optional[Dict[str, Any]] = Field(None, description="Validation rules")
    widget: Optional[str] = Field(None, description="Custom widget type")
    options: Optional[List[Dict[str, Any]]] = Field(None, description="Options for select fields")
    rbac_view: Optional[List[str]] = Field(None, description="Roles that can view this field")
    rbac_edit: Optional[List[str]] = Field(None, description="Roles that can edit this field")
    help_text: Optional[str] = Field(None, description="Help text for the field")
    placeholder: Optional[str] = Field(None, description="Placeholder text")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "field": "email",
                "title": "Email Address",
                "type": "email",
                "required": True,
                "readonly": False,
                "validators": {"pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"},
                "help_text": "Enter your email address"
            }
        }
    )

class ColumnMetadata(BaseModel):
    """Table column metadata for grid configuration"""
    field: str = Field(..., description="Field name/key")
    title: str = Field(..., description="Column header title")
    sortable: bool = Field(default=True, description="Whether column is sortable")
    filterable: bool = Field(default=True, description="Whether column is filterable")
    width: Optional[int] = Field(None, description="Column width in pixels")
    format: Optional[str] = Field(None, description="Format type: date, currency, percentage, etc.")
    rbac_view: Optional[List[str]] = Field(None, description="Roles that can view this column")
    align: Optional[Literal["left", "center", "right"]] = Field(None, description="Column alignment")

class TableConfig(BaseModel):
    """Table/Grid configuration"""
    columns: List[ColumnMetadata] = Field(default_factory=list, description="Column definitions")
    default_sort: Optional[Union[List[List[str]], Dict[str, str]]] = Field(None, description="Default sort configuration [[field, asc/desc]] or {field, direction}")
    default_filters: Optional[Dict[str, Any]] = Field(None, description="Default filters")
    page_size: int = Field(default=25, ge=1, le=100, description="Default page size")
    actions: Optional[Union[List[str], Dict[str, bool]]] = Field(None, description="Available actions: view, edit, delete")
    selectable: bool = Field(default=False, description="Whether rows are selectable")
    exportable: bool = Field(default=False, description="Whether data can be exported")

    @field_validator('default_sort', mode='before')
    @classmethod
    def normalize_default_sort(cls, v):
        """Convert dict format {field, direction} to list format [[field, direction]]"""
        if v is None:
            return None
        if isinstance(v, dict):
            # Handle {field: "created_at", direction: "desc"} format
            field = v.get('field')
            direction = v.get('direction', 'asc')
            if field:
                return [[field, direction]]
            return None
        return v

    @field_validator('actions', mode='before')
    @classmethod
    def normalize_actions(cls, v):
        """Convert dict format {view: True, edit: True} to list format ["view", "edit"]"""
        if v is None:
            return None
        if isinstance(v, dict):
            # Handle {view: True, edit: True, delete: True} format
            return [action for action, enabled in v.items() if enabled]
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "columns": [
                    {"field": "name", "title": "Name", "sortable": True},
                    {"field": "email", "title": "Email", "sortable": True}
                ],
                "default_sort": [["name", "asc"]],
                "page_size": 25,
                "actions": ["view", "edit", "delete"],
                "selectable": True
            }
        }
    )

class FormConfig(BaseModel):
    """Form configuration"""
    fields: List[FieldMetadata] = Field(..., description="Field definitions")
    layout: Optional[Literal["vertical", "horizontal", "grid"]] = Field(default="vertical", description="Form layout type")
    sections: Optional[List[Dict[str, Any]]] = Field(None, description="Form sections for grouping fields")
    submit_button_text: Optional[str] = Field(None, description="Custom submit button text")
    cancel_button_text: Optional[str] = Field(None, description="Custom cancel button text")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fields": [
                    {
                        "field": "name",
                        "title": "Name",
                        "type": "text",
                        "required": True
                    }
                ],
                "layout": "vertical",
                "submit_button_text": "Save",
                "cancel_button_text": "Cancel"
            }
        }
    )

class EntityMetadataResponse(BaseModel):
    """Complete entity metadata response"""
    id: str = Field(..., description="Metadata unique identifier")
    entity_name: str = Field(..., description="Entity name (unique identifier)")
    display_name: str = Field(..., description="Human-readable display name")
    description: Optional[str] = Field(None, description="Entity description")
    icon: Optional[str] = Field(None, description="Icon name or URL")
    table: TableConfig = Field(..., description="Table/grid configuration")
    form: FormConfig = Field(..., description="Form configuration")
    permissions: Optional[Dict[str, List[str]]] = Field(None, description="Role-based permissions {role: [actions]}")
    version: int = Field(..., description="Version number for optimistic locking")
    is_active: bool = Field(..., description="Whether entity is active")
    is_system: bool = Field(default=False, description="Whether entity is system-defined")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Created by user ID")
    updated_by: Optional[str] = Field(None, description="Last updated by user ID")

    model_config = ConfigDict(from_attributes=True)

class EntityMetadataCreate(BaseModel):
    """Create entity metadata"""
    entity_name: str = Field(..., max_length=100, description="Entity name (unique)")
    display_name: str = Field(..., max_length=255, description="Display name")
    description: Optional[str] = Field(None, description="Entity description")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name")
    table_config: TableConfig = Field(..., description="Table configuration")
    form_config: FormConfig = Field(..., description="Form configuration")
    permissions: Optional[Dict[str, List[str]]] = Field(None, description="Role permissions")
    is_system: bool = Field(default=False, description="System entity flag")

class EntityMetadataUpdate(BaseModel):
    """Update entity metadata"""
    display_name: Optional[str] = Field(None, max_length=255, description="Display name")
    description: Optional[str] = Field(None, description="Entity description")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name")
    table_config: Optional[TableConfig] = Field(None, description="Table configuration")
    form_config: Optional[FormConfig] = Field(None, description="Form configuration")
    permissions: Optional[Dict[str, List[str]]] = Field(None, description="Role permissions")
    is_active: Optional[bool] = Field(None, description="Active status")

class EntityListResponse(BaseModel):
    """List of available entities"""
    entities: List[str] = Field(..., description="List of entity names")
    total: int = Field(..., description="Total count of entities")

class EntityMetadataDetailResponse(BaseModel):
    """Detailed entity metadata with additional info"""
    metadata: EntityMetadataResponse = Field(..., description="Entity metadata")
    statistics: Optional[Dict[str, Any]] = Field(None, description="Usage statistics")
    last_accessed: Optional[datetime] = Field(None, description="Last accessed timestamp")