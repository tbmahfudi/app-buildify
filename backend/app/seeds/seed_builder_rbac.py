"""
UI Builder RBAC Seed
====================
Seeds permissions and role for the UI Builder feature.

This creates:
1. 8 UI Builder permissions
2. A "UI Builder Admin" system role
3. Assigns all permissions to the role
4. Assigns the role to the "Administrators" group

Run: python -m app.seeds.seed_builder_rbac
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.db import SessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.group import Group
from app.models.rbac_junctions import RolePermission, GroupRole


# ============================================================================
# UI BUILDER PERMISSIONS
# ============================================================================

BUILDER_PERMISSIONS = [
    {
        "code": "builder:design:tenant",
        "name": "Design UI Pages",
        "description": "Create and design UI pages using the builder",
        "category": "builder",
        "resource": "builder",
        "action": "design",
        "scope": "tenant"
    },
    {
        "code": "builder:pages:read:tenant",
        "name": "View Builder Pages",
        "description": "View list of builder pages",
        "category": "builder",
        "resource": "pages",
        "action": "read",
        "scope": "tenant"
    },
    {
        "code": "builder:pages:create:tenant",
        "name": "Create Builder Pages",
        "description": "Create new builder pages",
        "category": "builder",
        "resource": "pages",
        "action": "create",
        "scope": "tenant"
    },
    {
        "code": "builder:pages:edit:tenant",
        "name": "Edit Builder Pages",
        "description": "Edit existing builder pages",
        "category": "builder",
        "resource": "pages",
        "action": "edit",
        "scope": "tenant"
    },
    {
        "code": "builder:pages:delete:tenant",
        "name": "Delete Builder Pages",
        "description": "Delete builder pages",
        "category": "builder",
        "resource": "pages",
        "action": "delete",
        "scope": "tenant"
    },
    {
        "code": "builder:publish:tenant",
        "name": "Publish Pages",
        "description": "Publish builder pages to production",
        "category": "builder",
        "resource": "builder",
        "action": "publish",
        "scope": "tenant"
    },
    {
        "code": "builder:manage-permissions:tenant",
        "name": "Manage Page Permissions",
        "description": "Assign permissions to builder pages",
        "category": "builder",
        "resource": "permissions",
        "action": "manage",
        "scope": "tenant"
    },
    {
        "code": "builder:manage-menus:tenant",
        "name": "Manage Page Menus",
        "description": "Create menu entries for builder pages",
        "category": "builder",
        "resource": "menus",
        "action": "manage",
        "scope": "tenant"
    }
]


def seed_builder_permissions(db: Session):
    """Create UI Builder permissions"""
    print("\n📋 Creating UI Builder Permissions...")
    print("-" * 70)

    created_count = 0
    existing_count = 0

    for perm_data in BUILDER_PERMISSIONS:
        # Check if permission already exists
        existing = db.query(Permission).filter(Permission.code == perm_data["code"]).first()

        if existing:
            print(f"  ⏭️  {perm_data['code']} (already exists)")
            existing_count += 1
            continue

        # Create permission (ID auto-generated)
        permission = Permission(
            code=perm_data["code"],
            name=perm_data["name"],
            description=perm_data["description"],
            category=perm_data["category"],
            resource=perm_data["resource"],
            action=perm_data["action"],
            scope=perm_data["scope"],
            is_active=True,
            is_system=True  # System permission, can't be deleted
        )

        db.add(permission)
        print(f"  ✅ {perm_data['code']}")
        created_count += 1

    db.commit()

    print(f"\n  Created: {created_count} | Existing: {existing_count}")
    print(f"  Total: {len(BUILDER_PERMISSIONS)} UI Builder permissions")


def seed_builder_role(db: Session):
    """Create UI Builder Admin role and assign permissions"""
    print("\n👤 Creating UI Builder Admin Role...")
    print("-" * 70)

    # Check if role already exists
    role_code = "ui_builder_admin"
    existing_role = db.query(Role).filter(Role.code == role_code).first()

    if existing_role:
        print(f"  ⏭️  Role '{role_code}' already exists")
        role = existing_role
    else:
        # Create system role (tenant_id = None means available to all tenants, ID auto-generated)
        role = Role(
            tenant_id=None,  # System role
            code=role_code,
            name="UI Builder Administrator",
            description="Full access to UI Builder - design, manage, and publish pages",
            role_type="system",
            is_active=True,
            is_system=True
        )

        db.add(role)
        db.commit()
        print(f"  ✅ Created role: {role.name}")

    # Assign all builder permissions to the role
    print("\n  Assigning permissions to role...")
    assigned_count = 0
    existing_count = 0

    for perm_data in BUILDER_PERMISSIONS:
        # Get permission
        permission = db.query(Permission).filter(Permission.code == perm_data["code"]).first()

        if not permission:
            print(f"    ⚠️  Permission not found: {perm_data['code']}")
            continue

        # Check if already assigned
        existing = db.query(RolePermission).filter(
            and_(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == permission.id
            )
        ).first()

        if existing:
            existing_count += 1
            continue

        # Assign permission to role (ID auto-generated)
        role_perm = RolePermission(
            role_id=role.id,
            permission_id=permission.id
        )

        db.add(role_perm)
        print(f"    ✅ {permission.code}")
        assigned_count += 1

    db.commit()

    print(f"\n  Assigned: {assigned_count} | Already assigned: {existing_count}")

    return role


def assign_role_to_admin_group(db: Session, role: Role):
    """Assign UI Builder Admin role to the Administrators group"""
    print("\n🔗 Assigning Role to Administrators Group...")
    print("-" * 70)

    # Find the administrators group (tenant_id = None for default groups, or first tenant)
    admin_group = db.query(Group).filter(Group.code == "administrators").first()

    if not admin_group:
        print("  ⚠️  'Administrators' group not found!")
        print("  💡 Run seed_rbac_with_groups.py first to create default groups")
        return

    # Check if already assigned
    existing = db.query(GroupRole).filter(
        and_(
            GroupRole.group_id == admin_group.id,
            GroupRole.role_id == role.id
        )
    ).first()

    if existing:
        print(f"  ⏭️  Role already assigned to '{admin_group.name}' group")
        return

    # Assign role to group (ID auto-generated)
    group_role = GroupRole(
        group_id=admin_group.id,
        role_id=role.id
    )

    db.add(group_role)
    db.commit()

    print(f"  ✅ Assigned '{role.name}' role to '{admin_group.name}' group")
    print(f"  📍 Group: {admin_group.name} (tenant: {admin_group.tenant_id or 'system'})")


def seed_builder_rbac():
    """Main function to seed UI Builder RBAC"""
    print("\n" + "=" * 70)
    print("UI BUILDER RBAC SEED")
    print("=" * 70)

    db = SessionLocal()

    try:
        # Step 1: Create permissions
        seed_builder_permissions(db)

        # Step 2: Create role and assign permissions
        role = seed_builder_role(db)

        # Step 3: Assign role to administrators group
        assign_role_to_admin_group(db, role)

        print("\n" + "=" * 70)
        print("✅ UI BUILDER RBAC SEEDED SUCCESSFULLY")
        print("=" * 70)
        print("\nWhat was created:")
        print("  • 8 UI Builder permissions")
        print("  • 1 UI Builder Admin role (system role)")
        print("  • Role assigned to Administrators group")
        print("\nNext steps:")
        print("  1. Users in the Administrators group now have access to UI Builder")
        print("  2. You can assign this role to other groups as needed")
        print("  3. Access the UI Builder at: Developer Tools → UI Builder")
        print("\n" + "=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error seeding UI Builder RBAC: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_builder_rbac()
