"""
Healthcare — Audit log API.

T-HC-014

GET /api/v1/modules/healthcare/audit-log — Clinic Owner only; paginated.
No UPDATE or DELETE endpoints (append-only log).
"""
from __future__ import annotations
from modules.healthcare.sdk.hc_tenant import hc_shared_tenant_id

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from modules.sdk.dependencies import tenant_scoped_session, get_current_user
from modules.healthcare.models import HCAuditLog
from modules.healthcare.schemas.audit import AuditLogListResponse, AuditLogResponse
from modules.healthcare.sdk.hc_permissions import HCRole, has_hc_permission

router = APIRouter(
    prefix="/api/v1/modules/healthcare",
    tags=["healthcare-audit"],
)


@router.get(
    "/audit-log",
    response_model=AuditLogListResponse,
    summary="List audit log entries (Clinic Owner only)",
)
async def list_audit_log(
    from_dt: Optional[datetime] = Query(None, alias="from"),
    to_dt: Optional[datetime] = Query(None, alias="to"),
    event_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(tenant_scoped_session),
    current_user=Depends(get_current_user),
    _=Depends(has_hc_permission(HCRole.clinic_owner)),
):
    offset = (page - 1) * page_size
    query = db.query(HCAuditLog).filter(
        HCAuditLog.tenant_id == hc_shared_tenant_id()
    )

    if from_dt:
        query = query.filter(HCAuditLog.created_at >= from_dt)
    if to_dt:
        query = query.filter(HCAuditLog.created_at <= to_dt)
    if event_type:
        query = query.filter(HCAuditLog.event_type == event_type)

    total = query.count()
    items = (
        query.order_by(HCAuditLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return AuditLogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
