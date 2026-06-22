# Platform SDK — database base classes
# Module code imports from here; never from backend.app directly.
from app.models.base import Base, GUID, generate_uuid

__all__ = ["Base", "GUID", "generate_uuid"]
