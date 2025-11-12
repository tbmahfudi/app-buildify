"""
Base schemas with common utilities for UUID serialization.
"""
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, field_serializer


def serialize_uuid_field(value: Any) -> Optional[str]:
    """
    Helper function to serialize UUID objects to strings.

    Args:
        value: UUID object, string, or None

    Returns:
        String representation of UUID or None
    """
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    # If already a string, return as-is
    if isinstance(value, str):
        return value
    # Try to convert to string
    return str(value)


class UUIDMixin:
    """
    Mixin to add UUID serialization for common ID fields.

    Automatically serializes 'id', 'user_id', 'tenant_id', 'created_by', 'updated_by'
    to strings for JSON serialization.

    Usage:
        class MyResponse(UUIDMixin, BaseModel):
            id: str
            user_id: str
            ...
    """

    @field_serializer('id', 'user_id', 'tenant_id', 'created_by', 'updated_by', check_fields=False)
    def serialize_common_uuid_fields(self, value: Any, _info) -> Optional[str]:
        """Serialize common UUID fields to strings."""
        return serialize_uuid_field(value)


class BaseResponse(UUIDMixin, BaseModel):
    """
    Base response schema with UUID serialization and common config.

    All response schemas should inherit from this to get:
    - Automatic UUID serialization for common fields
    - from_attributes = True for ORM compatibility
    """

    class Config:
        from_attributes = True
