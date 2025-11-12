from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from .base import GUID, Base, generate_uuid


class NotificationQueue(Base):
    """
    Queue for async notifications with retry logic.
    Acts as a buffer table for email, SMS, webhook, and push notifications.
    """
    __tablename__ = "notification_queue"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # References
    tenant_id = Column(GUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    # Notification details
    notification_type = Column(String(50), nullable=False, index=True)
    # Types: 'account_locked', 'password_expiring', 'password_changed', 'password_reset',
    #        'login_from_new_device', 'suspicious_activity'

    delivery_method = Column(String(20), nullable=False)  # 'email', 'sms', 'webhook', 'push'
    recipient = Column(String(255), nullable=False)  # Email address, phone number, webhook URL, etc.

    # Message content
    subject = Column(String(255), nullable=True)  # For email
    message = Column(Text, nullable=False)  # Plain text message or template name
    template_data = Column(JSON, nullable=True)  # JSON data for templating

    # Priority and status
    priority = Column(Integer, nullable=False, default=5)  # 1-10, lower = higher priority
    status = Column(String(20), nullable=False, default='pending', index=True)
    # Status: 'pending', 'processing', 'sent', 'failed', 'cancelled'

    # Retry logic
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    error_message = Column(Text, nullable=True)

    # Scheduling
    scheduled_for = Column(DateTime, nullable=True, index=True)  # For delayed notifications
    sent_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User")

    def __repr__(self):
        return f"<NotificationQueue(id={self.id}, type={self.notification_type}, method={self.delivery_method}, status={self.status})>"

    @property
    def can_retry(self) -> bool:
        """Check if notification can be retried."""
        return self.status == 'failed' and self.attempts < self.max_attempts

    @property
    def is_ready(self) -> bool:
        """Check if notification is ready to be sent."""
        from datetime import datetime, timezone
        if self.status != 'pending':
            return False
        if self.scheduled_for is None:
            return True
        return datetime.now(timezone.utc) >= self.scheduled_for
