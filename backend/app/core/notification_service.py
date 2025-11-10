"""
Notification Service

Queue-based notification system with configurable delivery methods.
Supports email, SMS, webhook, and push notifications.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import NotificationQueue, NotificationConfig


class NotificationService:
    """Service for queuing and managing notifications"""

    @staticmethod
    async def queue_notification(
        db: AsyncSession,
        notification_type: str,
        delivery_method: str,
        recipient: str,
        message: str,
        subject: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        scheduled_for: Optional[datetime] = None,
        max_attempts: int = 3
    ) -> NotificationQueue:
        """
        Queue a notification for delivery.

        Args:
            db: Database session
            notification_type: Type of notification
            delivery_method: How to deliver (email, sms, webhook, push)
            recipient: Recipient address/number/URL
            message: Message content
            subject: Optional subject (for email)
            tenant_id: Optional tenant ID
            user_id: Optional user ID
            template_data: Optional template data
            priority: Priority (1-10, lower = higher priority)
            scheduled_for: Optional scheduled delivery time
            max_attempts: Maximum delivery attempts

        Returns:
            NotificationQueue instance
        """
        notification = NotificationQueue(
            tenant_id=tenant_id,
            user_id=user_id,
            notification_type=notification_type,
            delivery_method=delivery_method,
            recipient=recipient,
            subject=subject,
            message=message,
            template_data=template_data,
            priority=priority,
            scheduled_for=scheduled_for,
            max_attempts=max_attempts
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    @staticmethod
    async def get_notification_config(
        db: AsyncSession,
        tenant_id: Optional[str] = None
    ) -> Optional[NotificationConfig]:
        """
        Get notification configuration for tenant (or system default).

        Args:
            db: Database session
            tenant_id: Optional tenant ID

        Returns:
            NotificationConfig if found
        """
        # Try tenant-specific first
        if tenant_id:
            query = select(NotificationConfig).where(
                and_(
                    NotificationConfig.tenant_id == tenant_id,
                    NotificationConfig.is_active == True
                )
            )
            result = await db.execute(query)
            config = result.scalars().first()
            if config:
                return config

        # Fall back to system default
        query = select(NotificationConfig).where(
            and_(
                NotificationConfig.tenant_id == None,
                NotificationConfig.is_active == True
            )
        )
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def notify_account_locked(
        db: AsyncSession,
        user_email: str,
        locked_until: datetime,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[NotificationQueue]:
        """
        Queue notification for account lockout.

        Args:
            db: Database session
            user_email: User's email
            locked_until: When lockout expires
            user_id: Optional user ID
            tenant_id: Optional tenant ID

        Returns:
            List of queued notifications
        """
        config = await NotificationService.get_notification_config(db, tenant_id)
        notifications = []

        if not config or not config.account_locked_enabled:
            return notifications

        methods = config.get_methods_for_notification_type('account_locked')
        duration = locked_until - datetime.now(timezone.utc)
        minutes = int(duration.total_seconds() / 60)

        message = f"Your account has been locked due to too many failed login attempts. It will be unlocked in {minutes} minutes."

        for method in methods:
            notification = await NotificationService.queue_notification(
                db=db,
                notification_type='account_locked',
                delivery_method=method,
                recipient=user_email,
                message=message,
                subject="Account Locked - Security Alert",
                tenant_id=tenant_id,
                user_id=user_id,
                priority=2  # High priority
            )
            notifications.append(notification)

        return notifications

    @staticmethod
    async def notify_password_expiring(
        db: AsyncSession,
        user_email: str,
        days_until_expiry: int,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[NotificationQueue]:
        """
        Queue notification for password expiring soon.

        Args:
            db: Database session
            user_email: User's email
            days_until_expiry: Days until password expires
            user_id: Optional user ID
            tenant_id: Optional tenant ID

        Returns:
            List of queued notifications
        """
        config = await NotificationService.get_notification_config(db, tenant_id)
        notifications = []

        if not config or not config.password_expiring_enabled:
            return notifications

        methods = config.get_methods_for_notification_type('password_expiring')
        message = f"Your password will expire in {days_until_expiry} days. Please change it soon to avoid service interruption."

        for method in methods:
            notification = await NotificationService.queue_notification(
                db=db,
                notification_type='password_expiring',
                delivery_method=method,
                recipient=user_email,
                message=message,
                subject="Password Expiring Soon",
                tenant_id=tenant_id,
                user_id=user_id,
                priority=5  # Normal priority
            )
            notifications.append(notification)

        return notifications

    @staticmethod
    async def notify_password_changed(
        db: AsyncSession,
        user_email: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[NotificationQueue]:
        """
        Queue notification for password change.

        Args:
            db: Database session
            user_email: User's email
            user_id: Optional user ID
            tenant_id: Optional tenant ID

        Returns:
            List of queued notifications
        """
        config = await NotificationService.get_notification_config(db, tenant_id)
        notifications = []

        if not config or not config.password_changed_enabled:
            return notifications

        methods = config.get_methods_for_notification_type('password_changed')
        message = "Your password has been changed successfully. If you did not make this change, please contact support immediately."

        for method in methods:
            notification = await NotificationService.queue_notification(
                db=db,
                notification_type='password_changed',
                delivery_method=method,
                recipient=user_email,
                message=message,
                subject="Password Changed - Security Alert",
                tenant_id=tenant_id,
                user_id=user_id,
                priority=3  # Medium-high priority
            )
            notifications.append(notification)

        return notifications

    @staticmethod
    async def notify_password_reset(
        db: AsyncSession,
        user_email: str,
        reset_link: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[NotificationQueue]:
        """
        Queue notification for password reset.

        Args:
            db: Database session
            user_email: User's email
            reset_link: Password reset link
            user_id: Optional user ID
            tenant_id: Optional tenant ID

        Returns:
            List of queued notifications
        """
        config = await NotificationService.get_notification_config(db, tenant_id)
        notifications = []

        if not config or not config.password_reset_enabled:
            return notifications

        methods = config.get_methods_for_notification_type('password_reset')
        message = f"You requested a password reset. Click the link to reset your password: {reset_link}\n\nThis link expires in 1 hour. If you did not request this, please ignore this message."

        for method in methods:
            notification = await NotificationService.queue_notification(
                db=db,
                notification_type='password_reset',
                delivery_method=method,
                recipient=user_email,
                message=message,
                subject="Password Reset Request",
                tenant_id=tenant_id,
                user_id=user_id,
                priority=2  # High priority
            )
            notifications.append(notification)

        return notifications


# Convenience exports
async def notify_account_locked(db: AsyncSession, user_email: str, locked_until: datetime, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> List[NotificationQueue]:
    """Queue account locked notification"""
    return await NotificationService.notify_account_locked(db, user_email, locked_until, user_id, tenant_id)


async def notify_password_expiring(db: AsyncSession, user_email: str, days_until_expiry: int, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> List[NotificationQueue]:
    """Queue password expiring notification"""
    return await NotificationService.notify_password_expiring(db, user_email, days_until_expiry, user_id, tenant_id)


async def notify_password_changed(db: AsyncSession, user_email: str, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> List[NotificationQueue]:
    """Queue password changed notification"""
    return await NotificationService.notify_password_changed(db, user_email, user_id, tenant_id)


async def notify_password_reset(db: AsyncSession, user_email: str, reset_link: str, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> List[NotificationQueue]:
    """Queue password reset notification"""
    return await NotificationService.notify_password_reset(db, user_email, reset_link, user_id, tenant_id)
