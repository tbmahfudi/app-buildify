"""
UI Builder Menu Items Seed
===========================
Seeds the menu_items table with UI Builder navigation items.

This creates:
1. Developer Tools menu (if it doesn't exist)
2. UI Builder submenu
3. Page Designer menu item
4. Manage Pages menu item

Run: python -m app.seeds.seed_builder_menu
"""

from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.menu_item import MenuItem


def seed_builder_menu():
    """Seed UI Builder menu items into the database"""
    print("\n" + "=" * 70)
    print("UI BUILDER MENU ITEMS SEED")
    print("=" * 70)

    db = SessionLocal()

    try:
        created_count = 0
        updated_count = 0
        existing_count = 0

        # Step 1: Ensure Developer Tools parent menu exists
        print("\n📁 Step 1: Checking Developer Tools menu...")
        dev_tools = db.query(MenuItem).filter(MenuItem.code == "developer_tools").first()

        if not dev_tools:
            dev_tools = MenuItem(
                code="developer_tools",
                tenant_id=None,  # System menu
                parent_id=None,
                order=900,  # Show near the bottom
                title="Developer Tools",
                icon="ph-duotone ph-code",
                route=None,  # No direct route, it's a parent menu
                description="Development and system tools",
                permission=None,  # No permission required for parent
                is_active=True,
                is_visible=True,
                is_system=True,
                module_code=None
            )
            db.add(dev_tools)
            db.flush()  # Get the ID
            print(f"  ✅ Created: Developer Tools (order: {dev_tools.order})")
            created_count += 1
        else:
            print(f"  ⏭️  Developer Tools already exists (order: {dev_tools.order})")
            existing_count += 1

        # Step 2: Create UI Builder submenu
        print("\n🎨 Step 2: Creating UI Builder submenu...")
        ui_builder = db.query(MenuItem).filter(MenuItem.code == "ui_builder").first()

        if not ui_builder:
            ui_builder = MenuItem(
                code="ui_builder",
                tenant_id=None,
                parent_id=dev_tools.id,
                order=10,
                title="UI Builder",
                icon="ph-duotone ph-code-block",
                route=None,  # Parent menu, no direct route
                description="Visual page builder",
                permission=None,  # No permission for parent
                is_active=True,
                is_visible=True,
                is_system=True,
                module_code=None
            )
            db.add(ui_builder)
            db.flush()
            print(f"  ✅ Created: UI Builder (parent: Developer Tools)")
            created_count += 1
        else:
            print(f"  ⏭️  UI Builder already exists")
            existing_count += 1

        # Step 3: Create Page Designer menu item
        print("\n✏️  Step 3: Creating Page Designer menu item...")
        page_designer = db.query(MenuItem).filter(MenuItem.code == "builder_page_designer").first()

        if not page_designer:
            page_designer = MenuItem(
                code="builder_page_designer",
                tenant_id=None,
                parent_id=ui_builder.id,
                order=10,
                title="Page Designer",
                icon="ph-duotone ph-paint-brush",
                route="builder",
                description="Design and create UI pages",
                permission="builder:design:tenant",
                is_active=True,
                is_visible=True,
                is_system=True,
                module_code=None
            )
            db.add(page_designer)
            print(f"  ✅ Created: Page Designer (route: builder, permission: builder:design:tenant)")
            created_count += 1
        else:
            # Update permission if it changed
            if page_designer.permission != "builder:design:tenant":
                page_designer.permission = "builder:design:tenant"
                updated_count += 1
                print(f"  🔄 Updated: Page Designer (permission updated)")
            else:
                print(f"  ⏭️  Page Designer already exists")
                existing_count += 1

        # Step 4: Create Manage Pages menu item
        print("\n📄 Step 4: Creating Manage Pages menu item...")
        manage_pages = db.query(MenuItem).filter(MenuItem.code == "builder_manage_pages").first()

        if not manage_pages:
            manage_pages = MenuItem(
                code="builder_manage_pages",
                tenant_id=None,
                parent_id=ui_builder.id,
                order=20,
                title="Manage Pages",
                icon="ph-duotone ph-files",
                route="builder-pages-list",
                description="View and manage builder pages",
                permission="builder:pages:read:tenant",
                is_active=True,
                is_visible=True,
                is_system=True,
                module_code=None
            )
            db.add(manage_pages)
            print(f"  ✅ Created: Manage Pages (route: builder/pages, permission: builder:pages:read:tenant)")
            created_count += 1
        else:
            # Update permission if it changed
            if manage_pages.permission != "builder:pages:read:tenant":
                manage_pages.permission = "builder:pages:read:tenant"
                updated_count += 1
                print(f"  🔄 Updated: Manage Pages (permission updated)")
            else:
                print(f"  ⏭️  Manage Pages already exists")
                existing_count += 1

        # Step 5: Create Pages Showcase menu item
        print("\n🎨 Step 5: Creating Pages Showcase menu item...")
        pages_showcase = db.query(MenuItem).filter(MenuItem.code == "builder_pages_showcase").first()

        if not pages_showcase:
            pages_showcase = MenuItem(
                code="builder_pages_showcase",
                tenant_id=None,
                parent_id=ui_builder.id,
                order=30,
                title="Pages Showcase",
                icon="ph-duotone ph-squares-four",
                route="builder-showcase",
                description="Browse and preview created pages",
                permission="builder:design:tenant",
                is_active=True,
                is_visible=True,
                is_system=True,
                module_code=None
            )
            db.add(pages_showcase)
            print(f"  ✅ Created: Pages Showcase (route: builder/showcase, permission: builder:design:tenant)")
            created_count += 1
        else:
            # Update permission if it changed
            if pages_showcase.permission != "builder:design:tenant":
                pages_showcase.permission = "builder:design:tenant"
                updated_count += 1
                print(f"  🔄 Updated: Pages Showcase (permission updated)")
            else:
                print(f"  ⏭️  Pages Showcase already exists")
                existing_count += 1

        db.commit()

        print("\n" + "=" * 70)
        print("✅ UI BUILDER MENU ITEMS SEEDED SUCCESSFULLY")
        print("=" * 70)
        print(f"\nSummary:")
        print(f"  • Created: {created_count} menu items")
        print(f"  • Updated: {updated_count} menu items")
        print(f"  • Existing: {existing_count} menu items")
        print(f"\nMenu Structure:")
        print(f"  Developer Tools")
        print(f"    └── UI Builder")
        print(f"          ├── Page Designer (builder:design:tenant)")
        print(f"          ├── Manage Pages (builder:pages:read:tenant)")
        print(f"          └── Pages Showcase (builder:design:tenant)")
        print(f"\nThe UI Builder menu should now appear for users with the required permissions!")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error seeding UI Builder menu items: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_builder_menu()
