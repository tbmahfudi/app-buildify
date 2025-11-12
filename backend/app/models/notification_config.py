from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from .base import GUID, Base, generate_uuid


class NotificationConfig(Base):
    """
    Configuration for notification delivery methods.
    NULL tenant_id means system-wide default configuration.
    Superadmin can configure both system defaults and tenant-specific settings.
    """
    __tablename__ = "notification_config"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Tenant reference (NULL = system default)
    tenant_id = Column(GUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, unique=True, index=True)

    # Configuration name
    config_name = Column(String(100), nullable=False)

    # ========== Notification Type Settings ==========
    # Each notification type can be enabled/disabled and use specific delivery methods

    account_locked_enabled = Column(Boolean, nullable=False, default=True)
    account_locked_methods = Column(JSON, nullable=True)  # ['email', 'sms']

    password_expiring_enabled = Column(Boolean, nullable=False, default=True)
    password_expiring_methods = Column(JSON, nullable=True)  # ['email']

    password_changed_enabled = Column(Boolean, nullable=False, default=True)
    password_changed_methods = Column(JSON, nullable=True)  # ['email', 'sms']

    password_reset_enabled = Column(Boolean, nullable=False, default=True)
    password_reset_methods = Column(JSON, nullable=True)  # ['email']

    login_from_new_device_enabled = Column(Boolean, nullable=False, default=False)
    login_from_new_device_methods = Column(JSON, nullable=True)  # ['email']

    # ========== Email Configuration ==========
    email_enabled = Column(Boolean, nullable=False, default=True)
    email_from = Column(String(255), nullable=True)
    email_smtp_host = Column(String(255), nullable=True)
    email_smtp_port = Column(Integer, nullable=True)
    email_smtp_user = Column(String(255), nullable=True)
    email_smtp_password = Column(String(255), nullable=True)  # Should be encrypted
    email_use_tls = Column(Boolean, nullable=True, default=True)

    # ========== SMS Configuration ==========
    sms_enabled = Column(Boolean, nullable=False, default=False)
    sms_provider = Column(String(50), nullable=True)  # 'twilio', 'aws_sns', 'nexmo', etc.
    sms_api_key = Column(String(255), nullable=True)  # Should be encrypted
    sms_from_number = Column(String(20), nullable=True)

    # ========== Webhook Configuration ==========
    webhook_enabled = Column(Boolean, nullable=False, default=False)
    webhook_url = Column(String(500), nullable=True)
    webhook_auth_header = Column(String(255), nullable=True)  # Authorization header value

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
        return f"<NotificationConfig(id={self.id}, {tenant_str}, config_name={self.config_name})>"

    def get_methods_for_notification_type(self, notification_type: str) -> list:
        """Get enabled delivery methods for a specific notification type."""
        type_map = {
            'account_locked': (self.account_locked_enabled, self.account_locked_methods),
            'password_expiring': (self.password_expiring_enabled, self.password_expiring_methods),
            'password_changed': (self.password_changed_enabled, self.password_changed_methods),
            'password_reset': (self.password_reset_enabled, self.password_reset_methods),
            'login_from_new_device': (self.login_from_new_device_enabled, self.login_from_new_device_methods),
        }

        enabled, methods = type_map.get(notification_type, (False, None))
        if not enabled:
            return []

        # Return configured methods, filtering by globally enabled delivery methods
        available_methods = []
        if methods:
            for method in methods:
                if method == 'email' and self.email_enabled:
                    available_methods.append(method)
                elif method == 'sms' and self.sms_enabled:
                    available_methods.append(method)
                elif method == 'webhook' and self.webhook_enabled:
                    available_methods.append(method)

        return available_methods
