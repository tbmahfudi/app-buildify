"""
PostgreSQL Event Bus

Minimal event bus implementation using PostgreSQL for inter-module communication.

Components:
- EventPublisher: Publish events to unlogged table
- EventSubscriber: Subscribe to events using LISTEN/NOTIFY
- EventProcessor: Background worker for polling fallback

Features:
- Real-time delivery via LISTEN/NOTIFY
- Fallback polling for reliability
- Pattern matching for subscriptions
- Automatic cleanup and archival
"""

from .publisher import EventPublisher, get_event_publisher
from .subscriber import EventHandler, EventSubscriber

__all__ = [
    "EventPublisher",
    "EventSubscriber",
    "EventHandler",
    "get_event_publisher",
]
