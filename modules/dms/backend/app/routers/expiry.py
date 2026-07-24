"""Document expiry + reminders endpoints — mounted at {API_PREFIX}/expiry (E4).

- PUT /expiry/documents/{id}  — set/clear a document's expiry (write + ACL edit).
- GET /expiry/soon            — documents expiring within N days (read, ACL-filtered).
- POST /expiry/scan           — INTERNAL daily reminder scan, invoked by the
                                platform scheduler as a webhook; guarded by a
                                shared secret header, not a user JWT.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..core.database import get_untenanted_db
from ..core.security import Principal, require_permission, tenant_session
from ..schemas.document import DocumentResponse
from ..services.acl_service import AclService
from ..services.audit_service import AuditService
from ..services.document_service import DocumentError, DocumentService
from ..services.expiry_service import ExpiryService

router = APIRouter()

_DOC_ADMIN = "dms:document:delete:company"


class SetExpiryRequest(BaseModel):
    expires_at: Optional[datetime] = None  # null clears the expiry


@router.put("/documents/{document_id}", response_model=DocumentResponse)
async def set_expiry(
    document_id: str,
    body: SetExpiryRequest,
    principal: Principal = Depends(require_permission("dms:document:write:company")),
    db: AsyncSession = Depends(tenant_session),
):
    doc = await DocumentService.get(db, tenant_id=principal.tenant_id, document_id=document_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    group_ids = await AclService.user_group_ids(db, principal.user_id)
    ok = await AclService.authorize_document(
        db, tenant_id=principal.tenant_id, user_id=principal.user_id, group_ids=group_ids,
        is_admin=principal.has_permission(_DOC_ADMIN), document=doc, need="edit",
    )
    if not ok:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this document")
    try:
        doc = await ExpiryService.set_expiry(
            db, tenant_id=principal.tenant_id, document_id=document_id, expires_at=body.expires_at
        )
    except DocumentError as e:
        raise HTTPException(e.status_code, str(e))
    await AuditService.safe_record(
        db, tenant_id=principal.tenant_id, actor_id=principal.user_id,
        action="document.expiry_set", entity_type="document", entity_id=str(document_id),
        detail={"expires_at": body.expires_at.isoformat() if body.expires_at else None},
    )
    return DocumentResponse.model_validate(doc)


@router.get("/soon", response_model=List[DocumentResponse])
async def expiring_soon(
    within_days: int = Query(30, ge=1, le=365),
    principal: Principal = Depends(require_permission("dms:document:read:company")),
    db: AsyncSession = Depends(tenant_session),
):
    docs = await ExpiryService.list_expiring(
        db, tenant_id=principal.tenant_id, within_days=within_days
    )
    # Hide restricted docs the caller cannot view.
    group_ids = await AclService.user_group_ids(db, principal.user_id)
    is_admin = principal.has_permission(_DOC_ADMIN)
    visible = []
    for d in docs:
        if await AclService.authorize_document(
            db, tenant_id=principal.tenant_id, user_id=principal.user_id,
            group_ids=group_ids, is_admin=is_admin, document=d, need="view",
        ):
            visible.append(d)
    return [DocumentResponse.model_validate(d) for d in visible]


@router.post("/scan")
async def expiry_scan(
    x_dms_internal_secret: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_untenanted_db),
):
    """Cross-tenant daily reminder scan. Invoked by the platform scheduler
    (webhook) — authenticated by a shared secret, never a user session."""
    if not x_dms_internal_secret or x_dms_internal_secret != settings.INTERNAL_SECRET:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid internal secret")
    return await ExpiryService.scan_and_remind(db)
