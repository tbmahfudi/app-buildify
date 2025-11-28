import uuid

from sqlalchemy import String, TypeDecorator
from sqlalchemy.orm import declarative_base

# Try to import PostgreSQL UUID type
try:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    HAS_PG_UUID = True
except ImportError:
    HAS_PG_UUID = False

Base = declarative_base()


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses String(36).
    Ensures consistent UUID handling across PostgreSQL, MySQL, and SQLite.
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Load the appropriate type based on the database dialect."""
        if dialect.name == 'postgresql' and HAS_PG_UUID:
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        """Convert UUID to appropriate type for database."""
        if value is None:
            return value
        elif dialect.name == 'postgresql' and HAS_PG_UUID:
            # PostgreSQL can handle UUID objects directly
            if isinstance(value, uuid.UUID):
                return value
            else:
                # Validate the string is a valid UUID before converting
                try:
                    return uuid.UUID(value) if value else None
                except (ValueError, AttributeError, TypeError):
                    # If the value is not a valid UUID string, return None
                    # This handles cases where non-UUID strings (like module names or emails)
                    # are passed to UUID fields
                    return None
        else:
            # MySQL and SQLite need string
            if isinstance(value, uuid.UUID):
                return str(value)
            else:
                # Validate the string is a valid UUID before converting
                try:
                    return str(uuid.UUID(value)) if value else None
                except (ValueError, AttributeError, TypeError):
                    # If the value is not a valid UUID string, return None
                    return None

    def process_result_value(self, value, dialect):
        """Convert database value to UUID."""
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


def generate_uuid():
    """Generate a new UUID object."""
    return uuid.uuid4()
