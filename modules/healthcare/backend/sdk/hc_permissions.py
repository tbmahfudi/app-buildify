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

    Clinic owner has a NULL branch_id sentinel row. When a ``branch_id`` is given, that
    sentinel grants owner ONLY for branches in the owner's OWN Company — Company is the
    isolation boundary under the shared SaaS tenant (ADR-HC-010). Otherwise a matching
    branch-specific staff row is used.

    Returns None if no matching row found (caller has no HC role for that branch).
    """
    from sqlalchemy import text

    if branch_id is not None:
        # Branch-scoped check. The clinic_owner sentinel (branch_id IS NULL) is fenced to
        # the owner's Company: it only authorizes for branches whose platform Company
        # matches the sentinel's company_id. WITHOUT this join, any clinic_owner could act
        # on ANY other Company's clinic simply by passing its branch_id — a confirmed
        # cross-company account-takeover vector via routes_household.staff_link_account
        # (ADR-HC-010: Company is the isolation boundary). A sentinel with a NULL
        # company_id is malformed and fails closed (grants nothing here).
        owner_row = db.execute(
            text(
                "SELECT 1 FROM hc_branch_staff s "
                "JOIN hc_branches b ON b.id = :bid AND b.tenant_id = :tid "
                "WHERE s.tenant_id = :tid AND s.user_id = :uid AND s.branch_id IS NULL "
                "AND s.role = 'clinic_owner' AND s.status = 'active' AND s.is_active = true "
                "AND s.company_id IS NOT NULL AND s.company_id = b.platform_company_id "
                "LIMIT 1"
            ),
            {"tid": tenant_id, "uid": user_id, "bid": branch_id},
        ).fetchone()
        if owner_row:
            return HCRole.clinic_owner

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

    # No branch context: "is this user a clinic owner at all?" The sentinel answers yes;
    # any branch/Company-specific operation the caller performs must scope itself (a
    # branch-scoped caller passes branch_id and hits the Company-fenced path above).
    owner_row = db.execute(
        text(
            "SELECT role FROM hc_branch_staff "
            "WHERE tenant_id = :tid AND user_id = :uid AND branch_id IS NULL "
            "AND role = 'clinic_owner' AND status = 'active' AND is_active = true "
            "LIMIT 1"
        ),
        {"tid": tenant_id, "uid": user_id},
    ).fetchone()

    if owner_row:
        return HCRole.clinic_owner

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
