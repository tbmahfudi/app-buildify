"""Document business logic: store/list/get/download/delete.

Every method runs against a tenant-scoped session (RLS bound to `app.tenant_id`),
so the DB filters rows to the caller's tenant automatically. We still pass
`tenant_id` explicitly for the storage key and for writing it onto new rows.
"""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.storage import storage
from ..models.document import Document


class DocumentService:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        tenant_id: str,
        user_id: Optional[str],
        filename: str,
        content_type: str,
        data: bytes,
    ) -> Document:
        doc_id = uuid.uuid4()
        key = storage.object_key(str(tenant_id), str(doc_id), 1)
        await storage.put(key, data, content_type)

        doc = Document(
            id=doc_id,
            tenant_id=tenant_id,
            filename=filename,
            content_type=content_type or "application/octet-stream",
            size_bytes=len(data),
            current_version=1,
            storage_key=key,
            uploaded_by=user_id,
            is_active=True,
        )
        db.add(doc)
        await db.flush()
        return doc

    @staticmethod
    async def list(
        db: AsyncSession, *, tenant_id: str, skip: int = 0, limit: int = 50
    ) -> Tuple[List[Document], int]:
        # Defense-in-depth: filter by tenant in code AND rely on RLS. The
        # platform's `appuser` role can bypass RLS, so code-level scoping is the
        # primary tenant guarantee here (see tenant_isolation_doc.md, layer 1).
        base = select(Document).where(
            Document.tenant_id == tenant_id, Document.is_active.is_(True)
        )
        total = await db.scalar(
            select(func.count()).select_from(base.subquery())
        )
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
    async def download_url(
        db: AsyncSession, *, tenant_id: str, document_id: str
    ) -> Optional[str]:
        doc = await DocumentService.get(db, tenant_id=tenant_id, document_id=document_id)
        if not doc:
            return None
        return await storage.presigned_get_url(
            doc.storage_key, doc.filename, doc.content_type
        )

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
