"""
Module Management RBAC Seed Data
=================================
Sets up permissions for module management functionality.

These permissions control who can install, uninstall, enable, and disable modules.

Run: python -m app.seeds.seed_module_management_rbac
"""

from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.permission import Permission


def seed_module_management_rbac():
    """
    Seed RBAC permissions for module management.

    Creates:
    - Module management permissions (superuser operations)
    - Module viewing permissions (all authenticated users)
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

        print(f"\n🎯 Next Steps:")
        print(f"   1. Superusers automatically have all module management permissions")
        print(f"   2. Assign 'modules:manage:tenant' to tenant admins for tenant-level management")
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
    print("\n🚀 Starting Module Management RBAC Setup...")
    seed_module_management_rbac()
    print("✅ Done!\n")
