"""
Builder Module Backend Implementation

Implements BaseModule interface for the builder module.
"""

from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter

# Import from core platform
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.module_system.base_module import BaseModule
from .backend.app.routers import pages


class BuilderModule(BaseModule):
    """
    UI Builder Module Backend Implementation.

    Provides drag-and-drop UI building capabilities with GrapeJS.
    """

    def __init__(self, module_path: Path):
        """Initialize the builder module."""
        super().__init__(module_path)

        # Initialize router
        self._setup_router()

    def _setup_router(self):
        """Setup module router with all endpoints."""
        self.router = APIRouter()

        # Include pages router
        self.router.include_router(
            pages.router,
            prefix="/pages",
            tags=["builder-pages"]
        )

    def get_router(self) -> APIRouter:
        """
        Return the FastAPI router for this module.

        Returns:
            APIRouter with builder endpoints
        """
        return self.router

    def get_permissions(self) -> List[Dict[str, Any]]:
        """
        Return permissions defined in manifest.

        Returns:
            List of permission dictionaries
        """
        # Get permissions from manifest
        permissions = self.manifest.get("permissions", [])

        # Ensure all required fields are present
        validated_permissions = []
        for perm in permissions:
            if "code" in perm and "name" in perm:
                validated_permissions.append({
                    "code": perm["code"],
                    "name": perm["name"],
                    "description": perm.get("description", ""),
                    "category": perm.get("category", "builder"),
                    "resource": perm.get("resource", ""),
                    "action": perm.get("action", ""),
                    "scope": perm.get("scope", "tenant")
                })

        return validated_permissions

    def get_models(self) -> List[Any]:
        """
        Return SQLAlchemy models for migration.

        Returns:
            List of model classes
        """
        from .backend.app.models.page import BuilderPage, BuilderPageVersion

        return [BuilderPage, BuilderPageVersion]

    # Lifecycle Hooks

    def check_dependencies(self, installed_modules: List[str]) -> tuple[bool, str]:
        """
        Check if module dependencies are satisfied.

        Args:
            installed_modules: List of installed module names

        Returns:
            Tuple of (dependencies_met, error_message)
        """
        required = self.manifest.get("dependencies", {}).get("required_modules", [])

        missing = [dep for dep in required if dep not in installed_modules]

        if missing:
            return False, f"Missing required modules: {', '.join(missing)}"

        return True, ""

    def pre_install(self, db) -> tuple[bool, str]:
        """
        Pre-installation hook.

        Args:
            db: Database session

        Returns:
            Tuple of (proceed, error_message)
        """
        # Builder module has no special pre-install requirements
        return True, ""

    def post_install(self, db) -> None:
        """
        Post-installation hook.

        Args:
            db: Database session
        """
        # No post-install actions needed
        pass

    def pre_enable(self, db, tenant_id: str) -> tuple[bool, str]:
        """
        Pre-enable hook for tenant.

        Args:
            db: Database session
            tenant_id: Tenant ID

        Returns:
            Tuple of (proceed, error_message)
        """
        # No special pre-enable requirements
        return True, ""

    def post_enable(self, db, tenant_id: str) -> None:
        """
        Post-enable hook for tenant.

        Args:
            db: Database session
            tenant_id: Tenant ID
        """
        # No post-enable actions needed
        pass

    def pre_disable(self, db, tenant_id: str) -> tuple[bool, str]:
        """
        Pre-disable hook for tenant.

        Args:
            db: Database session
            tenant_id: Tenant ID

        Returns:
            Tuple of (proceed, error_message)
        """
        # Allow disabling
        return True, ""

    def post_disable(self, db, tenant_id: str) -> None:
        """
        Post-disable hook for tenant.

        Args:
            db: Database session
            tenant_id: Tenant ID
        """
        # No post-disable actions needed
        pass

    def pre_uninstall(self, db) -> tuple[bool, str]:
        """
        Pre-uninstall hook.

        Args:
            db: Database session

        Returns:
            Tuple of (proceed, error_message)
        """
        # Check if there are any pages created
        from .backend.app.models.page import BuilderPage
        from sqlalchemy import select

        result = db.execute(select(BuilderPage).limit(1))
        has_pages = result.scalar_one_or_none() is not None

        if has_pages:
            return False, "Cannot uninstall: Builder pages exist. Please delete all pages first."

        return True, ""

    def post_uninstall(self, db) -> None:
        """
        Post-uninstall hook.

        Args:
            db: Database session
        """
        # Cleanup would be handled by database cascade delete
        pass
