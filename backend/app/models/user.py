from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base, GUID, generate_uuid


class User(Base):
    """
    User entity for authentication and authorization.

    Users belong to ONE tenant but can access MULTIPLE companies within that tenant.
    """
    __tablename__ = "users"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Multi-tenancy (REQUIRED)
    tenant_id = Column(GUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Default company (OPTIONAL - user can access multiple companies)
    default_company_id = Column(GUID, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)

    # Organization assignment (OPTIONAL)
    branch_id = Column(GUID, ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(GUID, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Extra data (JSON)
    extra_data = Column(Text, nullable=True)  # JSON: custom fields

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    default_company = relationship("Company", foreign_keys=[default_company_id])
    branch = relationship("Branch")
    department = relationship("Department")

    # Multi-company access
    company_accesses = relationship("UserCompanyAccess", back_populates="user",
                                   foreign_keys="[UserCompanyAccess.user_id]",
                                   cascade="all, delete-orphan")

    # RBAC
    user_roles = relationship("UserRole", back_populates="user",
                             foreign_keys="[UserRole.user_id]",
                             cascade="all, delete-orphan")
    user_groups = relationship("UserGroup", back_populates="user",
                              foreign_keys="[UserGroup.user_id]",
                              cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, tenant_id={self.tenant_id})>"

    def has_company_access(self, company_id: str, access_level: str = None) -> bool:
        """
        Check if user has access to a specific company.

        Args:
            company_id: The company ID to check
            access_level: Optional access level to check (full, read, restricted)

        Returns:
            True if user has access, False otherwise
        """
        for access in self.company_accesses:
            if str(access.company_id) == str(company_id):
                if access_level is None:
                    return True
                return access.access_level == access_level
        return False

    def get_accessible_companies(self):
        """Get list of companies this user can access."""
        return [access.company for access in self.company_accesses if access.company]

    def get_permissions(self):
        """
        Get all permissions for this user from direct roles and group roles.

        Returns:
            Set of permission codes
        """
        permissions = set()

        # Get permissions from direct user roles
        for user_role in self.user_roles:
            if user_role.role and user_role.role.is_active:
                for role_perm in user_role.role.role_permissions:
                    if role_perm.permission and role_perm.permission.is_active:
                        permissions.add(role_perm.permission.code)

        # Get permissions from group roles
        for user_group in self.user_groups:
            if user_group.group and user_group.group.is_active:
                for group_role in user_group.group.group_roles:
                    if group_role.role and group_role.role.is_active:
                        for role_perm in group_role.role.role_permissions:
                            if role_perm.permission and role_perm.permission.is_active:
                                permissions.add(role_perm.permission.code)

        return permissions
