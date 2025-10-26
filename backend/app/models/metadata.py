from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, func
from .base import Base, GUID, generate_uuid


class EntityMetadata(Base):
    """Stores metadata definitions for entities"""
    __tablename__ = "entity_metadata"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Entity identifier
    entity_name = Column(String(100), unique=True, nullable=False, index=True)

    # Display info
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)

    # Table configuration (JSON)
    table_config = Column(Text, nullable=True)  # JSON: columns, filters, sort

    # Form configuration (JSON)
    form_config = Column(Text, nullable=True)  # JSON: fields, validation, layout

    # RBAC permissions (JSON)
    permissions = Column(Text, nullable=True)  # JSON: {role: [actions]}

    # Version control
    version = Column(Integer, default=1, nullable=False)

    # Flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # System entities can't be deleted

    # Audit
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    created_by = Column(GUID, nullable=True)
    updated_by = Column(GUID, nullable=True)

    def __repr__(self):
        return f"<EntityMetadata(entity_name={self.entity_name}, display_name={self.display_name})>"
