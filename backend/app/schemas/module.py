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


class ModuleRegistrationRequest(BaseModel):
    """Request from module to register itself with core platform"""
    manifest: Dict[str, Any] = Field(..., description="Full module manifest")
    backend_service_url: str = Field(..., description="URL of module backend service")
    health_check_url: Optional[str] = Field(None, description="Health check endpoint URL")


class ModuleRegistrationResponse(BaseModel):
    """Response to module registration request"""
    success: bool
    message: str
    module_name: str
    registered_at: datetime
    should_install: bool = Field(
        default=False,
        description="Whether module should run installation scripts"
    )


class ModuleHeartbeatRequest(BaseModel):
    """Heartbeat request from module"""
    module_name: str
    version: str
    status: str = Field(default="healthy", description="Module health status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional module metadata")


class ModuleHeartbeatResponse(BaseModel):
    """Response to heartbeat"""
    success: bool
    message: str
    last_seen: datetime


# ── Epic-23 additions ─────────────────────────────────────────────────────────

class ModuleErrorResponse(BaseModel):
    """Structured error body for /api/v1/modules endpoints (T-23.003)."""
    code: str
    message: str
    detail: Optional[Any] = None


class ActivationPreviewPermission(BaseModel):
    name: str
    description: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None


class ActivationPreviewMenuItem(BaseModel):
    label: str
    route: Optional[str] = None
    icon: Optional[str] = None


class ActivationPreviewDependency(BaseModel):
    name: str
    display_name: Optional[str] = None
    status: str  # "active" | "inactive" | "not_installed"
    required_version: Optional[str] = None


class ActivationPreviewResponse(BaseModel):
    """Response for GET /modules/{name}/activation-preview (T-23.002)."""
    module_name: str
    display_name: str
    permissions: List[ActivationPreviewPermission]
    menu_items: List[ActivationPreviewMenuItem]
    dependencies: List[ActivationPreviewDependency]
    # T-22.016: tenant DB provisioning status ('not_provisioned' when no row exists)
    tenant_db_status: Optional[str] = None


class ModuleListItemV2(BaseModel):
    """Module list item for GET /api/v1/modules (includes activation_status).

    T-23.018 — Story 23.4.1 backend AC.
    """
    id: str
    name: str
    display_name: str
    description: Optional[str] = None
    version: str
    category: Optional[str] = None
    status: str
    is_core: bool
    install_status: str = "ready"
    activation_status: str  # "active" | "inactive"
    permissions_added: List[Any] = Field(default_factory=list)
    menu_items_added: List[Any] = Field(default_factory=list)
    dependencies: List[Any] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ModulesListResponse(BaseModel):
    modules: List[ModuleListItemV2]
    total: int


class ModuleEnableResponse(BaseModel):
    """Response for POST /api/v1/modules/{module_id}/enable (T-23.020)."""
    status: str  # "active"
    permissions_added: List[str] = Field(default_factory=list)
    menu_items_added: List[str] = Field(default_factory=list)
    # T-22.014: DB provisioning status when module requires_tenant_db
    tenant_db_status: Optional[str] = None
    connection_secret_ref: Optional[str] = None


class TenantDBStatusResponse(BaseModel):
    """Response for GET /api/v1/modules/{module_id}/tenant-db-status (T-22.017)."""
    status: str
    connection_secret_ref: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


class ModuleDisableResponse(BaseModel):
    """Response for POST /api/v1/modules/{module_id}/disable (T-23.022)."""
    status: str  # "inactive"
    permissions_deactivated: List[str] = Field(default_factory=list)
    menu_items_deactivated: List[str] = Field(default_factory=list)


class ModuleDeactivateAllResponse(BaseModel):
    """Response for POST /api/v1/admin/modules/{module_id}/deactivate-all (T-23.024)."""
    status: str  # "deactivation_pending"
    tenants_deactivated: int
