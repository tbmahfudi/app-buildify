from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship

from .base import GUID, Base, generate_uuid


class RolePermission(Base):
    """
    Junction table: Role → Permission (N:M)

    Assigns permissions to roles.
    """
    __tablename__ = "role_permissions"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Foreign keys
    role_id = Column(GUID, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(GUID, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    granted_by_user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")

    # Constraints
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )

    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"


class UserRole(Base):
    """
    Junction table: User → Role (N:M)

    Assigns roles directly to users.
    """
    __tablename__ = "user_roles"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Foreign keys
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(GUID, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    granted_by_user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="user_roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
    )

    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class UserGroup(Base):
    """
    Junction table: User → Group (N:M)

    Adds users to groups.
    """
    __tablename__ = "user_groups"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Foreign keys
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id = Column(GUID, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    added_by_user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="user_groups", foreign_keys=[user_id])
    group = relationship("Group", back_populates="user_groups")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'group_id', name='uq_user_group'),
    )

    def __repr__(self):
        return f"<UserGroup(user_id={self.user_id}, group_id={self.group_id})>"


class GroupRole(Base):
    """
    Junction table: Group → Role (N:M)

    Assigns roles to groups.
    """
    __tablename__ = "group_roles"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Foreign keys
    group_id = Column(GUID, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(GUID, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    granted_by_user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    group = relationship("Group", back_populates="group_roles")
    role = relationship("Role", back_populates="group_roles")

    # Constraints
    __table_args__ = (
        UniqueConstraint('group_id', 'role_id', name='uq_group_role'),
    )

    def __repr__(self):
        return f"<GroupRole(group_id={self.group_id}, role_id={self.role_id})>"
