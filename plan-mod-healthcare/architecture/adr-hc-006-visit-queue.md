---
artifact_id: adr-hc-006
type: adr
module: healthcare_registration
status: proposed
producer: B1 Backend Architect
upstream: [BACKLOG.md (v3), adr-hc-001, adr-hc-002, adr-hc-005, schema-hc-01, epic-09-visit-registration-queue]
created: 2026-07-02
---

# ADR-HC-006 — Visit / Registration & Queue Model

## Status

proposed

## Context

BACKLOG v3 adds **Registration/Visit + Queue** as a NEW clinical domain (module
`healthcare_registration`, epic-09, MVP). Today the suite has `hcs_appointments` (booking) and
`hc_encounters` (clinical record) but no representation of the *front-desk visit* that connects them:
check-in (from a booked appointment or as a walk-in), payment-category / insurance tagging, referral
capture, department routing, and a live **queue board** for waiting rooms.

Design questions:

1. **Visit model** — what carries the check-in event, its payment/insurance/referral metadata, its
   department routing, and the link `appointment_id → encounter_id`?
2. **Queue model** — how are tickets issued, stationed, and advanced through their lifecycle
   (waiting → called → skipped → recalled → transferred → served)?
3. **Real-time delivery** — how does the waiting-room queue board stay current: polling or
   server-push?

**Constraints:**
- ADR-HC-001: both new tables are branch-scoped (`tenant_id` + `branch_id` + RLS `§D4`).
- ADR-HC-005: department routing references `hc_departments.id`.
- The visit references `hcs_appointments.id` (nullable, walk-ins have none), `hc_patients.id`,
  `hcb_insurance_profiles.id` (nullable), and produces/links `hc_encounters.id` (nullable until the
  clinician opens the encounter).

## Decision

### D1 — `hcr_visits`: the check-in / registration record

A new branch-scoped table `hcr_visits` (canonical name per BACKLOG) is the front-desk visit:

```
hcr_visits (
  id, tenant_id, branch_id,
  patient_id            → hc_patients.id,
  appointment_id nullable → hcs_appointments.id,   # NULL for walk-in
  visit_type ∈ {appointment, walk_in},
  payment_category,                                # e.g. self_pay, bpjs, private_insurance, corporate
  insurance_profile_id nullable → hcb_insurance_profiles.id,
  referral_source,                                 # e.g. self, gp_referral, internal, corporate
  department_id         → hc_departments.id,       # routing target (ADR-HC-005)
  status,                                          # visit lifecycle (below)
  checked_in_at,
  encounter_id nullable → hc_encounters.id,        # set when clinician opens the encounter
  created_at, updated_at
)
```

- **Two entry paths, one table.** `visit_type = 'appointment'` sets `appointment_id`; `visit_type =
  'walk_in'` leaves it NULL. A CHECK enforces `appointment_id IS NOT NULL` iff `visit_type =
  'appointment'`.
- **`appointment_id → encounter_id` bridge.** The visit is the join that connects a booking to its
  clinical encounter. On check-in, `encounter_id` is NULL; when the assigned clinician opens the
  encounter, the healthcare base module writes `hcr_visits.encounter_id` and mirrors
  `hc_encounters.appointment_id` (existing nullable column). This keeps the appointment→encounter
  provenance in one place without adding columns to `hc_encounters`.
- **`payment_category` and `insurance_profile_id`** are captured at registration so downstream
  billing (epic-03) and revenue reporting (ADR-HC-008 `v_hc_revenue`) can attribute by payer without
  re-deriving it. `insurance_profile_id` is nullable (self-pay visits have none).
- **`department_id`** routes the visit to a clinical department (ADR-HC-005); the queue ticket
  inherits this routing.
- **Visit `status`** lifecycle: `registered → waiting → in_service → completed → cancelled`
  (`no_show` for appointment visits that never check in is represented on `hcs_appointments`, not
  here). The visit status is a coarse summary; fine-grained queue movement lives on the ticket (D2).
- **PHI stance.** `hcr_visits` stores no free-text clinical content; it is PHI-by-association
  (`patient_id`, `encounter_id`) and therefore RLS-protected exactly like `hcb_invoices` /
  `hcp_prescriptions` in schema-hc-01. No column requires `EncryptedPHIType`.

### D2 — `hcr_queue_tickets`: the queue lifecycle

A new branch-scoped table `hcr_queue_tickets` (canonical name per BACKLOG):

```
hcr_queue_tickets (
  id, tenant_id, branch_id,
  visit_id      → hcr_visits.id,
  department_id → hc_departments.id,               # queue is per department/station
  ticket_number,                                   # human-facing, per branch/dept/day
  station,                                         # counter/room the ticket is called to
  status ∈ {waiting, called, skipped, recalled, transferred, served},
  called_at, served_at,
  created_at, updated_at
)
```

- **One active ticket per visit per department.** A visit routed to a department gets a ticket; a
  *transfer* to another department (`status = 'transferred'`) closes the current ticket and issues a
  new `waiting` ticket in the target department (a `transferred_to_id` self-ref, see schema-hc-02).
- **`ticket_number`** is human-facing and unique per `(branch_id, department_id, service_day)`;
  generation is application-layer (monotonic per department per day, optional `station`/kind prefix).
- **Lifecycle** matches the canonical set exactly: `waiting` (issued) → `called` (staff calls it to a
  `station`, sets `called_at`) → `served` (`served_at`), with `skipped` (no-show at call),
  `recalled` (re-announced after a skip), and `transferred` (moved to another department). Only these
  six values are permitted (CHECK constraint).
- **Timestamps** `called_at` / `served_at` drive wait-time and service-time metrics surfaced by
  `v_hc_queue` (ADR-HC-008).

### D3 — Real-time delivery: short-poll now, SSE-ready contract

**Decision: the queue board uses HTTP short-polling of a read endpoint in v1, behind a delivery
contract designed so it can be upgraded to Server-Sent Events (SSE) later without a data-model or API
shape change.**

Endpoint: `GET /api/v1/modules/healthcare/registration/queue?department_id=…` returns the current
ordered ticket list for the caller's branch/department (branch-scoped via `healthcare_branch_session`,
ADR-HC-001). The waiting-room board polls it on a short interval (default 5 s, tunable per branch).

**Rationale for polling over SSE/WebSocket in v1:**

| Factor | Polling | SSE / WebSocket |
|---|---|---|
| Fit with platform | Plain FastAPI route through the existing `healthcare_branch_session` dependency + `BranchScopeListener` + RLS. No new infra. | Requires a long-lived connection layer, sticky routing, and a branch-scoped fan-out/pub-sub the platform does not yet provide. |
| Branch isolation | Each poll re-authorizes the branch header and re-applies RLS — isolation is enforced per request, identical to every other endpoint. | A persistent stream must re-assert `tenant_id`/`branch_id` scoping for its whole lifetime; a subscription bug could leak cross-branch ticket state. Higher-risk against ADR-HC-001. |
| Scale | A waiting-room board is one screen per department; a handful of pollers per branch at 5 s is negligible load. | Optimizes for many concurrent subscribers — not the MVP shape. |
| Operational simplicity | No connection lifecycle, reconnect, or heartbeat handling. | Reverse-proxy buffering, timeouts, and reconnect logic to manage. |

**Upgrade path.** The read endpoint returns a `queue_version` (max `updated_at` epoch for the
department) so a future SSE endpoint can emit the same ordered payload as events while polling clients
keep working. The ticket lifecycle timestamps (`called_at`, `served_at`, `updated_at`) already give
SSE everything it needs; no schema change is required to switch transports. WebSocket is not chosen —
the queue board is a one-directional broadcast; SSE is the simpler push primitive if/when push is
warranted (revisit at R3 exec-dashboard scale, ADR-HC-008).

### D4 — Isolation conformance

Both tables are `__tenant_scoped__` + `__branch_scoped__`, filtered by `BranchScopeListener` and the
ADR-HC-001 `§D4` RLS policy. All visit/queue endpoints use `healthcare_branch_session` (missing
`X-Branch-ID` ⇒ 422; ADR-HC-001 `§D2`). The `clinic_owner` `branch_id = 'ALL'` bypass applies to
read-only aggregate queue reporting only, never to ticket mutation.

## Consequences

### Positive
- **Single visit record** ties appointment ⇄ walk-in ⇄ encounter ⇄ payer without touching
  `hcs_appointments` or `hc_encounters` schemas beyond their existing nullable link columns.
- **Canonical queue lifecycle** (`waiting/called/skipped/recalled/transferred/served`) is captured
  exactly, giving reporting (`v_hc_queue`) clean wait/service metrics.
- **Polling keeps isolation simple** — every board refresh is a normal branch-scoped request; no
  new persistent-connection attack surface for PHI/branch leakage.
- **SSE-ready** via `queue_version` + lifecycle timestamps; transport can change without a migration.

### Negative
- **Poll latency** (up to the poll interval, default 5 s) before a called ticket appears on the
  board. Mitigation: interval is tunable per branch; acceptable for waiting-room UX; SSE upgrade path
  documented.
- **Transfer = new ticket** adds a row per department hop. Mitigation: `transferred_to_id` self-ref
  preserves the chain; reporting follows the chain by `visit_id`.
- **Polling load at very large branches** is higher than push. Mitigation: negligible at MVP board
  counts; revisit with SSE at exec-dashboard scale.

## Alternatives Considered

| Alternative | Rejected because |
|---|---|
| Model the visit as extra columns on `hcs_appointments` | Walk-ins have no appointment; overloading the appointment table with front-desk/queue state couples two lifecycles and breaks the clean appointment→visit→encounter chain. |
| Put queue state on `hcr_visits` (no ticket table) | A visit can be transferred across departments, producing multiple sequential queue positions; a single status column cannot model the ticket-per-department lifecycle or per-department numbering. |
| WebSocket for the board in v1 | Bidirectional channel is unnecessary for a broadcast board; adds connection-lifecycle complexity and a harder-to-isolate persistent surface. SSE is the simpler push option if needed. |
| SSE from day one | Requires branch-scoped fan-out infra the platform lacks; a long-lived stream is a higher-risk surface against ADR-HC-001 branch isolation than per-request polling. Deferred behind an SSE-ready contract. |

## Reference Map

| File | Relevance |
|------|-----------|
| `modules/healthcare/backend/models.py` | `hc_encounters.appointment_id` (existing nullable link mirrored by the visit) |
| `plan-mod-healthcare/architecture/adr-hc-001-branch-isolation-strategy.md` | Branch isolation + `healthcare_branch_session` + RLS `§D4` |
| `plan-mod-healthcare/architecture/adr-hc-005-org-linkage-departments.md` | `hc_departments` routing target for `department_id` |
| `plan-mod-healthcare/architecture/adr-hc-008-reporting-integration.md` | `v_hc_queue`, `v_hc_daily_patients` consume visit/ticket data |
| `plan-mod-healthcare/architecture/schema-hc-02.md` | DDL for `hcr_visits`, `hcr_queue_tickets` |
| `plan-mod-healthcare/BACKLOG.md` | v3 Canonical names for visit/queue columns |
