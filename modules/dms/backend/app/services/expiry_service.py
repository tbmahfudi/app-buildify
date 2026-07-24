"""Document expiry + reminders (E4).

A document may carry an `expires_at`. A daily platform-scheduler webhook calls
`scan_and_remind`, which walks documents across all tenants and, as each crosses
the 30/7/1/0-day windows, records a `document.expiry_reminder` audit event (at
most once per window, tracked by `expiry_reminder_window`).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.document import Document
from .audit_service import AuditService

# Largest-to-smallest so we pick the tightest window a document has entered.
REMINDER_WINDOWS = [30, 7, 1, 0]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _days_left(expires_at: datetime) -> int:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    delta = expires_at - _now()
    # Ceil toward the day boundary: 0 means expired (<= now).
    secs = delta.total_seconds()
    if secs <= 0:
        return 0
    return max(1, -(-int(secs) // 86400))


def _window_for(days_left: int) -> Optional[int]:
    # The tightest window the document has entered (e.g. 5 days left → 7).
    matched = [w for w in REMINDER_WINDOWS if days_left <= w]
    return min(matched) if matched else None


class ExpiryService:
    @staticmethod
    async def set_expiry(
        db: AsyncSession, *, tenant_id: str, document_id: str, expires_at: Optional[datetime]
    ) -> Document:
        doc = await db.scalar(
            select(Document).where(
                Document.id == document_id, Document.tenant_id == tenant_id,
                Document.is_active.is_(True),
            )
        )
        if not doc:
            from .document_service import DocumentError
            raise DocumentError("Document not found", 404)
        doc.expires_at = expires_at
        doc.expiry_reminder_window = None  # re-arm reminders for the new date
        await db.flush()
        return doc

    @staticmethod
    async def list_expiring(
        db: AsyncSession, *, tenant_id: str, within_days: int = 30
    ) -> List[Document]:
        cutoff = _now().timestamp() + within_days * 86400
        rows = (
            await db.execute(
                select(Document).where(
                    Document.tenant_id == tenant_id,
                    Document.is_active.is_(True),
                    Document.expires_at.isnot(None),
                ).order_by(Document.expires_at)
            )
        ).scalars().all()
        # Filter in Python to keep tz handling simple + include already-expired.
        return [d for d in rows if d.expires_at and d.expires_at.timestamp() <= cutoff]

    @staticmethod
    async def scan_and_remind(db: AsyncSession) -> Dict[str, Any]:
        """Cross-tenant batch (untenanted session): fire due reminders once per
        window. Returns a summary."""
        rows = (
            await db.execute(
                select(Document).where(
                    Document.is_active.is_(True),
                    Document.expires_at.isnot(None),
                    or_(
                        Document.expiry_reminder_window.is_(None),
                        Document.expiry_reminder_window > 0,
                    ),
                )
            )
        ).scalars().all()

        reminded = 0
        by_window: Dict[int, int] = {}
        for doc in rows:
            days_left = _days_left(doc.expires_at)
            window = _window_for(days_left)
            if window is None:
                continue
            prev = doc.expiry_reminder_window
            # New reminder only when entering a *tighter* window than last time.
            if prev is not None and window >= prev:
                continue
            await AuditService.safe_record(
                db, tenant_id=str(doc.tenant_id), actor_id=None,
                action="document.expiry_reminder", entity_type="document",
                entity_id=str(doc.id),
                detail={"days_left": days_left, "window": window, "filename": doc.filename},
            )
            doc.expiry_reminder_window = window
            reminded += 1
            by_window[window] = by_window.get(window, 0) + 1

        await db.flush()
        return {"scanned": len(rows), "reminded": reminded,
                "by_window": {str(k): v for k, v in by_window.items()}}
