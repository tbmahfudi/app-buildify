"""
Resync module manifest in database
Updates the financial module manifest in the database with the latest from the file.
"""
import json
from pathlib import Path
from app.core.db import SessionLocal
from app.models.module_registry import ModuleRegistry

# Read the manifest file
manifest_path = Path(__file__).parent / "modules" / "financial" / "manifest.json"

print(f"Reading manifest from: {manifest_path}")

with open(manifest_path, 'r') as f:
    manifest = json.load(f)

print(f"✓ Loaded manifest for: {manifest['name']}")
print(f"  Display name: {manifest['display_name']}")
print(f"  Version: {manifest['version']}")

# Check routes
if 'routes' in manifest:
    print(f"  Routes: {len(manifest['routes'])}")
    menu_routes = [r for r in manifest['routes'] if 'menu' in r]
    print(f"  Routes with menu: {len(menu_routes)}")

    if menu_routes:
        print(f"\n  Menu items:")
        for route in menu_routes:
            print(f"    - {route['menu']['label']} (permission: {route.get('permission', 'none')})")
else:
    print(f"  ⚠️  No routes in manifest!")

# Update database
db = SessionLocal()

try:
    # Find the financial module
    module = db.query(ModuleRegistry).filter(
        ModuleRegistry.name == manifest['name']
    ).first()

    if not module:
        print(f"\n❌ Module '{manifest['name']}' not found in database!")
        print("   Run the module sync/install process first.")
        exit(1)

    print(f"\n✓ Found module in database (ID: {module.id})")
    print(f"  Current manifest has {len(module.manifest.get('routes', []))} routes")

    # Update the manifest
    module.manifest = manifest
    module.version = manifest['version']
    module.description = manifest.get('description')

    db.commit()

    print(f"\n✓ Updated manifest in database")
    print(f"  New manifest has {len(manifest.get('routes', []))} routes")

    # Verify
    db.refresh(module)
    updated_routes = module.manifest.get('routes', [])
    updated_menu_routes = [r for r in updated_routes if 'menu' in r]

    print(f"\n✓ Verification:")
    print(f"  Routes in DB: {len(updated_routes)}")
    print(f"  Menu routes in DB: {len(updated_menu_routes)}")

    if updated_menu_routes:
        print(f"\n  Menu items now in database:")
        for route in updated_menu_routes:
            print(f"    ✓ {route['menu']['label']}")

    print(f"\n{'='*80}")
    print(f"✅ SUCCESS! Module manifest updated.")
    print(f"{'='*80}")
    print(f"\nNext steps:")
    print(f"  1. Restart backend: docker restart app_buildify_backend")
    print(f"  2. Refresh browser to see financial menu items")
    print(f"  3. Run debug script to verify: python debug_module_menus.py")

finally:
    db.close()
