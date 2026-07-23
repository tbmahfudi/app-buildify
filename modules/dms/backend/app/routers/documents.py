"""Document endpoints — mounted at {API_PREFIX}/documents (i.e. /api/v1/dms/documents)."""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..core.security import Principal, require_permission, tenant_session
from ..schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DownloadLinkResponse,
    MoveDocumentRequest,
    VersionResponse,
)
from ..services.document_service import DocumentError, DocumentService

router = APIRouter()


def _check_size(data: bytes) -> None:
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file")
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File exceeds max size of {settings.MAX_UPLOAD_BYTES} bytes",
        )


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    folder_id: Optional[str] = Form(None),
    principal: Principal = Depends(require_permission("dms:document:write:company")),
    db: AsyncSession = Depends(tenant_session),
):
    data = await file.read()
    _check_size(data)
    try:
        doc = await DocumentService.create(
            db, tenant_id=principal.tenant_id, user_id=principal.user_id,
            filename=file.filename or "untitled",
            content_type=file.content_type or "application/octet-stream",
            data=data, folder_id=folder_id,
        )
    except DocumentError as e:
        raise HTTPException(e.status_code, str(e))
    return DocumentResponse.model_validate(doc)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    folder_id: Optional[str] = Query(None, description="Filter to a folder; omit for all"),
    root_only: bool = Query(False, description="List only documents at the root (no folder)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    principal: Principal = Depends(require_permission("dms:document:read:company")),
    db: AsyncSession = Depends(tenant_session),
):
    skip = (page - 1) * page_size
    in_folder = folder_id is not None or root_only
    docs, total = await DocumentService.list(
        db, tenant_id=principal.tenant_id, folder_id=folder_id,
        in_folder=in_folder, skip=skip, limit=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total else 0
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in docs],
        total=total, page=page, page_size=page_size, total_pages=total_pages,
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
    version: Optional[int] = Query(None, ge=1, description="Download a specific version"),
    principal: Principal = Depends(require_permission("dms:document:read:company")),
    db: AsyncSession = Depends(tenant_session),
):
    url = await DocumentService.download_url(
        db, tenant_id=principal.tenant_id, document_id=document_id, version_no=version
    )
    if not url:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document or version not found")
    return DownloadLinkResponse(url=url, expires_in=settings.PRESIGN_EXPIRY_SECONDS)


@router.post("/{document_id}/versions", response_model=DocumentResponse)
async def upload_new_version(
    document_id: str,
    file: UploadFile = File(...),
    change_comment: Optional[str] = Form(None),
    principal: Principal = Depends(require_permission("dms:document:write:company")),
    db: AsyncSession = Depends(tenant_session),
):
    data = await file.read()
    _check_size(data)
    try:
        doc = await DocumentService.add_version(
            db, tenant_id=principal.tenant_id, user_id=principal.user_id,
            document_id=document_id, filename=file.filename or "untitled",
            content_type=file.content_type or "application/octet-stream",
            data=data, change_comment=change_comment,
        )
    except DocumentError as e:
        raise HTTPException(e.status_code, str(e))
    return DocumentResponse.model_validate(doc)


@router.get("/{document_id}/versions", response_model=list[VersionResponse])
async def list_versions(
    document_id: str,
    principal: Principal = Depends(require_permission("dms:document:read:company")),
    db: AsyncSession = Depends(tenant_session),
):
    try:
        versions = await DocumentService.list_versions(
            db, tenant_id=principal.tenant_id, document_id=document_id
        )
    except DocumentError as e:
        raise HTTPException(e.status_code, str(e))
    return [VersionResponse.model_validate(v) for v in versions]


@router.post("/{document_id}/versions/{version_no}/restore", response_model=DocumentResponse)
async def restore_version(
    document_id: str,
    version_no: int,
    principal: Principal = Depends(require_permission("dms:document:write:company")),
    db: AsyncSession = Depends(tenant_session),
):
    try:
        doc = await DocumentService.restore_version(
            db, tenant_id=principal.tenant_id, user_id=principal.user_id,
            document_id=document_id, version_no=version_no,
        )
    except DocumentError as e:
        raise HTTPException(e.status_code, str(e))
    return DocumentResponse.model_validate(doc)


@router.post("/{document_id}/move", response_model=DocumentResponse)
async def move_document(
    document_id: str,
    body: MoveDocumentRequest,
    principal: Principal = Depends(require_permission("dms:document:write:company")),
    db: AsyncSession = Depends(tenant_session),
):
    try:
        doc = await DocumentService.move(
            db, tenant_id=principal.tenant_id, document_id=document_id,
            folder_id=str(body.folder_id) if body.folder_id else None,
        )
    except DocumentError as e:
        raise HTTPException(e.status_code, str(e))
    return DocumentResponse.model_validate(doc)


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
