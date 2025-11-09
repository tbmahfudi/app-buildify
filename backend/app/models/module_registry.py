from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, func
from sqlalchemy.orm import relationship
from .base import Base, GUID, generate_uuid


class ModuleRegistry(Base):
    """
    Tracks installed and enabled modules in the platform.
    This is a platform-wide registry of all available modules.
    """
    __tablename__ = "module_registry"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Module identification
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    # Module metadata
    category = Column(String(50), nullable=True, index=True)  # finance, healthcare, warehousing, etc.
    tags = Column(JSON, nullable=True)  # ["accounting", "invoicing"]
    author = Column(String(255), nullable=True)
    license = Column(String(100), nullable=True)

    # Status
    is_installed = Column(Boolean, default=False, nullable=False, index=True)
    is_enabled = Column(Boolean, default=False, nullable=False)
    is_core = Column(Boolean, default=False, nullable=False)  # Core modules can't be disabled

    # Installation tracking
    installed_at = Column(DateTime, nullable=True)
    installed_by_user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Configuration
    manifest = Column(JSON, nullable=False)  # Full manifest data
    configuration = Column(JSON, nullable=True)  # Module-specific default config

    # Dependencies
    dependencies = Column(JSON, nullable=True)  # {"required": ["module1"], "optional": ["module2"]}

    # Subscription requirements
    subscription_tier = Column(String(50), nullable=True)  # Which tier needed: basic, premium, enterprise
    pricing_model = Column(String(50), nullable=True)  # per_company, per_user, flat

    # API information
    api_prefix = Column(String(100), nullable=True)  # e.g., /api/v1/financial

    # Database information
    has_migrations = Column(Boolean, default=False, nullable=False)
    database_tables = Column(JSON, nullable=True)  # List of tables this module creates

    # Status tracking
    status = Column(String(50), default="available", nullable=False)  # available, stable, beta, deprecated

    # Support
    homepage = Column(String(500), nullable=True)
    repository = Column(String(500), nullable=True)
    support_email = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    tenant_modules = relationship("TenantModule", back_populates="module", cascade="all, delete-orphan")
    installed_by = relationship("User", foreign_keys=[installed_by_user_id])

    def __repr__(self):
        return f"<ModuleRegistry(name={self.name}, version={self.version}, installed={self.is_installed})>"


class TenantModule(Base):
    """
    Tracks which modules are enabled per tenant.
    Per-tenant module activation and configuration.
    """
    __tablename__ = "tenant_modules"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Foreign keys
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False, index=True)
    module_id = Column(GUID, ForeignKey("module_registry.id"), nullable=False, index=True)

    # Status
    is_enabled = Column(Boolean, default=False, nullable=False, index=True)
    is_configured = Column(Boolean, default=False, nullable=False)

    # Tenant-specific configuration
    configuration = Column(JSON, nullable=True)  # Overrides default module configuration

    # Activation tracking
    enabled_at = Column(DateTime, nullable=True)
    enabled_by_user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    disabled_at = Column(DateTime, nullable=True)
    disabled_by_user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Usage tracking (optional, for billing)
    usage_count = Column(JSON, nullable=True)  # Track usage metrics
    last_used_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", backref="tenant_modules")
    module = relationship("ModuleRegistry", back_populates="tenant_modules")
    enabled_by = relationship("User", foreign_keys=[enabled_by_user_id])
    disabled_by = relationship("User", foreign_keys=[disabled_by_user_id])

    def __repr__(self):
        return f"<TenantModule(tenant_id={self.tenant_id}, module={self.module.name}, enabled={self.is_enabled})>"
