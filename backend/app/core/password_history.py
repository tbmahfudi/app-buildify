"""
Password History Service

Manages password history tracking to prevent password reuse.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models import PasswordHistory, User
from app.core.auth import get_password_hash
from app.core.security_config import PasswordPolicyConfig


class PasswordHistoryService:
    """Service for managing password history"""

    @staticmethod
    async def add_to_history(
        db: AsyncSession,
        user_id: str,
        hashed_password: str
    ) -> PasswordHistory:
        """
        Add a password to user's history.

        Args:
            db: Database session
            user_id: User ID
            hashed_password: Hashed password to store

        Returns:
            PasswordHistory instance
        """
        history_entry = PasswordHistory(
            user_id=user_id,
            hashed_password=hashed_password
        )
        db.add(history_entry)
        await db.commit()
        await db.refresh(history_entry)
        return history_entry

    @staticmethod
    async def cleanup_old_history(
        db: AsyncSession,
        user_id: str,
        keep_count: int
    ) -> int:
        """
        Remove old password history entries beyond the configured limit.

        Args:
            db: Database session
            user_id: User ID
            keep_count: Number of recent passwords to keep

        Returns:
            Number of entries deleted
        """
        if keep_count == 0:
            # Delete all history
            result = await db.execute(
                delete(PasswordHistory).where(PasswordHistory.user_id == user_id)
            )
            await db.commit()
            return result.rowcount

        # Get all history entries for user, ordered by date
        query = select(PasswordHistory).where(
            PasswordHistory.user_id == user_id
        ).order_by(PasswordHistory.created_at.desc())

        result = await db.execute(query)
        all_history = result.scalars().all()

        # Delete entries beyond keep_count
        if len(all_history) > keep_count:
            to_delete = all_history[keep_count:]
            for entry in to_delete:
                await db.delete(entry)
            await db.commit()
            return len(to_delete)

        return 0

    @staticmethod
    async def record_password_change(
        db: AsyncSession,
        user: User,
        new_password_hash: str,
        policy: PasswordPolicyConfig
    ) -> None:
        """
        Record a password change:
        1. Add current password to history
        2. Update user's password_changed_at timestamp
        3. Calculate and set password expiration
        4. Clean up old history beyond policy limit

        Args:
            db: Database session
            user: User instance
            new_password_hash: New hashed password
            policy: Password policy configuration
        """
        # Add to history
        await PasswordHistoryService.add_to_history(db, str(user.id), new_password_hash)

        # Update user timestamps
        now = datetime.now(timezone.utc)
        user.password_changed_at = now

        # Calculate expiration if policy requires it
        if policy.expiration_days > 0:
            from datetime import timedelta
            user.password_expires_at = now + timedelta(days=policy.expiration_days)
        else:
            user.password_expires_at = None

        # Reset grace logins
        user.grace_logins_remaining = policy.grace_logins
        user.require_password_change = False

        await db.commit()

        # Clean up old history
        if policy.history_count > 0:
            await PasswordHistoryService.cleanup_old_history(
                db,
                str(user.id),
                policy.history_count
            )


async def record_password_change(
    db: AsyncSession,
    user: User,
    new_password_hash: str,
    policy: PasswordPolicyConfig
) -> None:
    """
    Convenience function to record a password change.
    """
    await PasswordHistoryService.record_password_change(db, user, new_password_hash, policy)
