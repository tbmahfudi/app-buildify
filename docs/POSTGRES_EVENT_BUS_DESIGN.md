# PostgreSQL Event Bus Design

## Overview

Instead of adding RabbitMQ, Kafka, or Redis for event-driven communication, we'll use **PostgreSQL itself** as the event bus using:

- **Unlogged tables** for high-performance event storage
- **LISTEN/NOTIFY** for real-time event delivery
- **Background workers** for event processing
- **Periodic cleanup** to prevent table bloat

This approach minimizes system complexity while providing reliable event-driven communication between modules.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Event Flow                                │
└─────────────────────────────────────────────────────────────────┘

Module A (Publisher)
    │
    ├─→ INSERT INTO events (unlogged table)
    │
    └─→ NOTIFY event_channel, 'event_id'
            │
            ├─→ Module B (Subscriber) ← Listening on channel
            │       └─→ Process event immediately
            │
            └─→ Module C (Subscriber) ← Listening on channel
                    └─→ Process event immediately

Background Worker (Polling)
    │
    └─→ SELECT * FROM events WHERE status = 'pending'
            └─→ Process events that weren't caught by LISTEN
```

---

## Database Schema

### Events Table (Unlogged)

```sql
-- Unlogged table for high-performance event storage
-- WARNING: Data is lost on PostgreSQL crash, but that's acceptable for events
CREATE UNLOGGED TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event identification
    event_type VARCHAR(255) NOT NULL,          -- e.g., 'financial.invoice.created'
    event_source VARCHAR(100) NOT NULL,         -- e.g., 'financial-module'

    -- Event data
    payload JSONB NOT NULL,                     -- Event data

    -- Routing
    tenant_id UUID NOT NULL,                    -- Tenant isolation
    company_id UUID,                            -- Optional company context
    user_id UUID,                               -- Optional user context

    -- Processing status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed
    retry_count INT NOT NULL DEFAULT 0,
    max_retries INT NOT NULL DEFAULT 3,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL DEFAULT NOW() + INTERVAL '24 hours',

    -- Error tracking
    error_message TEXT,
    last_error_at TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX idx_events_status ON events(status) WHERE status IN ('pending', 'processing');
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_tenant ON events(tenant_id);
CREATE INDEX idx_events_expires ON events(expires_at);
CREATE INDEX idx_events_created ON events(created_at);

-- Partial index for pending events (most common query)
CREATE INDEX idx_events_pending ON events(created_at) WHERE status = 'pending';
```

### Event Subscriptions Table (Logged)

```sql
-- This table should be LOGGED (persistent) as it contains configuration
CREATE TABLE event_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Subscriber identification
    module_name VARCHAR(100) NOT NULL,          -- e.g., 'notification-module'
    handler_name VARCHAR(255) NOT NULL,         -- e.g., 'send_invoice_notification'

    -- Event pattern matching
    event_pattern VARCHAR(255) NOT NULL,        -- e.g., 'financial.invoice.*' or 'financial.invoice.created'

    -- Filtering (optional)
    tenant_id UUID,                             -- Subscribe only to specific tenant
    filter_conditions JSONB,                    -- Additional JSON filters

    -- Configuration
    is_active BOOLEAN NOT NULL DEFAULT true,
    priority INT NOT NULL DEFAULT 5,            -- 1-10, higher = processed first

    -- Delivery settings
    delivery_mode VARCHAR(20) NOT NULL DEFAULT 'async',  -- 'async' or 'sync'
    max_retry_attempts INT NOT NULL DEFAULT 3,
    retry_delay_seconds INT NOT NULL DEFAULT 60,

    -- Callback URL (for remote modules)
    callback_url VARCHAR(500),                  -- e.g., 'http://notification-module/api/events/handle'

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    last_triggered_at TIMESTAMP
);

CREATE INDEX idx_subscriptions_pattern ON event_subscriptions(event_pattern);
CREATE INDEX idx_subscriptions_active ON event_subscriptions(is_active) WHERE is_active = true;
CREATE INDEX idx_subscriptions_module ON event_subscriptions(module_name);
```

### Event Handlers Tracking (Logged)

```sql
-- Track which handlers have processed which events (for idempotency)
CREATE TABLE event_handlers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    event_id UUID NOT NULL,                     -- References events.id
    subscription_id UUID NOT NULL REFERENCES event_subscriptions(id),

    -- Processing status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, completed, failed, skipped
    retry_count INT NOT NULL DEFAULT 0,

    -- Timestamps
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Error tracking
    error_message TEXT,

    CONSTRAINT uq_event_handler UNIQUE(event_id, subscription_id)
);

CREATE INDEX idx_event_handlers_event ON event_handlers(event_id);
CREATE INDEX idx_event_handlers_status ON event_handlers(status);
CREATE INDEX idx_event_handlers_pending ON event_handlers(subscription_id, status)
    WHERE status IN ('pending', 'failed');
```

---

## Core Event Bus Implementation

### 1. Event Publisher

```python
# core/event_bus/publisher.py

import asyncio
import json
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

class EventPublisher:
    """Publishes events to PostgreSQL event bus"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        tenant_id: UUID,
        company_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        event_source: str = "core-platform",
        ttl_hours: int = 24
    ) -> UUID:
        """
        Publish an event to the event bus.

        Args:
            event_type: Event type (e.g., 'financial.invoice.created')
            payload: Event data as dictionary
            tenant_id: Tenant ID for data isolation
            company_id: Optional company context
            user_id: Optional user context
            event_source: Source module name
            ttl_hours: Time-to-live in hours

        Returns:
            Event ID
        """
        event_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

        # Insert event into unlogged table
        query = text("""
            INSERT INTO events (
                id, event_type, event_source, payload,
                tenant_id, company_id, user_id, expires_at
            ) VALUES (
                :id, :event_type, :event_source, :payload,
                :tenant_id, :company_id, :user_id, :expires_at
            )
        """)

        await self.db.execute(query, {
            "id": event_id,
            "event_type": event_type,
            "event_source": event_source,
            "payload": json.dumps(payload),
            "tenant_id": tenant_id,
            "company_id": company_id,
            "user_id": user_id,
            "expires_at": expires_at
        })

        await self.db.commit()

        # Send NOTIFY for real-time delivery
        await self._notify(event_type, event_id)

        return event_id

    async def _notify(self, event_type: str, event_id: UUID):
        """Send PostgreSQL NOTIFY for real-time event delivery"""
        # Notify on multiple channels for flexible subscription
        channels = [
            "events",                    # Global channel
            f"events:{event_type}",      # Specific event type
            f"events:{event_type.split('.')[0]}"  # Event category
        ]

        for channel in channels:
            notify_query = text(f"NOTIFY {channel}, :event_id")
            await self.db.execute(notify_query, {"event_id": str(event_id)})

# Usage example
async def create_invoice(invoice_data: dict, db: AsyncSession):
    # Business logic
    invoice = Invoice(**invoice_data)
    db.add(invoice)
    await db.commit()

    # Publish event
    publisher = EventPublisher(db)
    await publisher.publish(
        event_type="financial.invoice.created",
        payload={
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.number,
            "customer_id": str(invoice.customer_id),
            "total": float(invoice.total),
            "currency": invoice.currency
        },
        tenant_id=invoice.tenant_id,
        company_id=invoice.company_id,
        event_source="financial-module"
    )

    return invoice
```

### 2. Event Subscriber

```python
# core/event_bus/subscriber.py

import asyncio
import json
import select
from typing import Callable, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

class EventSubscriber:
    """Subscribes to events and processes them"""

    def __init__(
        self,
        db_session: AsyncSession,
        module_name: str
    ):
        self.db = db_session
        self.module_name = module_name
        self.handlers: Dict[str, List[Callable]] = {}
        self._listening = False
        self._notify_conn = None

    def subscribe(
        self,
        event_pattern: str,
        handler: Callable,
        priority: int = 5
    ):
        """
        Register a handler for an event pattern.

        Args:
            event_pattern: Event pattern (e.g., 'financial.invoice.*' or 'financial.invoice.created')
            handler: Async function to handle the event
            priority: Handler priority (1-10, higher first)
        """
        if event_pattern not in self.handlers:
            self.handlers[event_pattern] = []

        self.handlers[event_pattern].append({
            'handler': handler,
            'priority': priority
        })

        # Sort by priority (descending)
        self.handlers[event_pattern].sort(
            key=lambda x: x['priority'],
            reverse=True
        )

    async def start_listening(self):
        """Start listening for PostgreSQL NOTIFY events"""
        # Get raw connection for LISTEN
        self._notify_conn = psycopg2.connect(
            # Connection string from your config
            "postgresql://user:pass@localhost/dbname"
        )
        self._notify_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = self._notify_conn.cursor()

        # Listen on event channels
        cursor.execute("LISTEN events")

        self._listening = True

        # Start listening loop
        asyncio.create_task(self._listen_loop())

    async def _listen_loop(self):
        """Background loop to listen for NOTIFY events"""
        while self._listening:
            if select.select([self._notify_conn], [], [], 1) == ([], [], []):
                continue

            self._notify_conn.poll()

            while self._notify_conn.notifies:
                notify = self._notify_conn.notifies.pop(0)
                event_id = notify.payload

                # Process event
                await self._process_event(event_id)

    async def _process_event(self, event_id: str):
        """Process a single event"""
        # Fetch event
        query = text("""
            SELECT id, event_type, payload, tenant_id, company_id, user_id
            FROM events
            WHERE id = :event_id AND status = 'pending'
        """)

        result = await self.db.execute(query, {"event_id": event_id})
        event = result.fetchone()

        if not event:
            return

        event_type = event.event_type
        payload = json.loads(event.payload)

        # Find matching handlers
        matching_handlers = self._find_handlers(event_type)

        # Execute handlers
        for handler_info in matching_handlers:
            try:
                await handler_info['handler']({
                    'id': event.id,
                    'type': event_type,
                    'payload': payload,
                    'tenant_id': event.tenant_id,
                    'company_id': event.company_id,
                    'user_id': event.user_id
                })
            except Exception as e:
                # Log error but don't stop processing other handlers
                print(f"Error in handler: {e}")

    def _find_handlers(self, event_type: str) -> List[Dict]:
        """Find handlers that match the event type"""
        matching = []

        for pattern, handlers in self.handlers.items():
            if self._matches_pattern(event_type, pattern):
                matching.extend(handlers)

        # Sort by priority
        matching.sort(key=lambda x: x['priority'], reverse=True)
        return matching

    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Check if event_type matches pattern (supports wildcards)"""
        if pattern == "*":
            return True

        if "*" not in pattern:
            return event_type == pattern

        # Simple wildcard matching
        # financial.invoice.* matches financial.invoice.created
        pattern_parts = pattern.split('.')
        event_parts = event_type.split('.')

        if len(pattern_parts) != len(event_parts):
            return False

        for p, e in zip(pattern_parts, event_parts):
            if p != "*" and p != e:
                return False

        return True

    async def stop_listening(self):
        """Stop listening for events"""
        self._listening = False
        if self._notify_conn:
            self._notify_conn.close()

# Usage example in a module
subscriber = EventSubscriber(db_session, "notification-module")

@subscriber.subscribe("financial.invoice.created", priority=8)
async def send_invoice_notification(event):
    """Handle invoice created event"""
    invoice_id = event['payload']['invoice_id']

    # Send notification
    await send_email(
        to=event['payload']['customer_email'],
        subject=f"Invoice {event['payload']['invoice_number']}",
        template="invoice_created"
    )

@subscriber.subscribe("financial.invoice.*", priority=5)
async def update_revenue_metrics(event):
    """Handle all invoice events"""
    # Update analytics
    pass

# Start listening
await subscriber.start_listening()
```

### 3. Background Event Processor (Polling)

For redundancy and handling events when LISTEN/NOTIFY fails:

```python
# core/event_bus/processor.py

import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

class EventProcessor:
    """Background worker that polls for pending events"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self._running = False

    async def start(self, poll_interval_seconds: int = 5):
        """Start the background event processor"""
        self._running = True

        while self._running:
            try:
                await self._process_pending_events()
            except Exception as e:
                print(f"Error processing events: {e}")

            await asyncio.sleep(poll_interval_seconds)

    async def _process_pending_events(self):
        """Process all pending events"""
        # Fetch pending events (ordered by creation time)
        query = text("""
            SELECT id, event_type, payload, tenant_id, company_id, user_id, retry_count, max_retries
            FROM events
            WHERE status = 'pending'
              AND created_at < NOW()
              AND (retry_count < max_retries OR retry_count IS NULL)
            ORDER BY created_at ASC
            LIMIT 100
            FOR UPDATE SKIP LOCKED
        """)

        result = await self.db.execute(query)
        events = result.fetchall()

        for event in events:
            # Mark as processing
            await self._mark_processing(event.id)

            # Get subscriptions for this event type
            subscriptions = await self._get_subscriptions(event.event_type)

            # Process each subscription
            success = True
            for sub in subscriptions:
                try:
                    await self._invoke_handler(sub, event)
                except Exception as e:
                    success = False
                    await self._mark_failed(event.id, str(e))

            if success:
                await self._mark_completed(event.id)

    async def _get_subscriptions(self, event_type: str):
        """Get active subscriptions for an event type"""
        query = text("""
            SELECT id, module_name, callback_url, filter_conditions
            FROM event_subscriptions
            WHERE is_active = true
              AND (
                  event_pattern = :event_type
                  OR event_pattern LIKE :wildcard_pattern
                  OR event_pattern = '*'
              )
            ORDER BY priority DESC
        """)

        # Extract category for wildcard matching
        category = event_type.split('.')[0]

        result = await self.db.execute(query, {
            "event_type": event_type,
            "wildcard_pattern": f"{category}.%"
        })

        return result.fetchall()

    async def _invoke_handler(self, subscription, event):
        """Invoke a subscription handler"""
        if subscription.callback_url:
            # Remote module - call via HTTP
            async with httpx.AsyncClient() as client:
                await client.post(
                    subscription.callback_url,
                    json={
                        'event_id': str(event.id),
                        'event_type': event.event_type,
                        'payload': json.loads(event.payload),
                        'tenant_id': str(event.tenant_id)
                    },
                    timeout=30.0
                )
        else:
            # Local handler - invoke directly
            # (This would be implemented based on your handler registry)
            pass

    async def _mark_processing(self, event_id):
        """Mark event as processing"""
        query = text("""
            UPDATE events
            SET status = 'processing'
            WHERE id = :event_id
        """)
        await self.db.execute(query, {"event_id": event_id})
        await self.db.commit()

    async def _mark_completed(self, event_id):
        """Mark event as completed"""
        query = text("""
            UPDATE events
            SET status = 'completed', processed_at = NOW()
            WHERE id = :event_id
        """)
        await self.db.execute(query, {"event_id": event_id})
        await self.db.commit()

    async def _mark_failed(self, event_id, error_message: str):
        """Mark event as failed and increment retry count"""
        query = text("""
            UPDATE events
            SET
                status = CASE
                    WHEN retry_count + 1 >= max_retries THEN 'failed'
                    ELSE 'pending'
                END,
                retry_count = retry_count + 1,
                error_message = :error_message,
                last_error_at = NOW()
            WHERE id = :event_id
        """)
        await self.db.execute(query, {
            "event_id": event_id,
            "error_message": error_message
        })
        await self.db.commit()

    def stop(self):
        """Stop the background processor"""
        self._running = False
```

---

## Cleanup & Maintenance

### 1. Automatic Cleanup Job

```python
# core/event_bus/cleanup.py

from sqlalchemy import text
from datetime import datetime

class EventCleanup:
    """Cleanup old and expired events"""

    async def cleanup_expired_events(self, db: AsyncSession):
        """Delete expired events"""
        query = text("""
            DELETE FROM events
            WHERE expires_at < NOW()
              OR (status = 'completed' AND processed_at < NOW() - INTERVAL '7 days')
        """)

        result = await db.execute(query)
        await db.commit()

        return result.rowcount

    async def cleanup_event_handlers(self, db: AsyncSession):
        """Cleanup old event handler records"""
        query = text("""
            DELETE FROM event_handlers
            WHERE completed_at < NOW() - INTERVAL '30 days'
        """)

        result = await db.execute(query)
        await db.commit()

        return result.rowcount

    async def archive_old_events(self, db: AsyncSession):
        """Archive old events to a logged table for analytics"""
        query = text("""
            INSERT INTO events_archive (
                id, event_type, event_source, payload,
                tenant_id, company_id, status, created_at, processed_at
            )
            SELECT
                id, event_type, event_source, payload,
                tenant_id, company_id, status, created_at, processed_at
            FROM events
            WHERE status = 'completed'
              AND processed_at < NOW() - INTERVAL '1 day'
        """)

        await db.execute(query)

        # Delete archived events
        delete_query = text("""
            DELETE FROM events
            WHERE status = 'completed'
              AND processed_at < NOW() - INTERVAL '1 day'
        """)

        await db.execute(delete_query)
        await db.commit()

# Run cleanup periodically (e.g., via APScheduler)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=2)  # Run at 2 AM daily
async def scheduled_cleanup():
    cleanup = EventCleanup()
    async with get_db_session() as db:
        deleted = await cleanup.cleanup_expired_events(db)
        print(f"Cleaned up {deleted} expired events")
```

### 2. Archive Table (Logged)

For long-term event storage and analytics:

```sql
-- Logged table for archiving events (survives crashes)
CREATE TABLE events_archive (
    id UUID PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    event_source VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    tenant_id UUID NOT NULL,
    company_id UUID,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    processed_at TIMESTAMP,
    archived_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for analytics
CREATE INDEX idx_events_archive_type ON events_archive(event_type);
CREATE INDEX idx_events_archive_tenant ON events_archive(tenant_id);
CREATE INDEX idx_events_archive_created ON events_archive(created_at);

-- Partition by month for better performance
CREATE TABLE events_archive_2024_01 PARTITION OF events_archive
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

---

## Integration with Module Architecture

### Module Event Handler Registration

```python
# financial-module/app/events.py

from core.event_bus import EventSubscriber

class FinancialModuleEvents:
    """Event handlers for financial module"""

    def __init__(self, db: AsyncSession):
        self.subscriber = EventSubscriber(db, "financial-module")
        self._register_handlers()

    def _register_handlers(self):
        """Register all event handlers"""

        # Listen to company creation
        self.subscriber.subscribe(
            "core.company.created",
            self.handle_company_created,
            priority=8
        )

        # Listen to user role changes
        self.subscriber.subscribe(
            "core.user.role_changed",
            self.handle_user_role_changed,
            priority=5
        )

    async def handle_company_created(self, event):
        """Create default financial accounts for new company"""
        company_id = event['payload']['company_id']
        tenant_id = event['tenant_id']

        # Create default chart of accounts
        await self.create_default_accounts(tenant_id, company_id)

        print(f"Created default accounts for company {company_id}")

    async def handle_user_role_changed(self, event):
        """Handle user role changes"""
        # Maybe update cached permissions, etc.
        pass

# In module startup
async def startup_event():
    db = get_db_session()
    events = FinancialModuleEvents(db)
    await events.subscriber.start_listening()
```

### Publishing Events from Modules

```python
# In any module
from core.event_bus import EventPublisher

async def mark_invoice_as_paid(invoice_id: str, db: AsyncSession):
    # Update invoice
    invoice = await db.get(Invoice, invoice_id)
    invoice.status = "paid"
    invoice.paid_at = datetime.utcnow()
    await db.commit()

    # Publish event
    publisher = EventPublisher(db)
    await publisher.publish(
        event_type="financial.invoice.paid",
        payload={
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.number,
            "amount": float(invoice.total),
            "paid_at": invoice.paid_at.isoformat()
        },
        tenant_id=invoice.tenant_id,
        company_id=invoice.company_id,
        event_source="financial-module"
    )
```

---

## Advantages of PostgreSQL Event Bus

### ✅ Pros

1. **No Additional Infrastructure**
   - Use existing PostgreSQL database
   - Simpler deployment and operations
   - Lower cost

2. **ACID Guarantees**
   - Transactional consistency
   - Reliable event storage

3. **Simple Debugging**
   - Query events with SQL
   - Easy to inspect and troubleshoot

4. **Data Locality**
   - Events stored with business data
   - Can join events with other tables

5. **Real-time with LISTEN/NOTIFY**
   - Low latency for event delivery
   - No polling overhead for most cases

6. **Unlogged Tables Performance**
   - Fast writes (no WAL overhead)
   - Acceptable risk for events (can be republished)

### ⚠️ Cons

1. **Not Crash-Safe**
   - Unlogged tables lose data on PostgreSQL crash
   - Mitigation: Important events can be republished from source data

2. **Limited Throughput**
   - Not as fast as dedicated message brokers
   - Good for up to ~10K events/second

3. **Manual Retry Logic**
   - Need to implement retry/DLQ yourself
   - Not as feature-rich as RabbitMQ

4. **Scaling Limitations**
   - Can't scale horizontally like Kafka
   - Fine for most SaaS applications

---

## Performance Optimization

### 1. Partitioning Events Table

```sql
-- Partition by created_at for better performance
CREATE TABLE events (
    -- columns...
) PARTITION BY RANGE (created_at);

CREATE TABLE events_today PARTITION OF events
    FOR VALUES FROM (CURRENT_DATE) TO (CURRENT_DATE + 1);

CREATE TABLE events_yesterday PARTITION OF events
    FOR VALUES FROM (CURRENT_DATE - 1) TO (CURRENT_DATE);

-- Create partitions automatically via cron
```

### 2. Batch Processing

```python
async def publish_batch(events: List[Dict], db: AsyncSession):
    """Publish multiple events efficiently"""
    query = text("""
        INSERT INTO events (
            id, event_type, event_source, payload, tenant_id
        )
        SELECT
            gen_random_uuid(),
            data->>'event_type',
            data->>'event_source',
            data->'payload',
            (data->>'tenant_id')::uuid
        FROM jsonb_array_elements(:events) AS data
    """)

    await db.execute(query, {"events": json.dumps(events)})
    await db.commit()
```

### 3. Monitoring

```sql
-- Monitor event processing lag
SELECT
    event_type,
    COUNT(*) as pending_count,
    MIN(created_at) as oldest_pending,
    NOW() - MIN(created_at) as max_lag
FROM events
WHERE status = 'pending'
GROUP BY event_type
ORDER BY max_lag DESC;

-- Monitor processing rate
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed
FROM events
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;
```

---

## Migration from RabbitMQ/Kafka (If Needed Later)

The interface remains the same! Just swap implementations:

```python
# Abstract interface
class EventBusInterface:
    async def publish(self, event_type, payload, **kwargs):
        raise NotImplementedError

    def subscribe(self, pattern, handler):
        raise NotImplementedError

# PostgreSQL implementation
class PostgresEventBus(EventBusInterface):
    # Current implementation
    pass

# RabbitMQ implementation (future)
class RabbitMQEventBus(EventBusInterface):
    async def publish(self, event_type, payload, **kwargs):
        # Use pika or aio-pika
        pass

# In config
EVENT_BUS_TYPE = os.getenv("EVENT_BUS_TYPE", "postgres")  # or "rabbitmq"

def get_event_bus():
    if EVENT_BUS_TYPE == "postgres":
        return PostgresEventBus()
    elif EVENT_BUS_TYPE == "rabbitmq":
        return RabbitMQEventBus()
```

---

## Recommendation

**Use PostgreSQL Event Bus for:**
- Small to medium SaaS applications (< 100K events/day)
- Development and staging environments
- When operational simplicity is priority
- When event loss on crash is acceptable (can be republished)

**Consider upgrading to RabbitMQ/Kafka when:**
- Event volume > 100K events/day
- Need guaranteed message delivery
- Need advanced routing and dead-letter queues
- Need to scale event processing independently

**For your modular architecture, PostgreSQL Event Bus is an excellent starting point!** 🚀
