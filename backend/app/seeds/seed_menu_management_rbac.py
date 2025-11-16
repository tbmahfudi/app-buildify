"""
Menu Management RBAC Seed Data
================================
Sets up roles and groups for menu management functionality.

These roles control who can manage menu items (create, update, delete, reorder).

Run: python -m app.seeds.seed_menu_management_rbac [TENANT_CODE]
"""

import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.group import Group
from app.models.rbac_junctions import RolePermission, GroupRole
from app.models.tenant import Tenant


def seed_menu_management_rbac(tenant_code=None):
    """
    Seed RBAC roles and groups for menu management.

    Prerequisites:
        - Menu permissions must exist (run: python -m app.seeds.seed_menu_items)

    Creates:
        - Roles for menu management (Menu Administrator, Menu Viewer)
        - Groups for menu management
        - Role-permission assignments

    Args:
        tenant_code: Optional tenant code to create roles/groups for. If None, lists available tenants.
    """
    db = SessionLocal()

    try:
        print("\n" + "="*80)
        print("MENU MANAGEMENT RBAC SETUP")
        print("="*80 + "\n")

        # ========================================================================
        # STEP 1: Verify Menu Permissions Exist
        # ========================================================================
        print("📋 Step 1: Verifying menu management permissions exist...")

        required_permissions = [
            "menu:read:tenant",
            "menu:create:tenant",
            "menu:update:tenant",
            "menu:delete:tenant",
            "menu:manage:tenant"
        ]

        permission_map = {}
        missing_permissions = []

        for perm_code in required_permissions:
            perm = db.query(Permission).filter(Permission.code == perm_code).first()
            if perm:
                permission_map[perm_code] = perm
                print(f"  ✓ Found permission: {perm_code}")
            else:
                missing_permissions.append(perm_code)
                print(f"  ✗ Missing permission: {perm_code}")

        if missing_permissions:
            print("\n❌ ERROR: Some menu permissions are missing!")
            print("\n💡 Solution:")
            print("   Run the menu items seed first to create permissions:")
            print("   python -m app.seeds.seed_menu_items")
            print("\n" + "="*80 + "\n")
            return 0

        print(f"\n✓ All {len(required_permissions)} menu permissions found")

        # ========================================================================
        # STEP 2: Create Roles and Groups (if tenant specified)
        # ========================================================================
        roles_created = 0
        groups_created = 0

        if not tenant_code:
            print("\n" + "="*80)
            print("ℹ️  NO TENANT SPECIFIED")
            print("="*80)
            print("\nTo create menu management roles and groups, provide a tenant code:")
            print("\nAvailable tenants:")

            tenants = db.query(Tenant).all()
            if not tenants:
                print("  ⚠️  No tenants found. Please create a tenant first.")
            else:
                for tenant in tenants:
                    print(f"  • {tenant.name} (code: {tenant.code})")

                print(f"\nUsage:")
                print(f"  python -m app.seeds.seed_menu_management_rbac [TENANT_CODE]")
                print(f"\nExample:")
                print(f"  python -m app.seeds.seed_menu_management_rbac {tenants[0].code}")

            print("\n" + "="*80 + "\n")
            return 0

        print(f"\n👥 Step 2: Creating menu management roles and groups for tenant '{tenant_code}'...")

        # Get tenant
        tenant = db.query(Tenant).filter(Tenant.code == tenant_code).first()
        if not tenant:
            print(f"\n❌ ERROR: Tenant '{tenant_code}' not found!")
            print("\nAvailable tenants:")
            tenants = db.query(Tenant).all()
            for t in tenants:
                print(f"  • {t.name} (code: {t.code})")
            print("\n" + "="*80 + "\n")
            return 0

        print(f"  ✓ Found tenant: {tenant.name}")

        # Define roles configuration
        roles_config = {
            "Menu Administrator": {
                "code": "MENU_ADMIN",
                "description": "Full menu management access (create, update, delete, reorder menu items)",
                "permissions": [
                    "menu:read:tenant",
                    "menu:create:tenant",
                    "menu:update:tenant",
                    "menu:delete:tenant",
                    "menu:manage:tenant"
                ]
            },
            "Menu Viewer": {
                "code": "MENU_VIEWER",
                "description": "View-only access to menu items",
                "permissions": [
                    "menu:read:tenant"
                ]
            }
        }

        role_map = {}
        for role_name, role_config in roles_config.items():
            # Check if role exists
            role = db.query(Role).filter(
                Role.code == role_config["code"],
                Role.tenant_id == tenant.id
            ).first()

            if not role:
                role = Role(
                    code=role_config["code"],
                    name=role_name,
                    description=role_config["description"],
                    tenant_id=tenant.id,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.add(role)
                db.flush()
                print(f"  ✓ Created role: {role_name}")
                roles_created += 1
            else:
                print(f"  • Role exists: {role_name}")

            # Assign permissions to role
            for perm_code in role_config["permissions"]:
                perm = permission_map.get(perm_code)
                if perm:
                    # Check if permission already assigned
                    existing = db.query(RolePermission).filter(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == perm.id
                    ).first()

                    if not existing:
                        role_perm = RolePermission(
                            id=str(uuid.uuid4()),
                            role_id=str(role.id),
                            permission_id=str(perm.id),
                            created_at=datetime.utcnow()
                        )
                        db.add(role_perm)
                        print(f"    ✓ Assigned permission: {perm_code}")

            db.commit()
            role_map[role_name] = role

        # Create groups
        groups_config = {
            "Menu Administrators": {
                "code": "MENU_ADMINS",
                "description": "Users who can manage menu items for the tenant",
                "roles": ["Menu Administrator"],
                "group_type": "team"
            },
            "Menu Viewers": {
                "code": "MENU_VIEWERS",
                "description": "Users who can view menu items",
                "roles": ["Menu Viewer"],
                "group_type": "team"
            }
        }

        for group_name, group_config in groups_config.items():
            # Check if group exists
            group = db.query(Group).filter(
                Group.code == group_config["code"],
                Group.tenant_id == tenant.id,
                Group.company_id == None  # Tenant-wide group
            ).first()

            if not group:
                group = Group(
                    code=group_config["code"],
                    name=group_name,
                    description=group_config["description"],
                    tenant_id=tenant.id,
                    company_id=None,  # Tenant-wide
                    group_type=group_config["group_type"],
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.add(group)
                db.flush()
                print(f"  ✓ Created group: {group_name}")
                groups_created += 1
            else:
                print(f"  • Group exists: {group_name}")

            # Assign roles to group
            for role_name in group_config["roles"]:
                role = role_map.get(role_name)
                if role:
                    # Check if role already assigned to group
                    existing = db.query(GroupRole).filter(
                        GroupRole.group_id == group.id,
                        GroupRole.role_id == role.id
                    ).first()

                    if not existing:
                        group_role = GroupRole(
                            id=str(uuid.uuid4()),
                            group_id=str(group.id),
                            role_id=str(role.id),
                            created_at=datetime.utcnow()
                        )
                        db.add(group_role)
                        print(f"    ✓ Assigned role '{role_name}' to group '{group_name}'")

            db.commit()

        print(f"\n✓ Created {roles_created} roles and {groups_created} groups")

        # ========================================================================
        # SUMMARY
        # ========================================================================
        print("\n" + "="*80)
        print("✅ MENU MANAGEMENT RBAC SETUP COMPLETE!")
        print("="*80)

        print(f"\n📋 Menu Permissions:")
        print(f"   • menu:read:tenant - View menu items")
        print(f"   • menu:create:tenant - Create menu items")
        print(f"   • menu:update:tenant - Update menu items")
        print(f"   • menu:delete:tenant - Delete menu items")
        print(f"   • menu:manage:tenant - Full menu management access")

        if tenant_code and (roles_created > 0 or groups_created > 0):
            print(f"\n👥 Roles and Groups Created for tenant '{tenant_code}':")
            print(f"   • Menu Administrator role → Menu Administrators group")
            print(f"     (Full menu management: create, update, delete, reorder)")
            print(f"   • Menu Viewer role → Menu Viewers group")
            print(f"     (View-only access)")

        print(f"\n🎯 Next Steps:")
        print(f"   1. Superusers automatically have all menu management permissions")
        if tenant_code and (groups_created > 0 or roles_created > 0):
            print(f"   2. Add tenant admins to 'Menu Administrators' group for full menu management")
            print(f"   3. Add users to 'Menu Viewers' group for view-only access")
            print(f"   4. Access menu management at /api/v1/menu")
        else:
            print(f"   2. Roles and groups already exist - check group membership")
            print(f"   3. Access menu management at /api/v1/menu")

        print("\n" + "="*80 + "\n")

        return roles_created + groups_created

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    # Check if tenant code provided as argument
    tenant_code = sys.argv[1] if len(sys.argv) > 1 else None

    print("\n🚀 Starting Menu Management RBAC Setup...")
    if tenant_code:
        print(f"   Creating roles and groups for tenant: {tenant_code}")
    else:
        print("   No tenant specified - will list available tenants")

    result = seed_menu_management_rbac(tenant_code)

    if result > 0:
        print("✅ Done!\n")
    elif tenant_code:
        print("⚠️  Roles may already exist or encountered an error\n")
    else:
        print("ℹ️  Run with a tenant code to create roles and groups\n")
