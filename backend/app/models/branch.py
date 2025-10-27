from sqlalchemy import Column, String, ForeignKey, DateTime, func, Boolean, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base, GUID, generate_uuid


class Branch(Base):
    """
    Branch entity - represents a physical location or branch of a company.

    Branches belong to a company and can have departments.
    """
    __tablename__ = "branches"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Multi-tenancy (REQUIRED)
    tenant_id = Column(GUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(GUID, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Contact
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)

    # Geolocation
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_headquarters = Column(Boolean, default=False, nullable=False)

    # Metadata (JSON)
    metadata = Column(Text, nullable=True)  # JSON: custom fields

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    company = relationship("Company", back_populates="branches")
    departments = relationship("Department", back_populates="branch", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'company_id', 'code', name='uq_branch_company_code'),
    )

    def __repr__(self):
        return f"<Branch(id={self.id}, name={self.name}, company_id={self.company_id})>"
