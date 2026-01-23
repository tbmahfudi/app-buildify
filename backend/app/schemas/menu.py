"""
Pydantic schemas for menu management with RBAC
"""

from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class MenuItemBase(BaseModel):
    """Base menu item schema"""
    code: str = Field(..., description="Unique identifier for menu item", max_length=100)
    title: str = Field(..., description="Display title", max_length=100)
    icon: Optional[str] = Field(None, description="Icon class or emoji", max_length=100)
    icon_color_primary: Optional[str] = Field(None, description="Primary color for duo-tone icons (e.g., '#3b82f6')", max_length=20)
    icon_color_secondary: Optional[str] = Field(None, description="Secondary color for duo-tone icons (e.g., '#93c5fd')", max_length=20)
    route: Optional[str] = Field(None, description="Frontend route", max_length=255)
    description: Optional[str] = Field(None, description="Menu item description")
    permission: Optional[str] = Field(None, description="Required permission (e.g., 'users:read:tenant')", max_length=200)
    required_roles: Optional[List[str]] = Field(None, description="Required roles (user needs at least one)")
    order: int = Field(0, description="Display order")
    target: str = Field("_self", description="Link target (_self, _blank, modal)", max_length=50)
    is_active: bool = Field(True, description="Is menu item active")
    is_visible: bool = Field(True, description="Is menu item visible")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata and custom properties")


class MenuItemCreate(MenuItemBase):
    """Schema for creating a menu item"""
    parent_id: Optional[UUID | str] = Field(None, description="Parent menu item ID (for submenus)")
    tenant_id: Optional[UUID | str] = Field(None, description="Tenant ID (null for system menus, auto-set for non-superusers)")
    module_code: Optional[str] = Field(None, description="Module code if menu is from a module", max_length=100)
    is_system: bool = Field(True, description="Is this a system menu item")


class MenuItemUpdate(BaseModel):
    """Schema for updating a menu item"""
    title: Optional[str] = Field(None, max_length=100)
    icon: Optional[str] = Field(None, max_length=100)
    icon_color_primary: Optional[str] = Field(None, max_length=20)
    icon_color_secondary: Optional[str] = Field(None, max_length=20)
    route: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    permission: Optional[str] = Field(None, max_length=200)
    required_roles: Optional[List[str]] = None
    order: Optional[int] = None
    target: Optional[str] = Field(None, max_length=50)
    parent_id: Optional[UUID | str] = None
    is_active: Optional[bool] = None
    is_visible: Optional[bool] = None
    extra_data: Optional[Dict[str, Any]] = None


class MenuItemResponse(MenuItemBase):
    """Schema for menu item response"""
    id: UUID | str
    parent_id: Optional[UUID | str] = None
    tenant_id: Optional[UUID | str] = None
    module_code: Optional[str] = None
    is_system: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    children: Optional[List['MenuItemResponse']] = Field(default_factory=list, description="Child menu items")

    @field_serializer('id', 'parent_id', 'tenant_id')
    def serialize_uuid(self, value: UUID | str | None) -> str | None:
        """Convert UUID to string for JSON serialization"""
        if value is None:
            return None
        return str(value)

    class Config:
        from_attributes = True


class MenuItemTree(BaseModel):
    """Schema for menu item in tree structure (for end users)"""
    id: UUID | str
    code: str
    title: str
    icon: Optional[str] = None
    icon_color_primary: Optional[str] = None
    icon_color_secondary: Optional[str] = None
    route: Optional[str] = None
    order: int
    target: str
    extra_data: Optional[Dict[str, Any]] = None
    children: Optional[List['MenuItemTree']] = Field(default_factory=list)

    @field_serializer('id')
    def serialize_uuid(self, value: UUID | str) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value)

    class Config:
        from_attributes = True


class MenuReorderItem(BaseModel):
    """Schema for reordering menu items"""
    id: UUID | str = Field(..., description="Menu item ID")
    order: int = Field(..., description="New order position")


class MenuReorderRequest(BaseModel):
    """Request to reorder multiple menu items"""
    items: List[MenuReorderItem] = Field(..., description="List of menu items with new orders")


class MenuItemListResponse(BaseModel):
    """Response for list of menu items"""
    items: List[MenuItemResponse]
    total: int


class UserMenuResponse(BaseModel):
    """Response for user's accessible menu"""
    menu: List[MenuItemTree]
    total: int


class MenuOperationResponse(BaseModel):
    """Response from menu operation"""
    success: bool
    message: str
    menu_item: Optional[MenuItemResponse] = None
    items_synced: Optional[int] = None  # For sync operations


# Update forward references
MenuItemResponse.model_rebuild()
MenuItemTree.model_rebuild()
