"""
Password Validator

Comprehensive password strength validation with configurable policies.
Supports checking against:
- Length requirements
- Character complexity (uppercase, lowercase, digits, special characters)
- Common passwords
- Password history
- Username/email similarity
"""
import re
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security_config import PasswordPolicyConfig
from app.core.common_passwords import is_common_password
from app.core.auth import verify_password


class PasswordValidationError(Exception):
    """Raised when password validation fails"""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class PasswordValidator:
    """
    Validates passwords against configurable security policies.
    """

    def __init__(self, policy: PasswordPolicyConfig):
        self.policy = policy

    def validate_strength(self, password: str, user_email: Optional[str] = None, user_name: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Validate password strength against policy rules.

        Args:
            password: Password to validate
            user_email: Optional user email for similarity checking
            user_name: Optional user name for similarity checking

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Length checks
        if len(password) < self.policy.min_length:
            errors.append(f"Password must be at least {self.policy.min_length} characters long")

        if len(password) > self.policy.max_length:
            errors.append(f"Password must not exceed {self.policy.max_length} characters")

        # Character type requirements
        if self.policy.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        if self.policy.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        if self.policy.require_digit and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")

        if self.policy.require_special_char and not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
            errors.append("Password must contain at least one special character (!@#$%^&*...)")

        # Unique characters check
        unique_chars = len(set(password))
        if unique_chars < self.policy.min_unique_chars:
            errors.append(f"Password must contain at least {self.policy.min_unique_chars} unique characters")

        # Repeating characters check
        if self.policy.max_repeating_chars > 0:
            pattern = r'(.)\1{' + str(self.policy.max_repeating_chars) + ',}'
            if re.search(pattern, password):
                errors.append(f"Password must not contain more than {self.policy.max_repeating_chars} consecutive repeating characters")

        # Common password check
        if not self.policy.allow_common and is_common_password(password):
            errors.append("Password is too common and easily guessable")

        # Username/email similarity check
        if not self.policy.allow_username:
            if user_email and user_email.lower() in password.lower():
                errors.append("Password must not contain your email address")
            if user_name and user_name.lower() in password.lower():
                errors.append("Password must not contain your name")

        return (len(errors) == 0, errors)

    async def validate_history(self, db: AsyncSession, user_id: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """
        Check if password has been used before (password history).

        Args:
            db: Database session
            user_id: User ID to check history for
            new_password: New password to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.policy.history_count == 0:
            return (True, None)

        from app.models import PasswordHistory

        # Get last N password hashes
        query = select(PasswordHistory).where(
            PasswordHistory.user_id == user_id
        ).order_by(PasswordHistory.created_at.desc()).limit(self.policy.history_count)

        result = await db.execute(query)
        history = result.scalars().all()

        # Check if new password matches any historical password
        for hist in history:
            if verify_password(new_password, hist.hashed_password):
                return (False, f"Password has been used recently. Please choose a different password (last {self.policy.history_count} passwords are blocked)")

        return (True, None)

    async def validate_full(
        self,
        db: AsyncSession,
        password: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Perform full password validation including strength and history checks.

        Args:
            db: Database session
            password: Password to validate
            user_id: Optional user ID for history checking
            user_email: Optional user email for similarity checking
            user_name: Optional user name for similarity checking

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        # Strength validation
        is_valid, errors = self.validate_strength(password, user_email, user_name)

        # History validation (only if user_id provided)
        if user_id:
            history_valid, history_error = await self.validate_history(db, user_id, password)
            if not history_valid and history_error:
                errors.append(history_error)
                is_valid = False

        return (is_valid, errors)

    def get_policy_description(self) -> dict:
        """
        Get human-readable description of password policy.
        Useful for displaying requirements to users.

        Returns:
            Dictionary with policy requirements
        """
        requirements = []

        requirements.append(f"Must be between {self.policy.min_length} and {self.policy.max_length} characters")

        if self.policy.require_uppercase:
            requirements.append("Must contain at least one uppercase letter (A-Z)")

        if self.policy.require_lowercase:
            requirements.append("Must contain at least one lowercase letter (a-z)")

        if self.policy.require_digit:
            requirements.append("Must contain at least one digit (0-9)")

        if self.policy.require_special_char:
            requirements.append("Must contain at least one special character (!@#$%^&*...)")

        if self.policy.min_unique_chars > 0:
            requirements.append(f"Must contain at least {self.policy.min_unique_chars} unique characters")

        if self.policy.max_repeating_chars > 0:
            requirements.append(f"Must not have more than {self.policy.max_repeating_chars} consecutive repeating characters")

        if not self.policy.allow_common:
            requirements.append("Must not be a commonly used password")

        if not self.policy.allow_username:
            requirements.append("Must not contain your email address or name")

        if self.policy.history_count > 0:
            requirements.append(f"Must not match your last {self.policy.history_count} passwords")

        if self.policy.expiration_days > 0:
            requirements.append(f"Must be changed every {self.policy.expiration_days} days")

        return {
            "requirements": requirements,
            "expiration_days": self.policy.expiration_days,
            "warning_days": self.policy.expiration_warning_days,
            "grace_logins": self.policy.grace_logins,
        }


async def validate_password(
    db: AsyncSession,
    password: str,
    policy: PasswordPolicyConfig,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    user_name: Optional[str] = None,
    raise_on_error: bool = False
) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate a password against a policy.

    Args:
        db: Database session
        password: Password to validate
        policy: Password policy configuration
        user_id: Optional user ID for history checking
        user_email: Optional user email for similarity checking
        user_name: Optional user name for similarity checking
        raise_on_error: If True, raises PasswordValidationError on validation failure

    Returns:
        Tuple of (is_valid, list_of_errors)

    Raises:
        PasswordValidationError: If raise_on_error=True and validation fails
    """
    validator = PasswordValidator(policy)
    is_valid, errors = await validator.validate_full(db, password, user_id, user_email, user_name)

    if not is_valid and raise_on_error:
        raise PasswordValidationError(errors)

    return (is_valid, errors)
