"""
Pydantic schemas for module management
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ModuleBase(BaseModel):
    """Base module schema"""
    name: str = Field(..., description="Module name (unique identifier)")
    display_name: str = Field(..., description="Human-readable name")
    version: str = Field(..., description="Module version (semver)")
    description: Optional[str] = Field(None, description="Module description")
    category: Optional[str] = Field(None, description="Module category")


class ModuleInfo(ModuleBase):
    """Detailed module information"""
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    license: Optional[str] = None
    is_installed: bool
    is_core: bool
    subscription_tier: Optional[str] = None
    dependencies: Optional[Dict[str, List[str]]] = None
    status: str
    homepage: Optional[str] = None
    repository: Optional[str] = None
    support_email: Optional[str] = None

    class Config:
        from_attributes = True


class ModuleListItem(BaseModel):
    """Module list item for overview"""
    name: str
    display_name: str
    version: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_installed: bool
    is_core: bool
    subscription_tier: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class ModuleInstallRequest(BaseModel):
    """Request to install a module"""
    module_name: str = Field(..., description="Name of module to install")


class ModuleUninstallRequest(BaseModel):
    """Request to uninstall a module"""
    module_name: str = Field(..., description="Name of module to uninstall")


class ModuleEnableRequest(BaseModel):
    """Request to enable a module for a tenant"""
    module_name: str = Field(..., description="Name of module to enable")
    tenant_id: Optional[str] = Field(
        None,
        description="Tenant ID to enable module for (superuser only, defaults to current user's tenant)"
    )
    configuration: Optional[Dict[str, Any]] = Field(
        None,
        description="Tenant-specific configuration (optional)"
    )


class ModuleDisableRequest(BaseModel):
    """Request to disable a module for a tenant"""
    module_name: str = Field(..., description="Name of module to disable")


class ModuleConfigurationUpdate(BaseModel):
    """Update module configuration for a tenant"""
    configuration: Dict[str, Any] = Field(..., description="New configuration values")


class TenantModuleInfo(BaseModel):
    """Information about a module enabled for a tenant"""
    module_name: str
    display_name: str
    version: str
    is_enabled: bool
    is_configured: bool
    configuration: Optional[Dict[str, Any]] = None
    enabled_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TenantModuleInfoWithTenant(BaseModel):
    """Information about a module enabled for a tenant (includes tenant info for superuser)"""
    module_name: str
    display_name: str
    version: str
    is_enabled: bool
    is_configured: bool
    configuration: Optional[Dict[str, Any]] = None
    enabled_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    tenant_id: str
    tenant_name: str
    tenant_code: str

    class Config:
        from_attributes = True


class ModuleOperationResponse(BaseModel):
    """Response from module operation"""
    success: bool
    message: str
    module_name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class AvailableModulesResponse(BaseModel):
    """Response containing list of available modules"""
    modules: List[ModuleListItem]
    total: int


class EnabledModulesResponse(BaseModel):
    """Response containing list of enabled modules for tenant"""
    modules: List[TenantModuleInfo]
    total: int


class AllTenantsModulesResponse(BaseModel):
    """Response containing list of enabled modules across all tenants (superuser only)"""
    modules: List[TenantModuleInfoWithTenant]
    total: int


class ModuleManifest(BaseModel):
    """Full module manifest"""
    name: str
    display_name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    compatibility: Optional[Dict[str, str]] = None
    dependencies: Optional[Dict[str, List[str]]] = None
    permissions: Optional[List[Dict[str, Any]]] = None
    default_roles: Optional[Dict[str, List[str]]] = None
    database: Optional[Dict[str, Any]] = None
    api: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    subscription_tier: Optional[str] = None
    pricing: Optional[Dict[str, Any]] = None
    installation: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    support_email: Optional[str] = None

    class Config:
        from_attributes = True
