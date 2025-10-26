from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, Literal
from datetime import datetime

class UserSettingsResponse(BaseModel):
    """User settings response"""
    id: str = Field(..., description="Settings unique identifier")
    user_id: str = Field(..., description="User ID")
    theme: str = Field(..., description="Theme preference (light/dark)")
    language: str = Field(..., description="Language code (e.g., en, es)")
    timezone: str = Field(..., description="Timezone (e.g., UTC, America/New_York)")
    density: str = Field(..., description="UI density (compact/normal/comfortable)")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Additional custom preferences")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)

class UserSettingsUpdate(BaseModel):
    """Update user settings"""
    theme: Optional[Literal["light", "dark"]] = Field(None, description="Theme preference")
    language: Optional[str] = Field(None, max_length=10, description="Language code")
    timezone: Optional[str] = Field(None, max_length=50, description="Timezone")
    density: Optional[Literal["compact", "normal", "comfortable"]] = Field(None, description="UI density")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Custom preferences")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "theme": "dark",
                "language": "en",
                "timezone": "UTC",
                "density": "normal",
                "preferences": {
                    "sidebar_collapsed": False,
                    "default_page_size": 25
                }
            }
        }
    )

class TenantSettingsResponse(BaseModel):
    """Tenant settings response"""
    id: str = Field(..., description="Settings unique identifier")
    tenant_id: str = Field(..., description="Tenant ID")
    tenant_name: Optional[str] = Field(None, description="Tenant display name")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    primary_color: Optional[str] = Field(None, description="Primary brand color (hex)")
    secondary_color: Optional[str] = Field(None, description="Secondary brand color (hex)")
    theme_config: Optional[Dict[str, Any]] = Field(None, description="Theme configuration (CSS variables)")
    enabled_features: Optional[Dict[str, Any]] = Field(None, description="Feature flags")
    settings: Optional[Dict[str, Any]] = Field(None, description="Miscellaneous settings")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    updated_by: Optional[str] = Field(None, description="Last updated by user ID")

    model_config = ConfigDict(from_attributes=True)

class TenantSettingsUpdate(BaseModel):
    """Update tenant settings"""
    tenant_name: Optional[str] = Field(None, max_length=255, description="Tenant display name")
    logo_url: Optional[str] = Field(None, max_length=500, description="Logo URL")
    primary_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="Primary color (hex)")
    secondary_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="Secondary color (hex)")
    theme_config: Optional[Dict[str, Any]] = Field(None, description="Theme configuration")
    enabled_features: Optional[Dict[str, Any]] = Field(None, description="Feature flags")
    settings: Optional[Dict[str, Any]] = Field(None, description="Miscellaneous settings")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tenant_name": "Acme Corporation",
                "logo_url": "https://example.com/logo.png",
                "primary_color": "#0066CC",
                "secondary_color": "#FF6600",
                "enabled_features": {
                    "advanced_reporting": True,
                    "api_access": True
                },
                "settings": {
                    "max_users": 100,
                    "data_retention_days": 365
                }
            }
        }
    )