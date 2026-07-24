"""Document version history model (E1 F1.2)."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from ..core.database import Base


class DocumentVersion(Base):
    __tablename__ = "dms_document_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("dms_documents.id", ondelete="CASCADE"), nullable=False
    )
    version_no = Column(Integer, nullable=False)
    filename = Column(String(512), nullable=False)
    content_type = Column(String(255), nullable=False)
    size_bytes = Column(BigInteger, nullable=False, default=0)
    storage_key = Column(Text, nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), nullable=True)
    change_comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
