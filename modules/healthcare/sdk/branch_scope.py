"""
Healthcare SDK — Branch-level session scoping.

T-HC-006

BranchScopeListener is the branch-level analogue of the platform TenantScopeListener.
It uses SQLAlchemy SessionEvents.do_orm_execute to enforce branch_id filtering on
all models tagged with __branch_scoped__ = True.

healthcare_branch_session FastAPI dependency:
  - Reads X-Branch-ID header (required for non-clinic-owner calls)
  - Verifies caller has access to that branch (hc_branch_staff row or is clinic_owner)
  - Sets PostgreSQL session vars: app.tenant_id and app.branch_id via SET LOCAL
  - Raises HTTP 422 if header missing or access denied

Clinic owner bypass: pass X-Branch-ID: ALL to skip branch filtering.
"""
from __future__ import annotations

import logging
from typing import Generator, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import event, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_BRANCH_SCOPE_ATTR = "_branch_scope"


class BranchScopeMissingError(Exception):
    """Raised when a branch-scoped ORM query is executed without branch_id set."""


class BranchScopeListener:
    """
    SQLAlchemy ORM execute listener for branch-level isolation.

    For models with ``__branch_scoped__ = True``:
      - Verifies that ``session._branch_scope`` is set before any ORM execute.
      - Raises ``BranchScopeMissingError`` if the scope is missing.
      - If ``session._branch_scope == 'ALL'`` (clinic owner bypass), skips filtering.

    The actual column-level filtering is enforced by PostgreSQL RLS policies
    (applied via Alembic migrations, see rls_policies.py). This listener provides
    the application-layer fail-fast guard.

    Install once when the healthcare module mounts::

        BranchScopeListener.install(engine)
    """

    @classmethod
    def install(cls, engine) -> None:
        """Register the do_orm_execute listener on the given engine."""
        event.listen(Session, "do_orm_execute", cls._on_orm_execute)
        logger.info("BranchScopeListener installed")

    @staticmethod
    def _on_orm_execute(orm_execute_state) -> None:
        """
        Called before every ORM SELECT/UPDATE/DELETE.

        If the mapped entity has ``__branch_scoped__ = True``:
          - Raises BranchScopeMissingError if _branch_scope is not set on the session.
          - Returns without filtering if _branch_scope == 'ALL' (clinic owner).
        """
        try:
            entities = orm_execute_state.all_mappers
        except Exception:
            return

        for mapper in entities:
            model = mapper.class_
            if not getattr(model, "__branch_scoped__", False):
                continue

            session = orm_execute_state.session
            branch_scope: Optional[str] = getattr(session, _BRANCH_SCOPE_ATTR, None)

            if branch_scope is None:
                raise BranchScopeMissingError(
                    f"Query on branch-scoped model {model.__name__!r} without branch "
                    "scope set. Use healthcare_branch_session() dependency."
                )

            if branch_scope == "ALL":
                # Clinic owner — allowed without branch filter injection
                # (RLS policy handles the actual DB filtering with 'ALL' sentinel)
                return

            # Branch filter injection is handled by PostgreSQL RLS policies.
            # The session variable app.branch_id is set by healthcare_branch_session.
            return  # only check once per query


def set_branch_scope(session: Session, branch_id: str) -> None:
    """Bind a branch_id to this session (called by healthcare_branch_session)."""
    setattr(session, _BRANCH_SCOPE_ATTR, str(branch_id))


def clear_branch_scope(session: Session) -> None:
    """Remove branch binding (called on session cleanup)."""
    if hasattr(session, _BRANCH_SCOPE_ATTR):
        delattr(session, _BRANCH_SCOPE_ATTR)


def healthcare_branch_session(
    x_branch_id: Optional[str] = Header(None, alias="X-Branch-ID"),
    db: Session = Depends(_tenant_scoped_session),
    current_user=Depends(_real_get_current_user),
) -> Generator[Session, None, None]:
    """
    FastAPI dependency — yields a SQLAlchemy session scoped to both tenant and branch.

    1. Validates X-Branch-ID header (raises HTTP 422 if absent for non-owners).
    2. Verifies the caller has a row in hc_branch_staff for the requested branch,
       OR is a clinic_owner (which sets branch_id = 'ALL').
    3. Sets PostgreSQL session vars: SET LOCAL app.tenant_id and app.branch_id.
    4. Yields the session; BranchScopeListener enforces the scope on ORM queries.

    Clinic owner bypass: X-Branch-ID: ALL skips per-branch verification.
    """
    from modules.healthcare.sdk._branch_access import verify_branch_access

    # Determine effective branch_id
    is_clinic_owner = _is_clinic_owner(current_user)

    if x_branch_id is None:
        if is_clinic_owner:
            # Clinic owners can operate without a branch header (gets ALL scope)
            effective_branch_id = "ALL"
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="X-Branch-ID header is required for branch-scoped endpoints",
            )
    elif x_branch_id == "ALL":
        if not is_clinic_owner:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="X-Branch-ID: ALL is only permitted for clinic owners",
            )
        effective_branch_id = "ALL"
    else:
        # Verify the user has access to this specific branch
        has_access = verify_branch_access(
            db=db,
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            branch_id=x_branch_id,
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Access to this branch is not permitted",
            )
        effective_branch_id = x_branch_id

    # Set PostgreSQL session-level variables for RLS enforcement
    tenant_id = str(current_user.tenant_id) if current_user.tenant_id else ""
    try:
        db.execute(text("SELECT set_config('app.tenant_id', :val, true)"), {"val": str(tenant_id)})
        db.execute(text("SELECT set_config('app.branch_id', :val, true)"), {"val": str(effective_branch_id)})
    except Exception as exc:
        logger.warning("Could not set PostgreSQL session vars: %s", exc)

    # Set Python-layer scope for BranchScopeListener
    set_branch_scope(db, effective_branch_id)

    try:
        yield db
    finally:
        clear_branch_scope(db)


def _is_clinic_owner(user) -> bool:
    """Check if user has the clinic_owner role."""
    try:
        roles = user.get_roles() if hasattr(user, "get_roles") else set()
        return "clinic_owner" in roles
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Deferred imports to avoid circular dependencies
# ---------------------------------------------------------------------------

from modules.sdk.dependencies import tenant_scoped_session as _tenant_scoped_session
from modules.sdk.dependencies import get_current_user as _real_get_current_user


__all__ = [
    "BranchScopeListener",
    "BranchScopeMissingError",
    "healthcare_branch_session",
    "set_branch_scope",
    "clear_branch_scope",
]
