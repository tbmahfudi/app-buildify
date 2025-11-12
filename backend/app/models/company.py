from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from .base import GUID, Base, generate_uuid


class Company(Base):
    """
    Company entity - represents a business unit within a tenant.

    A tenant can have multiple companies (up to max_companies limit).
    Companies contain branches, departments, and other organizational entities.
    """
    __tablename__ = "companies"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Multi-tenancy (REQUIRED)
    tenant_id = Column(GUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Contact
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)

    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)

    # Tax/Legal
    tax_id = Column(String(50), nullable=True)
    registration_number = Column(String(50), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Extra data (JSON)
    extra_data = Column(Text, nullable=True)  # JSON: custom fields

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    tenant = relationship("Tenant", back_populates="companies")
    branches = relationship("Branch", back_populates="company", cascade="all, delete-orphan")
    departments = relationship("Department", back_populates="company", cascade="all, delete-orphan")
    user_accesses = relationship("UserCompanyAccess", back_populates="company", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="company", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'code', name='uq_company_tenant_code'),
    )

    def __repr__(self):
        return f"<Company(id={self.id}, name={self.name}, tenant_id={self.tenant_id})>"
