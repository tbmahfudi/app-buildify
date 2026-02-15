"""
Module Service Models

Models for cross-module service access (Phase 4 Priority 2):
- ModuleService: Service registry for module-to-module communication
- ModuleServiceAccessLog: Audit log for service access
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DateTime, UniqueConstraint, CheckConstraint, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.models.base import Base, GUID, generate_uuid


class ModuleService(Base):
    """
    Module Service Registry

    Registers services that modules expose for cross-module access.
    Each service defines a contract (methods and signatures) that other
    modules can call with permission checking and logging.
    """
    __tablename__ = 'module_services'

    # Identity
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Module reference
    module_id = Column(
        GUID,
        ForeignKey('modules.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Service definition
    service_name = Column(String(100), nullable=False, index=True)  # e.g., "EmployeeService"
    service_class = Column(String(200), nullable=False)  # Full Python class path
    service_version = Column(String(20), nullable=False, default='1.0.0')

    # API contract (list of public methods with signatures)
    methods = Column(JSON, nullable=False, default=list)

    # Documentation
    description = Column(Text)

    # Status
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(GUID, ForeignKey('users.id'))

    # Relationships
    module = relationship("Module", back_populates="services")
    creator = relationship("User", foreign_keys=[created_by])
    access_logs = relationship(
        "ModuleServiceAccessLog",
        back_populates="service",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            'module_id', 'service_name', 'service_version',
            name='unique_module_service'
        ),
        Index('idx_module_services_module', 'module_id'),
        Index('idx_module_services_name', 'service_name'),
    )

    def __repr__(self):
        return f"<ModuleService(service_name='{self.service_name}', version='{self.service_version}')>"


class ModuleServiceAccessLog(Base):
    """
    Module Service Access Log

    Tracks all cross-module service calls for auditing, debugging,
    and performance monitoring.
    """
    __tablename__ = 'module_service_access_log'

    # Identity
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Access details
    calling_module_id = Column(
        GUID,
        ForeignKey('modules.id', ondelete='SET NULL'),
        index=True
    )
    service_id = Column(
        GUID,
        ForeignKey('module_services.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    method_name = Column(String(100), nullable=False)

    # Request context
    user_id = Column(GUID, ForeignKey('users.id', ondelete='SET NULL'))
    tenant_id = Column(GUID, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    parameters = Column(JSON)  # Method parameters (sanitized)

    # Response
    success = Column(Boolean)
    error_message = Column(Text)
    execution_time_ms = Column(Integer)  # Milliseconds

    # Permissions
    permission_checked = Column(String(200))  # Permission that was checked

    # Audit
    accessed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    calling_module = relationship("Module", foreign_keys=[calling_module_id])
    service = relationship("ModuleService", back_populates="access_logs")
    user = relationship("User", foreign_keys=[user_id])
    tenant = relationship("Tenant", foreign_keys=[tenant_id])

    # Constraints
    __table_args__ = (
        Index('idx_service_access_calling_module', 'calling_module_id'),
        Index('idx_service_access_service', 'service_id'),
        Index('idx_service_access_time', 'accessed_at'),
        Index('idx_service_access_tenant', 'tenant_id'),
    )

    def __repr__(self):
        status = 'success' if self.success else 'error'
        return f"<ModuleServiceAccessLog(method='{self.method_name}', status='{status}')>"
