"""Document business logic: store/list/get/download/delete, versions, folders.

Every method runs against a tenant-scoped session (RLS bound to `app.tenant_id`),
and additionally filters by `tenant_id` in code (defense-in-depth — the platform
`appuser` role can bypass RLS; see tenant_isolation_doc.md).
"""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.storage import storage
from ..models.document import Document
from ..models.folder import Folder
from ..models.version import DocumentVersion


class DocumentError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class DocumentService:
    # -- creation ------------------------------------------------------------
    @staticmethod
    async def create(
        db: AsyncSession, *, tenant_id: str, user_id: Optional[str], filename: str,
        content_type: str, data: bytes, folder_id: Optional[str] = None,
    ) -> Document:
        if folder_id is not None:
            exists = await db.scalar(
                select(Folder.id).where(
                    Folder.id == folder_id,
                    Folder.tenant_id == tenant_id,
                    Folder.is_active.is_(True),
                )
            )
            if not exists:
                raise DocumentError("Target folder not found", 404)

        doc_id = uuid.uuid4()
        key = storage.object_key(str(tenant_id), str(doc_id), 1)
        await storage.put(key, data, content_type)

        ct = content_type or "application/octet-stream"
        doc = Document(
            id=doc_id, tenant_id=tenant_id, folder_id=folder_id, filename=filename,
            content_type=ct, size_bytes=len(data), current_version=1,
            storage_key=key, uploaded_by=user_id, is_active=True,
        )
        db.add(doc)
        db.add(DocumentVersion(
            id=uuid.uuid4(), tenant_id=tenant_id, document_id=doc_id, version_no=1,
            filename=filename, content_type=ct, size_bytes=len(data), storage_key=key,
            uploaded_by=user_id, change_comment="Initial version",
        ))
        await db.flush()
        return doc

    # -- reads ---------------------------------------------------------------
    @staticmethod
    async def list(
        db: AsyncSession, *, tenant_id: str, folder_id: Optional[str] = None,
        in_folder: bool = False, skip: int = 0, limit: int = 50,
    ) -> Tuple[List[Document], int]:
        base = select(Document).where(
            Document.tenant_id == tenant_id, Document.is_active.is_(True)
        )
        # `in_folder` distinguishes "root (folder_id IS NULL)" from "all folders".
        if in_folder:
            base = base.where(
                Document.folder_id == folder_id if folder_id is not None
                else Document.folder_id.is_(None)
            )
        total = await db.scalar(select(func.count()).select_from(base.subquery()))
        rows = (
            await db.execute(
                base.order_by(Document.created_at.desc()).offset(skip).limit(limit)
            )
        ).scalars().all()
        return list(rows), int(total or 0)

    @staticmethod
    async def get(
        db: AsyncSession, *, tenant_id: str, document_id: str
    ) -> Optional[Document]:
        return await db.scalar(
            select(Document).where(
                Document.id == document_id,
                Document.tenant_id == tenant_id,
                Document.is_active.is_(True),
            )
        )

    @staticmethod
    async def _require(db: AsyncSession, *, tenant_id: str, document_id: str) -> Document:
        doc = await DocumentService.get(db, tenant_id=tenant_id, document_id=document_id)
        if not doc:
            raise DocumentError("Document not found", 404)
        return doc

    @staticmethod
    async def download_url(
        db: AsyncSession, *, tenant_id: str, document_id: str,
        version_no: Optional[int] = None,
    ) -> Optional[str]:
        doc = await DocumentService.get(db, tenant_id=tenant_id, document_id=document_id)
        if not doc:
            return None
        key, filename, ct = doc.storage_key, doc.filename, doc.content_type
        if version_no is not None and version_no != doc.current_version:
            ver = await db.scalar(
                select(DocumentVersion).where(
                    DocumentVersion.document_id == document_id,
                    DocumentVersion.tenant_id == tenant_id,
                    DocumentVersion.version_no == version_no,
                )
            )
            if not ver:
                return None
            key, filename, ct = ver.storage_key, ver.filename, ver.content_type
        return await storage.presigned_get_url(key, filename, ct)

    # -- versions ------------------------------------------------------------
    @staticmethod
    async def add_version(
        db: AsyncSession, *, tenant_id: str, user_id: Optional[str], document_id: str,
        filename: str, content_type: str, data: bytes, change_comment: Optional[str],
    ) -> Document:
        doc = await DocumentService._require(db, tenant_id=tenant_id, document_id=document_id)
        next_no = doc.current_version + 1
        key = storage.object_key(str(tenant_id), str(document_id), next_no)
        await storage.put(key, data, content_type)
        ct = content_type or "application/octet-stream"

        db.add(DocumentVersion(
            id=uuid.uuid4(), tenant_id=tenant_id, document_id=document_id,
            version_no=next_no, filename=filename, content_type=ct,
            size_bytes=len(data), storage_key=key, uploaded_by=user_id,
            change_comment=change_comment,
        ))
        doc.current_version = next_no
        doc.filename = filename
        doc.content_type = ct
        doc.size_bytes = len(data)
        doc.storage_key = key
        await db.flush()
        return doc

    @staticmethod
    async def list_versions(
        db: AsyncSession, *, tenant_id: str, document_id: str
    ) -> List[DocumentVersion]:
        await DocumentService._require(db, tenant_id=tenant_id, document_id=document_id)
        rows = (
            await db.execute(
                select(DocumentVersion).where(
                    DocumentVersion.document_id == document_id,
                    DocumentVersion.tenant_id == tenant_id,
                ).order_by(DocumentVersion.version_no.desc())
            )
        ).scalars().all()
        return list(rows)

    @staticmethod
    async def restore_version(
        db: AsyncSession, *, tenant_id: str, user_id: Optional[str], document_id: str,
        version_no: int,
    ) -> Document:
        doc = await DocumentService._require(db, tenant_id=tenant_id, document_id=document_id)
        src = await db.scalar(
            select(DocumentVersion).where(
                DocumentVersion.document_id == document_id,
                DocumentVersion.tenant_id == tenant_id,
                DocumentVersion.version_no == version_no,
            )
        )
        if not src:
            raise DocumentError("Version not found", 404)
        # Restoring makes the old content the new current version — recorded as a
        # fresh version row (reusing the existing blob) so history stays append-only.
        next_no = doc.current_version + 1
        db.add(DocumentVersion(
            id=uuid.uuid4(), tenant_id=tenant_id, document_id=document_id,
            version_no=next_no, filename=src.filename, content_type=src.content_type,
            size_bytes=src.size_bytes, storage_key=src.storage_key, uploaded_by=user_id,
            change_comment=f"Restored from v{version_no}",
        ))
        doc.current_version = next_no
        doc.filename = src.filename
        doc.content_type = src.content_type
        doc.size_bytes = src.size_bytes
        doc.storage_key = src.storage_key
        await db.flush()
        return doc

    # -- move / delete -------------------------------------------------------
    @staticmethod
    async def move(
        db: AsyncSession, *, tenant_id: str, document_id: str, folder_id: Optional[str]
    ) -> Document:
        doc = await DocumentService._require(db, tenant_id=tenant_id, document_id=document_id)
        if folder_id is not None:
            exists = await db.scalar(
                select(Folder.id).where(
                    Folder.id == folder_id,
                    Folder.tenant_id == tenant_id,
                    Folder.is_active.is_(True),
                )
            )
            if not exists:
                raise DocumentError("Target folder not found", 404)
        doc.folder_id = folder_id
        await db.flush()
        return doc

    @staticmethod
    async def soft_delete(
        db: AsyncSession, *, tenant_id: str, document_id: str
    ) -> bool:
        doc = await DocumentService.get(db, tenant_id=tenant_id, document_id=document_id)
        if not doc:
            return False
        doc.is_active = False
        await db.flush()
        return True
