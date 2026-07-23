"""DMS document metadata model.

Phase 0 stores a single current version per document (upload -> store -> list ->
download). Multi-version history (dms_versions) arrives in Phase 1; the schema is
already shaped for it (current_version, size/type captured per document).
"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

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

    uploaded_by = Column(UUID(as_uuid=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
