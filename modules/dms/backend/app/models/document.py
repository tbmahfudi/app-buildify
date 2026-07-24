"""DMS document metadata model.

Phase 0 stores a single current version per document (upload -> store -> list ->
download). Multi-version history (dms_versions) arrives in Phase 1; the schema is
already shaped for it (current_version, size/type captured per document).
"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from ..core.database import Base


class Document(Base):
    __tablename__ = "dms_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    folder_id = Column(
        UUID(as_uuid=True), ForeignKey("dms_folders.id", ondelete="SET NULL"), nullable=True
    )

    filename = Column(String(512), nullable=False)
    content_type = Column(String(255), nullable=False, default="application/octet-stream")
    size_bytes = Column(BigInteger, nullable=False, default=0)
    current_version = Column(Integer, nullable=False, default=1)

    # Blob location in the object store (bucket key of the current version).
    storage_key = Column(Text, nullable=False)

    # Free-form tags (GIN-indexed) and arbitrary custom metadata. `doc_metadata`
    # rather than `metadata` — the latter is reserved by SQLAlchemy's declarative
    # Base. Exposed to the API as `metadata` via a serialization alias.
    tags = Column(ARRAY(String), nullable=False, default=list, server_default="{}")
    doc_metadata = Column(JSONB, nullable=False, default=dict, server_default="{}")

    uploaded_by = Column(UUID(as_uuid=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    is_private = Column(Boolean, nullable=False, default=False)
    # Expiry (E4): when the document expires, and the smallest reminder window
    # (30/7/1/0 days) already fired — so the daily scan reminds once per window.
    expires_at = Column(DateTime(timezone=True), nullable=True)
    expiry_reminder_window = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
