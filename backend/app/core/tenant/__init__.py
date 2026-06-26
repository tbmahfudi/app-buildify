"""
backend/app/core/tenant
Public API for the tenant scope helper (Epic 22).

Import from here rather than from the submodule directly:

    from backend.app.core.tenant import (
        apply_tenant_scope,
        apply_tenant_scope_by_id,
        with_tenant_scope,
        with_admin_cross_tenant_scope,
        set_tenant_scope,
        get_tenant_scope,
        clear_tenant_scope,
        tenant_scope_dependency,
        TenantScopeNotSetError,
        TenantScopeMissingError,
        tenant_scoped_session,
    )
"""
from .scope import (
    TenantScopeMissingError,
    TenantScopeNotSetError,
    apply_tenant_scope,
    apply_tenant_scope_by_id,
    clear_tenant_scope,
    get_tenant_scope,
    set_tenant_scope,
    tenant_scope_dependency,
    with_admin_cross_tenant_scope,
    with_tenant_scope,
)

# FastAPI dependency (ContextVar-based; T-22.007)
from .dependencies import tenant_scoped_session

__all__ = [
    "TenantScopeNotSetError",
    "TenantScopeMissingError",
    "apply_tenant_scope",
    "apply_tenant_scope_by_id",
    "clear_tenant_scope",
    "get_tenant_scope",
    "set_tenant_scope",
    "tenant_scope_dependency",
    "with_admin_cross_tenant_scope",
    "with_tenant_scope",
    "tenant_scoped_session",
]
