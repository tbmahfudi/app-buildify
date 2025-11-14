"""
Assign Menu Management Permissions to Admin Roles
==================================================
One-time script to assign menu:manage:tenant and menu:read:tenant
permissions to existing admin roles.

Usage:
  python assign_menu_permissions.py [ROLE_CODE] [TENANT_CODE]

Examples:
  python assign_menu_permissions.py ADMIN FASHIONHUB
  python assign_menu_permissions.py SYSTEM_ADMIN TECHSTART

If no arguments provided, the script will list available roles.
"""

import sys
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.rbac_junctions import RolePermission


def list_roles_and_tenants(db: Session):
    """List all available roles and tenants."""
    print("\n" + "="*80)
    print("AVAILABLE TENANTS")
    print("="*80)

    tenants = db.query(Tenant).all()
    if not tenants:
        print("  ⚠️  No tenants found. Please create a tenant first.")
        return False

    for tenant in tenants:
        print(f"\n  📋 Tenant: {tenant.name}")
        print(f"     Code: {tenant.code}")
        print(f"     ID: {tenant.id}")

        # List roles for this tenant
        roles = db.query(Role).filter(Role.tenant_id == tenant.id).all()
        if roles:
            print(f"     Roles:")
            for role in roles:
                print(f"       • {role.name} (code: {role.code})")
        else:
            print(f"     ⚠️  No roles found for this tenant")

    print("\n" + "="*80)
    print("\nUsage:")
    print("  python assign_menu_permissions.py [ROLE_CODE] [TENANT_CODE]")
    print("\nExample:")
    if tenants and roles:
        print(f"  python assign_menu_permissions.py {roles[0].code} {tenant.code}")
    print("\n" + "="*80 + "\n")

    return True


def assign_menu_permissions(role_code: str, tenant_code: str):
    """
    Assign menu management permissions to a specific role.

    Args:
        role_code: The code of the role to assign permissions to
        tenant_code: The code of the tenant
    """
    db = SessionLocal()

    try:
        print("\n" + "="*80)
        print("ASSIGN MENU PERMISSIONS TO ADMIN ROLE")
        print("="*80 + "\n")

        # Find tenant
        tenant = db.query(Tenant).filter(Tenant.code == tenant_code).first()
        if not tenant:
            print(f"❌ ERROR: Tenant '{tenant_code}' not found!")
            print("\nAvailable tenants:")
            list_roles_and_tenants(db)
            return False

        print(f"✓ Found tenant: {tenant.name} ({tenant.code})")

        # Find role
        role = db.query(Role).filter(
            Role.code == role_code,
            Role.tenant_id == tenant.id
        ).first()

        if not role:
            print(f"❌ ERROR: Role '{role_code}' not found for tenant '{tenant_code}'!")
            print("\nAvailable roles for this tenant:")
            roles = db.query(Role).filter(Role.tenant_id == tenant.id).all()
            for r in roles:
                print(f"  • {r.name} (code: {r.code})")
            return False

        print(f"✓ Found role: {role.name} ({role.code})")

        # Find menu permissions
        menu_permission_codes = [
            "menu:read:tenant",
            "menu:create:tenant",
            "menu:update:tenant",
            "menu:delete:tenant",
            "menu:manage:tenant"
        ]

        print(f"\n📋 Assigning menu permissions to role '{role.name}'...")

        assigned_count = 0
        skipped_count = 0
        missing_count = 0

        for perm_code in menu_permission_codes:
            # Find permission
            perm = db.query(Permission).filter(Permission.code == perm_code).first()

            if not perm:
                print(f"  ⚠️  Permission not found: {perm_code}")
                print(f"     (Run: python -m app.seeds.seed_menu_items to create permissions)")
                missing_count += 1
                continue

            # Check if already assigned
            existing = db.query(RolePermission).filter(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == perm.id
            ).first()

            if existing:
                print(f"  • Already assigned: {perm_code}")
                skipped_count += 1
            else:
                # Assign permission to role
                role_perm = RolePermission(
                    id=str(uuid.uuid4()),
                    role_id=str(role.id),
                    permission_id=str(perm.id),
                    created_at=datetime.utcnow()
                )
                db.add(role_perm)
                print(f"  ✓ Assigned: {perm_code}")
                assigned_count += 1

        db.commit()

        # Summary
        print("\n" + "="*80)
        print("✅ ASSIGNMENT COMPLETE!")
        print("="*80)
        print(f"\nRole: {role.name} ({role.code})")
        print(f"Tenant: {tenant.name} ({tenant.code})")
        print(f"\nResults:")
        print(f"  • Newly assigned: {assigned_count}")
        print(f"  • Already had: {skipped_count}")
        print(f"  • Missing permissions: {missing_count}")

        if missing_count > 0:
            print(f"\n⚠️  Warning: Some permissions are missing!")
            print(f"   Run: python -m app.seeds.seed_menu_items")
            print(f"   This will create the menu permissions.")

        if assigned_count > 0:
            print(f"\n✓ Successfully assigned {assigned_count} new permission(s) to '{role.name}'")
            print(f"\n🎯 Next Steps:")
            print(f"   1. Users with the '{role.name}' role now have menu management access")
            print(f"   2. They can access /api/v1/menu endpoints")
            print(f"   3. No server restart required (permissions are dynamic)")

        print("\n" + "="*80 + "\n")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        # No arguments - list available roles
        print("\n🔍 No arguments provided. Listing available roles and tenants...\n")
        db = SessionLocal()
        try:
            list_roles_and_tenants(db)
        finally:
            db.close()
        return

    if len(sys.argv) < 3:
        print("\n❌ ERROR: Both ROLE_CODE and TENANT_CODE are required!")
        print("\nUsage:")
        print("  python assign_menu_permissions.py [ROLE_CODE] [TENANT_CODE]")
        print("\nExample:")
        print("  python assign_menu_permissions.py ADMIN FASHIONHUB")
        print("\nRun without arguments to see available roles:")
        print("  python assign_menu_permissions.py\n")
        return

    role_code = sys.argv[1]
    tenant_code = sys.argv[2]

    print(f"\n🚀 Assigning menu permissions to role '{role_code}' for tenant '{tenant_code}'...")
    success = assign_menu_permissions(role_code, tenant_code)

    if success:
        print("✅ Done!\n")
    else:
        print("❌ Failed!\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
