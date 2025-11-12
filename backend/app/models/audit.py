from sqlalchemy import Column, DateTime, Index, String, Text, func

from .base import GUID, Base, generate_uuid


class AuditLog(Base):
    """
    Audit trail for all operations.

    Tracks who did what, when, where, and the result.
    Provides complete audit trail for compliance and troubleshooting.
    """
    __tablename__ = "audit_logs"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Who
    user_id = Column(GUID, nullable=True, index=True)
    user_email = Column(String(255), nullable=True)

    # Where (multi-tenant context)
    tenant_id = Column(GUID, nullable=True, index=True)
    company_id = Column(GUID, nullable=True, index=True)
    branch_id = Column(GUID, nullable=True)
    department_id = Column(GUID, nullable=True)

    # What
    action = Column(String(50), nullable=False, index=True)  # CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, etc.
    entity_type = Column(String(100), nullable=True, index=True)  # users, companies, products, etc.
    entity_id = Column(GUID, nullable=True, index=True)

    # Details
    changes = Column(Text, nullable=True)  # JSON: before/after diff
    context_info = Column(Text, nullable=True)  # JSON: additional context

    # Request context
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    request_id = Column(GUID, nullable=True)
    request_method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE
    request_path = Column(String(500), nullable=True)

    # Result
    status = Column(String(20), nullable=False, index=True)  # success, failure, warning
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)

    # Performance
    duration_ms = Column(String(20), nullable=True)  # Duration in milliseconds

    # Timestamp
    created_at = Column(DateTime, server_default=func.now(), index=True, nullable=False)

    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_audit_user_action', 'user_id', 'action'),
        Index('ix_audit_entity', 'entity_type', 'entity_id'),
        Index('ix_audit_tenant_created', 'tenant_id', 'created_at'),
        Index('ix_audit_company_created', 'company_id', 'created_at'),
        Index('ix_audit_tenant_company', 'tenant_id', 'company_id'),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, entity_type={self.entity_type}, status={self.status})>"
