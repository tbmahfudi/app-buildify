"""
backend/app/core/tenant/dependencies.py
FastAPI dependency providing tenant-scoped SQLAlchemy sessions via ContextVar scope.
Story 22.3.2 / T-22.007
"""

from __future__ import annotations

from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.tenant.scope import (
    TenantScopeNotSetError,
    clear_tenant_scope,
    set_tenant_scope,
)
from app.models.user import User


def tenant_scoped_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Generator[Session, None, None]:
    """FastAPI dependency — yields a DB session with tenant scope set in the ContextVar.

    Sets tenant scope at request entry via set_tenant_scope(current_user.tenant_id)
    and clears it in the finally block unconditionally, preventing scope leakage
    between requests in async or threaded environments.

    Superusers get the "__superuser__" sentinel so the ORM listener (when installed)
    skips per-tenant filtering.

    Usage::

        @router.get("/things")
        def list_things(db: Session = Depends(tenant_scoped_session)):
            ...

    Raises:
        TenantScopeNotSetError: if a non-superuser has no tenant_id.
    """
    if current_user.is_superuser:
        tenant_id = "__superuser__"
    elif current_user.tenant_id:
        tenant_id = current_user.tenant_id
    else:
        raise TenantScopeNotSetError("Authenticated user has no tenant_id and is not a superuser.")

    set_tenant_scope(tenant_id)
    try:
        yield db
    finally:
        clear_tenant_scope()
