from sqlalchemy import Column, String, Boolean, DateTime, func, Text
from sqlalchemy.orm import relationship
from .base import Base
try:
    from sqlalchemy.dialects.postgresql import UUID
    UUIDType = UUID(as_uuid=True)
except Exception:
    from sqlalchemy import String as _String
    UUIDType = _String(36)

class User(Base):
    __tablename__ = "users"
    id = Column(UUIDType, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Multi-tenancy
    tenant_id = Column(String(36), nullable=True, index=True)
    
    # RBAC - JSON array of role names
    roles = Column(Text, nullable=True)  # JSON: ["admin", "user", "viewer"]
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
