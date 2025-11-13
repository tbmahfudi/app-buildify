#!/usr/bin/env python3
"""
Finance Module Access Diagnostic Tool

This script checks:
1. If the finance module is registered
2. If the finance module is installed
3. If the finance module is enabled for specific tenants
4. Which users have access to the finance module
5. User permissions for finance operations
"""

import sys
sys.path.insert(0, '/home/user/app-buildify/backend')

from app.core.db import SessionLocal
from app.models.module_registry import ModuleRegistry, TenantModule
from app.models.tenant import Tenant
from app.models.user import User
from app.models.permission import Permission
from app.models.role import Role
from app.models.rbac_junctions import RolePermission, GroupRole, UserGroup
from app.models.group import Group
from sqlalchemy.orm import joinedload

def main():
    print("\n" + "=" * 80)
    print("FINANCE MODULE ACCESS DIAGNOSTIC")
    print("=" * 80 + "\n")

    db = SessionLocal()

    try:
        # 1. Check if financial module is registered
        print("1️⃣  CHECKING MODULE REGISTRATION")
        print("-" * 80)

        module = db.query(ModuleRegistry).filter(
            ModuleRegistry.name == "financial"
        ).first()

        if not module:
            print("❌ Financial module NOT FOUND in module_registry")
            print("   Solution: Run module sync to register the module")
            print("   Command: POST /api/v1/modules/sync")
            return

        print(f"✅ Module registered: {module.display_name}")
        print(f"   - Name: {module.name}")
        print(f"   - Version: {module.version}")
        print(f"   - Installed: {module.is_installed}")
        print(f"   - Status: {module.status}")
        print()

        # 2. Check if module is installed
        print("2️⃣  CHECKING MODULE INSTALLATION")
        print("-" * 80)

        if not module.is_installed:
            print("❌ Financial module is NOT INSTALLED")
            print("   Solution: Install the module")
            print("   Command: POST /api/v1/modules/install")
            print("   Body: {\"module_name\": \"financial\"}")
            return

        print("✅ Module is installed")
        print(f"   - Installed at: {module.installed_at}")
        print(f"   - Installed by: {module.installed_by_user_id}")
        print()

        # 3. Check tenant enablement
        print("3️⃣  CHECKING TENANT ENABLEMENT")
        print("-" * 80)

        tenant_modules = db.query(TenantModule).filter(
            TenantModule.module_id == module.id,
            TenantModule.is_enabled == True
        ).all()

        if not tenant_modules:
            print("❌ Financial module is NOT ENABLED for any tenant")
            print("\n   Solution: Enable the module for your tenant")
            print("   Command: POST /api/v1/modules/enable")
            print("   Body: {")
            print("     \"module_name\": \"financial\",")
            print("     \"configuration\": {")
            print("       \"default_currency\": \"USD\",")
            print("       \"fiscal_year_start\": \"01-01\",")
            print("       \"enable_multi_currency\": false,")
            print("       \"tax_rate\": 0,")
            print("       \"invoice_prefix\": \"INV\"")
            print("     }")
            print("   }")
            print()

            # List all tenants
            tenants = db.query(Tenant).all()
            if tenants:
                print("   Available tenants:")
                for t in tenants:
                    print(f"     - {t.name} (Code: {t.code}, ID: {t.id})")
            return

        print(f"✅ Module enabled for {len(tenant_modules)} tenant(s):")
        for tm in tenant_modules:
            tenant = db.query(Tenant).filter(Tenant.id == tm.tenant_id).first()
            print(f"\n   📋 Tenant: {tenant.name if tenant else 'Unknown'}")
            print(f"      - Tenant ID: {tm.tenant_id}")
            print(f"      - Enabled at: {tm.enabled_at}")
            print(f"      - Configuration: {tm.configuration}")
        print()

        # 4. Check users with access
        print("4️⃣  CHECKING USER ACCESS")
        print("-" * 80)

        enabled_tenant_ids = [tm.tenant_id for tm in tenant_modules]

        # Get all financial permissions
        financial_permissions = db.query(Permission).filter(
            Permission.code.like('financial:%')
        ).all()

        if not financial_permissions:
            print("⚠️  No financial permissions found in database")
            print("   This might cause access issues even if module is enabled")
            print()
        else:
            print(f"✅ Found {len(financial_permissions)} financial permissions")
            print()

        # For each tenant with the module enabled, find users with access
        for tm in tenant_modules:
            tenant = db.query(Tenant).filter(Tenant.id == tm.tenant_id).first()
            if not tenant:
                continue

            print(f"\n   👥 Users in tenant: {tenant.name}")
            print("   " + "-" * 76)

            # Get all users in this tenant
            users = db.query(User).filter(
                User.tenant_id == tenant.id,
                User.is_active == True
            ).all()

            if not users:
                print("      ❌ No active users found in this tenant")
                continue

            # Check each user's permissions
            for user in users:
                # Get user's groups
                user_groups = db.query(UserGroup).filter(
                    UserGroup.user_id == user.id
                ).all()

                # Get roles from groups
                group_ids = [ug.group_id for ug in user_groups]
                group_roles = db.query(GroupRole).filter(
                    GroupRole.group_id.in_(group_ids)
                ).all() if group_ids else []

                role_ids = [gr.role_id for gr in group_roles]

                # Get permissions from roles
                role_permissions = db.query(RolePermission).filter(
                    RolePermission.role_id.in_(role_ids)
                ).all() if role_ids else []

                permission_ids = [rp.permission_id for rp in role_permissions]

                # Get actual permission objects
                user_permissions = db.query(Permission).filter(
                    Permission.id.in_(permission_ids)
                ).all() if permission_ids else []

                # Filter for financial permissions
                user_financial_perms = [p for p in user_permissions if p.code.startswith('financial:')]

                # Get group names
                groups = db.query(Group).filter(
                    Group.id.in_(group_ids)
                ).all() if group_ids else []
                group_names = [g.name for g in groups]

                # Get role names
                roles = db.query(Role).filter(
                    Role.id.in_(role_ids)
                ).all() if role_ids else []
                role_names = [r.name for r in roles]

                if user_financial_perms:
                    print(f"\n      ✅ {user.email}")
                    print(f"         - Full Name: {user.full_name}")
                    if group_names:
                        print(f"         - Groups: {', '.join(group_names)}")
                    if role_names:
                        print(f"         - Roles: {', '.join(role_names)}")
                    print(f"         - Financial Permissions: {len(user_financial_perms)}")

                    # Show sample permissions
                    sample_perms = [p.code for p in user_financial_perms[:5]]
                    for perm_code in sample_perms:
                        print(f"           • {perm_code}")
                    if len(user_financial_perms) > 5:
                        print(f"           ... and {len(user_financial_perms) - 5} more")
                else:
                    print(f"\n      ⚠️  {user.email}")
                    print(f"         - Full Name: {user.full_name}")
                    print(f"         - Has NO financial permissions")
                    if group_names:
                        print(f"         - Groups: {', '.join(group_names)}")
                    else:
                        print(f"         - Not in any groups")

        # 5. Summary and recommendations
        print("\n" + "=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)

        print(f"\n✓ Module Status:")
        print(f"  - Registered: ✅ Yes")
        print(f"  - Installed: ✅ Yes")
        print(f"  - Enabled for tenants: {len(tenant_modules)}")
        print(f"  - Financial permissions in DB: {len(financial_permissions)}")

        print(f"\n💡 RECOMMENDATIONS:")

        if len(tenant_modules) == 0:
            print("  1. Enable the financial module for your tenant")
            print("     Method: Use the API endpoint POST /api/v1/modules/enable")

        if not financial_permissions:
            print("  2. Install the module to register permissions")
            print("     The permissions should be auto-registered during installation")

        # Check if any users have no permissions
        users_without_perms = []
        for tm in tenant_modules:
            users = db.query(User).filter(
                User.tenant_id == tm.tenant_id,
                User.is_active == True
            ).all()

            for user in users:
                user_groups = db.query(UserGroup).filter(UserGroup.user_id == user.id).all()
                if not user_groups:
                    users_without_perms.append(user.email)

        if users_without_perms:
            print("  3. Assign users to financial groups/roles:")
            print(f"     Users without groups: {', '.join(users_without_perms[:5])}")
            if len(users_without_perms) > 5:
                print(f"     ... and {len(users_without_perms) - 5} more")
            print("     Solution: Run seed_financial_rbac.py to set up roles and assign users")

        print("\n" + "=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
