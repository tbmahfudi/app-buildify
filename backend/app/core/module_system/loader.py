"""
Module Loader

Discovers and dynamically loads modules from the modules directory.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional
from .base_module import BaseModule
import logging

logger = logging.getLogger(__name__)


class ModuleLoader:
    """
    Discovers and loads modules from the modules directory.

    Provides:
    - Module discovery (scan filesystem for valid modules)
    - Dynamic module loading (import module.py)
    - Module instance caching
    """

    def __init__(self, modules_path: Path):
        """
        Initialize the module loader.

        Args:
            modules_path: Path to the modules directory
        """
        self.modules_path = Path(modules_path)
        self.loaded_modules: Dict[str, BaseModule] = {}

        logger.info(f"ModuleLoader initialized with path: {self.modules_path}")

    def discover_modules(self) -> List[str]:
        """
        Discover all modules by looking for directories with module.py and manifest.json.

        A valid module must have:
        - A directory under modules/
        - A manifest.json file
        - A module.py file

        Returns:
            List of module names (directory names)
        """
        modules = []

        if not self.modules_path.exists():
            logger.warning(f"Modules path does not exist: {self.modules_path}")
            return modules

        if not self.modules_path.is_dir():
            logger.error(f"Modules path is not a directory: {self.modules_path}")
            return modules

        # Scan all subdirectories
        for module_dir in self.modules_path.iterdir():
            if not module_dir.is_dir():
                continue

            # Skip __pycache__ and hidden directories
            if module_dir.name.startswith('__') or module_dir.name.startswith('.'):
                continue

            # Check for required files
            manifest_file = module_dir / "manifest.json"
            module_file = module_dir / "module.py"

            if manifest_file.exists() and module_file.exists():
                modules.append(module_dir.name)
                logger.info(f"Discovered module: {module_dir.name}")
            else:
                logger.debug(
                    f"Skipping {module_dir.name}: missing manifest.json or module.py"
                )

        logger.info(f"Discovered {len(modules)} modules: {', '.join(modules)}")
        return modules

    def load_module(self, module_name: str) -> Optional[BaseModule]:
        """
        Dynamically load a module by importing its module.py.

        The module.py file should contain a class that:
        - Inherits from BaseModule
        - Is named in PascalCase based on module name (e.g., financial -> FinancialModule)

        Args:
            module_name: Name of the module to load

        Returns:
            BaseModule instance, or None if loading fails
        """
        # Return cached module if already loaded
        if module_name in self.loaded_modules:
            logger.debug(f"Returning cached module: {module_name}")
            return self.loaded_modules[module_name]

        module_dir = self.modules_path / module_name
        module_file = module_dir / "module.py"

        if not module_file.exists():
            logger.error(f"Module file not found: {module_file}")
            return None

        try:
            # Create module spec for dynamic import
            spec = importlib.util.spec_from_file_location(
                f"modules.{module_name}.module",
                module_file
            )

            if spec is None or spec.loader is None:
                logger.error(f"Failed to create module spec for {module_name}")
                return None

            # Load the module
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"modules.{module_name}.module"] = module
            spec.loader.exec_module(module)

            # Find the module class
            # Convention: module named 'financial' should have class 'FinancialModule'
            module_class_name = self._get_module_class_name(module_name)

            if not hasattr(module, module_class_name):
                # Try alternate naming: just capitalize first letter
                alt_class_name = module_name.capitalize() + 'Module'
                if hasattr(module, alt_class_name):
                    module_class_name = alt_class_name
                else:
                    logger.error(
                        f"Module class '{module_class_name}' not found in {module_name}. "
                        f"Expected class name: {module_class_name} or {alt_class_name}"
                    )
                    return None

            # Get the module class
            module_class = getattr(module, module_class_name)

            # Verify it inherits from BaseModule
            if not issubclass(module_class, BaseModule):
                logger.error(
                    f"Module class {module_class_name} does not inherit from BaseModule"
                )
                return None

            # Instantiate the module
            module_instance = module_class(module_dir)

            # Cache the module
            self.loaded_modules[module_name] = module_instance

            logger.info(f"Successfully loaded module: {module_name} (v{module_instance.version})")

            return module_instance

        except Exception as e:
            logger.error(f"Error loading module {module_name}: {e}", exc_info=True)
            return None

    def load_all_modules(self) -> Dict[str, BaseModule]:
        """
        Discover and load all modules.

        Returns:
            Dictionary of module_name -> BaseModule instance
        """
        discovered = self.discover_modules()

        logger.info(f"Loading {len(discovered)} discovered modules...")

        for module_name in discovered:
            self.load_module(module_name)

        logger.info(f"Successfully loaded {len(self.loaded_modules)} modules")

        return self.loaded_modules

    def get_module(self, module_name: str) -> Optional[BaseModule]:
        """
        Get a loaded module by name.

        Args:
            module_name: Name of the module

        Returns:
            BaseModule instance, or None if not loaded
        """
        return self.loaded_modules.get(module_name)

    def get_all_modules(self) -> Dict[str, BaseModule]:
        """
        Get all loaded modules.

        Returns:
            Dictionary of module_name -> BaseModule instance
        """
        return self.loaded_modules

    def reload_module(self, module_name: str) -> Optional[BaseModule]:
        """
        Reload a module (useful for development).

        Args:
            module_name: Name of the module to reload

        Returns:
            Reloaded BaseModule instance, or None if reload fails
        """
        # Remove from cache
        if module_name in self.loaded_modules:
            del self.loaded_modules[module_name]

        # Also remove from sys.modules to force reload
        module_key = f"modules.{module_name}.module"
        if module_key in sys.modules:
            del sys.modules[module_key]

        logger.info(f"Reloading module: {module_name}")

        # Load again
        return self.load_module(module_name)

    def unload_module(self, module_name: str) -> bool:
        """
        Unload a module from memory.

        Args:
            module_name: Name of the module to unload

        Returns:
            True if unloaded, False if module wasn't loaded
        """
        if module_name in self.loaded_modules:
            del self.loaded_modules[module_name]

            # Also remove from sys.modules
            module_key = f"modules.{module_name}.module"
            if module_key in sys.modules:
                del sys.modules[module_key]

            logger.info(f"Unloaded module: {module_name}")
            return True

        return False

    def _get_module_class_name(self, module_name: str) -> str:
        """
        Generate expected module class name from module name.

        Converts snake_case or kebab-case to PascalCase and appends 'Module'.

        Examples:
            financial -> FinancialModule
            user_management -> UserManagementModule
            warehouse-inventory -> WarehouseInventoryModule

        Args:
            module_name: Module name (directory name)

        Returns:
            Expected class name
        """
        # Replace dashes with underscores
        normalized = module_name.replace('-', '_')

        # Split by underscore and capitalize each word
        words = normalized.split('_')
        pascal_case = ''.join(word.capitalize() for word in words)

        return f"{pascal_case}Module"

    def validate_module(self, module_name: str) -> tuple[bool, Optional[str]]:
        """
        Validate a module without loading it.

        Checks:
        - Directory exists
        - manifest.json exists and is valid
        - module.py exists

        Args:
            module_name: Name of the module to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        module_dir = self.modules_path / module_name

        if not module_dir.exists():
            return False, f"Module directory not found: {module_dir}"

        if not module_dir.is_dir():
            return False, f"Module path is not a directory: {module_dir}"

        manifest_file = module_dir / "manifest.json"
        if not manifest_file.exists():
            return False, f"manifest.json not found in {module_name}"

        module_file = module_dir / "module.py"
        if not module_file.exists():
            return False, f"module.py not found in {module_name}"

        # Try to parse manifest
        import json
        try:
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)

            # Check required fields
            required_fields = ["name", "version", "display_name"]
            for field in required_fields:
                if field not in manifest:
                    return False, f"manifest.json missing required field: {field}"

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON in manifest.json: {e}"

        return True, None

    def __repr__(self):
        return f"<ModuleLoader(path={self.modules_path}, loaded={len(self.loaded_modules)})>"
