"""
Healthcare — Branch staff assignment API.

T-HC-011

POST   /api/v1/modules/healthcare/branches/{branch_id}/staff
GET    /api/v1/modules/healthcare/branches/{branch_id}/staff
DELETE /api/v1/modules/healthcare/branches/{branch_id}/staff/{user_id}
POST   /api/v1/modules/healthcare/staff/accept-invitation/{token}
"""
from __future__ import annotations
from modules.healthcare.sdk.hc_tenant import hc_shared_tenant_id

import secrets
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session, get_current_user
from modules.healthcare.models import HCBranchStaff
from modules.healthcare.schemas.staff import StaffInvite, StaffResponse
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.phi_audit import write_event_audit

router = APIRouter(
    prefix="/api/v1/modules/healthcare",
    tags=["healthcare-staff"],
)


@router.post(
    "/branches/{branch_id}/staff",
    response_model=StaffResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite staff to a branch",
)
async def invite_staff(
    branch_id: uuid.UUID,
    payload: StaffInvite,
    request: Request,
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission([HCRole.clinic_owner, HCRole.branch_manager])),
):
    """
    Invite a user by email to join the branch with the specified role.
    Creates an hc_branch_staff row with status=pending and a secure invitation_token.
    The invitation token should be emailed to the user (email sending handled by a
    separate notification service, not in scope for this endpoint).
    """
    # Resolve user_id from email via platform users table (simplified lookup)
    from sqlalchemy import text
    user_row = db.execute(
        text("SELECT id FROM users WHERE email = :email AND tenant_id = :tid LIMIT 1"),
        {"email": payload.email, "tid": hc_shared_tenant_id()},
    ).fetchone()

    if user_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found in tenant",
        )
    target_user_id = str(user_row[0])

    # Check for duplicate
    existing = (
        db.query(HCBranchStaff)
        .filter(
            HCBranchStaff.tenant_id == hc_shared_tenant_id(),
            HCBranchStaff.branch_id == str(branch_id),
            HCBranchStaff.user_id == target_user_id,
            HCBranchStaff.role == payload.role,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Staff assignment already exists",
        )

    invitation_token = secrets.token_urlsafe(32)
    staff = HCBranchStaff(
        tenant_id=hc_shared_tenant_id(),
        branch_id=str(branch_id),
        user_id=target_user_id,
        role=payload.role,
        status="pending",
        invitation_token=invitation_token,
        invited_at=datetime.utcnow(),
    )
    db.add(staff)
    db.flush()

    write_event_audit(
        db=db,
        actor_id=str(current_user.id),
        actor_type="staff",
        event_type="staff.invited",
        entity_type="branch_staff",
        entity_id=str(staff.id),
        tenant_id=hc_shared_tenant_id(),
        branch_id=str(branch_id),
        ip=request.client.host if request.client else None,
        ua=request.headers.get("user-agent"),
    )

    db.commit()
    db.refresh(staff)
    return staff


@router.get(
    "/branches/{branch_id}/staff",
    response_model=list[StaffResponse],
    summary="List staff for a branch",
)
async def list_branch_staff(
    branch_id: uuid.UUID,
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission([HCRole.clinic_owner, HCRole.branch_manager])),
):
    staff = (
        db.query(HCBranchStaff)
        .filter(
            HCBranchStaff.tenant_id == hc_shared_tenant_id(),
            HCBranchStaff.branch_id == str(branch_id),
        )
        .all()
    )
    return staff


@router.delete(
    "/branches/{branch_id}/staff/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a staff member from a branch",
)
async def remove_staff(
    branch_id: uuid.UUID,
    user_id: str,
    request: Request,
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission(HCRole.clinic_owner)),
):
    staff = (
        db.query(HCBranchStaff)
        .filter(
            HCBranchStaff.tenant_id == hc_shared_tenant_id(),
            HCBranchStaff.branch_id == str(branch_id),
            HCBranchStaff.user_id == user_id,
        )
        .first()
    )
    if not staff:
        raise HTTPException(status_code=404, detail="Staff assignment not found")

    staff.status = "revoked"
    staff.is_active = False

    write_event_audit(
        db=db,
        actor_id=str(current_user.id),
        actor_type="staff",
        event_type="staff.removed",
        entity_type="branch_staff",
        entity_id=str(staff.id),
        tenant_id=hc_shared_tenant_id(),
        branch_id=str(branch_id),
        ip=request.client.host if request.client else None,
        ua=request.headers.get("user-agent"),
    )

    db.commit()


@router.post(
    "/staff/accept-invitation/{token}",
    response_model=StaffResponse,
    summary="Accept a branch staff invitation",
)
async def accept_invitation(
    token: str,
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
):
    staff = (
        db.query(HCBranchStaff)
        .filter(
            HCBranchStaff.invitation_token == token,
            HCBranchStaff.user_id == str(current_user.id),
            HCBranchStaff.status == "pending",
        )
        .first()
    )
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or already accepted",
        )

    staff.status = "active"
    staff.is_active = True
    staff.accepted_at = datetime.utcnow()
    staff.invitation_token = None

    db.commit()
    db.refresh(staff)
    return staff
