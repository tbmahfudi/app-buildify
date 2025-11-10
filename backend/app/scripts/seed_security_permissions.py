"""
Seed script for security management permissions and roles.

Run this script to create permissions and roles for the security policy system.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import get_settings
from app.models import Permission, Role, RolePermission


async def seed_security_permissions():
    """Create security management permissions and roles"""

    settings = get_settings()

    # Convert sync URL to async
    db_url = settings.SQLALCHEMY_DATABASE_URL
    if db_url.startswith("sqlite"):
        async_db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
    elif db_url.startswith("postgresql"):
        async_db_url = db_url.replace("postgresql://", "postgresql+asyncpg://").replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    elif db_url.startswith("mysql"):
        async_db_url = db_url.replace("mysql://", "mysql+aiomysql://").replace("mysql+pymysql://", "mysql+aiomysql://")
    else:
        async_db_url = db_url

    engine = create_async_engine(async_db_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("🔐 Seeding security management permissions and roles...")

        # Define security permissions
        security_permissions = [
            # Security Policy Management
            {
                "code": "security_policy:read:all",
                "name": "View Security Policies",
                "description": "View system and tenant security policies",
                "resource": "security_policy",
                "action": "read",
                "scope": "all"
            },
            {
                "code": "security_policy:write:all",
                "name": "Manage Security Policies",
                "description": "Create and update security policies",
                "resource": "security_policy",
                "action": "write",
                "scope": "all"
            },
            {
                "code": "security_policy:delete:all",
                "name": "Delete Security Policies",
                "description": "Delete tenant security policies",
                "resource": "security_policy",
                "action": "delete",
                "scope": "all"
            },

            # Account Lockout Management
            {
                "code": "security:view_locked_accounts:all",
                "name": "View Locked Accounts",
                "description": "View list of locked user accounts",
                "resource": "security",
                "action": "view_locked_accounts",
                "scope": "all"
            },
            {
                "code": "security:unlock_account:all",
                "name": "Unlock Accounts",
                "description": "Manually unlock locked user accounts",
                "resource": "security",
                "action": "unlock_account",
                "scope": "all"
            },

            # Session Management
            {
                "code": "security:view_sessions:all",
                "name": "View Active Sessions",
                "description": "View all active user sessions",
                "resource": "security",
                "action": "view_sessions",
                "scope": "all"
            },
            {
                "code": "security:revoke_session:all",
                "name": "Revoke Sessions",
                "description": "Revoke user sessions",
                "resource": "security",
                "action": "revoke_session",
                "scope": "all"
            },

            # Login Attempt Audit
            {
                "code": "security:view_login_attempts:all",
                "name": "View Login Attempts",
                "description": "View login attempt audit logs",
                "resource": "security",
                "action": "view_login_attempts",
                "scope": "all"
            },

            # Notification Configuration
            {
                "code": "notification_config:read:all",
                "name": "View Notification Config",
                "description": "View notification configuration",
                "resource": "notification_config",
                "action": "read",
                "scope": "all"
            },
            {
                "code": "notification_config:write:all",
                "name": "Manage Notification Config",
                "description": "Update notification configuration",
                "resource": "notification_config",
                "action": "write",
                "scope": "all"
            },

            # Notification Queue (for monitoring)
            {
                "code": "notification_queue:read:all",
                "name": "View Notification Queue",
                "description": "View pending and sent notifications",
                "resource": "notification_queue",
                "action": "read",
                "scope": "all"
            },
        ]

        # Create permissions
        created_permissions = []
        for perm_data in security_permissions:
            # Check if permission already exists
            query = select(Permission).where(Permission.code == perm_data["code"])
            result = await db.execute(query)
            existing = result.scalars().first()

            if existing:
                print(f"  ℹ️  Permission already exists: {perm_data['code']}")
                created_permissions.append(existing)
            else:
                permission = Permission(**perm_data, is_active=True)
                db.add(permission)
                await db.flush()
                print(f"  ✅ Created permission: {perm_data['code']}")
                created_permissions.append(permission)

        await db.commit()

        # Define security roles
        security_roles = [
            {
                "code": "security_admin",
                "name": "Security Administrator",
                "description": "Full access to security policy management, account lockouts, sessions, and notifications",
                "permissions": [
                    "security_policy:read:all",
                    "security_policy:write:all",
                    "security_policy:delete:all",
                    "security:view_locked_accounts:all",
                    "security:unlock_account:all",
                    "security:view_sessions:all",
                    "security:revoke_session:all",
                    "security:view_login_attempts:all",
                    "notification_config:read:all",
                    "notification_config:write:all",
                    "notification_queue:read:all",
                ]
            },
            {
                "code": "security_viewer",
                "name": "Security Viewer",
                "description": "Read-only access to security features for monitoring and audit",
                "permissions": [
                    "security_policy:read:all",
                    "security:view_locked_accounts:all",
                    "security:view_sessions:all",
                    "security:view_login_attempts:all",
                    "notification_config:read:all",
                    "notification_queue:read:all",
                ]
            },
            {
                "code": "support_admin",
                "name": "Support Administrator",
                "description": "Can unlock accounts and manage sessions for user support",
                "permissions": [
                    "security:view_locked_accounts:all",
                    "security:unlock_account:all",
                    "security:view_sessions:all",
                    "security:revoke_session:all",
                    "security:view_login_attempts:all",
                ]
            }
        ]

        # Create roles and assign permissions
        for role_data in security_roles:
            # Check if role already exists
            query = select(Role).where(Role.code == role_data["code"])
            result = await db.execute(query)
            existing_role = result.scalars().first()

            if existing_role:
                print(f"  ℹ️  Role already exists: {role_data['code']}")
                role = existing_role
            else:
                role = Role(
                    code=role_data["code"],
                    name=role_data["name"],
                    description=role_data["description"],
                    is_active=True
                )
                db.add(role)
                await db.flush()
                print(f"  ✅ Created role: {role_data['code']}")

            # Assign permissions to role
            for perm_code in role_data["permissions"]:
                # Find permission
                perm = next((p for p in created_permissions if p.code == perm_code), None)
                if not perm:
                    print(f"  ⚠️  Permission not found: {perm_code}")
                    continue

                # Check if role-permission already exists
                query = select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == perm.id
                )
                result = await db.execute(query)
                existing_rp = result.scalars().first()

                if not existing_rp:
                    role_permission = RolePermission(
                        role_id=role.id,
                        permission_id=perm.id
                    )
                    db.add(role_permission)
                    print(f"    ➕ Assigned permission: {perm_code} to {role.code}")

        await db.commit()

        print("\n✅ Security permissions and roles seeded successfully!")
        print("\n📋 Created Roles:")
        print("  - security_admin: Full security management access")
        print("  - security_viewer: Read-only security monitoring")
        print("  - support_admin: Account unlock and session management")
        print("\n💡 Assign these roles to users who should manage security policies.")


if __name__ == "__main__":
    asyncio.run(seed_security_permissions())
