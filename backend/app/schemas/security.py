"""
Pydantic schemas for security administration.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== Security Policy Schemas ====================

class SecurityPolicyBase(BaseModel):
    tenant_id: Optional[str] = Field(None, description="Tenant ID (NULL for system default)")
    policy_name: str = Field(..., min_length=1, max_length=100)
    policy_type: str = Field(default="combined", description="Policy type: password, session, lockout, combined")

    # Password policy fields
    password_min_length: Optional[int] = Field(None, ge=8, le=128)
    password_max_length: Optional[int] = Field(None, ge=8, le=256)
    password_require_uppercase: Optional[bool] = None
    password_require_lowercase: Optional[bool] = None
    password_require_digit: Optional[bool] = None
    password_require_special_char: Optional[bool] = None
    password_min_unique_chars: Optional[int] = Field(None, ge=0)
    password_max_repeating_chars: Optional[int] = Field(None, ge=0)
    password_allow_common: Optional[bool] = None
    password_allow_username: Optional[bool] = None
    password_history_count: Optional[int] = Field(None, ge=0)
    password_expiration_days: Optional[int] = Field(None, ge=0)
    password_expiration_warning_days: Optional[int] = Field(None, ge=0)
    password_grace_logins: Optional[int] = Field(None, ge=0)

    # Account lockout policy fields
    login_max_attempts: Optional[int] = Field(None, ge=1)
    login_lockout_duration_min: Optional[int] = Field(None, ge=1)
    login_lockout_type: Optional[str] = Field(None, description="fixed or progressive")
    login_reset_attempts_after_min: Optional[int] = Field(None, ge=1)
    login_notify_user_on_lockout: Optional[bool] = None

    # Session policy fields
    session_timeout_minutes: Optional[int] = Field(None, ge=1)
    session_absolute_timeout_hours: Optional[int] = Field(None, ge=1)
    session_max_concurrent: Optional[int] = Field(None, ge=0)
    session_terminate_on_password_change: Optional[bool] = None

    # Password reset policy fields
    password_reset_token_expire_hours: Optional[int] = Field(None, ge=1)
    password_reset_max_attempts: Optional[int] = Field(None, ge=1)
    password_reset_notify_user: Optional[bool] = None


class SecurityPolicyCreate(SecurityPolicyBase):
    pass


class SecurityPolicyUpdate(BaseModel):
    policy_name: Optional[str] = Field(None, min_length=1, max_length=100)
    policy_type: Optional[str] = None

    # All policy fields optional for updates
    password_min_length: Optional[int] = Field(None, ge=8, le=128)
    password_max_length: Optional[int] = Field(None, ge=8, le=256)
    password_require_uppercase: Optional[bool] = None
    password_require_lowercase: Optional[bool] = None
    password_require_digit: Optional[bool] = None
    password_require_special_char: Optional[bool] = None
    password_min_unique_chars: Optional[int] = Field(None, ge=0)
    password_max_repeating_chars: Optional[int] = Field(None, ge=0)
    password_allow_common: Optional[bool] = None
    password_allow_username: Optional[bool] = None
    password_history_count: Optional[int] = Field(None, ge=0)
    password_expiration_days: Optional[int] = Field(None, ge=0)
    password_expiration_warning_days: Optional[int] = Field(None, ge=0)
    password_grace_logins: Optional[int] = Field(None, ge=0)

    login_max_attempts: Optional[int] = Field(None, ge=1)
    login_lockout_duration_min: Optional[int] = Field(None, ge=1)
    login_lockout_type: Optional[str] = None
    login_reset_attempts_after_min: Optional[int] = Field(None, ge=1)
    login_notify_user_on_lockout: Optional[bool] = None

    session_timeout_minutes: Optional[int] = Field(None, ge=1)
    session_absolute_timeout_hours: Optional[int] = Field(None, ge=1)
    session_max_concurrent: Optional[int] = Field(None, ge=0)
    session_terminate_on_password_change: Optional[bool] = None

    password_reset_token_expire_hours: Optional[int] = Field(None, ge=1)
    password_reset_max_attempts: Optional[int] = Field(None, ge=1)
    password_reset_notify_user: Optional[bool] = None

    is_active: Optional[bool] = None


class SecurityPolicyResponse(SecurityPolicyBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]

    class Config:
        from_attributes = True


# ==================== Locked Account Schemas ====================

class LockedAccountResponse(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str]
    tenant_id: str
    locked_until: datetime
    failed_attempts: int
    is_active: bool


class UnlockAccountRequest(BaseModel):
    user_id: str
    reason: Optional[str] = Field(None, description="Reason for unlocking")


# ==================== Session Schemas ====================

class UserSessionResponse(BaseModel):
    id: str
    user_id: str
    jti: str
    device_id: Optional[str]
    device_name: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    last_activity: datetime
    created_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime]

    class Config:
        from_attributes = True


class RevokeSessionRequest(BaseModel):
    session_id: str


# ==================== Login Attempt Schemas ====================

class LoginAttemptResponse(BaseModel):
    id: str
    user_id: Optional[str]
    email: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    success: bool
    failure_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Notification Config Schemas ====================

class NotificationConfigBase(BaseModel):
    tenant_id: Optional[str] = Field(None, description="Tenant ID (NULL for system default)")
    config_name: str = Field(..., min_length=1, max_length=100)

    # Notification type settings
    account_locked_enabled: bool = True
    account_locked_methods: Optional[List[str]] = Field(default=["email"])

    password_expiring_enabled: bool = True
    password_expiring_methods: Optional[List[str]] = Field(default=["email"])

    password_changed_enabled: bool = True
    password_changed_methods: Optional[List[str]] = Field(default=["email"])

    password_reset_enabled: bool = True
    password_reset_methods: Optional[List[str]] = Field(default=["email"])

    login_from_new_device_enabled: bool = False
    login_from_new_device_methods: Optional[List[str]] = Field(default=["email"])

    # Email configuration
    email_enabled: bool = True
    email_from: Optional[str] = None
    email_smtp_host: Optional[str] = None
    email_smtp_port: Optional[int] = None
    email_smtp_user: Optional[str] = None
    email_smtp_password: Optional[str] = None  # Should be encrypted in production
    email_use_tls: Optional[bool] = True

    # SMS configuration
    sms_enabled: bool = False
    sms_provider: Optional[str] = None
    sms_api_key: Optional[str] = None
    sms_from_number: Optional[str] = None

    # Webhook configuration
    webhook_enabled: bool = False
    webhook_url: Optional[str] = None
    webhook_auth_header: Optional[str] = None


class NotificationConfigUpdate(BaseModel):
    config_name: Optional[str] = Field(None, min_length=1, max_length=100)

    account_locked_enabled: Optional[bool] = None
    account_locked_methods: Optional[List[str]] = None

    password_expiring_enabled: Optional[bool] = None
    password_expiring_methods: Optional[List[str]] = None

    password_changed_enabled: Optional[bool] = None
    password_changed_methods: Optional[List[str]] = None

    password_reset_enabled: Optional[bool] = None
    password_reset_methods: Optional[List[str]] = None

    login_from_new_device_enabled: Optional[bool] = None
    login_from_new_device_methods: Optional[List[str]] = None

    email_enabled: Optional[bool] = None
    email_from: Optional[str] = None
    email_smtp_host: Optional[str] = None
    email_smtp_port: Optional[int] = None
    email_smtp_user: Optional[str] = None
    email_smtp_password: Optional[str] = None
    email_use_tls: Optional[bool] = None

    sms_enabled: Optional[bool] = None
    sms_provider: Optional[str] = None
    sms_api_key: Optional[str] = None
    sms_from_number: Optional[str] = None

    webhook_enabled: Optional[bool] = None
    webhook_url: Optional[str] = None
    webhook_auth_header: Optional[str] = None

    is_active: Optional[bool] = None


class NotificationConfigResponse(NotificationConfigBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]

    class Config:
        from_attributes = True


# ==================== Notification Queue Schemas ====================

class NotificationQueueResponse(BaseModel):
    id: str
    tenant_id: Optional[str]
    user_id: Optional[str]
    notification_type: str
    delivery_method: str
    recipient: str
    subject: Optional[str]
    message: str
    template_data: Optional[Dict[str, Any]]
    priority: int
    status: str
    attempts: int
    max_attempts: int
    error_message: Optional[str]
    scheduled_for: Optional[datetime]
    sent_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== Password Policy Display (for users) ====================

class PasswordPolicyRequirements(BaseModel):
    """Password policy requirements displayed to users"""
    requirements: List[str]
    expiration_days: int
    warning_days: int
    grace_logins: int


class PasswordStrengthCheck(BaseModel):
    """Response for password strength checking"""
    is_valid: bool
    errors: List[str]
    score: Optional[int] = Field(None, description="Strength score 0-100")
