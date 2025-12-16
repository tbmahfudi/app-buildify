"""
Enable Financial Module for Specified Tenants

Usage:
    python enable_financial_module.py TECHSTART
    python enable_financial_module.py FASHIONHUB
    python enable_financial_module.py TECHSTART FASHIONHUB  # Multiple tenants
"""
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from app.core.db import SessionLocal
from app.models.module_registry import ModuleRegistry, TenantModule
from app.models.tenant import Tenant


def enable_module_for_tenant(db, module, tenant_code):
    """Enable financial module for a specific tenant"""

    # Get tenant
    tenant = db.query(Tenant).filter(Tenant.code == tenant_code).first()
    if not tenant:
        print(f"❌ Tenant '{tenant_code}' not found!")
        return False

    print(f"\n{'='*60}")
    print(f"Enabling for: {tenant.name} ({tenant_code})")
    print(f"{'='*60}")
    print(f"Tenant ID: {tenant.id}")

    # Check if module is already enabled for tenant
    tenant_module = db.query(TenantModule).filter(
        TenantModule.tenant_id == tenant.id,
        TenantModule.module_id == module.id
    ).first()

    if tenant_module:
        if not tenant_module.is_enabled:
            tenant_module.is_enabled = True
            tenant_module.enabled_at = datetime.utcnow()
            db.commit()
            print(f"✅ Enabled Financial module for {tenant_code}")
        else:
            print(f"✅ Financial module already enabled for {tenant_code}")
    else:
        # Enable module for tenant with default configuration
        tenant_module = TenantModule(
            id=str(uuid.uuid4()),
            tenant_id=str(tenant.id),
            module_id=str(module.id),
            is_enabled=True,
            configuration={
                "default_currency": "USD",
                "fiscal_year_start": "01-01",
                "enable_multi_currency": False,
                "tax_rate": 0,
                "invoice_prefix": tenant_code[:2]
            },
            enabled_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(tenant_module)
        db.commit()
        print(f"✅ Enabled Financial module for {tenant_code}")

    return True


def main():
    """Main function"""
    print("\n" + "="*60)
    print("FINANCIAL MODULE ENABLEMENT")
    print("="*60)

    # Parse command line arguments
    if len(sys.argv) < 2:
        print("\n📋 Usage: python enable_financial_module.py [TENANT_CODE...]")
        print("\nExamples:")
        print("  python enable_financial_module.py TECHSTART")
        print("  python enable_financial_module.py FASHIONHUB")
        print("  python enable_financial_module.py TECHSTART FASHIONHUB")
        print("\nAvailable tenant codes:")
        print("  - TECHSTART")
        print("  - FASHIONHUB")
        print("  - MEDCARE")
        print("  - CLOUDWORK")
        print("  - FINTECH")
        sys.exit(1)

    tenant_codes = [code.upper() for code in sys.argv[1:]]

    db = SessionLocal()

    try:
        # Load financial module manifest - try multiple possible locations
        possible_paths = [
            # Docker: from backend directory
            Path(__file__).parent.parent / "modules" / "financial" / "manifest.json",
            # Docker: from /app
            Path("/app/../modules/financial/manifest.json"),
            # Docker: absolute path
            Path("/modules/financial/manifest.json"),
            # Development: relative to backend
            Path(__file__).parent / "../modules/financial/manifest.json",
        ]

        manifest_path = None
        for path in possible_paths:
            if path.exists():
                manifest_path = path
                print(f"✅ Found manifest at: {path}")
                break

        if not manifest_path:
            print(f"❌ Manifest not found!")
            print("\nSearched in:")
            for path in possible_paths:
                print(f"  - {path}")
            sys.exit(1)

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        print(f"✅ Loaded manifest for: {manifest['display_name']} v{manifest['version']}")

        # Check if module is already registered
        module = db.query(ModuleRegistry).filter(
            ModuleRegistry.name == manifest['name']
        ).first()

        if module:
            print(f"✅ Module already registered in database")

            # Update manifest if needed
            module.manifest = manifest
            module.version = manifest['version']
            module.display_name = manifest.get('display_name', manifest['name'].title())
            module.description = manifest.get('description')
            db.commit()
        else:
            # Register module
            module = ModuleRegistry(
                id=str(uuid.uuid4()),
                name=manifest['name'],
                display_name=manifest.get('display_name', manifest['name'].title()),
                version=manifest['version'],
                description=manifest.get('description'),
                category=manifest.get('category', 'business'),
                is_installed=True,
                is_enabled=False,
                is_core=False,
                manifest=manifest,
                status='available',
                installed_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            db.add(module)
            db.commit()
            print(f"✅ Registered Financial module in database")

        # Enable module for each specified tenant
        success_count = 0
        for tenant_code in tenant_codes:
            if enable_module_for_tenant(db, module, tenant_code):
                success_count += 1

        # Summary
        print("\n" + "="*60)
        print("✅ ENABLEMENT COMPLETE")
        print("="*60)
        print(f"Enabled for {success_count}/{len(tenant_codes)} tenant(s)")

        if success_count > 0:
            print("\n💡 Next Steps:")
            print("   1. Restart backend server (if running)")
            print("   2. Login to frontend:")
            if "TECHSTART" in tenant_codes:
                print("      - ceo@techstart.com / password123")
            if "FASHIONHUB" in tenant_codes:
                print("      - ceo@fashionhub.com / password123")
            print("   3. Financial menu should now appear!")
            print("   4. Navigate to: #/financial/dashboard")

        print("\n" + "="*60 + "\n")

    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
