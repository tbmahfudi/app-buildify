"""External share links (E3): create / list / revoke, and public resolution.

The public resolver runs on an *untenanted* session (the tenant is unknown until
the token row is found) and enforces revocation, expiry and the download cap
atomically. Every subsequent read is filtered by the tenant_id read from the
share row — the code-level guard that actually isolates tenants here.
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.document import Document
from ..models.share import DmsShare


class ShareError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ShareService:
    # -- authenticated management --------------------------------------------
    @staticmethod
    async def create(
        db: AsyncSession, *, tenant_id: str, user_id: Optional[str], document_id: str,
        expires_in_hours: Optional[int], max_downloads: Optional[int],
    ) -> DmsShare:
        doc = await db.scalar(
            select(Document).where(
                Document.id == document_id,
                Document.tenant_id == tenant_id,
                Document.is_active.is_(True),
            )
        )
        if not doc:
            raise ShareError("Document not found", 404)
        expires_at = _now() + timedelta(hours=expires_in_hours) if expires_in_hours else None
        share = DmsShare(
            id=uuid.uuid4(), tenant_id=tenant_id, document_id=document_id,
            token=secrets.token_urlsafe(32), created_by=user_id,
            expires_at=expires_at, max_downloads=max_downloads,
            download_count=0, is_revoked=False,
        )
        db.add(share)
        await db.flush()
        return share

    @staticmethod
    async def list(
        db: AsyncSession, *, tenant_id: str, document_id: Optional[str] = None
    ) -> List[DmsShare]:
        stmt = select(DmsShare).where(DmsShare.tenant_id == tenant_id)
        if document_id:
            stmt = stmt.where(DmsShare.document_id == document_id)
        rows = (await db.execute(stmt.order_by(DmsShare.created_at.desc()))).scalars().all()
        return list(rows)

    @staticmethod
    async def revoke(db: AsyncSession, *, tenant_id: str, share_id: str) -> DmsShare:
        share = await db.scalar(
            select(DmsShare).where(DmsShare.id == share_id, DmsShare.tenant_id == tenant_id)
        )
        if not share:
            raise ShareError("Share not found", 404)
        share.is_revoked = True
        await db.flush()
        return share

    # -- public (unauthenticated) resolution ---------------------------------
    @staticmethod
    async def resolve_and_consume(
        db: AsyncSession, *, token: str
    ) -> Tuple[DmsShare, Document, bytes]:
        """Validate a share token, atomically consume one download, return the
        document bytes. Raises ShareError(404/410/429) on any failure.

        Runs on an untenanted session; the document is fetched with an explicit
        tenant_id filter from the share row.
        """
        share = await db.scalar(select(DmsShare).where(DmsShare.token == token))
        if not share:
            raise ShareError("This link is not valid.", 404)
        if share.is_revoked:
            raise ShareError("This link has been revoked.", 410)
        if share.expires_at is not None and share.expires_at <= _now():
            raise ShareError("This link has expired.", 410)

        # Atomic check-and-increment so the cap can't be exceeded under races.
        result = await db.execute(
            update(DmsShare)
            .where(
                and_(
                    DmsShare.id == share.id,
                    DmsShare.is_revoked.is_(False),
                    or_(DmsShare.expires_at.is_(None), DmsShare.expires_at > _now()),
                    or_(
                        DmsShare.max_downloads.is_(None),
                        DmsShare.download_count < DmsShare.max_downloads,
                    ),
                )
            )
            .values(download_count=DmsShare.download_count + 1)
            .returning(DmsShare.id)
        )
        if result.first() is None:
            raise ShareError("This link has reached its download limit.", 429)

        doc = await db.scalar(
            select(Document).where(
                Document.id == share.document_id,
                Document.tenant_id == share.tenant_id,
                Document.is_active.is_(True),
            )
        )
        if not doc:
            raise ShareError("The shared document is no longer available.", 410)

        from ..core.storage import storage
        data = await storage.get_bytes(doc.storage_key)
        return share, doc, data
