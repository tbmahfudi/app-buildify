from __future__ import annotations
from contextlib import contextmanager
from sqlalchemy.orm import Query
from typing import Any


class TenantScopeMissingError(Exception):
    pass


def apply_tenant_scope(query: Query, model: Any, user: Any) -> Query:
    """Apply tenant_id filter. No-op for superusers and non-tenant-scoped models."""
    if getattr(user, 'is_superuser', False):
        return query
    if not hasattr(model, 'tenant_id'):
        return query
    tenant_id = getattr(user, 'tenant_id', None)
    if tenant_id is None:
        raise TenantScopeMissingError(f"No tenant_id on user when querying {model.__name__}")
    return query.filter(model.tenant_id == tenant_id)


def tenant_scope_dependency(user):
    """FastAPI dependency — validates user has tenant context. Returns user."""
    if not getattr(user, 'is_superuser', False) and getattr(user, 'tenant_id', None) is None:
        raise TenantScopeMissingError("Request has no tenant context")
    return user


@contextmanager
def with_admin_cross_tenant_scope(user, admin_reason: str, audit_log_fn=None):
    """Context manager for legitimate cross-tenant reads. Superuser only, audit-logged."""
    if not getattr(user, 'is_superuser', False):
        raise PermissionError("Cross-tenant scope requires superuser")
    if not admin_reason:
        raise ValueError("admin_reason is required for cross-tenant scope")
    if audit_log_fn:
        audit_log_fn(action='tenant.cross_scope.enter', details={'reason': admin_reason})
    try:
        yield
    finally:
        if audit_log_fn:
            audit_log_fn(action='tenant.cross_scope.exit', details={'reason': admin_reason})
