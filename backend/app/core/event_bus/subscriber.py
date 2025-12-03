"""
Event Subscriber for PostgreSQL Event Bus

Subscribes to events using PostgreSQL LISTEN/NOTIFY for real-time processing.
"""

import asyncio
import json
import re
from typing import Callable, Dict, List, Optional

import psycopg
from psycopg import AsyncConnection
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event_bus import Event, EventSubscription


class EventSubscriber:
    """
    Subscribes to events and processes them using PostgreSQL LISTEN/NOTIFY.

    Provides real-time event processing with pattern matching support.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        module_name: str,
        connection_string: str
    ):
        """
        Initialize event subscriber.

        Args:
            db_session: SQLAlchemy async session
            module_name: Name of the subscribing module
            connection_string: PostgreSQL connection string for LISTEN
        """
        self.db = db_session
        self.module_name = module_name
        self.connection_string = connection_string
        self.handlers: Dict[str, List[Dict]] = {}
        self._listening = False
        self._listen_conn: Optional[AsyncConnection] = None
        self._listen_task: Optional[asyncio.Task] = None

    def subscribe(
        self,
        event_pattern: str,
        handler: Callable,
        priority: int = 5,
        filter_tenant_id: Optional[str] = None
    ):
        """
        Register a handler for an event pattern.

        Args:
            event_pattern: Event pattern with wildcard support
                Examples: 'financial.invoice.created', 'financial.invoice.*', 'financial.*', '*'
            handler: Async function to handle the event
            priority: Handler priority (1-10, higher = executed first)
            filter_tenant_id: Optional tenant ID filter

        Example:
            >>> subscriber = EventSubscriber(db, "notification-module", conn_str)
            >>> @subscriber.subscribe("financial.invoice.created", priority=8)
            >>> async def send_invoice_email(event):
            ...     await send_email(event['payload']['customer_email'])
        """
        if event_pattern not in self.handlers:
            self.handlers[event_pattern] = []

        self.handlers[event_pattern].append({
            'handler': handler,
            'priority': priority,
            'tenant_filter': filter_tenant_id
        })

        # Sort handlers by priority (descending)
        self.handlers[event_pattern].sort(
            key=lambda x: x['priority'],
            reverse=True
        )

    async def start_listening(self, channels: Optional[List[str]] = None):
        """
        Start listening for PostgreSQL NOTIFY events.

        Args:
            channels: List of channels to listen on. If None, listens on 'events' channel.
        """
        if self._listening:
            return

        if channels is None:
            channels = ['events']

        # Create dedicated connection for LISTEN
        self._listen_conn = await psycopg.AsyncConnection.connect(
            self.connection_string,
            autocommit=True
        )

        # Start listening on all specified channels
        for channel in channels:
            await self._listen_conn.execute(f'LISTEN "{channel}"')

        self._listening = True

        # Start background listening loop
        self._listen_task = asyncio.create_task(self._listen_loop())

    async def _listen_loop(self):
        """Background loop to listen for NOTIFY events."""
        if not self._listen_conn:
            return

        try:
            async for notify in self._listen_conn.notifies():
                if not self._listening:
                    break

                # Process the notification
                event_id = notify.payload
                await self._process_event(event_id)

        except Exception as e:
            print(f"Error in LISTEN loop: {e}")
        finally:
            self._listening = False

    async def _process_event(self, event_id: str):
        """
        Process a single event.

        Args:
            event_id: UUID of the event to process
        """
        try:
            # Fetch event from database
            query = text("""
                SELECT id, event_type, payload, tenant_id, company_id, user_id, event_source
                FROM events
                WHERE id = :event_id AND status = 'pending'
            """)

            result = await self.db.execute(query, {"event_id": event_id})
            event_row = result.fetchone()

            if not event_row:
                return  # Event already processed or doesn't exist

            # Convert to dictionary
            event = {
                'id': event_row.id,
                'type': event_row.event_type,
                'payload': event_row.payload if isinstance(event_row.payload, dict) else json.loads(event_row.payload),
                'tenant_id': event_row.tenant_id,
                'company_id': event_row.company_id,
                'user_id': event_row.user_id,
                'source': event_row.event_source
            }

            # Find matching handlers
            matching_handlers = self._find_handlers(event['type'], event.get('tenant_id'))

            # Execute all matching handlers
            for handler_info in matching_handlers:
                try:
                    await handler_info['handler'](event)
                except Exception as e:
                    # Log error but continue processing other handlers
                    print(f"Error in event handler: {e}")
                    # You might want to record this failure in event_handlers table

        except Exception as e:
            print(f"Error processing event {event_id}: {e}")

    def _find_handlers(self, event_type: str, tenant_id: Optional[str] = None) -> List[Dict]:
        """
        Find handlers that match the event type and filters.

        Args:
            event_type: The event type to match
            tenant_id: Optional tenant ID for filtering

        Returns:
            List of matching handler info dictionaries
        """
        matching = []

        for pattern, handlers in self.handlers.items():
            if self._matches_pattern(event_type, pattern):
                for handler_info in handlers:
                    # Check tenant filter
                    if handler_info.get('tenant_filter'):
                        if str(handler_info['tenant_filter']) != str(tenant_id):
                            continue

                    matching.append(handler_info)

        # Sort by priority (descending)
        matching.sort(key=lambda x: x['priority'], reverse=True)
        return matching

    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """
        Check if event_type matches pattern (supports wildcards).

        Patterns:
            - Exact match: 'financial.invoice.created'
            - Wildcard segment: 'financial.invoice.*' matches 'financial.invoice.created'
            - Wildcard category: 'financial.*' matches any event starting with 'financial.'
            - Global: '*' matches everything

        Args:
            event_type: The event type (e.g., 'financial.invoice.created')
            pattern: The pattern to match against

        Returns:
            bool: True if event_type matches pattern
        """
        if pattern == "*":
            return True

        if "*" not in pattern:
            return event_type == pattern

        # Convert pattern to regex
        # Replace '.' with '\.' and '*' with '[^.]*'
        regex_pattern = pattern.replace('.', r'\.')
        regex_pattern = regex_pattern.replace('*', r'[^.]*')
        regex_pattern = f"^{regex_pattern}$"

        return bool(re.match(regex_pattern, event_type))

    async def register_subscription(
        self,
        event_pattern: str,
        handler_name: str,
        priority: int = 5,
        callback_url: Optional[str] = None,
        callback_method: Optional[str] = None
    ) -> EventSubscription:
        """
        Register a subscription in the database for persistence.

        This allows subscriptions to survive application restarts.

        Args:
            event_pattern: Event pattern to subscribe to
            handler_name: Name of the handler function
            priority: Priority level (1-10)
            callback_url: URL for remote module callback
            callback_method: Python import path for local handler

        Returns:
            EventSubscription: The created subscription

        Example:
            >>> subscription = await subscriber.register_subscription(
            ...     event_pattern="financial.invoice.*",
            ...     handler_name="process_invoice_event",
            ...     callback_method="app.handlers.invoice.process_invoice_event"
            ... )
        """
        subscription = EventSubscription(
            module_name=self.module_name,
            handler_name=handler_name,
            event_pattern=event_pattern,
            priority=priority,
            callback_url=callback_url,
            callback_method=callback_method,
            is_active=True
        )

        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)

        return subscription

    async def stop_listening(self):
        """Stop listening for events and cleanup resources."""
        self._listening = False

        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        if self._listen_conn:
            await self._listen_conn.close()
            self._listen_conn = None


# Decorator for easy handler registration
class EventHandler:
    """
    Decorator for registering event handlers.

    Example:
        >>> subscriber = EventSubscriber(db, "my-module", conn_str)
        >>> handler = EventHandler(subscriber)
        >>>
        >>> @handler.on("financial.invoice.created", priority=8)
        >>> async def handle_invoice_created(event):
        ...     print(f"Invoice created: {event['payload']['invoice_id']}")
    """

    def __init__(self, subscriber: EventSubscriber):
        self.subscriber = subscriber

    def on(self, event_pattern: str, priority: int = 5, tenant_id: Optional[str] = None):
        """
        Decorator to register an event handler.

        Args:
            event_pattern: Event pattern to match
            priority: Handler priority
            tenant_id: Optional tenant filter
        """
        def decorator(func: Callable):
            self.subscriber.subscribe(
                event_pattern=event_pattern,
                handler=func,
                priority=priority,
                filter_tenant_id=tenant_id
            )
            return func

        return decorator
