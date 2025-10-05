from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class UserSettingsResponse(BaseModel):
    """User settings response"""
    theme: str
    language: str
    timezone: str
    density: str
    preferences: Optional[Dict[str, Any]] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserSettingsUpdate(BaseModel):
    """Update user settings"""
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    density: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class TenantSettingsResponse(BaseModel):
    """Tenant settings response"""
    tenant_id: str
    tenant_name: Optional[str]
    logo_url: Optional[str]
    primary_color: Optional[str]
    secondary_color: Optional[str]
    theme_config: Optional[Dict[str, Any]] = None
    enabled_features: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TenantSettingsUpdate(BaseModel):
    """Update tenant settings"""
    tenant_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    theme_config: Optional[Dict[str, Any]] = None
    enabled_features: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None