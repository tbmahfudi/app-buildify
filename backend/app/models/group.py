from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey, Text, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base, GUID, generate_uuid


class Group(Base):
    """
    Group entity - represents a team or collection of users.

    Groups can be:
    - Tenant-scoped (company_id is NULL): Available to all companies in tenant
    - Company-scoped (company_id is set): Specific to a company

    Groups simplify role assignment - assign roles to groups, add users to groups.
    """
    __tablename__ = "groups"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Scoping (REQUIRED)
    tenant_id = Column(GUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Optional: Company-specific group
    company_id = Column(GUID, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    # NULL = tenant-wide group, NOT NULL = company-specific group

    # Basic info
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Group type
    group_type = Column(String(50), default="team", nullable=False, index=True)
    # - team: Regular team group
    # - department: Department-based group
    # - project: Project-based group
    # - custom: Custom group

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    created_by_user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="groups")
    company = relationship("Company", back_populates="groups")
    user_groups = relationship("UserGroup", back_populates="group", cascade="all, delete-orphan")
    group_roles = relationship("GroupRole", back_populates="group", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        # Group code must be unique per tenant + company combination
        UniqueConstraint('tenant_id', 'company_id', 'code', name='uq_group_tenant_company_code'),
        Index('ix_group_tenant_company', 'tenant_id', 'company_id'),
    )

    def __repr__(self):
        scope = "tenant" if self.company_id is None else f"company:{self.company_id}"
        return f"<Group(code={self.code}, name={self.name}, scope={scope})>"
