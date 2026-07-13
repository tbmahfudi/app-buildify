"""
Seed script for creating default system security policy.

This script creates a default system-wide security policy that serves as
the fallback for all tenants that don't have custom policies.

Run this script after migrations to set up baseline security settings.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.security_policy import SecurityPolicy


async def seed_default_security_policy():
    """Create default system security policy"""

    settings = get_settings()

    # Convert sync URL to async
    db_url = settings.SQLALCHEMY_DATABASE_URL
    if db_url.startswith("sqlite"):
        async_db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
    elif db_url.startswith("postgresql"):
        async_db_url = db_url.replace("postgresql://", "postgresql+asyncpg://").replace(
            "postgresql+psycopg2://", "postgresql+asyncpg://"
        )
    elif db_url.startswith("mysql"):
        async_db_url = db_url.replace("mysql://", "mysql+aiomysql://").replace("mysql+pymysql://", "mysql+aiomysql://")
    else:
        async_db_url = db_url

    engine = create_async_engine(async_db_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("🔐 Seeding default system security policy...")

        # Check if system default policy already exists
        query = select(SecurityPolicy).where(SecurityPolicy.tenant_id == None, SecurityPolicy.is_active == True)
        result = await db.execute(query)
        existing = result.scalars().first()

        if existing:
            print(f"  ℹ️  System default security policy already exists: {existing.policy_name}")
            print(f"      Policy ID: {existing.id}")
            return

        # Create default system security policy with sensible defaults
        default_policy = SecurityPolicy(
            tenant_id=None,  # NULL = system default
            policy_name="Default System Security Policy",
            policy_type="combined",
            # Password Policy - Moderate security
            password_min_length=12,
            password_max_length=128,
            password_require_uppercase=True,
            password_require_lowercase=True,
            password_require_digit=True,
            password_require_special_char=True,
            password_min_unique_chars=8,
            password_max_repeating_chars=2,
            password_allow_common=False,  # Don't allow common passwords
            password_allow_username=False,  # Don't allow username in password
            password_history_count=5,  # Remember last 5 passwords
            password_expiration_days=90,  # Expire after 90 days
            password_expiration_warning_days=14,  # Warn 14 days before expiration
            password_grace_logins=3,  # Allow 3 logins after expiration
            # Account Lockout Policy - Protect against brute force
            login_max_attempts=5,  # Lock after 5 failed attempts
            login_lockout_duration_min=30,  # Lock for 30 minutes
            login_lockout_type="progressive",  # Progressive lockout (increases with repeat failures)
            login_reset_attempts_after_min=60,  # Reset counter after 60 minutes of no attempts
            login_notify_user_on_lockout=True,  # Notify user when locked out
            # Session Policy - Balance security and usability
            session_timeout_minutes=60,  # Timeout after 60 minutes of inactivity
            session_absolute_timeout_hours=12,  # Absolute timeout after 12 hours
            session_max_concurrent=3,  # Max 3 concurrent sessions
            session_terminate_on_password_change=True,  # Terminate all sessions on password change
            # Password Reset Policy
            password_reset_token_expire_hours=24,  # Reset token valid for 24 hours
            password_reset_max_attempts=5,  # Max 5 reset attempts
            password_reset_notify_user=True,  # Notify user of password reset
            # Metadata
            is_active=True,
            created_by=None,  # System-generated
            updated_by=None,
        )

        db.add(default_policy)
        await db.commit()
        await db.refresh(default_policy)

        print("\n✅ Default system security policy created successfully!")
        print(f"   Policy ID: {default_policy.id}")
        print(f"   Policy Name: {default_policy.policy_name}")
        print(f"   Policy Type: {default_policy.policy_type}")
        print("\n📋 Policy Summary:")
        print("   Password:")
        print(f"     - Min length: {default_policy.password_min_length} characters")
        print("     - Must include: uppercase, lowercase, digit, special character")
        print(f"     - Expires after: {default_policy.password_expiration_days} days")
        print(f"     - History: Remembers last {default_policy.password_history_count} passwords")
        print("\n   Account Lockout:")
        print(f"     - Max attempts: {default_policy.login_max_attempts}")
        print(f"     - Lockout duration: {default_policy.login_lockout_duration_min} minutes")
        print(f"     - Lockout type: {default_policy.login_lockout_type}")
        print("\n   Session:")
        print(f"     - Idle timeout: {default_policy.session_timeout_minutes} minutes")
        print(f"     - Absolute timeout: {default_policy.session_absolute_timeout_hours} hours")
        print(f"     - Max concurrent: {default_policy.session_max_concurrent} sessions")
        print("\n   Password Reset:")
        print(f"     - Token expiration: {default_policy.password_reset_token_expire_hours} hours")
        print(f"     - Max attempts: {default_policy.password_reset_max_attempts}")
        print("\n💡 This policy will be used as the default for all tenants.")
        print("   Tenants can override these settings by creating tenant-specific policies.")


def seed_default_security_policy_sync():
    """Synchronous variant of the above.

    The async version needs asyncpg, which isn't installed in the standard
    (psycopg2/sync) image, so seeders that run under a sync engine call this.
    Idempotent: no-op if a system-default policy already exists.
    """
    from app.core.db import SessionLocal

    db = SessionLocal()
    try:
        existing = (
            db.query(SecurityPolicy)
            .filter(
                SecurityPolicy.tenant_id.is_(None),
                SecurityPolicy.is_active == True,
            )
            .first()
        )
        if existing:
            print(f"  ℹ️  System default security policy already exists: {existing.policy_name}")
            return
        db.add(
            SecurityPolicy(
                tenant_id=None,
                policy_name="Default System Security Policy",
                policy_type="combined",
                password_min_length=12,
                password_max_length=128,
                password_require_uppercase=True,
                password_require_lowercase=True,
                password_require_digit=True,
                password_require_special_char=True,
                password_min_unique_chars=8,
                password_max_repeating_chars=2,
                password_allow_common=False,
                password_allow_username=False,
                password_history_count=5,
                password_expiration_days=90,
                password_expiration_warning_days=14,
                password_grace_logins=3,
                login_max_attempts=5,
                login_lockout_duration_min=30,
                login_lockout_type="progressive",
                login_reset_attempts_after_min=60,
                login_notify_user_on_lockout=True,
                session_timeout_minutes=60,
                session_absolute_timeout_hours=12,
                session_max_concurrent=3,
                session_terminate_on_password_change=True,
                password_reset_token_expire_hours=24,
                password_reset_max_attempts=5,
                password_reset_notify_user=True,
                is_active=True,
                created_by=None,
                updated_by=None,
            )
        )
        db.commit()
        print("  ✓ Seeded system-default security policy")
    except Exception as exc:  # pragma: no cover - defensive
        db.rollback()
        print(f"  ⚠ default security policy seed failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(seed_default_security_policy())
