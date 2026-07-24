"""Folder endpoints — mounted at {API_PREFIX}/folders (i.e. /api/v1/dms/folders)."""

import io
import zipfile
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import Principal, require_permission, tenant_session
from ..core.storage import storage
from ..schemas.folder import (
    ApplyTemplateRequest,
    FolderCreate,
    FolderListResponse,
    FolderMove,
    FolderRename,
    FolderResponse,
    TemplateListResponse,
)
from ..services.document_service import DocumentService
from ..services.folder_service import (
    WORKSPACE_TEMPLATES,
    FolderError,
    FolderService,
)

router = APIRouter()


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    principal: Principal = Depends(require_permission("dms:folder:read:company")),
):
    return TemplateListResponse(templates=WORKSPACE_TEMPLATES)


@router.post("/templates/{template_name}", response_model=FolderResponse,
             status_code=status.HTTP_201_CREATED)
async def apply_template(
    template_name: str,
    body: ApplyTemplateRequest,
    principal: Principal = Depends(require_permission("dms:folder:manage:company")),
    db: AsyncSession = Depends(tenant_session),
):
    try:
        root = await FolderService.apply_template(
            db, tenant_id=principal.tenant_id, user_id=principal.user_id,
            template_name=template_name,
            parent_id=str(body.parent_id) if body.parent_id else None,
        )
    except FolderError as e:
        raise HTTPException(e.status_code, str(e))
    return FolderResponse.model_validate(root)


@router.post("", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    body: FolderCreate,
    principal: Principal = Depends(require_permission("dms:folder:manage:company")),
    db: AsyncSession = Depends(tenant_session),
):
    try:
        folder = await FolderService.create(
            db, tenant_id=principal.tenant_id, user_id=principal.user_id,
            name=body.name, parent_id=str(body.parent_id) if body.parent_id else None,
        )
    except FolderError as e:
        raise HTTPException(e.status_code, str(e))
    return FolderResponse.model_validate(folder)


@router.get("", response_model=FolderListResponse)
async def list_folders(
    parent_id: Optional[str] = Query(None, description="List children of this folder; omit for root"),
    principal: Principal = Depends(require_permission("dms:folder:read:company")),
    db: AsyncSession = Depends(tenant_session),
):
    folders = await FolderService.list(
        db, tenant_id=principal.tenant_id, parent_id=parent_id
    )
    return FolderListResponse(folders=[FolderResponse.model_validate(f) for f in folders])


@router.get("/{folder_id}/download")
async def download_folder_zip(
    folder_id: str,
    principal: Principal = Depends(require_permission("dms:document:read:company")),
    db: AsyncSession = Depends(tenant_session),
):
    """Download every document directly in a folder as a single zip archive."""
    folder = await FolderService.get(db, tenant_id=principal.tenant_id, folder_id=folder_id)
    if not folder:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Folder not found")
    docs = await DocumentService.all_in_folder(
        db, tenant_id=principal.tenant_id, folder_id=folder_id
    )

    buf = io.BytesIO()
    seen: dict[str, int] = {}
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for doc in docs:
            data = await storage.get_bytes(doc.storage_key)
            # De-duplicate names within the archive (Windows-friendly).
            name = doc.filename
            if name in seen:
                seen[name] += 1
                stem, _, ext = name.rpartition(".")
                name = f"{stem} ({seen[name]}).{ext}" if ext else f"{name} ({seen[name]})"
            else:
                seen[name] = 0
            zf.writestr(name, data)
    buf.seek(0)

    safe = folder.name.replace('"', "")
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{safe}.zip"'},
    )


@router.patch("/{folder_id}", response_model=FolderResponse)
async def rename_folder(
    folder_id: str,
    body: FolderRename,
    principal: Principal = Depends(require_permission("dms:folder:manage:company")),
    db: AsyncSession = Depends(tenant_session),
):
    try:
        folder = await FolderService.rename(
            db, tenant_id=principal.tenant_id, folder_id=folder_id, name=body.name
        )
    except FolderError as e:
        raise HTTPException(e.status_code, str(e))
    return FolderResponse.model_validate(folder)


@router.post("/{folder_id}/move", response_model=FolderResponse)
async def move_folder(
    folder_id: str,
    body: FolderMove,
    principal: Principal = Depends(require_permission("dms:folder:manage:company")),
    db: AsyncSession = Depends(tenant_session),
):
    try:
        folder = await FolderService.move(
            db, tenant_id=principal.tenant_id, folder_id=folder_id,
            new_parent_id=str(body.parent_id) if body.parent_id else None,
        )
    except FolderError as e:
        raise HTTPException(e.status_code, str(e))
    return FolderResponse.model_validate(folder)


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: str,
    principal: Principal = Depends(require_permission("dms:folder:manage:company")),
    db: AsyncSession = Depends(tenant_session),
):
    try:
        await FolderService.delete(db, tenant_id=principal.tenant_id, folder_id=folder_id)
    except FolderError as e:
        raise HTTPException(e.status_code, str(e))
