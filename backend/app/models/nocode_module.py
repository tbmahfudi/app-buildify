"""
No-Code Module Models

Models for the Module System Foundation (Phase 4):
- NocodeModule: Module registry with semantic versioning
- ModuleDependency: Cross-module dependencies
- ModuleVersion: Version history and snapshots
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DateTime, UniqueConstraint, CheckConstraint, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.models.base import Base, GUID, generate_uuid


class NocodeModule(Base):
    """
    No-Code Module Registry

    Represents a business domain module with semantic versioning,
    dependencies, and component grouping.

    Table naming convention: {table_prefix}_{entity_name}
    - table_prefix: max 10 chars, lowercase alphanumeric, no underscore within
    - Example: hr_employees, payroll_payslips, support_tickets
    """
    __tablename__ = 'nocode_modules'

    # Identity
    id = Column(GUID, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text)

    # Versioning (Semantic Versioning: MAJOR.MINOR.PATCH)
    version = Column(String(20), nullable=False, default='1.0.0')
    major_version = Column(Integer, nullable=False, default=1)
    minor_version = Column(Integer, nullable=False, default=0)
    patch_version = Column(Integer, nullable=False, default=0)

    # Table naming (no underscore in prefix, max 10 chars)
    table_prefix = Column(String(10), nullable=False, unique=True, index=True)

    # Metadata
    category = Column(String(50))  # hr, finance, sales, crm, etc.
    tags = Column(JSON, default=list)
    icon = Column(String(50))  # Phosphor icon name
    color = Column(String(7))  # Hex color for UI

    # Status
    status = Column(String(20), nullable=False, default='draft', index=True)
    is_core = Column(Boolean, default=False)  # Core platform module
    is_template = Column(Boolean, default=False)  # Available as template

    # Organization (NULL = platform-level template)
    tenant_id = Column(GUID, ForeignKey('tenants.id', ondelete='CASCADE'), index=True)

    # Permissions
    permissions = Column(JSON, default=list)  # Custom permissions this module defines

    # Configuration
    config = Column(JSON, default=dict)  # Module-specific configuration

    # Audit
    created_by = Column(GUID, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_by = Column(GUID, ForeignKey('users.id'))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    published_by = Column(GUID, ForeignKey('users.id'))

    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id], backref="nocode_modules")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    publisher = relationship("User", foreign_keys=[published_by])

    dependencies = relationship(
        "ModuleDependency",
        foreign_keys="[ModuleDependency.module_id]",
        back_populates="module",
        cascade="all, delete-orphan"
    )

    depended_by = relationship(
        "ModuleDependency",
        foreign_keys="[ModuleDependency.depends_on_module_id]",
        back_populates="depends_on_module"
    )

    versions = relationship(
        "ModuleVersion",
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="desc(ModuleVersion.version_number)"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "version ~ '^[0-9]+\\.[0-9]+\\.[0-9]+$'",
            name='valid_version'
        ),
        CheckConstraint(
            "table_prefix ~ '^[a-z0-9]{1,10}$'",
            name='valid_prefix'
        ),
        CheckConstraint(
            "status IN ('draft', 'active', 'deprecated', 'archived')",
            name='valid_status'
        ),
    )

    def __repr__(self):
        return f"<NocodeModule(name='{self.name}', version='{self.version}', status='{self.status}')>"


class ModuleDependency(Base):
    """
    Module Dependencies

    Defines relationships between modules with version constraints.
    Supports required, optional, and conflict declarations.
    """
    __tablename__ = 'module_dependencies'

    # Identity
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Relationship
    module_id = Column(
        GUID,
        ForeignKey('nocode_modules.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    depends_on_module_id = Column(
        GUID,
        ForeignKey('nocode_modules.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )

    # Dependency type
    dependency_type = Column(String(20), nullable=False, default='required')

    # Version constraints (Semantic Versioning)
    min_version = Column(String(20))  # Minimum version (inclusive)
    max_version = Column(String(20))  # Maximum version (exclusive)
    version_constraint = Column(String(100))  # e.g., ">=1.5.0, <2.0.0"

    # Metadata
    reason = Column(Text)  # Why this dependency exists

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(GUID, ForeignKey('users.id'))

    # Relationships
    module = relationship(
        "NocodeModule",
        foreign_keys=[module_id],
        back_populates="dependencies"
    )
    depends_on_module = relationship(
        "NocodeModule",
        foreign_keys=[depends_on_module_id],
        back_populates="depended_by"
    )
    creator = relationship("User", foreign_keys=[created_by])

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "dependency_type IN ('required', 'optional', 'conflicts')",
            name='valid_dependency_type'
        ),
        CheckConstraint(
            "module_id != depends_on_module_id",
            name='no_self_dependency'
        ),
        UniqueConstraint('module_id', 'depends_on_module_id', name='unique_module_dependency'),
        Index('idx_module_dependencies_module', 'module_id'),
        Index('idx_module_dependencies_depends_on', 'depends_on_module_id'),
    )

    def __repr__(self):
        return f"<ModuleDependency(module_id='{self.module_id}', depends_on='{self.depends_on_module_id}', type='{self.dependency_type}')>"


class ModuleVersion(Base):
    """
    Module Version History

    Tracks all versions of a module with complete snapshots.
    Enables rollback and version comparison.
    """
    __tablename__ = 'module_versions'

    # Identity
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Module reference
    module_id = Column(
        GUID,
        ForeignKey('nocode_modules.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Version info
    version = Column(String(20), nullable=False)
    version_number = Column(Integer, nullable=False)  # Auto-increment per module
    major_version = Column(Integer, nullable=False)
    minor_version = Column(Integer, nullable=False)
    patch_version = Column(Integer, nullable=False)

    # Change tracking
    change_type = Column(String(20), nullable=False)  # major, minor, patch, hotfix
    change_summary = Column(Text, nullable=False)
    changelog = Column(Text)
    breaking_changes = Column(Text)

    # Snapshot (full module state at this version)
    snapshot = Column(JSON, nullable=False)  # Complete module definition

    # Status
    is_current = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(GUID, ForeignKey('users.id'))

    # Relationships
    module = relationship("NocodeModule", back_populates="versions")
    creator = relationship("User", foreign_keys=[created_by])

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "change_type IN ('major', 'minor', 'patch', 'hotfix')",
            name='valid_change_type'
        ),
        UniqueConstraint('module_id', 'version', name='unique_module_version'),
        Index('idx_module_versions_module', 'module_id'),
        Index('idx_module_versions_current', 'module_id', 'is_current', postgresql_where=(is_current == True)),
        Index('idx_module_versions_number', 'module_id', 'version_number'),
    )

    def __repr__(self):
        return f"<ModuleVersion(module_id='{self.module_id}', version='{self.version}', change_type='{self.change_type}')>"
