"""
backend/app/core/scope.py
Legacy shim — re-exports everything from backend.app.core.tenant.scope.

Existing code that imports from backend.app.core.scope continues to work
unchanged. New code should import from backend.app.core.tenant directly.
"""

try:
    # Canonical location when the package root is ``app`` (production / tests).
    from app.core.tenant.scope import (  # noqa: F401
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
except ModuleNotFoundError:  # pragma: no cover - alt root where ``backend`` is a package
    from backend.app.core.tenant.scope import (  # noqa: F401
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
]
