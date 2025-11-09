"""
Financial Module RBAC Seed Data
================================
Sets up roles, permissions, and user assignments for the Financial module
specifically for FashionHub Retail Ltd. company.

This demonstrates a complete RBAC setup for a business module.

Run: python -m backend.app.seeds.seed_financial_rbac
"""

import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.models.company import Company
from app.models.role import Role
from app.models.permission import Permission
from app.models.rbac_junctions import RolePermission, GroupRole, UserGroup
from app.models.group import Group
from app.models.module_registry import ModuleRegistry, TenantModule


def seed_financial_rbac():
    """
    Seed RBAC configuration for Financial module on FashionHub company.

    Creates:
    - Financial module permissions (if not exist)
    - Financial module roles
    - User role assignments based on job functions
    """
    db = SessionLocal()

    try:
        print("\n" + "="*80)
        print("FINANCIAL MODULE RBAC SETUP FOR FASHIONHUB")
        print("="*80 + "\n")

        # ========================================================================
        # STEP 1: Get FashionHub Tenant and Company
        # ========================================================================
        print("📊 Step 1: Loading FashionHub organization...")

        tenant = db.query(Tenant).filter(Tenant.code == "FASHIONHUB").first()
        if not tenant:
            print("❌ ERROR: FashionHub tenant not found!")
            print("   Please run seed_complete_org.py first")
            return

        company = db.query(Company).filter(
            Company.code == "FASHIONHUB",
            Company.tenant_id == tenant.id
        ).first()
        if not company:
            print("❌ ERROR: FashionHub company not found!")
            return

        print(f"✓ Found tenant: {tenant.name} (ID: {tenant.id})")
        print(f"✓ Found company: {company.name} (ID: {company.id})")

        # ========================================================================
        # STEP 2: Register Financial Module Permissions
        # ========================================================================
        print("\n📋 Step 2: Registering Financial module permissions...")

        financial_permissions = [
            # Accounts
            {
                "code": "financial:accounts:read:company",
                "name": "View Accounts",
                "description": "View chart of accounts",
                "category": "financial"
            },
            {
                "code": "financial:accounts:create:company",
                "name": "Create Accounts",
                "description": "Create new accounts in chart of accounts",
                "category": "financial"
            },
            {
                "code": "financial:accounts:update:company",
                "name": "Update Accounts",
                "description": "Update existing accounts",
                "category": "financial"
            },
            {
                "code": "financial:accounts:delete:company",
                "name": "Delete Accounts",
                "description": "Delete accounts from chart of accounts",
                "category": "financial"
            },
            # Transactions
            {
                "code": "financial:transactions:read:company",
                "name": "View Transactions",
                "description": "View financial transactions",
                "category": "financial"
            },
            {
                "code": "financial:transactions:create:company",
                "name": "Create Transactions",
                "description": "Create financial transactions",
                "category": "financial"
            },
            {
                "code": "financial:transactions:update:company",
                "name": "Update Transactions",
                "description": "Update financial transactions",
                "category": "financial"
            },
            {
                "code": "financial:transactions:delete:company",
                "name": "Delete Transactions",
                "description": "Delete financial transactions",
                "category": "financial"
            },
            {
                "code": "financial:transactions:post:company",
                "name": "Post Transactions",
                "description": "Post transactions to the ledger",
                "category": "financial"
            },
            # Invoices
            {
                "code": "financial:invoices:read:company",
                "name": "View Invoices",
                "description": "View invoices",
                "category": "financial"
            },
            {
                "code": "financial:invoices:create:company",
                "name": "Create Invoices",
                "description": "Create and manage invoices",
                "category": "financial"
            },
            {
                "code": "financial:invoices:update:company",
                "name": "Update Invoices",
                "description": "Update invoice details",
                "category": "financial"
            },
            {
                "code": "financial:invoices:delete:company",
                "name": "Delete Invoices",
                "description": "Delete invoices",
                "category": "financial"
            },
            {
                "code": "financial:invoices:send:company",
                "name": "Send Invoices",
                "description": "Send invoices to customers",
                "category": "financial"
            },
            # Payments
            {
                "code": "financial:payments:read:company",
                "name": "View Payments",
                "description": "View payment records",
                "category": "financial"
            },
            {
                "code": "financial:payments:create:company",
                "name": "Create Payments",
                "description": "Record payments",
                "category": "financial"
            },
            {
                "code": "financial:payments:update:company",
                "name": "Update Payments",
                "description": "Update payment records",
                "category": "financial"
            },
            {
                "code": "financial:payments:delete:company",
                "name": "Delete Payments",
                "description": "Delete payment records",
                "category": "financial"
            },
            # Reports
            {
                "code": "financial:reports:read:company",
                "name": "View Reports",
                "description": "View financial reports",
                "category": "financial"
            },
            {
                "code": "financial:reports:export:company",
                "name": "Export Reports",
                "description": "Export financial reports",
                "category": "financial"
            }
        ]

        permission_map = {}
        for perm_data in financial_permissions:
            perm = db.query(Permission).filter(
                Permission.code == perm_data["code"]
            ).first()

            if not perm:
                # Parse permission code: format is "financial:resource:action:scope"
                # Example: "financial:accounts:read:company" -> resource="accounts", action="read", scope="company"
                parts = perm_data["code"].split(":")
                if len(parts) == 4:
                    _, resource, action, scope = parts
                elif len(parts) == 3:
                    resource, action, scope = parts
                else:
                    raise ValueError(f"Invalid permission code format: {perm_data['code']}")

                perm = Permission(
                    code=perm_data["code"],
                    name=perm_data["name"],
                    description=perm_data["description"],
                    resource=resource,
                    action=action,
                    scope=scope,
                    category=perm_data["category"],
                    is_system=False
                )
                db.add(perm)
                db.flush()
                print(f"  ✓ Created permission: {perm_data['code']}")
            else:
                print(f"  • Permission exists: {perm_data['code']}")

            permission_map[perm_data["code"]] = perm

        db.commit()
        print(f"✓ Registered {len(financial_permissions)} permissions")

        # ========================================================================
        # STEP 3: Create Financial Roles for FashionHub
        # ========================================================================
        print("\n👥 Step 3: Creating Financial roles for FashionHub...")

        roles_config = {
            "Financial Manager": {
                "code": "FIN_MANAGER",
                "description": "Full access to all financial functions - for CFO and Finance Director",
                "permissions": [
                    "financial:accounts:read:company",
                    "financial:accounts:create:company",
                    "financial:accounts:update:company",
                    "financial:accounts:delete:company",
                    "financial:transactions:read:company",
                    "financial:transactions:create:company",
                    "financial:transactions:update:company",
                    "financial:transactions:delete:company",
                    "financial:transactions:post:company",
                    "financial:invoices:read:company",
                    "financial:invoices:create:company",
                    "financial:invoices:update:company",
                    "financial:invoices:delete:company",
                    "financial:invoices:send:company",
                    "financial:payments:read:company",
                    "financial:payments:create:company",
                    "financial:payments:update:company",
                    "financial:payments:delete:company",
                    "financial:reports:read:company",
                    "financial:reports:export:company"
                ]
            },
            "Accountant": {
                "code": "ACCOUNTANT",
                "description": "Manage accounts and transactions, view reports",
                "permissions": [
                    "financial:accounts:read:company",
                    "financial:accounts:update:company",
                    "financial:transactions:read:company",
                    "financial:transactions:create:company",
                    "financial:transactions:update:company",
                    "financial:transactions:post:company",
                    "financial:invoices:read:company",
                    "financial:payments:read:company",
                    "financial:reports:read:company"
                ]
            },
            "Billing Clerk": {
                "code": "BILLING_CLERK",
                "description": "Manage invoices and payments",
                "permissions": [
                    "financial:invoices:read:company",
                    "financial:invoices:create:company",
                    "financial:invoices:update:company",
                    "financial:invoices:send:company",
                    "financial:payments:read:company",
                    "financial:payments:create:company",
                    "financial:payments:update:company"
                ]
            },
            "Financial Viewer": {
                "code": "FIN_VIEWER",
                "description": "Read-only access to financial data",
                "permissions": [
                    "financial:accounts:read:company",
                    "financial:transactions:read:company",
                    "financial:invoices:read:company",
                    "financial:payments:read:company",
                    "financial:reports:read:company"
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

            # Commit after each role to avoid bulk insert issues with UUIDs
            db.commit()
            role_map[role_name] = role

        print(f"✓ Created {len(roles_config)} roles with permissions")

        # ========================================================================
        # STEP 4: Create Groups and Assign Roles to Groups
        # ========================================================================
        print("\n👥 Step 4: Creating Financial groups and assigning roles...")

        groups_config = {
            "Financial Managers": {
                "code": "FIN_MANAGERS",
                "description": "Finance executives with full financial access",
                "roles": ["Financial Manager"],
                "group_type": "team"
            },
            "Accountants": {
                "code": "ACCOUNTANTS",
                "description": "Accounting team members",
                "roles": ["Accountant"],
                "group_type": "team"
            },
            "Billing Clerks": {
                "code": "BILLING_CLERKS",
                "description": "Billing and invoicing staff",
                "roles": ["Billing Clerk"],
                "group_type": "team"
            },
            "Financial Viewers": {
                "code": "FIN_VIEWERS",
                "description": "Users with read-only financial access",
                "roles": ["Financial Viewer"],
                "group_type": "team"
            }
        }

        group_map = {}
        for group_name, group_config in groups_config.items():
            # Check if group exists
            group = db.query(Group).filter(
                Group.code == group_config["code"],
                Group.tenant_id == tenant.id,
                Group.company_id == company.id
            ).first()

            if not group:
                group = Group(
                    code=group_config["code"],
                    name=group_name,
                    description=group_config["description"],
                    tenant_id=tenant.id,
                    company_id=company.id,
                    group_type=group_config["group_type"],
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.add(group)
                db.flush()
                print(f"  ✓ Created group: {group_name}")
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
                    else:
                        print(f"    • Role '{role_name}' already assigned to group '{group_name}'")

            db.commit()
            group_map[group_name] = group

        print(f"✓ Created {len(groups_config)} groups with role assignments")

        # ========================================================================
        # STEP 5: Assign Users to Groups
        # ========================================================================
        print("\n🔐 Step 5: Assigning FashionHub users to groups...")

        user_assignments = [
            {
                "email": "cfo@fashionhub.com",
                "groups": ["Financial Managers"],
                "title": "CFO (Chief Financial Officer)"
            },
            {
                "email": "accountant1@fashionhub.com",
                "groups": ["Accountants"],
                "title": "Senior Accountant",
                "create_if_missing": True,
                "dept": "FIN",
                "branch": "CORP"
            },
            {
                "email": "accountant2@fashionhub.com",
                "groups": ["Accountants"],
                "title": "Staff Accountant",
                "create_if_missing": True,
                "dept": "FIN",
                "branch": "CORP"
            },
            {
                "email": "billing@fashionhub.com",
                "groups": ["Billing Clerks"],
                "title": "Billing Specialist",
                "create_if_missing": True,
                "dept": "FIN",
                "branch": "CORP"
            },
            {
                "email": "ar@fashionhub.com",
                "groups": ["Billing Clerks"],
                "title": "Accounts Receivable Clerk",
                "create_if_missing": True,
                "dept": "FIN",
                "branch": "CORP"
            },
            {
                "email": "ceo@fashionhub.com",
                "groups": ["Financial Viewers"],
                "title": "CEO (Read-only financial access)"
            },
            {
                "email": "manager.nyc1@fashionhub.com",
                "groups": ["Financial Viewers"],
                "title": "Store Manager (View financial reports)"
            }
        ]

        from app.core.auth import hash_password
        from app.models.department import Department
        from app.models.branch import Branch

        for assignment in user_assignments:
            user = db.query(User).filter(
                User.email == assignment["email"],
                User.tenant_id == tenant.id
            ).first()

            # Create user if doesn't exist and create_if_missing is True
            if not user and assignment.get("create_if_missing"):
                # Get department and branch
                dept = None
                branch = None

                if assignment.get("dept"):
                    dept = db.query(Department).filter(
                        Department.code == assignment["dept"],
                        Department.company_id == company.id
                    ).first()

                if assignment.get("branch"):
                    branch = db.query(Branch).filter(
                        Branch.code == assignment["branch"],
                        Branch.company_id == company.id
                    ).first()

                user = User(
                    email=assignment["email"],
                    hashed_password=hash_password("password123"),  # Default password
                    full_name=assignment["title"],
                    tenant_id=tenant.id,
                    default_company_id=company.id,
                    department_id=dept.id if dept else None,
                    branch_id=branch.id if branch else None,
                    is_active=True,
                    is_superuser=False,
                    is_verified=True,
                    created_at=datetime.utcnow()
                )
                db.add(user)
                db.flush()
                print(f"  ✓ Created user: {assignment['email']}")

            if not user:
                print(f"  ⚠ User not found: {assignment['email']}")
                continue

            # Assign user to groups
            for group_name in assignment["groups"]:
                group = group_map.get(group_name)
                if group:
                    # Check if user already in group
                    existing = db.query(UserGroup).filter(
                        UserGroup.user_id == user.id,
                        UserGroup.group_id == group.id
                    ).first()

                    if not existing:
                        user_group = UserGroup(
                            id=str(uuid.uuid4()),
                            user_id=str(user.id),
                            group_id=str(group.id),
                            created_at=datetime.utcnow()
                        )
                        db.add(user_group)
                        print(f"  ✓ Added {user.email} to group '{group_name}'")
                    else:
                        print(f"  • User {user.email} already in group '{group_name}'")

        db.commit()
        print(f"✓ User group assignments completed")

        # ========================================================================
        # STEP 6: Enable Financial Module for FashionHub Tenant
        # ========================================================================
        print("\n🔌 Step 6: Enabling Financial module for FashionHub tenant...")

        # Check if Financial module is registered
        module = db.query(ModuleRegistry).filter(
            ModuleRegistry.name == "financial"
        ).first()

        if not module:
            print("  ⚠ Financial module not registered in module_registry")
            print("     The module will be auto-discovered on next server startup")
        else:
            # Check if already enabled for tenant
            tenant_module = db.query(TenantModule).filter(
                TenantModule.tenant_id == tenant.id,
                TenantModule.module_id == module.id
            ).first()

            if not tenant_module:
                tenant_module = TenantModule(
                    tenant_id=tenant.id,
                    module_id=module.id,
                    is_enabled=True,
                    is_configured=True,
                    configuration={
                        "default_currency": "USD",
                        "fiscal_year_start": "01-01",
                        "enable_multi_currency": False,
                        "tax_rate": 8.875,  # NYC sales tax
                        "invoice_prefix": "FH"
                    },
                    enabled_at=datetime.utcnow()
                )
                db.add(tenant_module)
                db.commit()
                print("  ✓ Financial module enabled for FashionHub")
            else:
                if not tenant_module.is_enabled:
                    tenant_module.is_enabled = True
                    tenant_module.enabled_at = datetime.utcnow()
                    db.commit()
                    print("  ✓ Financial module re-enabled for FashionHub")
                else:
                    print("  • Financial module already enabled for FashionHub")

        # ========================================================================
        # SUMMARY
        # ========================================================================
        print("\n" + "="*80)
        print("✅ FINANCIAL RBAC SETUP COMPLETE!")
        print("="*80)
        print(f"\n📊 Company: {company.name}")
        print(f"🏢 Tenant: {tenant.name}")
        print(f"\n👥 Roles Created:")
        for role_name in roles_config.keys():
            print(f"   • {role_name}")

        print(f"\n🏢 Groups Created:")
        for group_name in groups_config.keys():
            print(f"   • {group_name}")

        print(f"\n🔐 User Access Configured (via Groups):")
        for assignment in user_assignments:
            groups_str = ", ".join(assignment["groups"])
            print(f"   • {assignment['email']:<30} → {groups_str}")

        print(f"\n📋 Permissions Registered: {len(financial_permissions)}")
        print(f"\n🎯 Next Steps:")
        print(f"   1. Restart the backend server")
        print(f"   2. Login as CFO: cfo@fashionhub.com / password123")
        print(f"   3. Navigate to Financial module")
        print(f"   4. Test different user permissions")

        print("\n" + "="*80 + "\n")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("\n🚀 Starting Financial Module RBAC Setup...")
    seed_financial_rbac()
    print("✅ Done!\n")
