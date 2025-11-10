"""
Security Configuration System

Provides configurable security policies with:
- Environment variable defaults
- Database-level overrides (tenant-specific)
- Hierarchical fallback (tenant -> system default -> env vars -> code defaults)
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from functools import lru_cache
import os


class PasswordPolicyConfig(BaseModel):
    """Password strength and lifecycle policies"""

    # Strength requirements
    min_length: int = Field(default=12, ge=8, le=128)
    max_length: int = Field(default=128, ge=8, le=256)
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special_char: bool = True
    min_unique_chars: int = Field(default=4, ge=0)
    max_repeating_chars: int = Field(default=3, ge=0)

    # Pattern restrictions
    allow_common: bool = False  # Allow common passwords (discouraged)
    allow_username: bool = False  # Allow password to contain username/email

    # History and rotation
    history_count: int = Field(default=5, ge=0)  # Remember last N passwords
    expiration_days: int = Field(default=90, ge=0)  # 0 = never expires
    expiration_warning_days: int = Field(default=14, ge=0)
    grace_logins: int = Field(default=3, ge=0)  # Logins allowed after expiration


class AccountLockoutConfig(BaseModel):
    """Account lockout policies for failed login attempts"""

    max_attempts: int = Field(default=5, ge=1)
    lockout_duration_min: int = Field(default=15, ge=1)
    lockout_type: str = Field(default="progressive")  # 'fixed' or 'progressive'
    reset_attempts_after_min: int = Field(default=60, ge=1)
    notify_user_on_lockout: bool = True

    # Progressive lockout durations (in minutes)
    progressive_durations: Dict[int, int] = {
        3: 5,    # 3 attempts: 5 min lockout
        5: 15,   # 5 attempts: 15 min lockout
        7: 60,   # 7 attempts: 60 min lockout
        10: 1440  # 10+ attempts: 24 hour lockout
    }


class SessionSecurityConfig(BaseModel):
    """Session management and timeout policies"""

    timeout_minutes: int = Field(default=30, ge=1)  # Idle timeout (matches access token expiration)
    absolute_timeout_hours: int = Field(default=8, ge=1)  # Max session duration
    max_concurrent: int = Field(default=3, ge=0)  # 0 = unlimited
    terminate_on_password_change: bool = True

    # Advanced session features
    require_reauth_for_sensitive: bool = True  # Require password re-entry for sensitive ops
    reauth_timeout_minutes: int = Field(default=15, ge=1)


class PasswordResetConfig(BaseModel):
    """Password reset policies"""

    token_expire_hours: int = Field(default=1, ge=1)
    max_attempts_per_hour: int = Field(default=3, ge=1)
    require_current_password: bool = True  # For password change (not forgot password)
    notify_user: bool = True


class SecurityConfig(BaseModel):
    """Master security configuration combining all policies"""

    password: PasswordPolicyConfig = Field(default_factory=PasswordPolicyConfig)
    lockout: AccountLockoutConfig = Field(default_factory=AccountLockoutConfig)
    session: SessionSecurityConfig = Field(default_factory=SessionSecurityConfig)
    reset: PasswordResetConfig = Field(default_factory=PasswordResetConfig)

    class Config:
        frozen = False  # Allow updates from database


def load_from_env() -> SecurityConfig:
    """
    Load security configuration from environment variables.
    Falls back to default values if not set.
    """
    password_config = PasswordPolicyConfig(
        min_length=int(os.getenv("PASSWORD_MIN_LENGTH", "12")),
        max_length=int(os.getenv("PASSWORD_MAX_LENGTH", "128")),
        require_uppercase=os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true",
        require_lowercase=os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true",
        require_digit=os.getenv("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true",
        require_special_char=os.getenv("PASSWORD_REQUIRE_SPECIAL_CHAR", "true").lower() == "true",
        min_unique_chars=int(os.getenv("PASSWORD_MIN_UNIQUE_CHARS", "4")),
        max_repeating_chars=int(os.getenv("PASSWORD_MAX_REPEATING_CHARS", "3")),
        allow_common=os.getenv("PASSWORD_ALLOW_COMMON", "false").lower() == "true",
        allow_username=os.getenv("PASSWORD_ALLOW_USERNAME", "false").lower() == "true",
        history_count=int(os.getenv("PASSWORD_HISTORY_COUNT", "5")),
        expiration_days=int(os.getenv("PASSWORD_EXPIRATION_DAYS", "90")),
        expiration_warning_days=int(os.getenv("PASSWORD_EXPIRATION_WARNING_DAYS", "14")),
        grace_logins=int(os.getenv("PASSWORD_GRACE_LOGINS", "3")),
    )

    lockout_config = AccountLockoutConfig(
        max_attempts=int(os.getenv("LOGIN_MAX_ATTEMPTS", "5")),
        lockout_duration_min=int(os.getenv("LOGIN_LOCKOUT_DURATION_MIN", "15")),
        lockout_type=os.getenv("LOGIN_LOCKOUT_TYPE", "progressive"),
        reset_attempts_after_min=int(os.getenv("LOGIN_RESET_ATTEMPTS_AFTER_MIN", "60")),
        notify_user_on_lockout=os.getenv("LOGIN_NOTIFY_USER_ON_LOCKOUT", "true").lower() == "true",
    )

    session_config = SessionSecurityConfig(
        timeout_minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", "30")),
        absolute_timeout_hours=int(os.getenv("SESSION_ABSOLUTE_TIMEOUT_HOURS", "8")),
        max_concurrent=int(os.getenv("SESSION_MAX_CONCURRENT", "3")),
        terminate_on_password_change=os.getenv("SESSION_TERMINATE_ON_PASSWORD_CHANGE", "true").lower() == "true",
        require_reauth_for_sensitive=os.getenv("SESSION_REQUIRE_REAUTH_FOR_SENSITIVE", "true").lower() == "true",
        reauth_timeout_minutes=int(os.getenv("SESSION_REAUTH_TIMEOUT_MINUTES", "15")),
    )

    reset_config = PasswordResetConfig(
        token_expire_hours=int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_HOURS", "1")),
        max_attempts_per_hour=int(os.getenv("PASSWORD_RESET_MAX_ATTEMPTS", "3")),
        require_current_password=os.getenv("PASSWORD_RESET_REQUIRE_CURRENT", "true").lower() == "true",
        notify_user=os.getenv("PASSWORD_RESET_NOTIFY_USER", "true").lower() == "true",
    )

    return SecurityConfig(
        password=password_config,
        lockout=lockout_config,
        session=session_config,
        reset=reset_config
    )


def load_from_db(security_policy_dict: Dict[str, Any]) -> SecurityConfig:
    """
    Load security configuration from database SecurityPolicy model.
    Merges with environment defaults for any missing values.
    """
    env_config = load_from_env()

    # Build password config from database, falling back to env config
    password_config = PasswordPolicyConfig(
        min_length=security_policy_dict.get("password_min_length", env_config.password.min_length),
        max_length=security_policy_dict.get("password_max_length", env_config.password.max_length),
        require_uppercase=security_policy_dict.get("password_require_uppercase", env_config.password.require_uppercase),
        require_lowercase=security_policy_dict.get("password_require_lowercase", env_config.password.require_lowercase),
        require_digit=security_policy_dict.get("password_require_digit", env_config.password.require_digit),
        require_special_char=security_policy_dict.get("password_require_special_char", env_config.password.require_special_char),
        min_unique_chars=security_policy_dict.get("password_min_unique_chars", env_config.password.min_unique_chars),
        max_repeating_chars=security_policy_dict.get("password_max_repeating_chars", env_config.password.max_repeating_chars),
        allow_common=security_policy_dict.get("password_allow_common", env_config.password.allow_common),
        allow_username=security_policy_dict.get("password_allow_username", env_config.password.allow_username),
        history_count=security_policy_dict.get("password_history_count", env_config.password.history_count),
        expiration_days=security_policy_dict.get("password_expiration_days", env_config.password.expiration_days),
        expiration_warning_days=security_policy_dict.get("password_expiration_warning_days", env_config.password.expiration_warning_days),
        grace_logins=security_policy_dict.get("password_grace_logins", env_config.password.grace_logins),
    )

    lockout_config = AccountLockoutConfig(
        max_attempts=security_policy_dict.get("login_max_attempts", env_config.lockout.max_attempts),
        lockout_duration_min=security_policy_dict.get("login_lockout_duration_min", env_config.lockout.lockout_duration_min),
        lockout_type=security_policy_dict.get("login_lockout_type", env_config.lockout.lockout_type),
        reset_attempts_after_min=security_policy_dict.get("login_reset_attempts_after_min", env_config.lockout.reset_attempts_after_min),
        notify_user_on_lockout=security_policy_dict.get("login_notify_user_on_lockout", env_config.lockout.notify_user_on_lockout),
    )

    session_config = SessionSecurityConfig(
        timeout_minutes=security_policy_dict.get("session_timeout_minutes", env_config.session.timeout_minutes),
        absolute_timeout_hours=security_policy_dict.get("session_absolute_timeout_hours", env_config.session.absolute_timeout_hours),
        max_concurrent=security_policy_dict.get("session_max_concurrent", env_config.session.max_concurrent),
        terminate_on_password_change=security_policy_dict.get("session_terminate_on_password_change", env_config.session.terminate_on_password_change),
    )

    reset_config = PasswordResetConfig(
        token_expire_hours=security_policy_dict.get("password_reset_token_expire_hours", env_config.reset.token_expire_hours),
        max_attempts_per_hour=security_policy_dict.get("password_reset_max_attempts", env_config.reset.max_attempts_per_hour),
        notify_user=security_policy_dict.get("password_reset_notify_user", env_config.reset.notify_user),
    )

    return SecurityConfig(
        password=password_config,
        lockout=lockout_config,
        session=session_config,
        reset=reset_config
    )


@lru_cache()
def get_default_security_config() -> SecurityConfig:
    """
    Get cached default security configuration from environment variables.
    This is used when no tenant-specific policy exists.
    """
    return load_from_env()


async def get_security_config(db, tenant_id: Optional[str] = None) -> SecurityConfig:
    """
    Get security configuration for a tenant with hierarchical fallback:
    1. Tenant-specific policy (from database)
    2. System default policy (from database, tenant_id=NULL)
    3. Environment variables (from .env)
    4. Code defaults (hardcoded in Pydantic models)

    Args:
        db: Database session
        tenant_id: Optional tenant ID. If None, returns system default.

    Returns:
        SecurityConfig instance
    """
    from sqlalchemy import select
    from app.models import SecurityPolicy

    # Try tenant-specific policy first
    if tenant_id:
        query = select(SecurityPolicy).where(
            SecurityPolicy.tenant_id == tenant_id,
            SecurityPolicy.is_active == True
        )
        result = await db.execute(query)
        tenant_policy = result.scalars().first()

        if tenant_policy:
            return load_from_db(tenant_policy.to_dict())

    # Try system default policy (tenant_id = NULL)
    query = select(SecurityPolicy).where(
        SecurityPolicy.tenant_id == None,
        SecurityPolicy.is_active == True
    )
    result = await db.execute(query)
    system_policy = result.scalars().first()

    if system_policy:
        return load_from_db(system_policy.to_dict())

    # Fall back to environment variables
    return get_default_security_config()


# For convenience, export individual config getters
async def get_password_policy(db, tenant_id: Optional[str] = None) -> PasswordPolicyConfig:
    """Get password policy for a tenant"""
    config = await get_security_config(db, tenant_id)
    return config.password


async def get_lockout_policy(db, tenant_id: Optional[str] = None) -> AccountLockoutConfig:
    """Get account lockout policy for a tenant"""
    config = await get_security_config(db, tenant_id)
    return config.lockout


async def get_session_policy(db, tenant_id: Optional[str] = None) -> SessionSecurityConfig:
    """Get session security policy for a tenant"""
    config = await get_security_config(db, tenant_id)
    return config.session


async def get_reset_policy(db, tenant_id: Optional[str] = None) -> PasswordResetConfig:
    """Get password reset policy for a tenant"""
    config = await get_security_config(db, tenant_id)
    return config.reset
