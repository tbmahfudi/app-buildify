from sqlalchemy import Column, String, Boolean, DateTime, Integer, func, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, GUID, generate_uuid


class SecurityPolicy(Base):
    """
    Configurable security policies for tenant-level customization.
    NULL tenant_id means system-wide default policy.
    """
    __tablename__ = "security_policies"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Tenant reference (NULL = system default)
    tenant_id = Column(GUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, unique=True, index=True)

    # Policy metadata
    policy_name = Column(String(100), nullable=False)
    policy_type = Column(String(50), nullable=False)  # 'password', 'session', 'lockout', 'combined'

    # ========== Password Policy Fields ==========
    password_min_length = Column(Integer, nullable=True)
    password_max_length = Column(Integer, nullable=True)
    password_require_uppercase = Column(Boolean, nullable=True)
    password_require_lowercase = Column(Boolean, nullable=True)
    password_require_digit = Column(Boolean, nullable=True)
    password_require_special_char = Column(Boolean, nullable=True)
    password_min_unique_chars = Column(Integer, nullable=True)
    password_max_repeating_chars = Column(Integer, nullable=True)
    password_allow_common = Column(Boolean, nullable=True)
    password_allow_username = Column(Boolean, nullable=True)
    password_history_count = Column(Integer, nullable=True)
    password_expiration_days = Column(Integer, nullable=True)
    password_expiration_warning_days = Column(Integer, nullable=True)
    password_grace_logins = Column(Integer, nullable=True)

    # ========== Account Lockout Policy Fields ==========
    login_max_attempts = Column(Integer, nullable=True)
    login_lockout_duration_min = Column(Integer, nullable=True)
    login_lockout_type = Column(String(20), nullable=True)  # 'fixed', 'progressive'
    login_reset_attempts_after_min = Column(Integer, nullable=True)
    login_notify_user_on_lockout = Column(Boolean, nullable=True)

    # ========== Session Policy Fields ==========
    session_timeout_minutes = Column(Integer, nullable=True)
    session_absolute_timeout_hours = Column(Integer, nullable=True)
    session_max_concurrent = Column(Integer, nullable=True)
    session_terminate_on_password_change = Column(Boolean, nullable=True)

    # ========== Password Reset Policy Fields ==========
    password_reset_token_expire_hours = Column(Integer, nullable=True)
    password_reset_max_attempts = Column(Integer, nullable=True)
    password_reset_notify_user = Column(Boolean, nullable=True)

    # Metadata
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    created_by = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    tenant = relationship("Tenant")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    def __repr__(self):
        tenant_str = f"tenant_id={self.tenant_id}" if self.tenant_id else "SYSTEM DEFAULT"
        return f"<SecurityPolicy(id={self.id}, {tenant_str}, policy_name={self.policy_name})>"

    def to_dict(self):
        """Convert policy to dictionary, excluding None values."""
        return {
            k: v for k, v in {
                # Password policies
                'password_min_length': self.password_min_length,
                'password_max_length': self.password_max_length,
                'password_require_uppercase': self.password_require_uppercase,
                'password_require_lowercase': self.password_require_lowercase,
                'password_require_digit': self.password_require_digit,
                'password_require_special_char': self.password_require_special_char,
                'password_min_unique_chars': self.password_min_unique_chars,
                'password_max_repeating_chars': self.password_max_repeating_chars,
                'password_allow_common': self.password_allow_common,
                'password_allow_username': self.password_allow_username,
                'password_history_count': self.password_history_count,
                'password_expiration_days': self.password_expiration_days,
                'password_expiration_warning_days': self.password_expiration_warning_days,
                'password_grace_logins': self.password_grace_logins,
                # Lockout policies
                'login_max_attempts': self.login_max_attempts,
                'login_lockout_duration_min': self.login_lockout_duration_min,
                'login_lockout_type': self.login_lockout_type,
                'login_reset_attempts_after_min': self.login_reset_attempts_after_min,
                'login_notify_user_on_lockout': self.login_notify_user_on_lockout,
                # Session policies
                'session_timeout_minutes': self.session_timeout_minutes,
                'session_absolute_timeout_hours': self.session_absolute_timeout_hours,
                'session_max_concurrent': self.session_max_concurrent,
                'session_terminate_on_password_change': self.session_terminate_on_password_change,
                # Reset policies
                'password_reset_token_expire_hours': self.password_reset_token_expire_hours,
                'password_reset_max_attempts': self.password_reset_max_attempts,
                'password_reset_notify_user': self.password_reset_notify_user,
            }.items() if v is not None
        }
