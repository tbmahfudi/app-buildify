"""
TEMPLATE module SQLAlchemy models.

All models MUST:
  1. Set __tenant_scoped__ = True
  2. Include a tenant_id column
  3. Use the platform Base (imported from backend via manage.sh migrations)
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID

# Use the platform declarative base
try:
    from backend.app.core.database import Base
except ImportError:
    # Fallback for standalone testing
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


class TEMPLATEItem(Base):
    """Example model — rename and extend for your use case."""

    __tablename__ = "template_items"

    # Required by TenantScopeListener
    __tenant_scoped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(36), nullable=False, index=True)  # Required

    # TODO: replace with your actual columns
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<TEMPLATEItem id={self.id} tenant={self.tenant_id}>"
