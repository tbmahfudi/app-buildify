"""Share-link endpoints — mounted at {API_PREFIX}/shares (E3).

Authenticated management (create/list/revoke) is gated by dms:share:create:company.
The public download (`/shares/public/{token}`) takes NO auth — the unguessable
token is the credential — and streams the document bytes, enforcing expiry,
revocation and the download cap.
"""

from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..core.database import get_untenanted_db
from ..core.security import Principal, require_permission, tenant_session
from ..schemas.share import (
    CreateShareRequest,
    ShareListResponse,
    ShareResponse,
)
from ..services.audit_service import AuditService
from ..services.share_service import ShareError, ShareService

router = APIRouter()

_MANAGE = require_permission("dms:share:create:company")


def _public_path(token: str) -> str:
    return f"{settings.API_PREFIX}/shares/public/{token}"


def _to_response(share) -> ShareResponse:
    resp = ShareResponse.model_validate(share)
    resp.public_path = _public_path(share.token)
    return resp


@router.post("", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
async def create_share(
    body: CreateShareRequest,
    principal: Principal = Depends(_MANAGE),
    db: AsyncSession = Depends(tenant_session),
):
    try:
        share = await ShareService.create(
            db, tenant_id=principal.tenant_id, user_id=principal.user_id,
            document_id=str(body.document_id),
            expires_in_hours=body.expires_in_hours, max_downloads=body.max_downloads,
        )
    except ShareError as e:
        raise HTTPException(e.status_code, str(e))
    await AuditService.safe_record(
        db, tenant_id=principal.tenant_id, actor_id=principal.user_id,
        action="share.create", entity_type="share", entity_id=str(share.id),
        detail={"document_id": str(body.document_id),
                "expires_in_hours": body.expires_in_hours,
                "max_downloads": body.max_downloads},
    )
    return _to_response(share)


@router.get("", response_model=ShareListResponse)
async def list_shares(
    document_id: Optional[str] = Query(None, description="Filter to one document"),
    principal: Principal = Depends(_MANAGE),
    db: AsyncSession = Depends(tenant_session),
):
    shares = await ShareService.list(
        db, tenant_id=principal.tenant_id, document_id=document_id
    )
    return ShareListResponse(shares=[_to_response(s) for s in shares])


@router.delete("/{share_id}", response_model=ShareResponse)
async def revoke_share(
    share_id: str,
    principal: Principal = Depends(_MANAGE),
    db: AsyncSession = Depends(tenant_session),
):
    try:
        share = await ShareService.revoke(
            db, tenant_id=principal.tenant_id, share_id=share_id
        )
    except ShareError as e:
        raise HTTPException(e.status_code, str(e))
    await AuditService.safe_record(
        db, tenant_id=principal.tenant_id, actor_id=principal.user_id,
        action="share.revoke", entity_type="share", entity_id=str(share_id),
    )
    return _to_response(share)


# --- PUBLIC: no authentication; the token is the credential -----------------
@router.get("/public/{token}")
async def download_shared(
    token: str,
    db: AsyncSession = Depends(get_untenanted_db),
):
    try:
        share, doc, data = await ShareService.resolve_and_consume(db, token=token)
    except ShareError as e:
        raise HTTPException(e.status_code, str(e))

    await AuditService.safe_record(
        db, tenant_id=str(share.tenant_id), actor_id=None,
        action="share.download", entity_type="document", entity_id=str(doc.id),
        detail={"share_id": str(share.id)},
    )
    filename = quote(doc.filename)
    return Response(
        content=data,
        media_type=doc.content_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )
