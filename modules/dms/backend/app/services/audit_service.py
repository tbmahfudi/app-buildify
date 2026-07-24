"""DMS audit trail (E3): record and query who did what.

`record()` runs inside the caller's tenant-scoped request transaction, so an
audit row commits atomically with the action it describes. Best-effort: an audit
failure must never break the underlying operation, so callers use `safe_record`.
"""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.audit import DmsAuditLog


class AuditService:
    @staticmethod
    async def record(
        db: AsyncSession, *, tenant_id: str, actor_id: Optional[str], action: str,
        entity_type: str, entity_id: Optional[str] = None, detail: Optional[dict] = None,
    ) -> None:
        db.add(DmsAuditLog(
            id=uuid.uuid4(), tenant_id=tenant_id, actor_id=actor_id, action=action,
            entity_type=entity_type, entity_id=entity_id, detail=detail or {},
        ))
        await db.flush()

    @staticmethod
    async def safe_record(db: AsyncSession, **kwargs) -> None:
        """Record without ever raising into the caller's happy path."""
        try:
            await AuditService.record(db, **kwargs)
        except Exception:  # noqa: BLE001 - auditing must not break the operation
            pass

    @staticmethod
    async def list(
        db: AsyncSession, *, tenant_id: str, entity_type: Optional[str] = None,
        entity_id: Optional[str] = None, action: Optional[str] = None,
        actor_id: Optional[str] = None, skip: int = 0, limit: int = 100,
    ) -> Tuple[List[DmsAuditLog], int]:
        base = select(DmsAuditLog).where(DmsAuditLog.tenant_id == tenant_id)
        if entity_type:
            base = base.where(DmsAuditLog.entity_type == entity_type)
        if entity_id:
            base = base.where(DmsAuditLog.entity_id == entity_id)
        if action:
            base = base.where(DmsAuditLog.action == action)
        if actor_id:
            base = base.where(DmsAuditLog.actor_id == actor_id)
        total = await db.scalar(select(func.count()).select_from(base.subquery()))
        rows = (
            await db.execute(
                base.order_by(DmsAuditLog.created_at.desc()).offset(skip).limit(limit)
            )
        ).scalars().all()
        return list(rows), int(total or 0)

    @staticmethod
    async def iter_all(
        db: AsyncSession, *, tenant_id: str, entity_type: Optional[str] = None,
    ) -> List[DmsAuditLog]:
        """Every entry (newest first) — for CSV export. Tenant-scoped."""
        stmt = select(DmsAuditLog).where(DmsAuditLog.tenant_id == tenant_id)
        if entity_type:
            stmt = stmt.where(DmsAuditLog.entity_type == entity_type)
        rows = (
            await db.execute(stmt.order_by(DmsAuditLog.created_at.desc()))
        ).scalars().all()
        return list(rows)
