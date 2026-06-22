"""TEMPLATE module SQLAlchemy models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text

# SDK-only import — never from backend.app directly
from modules.sdk.db import Base, GUID, generate_uuid


class TEMPLATEItem(Base):
    """Example model — rename and extend for your use case."""

    __tablename__ = "template_items"
    __tenant_scoped__ = True  # Required by TenantScopeListener

    id = Column(GUID(), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<TEMPLATEItem id={self.id} tenant={self.tenant_id}>"
