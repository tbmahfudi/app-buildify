"""
Unified Module System Models

Merges the previous ModuleRegistry (code-delivered modules) and NocodeModule
(user-designed modules) into a single unified module system.

Models:
- Module: Unified module registry with semantic versioning, marketplace fields,
  and nocode capabilities.
- ModuleActivation: Per-tenant (and optionally per-company/branch/department)
  activation with configuration overrides.
- ModuleDependency: Cross-module dependencies with version constraints.
- ModuleVersion: Version history and snapshots.
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, ForeignKey, DateTime,
    UniqueConstraint, CheckConstraint, Index, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base, GUID, generate_uuid


class Module(Base):
    """
    Unified Module Registry

    Represents any module in the platform, whether code-delivered (e.g. Financial)
    or user-designed (nocode). Combines fields from the old ModuleRegistry and
    NocodeModule tables into a single model.

    Module types:
    - 'code': Code-delivered modules with backend services (e.g., Financial)
    - 'nocode': User-designed modules via the nocode platform
    - 'hybrid': Code modules extended with nocode components
    """
    __tablename__ = 'modules'

    # Identity
    id = Column(GUID, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)

    # Module type
    module_type = Column(String(20), nullable=False, default='nocode', index=True)  # code, nocode, hybrid

    # Versioning (Semantic Versioning: MAJOR.MINOR.PATCH)
    version = Column(String(50), nullable=False, default='1.0.0')
    major_version = Column(Integer, nullable=False, default=1)
    minor_version = Column(Integer, nullable=False, default=0)
    patch_version = Column(Integer, nullable=False, default=0)

    # Nocode: table naming (no underscore in prefix, max 10 chars)
    # NULL for code-delivered modules that manage their own tables
    table_prefix = Column(String(10), unique=True, nullable=True, index=True)

    # Metadata
    category = Column(String(50), index=True)  # hr, finance, sales, crm, etc.
    tags = Column(JSON, default=list)
    icon = Column(String(50))  # Phosphor icon name
    color = Column(String(7))  # Hex color for UI
    author = Column(String(255))
    license = Column(String(100))

    # Status
    status = Column(String(50), nullable=False, default='draft', index=True)
    # code modules: available, stable, beta, deprecated
    # nocode modules: draft, active, deprecated, archived

    is_installed = Column(Boolean, default=False, nullable=False, index=True)
    is_core = Column(Boolean, default=False, nullable=False)  # Core modules can't be disabled
    is_template = Column(Boolean, default=False)  # Available as template

    # Organization (NULL = platform-level)
    tenant_id = Column(GUID, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True)

    # Installation tracking (for code modules)
    installed_at = Column(DateTime)
    installed_by_user_id = Column(GUID, ForeignKey('users.id', ondelete='SET NULL'))

    # Configuration & Manifest
    manifest = Column(JSON)  # Full manifest data (code modules)
    configuration = Column(JSON)  # Module-specific default config / nocode config
    permissions = Column(JSON, default=list)  # Custom permissions this module defines

    # Dependencies (simple JSON for code modules; structured via ModuleDependency for nocode)
    dependencies_json = Column(JSON)  # {"required": ["module1"], "optional": ["module2"]}

    # Subscription / Marketplace
    subscription_tier = Column(String(50))  # basic, premium, enterprise
    pricing_model = Column(String(50))  # per_company, per_user, flat

    # API information (code modules)
    api_prefix = Column(String(100))  # e.g., /api/v1/financial

    # Database information (code modules)
    has_migrations = Column(Boolean, default=False, nullable=False)
    database_tables = Column(JSON)  # List of tables this module creates

    # Support
    homepage = Column(String(500))
    repository = Column(String(500))
    support_email = Column(String(255))

    # Audit
    created_by = Column(GUID, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_by = Column(GUID, ForeignKey('users.id'))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    published_by = Column(GUID, ForeignKey('users.id'))

    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id], backref="modules")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    publisher = relationship("User", foreign_keys=[published_by])
    installed_by = relationship("User", foreign_keys=[installed_by_user_id])

    activations = relationship(
        "ModuleActivation",
        back_populates="module",
        cascade="all, delete-orphan"
    )

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

    services = relationship(
        "ModuleService",
        back_populates="module",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "module_type IN ('code', 'nocode', 'hybrid')",
            name='valid_module_type'
        ),
    )

    def __repr__(self):
        return f"<Module(name='{self.name}', type='{self.module_type}', version='{self.version}', status='{self.status}')>"


class ModuleActivation(Base):
    """
    Module Activation

    Tracks which modules are activated at various organizational levels:
    - Tenant-level activation (required)
    - Company-level override (optional)
    - Branch-level override (optional)
    - Department-level override (optional)

    Replaces the old TenantModule and CompanyModule tables with a single
    flexible activation model that supports any organizational scope.
    """
    __tablename__ = 'module_activations'

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Module reference
    module_id = Column(GUID, ForeignKey('modules.id', ondelete='CASCADE'), nullable=False, index=True)

    # Organizational scope (at least tenant_id is required)
    tenant_id = Column(GUID, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    company_id = Column(GUID, ForeignKey('companies.id', ondelete='CASCADE'), nullable=True, index=True)
    branch_id = Column(GUID, ForeignKey('branches.id', ondelete='CASCADE'), nullable=True, index=True)
    department_id = Column(GUID, ForeignKey('departments.id', ondelete='CASCADE'), nullable=True, index=True)

    # Status
    is_enabled = Column(Boolean, default=False, nullable=False, index=True)
    is_configured = Column(Boolean, default=False, nullable=False)

    # Scope-specific configuration overrides
    configuration = Column(JSON)

    # Feature toggles
    enabled_features = Column(JSON)  # ["invoicing", "payments", "reports"]
    disabled_features = Column(JSON)  # ["multi_currency", "advanced_reporting"]

    # Activation tracking
    enabled_at = Column(DateTime)
    enabled_by_user_id = Column(GUID, ForeignKey('users.id', ondelete='SET NULL'))
    disabled_at = Column(DateTime)
    disabled_by_user_id = Column(GUID, ForeignKey('users.id', ondelete='SET NULL'))

    # Usage tracking
    usage_count = Column(JSON)  # Track usage metrics
    last_used_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    module = relationship("Module", back_populates="activations")
    tenant = relationship("Tenant", foreign_keys=[tenant_id], backref="module_activations")
    company = relationship("Company", foreign_keys=[company_id], backref="module_activations")
    branch = relationship("Branch", foreign_keys=[branch_id], backref="module_activations")
    department = relationship("Department", foreign_keys=[department_id], backref="module_activations")
    enabled_by = relationship("User", foreign_keys=[enabled_by_user_id])
    disabled_by = relationship("User", foreign_keys=[disabled_by_user_id])

    # Constraints
    __table_args__ = (
        # Unique activation per scope level
        UniqueConstraint(
            'module_id', 'tenant_id', 'company_id', 'branch_id', 'department_id',
            name='unique_module_activation_scope'
        ),
        Index('idx_module_activations_tenant', 'tenant_id'),
        Index('idx_module_activations_module', 'module_id'),
        Index('idx_module_activations_company', 'company_id'),
    )

    @property
    def scope_level(self) -> str:
        """Return the most specific scope level of this activation."""
        if self.department_id:
            return 'department'
        if self.branch_id:
            return 'branch'
        if self.company_id:
            return 'company'
        return 'tenant'

    def __repr__(self):
        return f"<ModuleActivation(module_id={self.module_id}, tenant_id={self.tenant_id}, scope={self.scope_level}, enabled={self.is_enabled})>"


# ============================================================
# Backward-compatible aliases for gradual migration
# ============================================================
# These allow existing code that imports ModuleRegistry / TenantModule / NocodeModule
# to continue working without immediate changes to every file.
ModuleRegistry = Module
TenantModule = ModuleActivation
NocodeModule = Module
CompanyModule = ModuleActivation  # CompanyModule was unused; alias for safety


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
        ForeignKey('modules.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    depends_on_module_id = Column(
        GUID,
        ForeignKey('modules.id', ondelete='RESTRICT'),
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
        "Module",
        foreign_keys=[module_id],
        back_populates="dependencies"
    )
    depends_on_module = relationship(
        "Module",
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
        ForeignKey('modules.id', ondelete='CASCADE'),
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
    module = relationship("Module", back_populates="versions")
    creator = relationship("User", foreign_keys=[created_by])

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "change_type IN ('major', 'minor', 'patch', 'hotfix')",
            name='valid_change_type'
        ),
        UniqueConstraint('module_id', 'version', name='unique_module_version'),
        Index('idx_module_versions_module', 'module_id'),
        Index('idx_module_versions_current', 'module_id', 'is_current'),
        Index('idx_module_versions_number', 'module_id', 'version_number'),
    )

    def __repr__(self):
        return f"<ModuleVersion(module_id='{self.module_id}', version='{self.version}', change_type='{self.change_type}')>"
