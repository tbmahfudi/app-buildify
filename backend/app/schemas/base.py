"""
Base schemas with common utilities for UUID serialization.
"""
from typing import Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel, field_validator, field_serializer, model_validator


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
    Mixin to add automatic UUID serialization for all UUID fields.

    Automatically converts ALL UUID objects to strings in the model data,
    without needing to explicitly list field names.

    Uses model_validator with mode='before' to inspect all incoming data
    and convert any UUID values to strings before Pydantic validates types.

    Usage:
        class MyResponse(UUIDMixin, BaseModel):
            id: str
            user_id: str
            company_id: str
            # ... any UUID field will be automatically converted
    """

    @model_validator(mode='before')
    @classmethod
    def convert_all_uuids_to_str(cls, data: Any) -> Any:
        """
        Automatically convert all UUID values to strings.

        This validator inspects all values in the incoming data and converts
        any UUID objects to strings, regardless of field name.
        """
        if not isinstance(data, dict):
            return data

        # Create a new dict with converted values
        converted_data = {}
        for key, value in data.items():
            if isinstance(value, UUID):
                converted_data[key] = str(value)
            else:
                converted_data[key] = value

        return converted_data


class BaseResponse(UUIDMixin, BaseModel):
    """
    Base response schema with UUID serialization and common config.

    All response schemas should inherit from this to get:
    - Automatic UUID serialization for common fields
    - from_attributes = True for ORM compatibility
    """

    class Config:
        from_attributes = True
