"""Document endpoints — mounted at {API_PREFIX}/documents (i.e. /api/v1/dms/documents)."""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..core.security import Principal, get_principal, require_permission, tenant_session
from ..schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DownloadLinkResponse,
)
from ..services.document_service import DocumentService

router = APIRouter()


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    principal: Principal = Depends(require_permission("dms:document:write:company")),
    db: AsyncSession = Depends(tenant_session),
):
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file")
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File exceeds max size of {settings.MAX_UPLOAD_BYTES} bytes",
        )
    doc = await DocumentService.create(
        db,
        tenant_id=principal.tenant_id,
        user_id=principal.user_id,
        filename=file.filename or "untitled",
        content_type=file.content_type or "application/octet-stream",
        data=data,
    )
    return DocumentResponse.model_validate(doc)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    principal: Principal = Depends(require_permission("dms:document:read:company")),
    db: AsyncSession = Depends(tenant_session),
):
    skip = (page - 1) * page_size
    docs, total = await DocumentService.list(
        db, tenant_id=principal.tenant_id, skip=skip, limit=page_size
    )
    total_pages = (total + page_size - 1) // page_size if total else 0
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    principal: Principal = Depends(require_permission("dms:document:read:company")),
    db: AsyncSession = Depends(tenant_session),
):
    doc = await DocumentService.get(db, tenant_id=principal.tenant_id, document_id=document_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return DocumentResponse.model_validate(doc)


@router.get("/{document_id}/download", response_model=DownloadLinkResponse)
async def download_document(
    document_id: str,
    principal: Principal = Depends(require_permission("dms:document:read:company")),
    db: AsyncSession = Depends(tenant_session),
):
    url = await DocumentService.download_url(
        db, tenant_id=principal.tenant_id, document_id=document_id
    )
    if not url:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return DownloadLinkResponse(url=url, expires_in=settings.PRESIGN_EXPIRY_SECONDS)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    principal: Principal = Depends(require_permission("dms:document:delete:company")),
    db: AsyncSession = Depends(tenant_session),
):
    ok = await DocumentService.soft_delete(
        db, tenant_id=principal.tenant_id, document_id=document_id
    )
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
