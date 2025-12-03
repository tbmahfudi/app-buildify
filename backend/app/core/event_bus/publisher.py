"""
Event Publisher for PostgreSQL Event Bus

Publishes events to the unlogged events table and sends NOTIFY for real-time delivery.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class EventPublisher:
    """
    Publishes events to PostgreSQL event bus.

    Events are stored in an unlogged table for performance and
    notifications are sent via PostgreSQL LISTEN/NOTIFY for real-time delivery.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        tenant_id: UUID | str,
        company_id: Optional[UUID | str] = None,
        user_id: Optional[UUID | str] = None,
        event_source: str = "core-platform",
        ttl_hours: int = 24,
        max_retries: int = 3
    ) -> UUID:
        """
        Publish an event to the event bus.

        Args:
            event_type: Event type (e.g., 'financial.invoice.created')
            payload: Event data as dictionary
            tenant_id: Tenant ID for data isolation
            company_id: Optional company context
            user_id: Optional user context
            event_source: Source module/service name
            ttl_hours: Time-to-live in hours (default: 24)
            max_retries: Maximum retry attempts (default: 3)

        Returns:
            UUID: Event ID

        Example:
            >>> publisher = EventPublisher(db_session)
            >>> event_id = await publisher.publish(
            ...     event_type="financial.invoice.created",
            ...     payload={"invoice_id": "123", "total": 1000.00},
            ...     tenant_id=tenant_id,
            ...     company_id=company_id
            ... )
        """
        event_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

        # Convert UUIDs to strings for JSON serialization
        if isinstance(tenant_id, UUID):
            tenant_id = str(tenant_id)
        if isinstance(company_id, UUID):
            company_id = str(company_id)
        if isinstance(user_id, UUID):
            user_id = str(user_id)

        # Insert event into unlogged table
        query = text("""
            INSERT INTO events (
                id, event_type, event_source, payload,
                tenant_id, company_id, user_id, expires_at, max_retries
            ) VALUES (
                :id, :event_type, :event_source, :payload::jsonb,
                :tenant_id::uuid, :company_id::uuid, :user_id::uuid, :expires_at, :max_retries
            )
        """)

        await self.db.execute(query, {
            "id": str(event_id),
            "event_type": event_type,
            "event_source": event_source,
            "payload": json.dumps(payload),
            "tenant_id": tenant_id,
            "company_id": company_id,
            "user_id": user_id,
            "expires_at": expires_at,
            "max_retries": max_retries
        })

        await self.db.commit()

        # Send NOTIFY for real-time delivery
        await self._notify(event_type, event_id)

        return event_id

    async def publish_batch(
        self,
        events: list[Dict[str, Any]],
        tenant_id: UUID | str,
        event_source: str = "core-platform"
    ) -> list[UUID]:
        """
        Publish multiple events efficiently in a single database operation.

        Args:
            events: List of event dictionaries with 'type' and 'payload'
            tenant_id: Tenant ID for all events
            event_source: Source module/service name

        Returns:
            List of event IDs

        Example:
            >>> events = [
            ...     {"type": "user.created", "payload": {"user_id": "123"}},
            ...     {"type": "user.activated", "payload": {"user_id": "123"}}
            ... ]
            >>> event_ids = await publisher.publish_batch(events, tenant_id)
        """
        if not events:
            return []

        # Convert tenant_id to string
        if isinstance(tenant_id, UUID):
            tenant_id = str(tenant_id)

        # Prepare batch data
        batch_data = []
        event_ids = []

        for event in events:
            event_id = uuid4()
            event_ids.append(event_id)

            batch_data.append({
                "id": str(event_id),
                "event_type": event.get("type"),
                "event_source": event_source,
                "payload": json.dumps(event.get("payload", {})),
                "tenant_id": tenant_id,
                "company_id": event.get("company_id"),
                "user_id": event.get("user_id"),
                "expires_at": datetime.utcnow() + timedelta(hours=24),
                "max_retries": event.get("max_retries", 3)
            })

        # Batch insert
        query = text("""
            INSERT INTO events (
                id, event_type, event_source, payload, tenant_id,
                company_id, user_id, expires_at, max_retries
            )
            SELECT
                (data->>'id')::uuid,
                data->>'event_type',
                data->>'event_source',
                (data->>'payload')::jsonb,
                (data->>'tenant_id')::uuid,
                (data->>'company_id')::uuid,
                (data->>'user_id')::uuid,
                (data->>'expires_at')::timestamp,
                (data->>'max_retries')::integer
            FROM jsonb_array_elements(:batch_data::jsonb) AS data
        """)

        await self.db.execute(query, {"batch_data": json.dumps(batch_data)})
        await self.db.commit()

        # Send notifications for all events
        for event, event_id in zip(events, event_ids):
            await self._notify(event.get("type"), event_id)

        return event_ids

    async def _notify(self, event_type: str, event_id: UUID):
        """
        Send PostgreSQL NOTIFY for real-time event delivery.

        Notifies on multiple channels:
        - 'events' - Global channel for all events
        - 'events:{event_type}' - Specific event type channel
        - 'events:{category}' - Event category channel (e.g., 'events:financial')
        """
        payload = str(event_id)

        # Global channel
        await self._send_notify("events", payload)

        # Specific event type channel
        await self._send_notify(f"events:{event_type}", payload)

        # Category channel (first part of event_type)
        if '.' in event_type:
            category = event_type.split('.')[0]
            await self._send_notify(f"events:{category}", payload)

    async def _send_notify(self, channel: str, payload: str):
        """Send a PostgreSQL NOTIFY command."""
        try:
            # Escape the channel name to prevent SQL injection
            safe_channel = channel.replace('"', '""')
            query = text(f'NOTIFY "{safe_channel}", :payload')
            await self.db.execute(query, {"payload": payload})
        except Exception as e:
            # Log error but don't fail the publish operation
            print(f"Error sending NOTIFY on channel {channel}: {e}")


# Convenience function for dependency injection
def get_event_publisher(db: AsyncSession) -> EventPublisher:
    """Get an EventPublisher instance (for FastAPI dependency injection)."""
    return EventPublisher(db)
