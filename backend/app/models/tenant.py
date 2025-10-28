from sqlalchemy import Column, String, Boolean, Integer, DateTime, func, Text
from sqlalchemy.orm import relationship
from .base import Base, GUID, generate_uuid


class Tenant(Base):
    """
    Top-level tenant entity for multi-company architecture.

    A tenant represents a customer/organization that can have multiple companies.
    All data is isolated at the tenant level.
    """
    __tablename__ = "tenants"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Subscription info
    subscription_tier = Column(String(50), default="free", nullable=False)  # free, basic, premium, enterprise
    subscription_status = Column(String(50), default="active", nullable=False)  # active, suspended, cancelled
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)

    # Limits
    max_companies = Column(Integer, default=10, nullable=False)
    max_users = Column(Integer, default=500, nullable=False)
    max_storage_gb = Column(Integer, default=10, nullable=False)

    # Usage (updated periodically)
    current_companies = Column(Integer, default=0, nullable=False)
    current_users = Column(Integer, default=0, nullable=False)
    current_storage_gb = Column(Integer, default=0, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_trial = Column(Boolean, default=False, nullable=False)

    # Contact
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)

    # Branding
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), nullable=True)  # Hex color

    # Extra data (JSON)
    extra_data = Column(Text, nullable=True)  # JSON: custom fields

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    companies = relationship("Company", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="tenant", cascade="all, delete-orphan")
    roles = relationship("Role", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, code={self.code})>"
