from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from .base import GUID, Base, generate_uuid


class UserCompanyAccess(Base):
    """
    User-Company access mapping.

    Allows a user to access multiple companies within their tenant.
    Defines the access level for each company.
    """
    __tablename__ = "user_company_access"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Foreign keys
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(GUID, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)

    # Access level
    access_level = Column(
        String(50),
        nullable=False,
        default="full",
        comment="Access level: full, read, restricted"
    )
    # - full: Can read and write all data
    # - read: Can only read data
    # - restricted: Limited access based on branch/department

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Optional: Restrict to specific branch/department
    branch_id = Column(GUID, ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(GUID, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)

    # Granted by
    granted_by_user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Who granted this access
    granted_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    revoked_at = Column(DateTime, nullable=True)  # When access was revoked

    # Relationships
    user = relationship("User", back_populates="company_accesses", foreign_keys=[user_id])
    company = relationship("Company", back_populates="user_accesses")
    branch = relationship("Branch")
    department = relationship("Department")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'company_id', name='uq_user_company_access'),
    )

    def __repr__(self):
        return f"<UserCompanyAccess(user_id={self.user_id}, company_id={self.company_id}, level={self.access_level})>"
