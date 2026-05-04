---
artifact_id: arch-21
type: arch
producer: B1 Software Architect
consumers: [B2 Data Engineer, C1 Tech Lead, C2 Backend Developer, C3 Frontend Developer, D3 Security Engineer]
upstream: [vision-01-app-buildify, research-01-app-buildify, epic-21-risk-retirement]
downstream: [adr-002-smtp-worker-placement, schema-21, tasks-21]
status: approved
created: 2026-04-29
updated: 2026-04-29
corrections:
  - 2026-04-29 — B3 escalation caught component-list drift in §2.1 + §7. Canonical 9 layout-suite components per epic-15 story 15.1.1 and audit-15 are now reflected. Directory convention corrected to flat frontend/assets/js/components/ (no flex-layout subdir). RBAC page path corrected to frontend/assets/js/rbac.js per audit-04 evidence.
decisions:
  - No new microservice — only one new worker process (notification-worker)
  - SMTP placement decision deferred to adr-002 (binary: in-process vs. standalone container, gated by DEPLOYMENT_MODE)
  - Wildcard permission matching is per-segment and O(segments), not pattern matching
  - Per-entity permission check piggybacks on the entity-definition row already in request scope (no extra DB read)
  - 9 layout components ship as Vanilla JS web components in a NEW directory; no bundler, no external deps
open_questions:
  - Should notification-worker share the platform's Postgres connection pool or open its own? — defer to C2 implementation
  - Bundle-size budget for layout components — placeholder +10 KB; verify after implementation
---

# arch-21 — System Design for 🔴 Risk Retirement (Sprint 1)

> **Upstream**: [`epic-21-risk-retirement`](../epics/epic-21-risk-retirement.md). Designs the architectural shape of the 5 constituent stories. Bound by [`arch-platform.md`](arch-platform.md) and [`adr-001-deployment-modes.md`](adr-001-deployment-modes.md). One new ADR ([`adr-002-smtp-worker-placement.md`](adr-002-smtp-worker-placement.md)) is produced alongside this document.

---

## 1. Context

Epic-21 is a slice epic that retires 5 🔴 risks named in `vision-01` §7. Each constituent story has architectural implications:

| Item | Story | Architectural shape |
|------|-------|---------------------|
| 21.1 | 15.1.1 — Layout Component Suite | NEW frontend directory; 9 Vanilla JS web components; no bundler |
| 21.2 | 14.2.1 — SMTP Email Delivery Adapter | NEW worker process consuming the existing `notifications` LISTEN/NOTIFY channel; one new external dependency (SMTP) |
| 21.3 | 4.1.1 — Role CRUD<br>4.2.1 — Wildcard Permissions | Existing service updates only — no new components |
| 21.4 | 4.2.4 — Per-Entity Permission Enforcement | Existing service update — read-path gains a JSONB check |

The only new architectural decision is the **placement of the SMTP worker** under ADR-001's `DEPLOYMENT_MODE` regime — recorded in `adr-002`.

## 2. Components

### 2.1 New
- **`notification-worker`** (NEW process). Subscribes to the existing `notifications` Postgres LISTEN/NOTIFY channel from audit-14 Feature 14.1 (DONE). For each message, renders the email template (jinja2) and dispatches via `smtplib.SMTP_SSL` (stdlib). Outcome (success / retry / dead-letter) is written to the audit log and to the existing `notifications` table state column. **Placement**: see `adr-002` — in-process asyncio task in monolith mode (config-flagged) or a separate container in distributed mode.
- **9 layout-suite components** (NEW files, flat in the existing `frontend/assets/js/components/` directory — same convention as the UI suite from 15.1.2 DONE): `flex-stack`, `flex-grid`, `flex-sidebar`, `flex-split-pane`, `flex-container`, `flex-section`, `flex-cluster`, `flex-toolbar`, `flex-masonry`. Canonical list matches `epic-15-flex-component-library.md` story 15.1.1 and `audit-15-flex-component-library.md` 15.1.1 evidence. Web Components extending `BaseComponent`. **Correction applied 2026-04-29 per B3 escalation**: earlier draft of this section listed `flex-card`/`flex-modal`/`flex-drawer`/`flex-tabs` as NEW — those are part of 15.1.2 / 15.1.3 (DONE) and out of scope for epic-21.

### 2.2 Modified
- **`backend/app/services/auth_service.py`** — `has_permission(user_permissions, required_code)` updated to evaluate `*` wildcards per segment. Algorithm: split required code on `:`, split each cached permission on `:`, walk pairwise, accept literal match OR `*` in cached permission. O(segments × |user_permissions|) where segments = 3 and |user_permissions| ≤ 200 per story 4.2.1 NFR.
- **`backend/app/api/v1/rbac.py`** — gains `POST /rbac/roles`, `PUT /rbac/roles/{id}`, `DELETE /rbac/roles/{id}` per story 4.1.1 backend AC. `is_system` immutable. Delete blocked with 409 if role is referenced.
- **`backend/app/services/dynamic_entity_service.py`** — every CRUD method reads the loaded `EntityDefinition.permissions` JSONB before executing. If non-null and the user's roles intersect-empty with the action's allowed roles → 403. The entity-definition row is already loaded once per request to resolve table name; no extra DB round-trip is added.

### 2.3 Unchanged but referenced
- **`backend/app/core/event_bus/`** — owns the LISTEN/NOTIFY transport. The `notification-worker` is a new consumer; no change to the bus itself. (See risk #1 for the LISTEN/NOTIFY stub dependency.)
- **`backend/app/services/notification_service.py`** — already enqueues per audit-14.1 DONE; no change.
- **`backend/app/core/audit_logger.py`** — receives one new event type `notification.delivered` (and `.failed`); no schema change.

## 3. Data Flow

### 3.1 Password reset email (item 21.2)
```
client ──POST /auth/forgot-password──> api process
api process ──INSERT row + NOTIFY──> notifications table + Postgres LISTEN/NOTIFY
notification-worker ──LISTEN wakeup──> SELECT pending row, render template
notification-worker ──smtplib.send──> external SMTP server
notification-worker ──UPDATE state, audit_logger.log──> notifications table + audit_logs
```
On SMTP failure: state set to `retry` with backoff (5/30/300 s); after N retries → `dead-letter` + audit entry.

### 3.2 Permission check with wildcard (item 21.3)
```
client request ──Bearer token──> api process
api process ──require_permission("invoices:create:company")──> auth_service.has_permission(user.perms, code)
auth_service ──for each cached perm: split + match each segment──> True (≤ 5 ms p95)
api process ──proceed or 403──> client
```
Wildcard semantics: cached perm `*:*:platform` matches any required code at platform scope; required code `invoices:*:company` is not supported (wildcards live on the *granted* side, never the *required* side).

### 3.3 Per-entity permission check (item 21.4)
```
client ──CRUD on /entities/{tenant_entity}/...──> api process
api process ──load EntityDefinition──> already in request scope from URL→table resolution
api process ──if entity.permissions != null: check user roles ∩ allowed_roles[action]──> 200 or 403
api process ──fall through to global RBAC if entity.permissions == null──> existing path
```

## 4. Integration Points

| Integration | Direction | Failure isolation |
|-------------|-----------|-------------------|
| **SMTP server** (NEW dependency) | outbound from notification-worker | Outage cannot block API write path — emails accumulate in `notifications` table (existing). Worker retries with exponential backoff. After max retries, dead-letter + audit. |
| **Postgres LISTEN/NOTIFY** (existing) | platform ↔ notification-worker | If LISTEN connection drops, worker reconnects + scans for pending rows on resume. No message loss because state is in the table, not the channel. |
| **No new internal service-to-service** | — | — |

Required env vars (new): `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`. Add to `.env.example` and document in Epic 19 deployment.

## 5. NFRs

Inherited from `arch-platform.md` §7 and refined for this epic:

| NFR | Target | Source |
|-----|--------|--------|
| API availability | ≥ 99.5% monthly | arch-platform §7 (unchanged) |
| API p95 latency | < 500 ms | arch-platform §7 (unchanged) |
| Email delivery latency | p95 < 60 s end-to-end (enqueue → SMTP accept) | NEW (story 14.2.1 implied) |
| Permission resolution | p95 < 5 ms for users with up to 200 permissions | story 4.2.1 backend AC |
| Per-entity perm check overhead | ≤ 0 extra DB round-trips per CRUD op | NEW design constraint (entity already loaded) |
| Layout component bundle size | ≤ +10 KB total (uncompressed, all 9 components) | NEW; verify after implementation |
| SMTP delivery success rate | ≥ 99% over rolling 24h (excluding hard bounces) | NEW |

## 6. Risks

| 🚦 | Risk | Mitigation |
|----|------|-----------|
| 🟡 | LISTEN/NOTIFY subscriber stub (arch-platform.md §9 risk #14) is a hard dependency for the notification-worker. If it remains a stub, item 21.2 ships in monolith-only mode. | adr-002 records this as a hard dependency; sprint must retire the stub or accept the constraint. |
| 🟡 | Wildcard matching on hot paths (every authenticated request) — implementation must be O(segments) per cached perm, not regex compile + match. | Code review enforced; benchmark target documented in §5 NFRs. |
| 🟡 | Notification-worker as a separate process introduces a new failure surface (process crash → emails accumulate). | Health check + restart in compose / orchestrator; monitoring task already in epic-13 backlog (Prometheus MISSING). |
| 🟢 | Per-entity perm JSONB read is bounded — entity definition already in cache from request setup. | None needed. |
| 🟢 | Layout components ship without external deps — no new supply chain. | None needed. |

## 7. Reference Map

Files this design touches, grouped by component, with one-line rationale.

### Backend
- `backend/app/services/auth_service.py` — update `has_permission()` for `*` segment matching (story 4.2.1)
- `backend/app/api/v1/rbac.py` — add POST/PUT/DELETE role endpoints (story 4.1.1)
- `backend/app/services/dynamic_entity_service.py` — read `EntityDefinition.permissions` before each CRUD op (story 4.2.4)
- `backend/app/workers/notification_worker.py` — **NEW**; LISTEN/NOTIFY consumer + SMTP dispatch (story 14.2.1)
- `backend/app/workers/__init__.py` — **NEW**; package marker
- `backend/app/services/notification_service.py` — no change (already DONE per audit-14.1)
- `backend/app/core/event_bus/` — no change (consumed by new worker)
- `backend/app/core/audit_logger.py` — no schema change; new event types `notification.delivered` / `notification.failed`

### Frontend
- `frontend/assets/js/components/flex-stack.js` — **NEW**
- `frontend/assets/js/components/flex-grid.js` — **NEW**
- `frontend/assets/js/components/flex-sidebar.js` — **NEW**
- `frontend/assets/js/components/flex-split-pane.js` — **NEW**
- `frontend/assets/js/components/flex-container.js` — **NEW**
- `frontend/assets/js/components/flex-section.js` — **NEW**
- `frontend/assets/js/components/flex-cluster.js` — **NEW**
- `frontend/assets/js/components/flex-toolbar.js` — **NEW**
- `frontend/assets/js/components/flex-masonry.js` — **NEW**
- `frontend/index.html` (or equivalent shell) — register the 9 new components alongside the existing UI/Form suites (no separate barrel needed — convention is per-component `<script>` imports per 15.1.2 / 15.1.3 DONE; verify with C3)
- `frontend/assets/js/rbac.js` — refactor existing RBAC page (per `audit-04` 4.1.2 evidence) to use new layout components (proves integration per item 21.3 coordination AC)

### Configuration / Deployment
- `.env.example` — add `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `NOTIFICATION_WORKER_INPROCESS`
- `docker-compose.yml` (prod) — add `notification-worker` service for distributed mode (Epic 19 follow-up — not blocking for monolith ship)

## 8. Decisions

- No new microservice. The only new process is `notification-worker`, which is a worker — not an HTTP-serving service. Module-system additions are out of scope.
- ADR placement: SMTP worker placement is significant enough for an ADR (extends ADR-001's `DEPLOYMENT_MODE` regime to a new component category). Wildcard algorithm and per-entity perm check are NOT — they're routine service updates following existing patterns.
- The `notifications` table + LISTEN/NOTIFY channel from audit-14.1 is the canonical bus for this work. We do not introduce a new queue (Redis, RabbitMQ) because that would supersede ADR-001's "single Postgres" stance.
- Layout components mirror the convention of the existing UI / Form suites (audit-15.1.2 / 15.1.3 DONE) — same directory pattern, same instantiation style. No framework adoption.

## 9. Open Questions

- Should `notification-worker` share the platform's Postgres connection pool or open its own connection? Deferred to C2 implementation; default to its own connection (one LISTEN + one query channel) unless C2 finds a reason otherwise.
- Layout-component bundle-size budget — placeholder +10 KB; revisit after implementation.
- The `EntityDefinition.permissions` JSONB shape (`{role_name: [actions]}`) implies per-role-name matching; what happens when a tenant renames a role? Out of scope here (role-name immutability is implied by story 4.1.1 system-role rules; tenant-role rename consequences belong to a separate ADR if the case arises).

## 10. Hand-off

`status: review`. Once `approved`:
- **B2 Data Engineer** — confirm "no schema changes" with a one-paragraph `schema-21.md` (or skip — see epic-21 hand-off).
- **C1 Tech Lead** — gated on B2 + B3 also approved; produces `tasks-21.md` (sprint backlog).
- **C2 Backend Developer** — implements §7 backend list per item ordering in epic-21.
- **C3 Frontend Developer** — implements §7 frontend list; refactors `rbac-page.js` once layout suite lands.
- **D3 Security Engineer** — review wildcard algorithm and SMTP credential handling.
