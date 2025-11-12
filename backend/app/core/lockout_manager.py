"""
Account Lockout Manager

Manages account lockouts based on failed login attempts with support for:
- Fixed duration lockouts
- Progressive lockouts (increasing duration)
- Automatic lockout expiration
- Manual admin unlock
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.security_config import SecurityConfigService
from app.models.account_lockout import AccountLockout
from app.models.login_attempt import LoginAttempt
from app.models.user import User


class LockoutManager:
    """Manages account lockout policies and enforcement"""

    def __init__(self, db: Session):
        """
        Initialize lockout manager with database session.

        Args:
            db: Database session
        """
        self.db = db
        self.security_config = SecurityConfigService(db)

    def get_recent_failed_attempts(
        self,
        email: str,
        tenant_id: Optional[str] = None,
        since_minutes: Optional[int] = None
    ) -> int:
        """
        Count recent failed login attempts for an email.

        Args:
            email: Email to check
            tenant_id: Tenant ID for policy lookup
            since_minutes: Time window in minutes (uses policy default if None)

        Returns:
            Count of failed attempts
        """
        if since_minutes is None:
            since_minutes = self.security_config.get_config("login_reset_attempts_after_min", tenant_id) or 30

        since_time = datetime.utcnow() - timedelta(minutes=since_minutes)

        count = self.db.query(LoginAttempt).filter(
            LoginAttempt.email == email,
            LoginAttempt.success == False,
            LoginAttempt.created_at >= since_time
        ).count()

        return count

    def calculate_lockout_duration(self, attempt_count: int, tenant_id: Optional[str] = None) -> int:
        """
        Calculate lockout duration based on attempt count and policy.

        Args:
            attempt_count: Number of failed attempts
            tenant_id: Tenant ID for policy lookup

        Returns:
            Lockout duration in minutes
        """
        lockout_type = self.security_config.get_config("login_lockout_type", tenant_id) or "fixed"
        base_duration = self.security_config.get_config("login_lockout_duration_min", tenant_id) or 30

        if lockout_type == "fixed":
            return base_duration

        # Progressive lockout - double duration for each threshold exceeded
        if attempt_count >= 10:
            return base_duration * 4
        elif attempt_count >= 7:
            return base_duration * 2
        else:
            return base_duration

    def apply_lockout(
        self,
        user: User,
        attempt_count: int,
        reason: str = "Too many failed login attempts"
    ) -> AccountLockout:
        """
        Apply account lockout to a user.

        Args:
            user: User to lock
            attempt_count: Number of failed attempts
            reason: Lockout reason

        Returns:
            AccountLockout instance
        """
        duration_minutes = self.calculate_lockout_duration(attempt_count, user.tenant_id)
        locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)

        # Update user record
        user.locked_until = locked_until
        user.failed_login_attempts = attempt_count

        # Create lockout record
        lockout = AccountLockout(
            user_id=str(user.id),
            locked_until=locked_until,
            lockout_reason=reason,
            attempt_count=attempt_count
        )
        self.db.add(lockout)
        self.db.commit()
        self.db.refresh(lockout)

        return lockout

    def is_account_locked(self, user: User) -> bool:
        """
        Check if account is currently locked.

        Args:
            user: User to check

        Returns:
            True if locked, False otherwise
        """
        if user.locked_until and user.locked_until > datetime.utcnow():
            return True

        # Clear expired lockout
        if user.locked_until:
            user.locked_until = None
            user.failed_login_attempts = 0
            self.db.commit()

        return False

    def record_failed_login(self, user: User) -> None:
        """
        Record a failed login attempt and potentially lock account.

        Args:
            user: User who failed login
        """
        # Check if already locked
        if self.is_account_locked(user):
            return

        # Count recent failed attempts
        failed_attempts = self.get_recent_failed_attempts(user.email, user.tenant_id)
        max_attempts = self.security_config.get_config("login_max_attempts", user.tenant_id) or 5

        # Increment attempt count
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

        # Check if threshold exceeded
        if user.failed_login_attempts >= max_attempts:
            self.apply_lockout(user, user.failed_login_attempts)

            # Queue notification if enabled
            notify_on_lockout = self.security_config.get_config("login_notify_user_on_lockout", user.tenant_id)
            if notify_on_lockout:
                try:
                    from app.core.notification_service import NotificationService
                    notification_service = NotificationService(self.db)
                    notification_service.queue_notification(
                        tenant_id=user.tenant_id,
                        user_id=str(user.id),
                        notification_type="account_locked",
                        recipient=user.email,
                        subject="Account Locked",
                        message=f"Your account has been locked due to too many failed login attempts. It will be unlocked at {user.locked_until}.",
                        template_data={
                            "user_name": user.full_name or user.email,
                            "locked_until": user.locked_until.isoformat(),
                            "attempt_count": user.failed_login_attempts
                        }
                    )
                except Exception as e:
                    # Don't fail the lockout if notification fails
                    import logging
                    logging.warning(f"Failed to queue lockout notification for user {user.id}: {e}")
        else:
            self.db.commit()

    def unlock_account(
        self,
        user: User,
        unlocked_by_id: Optional[str] = None,
        reason: str = "Manual unlock by admin"
    ) -> None:
        """
        Manually unlock a user account.

        Args:
            user: User to unlock
            unlocked_by_id: ID of admin who unlocked
            reason: Unlock reason
        """
        # Clear user lockout
        user.locked_until = None
        user.failed_login_attempts = 0

        # Update most recent active lockout
        lockout = self.db.query(AccountLockout).filter(
            AccountLockout.user_id == str(user.id),
            AccountLockout.unlocked_at == None,
            AccountLockout.locked_until > datetime.utcnow()
        ).order_by(AccountLockout.locked_at.desc()).first()

        if lockout:
            lockout.unlocked_at = datetime.utcnow()
            lockout.unlocked_by = unlocked_by_id
            lockout.unlock_reason = reason

        self.db.commit()

    def reset_failed_attempts(self, user: User) -> None:
        """
        Reset failed login attempt counter (called on successful login).

        Args:
            user: User to reset
        """
        user.failed_login_attempts = 0
        # Don't commit here - let the caller handle it
