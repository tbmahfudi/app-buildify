"""
Create RBAC management permissions
Covers: Roles, Permissions, Groups, User RBAC operations
"""
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.permission import Permission

def seed_rbac_permissions():
    """Seed all RBAC-related permissions"""
    db = SessionLocal()

    try:
        # Define all RBAC permissions
        permissions = [
            # ==================== PERMISSION MANAGEMENT ====================
            {
                "code": "permissions:read:all",
                "name": "View All Permissions",
                "description": "View all permissions in the system (Superuser only)",
                "resource": "permissions",
                "action": "read",
                "scope": "all",
                "category": "rbac"
            },
            {
                "code": "permissions:read:tenant",
                "name": "View Tenant Permissions",
                "description": "View permissions available to tenant",
                "resource": "permissions",
                "action": "read",
                "scope": "tenant",
                "category": "rbac"
            },
            {
                "code": "permissions:read:own",
                "name": "View Own Permissions",
                "description": "View own effective permissions",
                "resource": "permissions",
                "action": "read",
                "scope": "own",
                "category": "rbac"
            },
            {
                "code": "permissions:create:all",
                "name": "Create Permissions",
                "description": "Create new system permissions (Superuser only)",
                "resource": "permissions",
                "action": "create",
                "scope": "all",
                "category": "rbac"
            },
            {
                "code": "permissions:update:all",
                "name": "Update Permissions",
                "description": "Update system permissions (Superuser only)",
                "resource": "permissions",
                "action": "update",
                "scope": "all",
                "category": "rbac"
            },
            {
                "code": "permissions:delete:all",
                "name": "Delete Permissions",
                "description": "Delete system permissions (Superuser only)",
                "resource": "permissions",
                "action": "delete",
                "scope": "all",
                "category": "rbac"
            },

            # ==================== ROLE MANAGEMENT ====================
            {
                "code": "roles:read:all",
                "name": "View All Roles",
                "description": "View all roles across all tenants (Superuser only)",
                "resource": "roles",
                "action": "read",
                "scope": "all",
                "category": "rbac"
            },
            {
                "code": "roles:read:tenant",
                "name": "View Tenant Roles",
                "description": "View all roles within tenant",
                "resource": "roles",
                "action": "read",
                "scope": "tenant",
                "category": "rbac"
            },
            {
                "code": "roles:read:own",
                "name": "View Own Roles",
                "description": "View own assigned roles",
                "resource": "roles",
                "action": "read",
                "scope": "own",
                "category": "rbac"
            },
            {
                "code": "roles:create:tenant",
                "name": "Create Roles",
                "description": "Create new roles within tenant",
                "resource": "roles",
                "action": "create",
                "scope": "tenant",
                "category": "rbac"
            },
            {
                "code": "roles:update:tenant",
                "name": "Update Roles",
                "description": "Update roles within tenant",
                "resource": "roles",
                "action": "update",
                "scope": "tenant",
                "category": "rbac"
            },
            {
                "code": "roles:delete:tenant",
                "name": "Delete Roles",
                "description": "Delete roles within tenant",
                "resource": "roles",
                "action": "delete",
                "scope": "tenant",
                "category": "rbac"
            },
            {
                "code": "roles:assign_permissions:tenant",
                "name": "Assign Permissions to Roles",
                "description": "Grant permissions to roles",
                "resource": "roles",
                "action": "assign_permissions",
                "scope": "tenant",
                "category": "rbac"
            },
            {
                "code": "roles:revoke_permissions:tenant",
                "name": "Revoke Permissions from Roles",
                "description": "Remove permissions from roles",
                "resource": "roles",
                "action": "revoke_permissions",
                "scope": "tenant",
                "category": "rbac"
            },

            # ==================== GROUP MANAGEMENT ====================
            {
                "code": "groups:read:all",
                "name": "View All Groups",
                "description": "View all groups across all tenants (Superuser only)",
                "resource": "groups",
                "action": "read",
                "scope": "all",
                "category": "rbac"
            },
            {
                "code": "groups:read:tenant",
                "name": "View Tenant Groups",
                "description": "View all groups within tenant",
                "resource": "groups",
                "action": "read",
                "scope": "tenant",
                "category": "rbac"
            },
            {
                "code": "groups:read:company",
                "name": "View Company Groups",
                "description": "View groups within company",
                "resource": "groups",
                "action": "read",
                "scope": "company",
                "category": "rbac"
            },
            {
                "code": "groups:read:own",
                "name": "View Own Groups",
                "description": "View own group memberships",
                "resource": "groups",
                "action": "read",
                "scope": "own",
                "category": "rbac"
            },
            {
                "code": "groups:create:tenant",
                "name": "Create Groups",
                "description": "Create new groups within tenant",
                "resource": "groups",
                "action": "create",
                "scope": "tenant",
                "category": "rbac"
            },
            {
                "code": "groups:update:tenant",
                "name": "Update Groups",
                "description": "Update groups within tenant",
                "resource": "groups",
                "action": "update",
                "scope": "tenant",
                "category": "rbac"
            },
            {
                "code": "groups:delete:tenant",
                "name": "Delete Groups",
                "description": "Delete groups within tenant",
                "resource": "groups",
                "action": "delete",
                "scope": "tenant",
                "category": "rbac"
            },
            {
                "code": "groups:add_members:tenant",
                "name": "Add Group Members",
                "description": "Add users to groups",
                "resource": "groups",
                "action": "add_members",
                "scope": "tenant",
                "category": "rbac"
            },
            {
                "code": "groups:remove_members:tenant",
                "name": "Remove Group Members",
                "description": "Remove users from groups",
                "resource": "groups",
                "action": "remove_members",
                "scope": "tenant",
                "category": "rbac"
            },
            {
                "code": "groups:assign_roles:tenant",
                "name": "Assign Roles to Groups",
                "description": "Grant roles to groups",
                "resource": "groups",
                "action": "assign_roles",
                "scope": "tenant",
                "category": "rbac"
            },
            {
                "code": "groups:revoke_roles:tenant",
                "name": "Revoke Roles from Groups",
                "description": "Remove roles from groups",
                "resource": "groups",
                "action": "revoke_roles",
                "scope": "tenant",
                "category": "rbac"
            },

            # ==================== USER RBAC OPERATIONS ====================
            {
                "code": "users:read_roles:tenant",
                "name": "View User Roles",
                "description": "View roles assigned to users",
                "resource": "users",
                "action": "read_roles",
                "scope": "tenant",
                "category": "rbac"
            },
            {
                "code": "users:read_permissions:tenant",
                "name": "View User Permissions",
                "description": "View effective permissions of users",
                "resource": "users",
                "action": "read_permissions",
                "scope": "tenant",
                "category": "rbac"
            },
            {
                "code": "users:assign_roles:tenant",
                "name": "Assign Roles to Users",
                "description": "Directly assign roles to users",
                "resource": "users",
                "action": "assign_roles",
                "scope": "tenant",
                "category": "rbac"
            },
            {
                "code": "users:revoke_roles:tenant",
                "name": "Revoke Roles from Users",
                "description": "Remove roles from users",
                "resource": "users",
                "action": "revoke_roles",
                "scope": "tenant",
                "category": "rbac"
            },

            # ==================== RBAC DASHBOARD ====================
            {
                "code": "rbac:dashboard:view:tenant",
                "name": "View RBAC Dashboard",
                "description": "View RBAC dashboard with statistics",
                "resource": "rbac",
                "action": "dashboard:view",
                "scope": "tenant",
                "category": "rbac"
            },
        ]

        # Create permissions
        created_count = 0
        updated_count = 0

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
        print(f"RBAC Permissions Seed Complete")
        print(f"{'='*60}")
        print(f"✓ Created: {created_count} permissions")
        print(f"• Updated: {updated_count} permissions")
        print(f"📊 Total: {len(permissions)} RBAC permissions")
        print(f"{'='*60}\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_rbac_permissions()
