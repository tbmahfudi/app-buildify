"""
Module Manifest Validator
Validates module manifests to ensure they have all required fields
and are properly configured for menu integration.

Usage:
  python validate_module_manifest.py financial
  python validate_module_manifest.py --all
"""
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

def validate_manifest(manifest_path: Path) -> Tuple[bool, List[str], List[str]]:
    """
    Validate a module manifest file.

    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors = []
    warnings = []

    # Check file exists
    if not manifest_path.exists():
        errors.append(f"Manifest file not found: {manifest_path}")
        return False, errors, warnings

    # Load JSON
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
        return False, errors, warnings

    # Required fields
    required_fields = ['name', 'display_name', 'version', 'description']
    for field in required_fields:
        if field not in manifest:
            errors.append(f"Missing required field: {field}")

    # Check routes array
    if 'routes' not in manifest:
        errors.append("Missing 'routes' array - module menus will not appear!")
    else:
        routes = manifest['routes']

        if not isinstance(routes, list):
            errors.append("'routes' must be an array")
        elif len(routes) == 0:
            warnings.append("'routes' array is empty - no menu items will be created")
        else:
            # Validate each route
            menu_routes = []
            for i, route in enumerate(routes):
                # Check required route fields
                if 'path' not in route:
                    errors.append(f"Route {i}: Missing 'path' field")
                if 'name' not in route:
                    errors.append(f"Route {i}: Missing 'name' field")

                # Check menu configuration
                if 'menu' in route:
                    menu_routes.append(route)
                    menu = route['menu']

                    # Required menu fields
                    if 'label' not in menu:
                        errors.append(f"Route {i} ({route.get('name', 'unknown')}): menu missing 'label'")
                    if 'icon' not in menu:
                        warnings.append(f"Route {i} ({route.get('name', 'unknown')}): menu missing 'icon'")
                    if 'order' not in menu:
                        warnings.append(f"Route {i} ({route.get('name', 'unknown')}): menu missing 'order'")

                    # Check permission
                    if 'permission' not in route:
                        warnings.append(f"Route {i} ({route.get('name', 'unknown')}): no permission specified - accessible to all authenticated users")

            if len(menu_routes) == 0:
                warnings.append("No routes have 'menu' configuration - no menu items will be created")
            else:
                print(f"  ✓ Found {len(menu_routes)} routes with menu configuration")

    # Check permissions array
    if 'permissions' not in manifest:
        warnings.append("Missing 'permissions' array - permissions must be manually created")
    elif not isinstance(manifest['permissions'], list):
        errors.append("'permissions' must be an array")
    elif len(manifest['permissions']) == 0:
        warnings.append("'permissions' array is empty")
    else:
        print(f"  ✓ Found {len(manifest['permissions'])} permission definitions")

    # Check default_roles
    if 'default_roles' in manifest:
        if not isinstance(manifest['default_roles'], dict):
            errors.append("'default_roles' must be an object")
        else:
            print(f"  ✓ Found {len(manifest['default_roles'])} default role definitions")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def validate_module(module_name: str) -> bool:
    """
    Validate a module's manifest.

    Returns:
        True if valid, False otherwise
    """
    backend_manifest_path = Path(__file__).parent / "modules" / module_name / "manifest.json"

    print(f"\n{'='*80}")
    print(f"VALIDATING MODULE: {module_name}")
    print(f"{'='*80}\n")

    print(f"Backend manifest: {backend_manifest_path}")

    is_valid, errors, warnings = validate_manifest(backend_manifest_path)

    # Print results
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  • {error}")

    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  • {warning}")

    if is_valid and not warnings:
        print(f"\n✅ Manifest is valid!")
    elif is_valid:
        print(f"\n✓ Manifest is valid (with warnings)")
    else:
        print(f"\n❌ Manifest is INVALID")

    print(f"\n{'='*80}\n")

    return is_valid


def validate_all_modules() -> None:
    """Validate all modules in the modules directory."""
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
    print(f"VALIDATING ALL MODULES ({len(module_dirs)} found)")
    print(f"{'='*80}\n")

    results = []

    for module_dir in module_dirs:
        module_name = module_dir.name
        is_valid = validate_module(module_name)
        results.append((module_name, is_valid))

    # Summary
    print(f"\n{'='*80}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*80}\n")

    valid_count = sum(1 for _, valid in results if valid)
    invalid_count = len(results) - valid_count

    for module_name, is_valid in results:
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"  {status}: {module_name}")

    print(f"\nTotal: {len(results)} modules")
    print(f"Valid: {valid_count}")
    print(f"Invalid: {invalid_count}")

    if invalid_count > 0:
        print(f"\n⚠️  {invalid_count} module(s) have validation errors!")
        sys.exit(1)
    else:
        print(f"\n✅ All modules are valid!")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python validate_module_manifest.py <module_name>")
        print("  python validate_module_manifest.py --all")
        print("\nExample:")
        print("  python validate_module_manifest.py financial")
        sys.exit(1)

    module_name = sys.argv[1]

    if module_name == "--all":
        validate_all_modules()
    else:
        is_valid = validate_module(module_name)
        sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
