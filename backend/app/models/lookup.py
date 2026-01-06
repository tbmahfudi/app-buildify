"""
Lookup Configuration - Database Models

Models for the no-code platform's lookup/reference configuration feature.
Enables comprehensive configuration for dropdown fields and data relationships.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import GUID, Base, generate_uuid


class LookupConfiguration(Base):
    """
    Lookup Configuration Model

    Stores configuration for dropdown fields, reference fields, and data lookups.
    """
    __tablename__ = "lookup_configurations"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    # tenant_id: NULL = platform-level (shared across tenants), specific ID = tenant-specific
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=True, index=True)

    # Basic Info
    name = Column(String(100), nullable=False)
    label = Column(String(200), nullable=False)
    description = Column(Text)

    # Source Configuration
    source_type = Column(String(50), nullable=False)  # 'entity', 'custom_query', 'static_list', 'api'

    # Entity Source
    source_entity_id = Column(GUID, ForeignKey("entity_definitions.id"))
    display_field = Column(String(100))  # Field to show in dropdown
    value_field = Column(String(100), default="id")  # Field to use as value
    additional_display_fields = Column(JSONB, default=list)  # Additional fields to show

    # Query Configuration
    custom_query = Column(Text)  # Custom SQL query for advanced scenarios
    query_parameters = Column(JSONB, default=dict)

    # Static List Source
    static_options = Column(JSONB, default=list)  # [{value, label, metadata}]

    # API Source
    api_endpoint = Column(String(500))
    api_method = Column(String(10), default="GET")
    api_headers = Column(JSONB, default=dict)
    api_response_mapping = Column(JSONB, default=dict)  # How to map API response

    # Filtering
    default_filter = Column(JSONB, default=dict)  # Default WHERE conditions
    allow_user_filter = Column(Boolean, default=True)
    filter_fields = Column(JSONB, default=list)  # Fields available for filtering

    # Sorting
    default_sort_field = Column(String(100))
    default_sort_order = Column(String(10), default="ASC")
    allow_user_sort = Column(Boolean, default=True)

    # Display Configuration
    display_template = Column(String(500))  # Template for displaying items
    placeholder_text = Column(String(200))
    empty_message = Column(String(200), default="No options available")

    # Search Configuration
    enable_search = Column(Boolean, default=True)
    search_fields = Column(JSONB, default=list)  # Fields to search in
    min_search_length = Column(Integer, default=3)
    search_debounce_ms = Column(Integer, default=300)

    # Autocomplete Configuration
    enable_autocomplete = Column(Boolean, default=False)
    autocomplete_min_chars = Column(Integer, default=2)
    autocomplete_max_results = Column(Integer, default=10)

    # Performance
    enable_caching = Column(Boolean, default=True)
    cache_ttl_seconds = Column(Integer, default=3600)
    lazy_load = Column(Boolean, default=False)  # Load on demand vs preload
    page_size = Column(Integer, default=50)

    # Dependency Configuration
    is_dependent = Column(Boolean, default=False)
    parent_lookup_id = Column(GUID, ForeignKey("lookup_configurations.id"))
    dependency_mapping = Column(JSONB, default=dict)  # How parent value affects this lookup

    # Advanced Features
    allow_create_new = Column(Boolean, default=False)  # Allow creating new options inline
    create_entity_id = Column(GUID, ForeignKey("entity_definitions.id"))  # Entity to create in

    allow_multiple = Column(Boolean, default=False)  # Multi-select
    max_selections = Column(Integer)

    # Metadata
    meta_data = Column(JSONB, default=dict)

    # Status
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(GUID, ForeignKey("users.id"))
    updated_by = Column(GUID, ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False)

    # Relationships
    cache_entries = relationship("LookupCache", back_populates="lookup", cascade="all, delete-orphan")
    parent_rules = relationship("CascadingLookupRule", foreign_keys="CascadingLookupRule.parent_lookup_id", back_populates="parent_lookup")
    child_rules = relationship("CascadingLookupRule", foreign_keys="CascadingLookupRule.child_lookup_id", back_populates="child_lookup")

    # Table constraints
    __table_args__ = (
        Index("idx_lookup_configurations_tenant", "tenant_id", postgresql_where=text("is_deleted = false")),
        Index("idx_lookup_configurations_source_entity", "source_entity_id"),
        Index("idx_lookup_configurations_parent", "parent_lookup_id", postgresql_where=text("is_dependent = true")),
    )


class LookupCache(Base):
    """
    Lookup Cache Model

    Caches lookup data for performance optimization.
    """
    __tablename__ = "lookup_cache"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    lookup_id = Column(GUID, ForeignKey("lookup_configurations.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False)

    # Cache Key
    cache_key = Column(String(255), nullable=False)  # Hash of query parameters

    # Cached Data
    cached_data = Column(JSONB, nullable=False)  # The actual lookup data
    record_count = Column(Integer)

    # Cache Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    hit_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    lookup = relationship("LookupConfiguration", back_populates="cache_entries")

    # Table constraints
    __table_args__ = (
        Index("idx_lookup_cache_lookup", "lookup_id"),
        Index("idx_lookup_cache_expires", "expires_at"),
        Index("idx_lookup_cache_key", "cache_key"),
    )


class CascadingLookupRule(Base):
    """
    Cascading Lookup Rule Model

    Defines parent-child relationships between lookup configurations
    for cascading dropdown functionality.
    """
    __tablename__ = "cascading_lookup_rules"

    # Primary Key
    id = Column(GUID, primary_key=True, default=generate_uuid)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False)

    # Basic Info
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Parent-Child Relationship
    parent_lookup_id = Column(GUID, ForeignKey("lookup_configurations.id"), nullable=False, index=True)
    child_lookup_id = Column(GUID, ForeignKey("lookup_configurations.id"), nullable=False, index=True)

    # Filtering Rule
    filter_type = Column(String(50), default="field_match")  # 'field_match', 'custom_query', 'function'
    parent_field = Column(String(100))  # Field in parent that drives filtering
    child_filter_field = Column(String(100))  # Field in child to filter on

    # Custom Filter
    custom_filter_expression = Column(Text)  # Advanced filtering logic

    # Behavior
    clear_on_parent_change = Column(Boolean, default=True)
    auto_select_if_single = Column(Boolean, default=False)  # Auto-select if only one option

    # Status
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(GUID, ForeignKey("users.id"))

    # Relationships
    parent_lookup = relationship("LookupConfiguration", foreign_keys=[parent_lookup_id], back_populates="parent_rules")
    child_lookup = relationship("LookupConfiguration", foreign_keys=[child_lookup_id], back_populates="child_rules")

    # Table constraints
    __table_args__ = (
        Index("idx_cascading_lookup_rules_parent", "parent_lookup_id"),
        Index("idx_cascading_lookup_rules_child", "child_lookup_id"),
    )
