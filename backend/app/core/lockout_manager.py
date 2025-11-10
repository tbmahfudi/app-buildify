"""
Account Lockout Manager

Manages account lockouts based on failed login attempts with support for:
- Fixed duration lockouts
- Progressive lockouts (increasing duration)
- Automatic lockout expiration
- Manual admin unlock
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import User, LoginAttempt, AccountLockout
from app.core.security_config import AccountLockoutConfig


class LockoutManager:
    """Manages account lockout policies and enforcement"""

    def __init__(self, policy: AccountLockoutConfig):
        self.policy = policy

    async def record_login_attempt(
        self,
        db: AsyncSession,
        user_id: Optional[str],
        email: str,
        success: bool,
        failure_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> LoginAttempt:
        """
        Record a login attempt (success or failure).

        Args:
            db: Database session
            user_id: User ID (None for non-existent users)
            email: Email used in login attempt
            success: Whether login was successful
            failure_reason: Reason for failure
            ip_address: IP address of request
            user_agent: User agent string

        Returns:
            LoginAttempt instance
        """
        attempt = LoginAttempt(
            user_id=user_id,
            email=email,
            success=success,
            failure_reason=failure_reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(attempt)
        await db.commit()
        await db.refresh(attempt)
        return attempt

    async def get_recent_failed_attempts(
        self,
        db: AsyncSession,
        email: str,
        since_minutes: Optional[int] = None
    ) -> int:
        """
        Count recent failed login attempts for an email.

        Args:
            db: Database session
            email: Email to check
            since_minutes: Time window in minutes (uses policy default if None)

        Returns:
            Count of failed attempts
        """
        since_minutes = since_minutes or self.policy.reset_attempts_after_min
        since_time = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)

        query = select(LoginAttempt).where(
            and_(
                LoginAttempt.email == email,
                LoginAttempt.success == False,
                LoginAttempt.created_at >= since_time
            )
        )

        result = await db.execute(query)
        attempts = result.scalars().all()
        return len(attempts)

    def calculate_lockout_duration(self, attempt_count: int) -> int:
        """
        Calculate lockout duration based on attempt count and policy.

        Args:
            attempt_count: Number of failed attempts

        Returns:
            Lockout duration in minutes
        """
        if self.policy.lockout_type == "fixed":
            return self.policy.lockout_duration_min

        # Progressive lockout
        for threshold, duration in sorted(self.policy.progressive_durations.items()):
            if attempt_count >= threshold:
                lockout_duration = duration

        # Default to policy duration if no threshold matched
        if 'lockout_duration' not in locals():
            lockout_duration = self.policy.lockout_duration_min

        return lockout_duration

    async def apply_lockout(
        self,
        db: AsyncSession,
        user: User,
        attempt_count: int,
        reason: str = "Too many failed login attempts"
    ) -> AccountLockout:
        """
        Apply account lockout to a user.

        Args:
            db: Database session
            user: User to lock
            attempt_count: Number of failed attempts
            reason: Lockout reason

        Returns:
            AccountLockout instance
        """
        duration_minutes = self.calculate_lockout_duration(attempt_count)
        locked_until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)

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
        db.add(lockout)
        await db.commit()
        await db.refresh(lockout)

        return lockout

    async def check_and_apply_lockout(
        self,
        db: AsyncSession,
        user: User,
        email: str
    ) -> Tuple[bool, Optional[datetime]]:
        """
        Check if user should be locked out based on recent failed attempts.
        Apply lockout if threshold exceeded.

        Args:
            db: Database session
            user: User to check
            email: User's email

        Returns:
            Tuple of (should_lock, locked_until)
        """
        # Check if already locked
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            return (True, user.locked_until)

        # Count recent failed attempts
        failed_attempts = await self.get_recent_failed_attempts(db, email)

        # Check if threshold exceeded
        if failed_attempts >= self.policy.max_attempts:
            lockout = await self.apply_lockout(db, user, failed_attempts)
            return (True, lockout.locked_until)

        # Update attempt count but don't lock
        user.failed_login_attempts = failed_attempts
        await db.commit()

        return (False, None)

    async def unlock_account(
        self,
        db: AsyncSession,
        user: User,
        unlocked_by_id: Optional[str] = None,
        reason: str = "Manual unlock by admin"
    ) -> None:
        """
        Manually unlock a user account.

        Args:
            db: Database session
            user: User to unlock
            unlocked_by_id: ID of admin who unlocked
            reason: Unlock reason
        """
        # Clear user lockout
        user.locked_until = None
        user.failed_login_attempts = 0

        # Update most recent active lockout
        query = select(AccountLockout).where(
            and_(
                AccountLockout.user_id == str(user.id),
                AccountLockout.unlocked_at == None,
                AccountLockout.locked_until > datetime.now(timezone.utc)
            )
        ).order_by(AccountLockout.locked_at.desc())

        result = await db.execute(query)
        lockout = result.scalars().first()

        if lockout:
            lockout.unlocked_at = datetime.now(timezone.utc)
            lockout.unlocked_by = unlocked_by_id
            lockout.unlock_reason = reason

        await db.commit()

    async def reset_failed_attempts(
        self,
        db: AsyncSession,
        user: User
    ) -> None:
        """
        Reset failed login attempt counter (called on successful login).

        Args:
            db: Database session
            user: User to reset
        """
        user.failed_login_attempts = 0
        await db.commit()

    async def is_account_locked(
        self,
        db: AsyncSession,
        user: User
    ) -> Tuple[bool, Optional[datetime]]:
        """
        Check if account is currently locked.

        Args:
            db: Database session
            user: User to check

        Returns:
            Tuple of (is_locked, locked_until)
        """
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            return (True, user.locked_until)

        # Clear expired lockout
        if user.locked_until:
            user.locked_until = None
            user.failed_login_attempts = 0
            await db.commit()

        return (False, None)


async def check_account_lockout(
    db: AsyncSession,
    user: User,
    policy: AccountLockoutConfig
) -> Tuple[bool, Optional[datetime], Optional[str]]:
    """
    Convenience function to check if account is locked.

    Returns:
        Tuple of (is_locked, locked_until, message)
    """
    manager = LockoutManager(policy)
    is_locked, locked_until = await manager.is_account_locked(db, user)

    if is_locked:
        duration = locked_until - datetime.now(timezone.utc)
        minutes = int(duration.total_seconds() / 60)
        message = f"Account is locked due to too many failed login attempts. Please try again in {minutes} minutes."
        return (True, locked_until, message)

    return (False, None, None)
