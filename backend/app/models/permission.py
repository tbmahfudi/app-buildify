from sqlalchemy import Column, String, Boolean, DateTime, func, Text, Index
from sqlalchemy.orm import relationship
from .base import Base, GUID, generate_uuid


class Permission(Base):
    """
    Permission entity - represents an atomic access right.

    Permissions are system-wide and can be assigned to roles.
    Format: resource:action:scope

    Examples:
    - users:create:tenant
    - products:read:company
    - audit:export:all
    """
    __tablename__ = "permissions"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Permission identifier (unique)
    code = Column(String(100), unique=True, nullable=False, index=True)

    # Display info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Permission components
    resource = Column(String(50), nullable=False, index=True)  # users, products, companies, etc.
    action = Column(String(50), nullable=False, index=True)    # create, read, update, delete, export, etc.
    scope = Column(String(50), nullable=False, index=True)      # all, tenant, company, branch, department, own

    # Categorization
    category = Column(String(50), nullable=True, index=True)   # user_management, data, system, etc.

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_system = Column(Boolean, default=False, nullable=False)  # System permissions can't be deleted

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")

    # Composite indexes
    __table_args__ = (
        Index('ix_permission_resource_action_scope', 'resource', 'action', 'scope'),
    )

    def __repr__(self):
        return f"<Permission(code={self.code}, resource={self.resource}, action={self.action}, scope={self.scope})>"
