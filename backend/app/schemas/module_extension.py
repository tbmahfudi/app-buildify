"""
Module Extension Schemas

Pydantic schemas for module extension API operations.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import re


# ===== Entity Extension Schemas =====

class EntityExtensionFieldSchema(BaseModel):
    """Schema for a field in an entity extension"""
    name: str = Field(..., min_length=1, max_length=100, description="Field name (lowercase, alphanumeric, underscore)")
    type: str = Field(..., description="Field type (string, text, integer, decimal, boolean, date, datetime, json)")
    max_length: Optional[int] = Field(None, description="Max length for string fields")
    precision: Optional[int] = Field(None, description="Precision for decimal fields")
    scale: Optional[int] = Field(None, description="Scale for decimal fields")
    label: str = Field(..., description="Display label for field")
    description: Optional[str] = Field(None, description="Field description")
    required: bool = Field(default=False, description="Whether field is required")
    default_value: Optional[Any] = Field(None, description="Default value")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate field name format"""
        if not re.match(r'^[a-z][a-z0-9_]*$', v):
            raise ValueError(
                "Field name must start with a letter and contain only lowercase letters, numbers, and underscores"
            )
        return v

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """Validate field type"""
        valid_types = ['string', 'text', 'integer', 'decimal', 'boolean', 'date', 'datetime', 'json']
        if v not in valid_types:
            raise ValueError(f"Invalid field type. Must be one of: {', '.join(valid_types)}")
        return v


class EntityExtensionCreate(BaseModel):
    """Schema for creating an entity extension"""
    extending_module_id: str = Field(..., description="Module creating the extension")
    target_entity_id: str = Field(..., description="Entity being extended")
    extension_fields: List[EntityExtensionFieldSchema] = Field(..., min_length=1, description="Fields to add")


class EntityExtensionResponse(BaseModel):
    """Schema for entity extension response"""
    id: str
    extending_module: Dict[str, Any]
    target_entity: Dict[str, Any]
    extension_table: str
    extension_fields: List[Dict[str, Any]]
    is_active: bool
    created_at: Optional[str]

    model_config = {"from_attributes": True}


# ===== Screen Extension Schemas =====

class ScreenExtensionCreate(BaseModel):
    """Schema for creating a screen extension"""
    extending_module_id: str = Field(..., description="Module creating the extension")
    target_module_id: str = Field(..., description="Module owning the screen")
    target_screen: str = Field(..., min_length=1, max_length=100, description="Screen identifier (e.g., 'employee_detail')")
    extension_type: str = Field(..., description="Extension type (tab, section, widget, action)")
    extension_config: Dict[str, Any] = Field(..., description="Extension configuration")
    position: int = Field(default=999, ge=0, description="Display order")
    required_permission: Optional[str] = Field(None, max_length=200, description="Permission required to see extension")

    @field_validator('extension_type')
    @classmethod
    def validate_extension_type(cls, v):
        """Validate extension type"""
        valid_types = ['tab', 'section', 'widget', 'action']
        if v not in valid_types:
            raise ValueError(f"Invalid extension_type. Must be one of: {', '.join(valid_types)}")
        return v

    @field_validator('extension_config')
    @classmethod
    def validate_extension_config(cls, v, info):
        """Validate extension configuration based on type"""
        extension_type = info.data.get('extension_type')

        if extension_type == 'tab':
            # Tab must have label and component_path
            if 'label' not in v:
                raise ValueError("Tab extension must have 'label' in config")
            if 'component_path' not in v:
                raise ValueError("Tab extension must have 'component_path' in config")

        elif extension_type == 'section':
            # Section must have label
            if 'label' not in v:
                raise ValueError("Section extension must have 'label' in config")

        elif extension_type == 'widget':
            # Widget must have component_path
            if 'component_path' not in v:
                raise ValueError("Widget extension must have 'component_path' in config")

        elif extension_type == 'action':
            # Action must have label and action_handler
            if 'label' not in v:
                raise ValueError("Action extension must have 'label' in config")
            if 'action_handler' not in v:
                raise ValueError("Action extension must have 'action_handler' in config")

        return v


class ScreenExtensionResponse(BaseModel):
    """Schema for screen extension response"""
    id: str
    extending_module: Dict[str, Any]
    target_screen: str
    extension_type: str
    extension_config: Dict[str, Any]
    position: int
    required_permission: Optional[str]

    model_config = {"from_attributes": True}


# ===== Menu Extension Schemas =====

class MenuExtensionCreate(BaseModel):
    """Schema for creating a menu extension"""
    extending_module_id: str = Field(..., description="Module creating the extension")
    target_module_id: Optional[str] = Field(None, description="Module to add menu to (None = root menu)")
    target_menu_item: Optional[str] = Field(None, max_length=100, description="Parent menu item (None = top level)")
    menu_config: Dict[str, Any] = Field(..., description="Menu configuration")
    position: int = Field(default=999, ge=0, description="Display order")
    required_permission: Optional[str] = Field(None, max_length=200, description="Permission required to see menu")

    @field_validator('menu_config')
    @classmethod
    def validate_menu_config(cls, v):
        """Validate menu configuration"""
        # Menu config must have label
        if 'label' not in v:
            raise ValueError("Menu config must have 'label'")

        # If type is submenu, must have items
        if v.get('type') == 'submenu':
            if 'items' not in v or not v['items']:
                raise ValueError("Submenu type must have 'items' array")

        # If type is link, must have route
        if v.get('type') == 'link':
            if 'route' not in v:
                raise ValueError("Link type must have 'route'")

        return v


class MenuExtensionResponse(BaseModel):
    """Schema for menu extension response"""
    id: str
    extending_module: Dict[str, Any]
    target_menu_item: Optional[str]
    menu_config: Dict[str, Any]
    position: int
    required_permission: Optional[str]

    model_config = {"from_attributes": True}


# ===== Common Response Schemas =====

class ExtensionOperationResponse(BaseModel):
    """Schema for extension operation response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
