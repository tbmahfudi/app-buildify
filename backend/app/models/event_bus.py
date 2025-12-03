from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .base import GUID, Base, generate_uuid


class Event(Base):
    """
    Unlogged table for high-performance event storage.
    Events are temporary and can be lost on PostgreSQL crash.
    This is acceptable as events can be republished from source.

    Note: This table should be created as UNLOGGED via migration:
    CREATE UNLOGGED TABLE events (...);
    """
    __tablename__ = "events"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Event identification
    event_type = Column(String(255), nullable=False, index=True)  # e.g., 'financial.invoice.created'
    event_source = Column(String(100), nullable=False)  # e.g., 'financial-module'

    # Event data
    payload = Column(JSONB, nullable=False)  # Event payload as JSON

    # Routing context
    tenant_id = Column(GUID, nullable=False, index=True)  # Tenant isolation
    company_id = Column(GUID, nullable=True)  # Optional company context
    user_id = Column(GUID, nullable=True)  # Optional user context

    # Processing status
    status = Column(String(20), nullable=False, default='pending', index=True)
    # Status values: 'pending', 'processing', 'completed', 'failed'

    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    processed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False, index=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    last_error_at = Column(DateTime, nullable=True)

    # Table args for indexes
    __table_args__ = (
        # Partial index for pending events (most common query)
        Index('idx_events_pending', 'created_at', postgresql_where=(status == 'pending')),
        Index('idx_events_status_pending', 'status', postgresql_where=(status.in_(['pending', 'processing']))),
    )

    def __repr__(self):
        return f"<Event(id={self.id}, type={self.event_type}, status={self.status})>"


class EventSubscription(Base):
    """
    Persistent table for event subscriptions.
    Defines which modules/handlers should receive which events.
    """
    __tablename__ = "event_subscriptions"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Subscriber identification
    module_name = Column(String(100), nullable=False, index=True)  # e.g., 'notification-module'
    handler_name = Column(String(255), nullable=False)  # e.g., 'send_invoice_notification'

    # Event pattern matching (supports wildcards)
    event_pattern = Column(String(255), nullable=False, index=True)
    # Examples: 'financial.invoice.created', 'financial.invoice.*', 'financial.*', '*'

    # Filtering (optional)
    tenant_id = Column(GUID, nullable=True)  # Subscribe only to specific tenant
    filter_conditions = Column(JSONB, nullable=True)  # Additional JSON filters

    # Configuration
    is_active = Column(String(20), nullable=False, default=True, index=True)
    priority = Column(Integer, nullable=False, default=5)  # 1-10, higher = processed first

    # Delivery settings
    delivery_mode = Column(String(20), nullable=False, default='async')  # 'async' or 'sync'
    max_retry_attempts = Column(Integer, nullable=False, default=3)
    retry_delay_seconds = Column(Integer, nullable=False, default=60)

    # Callback configuration
    callback_url = Column(String(500), nullable=True)  # For remote modules
    callback_method = Column(String(255), nullable=True)  # Python import path for local handlers

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_triggered_at = Column(DateTime, nullable=True)

    # Statistics
    total_events_processed = Column(Integer, nullable=False, default=0)
    total_events_failed = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<EventSubscription(module={self.module_name}, pattern={self.event_pattern}, active={self.is_active})>"


class EventHandler(Base):
    """
    Track which handlers have processed which events.
    Provides idempotency and retry tracking.
    """
    __tablename__ = "event_handlers"

    # Primary key
    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Foreign keys
    event_id = Column(GUID, nullable=False, index=True)  # References events.id
    subscription_id = Column(GUID, ForeignKey("event_subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Processing status
    status = Column(String(20), nullable=False, default='pending', index=True)
    # Status values: 'pending', 'completed', 'failed', 'skipped'

    retry_count = Column(Integer, nullable=False, default=0)

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)

    # Relationships
    subscription = relationship("EventSubscription", backref="handlers")

    # Table args for unique constraint
    __table_args__ = (
        Index('uq_event_handler', 'event_id', 'subscription_id', unique=True),
        Index('idx_event_handlers_pending', 'subscription_id', 'status',
              postgresql_where=(status.in_(['pending', 'failed']))),
    )

    def __repr__(self):
        return f"<EventHandler(event_id={self.event_id}, subscription_id={self.subscription_id}, status={self.status})>"


class EventArchive(Base):
    """
    Persistent archive for completed events.
    Used for analytics and audit purposes.
    """
    __tablename__ = "events_archive"

    # Primary key
    id = Column(GUID, primary_key=True)  # Same as original event ID

    # Event data (copied from events table)
    event_type = Column(String(255), nullable=False, index=True)
    event_source = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False)

    # Context
    tenant_id = Column(GUID, nullable=False, index=True)
    company_id = Column(GUID, nullable=True)
    user_id = Column(GUID, nullable=True)

    # Processing info
    status = Column(String(20), nullable=False)
    retry_count = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=False, server_default=func.now())

    # Error info (if failed)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<EventArchive(id={self.id}, type={self.event_type}, archived_at={self.archived_at})>"
