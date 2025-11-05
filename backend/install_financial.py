"""
Install and enable the financial module

Usage: Run this in the container/environment where the app is running
"""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.db import SessionLocal
from app.core.module_system.registry import ModuleRegistryService
from app.models.module_registry import ModuleRegistry, TenantModule
from app.models.user import User
from app.models.tenant import Tenant


def main():
    print("Installing and enabling financial module...")

    db = SessionLocal()

    try:
        # Get superuser and tenant
        superuser = db.query(User).filter(User.is_superuser == True).first()
        if not superuser:
            print("ERROR: No superuser found!")
            return False

        print(f"Using superuser: {superuser.email}")

        tenant = db.query(Tenant).filter(Tenant.id == superuser.tenant_id).first()
        print(f"Tenant: {tenant.name}")

        # Initialize module registry
        modules_path = Path(__file__).parent / "modules"
        registry = ModuleRegistryService(db, modules_path)
        registry.sync_modules()

        # Check module status
        module = db.query(ModuleRegistry).filter(ModuleRegistry.name == "financial").first()

        if not module:
            print("ERROR: Financial module not found!")
            return False

        print(f"Module: {module.display_name} v{module.version}")

        # Install if needed
        if not module.is_installed:
            print("Installing module...")
            success, error = registry.install_module("financial", str(superuser.id))
            if not success:
                print(f"ERROR: {error}")
                return False
            print("✓ Installed")
        else:
            print("✓ Already installed")

        # Enable for tenant if needed
        tenant_module = db.query(TenantModule).filter(
            TenantModule.tenant_id == tenant.id,
            TenantModule.module_id == module.id
        ).first()

        if not tenant_module or not tenant_module.is_enabled:
            print("Enabling for tenant...")
            config = {
                "default_currency": "USD",
                "fiscal_year_start": "01-01",
                "enable_multi_currency": False,
                "tax_rate": 0,
                "invoice_prefix": "INV"
            }
            success, error = registry.enable_module_for_tenant(
                "financial",
                str(tenant.id),
                str(superuser.id),
                config
            )
            if not success:
                print(f"ERROR: {error}")
                return False
            print("✓ Enabled")
        else:
            print("✓ Already enabled")

        print("\n✓ Financial module is ready!")
        print("  GET /api/v1/modules/enabled/names should now return ['financial']")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
