#!/usr/bin/env python3
"""
Setup Financial Module

This script installs and enables the financial module using the database directly.
Run this from the backend directory.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, '/home/user/app-buildify/backend')

from app.core.db import SessionLocal
from app.models.module_registry import ModuleRegistry, TenantModule
from app.models.tenant import Tenant
from app.models.user import User
from app.core.module_system.registry import ModuleRegistryService
from pathlib import Path
from datetime import datetime

def main():
    print("=" * 50)
    print("Financial Module Setup")
    print("=" * 50)
    print()

    db = SessionLocal()

    try:
        # Step 1: Check if module exists
        print("Step 1: Checking module status...")
        print("-" * 50)
        module = db.query(ModuleRegistry).filter(
            ModuleRegistry.name == "financial"
        ).first()

        if not module:
            print("❌ Financial module not found in database!")
            print("   The module sync may have failed.")
            return

        print(f"✓ Module found: {module.display_name} v{module.version}")
        print(f"  - Installed: {module.is_installed}")
        print(f"  - Status: {module.status}")
        print()

        # Step 2: Get a superuser and tenant
        print("Step 2: Finding superuser and tenant...")
        print("-" * 50)
        superuser = db.query(User).filter(User.is_superuser == True).first()

        if not superuser:
            print("❌ No superuser found! Please create a superuser first.")
            return

        print(f"✓ Superuser: {superuser.email}")

        tenant = db.query(Tenant).filter(Tenant.id == superuser.tenant_id).first()
        if not tenant:
            print("❌ Tenant not found!")
            return

        print(f"✓ Tenant: {tenant.name} (Subscription: {tenant.subscription_tier})")
        print()

        # Step 3: Install module if not installed
        print("Step 3: Installing module (if needed)...")
        print("-" * 50)

        if not module.is_installed:
            # Create module registry service
            modules_path = Path("/home/user/app-buildify/backend/modules")
            registry = ModuleRegistryService(db, modules_path)
            registry.sync_modules()  # Load modules

            success, error = registry.install_module("financial", str(superuser.id))

            if success:
                print("✓ Module installed successfully!")
            else:
                print(f"❌ Installation failed: {error}")
                return
        else:
            print("✓ Module already installed")
        print()

        # Step 4: Enable for tenant
        print("Step 4: Enabling module for tenant...")
        print("-" * 50)

        # Check if already enabled
        tenant_module = db.query(TenantModule).filter(
            TenantModule.tenant_id == tenant.id,
            TenantModule.module_id == module.id
        ).first()

        if tenant_module and tenant_module.is_enabled:
            print("✓ Module already enabled for this tenant")
        else:
            # Create module registry service
            modules_path = Path("/home/user/app-buildify/backend/modules")
            registry = ModuleRegistryService(db, modules_path)
            registry.sync_modules()  # Load modules

            # Default configuration
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

            if success:
                print("✓ Module enabled successfully!")
            else:
                print(f"❌ Enable failed: {error}")
                return
        print()

        # Step 5: Verify
        print("Step 5: Verifying setup...")
        print("-" * 50)

        enabled_modules = db.query(TenantModule).join(ModuleRegistry).filter(
            TenantModule.tenant_id == tenant.id,
            TenantModule.is_enabled == True,
            ModuleRegistry.is_installed == True
        ).all()

        print(f"✓ Tenant has {len(enabled_modules)} enabled module(s):")
        for tm in enabled_modules:
            print(f"  - {tm.module.display_name} (v{tm.module.version})")
        print()

        print("=" * 50)
        print("✓ Setup Complete!")
        print("=" * 50)
        print()
        print("The financial module is now available at:")
        print("  - GET  /api/v1/financial/health")
        print("  - GET  /api/v1/financial/accounts")
        print("  - POST /api/v1/financial/accounts")
        print("  - GET  /api/v1/financial/invoices")
        print("  - POST /api/v1/financial/invoices")
        print()
        print("Check enabled modules:")
        print("  - GET /api/v1/modules/enabled/names")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
