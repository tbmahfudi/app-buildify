"""
Create organization management permissions
Covers: Tenants, Companies, Branches, Departments, Users
"""
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.permission import Permission

def seed_organization_permissions():
    """Seed all organization-related permissions"""
    db = SessionLocal()

    try:
        # Define all organization permissions
        permissions = [
            # ==================== TENANT MANAGEMENT ====================
            {
                "code": "tenants:read:all",
                "name": "View All Tenants",
                "description": "View all tenants in the system (Superuser only)",
                "resource": "tenants",
                "action": "read",
                "scope": "all",
                "category": "organization"
            },
            {
                "code": "tenants:read:own",
                "name": "View Own Tenant",
                "description": "View own tenant information",
                "resource": "tenants",
                "action": "read",
                "scope": "own",
                "category": "organization"
            },
            {
                "code": "tenants:create:all",
                "name": "Create Tenants",
                "description": "Create new tenants (Superuser only)",
                "resource": "tenants",
                "action": "create",
                "scope": "all",
                "category": "organization"
            },
            {
                "code": "tenants:update:all",
                "name": "Update Any Tenant",
                "description": "Update any tenant (Superuser only)",
                "resource": "tenants",
                "action": "update",
                "scope": "all",
                "category": "organization"
            },
            {
                "code": "tenants:update:own",
                "name": "Update Own Tenant",
                "description": "Update own tenant settings",
                "resource": "tenants",
                "action": "update",
                "scope": "own",
                "category": "organization"
            },
            {
                "code": "tenants:delete:all",
                "name": "Delete Tenants",
                "description": "Delete tenants (Superuser only)",
                "resource": "tenants",
                "action": "delete",
                "scope": "all",
                "category": "organization"
            },

            # ==================== COMPANY MANAGEMENT ====================
            {
                "code": "companies:read:all",
                "name": "View All Companies",
                "description": "View all companies across all tenants (Superuser only)",
                "resource": "companies",
                "action": "read",
                "scope": "all",
                "category": "organization"
            },
            {
                "code": "companies:read:tenant",
                "name": "View Tenant Companies",
                "description": "View all companies within tenant",
                "resource": "companies",
                "action": "read",
                "scope": "tenant",
                "category": "organization"
            },
            {
                "code": "companies:read:own",
                "name": "View Own Company",
                "description": "View own company information",
                "resource": "companies",
                "action": "read",
                "scope": "own",
                "category": "organization"
            },
            {
                "code": "companies:create:tenant",
                "name": "Create Companies",
                "description": "Create new companies within tenant",
                "resource": "companies",
                "action": "create",
                "scope": "tenant",
                "category": "organization"
            },
            {
                "code": "companies:update:tenant",
                "name": "Update Tenant Companies",
                "description": "Update any company within tenant",
                "resource": "companies",
                "action": "update",
                "scope": "tenant",
                "category": "organization"
            },
            {
                "code": "companies:update:own",
                "name": "Update Own Company",
                "description": "Update own company details",
                "resource": "companies",
                "action": "update",
                "scope": "own",
                "category": "organization"
            },
            {
                "code": "companies:delete:tenant",
                "name": "Delete Companies",
                "description": "Delete companies within tenant",
                "resource": "companies",
                "action": "delete",
                "scope": "tenant",
                "category": "organization"
            },

            # ==================== BRANCH MANAGEMENT ====================
            {
                "code": "branches:read:all",
                "name": "View All Branches",
                "description": "View all branches across all tenants (Superuser only)",
                "resource": "branches",
                "action": "read",
                "scope": "all",
                "category": "organization"
            },
            {
                "code": "branches:read:tenant",
                "name": "View Tenant Branches",
                "description": "View all branches within tenant",
                "resource": "branches",
                "action": "read",
                "scope": "tenant",
                "category": "organization"
            },
            {
                "code": "branches:read:company",
                "name": "View Company Branches",
                "description": "View branches within company",
                "resource": "branches",
                "action": "read",
                "scope": "company",
                "category": "organization"
            },
            {
                "code": "branches:read:own",
                "name": "View Own Branch",
                "description": "View own branch information",
                "resource": "branches",
                "action": "read",
                "scope": "own",
                "category": "organization"
            },
            {
                "code": "branches:create:company",
                "name": "Create Branches",
                "description": "Create new branches within company",
                "resource": "branches",
                "action": "create",
                "scope": "company",
                "category": "organization"
            },
            {
                "code": "branches:update:company",
                "name": "Update Company Branches",
                "description": "Update branches within company",
                "resource": "branches",
                "action": "update",
                "scope": "company",
                "category": "organization"
            },
            {
                "code": "branches:update:own",
                "name": "Update Own Branch",
                "description": "Update own branch details",
                "resource": "branches",
                "action": "update",
                "scope": "own",
                "category": "organization"
            },
            {
                "code": "branches:delete:company",
                "name": "Delete Branches",
                "description": "Delete branches within company",
                "resource": "branches",
                "action": "delete",
                "scope": "company",
                "category": "organization"
            },

            # ==================== DEPARTMENT MANAGEMENT ====================
            {
                "code": "departments:read:all",
                "name": "View All Departments",
                "description": "View all departments across all tenants (Superuser only)",
                "resource": "departments",
                "action": "read",
                "scope": "all",
                "category": "organization"
            },
            {
                "code": "departments:read:tenant",
                "name": "View Tenant Departments",
                "description": "View all departments within tenant",
                "resource": "departments",
                "action": "read",
                "scope": "tenant",
                "category": "organization"
            },
            {
                "code": "departments:read:branch",
                "name": "View Branch Departments",
                "description": "View departments within branch",
                "resource": "departments",
                "action": "read",
                "scope": "branch",
                "category": "organization"
            },
            {
                "code": "departments:read:own",
                "name": "View Own Department",
                "description": "View own department information",
                "resource": "departments",
                "action": "read",
                "scope": "own",
                "category": "organization"
            },
            {
                "code": "departments:create:branch",
                "name": "Create Departments",
                "description": "Create new departments within branch",
                "resource": "departments",
                "action": "create",
                "scope": "branch",
                "category": "organization"
            },
            {
                "code": "departments:update:branch",
                "name": "Update Branch Departments",
                "description": "Update departments within branch",
                "resource": "departments",
                "action": "update",
                "scope": "branch",
                "category": "organization"
            },
            {
                "code": "departments:update:own",
                "name": "Update Own Department",
                "description": "Update own department details",
                "resource": "departments",
                "action": "update",
                "scope": "own",
                "category": "organization"
            },
            {
                "code": "departments:delete:branch",
                "name": "Delete Departments",
                "description": "Delete departments within branch",
                "resource": "departments",
                "action": "delete",
                "scope": "branch",
                "category": "organization"
            },

            # ==================== ORGANIZATION VIEW ====================
            {
                "code": "organization:view:tenant",
                "name": "View Organization Structure",
                "description": "View complete organization hierarchy",
                "resource": "organization",
                "action": "view",
                "scope": "tenant",
                "category": "organization"
            },

            # ==================== USER MANAGEMENT ====================
            {
                "code": "users:read:all",
                "name": "View All Users",
                "description": "View all users across all tenants (Superuser only)",
                "resource": "users",
                "action": "read",
                "scope": "all",
                "category": "user_management"
            },
            {
                "code": "users:read:tenant",
                "name": "View Tenant Users",
                "description": "View all users within tenant",
                "resource": "users",
                "action": "read",
                "scope": "tenant",
                "category": "user_management"
            },
            {
                "code": "users:read:company",
                "name": "View Company Users",
                "description": "View users within company",
                "resource": "users",
                "action": "read",
                "scope": "company",
                "category": "user_management"
            },
            {
                "code": "users:read:department",
                "name": "View Department Users",
                "description": "View users within department",
                "resource": "users",
                "action": "read",
                "scope": "department",
                "category": "user_management"
            },
            {
                "code": "users:read:own",
                "name": "View Own Profile",
                "description": "View own user profile",
                "resource": "users",
                "action": "read",
                "scope": "own",
                "category": "user_management"
            },
            {
                "code": "users:create:tenant",
                "name": "Create Users",
                "description": "Create new users within tenant",
                "resource": "users",
                "action": "create",
                "scope": "tenant",
                "category": "user_management"
            },
            {
                "code": "users:update:all",
                "name": "Update Any User",
                "description": "Update any user (Superuser only)",
                "resource": "users",
                "action": "update",
                "scope": "all",
                "category": "user_management"
            },
            {
                "code": "users:update:tenant",
                "name": "Update Tenant Users",
                "description": "Update any user within tenant",
                "resource": "users",
                "action": "update",
                "scope": "tenant",
                "category": "user_management"
            },
            {
                "code": "users:update:own",
                "name": "Update Own Profile",
                "description": "Update own user profile",
                "resource": "users",
                "action": "update",
                "scope": "own",
                "category": "user_management"
            },
            {
                "code": "users:delete:all",
                "name": "Delete Any User",
                "description": "Delete any user (Superuser only)",
                "resource": "users",
                "action": "delete",
                "scope": "all",
                "category": "user_management"
            },
            {
                "code": "users:delete:tenant",
                "name": "Delete Tenant Users",
                "description": "Delete users within tenant",
                "resource": "users",
                "action": "delete",
                "scope": "tenant",
                "category": "user_management"
            },
            {
                "code": "users:reset_password:all",
                "name": "Reset Any User Password",
                "description": "Reset password for any user (Superuser only)",
                "resource": "users",
                "action": "reset_password",
                "scope": "all",
                "category": "user_management"
            },
            {
                "code": "users:reset_password:tenant",
                "name": "Reset Tenant User Passwords",
                "description": "Reset passwords for users within tenant",
                "resource": "users",
                "action": "reset_password",
                "scope": "tenant",
                "category": "user_management"
            },
            {
                "code": "users:change_password:own",
                "name": "Change Own Password",
                "description": "Change own password",
                "resource": "users",
                "action": "change_password",
                "scope": "own",
                "category": "user_management"
            },
            {
                "code": "users:impersonate:all",
                "name": "Impersonate Users",
                "description": "Impersonate any user for support purposes (Superuser only)",
                "resource": "users",
                "action": "impersonate",
                "scope": "all",
                "category": "user_management"
            },
        ]

        # Create permissions
        created_count = 0
        updated_count = 0
        existing_count = 0

        for perm_data in permissions:
            perm = db.query(Permission).filter(
                Permission.code == perm_data["code"]
            ).first()

            if not perm:
                perm = Permission(**perm_data, is_active=True)
                db.add(perm)
                db.flush()
                print(f"✓ Created: {perm_data['code']}")
                created_count += 1
            else:
                # Update existing permission details
                for key, value in perm_data.items():
                    setattr(perm, key, value)
                perm.is_active = True
                print(f"• Updated: {perm_data['code']}")
                updated_count += 1

        db.commit()

        print(f"\n{'='*60}")
        print(f"Organization Permissions Seed Complete")
        print(f"{'='*60}")
        print(f"✓ Created: {created_count} permissions")
        print(f"• Updated: {updated_count} permissions")
        print(f"📊 Total: {len(permissions)} organization permissions")
        print(f"{'='*60}\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_organization_permissions()
