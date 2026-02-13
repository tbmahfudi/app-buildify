"""
Module Registry Service

Manages module registration, installation, and lifecycle operations.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path
import logging

from app.models.module_registry import ModuleRegistry, TenantModule
from app.models.permission import Permission
from app.models.tenant import Tenant
from .base_module import BaseModule
from .loader import ModuleLoader

logger = logging.getLogger(__name__)


class ModuleRegistryService:
    """
    Manages module registration, installation, and lifecycle.

    Provides:
    - Module discovery and registration in database
    - Module installation (platform-wide)
    - Module enablement/disablement per tenant
    - Permission registration
    - Configuration management
    - Dependency resolution
    """

    def __init__(self, db: Session, modules_path: Path):
        """
        Initialize the registry service.

        Args:
            db: SQLAlchemy database session
            modules_path: Path to modules directory
        """
        self.db = db
        self.loader = ModuleLoader(modules_path)
        self.modules: Dict[str, BaseModule] = {}

    def sync_modules(self) -> None:
        """
        Discover and sync modules with database registry.

        This should be run at app startup to:
        - Discover modules from filesystem
        - Register new modules in database
        - Update existing module manifests
        - Load modules into memory
        """
        logger.info("Syncing modules with database...")

        # Load all modules from filesystem
        discovered = self.loader.load_all_modules()

        for name, module_instance in discovered.items():
            try:
                # Check if module exists in registry
                registry_entry = self.db.query(ModuleRegistry).filter(
                    ModuleRegistry.name == name
                ).first()

                if not registry_entry:
                    # Register new module
                    registry_entry = ModuleRegistry(
                        name=name,
                        display_name=module_instance.display_name,
                        module_type='code',
                        version=module_instance.version,
                        description=module_instance.manifest.get("description"),
                        category=module_instance.manifest.get("category"),
                        tags=module_instance.manifest.get("tags"),
                        author=module_instance.manifest.get("author"),
                        license=module_instance.manifest.get("license"),
                        manifest=module_instance.manifest,
                        is_installed=False,
                        is_core=module_instance.manifest.get("is_core", False),
                        dependencies_json=module_instance.manifest.get("dependencies"),
                        subscription_tier=module_instance.manifest.get("subscription_tier"),
                        pricing_model=module_instance.manifest.get("pricing", {}).get("model"),
                        api_prefix=module_instance.manifest.get("api", {}).get("prefix"),
                        has_migrations=module_instance.manifest.get("database", {}).get("has_migrations", False),
                        database_tables=module_instance.manifest.get("database", {}).get("tables"),
                        status=module_instance.manifest.get("status", "available"),
                        homepage=module_instance.manifest.get("homepage"),
                        repository=module_instance.manifest.get("repository"),
                        support_email=module_instance.manifest.get("support_email"),
                    )
                    self.db.add(registry_entry)
                    logger.info(f"Registered new module: {name}")
                else:
                    # Update manifest if version changed
                    if registry_entry.version != module_instance.version:
                        registry_entry.version = module_instance.version
                        registry_entry.manifest = module_instance.manifest
                        registry_entry.display_name = module_instance.display_name
                        registry_entry.description = module_instance.manifest.get("description")
                        logger.info(f"Updated module {name} to version {module_instance.version}")

                self.modules[name] = module_instance

            except Exception as e:
                logger.error(f"Error syncing module {name}: {e}", exc_info=True)

        self.db.commit()
        logger.info(f"Synced {len(self.modules)} modules")

    def install_module(self, module_name: str, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Install a module platform-wide.

        Installation steps:
        1. Load module
        2. Check dependencies
        3. Run pre-install hooks
        4. Mark as installed in registry
        5. Register permissions
        6. Run post-install hooks

        Args:
            module_name: Name of the module to install
            user_id: ID of user performing installation

        Returns:
            Tuple of (success, error_message)
        """
        logger.info(f"Installing module: {module_name}")

        # Get module instance
        module = self.loader.get_module(module_name)
        if not module:
            return False, f"Module {module_name} not found"

        # Get registry entry
        registry_entry = self.db.query(ModuleRegistry).filter(
            ModuleRegistry.name == module_name
        ).first()

        if not registry_entry:
            return False, f"Module {module_name} not registered in database"

        if registry_entry.is_installed:
            return False, f"Module {module_name} is already installed"

        # Check dependencies
        installed_modules = [
            m.name for m in self.db.query(ModuleRegistry)
            .filter(ModuleRegistry.is_installed == True)
            .all()
        ]

        deps_ok, deps_error = module.check_dependencies(installed_modules)
        if not deps_ok:
            return False, deps_error

        # Pre-install hook
        try:
            proceed, error = module.pre_install(self.db)
            if not proceed:
                return False, error or "Pre-install check failed"
        except Exception as e:
            logger.error(f"Error in pre-install hook: {e}", exc_info=True)
            return False, f"Pre-install hook error: {str(e)}"

        # Mark as installed
        registry_entry.is_installed = True
        registry_entry.installed_by_user_id = user_id
        registry_entry.installed_at = datetime.utcnow()

        # Register permissions
        try:
            self._register_permissions(module)
        except Exception as e:
            logger.error(f"Error registering permissions: {e}", exc_info=True)
            self.db.rollback()
            return False, f"Permission registration error: {str(e)}"

        # Post-install hook
        try:
            module.post_install(self.db)
        except Exception as e:
            logger.error(f"Error in post-install hook: {e}", exc_info=True)
            self.db.rollback()
            return False, f"Post-install hook error: {str(e)}"

        self.db.commit()
        logger.info(f"Module {module_name} installed successfully")
        return True, None

    def uninstall_module(self, module_name: str) -> tuple[bool, Optional[str]]:
        """
        Uninstall a module platform-wide.

        Args:
            module_name: Name of the module to uninstall

        Returns:
            Tuple of (success, error_message)
        """
        logger.info(f"Uninstalling module: {module_name}")

        module = self.loader.get_module(module_name)
        if not module:
            return False, f"Module {module_name} not found"

        registry_entry = self.db.query(ModuleRegistry).filter(
            ModuleRegistry.name == module_name
        ).first()

        if not registry_entry:
            return False, f"Module {module_name} not registered"

        if not registry_entry.is_installed:
            return False, f"Module {module_name} is not installed"

        # Pre-uninstall hook
        try:
            proceed, error = module.pre_uninstall(self.db)
            if not proceed:
                return False, error or "Pre-uninstall check failed"
        except Exception as e:
            logger.error(f"Error in pre-uninstall hook: {e}", exc_info=True)
            return False, f"Pre-uninstall hook error: {str(e)}"

        # Mark as uninstalled
        registry_entry.is_installed = False
        registry_entry.is_enabled = False

        # Post-uninstall hook
        try:
            module.post_uninstall(self.db)
        except Exception as e:
            logger.error(f"Error in post-uninstall hook: {e}", exc_info=True)

        self.db.commit()
        logger.info(f"Module {module_name} uninstalled successfully")
        return True, None

    def enable_module_for_tenant(
        self,
        module_name: str,
        tenant_id: str,
        user_id: str,
        configuration: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Enable a module for a specific tenant.

        Args:
            module_name: Name of the module
            tenant_id: ID of the tenant
            user_id: ID of user enabling the module
            configuration: Optional tenant-specific configuration

        Returns:
            Tuple of (success, error_message)
        """
        logger.info(f"Enabling module {module_name} for tenant {tenant_id}")

        module = self.loader.get_module(module_name)
        if not module:
            return False, f"Module {module_name} not found"

        # Check if module is installed
        registry_entry = self.db.query(ModuleRegistry).filter(
            ModuleRegistry.name == module_name,
            ModuleRegistry.is_installed == True
        ).first()

        if not registry_entry:
            return False, f"Module {module_name} is not installed"

        # Get tenant
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return False, f"Tenant {tenant_id} not found"

        # Check subscription tier
        if not module.check_subscription_tier(tenant.subscription_tier):
            required_tier = module.manifest.get("subscription_tier")
            return False, f"Module requires {required_tier} subscription tier"

        # Check if already enabled
        tenant_module = self.db.query(TenantModule).filter(
            TenantModule.tenant_id == tenant_id,
            TenantModule.module_id == registry_entry.id
        ).first()

        if tenant_module and tenant_module.is_enabled:
            return False, f"Module {module_name} is already enabled for this tenant"

        # Validate configuration
        if configuration:
            is_valid, error = module.validate_configuration(configuration)
            if not is_valid:
                return False, f"Invalid configuration: {error}"
        else:
            configuration = module.get_default_configuration()

        # Pre-enable hook
        try:
            proceed, error = module.pre_enable(self.db, tenant_id)
            if not proceed:
                return False, error or "Pre-enable check failed"
        except Exception as e:
            logger.error(f"Error in pre-enable hook: {e}", exc_info=True)
            return False, f"Pre-enable hook error: {str(e)}"

        # Create or update tenant module
        if not tenant_module:
            tenant_module = TenantModule(
                tenant_id=tenant_id,
                module_id=registry_entry.id,
                is_enabled=True,
                is_configured=True,
                configuration=configuration,
                enabled_at=datetime.utcnow(),
                enabled_by_user_id=user_id
            )
            self.db.add(tenant_module)
        else:
            tenant_module.is_enabled = True
            tenant_module.is_configured = True
            tenant_module.configuration = configuration
            tenant_module.enabled_at = datetime.utcnow()
            tenant_module.enabled_by_user_id = user_id

        # Post-enable hook
        try:
            module.post_enable(self.db, tenant_id)
        except Exception as e:
            logger.error(f"Error in post-enable hook: {e}", exc_info=True)
            self.db.rollback()
            return False, f"Post-enable hook error: {str(e)}"

        self.db.commit()
        logger.info(f"Module {module_name} enabled for tenant {tenant_id}")
        return True, None

    def disable_module_for_tenant(
        self,
        module_name: str,
        tenant_id: str,
        user_id: str
    ) -> tuple[bool, Optional[str]]:
        """
        Disable a module for a specific tenant.

        Args:
            module_name: Name of the module
            tenant_id: ID of the tenant
            user_id: ID of user disabling the module

        Returns:
            Tuple of (success, error_message)
        """
        logger.info(f"Disabling module {module_name} for tenant {tenant_id}")

        module = self.loader.get_module(module_name)
        if not module:
            return False, f"Module {module_name} not found"

        registry_entry = self.db.query(ModuleRegistry).filter(
            ModuleRegistry.name == module_name
        ).first()

        if not registry_entry:
            return False, f"Module {module_name} not registered"

        # Check if core module
        if registry_entry.is_core:
            return False, "Cannot disable core modules"

        tenant_module = self.db.query(TenantModule).filter(
            TenantModule.tenant_id == tenant_id,
            TenantModule.module_id == registry_entry.id
        ).first()

        if not tenant_module or not tenant_module.is_enabled:
            return False, f"Module {module_name} is not enabled for this tenant"

        # Pre-disable hook
        try:
            proceed, error = module.pre_disable(self.db, tenant_id)
            if not proceed:
                return False, error or "Pre-disable check failed"
        except Exception as e:
            logger.error(f"Error in pre-disable hook: {e}", exc_info=True)
            return False, f"Pre-disable hook error: {str(e)}"

        # Disable module
        tenant_module.is_enabled = False
        tenant_module.disabled_at = datetime.utcnow()
        tenant_module.disabled_by_user_id = user_id

        # Post-disable hook
        try:
            module.post_disable(self.db, tenant_id)
        except Exception as e:
            logger.error(f"Error in post-disable hook: {e}", exc_info=True)

        self.db.commit()
        logger.info(f"Module {module_name} disabled for tenant {tenant_id}")
        return True, None

    def _register_permissions(self, module: BaseModule) -> None:
        """
        Register module permissions in the database.

        Args:
            module: Module instance
        """
        permissions = module.get_permissions()

        for perm_data in permissions:
            # Parse permission code to extract resource, action, and scope
            # Format: module:resource:action:scope or resource:action:scope
            code_parts = perm_data["code"].split(":")

            if len(code_parts) == 4:
                # Format: module:resource:action:scope (e.g., financial:accounts:read:company)
                _, resource, action, scope = code_parts
            elif len(code_parts) == 3:
                # Format: resource:action:scope (e.g., users:create:tenant)
                resource, action, scope = code_parts
            else:
                logger.warning(f"Invalid permission code format: {perm_data['code']}, skipping")
                continue

            # Check if permission already exists
            existing = self.db.query(Permission).filter(
                Permission.code == perm_data["code"]
            ).first()

            if not existing:
                perm = Permission(
                    code=perm_data["code"],
                    name=perm_data["name"],
                    description=perm_data.get("description"),
                    resource=resource,
                    action=action,
                    scope=scope,
                    category=perm_data.get("category", "module"),
                    is_system=perm_data.get("is_system", False)
                )
                self.db.add(perm)
                self.db.flush()  # Flush to get the ID assigned
                logger.info(f"Registered permission: {perm_data['code']}")
            else:
                # Update existing permission if needed
                existing.name = perm_data["name"]
                existing.description = perm_data.get("description")
                existing.resource = resource
                existing.action = action
                existing.scope = scope
                existing.category = perm_data.get("category", "module")

        self.db.commit()

    def get_enabled_modules_for_tenant(self, tenant_id: str) -> List[str]:
        """
        Get list of enabled module names for a tenant.

        Args:
            tenant_id: ID of the tenant

        Returns:
            List of module names
        """
        tenant_modules = self.db.query(TenantModule).join(ModuleRegistry).filter(
            TenantModule.tenant_id == tenant_id,
            TenantModule.is_enabled == True,
            ModuleRegistry.is_installed == True
        ).all()

        return [tm.module.name for tm in tenant_modules]

    def get_all_routers(self, tenant_id: Optional[str] = None) -> List[Any]:
        """
        Get all routers for enabled modules.

        Args:
            tenant_id: Optional tenant ID to filter by enabled modules

        Returns:
            List of APIRouter instances
        """
        routers = []

        if tenant_id:
            # Get only enabled modules for this tenant
            enabled_modules = self.get_enabled_modules_for_tenant(tenant_id)
            for module_name in enabled_modules:
                if module_name in self.modules:
                    try:
                        router = self.modules[module_name].get_router()
                        routers.append(router)
                    except Exception as e:
                        logger.error(f"Error getting router for {module_name}: {e}")
        else:
            # Get all installed module routers
            installed = self.db.query(ModuleRegistry).filter(
                ModuleRegistry.is_installed == True
            ).all()

            for module_entry in installed:
                if module_entry.name in self.modules:
                    try:
                        router = self.modules[module_entry.name].get_router()
                        routers.append(router)
                    except Exception as e:
                        logger.error(f"Error getting router for {module_entry.name}: {e}")

        return routers

    def get_available_modules(self) -> List[Dict[str, Any]]:
        """
        Get list of all available modules with their status.

        Returns:
            List of module information dictionaries
        """
        modules = self.db.query(ModuleRegistry).all()

        return [
            {
                "name": m.name,
                "display_name": m.display_name,
                "version": m.version,
                "description": m.description,
                "category": m.category,
                "is_installed": m.is_installed,
                "is_core": m.is_core,
                "subscription_tier": m.subscription_tier,
                "status": m.status,
            }
            for m in modules
        ]

    def get_module_info(self, module_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a module.

        Args:
            module_name: Name of the module

        Returns:
            Module information dictionary, or None if not found
        """
        registry_entry = self.db.query(ModuleRegistry).filter(
            ModuleRegistry.name == module_name
        ).first()

        if not registry_entry:
            return None

        return {
            "name": registry_entry.name,
            "display_name": registry_entry.display_name,
            "version": registry_entry.version,
            "description": registry_entry.description,
            "category": registry_entry.category,
            "tags": registry_entry.tags,
            "author": registry_entry.author,
            "license": registry_entry.license,
            "is_installed": registry_entry.is_installed,
            "is_core": registry_entry.is_core,
            "subscription_tier": registry_entry.subscription_tier,
            "dependencies": registry_entry.dependencies_json,
            "manifest": registry_entry.manifest,
            "status": registry_entry.status,
        }

    def get_module_count(self) -> int:
        """
        Get the number of loaded modules.

        Returns:
            Number of modules currently loaded in memory
        """
        return len(self.modules)

    def __repr__(self):
        return f"<ModuleRegistryService(loaded_modules={len(self.modules)})>"
