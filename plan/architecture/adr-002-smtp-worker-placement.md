---
artifact_id: adr-002
type: adr
producer: B1 Software Architect
consumers: [C1 Tech Lead, C2 Backend Developer, E1 DevOps Engineer]
upstream: [adr-001-deployment-modes, arch-platform, arch-21, epic-21-risk-retirement]
downstream: []
status: proposed
created: 2026-04-29
updated: 2026-04-29
---

# ADR-002 — SMTP Notification Worker Placement under DEPLOYMENT_MODE

## Status

Proposed. (Will flip to **accepted** once team review on epic-21 completes.)

## Context

Story 14.2.1 (SMTP Email Delivery Adapter) is part of [`epic-21-risk-retirement`](../epics/epic-21-risk-retirement.md) item 21.2. The platform already ships:

- The `notifications` table and a queueing mechanism via Postgres LISTEN/NOTIFY (per `audit-14-notification-system.md` Feature 14.1, status DONE).
- `notification_service.py` enqueues — but no worker dequeues. Password-reset emails today are dead-letter.
- `arch-platform.md` §9 risk #14 documents the LISTEN/NOTIFY subscriber as a stub in distributed mode.

The new question: **where does the SMTP-dispatching worker run?** This question matters because [`adr-001-deployment-modes`](adr-001-deployment-modes.md) defines two deployment shapes (`monolith` and `distributed`) controlled by the `DEPLOYMENT_MODE` env var, and a worker has different operational characteristics than the API processes it complements:

- **Bursty load**: a tenant onboarding burst can produce hundreds of password-reset and welcome emails in seconds. The worker benefits from independent scaling.
- **Different failure mode**: external SMTP server outages should not back-pressure the API write path. Today they cannot (the API only enqueues), but coupling the worker to the API process would create that coupling.
- **Operational simplicity for small deployments**: ADR-001 explicitly preserves a "small-deployment" promise — running everything in one container is supported. A second mandatory container would violate that.

Two placement options:

1. **In-process asyncio task in the platform monolith.** Simplest deployment. Couples worker lifecycle to API process; SMTP outage handling lives in the API container.
2. **Standalone `notification-worker` process / container.** Independent scaling, isolation from API. Adds a second container to the prod manifest.

## Decision

**Run the notification-worker as a separate process, with one config flag for in-process embedding.**

| `DEPLOYMENT_MODE` | `NOTIFICATION_WORKER_INPROCESS` | Effect |
|--------|--------|--------|
| `monolith` | `true` | Worker is started as an asyncio task during the platform's `lifespan` startup. Single container, single process. Suitable for small deployments. |
| `monolith` | `false` (default) | Worker runs as a separate `notification-worker` container in the same compose project. Suitable for medium deployments still using monolith API. |
| `distributed` | (ignored) | Worker **always** runs as a separate `notification-worker` container. Independent scaling. |

Mechanics:

- The worker subscribes to the **existing** `notifications` LISTEN/NOTIFY channel. **No new queue introduced.** This preserves ADR-001's "single Postgres" stance.
- In `distributed` mode the worker connects to the same Postgres instance that the API does (when `DATABASE_STRATEGY=shared`) or to its module's database (when `separate`). For epic-21 only `shared` is exercised — `separate` is a future expansion.
- The worker is implemented in `backend/app/workers/notification_worker.py` and is launchable via `python -m app.workers.notification_worker` for the standalone case.
- In-process mode is wired in `backend/app/main.py` `lifespan` behind `NOTIFICATION_WORKER_INPROCESS=true`.

## Consequences

### Positive
- ✅ SMTP outages cannot back-pressure the API write path (API only enqueues; worker is the only SMTP caller).
- ✅ Worker scales independently in distributed mode.
- ✅ In-process mode preserves ADR-001's small-deployment promise; one config flag covers it.
- ✅ No new queueing infrastructure (Redis, RabbitMQ) — extends what's already shipped.
- ✅ The same code path runs in both placements; only the entrypoint differs.

### Negative
- ❌ Adds a new container to the docker-compose prod manifest in the default monolith case (`NOTIFICATION_WORKER_INPROCESS=false`). **Follow-up**: Epic 19 Feature 19.2 (prod compose) gains one service entry — not blocking for epic-21 but tracked.
- ❌ **Hard dependency**: production-ready LISTEN/NOTIFY subscriber. `arch-platform.md` §9 risk #14 still applies — the subscriber stub in `modules/financial/backend/app/core/event_handler.py:43-47` is unrelated (it's a module-side stub), but the **core** subscriber implementation in `backend/app/core/event_bus/` must be production-ready or the worker cannot ship beyond monolith mode. **If the LISTEN/NOTIFY subscriber is not retired in this sprint, item 21.2 ships in monolith mode only and `distributed` mode is deferred.**
- ❌ Operators must learn one new env var (`NOTIFICATION_WORKER_INPROCESS`).

### Neutral
- Audit log fan-out adds two new event types (`notification.delivered`, `notification.failed`). No schema change; consumers (audit reader) treat them as opaque event names.

## Alternatives considered

- **Option A — In-process asyncio task only.** Rejected: violates the bursty-load + outage-isolation requirements; cannot scale workers in distributed mode.
- **Option B — External queue (Redis + RQ, RabbitMQ + Celery).** Rejected: introduces new infrastructure; supersedes ADR-001's single-Postgres stance; not justified at current scale.
- **Option C — Always standalone, no in-process mode.** Rejected: violates ADR-001's small-deployment promise; forces every demo / dev environment to run two containers.

## References

- [`adr-001-deployment-modes`](adr-001-deployment-modes.md) — the regime this ADR extends
- [`arch-platform.md`](arch-platform.md) §7 NFRs, §9 risk #14
- [`arch-21.md`](arch-21.md) — system design that motivates this ADR
- [`epic-21-risk-retirement.md`](../epics/epic-21-risk-retirement.md) item 21.2
- [`audit-14-notification-system.md`](audits/audit-14-notification-system.md) Feature 14.1 (DONE) and Feature 14.2 (the gap this closes)
