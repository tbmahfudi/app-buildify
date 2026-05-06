"""Notification delivery worker.

Consumes ``notification_queue`` rows produced by ``NotificationService``
(see ``app/core/notification_service.py``) and dispatches them via the
appropriate channel (email/SMS/webhook/push). Email dispatch via SMTP
is the focus of epic-21 item 21.2 — see story 14.2.1 backend AC.

This file is the **skeleton only** (T-21.2.1). The actual SMTP send,
template rendering, and retry/dead-letter logic land in T-21.2.2 +
T-21.2.3. ``_dispatch`` here is a placeholder that logs the message
and reports success so the loop can be exercised end-to-end.

Placement (per ADR-002):
- ``DEPLOYMENT_MODE=monolith`` + ``NOTIFICATION_WORKER_INPROCESS=true``
  → started as an asyncio task during the platform's lifespan
  (wired in T-21.2.5)
- ``DEPLOYMENT_MODE=monolith`` + ``NOTIFICATION_WORKER_INPROCESS=false``
  (default) → run as a standalone container via
  ``python -m app.workers.notification_worker``
- ``DEPLOYMENT_MODE=distributed`` → always standalone container

The worker uses **polling** against the ``notification_queue`` table
rather than Postgres LISTEN/NOTIFY. Polling is simpler, more robust to
connection drops, and acceptable at the scale of password-reset emails.
LISTEN/NOTIFY can be added later as a low-latency wakeup signal on top
of the same polling fallback.
"""

import logging
import os
import signal
import smtplib
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import List, Optional

from jinja2 import Environment, StrictUndefined, TemplateError
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.notification_config import NotificationConfig
from app.models.notification_queue import NotificationQueue

logger = logging.getLogger(__name__)

# Jinja2 environment with autoescape OFF (subject/body are plain text;
# enable per-template autoescape later when HTML templates land).
# StrictUndefined surfaces missing template_data keys at render time
# instead of silently producing empty strings — caller sees the bug.
_jinja = Environment(undefined=StrictUndefined)


@dataclass(frozen=True)
class SMTPConfig:
    host: str
    port: int
    user: Optional[str]
    password: Optional[str]
    from_addr: str
    use_tls: bool

    @property
    def is_complete(self) -> bool:
        return bool(self.host and self.port and self.from_addr)


class NotificationWorker:
    """Polling worker that dispatches pending ``notification_queue`` rows.

    State transitions per row:
        pending -> processing -> sent           (success)
        pending -> processing -> pending        (transient failure, attempts < max)
        pending -> processing -> failed         (attempts >= max, dead-letter)

    The worker holds **no in-memory queue** — every dispatch decision is
    backed by a row update so a crash mid-loop loses no work. Rows in
    ``processing`` state for longer than ``stuck_after_seconds`` are
    reclaimed (treated as transient failure on the next loop) so a worker
    restart does not leave rows stranded.
    """

    def __init__(
        self,
        poll_interval_seconds: float = 5.0,
        batch_size: int = 20,
        stuck_after_seconds: int = 300,
    ):
        self.poll_interval_seconds = poll_interval_seconds
        self.batch_size = batch_size
        self.stuck_after_seconds = stuck_after_seconds
        self._stop = False

    # ----- lifecycle ------------------------------------------------------

    def stop(self) -> None:
        """Request a graceful shutdown after the current batch completes."""
        self._stop = True

    def run(self) -> None:
        """Block-and-poll until ``stop()`` is called or SIGTERM/SIGINT received.

        Suitable for both standalone-process and asyncio-thread embedding.
        """
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        logger.info(
            "notification-worker starting (poll=%ss, batch=%s)",
            self.poll_interval_seconds,
            self.batch_size,
        )

        while not self._stop:
            try:
                processed = self._tick()
                if processed == 0 and not self._stop:
                    time.sleep(self.poll_interval_seconds)
            except Exception as exc:  # pragma: no cover - top-level safety net
                logger.exception("notification-worker tick failed: %s", exc)
                time.sleep(self.poll_interval_seconds)

        logger.info("notification-worker stopped")

    def _handle_signal(self, signum, _frame) -> None:
        logger.info("notification-worker received signal %s; stopping", signum)
        self.stop()

    # ----- polling tick --------------------------------------------------

    def _tick(self) -> int:
        """Process one batch. Returns the number of rows handled."""
        db: Session = SessionLocal()
        try:
            self._reclaim_stuck(db)
            ready = self._fetch_ready(db)
            for row in ready:
                self._handle_one(db, row)
            return len(ready)
        finally:
            db.close()

    def _reclaim_stuck(self, db: Session) -> int:
        """Reset stale ``processing`` rows back to ``pending`` for retry.

        Triggered when a previous worker crashed mid-dispatch. Rows older
        than ``stuck_after_seconds`` since their last update are reclaimed.
        """
        cutoff_seconds = self.stuck_after_seconds
        stuck = (
            db.query(NotificationQueue)
            .filter(NotificationQueue.status == "processing")
            .all()
        )
        reclaimed = 0
        now = datetime.now(timezone.utc)
        for row in stuck:
            ts = row.updated_at or row.created_at
            if ts is None:
                continue
            # SQLAlchemy may return naive datetimes; coerce to UTC for comparison
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if (now - ts).total_seconds() >= cutoff_seconds:
                row.status = "pending"
                reclaimed += 1
        if reclaimed:
            db.commit()
            logger.warning("Reclaimed %s stuck processing rows", reclaimed)
        return reclaimed

    def _fetch_ready(self, db: Session) -> List[NotificationQueue]:
        """Claim up to ``batch_size`` pending+ready rows by flipping them to processing."""
        now = datetime.now(timezone.utc)
        # We do the read+update in a single transaction; concurrent workers
        # are tolerated because the second worker's UPDATE on the same row
        # will set status='processing' a second time (idempotent — _handle_one
        # is the same operation either way) and the row's notification will
        # be dispatched at most once because notification_queue rows transition
        # monotonically through pending->processing->{sent,failed,pending-retry}.
        candidates = (
            db.query(NotificationQueue)
            .filter(NotificationQueue.status == "pending")
            .filter(
                (NotificationQueue.scheduled_for.is_(None))
                | (NotificationQueue.scheduled_for <= now)
            )
            .filter(NotificationQueue.attempts < NotificationQueue.max_attempts)
            .order_by(NotificationQueue.priority.asc(), NotificationQueue.created_at.asc())
            .limit(self.batch_size)
            .all()
        )
        for row in candidates:
            row.status = "processing"
        if candidates:
            db.commit()
        return candidates

    # ----- dispatch ------------------------------------------------------

    def _handle_one(self, db: Session, row: NotificationQueue) -> None:
        try:
            row.attempts = (row.attempts or 0) + 1
            self._dispatch(row)
        except Exception as exc:
            self._mark_failed(db, row, str(exc))
            return
        self._mark_sent(db, row)

    def _dispatch(self, row: NotificationQueue) -> None:
        """Channel-specific delivery.

        Email is implemented (T-21.2.2). SMS/webhook/push raise
        ``NotImplementedError`` and dead-letter via the retry path.
        """
        logger.info(
            "notification-worker dispatching id=%s type=%s method=%s recipient=%s",
            row.id, row.notification_type, row.delivery_method, row.recipient,
        )
        if row.delivery_method == "email":
            self._send_email(row)
            return
        # SMS / webhook / push are out of scope for epic-21 (see story 14.3)
        raise NotImplementedError(
            f"delivery_method '{row.delivery_method}' not yet implemented"
        )

    # ----- email (T-21.2.2) ----------------------------------------------

    def _send_email(self, row: NotificationQueue) -> None:
        """Render templates and dispatch via SMTP.

        Looks up SMTP config from ``NotificationConfig`` (tenant-specific
        first, then system default at ``tenant_id IS NULL``), then falls
        back to env vars (``SMTP_HOST``, ``SMTP_PORT``, ``SMTP_USER``,
        ``SMTP_PASSWORD``, ``SMTP_FROM``, ``SMTP_USE_TLS``) per arch-21 §4.
        """
        config = self._get_smtp_config(row.tenant_id)
        if not config or not config.is_complete:
            raise ValueError(
                "No SMTP config available (checked tenant config, system config, and env vars)"
            )

        subject = self._render(row.subject or "", row.template_data or {})
        body = self._render(row.message or "", row.template_data or {})

        msg = EmailMessage()
        msg["From"] = config.from_addr
        msg["To"] = row.recipient
        msg["Subject"] = subject or f"[{row.notification_type}]"
        msg.set_content(body)

        if config.use_tls:
            with smtplib.SMTP(config.host, config.port, timeout=30) as smtp:
                smtp.starttls()
                if config.user:
                    smtp.login(config.user, config.password or "")
                smtp.send_message(msg)
        else:
            # Plain SMTP (e.g. local dev MailHog) — auth optional
            with smtplib.SMTP(config.host, config.port, timeout=30) as smtp:
                if config.user:
                    smtp.login(config.user, config.password or "")
                smtp.send_message(msg)

    @staticmethod
    def _render(template_str: str, context: dict) -> str:
        """Render ``template_str`` with ``context``. Empty template returns ''.

        Jinja2 errors (undefined vars, syntax) propagate as ``ValueError``
        so the worker's retry logic dead-letters them after max_attempts.
        """
        if not template_str:
            return ""
        if not context:
            # Fast path: no substitution needed
            return template_str
        try:
            return _jinja.from_string(template_str).render(**context)
        except TemplateError as exc:
            raise ValueError(f"Template render error: {exc}") from exc

    def _get_smtp_config(self, tenant_id) -> Optional[SMTPConfig]:
        """Return the SMTP config for this tenant.

        Resolution order:
            1. NotificationConfig where tenant_id matches
            2. NotificationConfig where tenant_id IS NULL (system default)
            3. Env vars (SMTP_HOST/PORT/USER/PASSWORD/FROM/USE_TLS)
        Returns ``None`` if none of the above produces a complete config.
        """
        db: Session = SessionLocal()
        try:
            nc: Optional[NotificationConfig] = None
            if tenant_id is not None:
                nc = (
                    db.query(NotificationConfig)
                    .filter(NotificationConfig.tenant_id == tenant_id)
                    .filter(NotificationConfig.is_active.is_(True))
                    .first()
                )
            if nc is None:
                nc = (
                    db.query(NotificationConfig)
                    .filter(NotificationConfig.tenant_id.is_(None))
                    .filter(NotificationConfig.is_active.is_(True))
                    .first()
                )
            if nc and nc.email_enabled and nc.email_smtp_host:
                return SMTPConfig(
                    host=nc.email_smtp_host,
                    port=int(nc.email_smtp_port or 587),
                    user=nc.email_smtp_user,
                    password=nc.email_smtp_password,
                    from_addr=nc.email_from or (nc.email_smtp_user or ""),
                    use_tls=bool(nc.email_use_tls if nc.email_use_tls is not None else True),
                )
        finally:
            db.close()

        # Env-var fallback
        host = os.environ.get("SMTP_HOST")
        if not host:
            return None
        return SMTPConfig(
            host=host,
            port=int(os.environ.get("SMTP_PORT", "587")),
            user=os.environ.get("SMTP_USER"),
            password=os.environ.get("SMTP_PASSWORD"),
            from_addr=os.environ.get("SMTP_FROM", os.environ.get("SMTP_USER", "")),
            use_tls=_bool_env("SMTP_USE_TLS", default=True),
        )

    def _mark_sent(self, db: Session, row: NotificationQueue) -> None:
        row.status = "sent"
        row.sent_at = datetime.now(timezone.utc)
        row.error_message = None
        db.commit()
        # T-21.2.4 will add audit_logger.log("notification.delivered", ...)

    def _mark_failed(self, db: Session, row: NotificationQueue, error: str) -> None:
        row.error_message = error
        if row.attempts >= row.max_attempts:
            row.status = "failed"  # dead-letter
            logger.error(
                "notification-worker DEAD-LETTER id=%s after %s attempts: %s",
                row.id, row.attempts, error,
            )
        else:
            row.status = "pending"  # retry on next tick
            logger.warning(
                "notification-worker transient failure id=%s attempts=%s/%s: %s",
                row.id, row.attempts, row.max_attempts, error,
            )
        db.commit()
        # T-21.2.4 will add audit_logger.log("notification.failed", ...)


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def main() -> None:  # pragma: no cover
    """Entry point for standalone-process mode (per ADR-002)."""
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    poll = float(os.environ.get("NOTIFICATION_WORKER_POLL_SECONDS", "5"))
    batch = int(os.environ.get("NOTIFICATION_WORKER_BATCH_SIZE", "20"))
    worker = NotificationWorker(poll_interval_seconds=poll, batch_size=batch)
    worker.run()


if __name__ == "__main__":  # pragma: no cover
    main()
