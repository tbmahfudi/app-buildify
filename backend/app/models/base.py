from sqlalchemy import TypeDecorator, String
from sqlalchemy.orm import declarative_base
import uuid

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
                return uuid.UUID(value) if value else None
        else:
            # MySQL and SQLite need string
            if isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(uuid.UUID(value)) if value else None

    def process_result_value(self, value, dialect):
        """Convert database value to UUID."""
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


def generate_uuid():
    """Generate a new UUID as a string."""
    return str(uuid.uuid4())
