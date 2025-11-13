"""
Seed script for menu items - imports current menu.json into database.

Run this script to populate the menu_items table with the current static menu.
This is the first step in migrating from static JSON menus to backend-driven menus.
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import get_settings
from app.models import MenuItem
from app.models.base import generate_uuid


async def seed_menu_items():
    """Import menu items from /frontend/config/menu.json into database"""

    settings = get_settings()

    # Convert sync URL to async
    db_url = settings.SQLALCHEMY_DATABASE_URL
    if db_url.startswith("sqlite"):
        async_db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
    elif db_url.startswith("postgresql"):
        async_db_url = db_url.replace("postgresql://", "postgresql+asyncpg://").replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    elif db_url.startswith("mysql"):
        async_db_url = db_url.replace("mysql://", "mysql+aiomysql://").replace("mysql+pymysql://", "mysql+aiomysql://")
    else:
        async_db_url = db_url

    engine = create_async_engine(async_db_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("🍔 Seeding menu items from menu.json...")

        # Load menu.json
        menu_json_path = Path(__file__).parent.parent.parent.parent / "frontend" / "config" / "menu.json"

        if not menu_json_path.exists():
            print(f"❌ Error: menu.json not found at {menu_json_path}")
            return

        try:
            with open(menu_json_path, 'r', encoding='utf-8') as f:
                menu_data = json.load(f)
        except Exception as e:
            print(f"❌ Error loading menu.json: {e}")
            return

        if 'items' not in menu_data:
            print("❌ Error: menu.json does not have 'items' array")
            return

        # Check if menu items already exist
        result = await db.execute(select(MenuItem).limit(1))
        existing_item = result.scalar_one_or_none()

        if existing_item:
            print("⚠️  Warning: Menu items already exist in database")
            response = input("Do you want to clear existing menu items and re-seed? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Seeding cancelled")
                return

            # Delete existing menu items
            result = await db.execute(select(MenuItem))
            existing_items = result.scalars().all()
            for item in existing_items:
                await db.delete(item)
            await db.commit()
            print(f"🗑️  Deleted {len(existing_items)} existing menu items")

        # Process menu items
        items_created = 0
        for idx, item in enumerate(menu_data['items']):
            created_count = await create_menu_item_recursive(
                db=db,
                item_data=item,
                parent_id=None,
                order=idx * 10
            )
            items_created += created_count

        await db.commit()
        print(f"✅ Successfully seeded {items_created} menu items")


async def create_menu_item_recursive(
    db: AsyncSession,
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
    result = await db.execute(
        select(MenuItem).where(MenuItem.code == code)
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"⏭️  Skipping existing menu item: {code}")
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
        await db.flush()  # Get ID

        menu_item_id = str(menu_item.id)
        items_created = 1

        print(f"✨ Created menu item: {code} (ID: {menu_item_id})")

    # Process submenu
    if 'submenu' in item_data and item_data['submenu']:
        for child_idx, child_data in enumerate(item_data['submenu']):
            child_count = await create_menu_item_recursive(
                db=db,
                item_data=child_data,
                parent_id=menu_item_id,
                order=child_idx * 10
            )
            items_created += child_count

    return items_created


async def seed_menu_permissions():
    """Create permissions for menu management"""

    settings = get_settings()

    # Convert sync URL to async
    db_url = settings.SQLALCHEMY_DATABASE_URL
    if db_url.startswith("sqlite"):
        async_db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
    elif db_url.startswith("postgresql"):
        async_db_url = db_url.replace("postgresql://", "postgresql+asyncpg://").replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    elif db_url.startswith("mysql"):
        async_db_url = db_url.replace("mysql://", "mysql+aiomysql://").replace("mysql+pymysql://", "mysql+aiomysql://")
    else:
        async_db_url = db_url

    engine = create_async_engine(async_db_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("🔐 Seeding menu management permissions...")

        from app.models import Permission

        # Define menu management permissions
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

        permissions_created = 0

        for perm_data in menu_permissions:
            # Check if permission exists
            result = await db.execute(
                select(Permission).where(Permission.code == perm_data['code'])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"⏭️  Permission already exists: {perm_data['code']}")
            else:
                permission = Permission(
                    id=generate_uuid(),
                    **perm_data
                )
                db.add(permission)
                permissions_created += 1
                print(f"✨ Created permission: {perm_data['code']}")

        await db.commit()
        print(f"✅ Successfully seeded {permissions_created} menu permissions")


async def main():
    """Main entry point"""
    print("=" * 60)
    print("Menu System Seeder")
    print("=" * 60)
    print()

    # Seed permissions first
    await seed_menu_permissions()

    print()

    # Then seed menu items
    await seed_menu_items()

    print()
    print("=" * 60)
    print("✅ Menu system seeding complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
