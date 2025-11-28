"""
Create default role templates with permission assignments
Based on FRONTEND_PERMISSIONS_MAP.md and BACKEND_API_PERMISSIONS.md
"""
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.role import Role
from app.models.permission import Permission
from app.models.rbac_junctions import RolePermission

def seed_role_templates():
    """Seed default role templates with appropriate permissions"""
    db = SessionLocal()

    try:
        # Define role templates
        role_templates = [
            {
                "code": "superuser",
                "name": "Superuser",
                "description": "Full system access - all permissions across all tenants",
                "is_system": True,
                "permissions": []  # Superusers bypass permission checks
            },
            {
                "code": "tenant_admin",
                "name": "Tenant Administrator",
                "description": "Full administrative access within tenant",
                "is_system": False,
                "permissions": [
                    # Organization Management
                    "companies:read:tenant", "companies:create:tenant", "companies:update:tenant", "companies:delete:tenant",
                    "branches:read:tenant", "branches:create:company", "branches:update:company", "branches:delete:company",
                    "departments:read:tenant", "departments:create:branch", "departments:update:branch", "departments:delete:branch",
                    "organization:view:tenant",

                    # User Management
                    "users:read:tenant", "users:create:tenant", "users:update:tenant", "users:delete:tenant",
                    "users:reset_password:tenant", "users:change_password:own",

                    # RBAC Management
                    "permissions:read:tenant",
                    "roles:read:tenant", "roles:create:tenant", "roles:update:tenant", "roles:delete:tenant",
                    "roles:assign_permissions:tenant", "roles:revoke_permissions:tenant",
                    "groups:read:tenant", "groups:create:tenant", "groups:update:tenant", "groups:delete:tenant",
                    "groups:add_members:tenant", "groups:remove_members:tenant",
                    "groups:assign_roles:tenant", "groups:revoke_roles:tenant",
                    "users:read_roles:tenant", "users:read_permissions:tenant",
                    "users:assign_roles:tenant", "users:revoke_roles:tenant",
                    "rbac:dashboard:view:tenant",

                    # Dashboard Management
                    "dashboards:read:tenant", "dashboards:create:tenant", "dashboards:update:tenant", "dashboards:delete:tenant",
                    "dashboards:clone:tenant", "dashboards:share:tenant", "dashboards:snapshot:tenant", "dashboards:export:tenant",
                    "dashboards:create_page:tenant", "dashboards:create_widget:tenant",

                    # Report Management
                    "reports:read:tenant", "reports:create:tenant", "reports:update:tenant", "reports:delete:tenant",
                    "reports:execute:tenant", "reports:export:tenant",
                    "reports:schedule:create:tenant", "reports:schedule:read:tenant",
                    "reports:schedule:update:tenant", "reports:schedule:delete:tenant",
                    "reports:templates:read:tenant", "reports:templates:create:tenant",
                    "reports:templates:update:tenant", "reports:templates:delete:tenant",

                    # Scheduler Management
                    "scheduler:config:read:tenant", "scheduler:config:create:tenant",
                    "scheduler:config:update:tenant", "scheduler:config:delete:tenant",
                    "scheduler:jobs:read:tenant", "scheduler:jobs:create:tenant",
                    "scheduler:jobs:update:tenant", "scheduler:jobs:delete:tenant", "scheduler:jobs:execute:tenant",
                    "scheduler:executions:read:tenant", "scheduler:executions:cancel:tenant",

                    # Audit & Monitoring
                    "audit:read:tenant", "audit:summary:read:tenant", "audit:export:tenant",
                    "api_activity:read:tenant", "api_activity:metrics:tenant",
                    "analytics:read:tenant", "analytics:export:tenant",

                    # Settings Management
                    "settings:read:tenant", "settings:update:tenant",
                    "settings:branding:read:tenant", "settings:branding:update:tenant",
                    "settings:integration:read:tenant", "settings:integration:update:tenant",
                    "settings:api_keys:read:tenant", "settings:api_keys:create:tenant",
                    "settings:api_keys:revoke:tenant", "settings:api_keys:delete:tenant",
                    "settings:email:read:tenant", "settings:email:update:tenant", "settings:email:test:tenant",
                    "settings:sms:read:tenant", "settings:sms:update:tenant", "settings:sms:test:tenant",

                    # Metadata Management
                    "metadata:read:tenant", "metadata:create:tenant", "metadata:update:tenant", "metadata:delete:tenant",
                    "metadata:schema:design:tenant", "metadata:schema:deploy:tenant", "metadata:schema:export:tenant",
                    "metadata:fields:create:tenant", "metadata:fields:update:tenant", "metadata:fields:delete:tenant",
                ]
            },
            {
                "code": "company_manager",
                "name": "Company Manager",
                "description": "Manage company operations, branches, departments, and users within company",
                "is_system": False,
                "permissions": [
                    # Organization - Company scope
                    "companies:read:tenant", "companies:update:own",
                    "branches:read:company", "branches:create:company", "branches:update:company", "branches:delete:company",
                    "departments:read:branch", "departments:create:branch", "departments:update:branch", "departments:delete:branch",
                    "organization:view:tenant",

                    # User Management - Company scope
                    "users:read:company", "users:create:tenant", "users:update:tenant",
                    "users:reset_password:tenant", "users:change_password:own",
                    "users:read_roles:tenant", "users:assign_roles:tenant",

                    # Dashboards
                    "dashboards:read:tenant", "dashboards:create:tenant", "dashboards:update:own", "dashboards:delete:own",
                    "dashboards:clone:tenant", "dashboards:export:tenant",

                    # Reports
                    "reports:read:company", "reports:create:tenant", "reports:update:own",
                    "reports:execute:company", "reports:export:company",
                    "reports:schedule:create:tenant", "reports:schedule:read:tenant",

                    # Analytics
                    "analytics:read:company", "analytics:export:company",
                    "audit:read:company",

                    # Settings
                    "settings:read:own", "settings:update:own",
                ]
            },
            {
                "code": "department_manager",
                "name": "Department Manager",
                "description": "Manage department operations and users",
                "is_system": False,
                "permissions": [
                    # Organization - Department scope
                    "departments:read:branch", "departments:update:own",
                    "organization:view:tenant",

                    # User Management - Department scope
                    "users:read:department", "users:change_password:own",

                    # Dashboards
                    "dashboards:read:tenant", "dashboards:create:tenant", "dashboards:update:own",

                    # Reports
                    "reports:read:department", "reports:execute:department", "reports:export:department",

                    # Analytics
                    "analytics:read:department",
                    "audit:read:department",

                    # Settings
                    "settings:read:own", "settings:update:own",
                ]
            },
            {
                "code": "security_admin",
                "name": "Security Administrator",
                "description": "Manage security, RBAC, permissions, and audit logs",
                "is_system": False,
                "permissions": [
                    # RBAC Full Management
                    "permissions:read:tenant",
                    "roles:read:tenant", "roles:create:tenant", "roles:update:tenant", "roles:delete:tenant",
                    "roles:assign_permissions:tenant", "roles:revoke_permissions:tenant",
                    "groups:read:tenant", "groups:create:tenant", "groups:update:tenant", "groups:delete:tenant",
                    "groups:add_members:tenant", "groups:remove_members:tenant",
                    "groups:assign_roles:tenant", "groups:revoke_roles:tenant",
                    "users:read:tenant", "users:read_roles:tenant", "users:read_permissions:tenant",
                    "users:assign_roles:tenant", "users:revoke_roles:tenant",
                    "users:reset_password:tenant",
                    "rbac:dashboard:view:tenant",

                    # Audit & Security
                    "audit:read:tenant", "audit:summary:read:tenant", "audit:export:tenant",
                    "api_activity:read:tenant", "api_activity:metrics:tenant",
                    "analytics:read:tenant",

                    # Settings - Security related
                    "settings:api_keys:read:tenant", "settings:api_keys:create:tenant",
                    "settings:api_keys:revoke:tenant", "settings:api_keys:delete:tenant",
                    "auth_policies:read:tenant", "auth_policies:update:tenant",

                    # Organization (read-only for context)
                    "companies:read:tenant", "branches:read:company", "departments:read:branch",
                    "organization:view:tenant",
                ]
            },
            {
                "code": "module_admin",
                "name": "Module Administrator",
                "description": "Manage modules, menus, and security configuration",
                "is_system": False,
                "permissions": [
                    # Module & Menu Management (from existing seed scripts)
                    "modules:read:all", "modules:create:all", "modules:update:all", "modules:delete:all",
                    "menus:read:all", "menus:create:all", "menus:update:all", "menus:delete:all",

                    # Metadata Management
                    "metadata:read:tenant", "metadata:create:tenant", "metadata:update:tenant", "metadata:delete:tenant",
                    "metadata:schema:design:tenant", "metadata:schema:deploy:tenant",
                    "metadata:fields:create:tenant", "metadata:fields:update:tenant", "metadata:fields:delete:tenant",

                    # Settings
                    "settings:read:tenant", "settings:update:tenant",
                    "integrations:read:tenant", "integrations:configure:tenant",

                    # View organization
                    "organization:view:tenant",
                ]
            },
            {
                "code": "report_developer",
                "name": "Report Developer",
                "description": "Create and manage reports, dashboards, and analytics",
                "is_system": False,
                "permissions": [
                    # Full Report Management
                    "reports:read:tenant", "reports:create:tenant", "reports:update:tenant", "reports:delete:tenant",
                    "reports:execute:tenant", "reports:export:tenant",
                    "reports:schedule:create:tenant", "reports:schedule:read:tenant",
                    "reports:schedule:update:tenant", "reports:schedule:delete:tenant",
                    "reports:templates:read:tenant", "reports:templates:create:tenant",
                    "reports:templates:update:tenant", "reports:templates:delete:tenant",
                    "reports:history:read:tenant",

                    # Dashboard Management
                    "dashboards:read:tenant", "dashboards:create:tenant", "dashboards:update:tenant", "dashboards:delete:tenant",
                    "dashboards:clone:tenant", "dashboards:share:tenant", "dashboards:export:tenant",
                    "dashboards:create_page:tenant", "dashboards:update_page:own", "dashboards:delete_page:own",
                    "dashboards:create_widget:tenant", "dashboards:update_widget:own", "dashboards:delete_widget:own",

                    # Analytics
                    "analytics:read:tenant", "analytics:export:tenant",

                    # View organization for report context
                    "companies:read:tenant", "branches:read:company", "departments:read:branch",
                    "users:read:tenant", "organization:view:tenant",
                ]
            },
            {
                "code": "regular_user",
                "name": "Regular User",
                "description": "Standard user with basic access to view and use the system",
                "is_system": False,
                "permissions": [
                    # Basic organization view
                    "companies:read:tenant", "branches:read:company", "departments:read:branch",
                    "users:read:own", "users:change_password:own",

                    # View dashboards
                    "dashboards:read:tenant", "dashboards:create:tenant", "dashboards:update:own", "dashboards:delete:own",

                    # Execute and view reports
                    "reports:read:tenant", "reports:execute:own", "reports:history:read:own",

                    # View own data
                    "audit:read:own", "api_activity:read:own",

                    # Personal settings
                    "settings:read:own", "settings:update:own",
                ]
            },
            {
                "code": "auditor",
                "name": "Auditor",
                "description": "Read-only access to audit logs, reports, and analytics",
                "is_system": False,
                "permissions": [
                    # Audit & Monitoring (read-only)
                    "audit:read:tenant", "audit:summary:read:tenant", "audit:export:tenant",
                    "api_activity:read:tenant", "api_activity:metrics:tenant",
                    "analytics:read:tenant", "analytics:export:tenant",

                    # Reports (read and execute only)
                    "reports:read:tenant", "reports:execute:tenant", "reports:export:tenant",
                    "reports:history:read:tenant",

                    # View dashboards
                    "dashboards:read:tenant",

                    # View organization structure
                    "companies:read:tenant", "branches:read:company", "departments:read:branch",
                    "users:read:tenant", "organization:view:tenant",

                    # View RBAC configuration
                    "permissions:read:tenant", "roles:read:tenant", "groups:read:tenant",
                    "users:read_roles:tenant", "users:read_permissions:tenant",
                ]
            },
        ]

        # Create roles and assign permissions
        created_count = 0
        updated_count = 0
        permissions_assigned = 0

        for role_template in role_templates:
            # Check if role exists
            role = db.query(Role).filter(Role.code == role_template["code"]).first()

            if not role:
                # Create new role
                role = Role(
                    code=role_template["code"],
                    name=role_template["name"],
                    description=role_template["description"],
                    is_system=role_template["is_system"],
                    is_active=True
                )
                db.add(role)
                db.flush()
                print(f"✓ Created role: {role_template['name']} ({role_template['code']})")
                created_count += 1
            else:
                # Update existing role
                role.name = role_template["name"]
                role.description = role_template["description"]
                role.is_system = role_template["is_system"]
                role.is_active = True
                print(f"• Updated role: {role_template['name']} ({role_template['code']})")
                updated_count += 1

            # Clear existing permissions for this role
            db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()

            # Assign permissions
            for perm_code in role_template["permissions"]:
                permission = db.query(Permission).filter(Permission.code == perm_code).first()
                if permission:
                    role_perm = RolePermission(
                        role_id=role.id,
                        permission_id=permission.id
                    )
                    db.add(role_perm)
                    permissions_assigned += 1
                else:
                    print(f"  ⚠️  Permission not found: {perm_code}")

        db.commit()

        print(f"\n{'='*60}")
        print(f"Role Templates Seed Complete")
        print(f"{'='*60}")
        print(f"✓ Created: {created_count} roles")
        print(f"• Updated: {updated_count} roles")
        print(f"📊 Total: {len(role_templates)} role templates")
        print(f"🔑 Permissions assigned: {permissions_assigned}")
        print(f"{'='*60}\n")

        # Print role summary
        print("Role Templates Created:")
        print("-" * 60)
        for role_template in role_templates:
            perm_count = len(role_template["permissions"])
            print(f"{role_template['name']:30} - {perm_count:3} permissions")
        print(f"{'='*60}\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_role_templates()
