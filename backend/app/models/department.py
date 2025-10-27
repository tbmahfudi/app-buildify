from sqlalchemy import Column, String, ForeignKey, DateTime, func, Boolean, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base, GUID, generate_uuid


class Department(Base):
    """
    Department entity - represents a functional unit within a company.

    Departments can be:
    - Company-wide (branch_id is NULL)
    - Branch-specific (branch_id is set)
    """
    __tablename__ = "departments"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Multi-tenancy (REQUIRED)
    tenant_id = Column(GUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(GUID, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)

    # Optional: Branch-specific department
    branch_id = Column(GUID, ForeignKey("branches.id", ondelete="CASCADE"), nullable=True, index=True)

    # Basic info
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Hierarchy
    parent_department_id = Column(GUID, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)

    # Head of department
    head_user_id = Column(GUID, nullable=True)  # FK to users.id (but not enforced to avoid circular deps)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Metadata (JSON)
    metadata = Column(Text, nullable=True)  # JSON: custom fields

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    company = relationship("Company", back_populates="departments")
    branch = relationship("Branch", back_populates="departments")
    parent_department = relationship("Department", remote_side=[id], foreign_keys=[parent_department_id])

    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'company_id', 'branch_id', 'code', name='uq_dept_branch_code'),
    )

    def __repr__(self):
        return f"<Department(id={self.id}, name={self.name}, company_id={self.company_id})>"
