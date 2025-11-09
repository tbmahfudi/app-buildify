"""
Module Management RBAC Seed Data
=================================
Sets up permissions, roles, and groups for module management functionality.

These permissions control who can install, uninstall, enable, and disable modules.

Run: python -m app.seeds.seed_module_management_rbac
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


def seed_module_management_rbac(tenant_code=None):
    """
    Seed RBAC permissions, roles, and groups for module management.

    Creates:
    - Module management permissions (superuser operations)
    - Module viewing permissions (all authenticated users)
    - Roles for module management
    - Groups for module management

    Args:
        tenant_code: Optional tenant code to create roles/groups for. If None, only permissions are created.
    """
    db = SessionLocal()

    try:
        print("\n" + "="*80)
        print("MODULE MANAGEMENT RBAC SETUP")
        print("="*80 + "\n")

        # ========================================================================
        # STEP 1: Register Module Management Permissions
        # ========================================================================
        print("📋 Step 1: Registering Module Management permissions...")

        module_permissions = [
            # View/List modules (available to all authenticated users)
            {
                "code": "modules:list:tenant",
                "name": "List Modules",
                "description": "View list of available modules",
                "resource": "modules",
                "action": "list",
                "scope": "tenant",
                "category": "module_management",
                "is_system": True
            },
            {
                "code": "modules:view:tenant",
                "name": "View Module Details",
                "description": "View detailed information about a module",
                "resource": "modules",
                "action": "view",
                "scope": "tenant",
                "category": "module_management",
                "is_system": True
            },
            # Install/Uninstall (superuser only - platform-wide operations)
            {
                "code": "modules:install:all",
                "name": "Install Modules",
                "description": "Install modules platform-wide (superuser only)",
                "resource": "modules",
                "action": "install",
                "scope": "all",
                "category": "module_management",
                "is_system": True
            },
            {
                "code": "modules:uninstall:all",
                "name": "Uninstall Modules",
                "description": "Uninstall modules platform-wide (superuser only)",
                "resource": "modules",
                "action": "uninstall",
                "scope": "all",
                "category": "module_management",
                "is_system": True
            },
            {
                "code": "modules:sync:all",
                "name": "Sync Modules",
                "description": "Sync modules from filesystem (superuser only)",
                "resource": "modules",
                "action": "sync",
                "scope": "all",
                "category": "module_management",
                "is_system": True
            },
            # Enable/Disable for tenant (tenant admin operations)
            {
                "code": "modules:enable:tenant",
                "name": "Enable Modules for Tenant",
                "description": "Enable modules for the current tenant",
                "resource": "modules",
                "action": "enable",
                "scope": "tenant",
                "category": "module_management",
                "is_system": True
            },
            {
                "code": "modules:disable:tenant",
                "name": "Disable Modules for Tenant",
                "description": "Disable modules for the current tenant",
                "resource": "modules",
                "action": "disable",
                "scope": "tenant",
                "category": "module_management",
                "is_system": True
            },
            {
                "code": "modules:configure:tenant",
                "name": "Configure Modules",
                "description": "Update module configuration for tenant",
                "resource": "modules",
                "action": "configure",
                "scope": "tenant",
                "category": "module_management",
                "is_system": True
            },
            # Management page access
            {
                "code": "modules:manage:tenant",
                "name": "Access Module Management",
                "description": "Access module management page",
                "resource": "modules",
                "action": "manage",
                "scope": "tenant",
                "category": "module_management",
                "is_system": True
            }
        ]

        created_count = 0
        existing_count = 0

        for perm_data in module_permissions:
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

        permission_map = {p["code"]: db.query(Permission).filter(Permission.code == p["code"]).first()
                         for p in module_permissions}

        # ========================================================================
        # STEP 2: Create Roles and Groups (if tenant specified)
        # ========================================================================
        roles_created = 0
        groups_created = 0

        if tenant_code:
            print(f"\n👥 Step 2: Creating Module Management roles and groups for tenant '{tenant_code}'...")

            # Get tenant
            tenant = db.query(Tenant).filter(Tenant.code == tenant_code).first()
            if not tenant:
                print(f"  ⚠ Tenant '{tenant_code}' not found. Skipping roles and groups creation.")
            else:
                # Define roles configuration
                roles_config = {
                    "Module Administrator": {
                        "code": "MODULE_ADMIN",
                        "description": "Full module management access for tenant (enable, disable, configure)",
                        "permissions": [
                            "modules:list:tenant",
                            "modules:view:tenant",
                            "modules:enable:tenant",
                            "modules:disable:tenant",
                            "modules:configure:tenant",
                            "modules:manage:tenant"
                        ]
                    },
                    "Module Viewer": {
                        "code": "MODULE_VIEWER",
                        "description": "View-only access to module information",
                        "permissions": [
                            "modules:list:tenant",
                            "modules:view:tenant"
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

                    db.commit()
                    role_map[role_name] = role

                # Create groups
                groups_config = {
                    "Module Administrators": {
                        "code": "MODULE_ADMINS",
                        "description": "Users who can manage modules for the tenant",
                        "roles": ["Module Administrator"],
                        "group_type": "team"
                    },
                    "Module Viewers": {
                        "code": "MODULE_VIEWERS",
                        "description": "Users who can view module information",
                        "roles": ["Module Viewer"],
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

                print(f"✓ Created {roles_created} roles and {groups_created} groups")

        # ========================================================================
        # SUMMARY
        # ========================================================================
        print("\n" + "="*80)
        print("✅ MODULE MANAGEMENT RBAC SETUP COMPLETE!")
        print("="*80)

        print(f"\n📋 Permissions Created:")
        print(f"   • Platform-wide operations (superuser only):")
        print(f"      - modules:install:all")
        print(f"      - modules:uninstall:all")
        print(f"      - modules:sync:all")

        print(f"\n   • Tenant operations (admin/users):")
        print(f"      - modules:list:tenant")
        print(f"      - modules:view:tenant")
        print(f"      - modules:enable:tenant")
        print(f"      - modules:disable:tenant")
        print(f"      - modules:configure:tenant")
        print(f"      - modules:manage:tenant")

        if tenant_code and roles_created > 0:
            print(f"\n👥 Roles and Groups Created for tenant '{tenant_code}':")
            print(f"   • Module Administrator role → Module Administrators group")
            print(f"   • Module Viewer role → Module Viewers group")

        print(f"\n🎯 Next Steps:")
        print(f"   1. Superusers automatically have all module management permissions")
        if tenant_code and groups_created > 0:
            print(f"   2. Add tenant admins to 'Module Administrators' group for tenant-level management")
            print(f"   3. Add users to 'Module Viewers' group for view-only access")
            print(f"   4. Restart the backend server")
            print(f"   5. Access module management at /app#modules")
        else:
            print(f"   2. Run this script with a tenant code to create roles and groups")
            print(f"      Example: seed_module_management_rbac('FASHIONHUB')")
            print(f"   3. Restart the backend server")
            print(f"   4. Access module management at /app#modules")

        print("\n" + "="*80 + "\n")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    # Check if tenant code provided as argument
    tenant_code = sys.argv[1] if len(sys.argv) > 1 else None

    print("\n🚀 Starting Module Management RBAC Setup...")
    if tenant_code:
        print(f"   Creating roles and groups for tenant: {tenant_code}")
    else:
        print("   Creating permissions only (no tenant specified)")

    seed_module_management_rbac(tenant_code)
    print("✅ Done!\n")
