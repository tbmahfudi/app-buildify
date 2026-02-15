"""
Base Module Class

All pluggable modules must inherit from this base class and implement
the required abstract methods.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from fastapi import APIRouter
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BaseModule(ABC):
    """
    Base class for all pluggable modules.

    Provides:
    - Manifest loading
    - Lifecycle hooks (pre/post install, enable, disable)
    - Router registration
    - Permission registration
    - Configuration management
    """

    def __init__(self, module_path: Path):
        """
        Initialize the module.

        Args:
            module_path: Path to the module directory
        """
        self.module_path = module_path
        self.manifest = self._load_manifest()
        self.name = self.manifest.get("name")
        self.version = self.manifest.get("version")
        self.display_name = self.manifest.get("display_name", self.name)
        self.router: Optional[APIRouter] = None

        if not self.name or not self.version:
            raise ValueError(f"Module manifest must contain 'name' and 'version' fields")

    def _load_manifest(self) -> Dict[str, Any]:
        """
        Load module manifest.json file.

        Returns:
            Dictionary containing manifest data

        Raises:
            FileNotFoundError: If manifest.json doesn't exist
            json.JSONDecodeError: If manifest is invalid JSON
        """
        manifest_path = self.module_path / "manifest.json"

        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found at {manifest_path}")

        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            logger.info(f"Loaded manifest for module: {manifest.get('name')}")
            return manifest
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in manifest: {e}")
            raise

    @abstractmethod
    def get_router(self) -> APIRouter:
        """
        Return the FastAPI router for this module.

        This method must be implemented by all modules to define
        their API endpoints.

        Returns:
            APIRouter instance with module endpoints
        """
        pass

    @abstractmethod
    def get_permissions(self) -> List[Dict[str, Any]]:
        """
        Return list of permissions this module defines.

        Each permission should be a dictionary with:
        - code: Permission code (e.g., "financial:invoices:create:company")
        - name: Human-readable name
        - description: What the permission allows
        - category: Category for grouping
        - scope: Access scope (all, tenant, company, department, own)

        Returns:
            List of permission dictionaries
        """
        pass

    def get_models(self) -> List[Any]:
        """
        Return list of SQLAlchemy models for migration discovery.

        Override this method if your module defines database models.

        Returns:
            List of SQLAlchemy model classes
        """
        return []

    def get_default_configuration(self) -> Dict[str, Any]:
        """
        Return default configuration values for this module.

        Configuration settings are defined in the manifest under
        'configuration.settings'.

        Returns:
            Dictionary of configuration key-value pairs
        """
        config_settings = self.manifest.get("configuration", {}).get("settings", [])

        # Convert list of setting objects to dict of key-value pairs
        default_config = {}
        for setting in config_settings:
            key = setting.get("key")
            default_value = setting.get("default")
            if key:
                default_config[key] = default_value

        return default_config

    def validate_configuration(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate configuration values.

        Override this method to add custom validation logic.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation: check if all required keys are present
        default_config = self.get_default_configuration()

        for key in default_config.keys():
            if key not in config:
                return False, f"Missing required configuration key: {key}"

        return True, None

    def check_dependencies(self, installed_modules: List[str]) -> tuple[bool, Optional[str]]:
        """
        Check if required dependencies are installed.

        Args:
            installed_modules: List of installed module names

        Returns:
            Tuple of (dependencies_met, error_message)
        """
        required = self.manifest.get("dependencies", {}).get("required", [])

        missing = [dep for dep in required if dep not in installed_modules]

        if missing:
            return False, f"Missing required dependencies: {', '.join(missing)}"

        return True, None

    def check_subscription_tier(self, tenant_subscription_tier: str) -> bool:
        """
        Check if tenant's subscription tier meets module requirements.

        Args:
            tenant_subscription_tier: Tenant's current subscription tier

        Returns:
            True if tenant can use this module, False otherwise
        """
        required_tier = self.manifest.get("subscription_tier")

        if not required_tier:
            # No subscription requirement
            return True

        # Define tier hierarchy
        tier_hierarchy = {
            "free": 0,
            "basic": 1,
            "premium": 2,
            "enterprise": 3
        }

        tenant_level = tier_hierarchy.get(tenant_subscription_tier, 0)
        required_level = tier_hierarchy.get(required_tier, 0)

        return tenant_level >= required_level

    # Lifecycle hooks

    def pre_install(self, db_session: Any) -> tuple[bool, Optional[str]]:
        """
        Hook called before module installation.

        Use this to check prerequisites, validate environment, etc.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Tuple of (should_proceed, error_message)
        """
        logger.info(f"Running pre-install checks for {self.name}")
        return True, None

    def post_install(self, db_session: Any) -> None:
        """
        Hook called after module installation.

        Use this to create default data, run migrations, etc.

        Args:
            db_session: SQLAlchemy database session
        """
        logger.info(f"Running post-install tasks for {self.name}")
        pass

    def pre_enable(self, db_session: Any, tenant_id: str) -> tuple[bool, Optional[str]]:
        """
        Hook called before module is enabled for a tenant.

        Use this to validate tenant-specific prerequisites.

        Args:
            db_session: SQLAlchemy database session
            tenant_id: ID of the tenant enabling the module

        Returns:
            Tuple of (should_proceed, error_message)
        """
        logger.info(f"Running pre-enable checks for {self.name} on tenant {tenant_id}")
        return True, None

    def post_enable(self, db_session: Any, tenant_id: str) -> None:
        """
        Hook called after module is enabled for tenant.

        Use this to create tenant-specific data, configuration, etc.

        Args:
            db_session: SQLAlchemy database session
            tenant_id: ID of the tenant
        """
        logger.info(f"Running post-enable tasks for {self.name} on tenant {tenant_id}")
        pass

    def pre_disable(self, db_session: Any, tenant_id: str) -> tuple[bool, Optional[str]]:
        """
        Hook called before module is disabled for a tenant.

        Use this to check if module can be safely disabled.

        Args:
            db_session: SQLAlchemy database session
            tenant_id: ID of the tenant

        Returns:
            Tuple of (should_proceed, error_message)
        """
        logger.info(f"Running pre-disable checks for {self.name} on tenant {tenant_id}")
        return True, None

    def post_disable(self, db_session: Any, tenant_id: str) -> None:
        """
        Hook called after module is disabled.

        Use this for cleanup, archiving data, etc.
        Note: Should not delete data, just disable functionality.

        Args:
            db_session: SQLAlchemy database session
            tenant_id: ID of the tenant
        """
        logger.info(f"Running post-disable tasks for {self.name} on tenant {tenant_id}")
        pass

    def pre_uninstall(self, db_session: Any) -> tuple[bool, Optional[str]]:
        """
        Hook called before module uninstallation.

        Use this to check if module can be safely uninstalled.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Tuple of (should_proceed, error_message)
        """
        logger.info(f"Running pre-uninstall checks for {self.name}")

        # Check if module is enabled for any tenants
        from app.models.nocode_module import Module as ModuleRegistry, ModuleActivation as TenantModule

        module = db_session.query(ModuleRegistry).filter(
            ModuleRegistry.name == self.name
        ).first()

        if module:
            enabled_tenants = db_session.query(TenantModule).filter(
                TenantModule.module_id == module.id,
                TenantModule.is_enabled == True
            ).count()

            if enabled_tenants > 0:
                return False, f"Module is enabled for {enabled_tenants} tenant(s). Disable for all tenants first."

        return True, None

    def post_uninstall(self, db_session: Any) -> None:
        """
        Hook called after module uninstallation.

        Use this for final cleanup.

        Args:
            db_session: SQLAlchemy database session
        """
        logger.info(f"Running post-uninstall tasks for {self.name}")
        pass

    def get_menu_items(self) -> List[Dict[str, Any]]:
        """
        Return menu items for frontend navigation.

        Extracted from routes in manifest that have menu configuration.

        Returns:
            List of menu item dictionaries
        """
        menu_items = []

        routes = self.manifest.get("routes", [])
        for route in routes:
            if "menu" in route:
                menu_items.append({
                    "path": route.get("path"),
                    "name": route.get("name"),
                    "permission": route.get("permission"),
                    "menu": route.get("menu")
                })

        return menu_items

    def __repr__(self):
        return f"<{self.__class__.__name__}(name={self.name}, version={self.version})>"
