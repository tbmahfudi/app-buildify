"""
Healthcare SDK — PHI audit log writer.

T-HC-014

write_phi_read_audit() — records PHI access events (phi_accessed=True).
write_event_audit()    — records non-PHI events (phi_accessed=False).

All writes are INSERT-only to hc_audit_log. The DB user has no UPDATE/DELETE
on that table (enforced by hc_003_audit_log_permissions migration).
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def write_phi_read_audit(
    db: Session,
    actor_id: str,
    actor_type: str,
    entity_type: str,
    entity_id: str,
    tenant_id: str,
    branch_id: Optional[str] = None,
    ip: Optional[str] = None,
    ua: Optional[str] = None,
    source_module: str = "healthcare",
    metadata: Optional[dict] = None,
) -> None:
    """
    Write a PHI read audit event to hc_audit_log.

    Must be called before returning any PHI field to the caller.
    phi_accessed is set to True.

    Args:
        db:           Active SQLAlchemy session.
        actor_id:     user_id or patient_id of the accessor.
        actor_type:   'staff', 'patient', or 'system'.
        entity_type:  e.g. 'patient', 'encounter'.
        entity_id:    UUID of the accessed entity.
        tenant_id:    Tenant scope.
        branch_id:    Branch scope; None for tenant-wide events.
        ip:           Request IP address.
        ua:           User-Agent header.
        source_module: Module identifier (default: 'healthcare').
        metadata:     Optional JSONB dict for extra context.
    """
    _write_audit(
        db=db,
        actor_id=actor_id,
        actor_type=actor_type,
        event_type="phi.read",
        entity_type=entity_type,
        entity_id=entity_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        phi_accessed=True,
        ip=ip,
        ua=ua,
        source_module=source_module,
        metadata=metadata,
    )


def write_event_audit(
    db: Session,
    actor_id: str,
    actor_type: str,
    event_type: str,
    entity_type: str,
    entity_id: str,
    tenant_id: str,
    branch_id: Optional[str] = None,
    ip: Optional[str] = None,
    ua: Optional[str] = None,
    source_module: str = "healthcare",
    metadata: Optional[dict] = None,
) -> None:
    """
    Write a non-PHI event to hc_audit_log.

    phi_accessed is set to False. Use for lifecycle events such as
    branch.created, staff.invited, consent.recorded, etc.

    Args:
        event_type: Dot-notation event string, e.g. 'branch.created'.
        (See write_phi_read_audit for other arg docs.)
    """
    _write_audit(
        db=db,
        actor_id=actor_id,
        actor_type=actor_type,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        phi_accessed=False,
        ip=ip,
        ua=ua,
        source_module=source_module,
        metadata=metadata,
    )


def _write_audit(
    db: Session,
    actor_id: str,
    actor_type: str,
    event_type: str,
    entity_type: str,
    entity_id: str,
    tenant_id: str,
    phi_accessed: bool,
    branch_id: Optional[str] = None,
    ip: Optional[str] = None,
    ua: Optional[str] = None,
    source_module: str = "healthcare",
    metadata: Optional[dict] = None,
) -> None:
    """Internal — shared INSERT logic for audit log rows."""
    try:
        from modules.healthcare.models import HCAuditLog

        log_entry = HCAuditLog(
            actor_id=actor_id,
            actor_type=actor_type,
            event_type=event_type,
            resource_type=entity_type,
            resource_id=str(entity_id),
            tenant_id=tenant_id,
            branch_id=branch_id,
            phi_accessed=phi_accessed,
            source_module=source_module,
            ip=ip,
            user_agent=ua,
            metadata_json=metadata,
        )
        db.add(log_entry)
        db.flush()
    except Exception as exc:
        # Audit log failure must never crash the request — log and continue
        logger.error("Failed to write audit log entry: %s", exc, exc_info=True)


__all__ = [
    "write_phi_read_audit",
    "write_event_audit",
]
