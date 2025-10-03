from sqlalchemy import Column, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base
try:
    from sqlalchemy.dialects.postgresql import UUID
    UUIDType = UUID(as_uuid=True)
except Exception:
    from sqlalchemy import String as _String
    UUIDType = _String(36)

class Branch(Base):
    __tablename__ = "branches"
    id = Column(UUIDType, primary_key=True)
    company_id = Column(UUIDType, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(32), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    company = relationship("Company", back_populates="branches")
    departments = relationship("Department", back_populates="branch", cascade="all, delete-orphan")
