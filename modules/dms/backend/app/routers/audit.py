"""Audit trail endpoints — mounted at {API_PREFIX}/audit (E3).

Read-only; gated by dms:audit:view:company. Records are written by the document
and folder services as a side effect of the actions they perform.
"""

import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import Principal, require_permission, tenant_session
from ..schemas.audit import AuditEntryResponse, AuditListResponse
from ..services.audit_service import AuditService

router = APIRouter()

_VIEW = require_permission("dms:audit:view:company")


@router.get("", response_model=AuditListResponse)
async def list_audit(
    entity_type: Optional[str] = Query(None, description="document | folder | share | version"),
    entity_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    actor_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    principal: Principal = Depends(_VIEW),
    db: AsyncSession = Depends(tenant_session),
):
    rows, total = await AuditService.list(
        db, tenant_id=principal.tenant_id, entity_type=entity_type,
        entity_id=entity_id, action=action, actor_id=actor_id,
        skip=(page - 1) * page_size, limit=page_size,
    )
    return AuditListResponse(
        entries=[AuditEntryResponse.model_validate(r) for r in rows], total=total
    )


@router.get("/export.csv")
async def export_audit_csv(
    entity_type: Optional[str] = Query(None),
    principal: Principal = Depends(_VIEW),
    db: AsyncSession = Depends(tenant_session),
):
    rows = await AuditService.iter_all(
        db, tenant_id=principal.tenant_id, entity_type=entity_type
    )
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["timestamp", "actor_id", "action", "entity_type", "entity_id", "detail"])
    for r in rows:
        writer.writerow([
            r.created_at.isoformat(), str(r.actor_id or ""), r.action,
            r.entity_type, str(r.entity_id or ""), _flatten(r.detail),
        ])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="dms-audit.csv"'},
    )


def _flatten(detail: dict) -> str:
    if not detail:
        return ""
    return "; ".join(f"{k}={v}" for k, v in detail.items())
