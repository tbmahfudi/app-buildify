"""
backend/app/core/tenant/scope.py
Centralized tenant scope helper for Epic 22.
"""

from __future__ import annotations

import inspect
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Generator
from uuid import UUID

from sqlalchemy.orm import Query

logger = logging.getLogger(__name__)

_current_tenant_id: ContextVar[UUID | None] = ContextVar("_current_tenant_id", default=None)


class TenantScopeNotSetError(Exception):
    """Raised when tenant scope is required but has not been set."""


TenantScopeMissingError = TenantScopeNotSetError


def set_tenant_scope(tenant_id: UUID) -> None:
    """Bind tenant_id to the current async/thread context."""
    _current_tenant_id.set(tenant_id)
    logger.debug("tenant_scope.set tenant_id=%s", tenant_id)


def get_tenant_scope() -> UUID:
    """Return the current tenant UUID; raises TenantScopeNotSetError if not set."""
    value = _current_tenant_id.get()
    if value is None:
        raise TenantScopeNotSetError(
            "Tenant scope is not set for the current request context. "
            "Use tenant_scoped_session() or with_tenant_scope() to establish scope."
        )
    return value


def clear_tenant_scope() -> None:
    """Remove the current tenant binding from the context."""
    _current_tenant_id.set(None)
    logger.debug("tenant_scope.clear")


@contextmanager
def with_tenant_scope(tenant_id: UUID) -> Generator[None, None, None]:
    """Set tenant scope for the duration of the block, then clear it."""
    token = _current_tenant_id.set(tenant_id)
    logger.debug("tenant_scope.enter tenant_id=%s", tenant_id)
    try:
        yield
    finally:
        _current_tenant_id.reset(token)
        logger.debug("tenant_scope.exit tenant_id=%s", tenant_id)


@contextmanager
def with_admin_cross_tenant_scope(
    user,
    admin_reason: str,
    audit_log_fn=None,
) -> Generator[None, None, None]:
    """Audit-logged bypass for legitimate cross-tenant admin reads.

    Sets the scope to the __superuser__ sentinel so the ORM listener skips
    per-tenant filtering.

    Args:
        user:          Must have is_superuser == True; raises PermissionError otherwise.
        admin_reason:  Non-empty string; raises ValueError if missing.
        audit_log_fn:  Optional callable(action: str, **kwargs). Writes
                       tenant.cross_scope.enter and tenant.cross_scope.exit
                       audit entries including calling stack frame.

    Raises:
        PermissionError: if user.is_superuser is not True.
        ValueError:      if admin_reason is empty or None.
    """
    if not getattr(user, "is_superuser", False):
        raise PermissionError("with_admin_cross_tenant_scope() requires a superuser account.")
    if not admin_reason:
        raise ValueError("admin_reason is required for cross-tenant scope.")

    caller_frame = inspect.stack()[2]
    caller_info = f"{caller_frame.filename}:{caller_frame.lineno} in {caller_frame.function}"

    if audit_log_fn is not None:
        audit_log_fn(
            action="tenant.cross_scope.enter",
            details={
                "reason": admin_reason,
                "caller": caller_info,
                "user_id": str(getattr(user, "id", "unknown")),
            },
        )

    token = _current_tenant_id.set("__superuser__")  # type: ignore[arg-type]
    logger.info("tenant_scope.cross_tenant_enter reason=%r caller=%s", admin_reason, caller_info)
    try:
        yield
    finally:
        _current_tenant_id.reset(token)
        logger.info(
            "tenant_scope.cross_tenant_exit reason=%r caller=%s",
            admin_reason,
            caller_info,
        )
        if audit_log_fn is not None:
            audit_log_fn(
                action="tenant.cross_scope.exit",
                details={
                    "reason": admin_reason,
                    "caller": caller_info,
                    "user_id": str(getattr(user, "id", "unknown")),
                },
            )


def apply_tenant_scope(query: Query, model, user) -> Query:
    """Add WHERE tenant_id = user.tenant_id to query.

    No-op when user.is_superuser is True or model lacks __tenant_scoped__ = True.
    Raises TenantScopeNotSetError when model is scoped but user has no tenant_id.
    """
    if getattr(user, "is_superuser", False):
        return query
    if not getattr(model, "__tenant_scoped__", False):
        return query
    tenant_id = getattr(user, "tenant_id", None)
    if tenant_id is None:
        raise TenantScopeNotSetError(f"User has no tenant_id when querying {model.__name__}")
    return query.filter(model.tenant_id == tenant_id)  # noqa: tenant-scope-ok


def apply_tenant_scope_by_id(query: Query, model, tenant_id) -> Query:
    """Add WHERE tenant_id = tenant_id using a bare UUID value.

    Use in static/class methods without a current_user. Raises
    TenantScopeNotSetError when tenant_id is None.
    """
    if not getattr(model, "__tenant_scoped__", False):
        return query
    if tenant_id is None:
        raise TenantScopeNotSetError(f"tenant_id is None when querying {model.__name__}")
    return query.filter(model.tenant_id == tenant_id)  # noqa: tenant-scope-ok


def tenant_scope_dependency(user):
    """FastAPI dependency that validates user carries tenant context. Returns user."""
    if not getattr(user, "is_superuser", False) and getattr(user, "tenant_id", None) is None:
        raise TenantScopeNotSetError("Request has no tenant context.")
    return user
