"""
Password History Service

Manages password history tracking to prevent password reuse.
"""
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.core.auth import verify_password
from app.core.security_config import SecurityConfigService
from app.models.password_history import PasswordHistory
from app.models.user import User


class PasswordHistoryService:
    """Service for managing password history"""

    def __init__(self, db: Session):
        """Initialize the service with database session"""
        self.db = db

    def add_password_to_history(self, user: User, hashed_password: str) -> PasswordHistory:
        """
        Add a password to user's history.

        Args:
            user: User instance
            hashed_password: Hashed password to store

        Returns:
            PasswordHistory instance
        """
        history_entry = PasswordHistory(
            user_id=str(user.id),
            hashed_password=hashed_password
        )
        self.db.add(history_entry)

        # Get security config to determine history limit
        security_config = SecurityConfigService(self.db)
        history_count = security_config.get_config("password_history_count", user.tenant_id) or 5

        # Clean up old history entries beyond the limit
        if history_count > 0:
            self.cleanup_old_history(user, history_count)

        return history_entry

    def cleanup_old_history(self, user: User, keep_count: int) -> int:
        """
        Remove old password history entries beyond the configured limit.

        Args:
            user: User instance
            keep_count: Number of recent passwords to keep

        Returns:
            Number of entries deleted
        """
        if keep_count == 0:
            # Delete all history
            deleted = self.db.query(PasswordHistory).filter(
                PasswordHistory.user_id == str(user.id)
            ).delete()
            return deleted

        # Get all history entries for user, ordered by date
        all_history = self.db.query(PasswordHistory).filter(
            PasswordHistory.user_id == str(user.id)
        ).order_by(PasswordHistory.created_at.desc()).all()

        # Delete entries beyond keep_count
        if len(all_history) > keep_count:
            to_delete = all_history[keep_count:]
            deleted_count = 0
            for entry in to_delete:
                self.db.delete(entry)
                deleted_count += 1
            return deleted_count

        return 0

    def get_password_history(self, user: User, limit: int = None) -> List[PasswordHistory]:
        """
        Get password history for a user.

        Args:
            user: User instance
            limit: Optional limit on number of entries to return

        Returns:
            List of PasswordHistory entries
        """
        query = self.db.query(PasswordHistory).filter(
            PasswordHistory.user_id == str(user.id)
        ).order_by(PasswordHistory.created_at.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

    def is_password_allowed(self, user: User, plain_password: str) -> bool:
        """
        Check if a password is allowed based on history.
        Returns False if the password matches any in the history.

        Args:
            user: User instance
            plain_password: Plain text password to check

        Returns:
            True if password is allowed (not in history), False otherwise
        """
        # Get security config to determine how many passwords to check
        security_config = SecurityConfigService(self.db)
        history_count = security_config.get_config("password_history_count", user.tenant_id)

        # If history checking is disabled, allow any password
        if not history_count or history_count == 0:
            return True

        # Get recent password history
        history_entries = self.get_password_history(user, limit=history_count)

        # Check if the new password matches any in history
        for entry in history_entries:
            if verify_password(plain_password, entry.hashed_password):
                return False

        return True

    def check_password_in_history(self, user: User, plain_password: str, check_count: int = None) -> bool:
        """
        Check if a password exists in the user's history.

        Args:
            user: User instance
            plain_password: Plain text password to check
            check_count: Number of history entries to check (defaults to policy setting)

        Returns:
            True if password found in history, False otherwise
        """
        if check_count is None:
            security_config = SecurityConfigService(self.db)
            check_count = security_config.get_config("password_history_count", user.tenant_id) or 5

        history_entries = self.get_password_history(user, limit=check_count)

        for entry in history_entries:
            if verify_password(plain_password, entry.hashed_password):
                return True

        return False
