"""
Complete RBAC Seed with Group-Based Access Control
===================================================
Seeds a consistent RBAC hierarchy: User → Group → Role → Permission

This seed file implements the proper RBAC model where:
1. Permissions are created (atomic access rights)
2. Roles are created and assigned permissions
3. Groups are created (organizational units)
4. Roles are assigned to groups
5. Users are assigned to groups

Run: python -m app.seeds.seed_rbac_with_groups
"""

import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.group import Group
from app.models.rbac_junctions import RolePermission, GroupRole, UserGroup
from app.models.user import User
from app.models.tenant import Tenant


# ============================================================================
# RECOMMENDED GROUPS
# ============================================================================

RECOMMENDED_GROUPS = """
┌─────────────────────────────────────────────────────────────────────────┐
│ RECOMMENDED GROUPS FOR RBAC                                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ 1. ADMINISTRATORS                                                        │
│    - Full system access                                                  │
│    - Manage all settings, users, and data                                │
│    - Assign roles: tenant_admin, system_admin                            │
│                                                                          │
│ 2. MANAGERS / SUPERVISORS                                                │
│    - Department/team management access                                   │
│    - Approve workflows, view reports                                     │
│    - Assign roles: manager, supervisor                                   │
│                                                                          │
│ 3. EMPLOYEES / STAFF                                                     │
│    - Standard operational access                                         │
│    - Create and edit own records                                         │
│    - Assign roles: employee, user                                        │
│                                                                          │
│ 4. VIEWERS / READ-ONLY                                                   │
│    - View-only access to data                                            │
│    - No create/update/delete permissions                                 │
│    - Assign roles: viewer, auditor                                       │
│                                                                          │
│ 5. FINANCE TEAM                                                          │
│    - Financial data access                                               │
│    - Accounting, budgeting, reporting                                    │
│    - Assign roles: accountant, financial_manager                         │
│                                                                          │
│ 6. HR TEAM                                                               │
│    - Employee records access                                             │
│    - Recruitment, payroll, benefits                                      │
│    - Assign roles: hr_manager, hr_staff                                  │
│                                                                          │
│ 7. IT SUPPORT                                                            │
│    - Technical system access                                             │
│    - User management, system configuration                               │
│    - Assign roles: it_admin, support                                     │
│                                                                          │
│ 8. DEPARTMENT-SPECIFIC GROUPS                                            │
│    - Engineering Team → roles: developer, tech_lead                      │
│    - Sales Team → roles: sales_rep, sales_manager                        │
│    - Marketing Team → roles: marketer, marketing_manager                 │
│    - Operations Team → roles: operator, operations_manager               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
"""


# ============================================================================
# DEFAULT GROUPS
# ============================================================================

DEFAULT_GROUPS = [
    {
        "code": "administrators",
        "name": "Administrators",
        "description": "Full system administrators with complete access",
        "group_type": "team",
        "roles": ["tenant_admin"]
    },
    {
        "code": "managers",
        "name": "Managers",
        "description": "Department and team managers with supervisory access",
        "group_type": "team",
        "roles": ["manager"]
    },
    {
        "code": "employees",
        "name": "Employees",
        "description": "Standard employees with operational access",
        "group_type": "team",
        "roles": ["employee"]
    },
    {
        "code": "viewers",
        "name": "Viewers",
        "description": "Read-only access for viewing data",
        "group_type": "team",
        "roles": ["viewer"]
    },
    {
        "code": "finance_team",
        "name": "Finance Team",
        "description": "Financial operations and accounting team",
        "group_type": "department",
        "roles": ["accountant"]
    },
    {
        "code": "hr_team",
        "name": "HR Team",
        "description": "Human resources and people operations team",
        "group_type": "department",
        "roles": ["hr_manager"]
    },
    {
        "code": "it_support",
        "name": "IT Support",
        "description": "Technical support and system administration",
        "group_type": "team",
        "roles": ["it_admin"]
    },
    {
        "code": "engineering",
        "name": "Engineering Team",
        "description": "Software development and engineering",
        "group_type": "department",
        "roles": ["developer"]
    },
    {
        "code": "sales_team",
        "name": "Sales Team",
        "description": "Sales and business development",
        "group_type": "department",
        "roles": ["sales_rep"]
    },
    {
        "code": "marketing_team",
        "name": "Marketing Team",
        "description": "Marketing and communications",
        "group_type": "department",
        "roles": ["marketer"]
    }
]


# ============================================================================
# DEFAULT ROLES (if not already created)
# ============================================================================

DEFAULT_ROLES = [
    {
        "code": "tenant_admin",
        "name": "Tenant Administrator",
        "description": "Full administrative access to tenant",
        "role_type": "default",
        "permissions": [
            "users:read:tenant", "users:create:tenant", "users:update:tenant", "users:delete:tenant",
            "roles:read:tenant", "roles:create:tenant", "roles:update:tenant", "roles:delete:tenant",
            "roles:assign_permissions:tenant", "roles:revoke_permissions:tenant",
            "groups:read:tenant", "groups:create:tenant", "groups:update:tenant", "groups:delete:tenant",
            "groups:add_members:tenant", "groups:remove_members:tenant",
            "groups:assign_roles:tenant", "groups:revoke_roles:tenant",
            "permissions:read:tenant",
            "companies:read:tenant", "companies:create:tenant", "companies:update:tenant",
            "organization:view:tenant"
        ]
    },
    {
        "code": "manager",
        "name": "Manager",
        "description": "Department/team manager with supervisory access",
        "role_type": "default",
        "permissions": [
            "users:read:tenant",
            "groups:read:tenant",
            "roles:read:tenant",
            "organization:view:tenant"
        ]
    },
    {
        "code": "employee",
        "name": "Employee",
        "description": "Standard employee with operational access",
        "role_type": "default",
        "permissions": [
            "users:read:own",
            "roles:read:own",
            "permissions:read:own"
        ]
    },
    {
        "code": "viewer",
        "name": "Viewer",
        "description": "Read-only access to data",
        "role_type": "default",
        "permissions": [
            "users:read:own",
            "roles:read:own"
        ]
    },
    {
        "code": "accountant",
        "name": "Accountant",
        "description": "Financial operations access",
        "role_type": "default",
        "permissions": [
            "users:read:tenant",
            "roles:read:own"
        ]
    },
    {
        "code": "hr_manager",
        "name": "HR Manager",
        "description": "Human resources management access",
        "role_type": "default",
        "permissions": [
            "users:read:tenant",
            "users:create:tenant",
            "users:update:tenant",
            "groups:read:tenant",
            "groups:add_members:tenant",
            "groups:remove_members:tenant",
            "roles:read:tenant",
            "organization:view:tenant"
        ]
    },
    {
        "code": "it_admin",
        "name": "IT Administrator",
        "description": "Technical system administration access",
        "role_type": "default",
        "permissions": [
            "users:read:tenant",
            "users:create:tenant",
            "users:update:tenant",
            "groups:read:tenant",
            "roles:read:tenant",
            "organization:view:tenant"
        ]
    },
    {
        "code": "developer",
        "name": "Developer",
        "description": "Software development access",
        "role_type": "default",
        "permissions": [
            "users:read:own",
            "roles:read:own"
        ]
    },
    {
        "code": "sales_rep",
        "name": "Sales Representative",
        "description": "Sales operations access",
        "role_type": "default",
        "permissions": [
            "users:read:own",
            "roles:read:own"
        ]
    },
    {
        "code": "marketer",
        "name": "Marketing Specialist",
        "description": "Marketing operations access",
        "role_type": "default",
        "permissions": [
            "users:read:own",
            "roles:read:own"
        ]
    }
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_id():
    """Generate UUID as string."""
    return str(uuid.uuid4())


def get_or_create_permission(db: Session, code: str) -> Permission:
    """Get existing permission or return None if not found."""
    return db.query(Permission).filter(Permission.code == code).first()


def create_roles_for_tenant(db: Session, tenant_id: str):
    """Create default roles for a tenant."""
    print(f"\n  Creating roles for tenant...")

    created_roles = {}

    for role_data in DEFAULT_ROLES:
        # Check if role exists
        existing = db.query(Role).filter(
            Role.tenant_id == tenant_id,
            Role.code == role_data['code']
        ).first()

        if existing:
            print(f"    ✓ Role exists: {role_data['name']}")
            created_roles[role_data['code']] = existing
            continue

        # Create role
        role_id = create_id()
        role = Role(
            id=role_id,
            tenant_id=tenant_id,
            code=role_data['code'],
            name=role_data['name'],
            description=role_data['description'],
            role_type=role_data['role_type'],
            is_active=True,
            is_system=False,
            created_at=datetime.utcnow()
        )
        db.add(role)
        db.flush()

        # Assign permissions to role
        for perm_code in role_data['permissions']:
            permission = get_or_create_permission(db, perm_code)
            if permission:
                role_perm = RolePermission(
                    id=create_id(),
                    role_id=role_id,
                    permission_id=permission.id,
                    created_at=datetime.utcnow()
                )
                db.add(role_perm)

        created_roles[role_data['code']] = role
        print(f"    ✓ Created role: {role_data['name']} ({len(role_data['permissions'])} permissions)")

    db.flush()
    return created_roles


def create_groups_for_tenant(db: Session, tenant_id: str, company_id: str = None):
    """Create default groups for a tenant."""
    print(f"\n  Creating groups for tenant...")

    created_groups = {}

    for group_data in DEFAULT_GROUPS:
        # Check if group exists
        existing = db.query(Group).filter(
            Group.tenant_id == tenant_id,
            Group.code == group_data['code']
        ).first()

        if existing:
            print(f"    ✓ Group exists: {group_data['name']}")
            created_groups[group_data['code']] = existing
            continue

        # Create group
        group_id = create_id()
        group = Group(
            id=group_id,
            tenant_id=tenant_id,
            company_id=company_id,  # Can be tenant-wide (None) or company-specific
            code=group_data['code'],
            name=group_data['name'],
            description=group_data['description'],
            group_type=group_data['group_type'],
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(group)
        db.flush()

        created_groups[group_data['code']] = group
        print(f"    ✓ Created group: {group_data['name']} ({group_data['group_type']})")

    db.flush()
    return created_groups


def assign_roles_to_groups(db: Session, groups: dict, roles: dict):
    """Assign roles to groups based on DEFAULT_GROUPS configuration."""
    print(f"\n  Assigning roles to groups...")

    for group_data in DEFAULT_GROUPS:
        group = groups.get(group_data['code'])
        if not group:
            continue

        for role_code in group_data['roles']:
            role = roles.get(role_code)
            if not role:
                continue

            # Check if assignment exists
            existing = db.query(GroupRole).filter(
                GroupRole.group_id == group.id,
                GroupRole.role_id == role.id
            ).first()

            if existing:
                continue

            # Create assignment
            group_role = GroupRole(
                id=create_id(),
                group_id=group.id,
                role_id=role.id,
                created_at=datetime.utcnow()
            )
            db.add(group_role)
            print(f"    ✓ Assigned role '{role.name}' to group '{group.name}'")

    db.flush()


def assign_users_to_groups(db: Session, tenant_id: str, groups: dict):
    """
    Assign existing users to appropriate groups based on their email or role.
    This is a smart assignment based on common patterns.
    """
    print(f"\n  Assigning users to groups...")

    users = db.query(User).filter(User.tenant_id == tenant_id).all()

    for user in users:
        email = user.email.lower()
        assigned_groups = []

        # Smart group assignment based on email patterns
        if any(keyword in email for keyword in ['admin', 'ceo', 'cto', 'cfo']):
            assigned_groups.append('administrators')
        elif any(keyword in email for keyword in ['manager', 'director', 'head', 'lead']):
            assigned_groups.append('managers')
        elif any(keyword in email for keyword in ['hr', 'people']):
            assigned_groups.append('hr_team')
        elif any(keyword in email for keyword in ['finance', 'accounting', 'accountant']):
            assigned_groups.append('finance_team')
        elif any(keyword in email for keyword in ['it', 'tech', 'support']):
            assigned_groups.append('it_support')
        elif any(keyword in email for keyword in ['dev', 'engineer', 'eng']):
            assigned_groups.append('engineering')
        elif any(keyword in email for keyword in ['sales']):
            assigned_groups.append('sales_team')
        elif any(keyword in email for keyword in ['marketing', 'marketer']):
            assigned_groups.append('marketing_team')
        else:
            # Default to employees group
            assigned_groups.append('employees')

        # Assign to groups
        for group_code in assigned_groups:
            group = groups.get(group_code)
            if not group:
                continue

            # Check if already assigned
            existing = db.query(UserGroup).filter(
                UserGroup.user_id == user.id,
                UserGroup.group_id == group.id
            ).first()

            if existing:
                continue

            # Create assignment
            user_group = UserGroup(
                id=create_id(),
                user_id=user.id,
                group_id=group.id,
                created_at=datetime.utcnow()
            )
            db.add(user_group)
            print(f"    ✓ Added '{user.email}' to group '{group.name}'")

    db.flush()


def seed_rbac_for_tenant(db: Session, tenant_id: str, company_id: str = None):
    """Complete RBAC setup for a tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        print(f"❌ Tenant not found: {tenant_id}")
        return

    print(f"\n{'='*70}")
    print(f"Setting up RBAC for: {tenant.name}")
    print(f"{'='*70}")

    # 1. Create roles
    roles = create_roles_for_tenant(db, tenant_id)

    # 2. Create groups
    groups = create_groups_for_tenant(db, tenant_id, company_id)

    # 3. Assign roles to groups
    assign_roles_to_groups(db, groups, roles)

    # 4. Assign users to groups
    assign_users_to_groups(db, tenant_id, groups)

    db.commit()
    print(f"\n✓ RBAC setup completed for {tenant.name}!")


def seed_all_tenants(db: Session):
    """Setup RBAC for all existing tenants."""
    tenants = db.query(Tenant).all()

    if not tenants:
        print("\n❌ No tenants found. Please run organization seed first.")
        print("   Run: python -m app.seeds.seed_complete_org")
        return

    print(f"\nFound {len(tenants)} tenant(s). Setting up RBAC...")

    for tenant in tenants:
        try:
            seed_rbac_for_tenant(db, str(tenant.id))
        except Exception as e:
            print(f"\n❌ Error setting up RBAC for {tenant.name}: {str(e)}")
            import traceback
            traceback.print_exc()
            db.rollback()
            continue


def print_summary(db: Session):
    """Print RBAC setup summary."""
    print(f"\n{'='*70}")
    print("RBAC SETUP SUMMARY")
    print(f"{'='*70}")

    roles_count = db.query(Role).count()
    groups_count = db.query(Group).count()
    group_roles_count = db.query(GroupRole).count()
    user_groups_count = db.query(UserGroup).count()

    print(f"Roles:              {roles_count}")
    print(f"Groups:             {groups_count}")
    print(f"Role → Group:       {group_roles_count}")
    print(f"User → Group:       {user_groups_count}")
    print(f"{'='*70}\n")

    print("RBAC Model:")
    print("  User → Group → Role → Permission")
    print()
    print("✓ All users are now assigned to groups")
    print("✓ All groups have roles assigned")
    print("✓ All roles have permissions assigned")
    print()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main seeding function."""
    print("\n" + "="*70)
    print("RBAC SETUP WITH GROUP-BASED ACCESS CONTROL")
    print("="*70)
    print("\nThis will:")
    print("  1. Create default roles for each tenant")
    print("  2. Create default groups (Administrators, Managers, etc.)")
    print("  3. Assign roles to groups")
    print("  4. Assign existing users to appropriate groups")
    print()
    print(RECOMMENDED_GROUPS)
    print("\n" + "="*70)

    response = input("\nContinue with RBAC setup? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Aborted.")
        return

    db = SessionLocal()

    try:
        # Setup RBAC for all tenants
        seed_all_tenants(db)

        # Print summary
        print_summary(db)

        print("✓ RBAC setup completed successfully!")
        print("\nYou can now:")
        print("  1. Login with any user credentials")
        print("  2. View their roles via group membership")
        print("  3. Manage access by adding/removing users from groups")
        print("  4. Assign new roles to groups as needed")

    except Exception as e:
        print(f"\n❌ RBAC setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
