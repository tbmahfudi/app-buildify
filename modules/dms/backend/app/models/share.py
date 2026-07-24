"""External share-link model (E3 F1.5 / access control).

A share grants time-limited, optionally download-capped, unauthenticated access
to a single document via an unguessable token. Enforcement lives in
ShareService; this is just the record.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from ..core.database import Base


class DmsShare(Base):
    __tablename__ = "dms_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("dms_documents.id", ondelete="CASCADE"), nullable=False
    )
    token = Column(String(64), nullable=False, unique=True, index=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)   # null = no expiry
    max_downloads = Column(Integer, nullable=True)                # null = unlimited
    download_count = Column(Integer, nullable=False, default=0)
    is_revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
