"""
Application startup tasks
"""
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.security_policy import SecurityPolicy


def ensure_default_security_policy(db: Session) -> None:
    """
    Ensure a default system security policy exists.
    This runs on application startup to guarantee baseline security settings.

    If no system default policy exists (tenant_id = NULL), creates one.
    """
    try:
        # Check if system default policy exists
        query = select(SecurityPolicy).where(
            SecurityPolicy.tenant_id == None,
            SecurityPolicy.is_active == True
        )
        result = db.execute(query)
        existing = result.scalars().first()

        if existing:
            # Policy already exists, no action needed
            return

        # Create default system security policy
        default_policy = SecurityPolicy(
            id=str(uuid.uuid4()),
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
            password_allow_common=False,
            password_allow_username=False,
            password_history_count=5,
            password_expiration_days=90,
            password_expiration_warning_days=14,
            password_grace_logins=3,

            # Account Lockout Policy
            login_max_attempts=5,
            login_lockout_duration_min=30,
            login_lockout_type="progressive",
            login_reset_attempts_after_min=60,
            login_notify_user_on_lockout=True,

            # Session Policy
            session_timeout_minutes=60,
            session_absolute_timeout_hours=12,
            session_max_concurrent=3,
            session_terminate_on_password_change=True,

            # Password Reset Policy
            password_reset_token_expire_hours=24,
            password_reset_max_attempts=5,
            password_reset_notify_user=True,

            # Metadata
            is_active=True,
            created_by=None,
            updated_by=None
        )

        db.add(default_policy)
        db.commit()

        print("✅ Created default system security policy")

    except Exception as e:
        print(f"⚠️  Warning: Could not ensure default security policy exists: {e}")
        db.rollback()
