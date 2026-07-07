"""
Healthcare — Organization: Departments & Platform-Org Linkage API.

Epic-08 / ADR-HC-005.

    POST   /api/v1/modules/healthcare/branches/{branch_id}/departments
    GET    /api/v1/modules/healthcare/branches/{branch_id}/departments
    PUT    /api/v1/modules/healthcare/branches/{branch_id}/departments/{department_id}
    POST   /api/v1/modules/healthcare/branches/{branch_id}/departments/{department_id}/members
    DELETE /api/v1/modules/healthcare/branches/{branch_id}/departments/{department_id}/members/{member_id}
    PUT    /api/v1/modules/healthcare/branches/{branch_id}/org-linkage
    GET    /api/v1/modules/healthcare/branches/{branch_id}/org-linkage
    GET    /api/v1/modules/healthcare/branches/{branch_id}/org-context
"""
from __future__ import annotations
from modules.healthcare.sdk.hc_tenant import hc_shared_tenant_id

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from modules.sdk.dependencies import get_current_user
from modules.healthcare.models import HCBranch, HCDepartment, HCProvider, HCProviderDepartment
from modules.healthcare.schemas.department import (
    DepartmentCreate,
    DepartmentMemberCreate,
    DepartmentMemberResponse,
    DepartmentResponse,
    DepartmentUpdate,
    OrgContextResponse,
    OrgLinkageResponse,
    OrgLinkageUpdate,
)
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission
from modules.healthcare.sdk.branch_scope import healthcare_branch_session
from modules.healthcare.sdk.phi_audit import write_event_audit

router = APIRouter(
    prefix="/api/v1/modules/healthcare",
    tags=["healthcare-organization"],
)

_MANAGE = [HCRole.clinic_owner, HCRole.branch_manager]


def _audit(db, request, current_user, branch_id, event, entity_type, entity_id):
    write_event_audit(
        db=db,
        actor_id=str(current_user.id),
        actor_type="staff",
        event_type=event,
        entity_type=entity_type,
        entity_id=str(entity_id),
        tenant_id=hc_shared_tenant_id(),
        branch_id=str(branch_id),
        ip=request.client.host if request.client else None,
        ua=request.headers.get("user-agent"),
    )


def _get_branch(db, current_user, branch_id) -> HCBranch:
    branch = (
        db.query(HCBranch)
        .filter(HCBranch.id == str(branch_id), HCBranch.tenant_id == hc_shared_tenant_id())
        .first()
    )
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return branch


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------

@router.post(
    "/branches/{branch_id}/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a department in a branch",
)
async def create_department(
    branch_id: uuid.UUID,
    payload: DepartmentCreate,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission(_MANAGE)),
):
    _get_branch(db, current_user, branch_id)
    dup = (
        db.query(HCDepartment)
        .filter(
            HCDepartment.tenant_id == hc_shared_tenant_id(),
            HCDepartment.branch_id == str(branch_id),
            HCDepartment.code == payload.code,
        )
        .first()
    )
    if dup:
        raise HTTPException(status_code=409, detail="Department code already exists in this branch")

    dept = HCDepartment(
        tenant_id=hc_shared_tenant_id(),
        branch_id=str(branch_id),
        code=payload.code,
        name=payload.name,
        kind=payload.kind,
        is_active=payload.is_active,
    )
    db.add(dept)
    db.flush()
    _audit(db, request, current_user, branch_id, "department.created", "department", dept.id)
    db.commit()
    db.refresh(dept)
    return dept


@router.get(
    "/branches/{branch_id}/departments",
    response_model=list[DepartmentResponse],
    summary="List departments in a branch",
)
async def list_departments(
    branch_id: uuid.UUID,
    kind: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission(list(HCRole))),
):
    query = db.query(HCDepartment).filter(
        HCDepartment.tenant_id == hc_shared_tenant_id(),
        HCDepartment.branch_id == str(branch_id),
    )
    if kind:
        query = query.filter(HCDepartment.kind == kind)
    if is_active is not None:
        query = query.filter(HCDepartment.is_active == is_active)
    if q:
        like = f"%{q}%"
        query = query.filter(HCDepartment.name.ilike(like) | HCDepartment.code.ilike(like))
    offset = (page - 1) * page_size
    return query.order_by(HCDepartment.kind, HCDepartment.name).offset(offset).limit(page_size).all()


@router.put(
    "/branches/{branch_id}/departments/{department_id}",
    response_model=DepartmentResponse,
    summary="Update or disable a department",
)
async def update_department(
    branch_id: uuid.UUID,
    department_id: uuid.UUID,
    payload: DepartmentUpdate,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission(_MANAGE)),
):
    dept = (
        db.query(HCDepartment)
        .filter(
            HCDepartment.id == str(department_id),
            HCDepartment.tenant_id == hc_shared_tenant_id(),
            HCDepartment.branch_id == str(branch_id),
        )
        .first()
    )
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(dept, field, value)

    _audit(db, request, current_user, branch_id, "department.updated", "department", dept.id)
    db.commit()
    db.refresh(dept)
    return dept


# ---------------------------------------------------------------------------
# Provider <-> department assignment
# ---------------------------------------------------------------------------

@router.post(
    "/branches/{branch_id}/departments/{department_id}/members",
    response_model=DepartmentMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a provider to a department",
)
async def add_department_member(
    branch_id: uuid.UUID,
    department_id: uuid.UUID,
    payload: DepartmentMemberCreate,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission(_MANAGE)),
):
    tenant_id = hc_shared_tenant_id()
    dept = (
        db.query(HCDepartment)
        .filter(
            HCDepartment.id == str(department_id),
            HCDepartment.tenant_id == tenant_id,
            HCDepartment.branch_id == str(branch_id),
        )
        .first()
    )
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    provider = (
        db.query(HCProvider)
        .filter(
            HCProvider.id == payload.provider_id,
            HCProvider.tenant_id == tenant_id,
            HCProvider.branch_id == str(branch_id),
        )
        .first()
    )
    if not provider:
        raise HTTPException(status_code=422, detail="Provider not found in this branch")

    dup = (
        db.query(HCProviderDepartment)
        .filter(
            HCProviderDepartment.tenant_id == tenant_id,
            HCProviderDepartment.branch_id == str(branch_id),
            HCProviderDepartment.provider_id == payload.provider_id,
            HCProviderDepartment.department_id == str(department_id),
        )
        .first()
    )
    if dup:
        raise HTTPException(status_code=409, detail="Provider already assigned to this department")

    # At most one primary/home department per provider per branch.
    if payload.is_primary:
        db.query(HCProviderDepartment).filter(
            HCProviderDepartment.tenant_id == tenant_id,
            HCProviderDepartment.branch_id == str(branch_id),
            HCProviderDepartment.provider_id == payload.provider_id,
            HCProviderDepartment.is_primary == True,
        ).update({"is_primary": False})

    member = HCProviderDepartment(
        tenant_id=tenant_id,
        branch_id=str(branch_id),
        provider_id=payload.provider_id,
        department_id=str(department_id),
        is_primary=payload.is_primary,
    )
    db.add(member)
    db.flush()
    _audit(db, request, current_user, branch_id, "department.member_added", "provider_department", member.id)
    db.commit()
    db.refresh(member)
    return member


@router.delete(
    "/branches/{branch_id}/departments/{department_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a provider from a department",
)
async def remove_department_member(
    branch_id: uuid.UUID,
    department_id: uuid.UUID,
    member_id: uuid.UUID,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission(_MANAGE)),
):
    member = (
        db.query(HCProviderDepartment)
        .filter(
            HCProviderDepartment.id == str(member_id),
            HCProviderDepartment.tenant_id == hc_shared_tenant_id(),
            HCProviderDepartment.branch_id == str(branch_id),
            HCProviderDepartment.department_id == str(department_id),
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Assignment not found")
    db.delete(member)
    _audit(db, request, current_user, branch_id, "department.member_removed", "provider_department", member_id)
    db.commit()


# ---------------------------------------------------------------------------
# Platform-org linkage
# ---------------------------------------------------------------------------

def _platform_row(db, table: str, entity_id, tenant_id: Optional[str] = None):
    sql = f"SELECT id, tenant_id FROM {table} WHERE id = :id"
    row = db.execute(text(sql), {"id": str(entity_id)}).fetchone()
    return row


@router.put(
    "/branches/{branch_id}/org-linkage",
    response_model=OrgLinkageResponse,
    summary="Link this clinic/branch to the platform org hierarchy",
)
async def set_org_linkage(
    branch_id: uuid.UUID,
    payload: OrgLinkageUpdate,
    request: Request,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission([HCRole.clinic_owner])),
):
    branch = _get_branch(db, current_user, branch_id)
    tenant_id = hc_shared_tenant_id()

    # Validate each referenced platform entity exists and (company/branch) shares tenant.
    if payload.platform_company_id is not None:
        row = _platform_row(db, "companies", payload.platform_company_id)
        if not row:
            raise HTTPException(status_code=422, detail="Platform company not found")
        if str(row[1]) != tenant_id:
            raise HTTPException(status_code=422, detail="Platform company belongs to another tenant")
    if payload.platform_branch_id is not None:
        row = _platform_row(db, "branches", payload.platform_branch_id)
        if not row:
            raise HTTPException(status_code=422, detail="Platform branch not found")
        if str(row[1]) != tenant_id:
            raise HTTPException(status_code=422, detail="Platform branch belongs to another tenant")
    if payload.platform_department_id is not None:
        row = _platform_row(db, "departments", payload.platform_department_id)
        if not row:
            raise HTTPException(status_code=422, detail="Platform department not found")

    branch.platform_company_id = str(payload.platform_company_id) if payload.platform_company_id else None
    branch.platform_branch_id = str(payload.platform_branch_id) if payload.platform_branch_id else None
    branch.platform_department_id = str(payload.platform_department_id) if payload.platform_department_id else None

    _audit(db, request, current_user, branch_id, "branch.org_linked", "branch", branch.id)
    db.commit()
    db.refresh(branch)
    return OrgLinkageResponse(
        branch_id=branch.id,
        platform_company_id=branch.platform_company_id,
        platform_branch_id=branch.platform_branch_id,
        platform_department_id=branch.platform_department_id,
    )


@router.get(
    "/branches/{branch_id}/org-linkage",
    response_model=OrgLinkageResponse,
    summary="Get this branch's platform-org linkage",
)
async def get_org_linkage(
    branch_id: uuid.UUID,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission(list(HCRole))),
):
    branch = _get_branch(db, current_user, branch_id)
    return OrgLinkageResponse(
        branch_id=branch.id,
        platform_company_id=branch.platform_company_id,
        platform_branch_id=branch.platform_branch_id,
        platform_department_id=branch.platform_department_id,
    )


@router.get(
    "/branches/{branch_id}/org-context",
    response_model=OrgContextResponse,
    summary="Get the resolved platform-org context (names) for this branch",
)
async def get_org_context(
    branch_id: uuid.UUID,
    db: Session = Depends(healthcare_branch_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission(list(HCRole))),
):
    branch = _get_branch(db, current_user, branch_id)
    ctx = OrgContextResponse(branch_id=branch.id, linked=bool(branch.platform_branch_id))

    if branch.platform_company_id:
        row = db.execute(
            text("SELECT id, name FROM companies WHERE id = :id"),
            {"id": str(branch.platform_company_id)},
        ).fetchone()
        if row:
            ctx.company_id, ctx.company_name = row[0], row[1]
    if branch.platform_branch_id:
        row = db.execute(
            text("SELECT id, name FROM branches WHERE id = :id"),
            {"id": str(branch.platform_branch_id)},
        ).fetchone()
        if row:
            ctx.platform_branch_id, ctx.platform_branch_name = row[0], row[1]
    if branch.platform_department_id:
        row = db.execute(
            text("SELECT id, name FROM departments WHERE id = :id"),
            {"id": str(branch.platform_department_id)},
        ).fetchone()
        if row:
            ctx.department_id, ctx.department_name = row[0], row[1]

    return ctx
