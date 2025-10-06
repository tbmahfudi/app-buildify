from sqlalchemy import Column, String, Text, DateTime, func, Index
from .base import Base
try:
    from sqlalchemy.dialects.postgresql import UUID
    UUIDType = UUID(as_uuid=True)
except Exception:
    from sqlalchemy import String as _String
    UUIDType = _String(36)

class AuditLog(Base):
    """Audit trail for all operations"""
    __tablename__ = "audit_logs"
    
    id = Column(UUIDType, primary_key=True)
    
    # Who
    user_id = Column(String(36), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    tenant_id = Column(String(36), nullable=True, index=True)
    
    # What
    action = Column(String(50), nullable=False, index=True)  # CREATE, READ, UPDATE, DELETE, LOGIN, etc.
    entity_type = Column(String(100), nullable=True, index=True)  # users, companies, etc.
    entity_id = Column(String(36), nullable=True, index=True)
    
    # Details
    changes = Column(Text, nullable=True)  # JSON: before/after diff
    context_info  = Column(Text, nullable=True)  # JSON: additional context
    
    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(36), nullable=True)
    
    # Result
    status = Column(String(20), nullable=False)  # success, failure, warning
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_audit_user_action', 'user_id', 'action'),
        Index('ix_audit_entity', 'entity_type', 'entity_id'),
        Index('ix_audit_tenant_created', 'tenant_id', 'created_at'),
    )