---
artifact_id: audit-14-notification-system
type: audit
producer: Code Auditor
consumers: [Tech Lead, Product Owner]
upstream: [epic-14-notification-system, arch-platform]
downstream: []
status: approved
created: 2026-04-29
updated: 2026-04-29
audit_target: epic-14-notification-system
auditor: Claude (Opus 4.7)
commit_sha: cc47a54
coverage_pct: 100
---

# Audit — Epic 14: Notification System (audit-14-notification-system)

## 1. Summary

- Stories audited: **6**
- DONE: **3** • PARTIAL: **0** • DRIFT: **0** • MISSING: **3**
- Tag-drift count: **0** (claimed tags align with verified state)
- Recommended `BACKLOG.md` tag: **Arch + Email DONE; Templates/SMS/In-App MISSING** (currently "Arch DONE; Delivery OPEN/PLANNED")

> **Re-audit 2026-05-XX (epic-21 sprint 1)**: story 14.2.1 (SMTP Email Delivery Adapter) retired its 🔴 MISSING status. Evidence updated; gap moved to "Retired by epic-21" section. 14.2.2 (templates), 14.3.1 (SMS), 14.3.2 (in-app) remain MISSING — out of scope for this sprint.

## 2. Story-by-story

| Story | Title | Claimed | Verified | Backend evidence | Frontend evidence | Gaps | 🚦 |
|-------|-------|---------|----------|------------------|-------------------|------|----|
| 14.1.1 | Notification Queuing Architecture | DONE | DONE | `app/models/notification_queue.py:7 NotificationQueue`, `app/core/notification_service.py:20 queue_notification` | — | — | — |
| 14.1.2 | Notification Configuration per Tenant | DONE | DONE | `app/models/notification_config.py:16 NotificationConfig`, admin/security router config endpoints | — | — | — |
| 14.2.1 | SMTP Email Delivery Adapter | OPEN | DONE *(retired epic-21)* | **`backend/app/workers/notification_worker.py NotificationWorker`** — polling consumer of `notification_queue` (T-21.2.1); `_send_email()` uses stdlib `smtplib.SMTP` + `starttls()` + `send_message()` (T-21.2.2); jinja2 template rendering with `StrictUndefined`; 3-tier SMTP config fallback (per-tenant `NotificationConfig` → system default → env vars); `_audit()` writes `notification.delivered` / `notification.failed` audit-log entries (T-21.2.4); `backend/app/main.py` lifespan starts an in-process daemon thread when `NOTIFICATION_WORKER_INPROCESS=true` (T-21.2.5); `backend/.env.example` + `docker-compose.yml` + `infra/docker-compose.prod.yml` ship the worker container (T-21.2.6/.7) | — (no UI surface) | — (was MISSING; password-reset emails now deliverable end-to-end) | ✅ |
| 14.2.2 | Email Template System | OPEN | MISSING | — | — | No `app/templates/email/`, no `EmailRenderer.render()`, no per-tenant template overrides | 🔴 |
| 14.3.1 | SMS Delivery via Provider | PLANNED | MISSING | — | — | No Twilio (or generic) SMS adapter, no test-sms endpoint | 🔴 |
| 14.3.2 | In-App Notification Center | PLANNED | MISSING | — | — | No `notifications` table, no `GET /notifications/me`, no read/unread state, no bell UI | 🔴 |

## 3. Gaps

### ✅ Retired by epic-21 sprint 1
- [x] **14.2.1** SMTP delivery worker shipped (T-21.2.1/.2/.4/.5/.6/.7). Polling-based (chose simpler than LISTEN/NOTIFY for skeleton); 17/17 SMTP wire-path tests pass; 5/5 state-machine tests pass; container shipped in both dev + prod compose; lifespan integration via `NOTIFICATION_WORKER_INPROCESS=true`.

### 🔴 High
- [ ] **14.2.2** Email template system (default templates per event type + per-tenant overrides). **Files**: `backend/app/services/email_renderer.py`, `backend/app/templates/email/`. **Effort**: M. *(Note: T-21.2.2 ships inline jinja2 rendering of `notification_queue.message`/`subject` — adequate for password-reset; richer per-event templates + per-tenant overrides remain.)*
- [ ] **14.3.1** SMS delivery adapter (Twilio default, plug-in pattern for others). **Effort**: M.
- [ ] **14.3.2** In-app notification model + endpoints + bell UI. **Files**: `backend/app/models/notification.py`, `backend/app/routers/notifications.py`, `frontend/assets/js/notifications.js`. **Effort**: L.

## 5. Verdict

**Updated 2026-05-XX (post epic-21 sprint 1):** the email channel is now live end-to-end. Password-reset emails, account-locked notifications, and any other queued email message will deliver via SMTP. The `BACKLOG.md` tag should now read **"Arch + Email DONE; Templates / SMS / In-App MISSING"**.

*Original verdict (pre-sprint), preserved for historical context:* The queuing architecture is real (14.1 DONE) but no actual notification has ever been delivered — every channel (email, SMS, in-app) is unimplemented. Single most impactful next action: **14.2.1 SMTP adapter** so password-reset and audit notifications stop dead-lettering.

## Decisions

- Marked all of 14.2 and 14.3 MISSING despite some having `[OPEN]` (which suggests "design exists, code does not"). The tags are honest; just record them in the audit for completeness.

## Open Questions

- Should the in-app notification center reuse the `notification_queue` table or get its own `notifications` table? Recommend separate (queue is delivery-oriented; in-app is read-state-oriented).
