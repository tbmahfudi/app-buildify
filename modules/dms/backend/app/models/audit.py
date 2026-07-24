"""DMS audit trail model (E3).

Append-only record of who did what to which document/folder/share. Enforced
append-only at the DB by a trigger (dms_004) — even a BYPASSRLS role cannot
UPDATE/DELETE rows — so the trail is tamper-evident.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from ..core.database import Base


class DmsAuditLog(Base):
    __tablename__ = "dms_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    actor_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(100), nullable=False)       # e.g. "document.download"
    entity_type = Column(String(32), nullable=False)   # document | folder | share | version
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    detail = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
