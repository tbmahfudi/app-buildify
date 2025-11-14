"""
Resync module manifest in database
Updates a module's manifest in the database with the latest from the file.

Usage:
  python resync_module_manifest.py financial
  python resync_module_manifest.py --all
"""
import sys
import json
from pathlib import Path
from app.core.db import SessionLocal
from app.models.module_registry import ModuleRegistry


def resync_module(module_name: str) -> bool:
    """
    Resync a module's manifest from file to database.

    Returns:
        True if successful, False otherwise
    """
    # Read the manifest file
    manifest_path = Path(__file__).parent / "modules" / module_name / "manifest.json"

    if not manifest_path.exists():
        print(f"❌ Manifest not found: {manifest_path}")
        return False

    print(f"\n{'='*80}")
    print(f"RESYNCING MODULE: {module_name}")
    print(f"{'='*80}\n")

    print(f"Reading manifest from: {manifest_path}")

    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in manifest: {e}")
        return False

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
        # Find the module
        module = db.query(ModuleRegistry).filter(
            ModuleRegistry.name == manifest['name']
        ).first()

        if not module:
            print(f"\n❌ Module '{manifest['name']}' not found in database!")
            print("   Run the module sync/install process first.")
            return False

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
        print(f"✅ SUCCESS! Module '{module_name}' manifest updated.")
        print(f"{'='*80}")

        return True

    finally:
        db.close()


def resync_all_modules() -> None:
    """Resync all modules in the modules directory."""
    modules_dir = Path(__file__).parent / "modules"

    if not modules_dir.exists():
        print(f"❌ Modules directory not found: {modules_dir}")
        return

    # Find all module directories
    module_dirs = [d for d in modules_dir.iterdir() if d.is_dir() and (d / "manifest.json").exists()]

    if not module_dirs:
        print("No modules found")
        return

    print(f"\n{'='*80}")
    print(f"RESYNCING ALL MODULES ({len(module_dirs)} found)")
    print(f"{'='*80}\n")

    results = []

    for module_dir in module_dirs:
        module_name = module_dir.name
        success = resync_module(module_name)
        results.append((module_name, success))

    # Summary
    print(f"\n{'='*80}")
    print(f"RESYNC SUMMARY")
    print(f"{'='*80}\n")

    success_count = sum(1 for _, success in results if success)
    failed_count = len(results) - success_count

    for module_name, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {status}: {module_name}")

    print(f"\nTotal: {len(results)} modules")
    print(f"Success: {success_count}")
    print(f"Failed: {failed_count}")

    print(f"\n{'='*80}")
    print(f"NEXT STEPS")
    print(f"{'='*80}")
    print(f"  1. Restart backend: docker restart app_buildify_backend")
    print(f"  2. Refresh browser to see updated menu items")
    print(f"  3. Run debug script to verify: python debug_module_menus.py")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python resync_module_manifest.py <module_name>")
        print("  python resync_module_manifest.py --all")
        print("\nExample:")
        print("  python resync_module_manifest.py financial")
        sys.exit(1)

    module_name = sys.argv[1]

    if module_name == "--all":
        resync_all_modules()
    else:
        success = resync_module(module_name)
        if success:
            print(f"\n{'='*80}")
            print(f"NEXT STEPS")
            print(f"{'='*80}")
            print(f"  1. Restart backend: docker restart app_buildify_backend")
            print(f"  2. Refresh browser to see menu items")
            print(f"  3. Run debug script to verify: python debug_module_menus.py")
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
