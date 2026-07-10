"""
Healthcare — Branch CRUD API.

T-HC-010 / epic-20 Feature 20.2 (Company-scoped)

POST   /api/v1/modules/healthcare/branches       — create; Clinic Owner; max 20 per Company
GET    /api/v1/modules/healthcare/branches       — list; Clinic Owner, Branch Manager
GET    /api/v1/modules/healthcare/branches/{id}  — single; any staff
PUT    /api/v1/modules/healthcare/branches/{id}  — update; Clinic Owner, Branch Manager
DELETE /api/v1/modules/healthcare/branches/{id}  — soft delete; Clinic Owner

Company fencing (ADR-HC-010): all clinics share the SAAS tenant, so filtering by
tenant alone would leak every clinic's branches to every owner. Each query is fenced
to the caller's Company (hc_branches.platform_company_id) via resolve_caller_company_id,
which fails closed — a caller with no resolvable Company sees nothing. Each clinic site
IS a platform branch 1:1 (ADR-HC-005): create writes the platform `branches` row and
links it from hc_branches.
"""
from __future__ import annotations
from modules.healthcare.sdk.hc_tenant import hc_shared_tenant_id

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session, get_current_user
from modules.healthcare.models import HCBranch
from modules.healthcare.schemas.branch import BranchCreate, BranchUpdate, BranchResponse
from modules.healthcare.sdk.branch_scope import resolve_caller_company_id
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.phi_audit import write_event_audit

router = APIRouter(
    prefix="/api/v1/modules/healthcare",
    tags=["healthcare-branches"],
)

MAX_BRANCHES_PER_COMPANY = 20


def _require_caller_company(db: Session, current_user) -> str:
    """Resolve the caller's single Company id or fail closed (403).

    Every branch query is fenced to this Company so an owner/manager never sees or
    mutates another clinic's sites on the shared SaaS tenant (ADR-HC-010).
    """
    company_id = resolve_caller_company_id(db, str(current_user.id))
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No clinic Company resolved for this account",
        )
    return company_id


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
    company_id = _require_caller_company(db, current_user)

    # Max 20 branches per Company (was per-tenant; the tenant is now shared).
    existing_count = (
        db.query(HCBranch)
        .filter(
            HCBranch.platform_company_id == company_id,
            HCBranch.deleted_at.is_(None),
        )
        .count()
    )
    if existing_count >= MAX_BRANCHES_PER_COMPANY:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Maximum {MAX_BRANCHES_PER_COMPANY} branches per clinic reached",
        )

    # Branch slug must be unique within the Company (platform branches enforces
    # (company_id, code)); pre-check for a clean 409 rather than an IntegrityError.
    if db.execute(
        text("SELECT 1 FROM branches WHERE company_id = :cid AND code = :code"),
        {"cid": company_id, "code": payload.slug},
    ).fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="branch slug already exists in this clinic",
        )

    # ADR-HC-005: a clinic site IS a platform branch (1:1). Create the platform
    # `branches` row under the Company and link it from hc_branches.
    platform_branch_id = str(uuid.uuid4())
    db.execute(
        text(
            "INSERT INTO branches (id, company_id, code, name, tenant_id, is_active, is_headquarters) "
            "VALUES (:id, :cid, :code, :name, :tid, true, :hq)"
        ),
        {
            "id": platform_branch_id, "cid": company_id, "code": payload.slug,
            "name": payload.branch_name, "tid": hc_shared_tenant_id(),
            "hq": existing_count == 0,
        },
    )

    branch = HCBranch(
        id=str(uuid.uuid4()),  # explicit str id (generate_uuid() yields a UUID object,
                               # which makes refresh/compare emit varchar = uuid)
        tenant_id=hc_shared_tenant_id(),
        platform_company_id=company_id,
        platform_branch_id=platform_branch_id,
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
        tenant_id=hc_shared_tenant_id(),
        branch_id=str(branch.id),
        ip=request.client.host if request.client else None,
        ua=request.headers.get("user-agent"),
        metadata={"company_id": company_id, "platform_branch_id": platform_branch_id},
    )

    db.commit()
    db.refresh(branch)
    return branch


@router.get(
    "/branches",
    response_model=list[BranchResponse],
    summary="List branches for the caller's Company",
)
async def list_branches(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission([HCRole.clinic_owner, HCRole.branch_manager])),
):
    company_id = _require_caller_company(db, current_user)
    offset = (page - 1) * page_size
    branches = (
        db.query(HCBranch)
        .filter(
            HCBranch.platform_company_id == company_id,
            HCBranch.tenant_id == hc_shared_tenant_id(),
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
    company_id = _require_caller_company(db, current_user)
    branch = (
        db.query(HCBranch)
        .filter(
            HCBranch.id == str(branch_id),
            HCBranch.platform_company_id == company_id,
            HCBranch.tenant_id == hc_shared_tenant_id(),
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
    company_id = _require_caller_company(db, current_user)
    branch = (
        db.query(HCBranch)
        .filter(
            HCBranch.id == str(branch_id),
            HCBranch.platform_company_id == company_id,
            HCBranch.tenant_id == hc_shared_tenant_id(),
            HCBranch.deleted_at.is_(None),
        )
        .first()
    )
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(branch, field, value)

    # Keep the linked platform branch name in sync (ADR-HC-005 1:1).
    if "branch_name" in updates and branch.platform_branch_id:
        db.execute(
            text("UPDATE branches SET name = :name WHERE id = :id"),
            {"name": branch.branch_name, "id": str(branch.platform_branch_id)},
        )

    write_event_audit(
        db=db,
        actor_id=str(current_user.id),
        actor_type="staff",
        event_type="branch.updated",
        entity_type="branch",
        entity_id=str(branch.id),
        tenant_id=hc_shared_tenant_id(),
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
    company_id = _require_caller_company(db, current_user)
    branch = (
        db.query(HCBranch)
        .filter(
            HCBranch.id == str(branch_id),
            HCBranch.platform_company_id == company_id,
            HCBranch.tenant_id == hc_shared_tenant_id(),
            HCBranch.deleted_at.is_(None),
        )
        .first()
    )
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    branch.deleted_at = datetime.utcnow()
    # Deactivate the linked platform branch (ADR-HC-005 1:1).
    if branch.platform_branch_id:
        db.execute(
            text("UPDATE branches SET is_active = false WHERE id = :id"),
            {"id": str(branch.platform_branch_id)},
        )

    write_event_audit(
        db=db,
        actor_id=str(current_user.id),
        actor_type="staff",
        event_type="branch.deleted",
        entity_type="branch",
        entity_id=str(branch.id),
        tenant_id=hc_shared_tenant_id(),
        branch_id=str(branch_id),
        ip=request.client.host if request.client else None,
        ua=request.headers.get("user-agent"),
    )

    db.commit()
