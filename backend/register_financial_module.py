"""Register and enable Financial module for FashionHub"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from app.core.db import SessionLocal
from app.models.module_registry import ModuleRegistry, TenantModule
from app.models.tenant import Tenant

db = SessionLocal()

try:
    print("🔌 Registering Financial Module...")
    print("=" * 80)

    # Load manifest
    manifest_path = Path(__file__).parent / "modules" / "financial" / "manifest.json"
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    print(f"✓ Loaded manifest for module: {manifest['name']}")

    # Check if module is already registered
    existing_module = db.query(ModuleRegistry).filter(
        ModuleRegistry.name == manifest['name']
    ).first()

    if existing_module:
        print(f"✓ Module already registered in module_registry")
        module = existing_module

        # Update manifest if needed
        module.manifest = manifest
        module.version = manifest['version']
        module.display_name = manifest.get('display_name', manifest['name'].title())
        module.description = manifest.get('description')
        module.subscription_tier = manifest.get('subscription_tier')
        db.commit()
        print(f"✓ Updated module manifest to version {manifest['version']}")
    else:
        # Register module with all required fields from manifest
        module = ModuleRegistry(
            id=str(uuid.uuid4()),
            name=manifest['name'],
            display_name=manifest.get('display_name', manifest['name'].title()),
            module_type='code',
            version=manifest['version'],
            description=manifest.get('description'),
            category=manifest.get('category'),
            author=manifest.get('author'),
            license=manifest.get('license'),
            is_installed=True,
            is_core=False,
            manifest=manifest,
            subscription_tier=manifest.get('subscription_tier'),
            api_prefix=manifest.get('api_prefix'),
            has_migrations=bool(manifest.get('migrations')),
            status=manifest.get('status', 'available'),
            homepage=manifest.get('homepage'),
            repository=manifest.get('repository'),
            support_email=manifest.get('support_email'),
            installed_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(module)
        db.commit()
        print(f"✓ Registered Financial module (version {manifest['version']})")

    # Get FashionHub tenant
    tenant = db.query(Tenant).filter(Tenant.code == "FASHIONHUB").first()
    if not tenant:
        print("❌ FashionHub tenant not found!")
        exit(1)

    print(f"✓ Found tenant: {tenant.name} (ID: {tenant.id})")

    # Check if module is enabled for tenant
    tenant_module = db.query(TenantModule).filter(
        TenantModule.tenant_id == tenant.id,
        TenantModule.module_id == module.id
    ).first()

    if tenant_module:
        if not tenant_module.is_enabled:
            tenant_module.is_enabled = True
            db.commit()
            print(f"✓ Enabled Financial module for FashionHub tenant")
        else:
            print(f"✓ Financial module already enabled for FashionHub")
    else:
        # Enable module for tenant
        tenant_module = TenantModule(
            id=str(uuid.uuid4()),
            tenant_id=str(tenant.id),
            module_id=str(module.id),
            is_enabled=True,
            configuration={
                "default_currency": "USD",
                "tax_rate": 8.875,  # NYC sales tax
                "invoice_prefix": "FH",
                "fiscal_year_start": "01-01"
            },
            enabled_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(tenant_module)
        db.commit()
        print(f"✓ Enabled Financial module for FashionHub tenant")

    print("\n" + "=" * 80)
    print("✅ Financial Module Registration Complete!")
    print("=" * 80)
    print(f"\n📦 Module: {manifest['name']} v{manifest['version']}")
    print(f"🏢 Tenant: {tenant.name}")
    print(f"🔌 Status: Enabled")
    print(f"\n💡 Next Steps:")
    print(f"   1. Restart the backend server")
    print(f"   2. Login as: cfo@fashionhub.com / password123")
    print(f"   3. Navigate to /api/v1/modules/enabled to see enabled modules")
    print(f"   4. Financial menu should now appear in the frontend")
    print("\n" + "=" * 80)

except Exception as e:
    db.rollback()
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
