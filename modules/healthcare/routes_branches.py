"""
Healthcare — Branch CRUD API.

T-HC-010

POST   /api/v1/modules/healthcare/branches       — create; Clinic Owner; max 20 per tenant
GET    /api/v1/modules/healthcare/branches       — list; Clinic Owner, Branch Manager
GET    /api/v1/modules/healthcare/branches/{id}  — single; any staff
PUT    /api/v1/modules/healthcare/branches/{id}  — update; Clinic Owner, Branch Manager
DELETE /api/v1/modules/healthcare/branches/{id}  — soft delete; Clinic Owner
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session, get_current_user
from modules.healthcare.models import HCBranch
from modules.healthcare.schemas.branch import BranchCreate, BranchUpdate, BranchResponse
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.phi_audit import write_event_audit

router = APIRouter(
    prefix="/api/v1/modules/healthcare",
    tags=["healthcare-branches"],
)

MAX_BRANCHES_PER_TENANT = 20


@router.post(
    "/branches",
    response_model=BranchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new branch",
)
async def create_branch(
    payload: BranchCreate,
    request: Request,
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission(HCRole.clinic_owner)),
):
    # Application-layer enforcement: max 20 branches per tenant
    existing_count = (
        db.query(HCBranch)
        .filter(
            HCBranch.tenant_id == str(current_user.tenant_id),
            HCBranch.deleted_at.is_(None),
        )
        .count()
    )
    if existing_count >= MAX_BRANCHES_PER_TENANT:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Maximum {MAX_BRANCHES_PER_TENANT} branches per tenant reached",
        )

    branch = HCBranch(
        tenant_id=str(current_user.tenant_id),
        **payload.model_dump(),
    )
    db.add(branch)
    db.flush()

    write_event_audit(
        db=db,
        actor_id=str(current_user.id),
        actor_type="staff",
        event_type="branch.created",
        entity_type="branch",
        entity_id=str(branch.id),
        tenant_id=str(current_user.tenant_id),
        ip=request.client.host if request.client else None,
        ua=request.headers.get("user-agent"),
    )

    db.commit()
    db.refresh(branch)
    return branch


@router.get(
    "/branches",
    response_model=list[BranchResponse],
    summary="List all branches for tenant",
)
async def list_branches(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission([HCRole.clinic_owner, HCRole.branch_manager])),
):
    offset = (page - 1) * page_size
    branches = (
        db.query(HCBranch)
        .filter(
            HCBranch.tenant_id == str(current_user.tenant_id),
            HCBranch.deleted_at.is_(None),
        )
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return branches


@router.get(
    "/branches/{branch_id}",
    response_model=BranchResponse,
    summary="Get a single branch",
)
async def get_branch(
    branch_id: uuid.UUID,
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission(list(HCRole))),  # any staff role
):
    branch = (
        db.query(HCBranch)
        .filter(
            HCBranch.id == branch_id,
            HCBranch.tenant_id == str(current_user.tenant_id),
            HCBranch.deleted_at.is_(None),
        )
        .first()
    )
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return branch


@router.put(
    "/branches/{branch_id}",
    response_model=BranchResponse,
    summary="Update a branch",
)
async def update_branch(
    branch_id: uuid.UUID,
    payload: BranchUpdate,
    request: Request,
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission([HCRole.clinic_owner, HCRole.branch_manager])),
):
    branch = (
        db.query(HCBranch)
        .filter(
            HCBranch.id == branch_id,
            HCBranch.tenant_id == str(current_user.tenant_id),
            HCBranch.deleted_at.is_(None),
        )
        .first()
    )
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(branch, field, value)

    write_event_audit(
        db=db,
        actor_id=str(current_user.id),
        actor_type="staff",
        event_type="branch.updated",
        entity_type="branch",
        entity_id=str(branch.id),
        tenant_id=str(current_user.tenant_id),
        branch_id=str(branch_id),
        ip=request.client.host if request.client else None,
        ua=request.headers.get("user-agent"),
    )

    db.commit()
    db.refresh(branch)
    return branch


@router.delete(
    "/branches/{branch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a branch",
)
async def delete_branch(
    branch_id: uuid.UUID,
    request: Request,
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission(HCRole.clinic_owner)),
):
    branch = (
        db.query(HCBranch)
        .filter(
            HCBranch.id == branch_id,
            HCBranch.tenant_id == str(current_user.tenant_id),
            HCBranch.deleted_at.is_(None),
        )
        .first()
    )
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    branch.deleted_at = datetime.utcnow()

    write_event_audit(
        db=db,
        actor_id=str(current_user.id),
        actor_type="staff",
        event_type="branch.deleted",
        entity_type="branch",
        entity_id=str(branch.id),
        tenant_id=str(current_user.tenant_id),
        branch_id=str(branch_id),
        ip=request.client.host if request.client else None,
        ua=request.headers.get("user-agent"),
    )

    db.commit()
