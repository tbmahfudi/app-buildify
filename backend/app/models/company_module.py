from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from .base import GUID, Base, generate_uuid


class CompanyModule(Base):
    """
    Company-level module configuration and customization.
    Allows each company within a tenant to have custom module settings.
    This enables fine-grained control where different companies in the same
    tenant can have different module configurations.
    """
    __tablename__ = "company_modules"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Foreign keys
    company_id = Column(GUID, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_module_id = Column(GUID, ForeignKey("tenant_modules.id", ondelete="CASCADE"), nullable=False, index=True)

    # Status - can disable module at company level even if enabled at tenant level
    is_enabled = Column(Boolean, default=True, nullable=False, index=True)

    # Company-specific configuration overrides
    # This overrides both module defaults and tenant configuration
    configuration = Column(JSON, nullable=True)

    # Feature toggles - enable/disable specific features within a module
    enabled_features = Column(JSON, nullable=True)  # ["invoicing", "payments", "reports"]
    disabled_features = Column(JSON, nullable=True)  # ["multi_currency", "advanced_reporting"]

    # Customization metadata
    customized_at = Column(DateTime, nullable=True)
    customized_by_user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Usage tracking (optional, for analytics/billing)
    last_accessed_at = Column(DateTime, nullable=True)
    access_count = Column(JSON, nullable=True)  # {"2024-01": 150, "2024-02": 200}

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    company = relationship("Company", backref="company_modules")
    tenant_module = relationship("TenantModule", backref="company_modules")
    customized_by = relationship("User", foreign_keys=[customized_by_user_id])

    def __repr__(self):
        return f"<CompanyModule(company_id={self.company_id}, module={self.tenant_module.module.name if self.tenant_module else 'N/A'}, enabled={self.is_enabled})>"

    def get_effective_config(self) -> dict:
        """
        Get the effective configuration for this company module.
        Merges module defaults -> tenant config -> company config.
        """
        if not self.tenant_module or not self.tenant_module.module:
            return {}

        # Start with module defaults
        module = self.tenant_module.module
        config = module.manifest.get("configuration", {}).get("defaults", {})

        # Apply tenant configuration
        if self.tenant_module.configuration:
            config = self._deep_merge(config, self.tenant_module.configuration)

        # Apply company configuration (highest priority)
        if self.configuration:
            config = self._deep_merge(config, self.configuration)

        return config

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = CompanyModule._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
