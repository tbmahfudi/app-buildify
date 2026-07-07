"""
Healthcare SDK — RBAC middleware for staff role enforcement.

T-HC-013

HCRole enum covers all healthcare staff roles.
has_hc_permission() is a FastAPI dependency factory that reads the caller's
role from hc_branch_staff and enforces branch-level access rules.

Clinic owner: branch_id IS NULL sentinel → access to all branches.
Branch-scoped staff: only their assigned branch.
Patient JWT: always rejected on clinic endpoints.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, Union

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session, get_current_user


class HCRole(str, Enum):
    clinic_owner = "clinic_owner"
    branch_manager = "branch_manager"
    doctor = "doctor"
    nurse = "nurse"
    pharmacist = "pharmacist"
    lab_tech = "lab_tech"
    billing_staff = "billing_staff"


def get_caller_hc_role(
    db: Session,
    user_id: str,
    tenant_id: str,
    branch_id: Optional[str] = None,
) -> Optional[HCRole]:
    """
    Query hc_branch_staff to find the caller's role.

    Clinic owner has a NULL branch_id sentinel row — detected first.
    If branch_id is provided, also checks for a matching branch-specific row.

    Returns None if no matching row found (caller has no HC role).
    """
    from sqlalchemy import text

    # Check for clinic_owner (NULL branch_id sentinel)
    owner_row = db.execute(
        text(
            "SELECT role FROM hc_branch_staff "
            "WHERE tenant_id = :tid AND user_id = :uid AND branch_id IS NULL "
            "AND status = 'active' AND is_active = true "
            "LIMIT 1"
        ),
        {"tid": tenant_id, "uid": user_id},
    ).fetchone()

    if owner_row and owner_row[0] == HCRole.clinic_owner:
        return HCRole.clinic_owner

    if branch_id is not None:
        branch_row = db.execute(
            text(
                "SELECT role FROM hc_branch_staff "
                "WHERE tenant_id = :tid AND user_id = :uid AND branch_id = :bid "
                "AND status = 'active' AND is_active = true "
                "LIMIT 1"
            ),
            {"tid": tenant_id, "uid": user_id, "bid": branch_id},
        ).fetchone()

        if branch_row:
            try:
                return HCRole(branch_row[0])
            except ValueError:
                return None

    return None


def has_hc_permission(
    allowed_roles: Union[HCRole, list[HCRole]],
    require_branch_id: Optional[str] = None,
):
    """
    FastAPI dependency factory — enforces HC RBAC.

    Args:
        allowed_roles: Role or list of roles permitted to call this endpoint.
        require_branch_id: If provided, must be a path/query param name containing
            the branch_id to scope the check. When None, only tenant-level checks apply.

    Usage::

        @router.get("/branches")
        async def list_branches(
            _=Depends(has_hc_permission([HCRole.clinic_owner, HCRole.branch_manager])),
        ):
            ...
    """
    if isinstance(allowed_roles, HCRole):
        allowed_roles = [allowed_roles]
    allowed_set = set(allowed_roles)

    def _checker(
        db: Session = Depends(tenant_scoped_session),
        current_user=Depends(get_current_user),
    ):
        # Reject patient JWTs at the clinic boundary
        user_roles = getattr(current_user, "roles", []) or []
        if user_roles == ["patient"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Staff credentials required for this endpoint",
            )

        # hc_branch_staff is on the shared SAAS tenant (ADR-HC-010) — resolve the role
        # against it, not the staff user's platform tenant.
        from modules.healthcare.sdk.hc_tenant import resolve_shared_tenant_id

        caller_role = get_caller_hc_role(
            db=db,
            user_id=str(current_user.id),
            tenant_id=resolve_shared_tenant_id(db),
            branch_id=require_branch_id,
        )

        if caller_role is None or caller_role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient healthcare role",
            )

        return caller_role

    return _checker


__all__ = [
    "HCRole",
    "get_caller_hc_role",
    "has_hc_permission",
]
