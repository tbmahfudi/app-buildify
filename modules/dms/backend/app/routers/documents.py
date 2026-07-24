"""Document endpoints — mounted at {API_PREFIX}/documents (i.e. /api/v1/dms/documents)."""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..core.security import Principal, require_permission, tenant_session
from ..schemas.document import (
    BulkMetadataRequest,
    BulkMetadataResponse,
    DocumentListResponse,
    DocumentResponse,
    DownloadLinkResponse,
    MoveDocumentRequest,
    UpdateMetadataRequest,
    VersionResponse,
)
from ..models.document import Document
from ..services.acl_service import AclService
from ..services.audit_service import AuditService
from ..services.document_service import DocumentError, DocumentService

router = APIRouter()

_DOC_ADMIN = "dms:document:delete:company"


def _check_size(data: bytes) -> None:
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file")
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File exceeds max size of {settings.MAX_UPLOAD_BYTES} bytes",
        )


async def _authorize_doc(db, principal: Principal, document: Document, need: str) -> None:
    """403 if the caller lacks `need` capability on a restricted document."""
    group_ids = await AclService.user_group_ids(db, principal.user_id)
    ok = await AclService.authorize_document(
        db, tenant_id=principal.tenant_id, user_id=principal.user_id, group_ids=group_ids,
        is_admin=principal.has_permission(_DOC_ADMIN), document=document, need=need,
    )
    if not ok:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this document")


async def _authorize_folder(db, principal: Principal, folder_id, need: str) -> None:
    """403 if the caller lacks `need` capability on a restricted target folder."""
    group_ids = await AclService.user_group_ids(db, principal.user_id)
    ok = await AclService.authorize_folder(
        db, tenant_id=principal.tenant_id, user_id=principal.user_id, group_ids=group_ids,
        is_admin=principal.has_permission("dms:folder:manage:company"),
        folder_id=folder_id, need=need,
    )
    if not ok:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this folder")


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    folder_id: Optional[str] = Form(None),
    principal: Principal = Depends(require_permission("dms:document:write:company")),
    db: AsyncSession = Depends(tenant_session),
):
    data = await file.read()
    _check_size(data)
    await _authorize_folder(db, principal, folder_id, "edit")
    try:
        doc = await DocumentService.create(
            db, tenant_id=principal.tenant_id, user_id=principal.user_id,
            filename=file.filename or "untitled",
            content_type=file.content_type or "application/octet-stream",
            data=data, folder_id=folder_id,
        )
    except DocumentError as e:
        raise HTTPException(e.status_code, str(e))
    await AuditService.safe_record(
        db, tenant_id=principal.tenant_id, actor_id=principal.user_id,
        action="document.upload", entity_type="document", entity_id=str(doc.id),
        detail={"filename": doc.filename, "folder_id": folder_id, "size_bytes": doc.size_bytes},
    )
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
    # Hide restricted documents the caller cannot at least view. Filtering happens
    # on the page after fetch; `total` is reduced by what was hidden here (so the
    # count is approximate when private docs exist, but a private doc is never
    # surfaced to an unauthorized caller).
    group_ids = await AclService.user_group_ids(db, principal.user_id)
    is_admin = principal.has_permission(_DOC_ADMIN)
    visible = []
    for d in docs:
        allowed = await AclService.authorize_document(
            db, tenant_id=principal.tenant_id, user_id=principal.user_id,
            group_ids=group_ids, is_admin=is_admin, document=d, need="view",
        )
        if allowed:
            visible.append(d)
    total = max(0, total - (len(docs) - len(visible)))
    total_pages = (total + page_size - 1) // page_size if total else 0
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in visible],
        total=total, page=page, page_size=page_size, total_pages=total_pages,
    )


@router.post("/bulk/metadata", response_model=BulkMetadataResponse)
async def bulk_update_metadata(
    body: BulkMetadataRequest,
    principal: Principal = Depends(require_permission("dms:document:write:company")),
    db: AsyncSession = Depends(tenant_session),
):
    updated = await DocumentService.bulk_update_metadata(
        db, tenant_id=principal.tenant_id,
        document_ids=[str(d) for d in body.document_ids],
        set_tags=body.set_tags, add_tags=body.add_tags,
        remove_tags=body.remove_tags, metadata=body.metadata,
    )
    return BulkMetadataResponse(updated=updated)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    principal: Principal = Depends(require_permission("dms:document:read:company")),
    db: AsyncSession = Depends(tenant_session),
):
    doc = await DocumentService.get(db, tenant_id=principal.tenant_id, document_id=document_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    await _authorize_doc(db, principal, doc, "view")
    return DocumentResponse.model_validate(doc)


@router.get("/{document_id}/download", response_model=DownloadLinkResponse)
async def download_document(
    document_id: str,
    version: Optional[int] = Query(None, ge=1, description="Download a specific version"),
    principal: Principal = Depends(require_permission("dms:document:read:company")),
    db: AsyncSession = Depends(tenant_session),
):
    doc = await DocumentService.get(db, tenant_id=principal.tenant_id, document_id=document_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    await _authorize_doc(db, principal, doc, "view")
    url = await DocumentService.download_url(
        db, tenant_id=principal.tenant_id, document_id=document_id, version_no=version
    )
    if not url:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document or version not found")
    await AuditService.safe_record(
        db, tenant_id=principal.tenant_id, actor_id=principal.user_id,
        action="document.download", entity_type="document", entity_id=str(document_id),
        detail={"version": version} if version else {},
    )
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
    existing = await DocumentService.get(db, tenant_id=principal.tenant_id, document_id=document_id)
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    await _authorize_doc(db, principal, existing, "edit")
    try:
        doc = await DocumentService.add_version(
            db, tenant_id=principal.tenant_id, user_id=principal.user_id,
            document_id=document_id, filename=file.filename or "untitled",
            content_type=file.content_type or "application/octet-stream",
            data=data, change_comment=change_comment,
        )
    except DocumentError as e:
        raise HTTPException(e.status_code, str(e))
    await AuditService.safe_record(
        db, tenant_id=principal.tenant_id, actor_id=principal.user_id,
        action="document.version.add", entity_type="document", entity_id=str(document_id),
        detail={"version": doc.current_version, "comment": change_comment},
    )
    return DocumentResponse.model_validate(doc)


@router.get("/{document_id}/versions", response_model=list[VersionResponse])
async def list_versions(
    document_id: str,
    principal: Principal = Depends(require_permission("dms:document:read:company")),
    db: AsyncSession = Depends(tenant_session),
):
    doc = await DocumentService.get(db, tenant_id=principal.tenant_id, document_id=document_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    await _authorize_doc(db, principal, doc, "view")
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
    existing = await DocumentService.get(db, tenant_id=principal.tenant_id, document_id=document_id)
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    await _authorize_doc(db, principal, existing, "edit")
    try:
        doc = await DocumentService.restore_version(
            db, tenant_id=principal.tenant_id, user_id=principal.user_id,
            document_id=document_id, version_no=version_no,
        )
    except DocumentError as e:
        raise HTTPException(e.status_code, str(e))
    await AuditService.safe_record(
        db, tenant_id=principal.tenant_id, actor_id=principal.user_id,
        action="document.version.restore", entity_type="document", entity_id=str(document_id),
        detail={"restored_from": version_no, "new_version": doc.current_version},
    )
    return DocumentResponse.model_validate(doc)


@router.post("/{document_id}/move", response_model=DocumentResponse)
async def move_document(
    document_id: str,
    body: MoveDocumentRequest,
    principal: Principal = Depends(require_permission("dms:document:write:company")),
    db: AsyncSession = Depends(tenant_session),
):
    existing = await DocumentService.get(db, tenant_id=principal.tenant_id, document_id=document_id)
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    await _authorize_doc(db, principal, existing, "edit")
    await _authorize_folder(
        db, principal, str(body.folder_id) if body.folder_id else None, "edit"
    )
    try:
        doc = await DocumentService.move(
            db, tenant_id=principal.tenant_id, document_id=document_id,
            folder_id=str(body.folder_id) if body.folder_id else None,
        )
    except DocumentError as e:
        raise HTTPException(e.status_code, str(e))
    await AuditService.safe_record(
        db, tenant_id=principal.tenant_id, actor_id=principal.user_id,
        action="document.move", entity_type="document", entity_id=str(document_id),
        detail={"folder_id": str(body.folder_id) if body.folder_id else None},
    )
    return DocumentResponse.model_validate(doc)


@router.patch("/{document_id}/metadata", response_model=DocumentResponse)
async def update_metadata(
    document_id: str,
    body: UpdateMetadataRequest,
    principal: Principal = Depends(require_permission("dms:document:write:company")),
    db: AsyncSession = Depends(tenant_session),
):
    existing = await DocumentService.get(db, tenant_id=principal.tenant_id, document_id=document_id)
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    await _authorize_doc(db, principal, existing, "edit")
    try:
        doc = await DocumentService.update_metadata(
            db, tenant_id=principal.tenant_id, document_id=document_id,
            tags=body.tags, metadata=body.metadata,
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
    existing = await DocumentService.get(db, tenant_id=principal.tenant_id, document_id=document_id)
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    await _authorize_doc(db, principal, existing, "manage")
    ok = await DocumentService.soft_delete(
        db, tenant_id=principal.tenant_id, document_id=document_id
    )
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    await AuditService.safe_record(
        db, tenant_id=principal.tenant_id, actor_id=principal.user_id,
        action="document.delete", entity_type="document", entity_id=str(document_id),
    )
