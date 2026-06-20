"""
TEMPLATE module entry point.

Replace TEMPLATE with your actual module name throughout.
"""
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter

# IMPORTANT: only import from modules.sdk — never from backend.app
from modules.sdk import BaseModule, PlatformBridge


class TEMPLATEModule(BaseModule):
    """Main module class. Rename to match your module."""

    def __init__(self, module_path: Path, bridge: PlatformBridge = None):
        super().__init__(module_path)
        self.bridge = bridge or PlatformBridge()

    # ── Required abstract implementations ────────────────────────────────────

    def get_router(self) -> APIRouter:
        from .routes import router
        return router

    def get_permissions(self) -> List[Dict[str, Any]]:
        return self.manifest.get("permissions", [])

    def get_models(self):
        from . import models  # noqa: F401 — import triggers SQLAlchemy registration
        from .models import TEMPLATEItem
        return [TEMPLATEItem]

    # ── Lifecycle hooks ───────────────────────────────────────────────────────

    def post_install(self, db_session) -> None:
        """Called once after the module is installed platform-wide."""
        super().post_install(db_session)
        # TODO: create default data, seed reference tables, etc.

    def post_enable(self, db_session, tenant_id: str) -> None:
        """Called each time the module is enabled for a tenant."""
        super().post_enable(db_session, tenant_id)
        # TODO: create tenant-specific default data
        self.bridge.audit_log(
            action="TEMPLATE.module.enabled",
            entity_type="module",
            entity_id=self.name,
            tenant_id=tenant_id,
        )

    def post_disable(self, db_session, tenant_id: str) -> None:
        """Called when the module is disabled for a tenant. Do NOT delete data."""
        super().post_disable(db_session, tenant_id)
        # TODO: archive / deactivate tenant data if needed


# Module entry point — the platform loader looks for this symbol
def create_module(module_path: Path, bridge: PlatformBridge = None) -> TEMPLATEModule:
    return TEMPLATEModule(module_path, bridge)
