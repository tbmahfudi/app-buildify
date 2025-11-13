"""
Menu Items Seed Data
====================
Seeds the menu_items table with data from /frontend/config/menu.json.
Creates menu management permissions for RBAC.

This is the first step in migrating from static JSON menus to backend-driven menus.

Run: python -m app.seeds.seed_menu_items
"""

import json
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.menu_item import MenuItem
from app.models.permission import Permission
from app.models.base import generate_uuid


def seed_menu_permissions(db: Session) -> int:
    """
    Create permissions for menu management.

    Returns:
        Number of permissions created
    """
    print("\n" + "="*80)
    print("MENU MANAGEMENT PERMISSIONS SETUP")
    print("="*80 + "\n")

    print("📋 Step 1: Registering Menu Management permissions...")

    menu_permissions = [
        {
            "code": "menu:read:tenant",
            "name": "View Menu Items",
            "description": "View menu items for tenant",
            "resource": "menu",
            "action": "read",
            "scope": "tenant",
            "category": "menu_management",
            "is_system": True
        },
        {
            "code": "menu:create:tenant",
            "name": "Create Menu Items",
            "description": "Create new menu items",
            "resource": "menu",
            "action": "create",
            "scope": "tenant",
            "category": "menu_management",
            "is_system": True
        },
        {
            "code": "menu:update:tenant",
            "name": "Update Menu Items",
            "description": "Update menu items",
            "resource": "menu",
            "action": "update",
            "scope": "tenant",
            "category": "menu_management",
            "is_system": True
        },
        {
            "code": "menu:delete:tenant",
            "name": "Delete Menu Items",
            "description": "Delete menu items",
            "resource": "menu",
            "action": "delete",
            "scope": "tenant",
            "category": "menu_management",
            "is_system": True
        },
        {
            "code": "menu:manage:tenant",
            "name": "Manage Menus",
            "description": "Full menu management access",
            "resource": "menu",
            "action": "manage",
            "scope": "tenant",
            "category": "menu_management",
            "is_system": True
        },
    ]

    created_count = 0
    existing_count = 0

    for perm_data in menu_permissions:
        perm = db.query(Permission).filter(
            Permission.code == perm_data["code"]
        ).first()

        if not perm:
            perm = Permission(
                code=perm_data["code"],
                name=perm_data["name"],
                description=perm_data["description"],
                resource=perm_data["resource"],
                action=perm_data["action"],
                scope=perm_data["scope"],
                category=perm_data["category"],
                is_system=perm_data["is_system"]
            )
            db.add(perm)
            db.flush()
            print(f"  ✓ Created permission: {perm_data['code']}")
            created_count += 1
        else:
            # Update description if changed
            if perm.description != perm_data["description"]:
                perm.description = perm_data["description"]
            print(f"  • Permission exists: {perm_data['code']}")
            existing_count += 1

    db.commit()
    print(f"\n✓ Created {created_count} new permissions")
    print(f"✓ Found {existing_count} existing permissions")

    return created_count


def create_menu_item_recursive(
    db: Session,
    item_data: dict,
    parent_id: str,
    order: int
) -> int:
    """
    Recursively create menu items and their children.

    Args:
        db: Database session
        item_data: Menu item data from JSON
        parent_id: Parent menu item ID (None for root items)
        order: Display order

    Returns:
        Number of items created (including children)
    """
    # Generate code from route or title
    code = item_data.get('route', item_data['title'].lower().replace(' ', '_').replace('&', 'and'))

    # Check if item already exists (by code)
    existing = db.query(MenuItem).filter(MenuItem.code == code).first()

    if existing:
        print(f"  • Skipping existing menu item: {code}")
        menu_item_id = str(existing.id)
        items_created = 0
    else:
        # Create menu item
        menu_item = MenuItem(
            id=generate_uuid(),
            code=code,
            title=item_data['title'],
            icon=item_data.get('icon'),
            route=item_data.get('route'),
            description=item_data.get('description'),
            permission=item_data.get('permission'),
            required_roles=item_data.get('roles'),  # JSON array
            parent_id=parent_id,
            order=order,
            is_system=True,  # All seeded menus are system menus
            tenant_id=None,  # System menus (visible to all tenants)
            is_active=True,
            is_visible=True,
            target='_self',
            module_code=None,
            created_at=datetime.utcnow()
        )

        db.add(menu_item)
        db.flush()  # Get ID

        menu_item_id = str(menu_item.id)
        items_created = 1

        print(f"  ✓ Created menu item: {code} (ID: {menu_item_id})")

    # Process submenu
    if 'submenu' in item_data and item_data['submenu']:
        for child_idx, child_data in enumerate(item_data['submenu']):
            child_count = create_menu_item_recursive(
                db=db,
                item_data=child_data,
                parent_id=menu_item_id,
                order=child_idx * 10
            )
            items_created += child_count

    return items_created


def seed_menu_items(clear_existing: bool = False) -> int:
    """
    Import menu items from /frontend/config/menu.json into database.

    Args:
        clear_existing: If True, delete existing menu items before seeding

    Returns:
        Number of menu items created
    """
    db = SessionLocal()

    try:
        print("\n" + "="*80)
        print("MENU ITEMS SEED")
        print("="*80 + "\n")

        print("📋 Step 1: Loading menu.json...")

        # Load menu.json
        menu_json_path = Path(__file__).parent.parent.parent.parent / "frontend" / "config" / "menu.json"

        if not menu_json_path.exists():
            print(f"❌ ERROR: menu.json not found at {menu_json_path}")
            return 0

        try:
            with open(menu_json_path, 'r', encoding='utf-8') as f:
                menu_data = json.load(f)
        except Exception as e:
            print(f"❌ ERROR: Failed to load menu.json: {e}")
            return 0

        if 'items' not in menu_data:
            print("❌ ERROR: menu.json does not have 'items' array")
            return 0

        print(f"  ✓ Loaded {len(menu_data['items'])} top-level menu items from menu.json")

        # Check if menu items already exist
        existing_count = db.query(MenuItem).count()

        if existing_count > 0:
            print(f"\n⚠️  Warning: Found {existing_count} existing menu items in database")
            if clear_existing:
                print("  🗑️  Clearing existing menu items...")
                db.query(MenuItem).delete()
                db.commit()
                print(f"  ✓ Deleted {existing_count} existing menu items")
            else:
                print("  ℹ️  Will skip existing items (based on code)")

        print("\n📋 Step 2: Creating menu items...")

        # Process menu items
        items_created = 0
        for idx, item in enumerate(menu_data['items']):
            created_count = create_menu_item_recursive(
                db=db,
                item_data=item,
                parent_id=None,
                order=idx * 10
            )
            items_created += created_count

        db.commit()

        print(f"\n✓ Successfully seeded {items_created} menu items")
        print("\n" + "="*80 + "\n")

        return items_created

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main(clear_existing: bool = False):
    """
    Main entry point for seeding menu system.

    Args:
        clear_existing: If True, delete existing menu items before seeding
    """
    print("\n🚀 Starting Menu System Seed...")
    print("="*80)

    db = SessionLocal()
    try:
        # Step 1: Seed permissions
        perms_created = seed_menu_permissions(db)

        # Step 2: Seed menu items
        items_created = seed_menu_items(clear_existing=clear_existing)

        print("\n" + "="*80)
        print("✅ MENU SYSTEM SEED COMPLETE!")
        print("="*80)
        print(f"\nSummary:")
        print(f"  • Permissions created: {perms_created}")
        print(f"  • Menu items created: {items_created}")
        print("\nNext steps:")
        print("  1. Assign 'menu:manage:tenant' permission to admin roles")
        print("  2. Restart backend application")
        print("  3. Test menu API: GET /api/v1/menu")
        print("="*80 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    import sys

    # Check if --clear flag provided
    clear_existing = '--clear' in sys.argv or '-c' in sys.argv

    if clear_existing:
        print("\n⚠️  Running with --clear flag: Will delete existing menu items!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Seeding cancelled")
            sys.exit(0)

    main(clear_existing=clear_existing)
