"""
Field Type Mapper - Maps EntityDefinition field types to SQLAlchemy column types

This module provides utilities to convert nocode field type definitions
into SQLAlchemy column types and Python native types.
"""

from typing import Any, Type, Optional
from sqlalchemy import (
    Column, String, Integer, BigInteger, Float, Boolean,
    DateTime, Date, Time, Text, JSON, ARRAY, Numeric, UUID
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from decimal import Decimal
from datetime import datetime, date, time
import uuid


class FieldTypeMapper:
    """Maps field types between different representations"""

    # Map EntityDefinition field_type to SQLAlchemy column type
    SQLALCHEMY_TYPE_MAP = {
        # String types
        'string': lambda field: String(field.get('max_length', 255)),
        'email': lambda field: String(255),
        'url': lambda field: String(512),
        'phone': lambda field: String(20),
        'text': lambda field: Text,
        'textarea': lambda field: Text,

        # Numeric types
        'integer': lambda field: Integer,
        'bigint': lambda field: BigInteger,
        'decimal': lambda field: Numeric(
            precision=field.get('precision', 10),
            scale=field.get('scale', 2)
        ),
        'float': lambda field: Float,
        'money': lambda field: Numeric(precision=19, scale=4),

        # Boolean
        'boolean': lambda field: Boolean,
        'checkbox': lambda field: Boolean,

        # Date/Time types
        'date': lambda field: Date,
        'datetime': lambda field: DateTime,
        'time': lambda field: Time,
        'timestamp': lambda field: DateTime,

        # UUID
        'uuid': lambda field: PG_UUID(as_uuid=True),

        # JSON
        'json': lambda field: JSON,
        'jsonb': lambda field: JSON,

        # Special types
        'array': lambda field: ARRAY(String),
        'enum': lambda field: String(255),  # Stored as string, validated in app
        'lookup': lambda field: String(36),  # FK as UUID string
        'reference': lambda field: String(36),  # FK as UUID string
    }

    # Map EntityDefinition field_type to Python native type
    PYTHON_TYPE_MAP = {
        'string': str,
        'email': str,
        'url': str,
        'phone': str,
        'text': str,
        'textarea': str,
        'integer': int,
        'bigint': int,
        'decimal': Decimal,
        'float': float,
        'money': Decimal,
        'boolean': bool,
        'checkbox': bool,
        'date': date,
        'datetime': datetime,
        'time': time,
        'timestamp': datetime,
        'uuid': uuid.UUID,
        'json': dict,
        'jsonb': dict,
        'array': list,
        'enum': str,
        'lookup': str,
        'reference': str,
    }

    # Map EntityDefinition field_type to JSON schema type (for Pydantic)
    JSON_SCHEMA_TYPE_MAP = {
        'string': 'string',
        'email': 'string',
        'url': 'string',
        'phone': 'string',
        'text': 'string',
        'textarea': 'string',
        'integer': 'integer',
        'bigint': 'integer',
        'decimal': 'number',
        'float': 'number',
        'money': 'number',
        'boolean': 'boolean',
        'checkbox': 'boolean',
        'date': 'string',  # ISO format
        'datetime': 'string',  # ISO format
        'time': 'string',  # ISO format
        'timestamp': 'string',  # ISO format
        'uuid': 'string',  # UUID format
        'json': 'object',
        'jsonb': 'object',
        'array': 'array',
        'enum': 'string',
        'lookup': 'string',
        'reference': 'string',
    }

    @classmethod
    def to_sqlalchemy_column(
        cls,
        field_definition: dict,
        include_foreign_key: bool = True
    ) -> Column:
        """
        Convert FieldDefinition to SQLAlchemy Column

        Args:
            field_definition: Dict with field metadata (name, field_type, is_required, etc.)
            include_foreign_key: Whether to include ForeignKey constraint for lookup fields

        Returns:
            SQLAlchemy Column object
        """
        field_type = field_definition.get('field_type', 'string')
        field_name = field_definition.get('db_column_name') or field_definition.get('name')

        # Get SQLAlchemy type
        type_func = cls.SQLALCHEMY_TYPE_MAP.get(field_type)
        if not type_func:
            # Default to String if type not found
            type_func = lambda f: String(255)

        col_type = type_func(field_definition)

        # Build column arguments
        col_args = []
        col_kwargs = {
            'nullable': not field_definition.get('is_required', False),
            'primary_key': field_definition.get('is_primary_key', False),
            'unique': field_definition.get('is_unique', False),
            'index': field_definition.get('is_indexed', False),
        }

        # Add default value if specified
        if 'default_value' in field_definition and field_definition['default_value'] is not None:
            col_kwargs['default'] = field_definition['default_value']

        # Handle foreign keys for lookup/reference fields
        if include_foreign_key and field_type in ('lookup', 'reference'):
            lookup_config = field_definition.get('lookup_config', {})
            if lookup_config and 'entity' in lookup_config:
                target_entity = lookup_config['entity']
                # ForeignKey format: schema.table.column
                fk_target = f"public.{target_entity}.id"  # Assuming 'id' is the target column
                from sqlalchemy import ForeignKey
                col_args.append(ForeignKey(fk_target))

        return Column(field_name, col_type, *col_args, **col_kwargs)

    @classmethod
    def to_python_type(cls, field_type: str) -> Type:
        """Get Python native type for field type"""
        return cls.PYTHON_TYPE_MAP.get(field_type, str)

    @classmethod
    def to_json_schema_type(cls, field_type: str) -> str:
        """Get JSON schema type for field type (used in Pydantic)"""
        return cls.JSON_SCHEMA_TYPE_MAP.get(field_type, 'string')

    @classmethod
    def validate_value(cls, field_definition: dict, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a value against field definition rules

        Args:
            field_definition: Dict with field metadata
            value: Value to validate

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        field_type = field_definition.get('field_type', 'string')
        field_label = field_definition.get('label', field_definition.get('name'))

        # Required check
        if field_definition.get('is_required', False) and value is None:
            return False, f"{field_label} is required"

        # Skip further validation if value is None and field is not required
        if value is None:
            return True, None

        # Type validation
        expected_type = cls.to_python_type(field_type)

        # Handle special cases
        if field_type in ('date', 'datetime', 'time', 'timestamp'):
            # Accept both datetime objects and ISO strings
            if not isinstance(value, (str, datetime, date, time)):
                return False, f"{field_label} must be a valid date/time"
        elif field_type == 'uuid':
            # Accept UUID objects or valid UUID strings
            if isinstance(value, str):
                try:
                    uuid.UUID(value)
                except ValueError:
                    return False, f"{field_label} must be a valid UUID"
            elif not isinstance(value, uuid.UUID):
                return False, f"{field_label} must be a valid UUID"
        elif field_type in ('json', 'jsonb'):
            # Accept dict or list
            if not isinstance(value, (dict, list)):
                return False, f"{field_label} must be a valid JSON object or array"
        elif field_type == 'array':
            if not isinstance(value, list):
                return False, f"{field_label} must be an array"
        else:
            # Standard type check
            if not isinstance(value, expected_type):
                try:
                    # Try to convert
                    expected_type(value)
                except (ValueError, TypeError):
                    return False, f"{field_label} must be of type {expected_type.__name__}"

        # Min/Max value validation (for numeric types)
        if field_type in ('integer', 'bigint', 'decimal', 'float', 'money'):
            if 'min_value' in field_definition and value < field_definition['min_value']:
                return False, f"{field_label} must be >= {field_definition['min_value']}"

            if 'max_value' in field_definition and value > field_definition['max_value']:
                return False, f"{field_label} must be <= {field_definition['max_value']}"

        # Length validation (for string types)
        if field_type in ('string', 'email', 'url', 'phone'):
            if isinstance(value, str):
                max_length = field_definition.get('max_length', 255)
                if len(value) > max_length:
                    return False, f"{field_label} must be <= {max_length} characters"

                if 'min_length' in field_definition and len(value) < field_definition['min_length']:
                    return False, f"{field_label} must be >= {field_definition['min_length']} characters"

        # Email format validation
        if field_type == 'email' and isinstance(value, str):
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                return False, f"{field_label} must be a valid email address"

        # URL format validation
        if field_type == 'url' and isinstance(value, str):
            import re
            url_pattern = r'^https?://'
            if not re.match(url_pattern, value):
                return False, f"{field_label} must be a valid URL starting with http:// or https://"

        # Enum validation
        if field_type == 'enum':
            allowed_values = field_definition.get('allowed_values', [])
            if allowed_values and value not in allowed_values:
                return False, f"{field_label} must be one of: {', '.join(map(str, allowed_values))}"

        # Custom validation rules (from field_definition.validation_rules JSON)
        validation_rules = field_definition.get('validation_rules')
        if validation_rules:
            # validation_rules is a JSON object with custom rules
            # Example: {"pattern": "^[A-Z]{3}-\\d{4}$", "message": "Must match format XXX-1234"}
            if isinstance(validation_rules, dict):
                if 'pattern' in validation_rules and isinstance(value, str):
                    import re
                    pattern = validation_rules['pattern']
                    if not re.match(pattern, value):
                        error_msg = validation_rules.get('message', f"{field_label} format is invalid")
                        return False, error_msg

        return True, None

    @classmethod
    def serialize_value(cls, field_type: str, value: Any) -> Any:
        """
        Serialize value for JSON response

        Converts Python objects to JSON-serializable types
        """
        if value is None:
            return None

        if field_type in ('date', 'datetime', 'time', 'timestamp'):
            if isinstance(value, (datetime, date, time)):
                return value.isoformat()

        if field_type == 'uuid':
            if isinstance(value, uuid.UUID):
                return str(value)

        if field_type in ('decimal', 'money'):
            if isinstance(value, Decimal):
                return float(value)

        # All other types are already JSON-serializable
        return value

    @classmethod
    def deserialize_value(cls, field_type: str, value: Any) -> Any:
        """
        Deserialize value from JSON request

        Converts JSON types to Python objects
        """
        if value is None:
            return None

        if field_type == 'date' and isinstance(value, str):
            return datetime.fromisoformat(value).date()

        if field_type in ('datetime', 'timestamp') and isinstance(value, str):
            return datetime.fromisoformat(value)

        if field_type == 'time' and isinstance(value, str):
            return datetime.fromisoformat(f"2000-01-01T{value}").time()

        if field_type == 'uuid' and isinstance(value, str):
            return uuid.UUID(value)

        if field_type in ('decimal', 'money'):
            return Decimal(str(value))

        # All other types remain as-is
        return value
