"""
Debug script to check module menu integration
"""
from app.core.db import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.models.module_registry import ModuleRegistry, TenantModule
import json

db = SessionLocal()

try:
    # Get FASHIONHUB tenant
    tenant = db.query(Tenant).filter(Tenant.code == "FASHIONHUB").first()
    if not tenant:
        print("❌ FASHIONHUB tenant not found")
        exit(1)

    print(f"✓ Found tenant: {tenant.name} (ID: {tenant.id})")
    print()

    # Check ModuleRegistry
    print("="*80)
    print("MODULE REGISTRY")
    print("="*80)

    all_modules = db.query(ModuleRegistry).all()
    print(f"Total modules in registry: {len(all_modules)}")

    for mod in all_modules:
        print(f"\n  Module: {mod.name}")
        print(f"    Display Name: {mod.display_name}")
        print(f"    Installed: {mod.is_installed}")
        print(f"    Enabled: {mod.is_enabled}")
        print(f"    Manifest exists: {mod.manifest is not None}")

        if mod.manifest:
            routes = mod.manifest.get('routes', [])
            print(f"    Routes in manifest: {len(routes)}")

            menu_routes = [r for r in routes if 'menu' in r]
            print(f"    Routes with menu config: {len(menu_routes)}")

            if menu_routes:
                print(f"    Menu routes:")
                for route in menu_routes:
                    print(f"      - {route['menu'].get('label', 'Unknown')} (path: {route.get('path', 'N/A')})")

    # Check TenantModule
    print("\n" + "="*80)
    print("TENANT MODULES (FASHIONHUB)")
    print("="*80)

    tenant_modules = db.query(TenantModule).filter(
        TenantModule.tenant_id == tenant.id
    ).all()

    print(f"Total tenant modules: {len(tenant_modules)}")

    for tm in tenant_modules:
        print(f"\n  TenantModule ID: {tm.id}")
        print(f"    Enabled: {tm.is_enabled}")
        print(f"    Module relationship loaded: {tm.module is not None}")

        if tm.module:
            print(f"    Module name: {tm.module.name}")
            print(f"    Module display name: {tm.module.display_name}")
            print(f"    Has manifest: {tm.module.manifest is not None}")

            if tm.module.manifest:
                routes = tm.module.manifest.get('routes', [])
                menu_routes = [r for r in routes if 'menu' in r]
                print(f"    Routes with menu: {len(menu_routes)}")

                if menu_routes:
                    print(f"    Menu items:")
                    for route in menu_routes:
                        print(f"      - {route['menu'].get('label')} (permission: {route.get('permission', 'none')})")
        else:
            print(f"    ⚠️  Module relationship not loaded! module_id: {tm.module_id}")

    # Check enabled modules specifically
    print("\n" + "="*80)
    print("ENABLED MODULES FOR FASHIONHUB")
    print("="*80)

    enabled_modules = db.query(TenantModule).filter(
        TenantModule.tenant_id == tenant.id,
        TenantModule.is_enabled == True
    ).all()

    print(f"Enabled modules: {len(enabled_modules)}")

    for tm in enabled_modules:
        if tm.module:
            print(f"\n  ✓ {tm.module.name} ({tm.module.display_name})")

            if tm.module.manifest and 'routes' in tm.module.manifest:
                routes = tm.module.manifest.get('routes', [])
                menu_routes = [r for r in routes if 'menu' in r]

                print(f"    Total routes: {len(routes)}")
                print(f"    Menu routes: {len(menu_routes)}")

                if menu_routes:
                    print(f"    Menu configurations:")
                    for route in menu_routes:
                        menu = route.get('menu', {})
                        perm = route.get('permission', 'none')
                        print(f"      • {menu.get('label', 'Unknown')}")
                        print(f"        Path: {route.get('path', 'N/A')}")
                        print(f"        Permission: {perm}")
                        print(f"        Icon: {menu.get('icon', 'N/A')}")
                        print(f"        Order: {menu.get('order', 0)}")
        else:
            print(f"  ⚠️  Module relationship is NULL for TenantModule {tm.id}")

    # Test getting a user and their permissions
    print("\n" + "="*80)
    print("USER PERMISSIONS TEST")
    print("="*80)

    user = db.query(User).filter(User.email == "cfo@fashionhub.com").first()
    if user:
        print(f"✓ Found user: {user.email}")
        permissions = user.get_permissions()
        print(f"  Total permissions: {len(permissions)}")

        financial_perms = [p for p in permissions if p.startswith('financial:')]
        print(f"  Financial permissions: {len(financial_perms)}")

        if financial_perms:
            print(f"  Sample financial permissions:")
            for perm in list(financial_perms)[:5]:
                print(f"    - {perm}")

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✓ Modules in registry: {len(all_modules)}")
    print(f"✓ Tenant modules: {len(tenant_modules)}")
    print(f"✓ Enabled modules: {len(enabled_modules)}")

    if enabled_modules:
        for tm in enabled_modules:
            if tm.module and tm.module.manifest:
                menu_count = len([r for r in tm.module.manifest.get('routes', []) if 'menu' in r])
                print(f"✓ {tm.module.name}: {menu_count} menu items")

finally:
    db.close()
