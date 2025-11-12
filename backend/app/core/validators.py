import re
from typing import Any

from pydantic import ValidationInfo, field_validator


class ValidationRules:
    """Common validation rules for the application"""

    # String length constraints
    MAX_NAME_LENGTH = 255
    MAX_DESCRIPTION_LENGTH = 1000
    MAX_CODE_LENGTH = 50
    MAX_EMAIL_LENGTH = 255

    # Pattern validators
    CODE_PATTERN = re.compile(r'^[A-Z0-9_-]+$', re.IGNORECASE)
    UUID_PATTERN = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )

    @staticmethod
    def validate_string_length(value: str, max_length: int, field_name: str) -> str:
        """Validate string length"""
        if value is None:
            return value

        if len(value) > max_length:
            raise ValueError(
                f"{field_name} must not exceed {max_length} characters"
            )

        return value.strip()

    @staticmethod
    def validate_code(value: str) -> str:
        """
        Validate code fields (alphanumeric, underscore, hyphen only).
        Prevents injection attacks.
        """
        if value is None:
            return value

        value = value.strip()

        if not ValidationRules.CODE_PATTERN.match(value):
            raise ValueError(
                "Code must contain only letters, numbers, underscores, and hyphens"
            )

        if len(value) > ValidationRules.MAX_CODE_LENGTH:
            raise ValueError(
                f"Code must not exceed {ValidationRules.MAX_CODE_LENGTH} characters"
            )

        return value

    @staticmethod
    def validate_name(value: str) -> str:
        """Validate name fields"""
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("Name cannot be empty")

        if len(value) > ValidationRules.MAX_NAME_LENGTH:
            raise ValueError(
                f"Name must not exceed {ValidationRules.MAX_NAME_LENGTH} characters"
            )

        # Prevent common injection patterns
        if any(char in value for char in ['<', '>', '{', '}', '\\x00']):
            raise ValueError("Name contains invalid characters")

        return value

    @staticmethod
    def validate_uuid(value: str, field_name: str = "ID") -> str:
        """Validate UUID format"""
        if value is None:
            return value

        value = str(value).strip()

        if not ValidationRules.UUID_PATTERN.match(value):
            raise ValueError(f"{field_name} must be a valid UUID")

        return value

    @staticmethod
    def sanitize_json_field(value: Any) -> Any:
        """
        Sanitize JSON fields to prevent injection.
        Ensures JSON doesn't contain dangerous patterns.
        """
        if value is None:
            return value

        if isinstance(value, str):
            # Check for potential script injection in JSON strings
            dangerous_patterns = [
                '<script',
                'javascript:',
                'onerror=',
                'onclick=',
                'onload=',
            ]

            value_lower = value.lower()
            for pattern in dangerous_patterns:
                if pattern in value_lower:
                    raise ValueError(
                        "JSON content contains potentially dangerous patterns"
                    )

        return value


def create_string_validator(max_length: int, field_name: str = None):
    """
    Factory function to create string length validators.

    Usage in Pydantic models:
        @field_validator('field_name')
        @classmethod
        def validate_field(cls, v):
            return ValidationRules.validate_string_length(v, 100, 'Field Name')
    """
    def validator(cls, value: str, info: ValidationInfo) -> str:
        name = field_name or info.field_name
        return ValidationRules.validate_string_length(value, max_length, name)

    return validator


def create_code_validator():
    """
    Factory function to create code validators.

    Usage in Pydantic models:
        @field_validator('code')
        @classmethod
        def validate_code(cls, v):
            return ValidationRules.validate_code(v)
    """
    def validator(cls, value: str) -> str:
        return ValidationRules.validate_code(value)

    return validator
