"""
Check User Permissions and Roles
=================================
Diagnostic script to check what permissions and roles a user has.

Usage: python -m app.seeds.check_user_permissions <email>
"""

import sys

from app.core.db import SessionLocal
from app.models.permission import Permission
from app.models.rbac_junctions import GroupRole, RolePermission, UserGroup, UserRole
from app.models.role import Role
from app.models.user import User


def check_user_permissions(email: str):
    """Check permissions for a user"""
    db = SessionLocal()

    try:
        # Find user
        user = db.query(User).filter(User.email == email).first()

        if not user:
            print(f"\n❌ User not found: {email}")
            return

        print("\n" + "=" * 80)
        print(f"USER: {user.email}")
        print("=" * 80)

        print("\n👤 User Info:")
        print(f"  - Name: {user.full_name}")
        print(f"  - Email: {user.email}")
        print(f"  - Is Superuser: {user.is_superuser}")
        print(f"  - Is Active: {user.is_active}")
        print(f"  - Tenant ID: {user.tenant_id}")

        # Check if superuser
        if user.is_superuser:
            print("\n🌟 SUPERUSER STATUS")
            print("  ✅ This user is a SUPERUSER and has ALL permissions automatically!")
            print("  ✅ All menus should be visible without explicit permissions")

        # Check direct role assignments
        print("\n📋 Direct Role Assignments:")
        direct_roles = db.query(Role).join(UserRole).filter(UserRole.user_id == user.id).all()

        if direct_roles:
            for role in direct_roles:
                print(f"  ✅ {role.code} - {role.name}")
        else:
            print("  ⚠️  No direct roles assigned")

        # Check group memberships and roles through groups
        print("\n👥 Group Memberships & Roles:")
        from app.models.group import Group

        groups = db.query(Group).join(UserGroup).filter(UserGroup.user_id == user.id).all()

        all_roles = []
        if groups:
            for group in groups:
                print(f"  📁 Group: {group.name} ({group.code})")

                # Get roles assigned to this group
                group_roles = db.query(Role).join(GroupRole).filter(GroupRole.group_id == group.id).all()

                if group_roles:
                    for role in group_roles:
                        print(f"     └─ Role: {role.code} - {role.name}")
                        all_roles.append(role)
                else:
                    print("     └─ No roles assigned to this group")
        else:
            print("  ⚠️  Not a member of any groups")

        # Combine all roles
        all_roles.extend(direct_roles)
        unique_roles = {role.id: role for role in all_roles}

        # Check Phase 1 permissions specifically
        print("\n🔧 Phase 1 No-Code Platform Permissions:")
        phase1_permission_codes = [
            "data_model:read:tenant",
            "workflows:read:tenant",
            "automations:read:tenant",
            "lookups:read:tenant",
        ]

        for perm_code in phase1_permission_codes:
            perm = db.query(Permission).filter(Permission.code == perm_code).first()

            if not perm:
                print(f"  ❌ {perm_code} - PERMISSION NOT CREATED")
                continue

            # Check if any of user's roles has this permission
            has_permission = False
            for role in unique_roles.values():
                role_has_perm = (
                    db.query(RolePermission)
                    .filter(RolePermission.role_id == role.id, RolePermission.permission_id == perm.id)
                    .first()
                )

                if role_has_perm:
                    has_permission = True
                    print(f"  ✅ {perm_code} (via role: {role.code})")
                    break

            if not has_permission and not user.is_superuser:
                print(f"  ❌ {perm_code} - NOT GRANTED")

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        if user.is_superuser:
            print("✅ User is SUPERUSER - has all permissions")
            print("✅ All No-Code Platform menus should be visible")
        elif unique_roles:
            print(f"✅ User has {len(unique_roles)} role(s)")
            print("📋 To see No-Code Platform menus:")
            print("   1. Run: docker exec -it app_buildify_backend python -m app.seeds.seed_phase1_permissions")
            print("   2. Logout and login again to refresh permissions")
        else:
            print("⚠️  User has NO roles assigned")
            print("💡 To grant access:")
            print("   1. Assign user to 'Administrators' group, OR")
            print("   2. Assign 'tenant_admin' role to user")
            print("   3. Run: docker exec -it app_buildify_backend python -m app.seeds.seed_phase1_permissions")
            print("   4. Logout and login again")

        print("")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()


def main():
    if len(sys.argv) < 2:
        print("\nUsage: python -m app.seeds.check_user_permissions <email>")
        print("\nExample: python -m app.seeds.check_user_permissions admin@example.com\n")
        sys.exit(1)

    email = sys.argv[1]
    check_user_permissions(email)


if __name__ == "__main__":
    main()
