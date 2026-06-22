from __future__ import annotations
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_REMINDER_HOURS = [24, 2]


def schedule_appointment_reminders(appointment_id: str, scheduled_at: datetime) -> None:
    # Store reminder jobs in Redis as hc:reminder:{appointment_id}:{hours}h with TTL.
    # Background worker (stub -- out of scope for Sprint 3):
    #   Subscribe to Redis keyspace events for hc:reminder:* expiry.
    #   On expiry: call NotificationService.dispatch_appointment_notification(
    #       appointment_id, "appointment_reminder_24h" | "appointment_reminder_2h"
    #   )
    now = datetime.utcnow()
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis as _redis
        r = _redis.from_url(redis_url)
        for hours in _REMINDER_HOURS:
            fire_at = scheduled_at - timedelta(hours=hours)
            ttl_seconds = int((fire_at - now).total_seconds())
            if ttl_seconds <= 0:
                continue
            key = f"hc:reminder:{appointment_id}:{hours}h"
            r.setex(key, ttl_seconds, appointment_id)
            logger.info("Scheduled %sh reminder for %s (TTL %ds)", hours, appointment_id, ttl_seconds)
    except Exception as exc:
        logger.warning("Redis unavailable; reminders not scheduled for %s: %s", appointment_id, exc)


__all__ = ["schedule_appointment_reminders"]
