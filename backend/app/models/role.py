from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from .base import GUID, Base, generate_uuid


class Role(Base):
    """
    Role entity - represents a job function or position.

    Roles can be:
    - System roles (tenant_id is NULL): Available to all tenants (e.g., superuser, admin)
    - Tenant roles (tenant_id is set): Custom roles for specific tenant

    Roles contain collections of permissions.
    """
    __tablename__ = "roles"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Scoping
    tenant_id = Column(GUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    # NULL = system role, NOT NULL = tenant-specific role

    # Basic info
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Role type
    role_type = Column(String(50), default="custom", nullable=False, index=True)
    # - system: Built-in system roles (superuser, admin)
    # - default: Default roles for tenants (user, viewer)
    # - custom: Custom roles created by tenants

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_system = Column(Boolean, default=False, nullable=False)  # System roles can't be deleted

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    created_by_user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="roles")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    group_roles = relationship("GroupRole", back_populates="role", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        # System roles: code must be unique globally
        # Tenant roles: code must be unique per tenant
        UniqueConstraint('tenant_id', 'code', name='uq_role_tenant_code'),
        Index('ix_role_tenant_type', 'tenant_id', 'role_type'),
    )

    def __repr__(self):
        scope = "system" if self.tenant_id is None else f"tenant:{self.tenant_id}"
        return f"<Role(code={self.code}, name={self.name}, scope={scope})>"
