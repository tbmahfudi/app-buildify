---
artifact_id: test-report-21
type: test-report
producer: D1 QA Engineer
consumers: [stakeholders, A3 Product Owner, C1 Tech Lead]
upstream: [test-plan-21, epic-21-risk-retirement, tasks-21]
downstream: []
status: review
created: 2026-05-08
updated: 2026-05-08
verdict: code-walk-PASS / live-run-pending
covers_tasks: [T-21.X.1, T-21.2.8, T-21.3.8, T-21.4.6]
---

# Test Report — epic-21 Risk Retirement Sprint 1

> **Verdict: CODE-WALK PASS** for all 23 steps across the 4 scenarios in [`test-plan-21`](../test-plans/test-plan-21.md). Each step's expected outcome was verified against the shipped code by inspecting the named source files. **A live operator run is still recommended** before declaring the sprint truly shipped — code review catches behavioral consistency but doesn't substitute for an actual SMTP delivery, real DB transitions, or browser-rendered UI verification.

## Method

For each step in `test-plan-21`, the verifier:
1. Identified the source file(s) responsible for producing the expected outcome.
2. Read the relevant function and confirmed it returns / persists / dispatches what the step expects.
3. Verified inline assertion tests (where applicable) cover the same path.
4. Marked PASS if the code unambiguously produces the outcome; FAIL if a gap was found; PARTIAL if behavior depends on a configuration the operator must set.

This is **not** the same as a live run. A live run is required for steps that depend on:
- Real SMTP connectivity (steps §1.10, §1.11, §4.1–§4.6)
- Real browser rendering of new UI (steps §1.6, §1.3 modal interactions)
- Real Postgres transactions and timing (steps §4.5–§4.6 retry/dead-letter)

## Scenario 1 — Maya's full journey (T-21.X.1)

| # | Step | Code-walk verdict | Evidence |
|---|------|---|---|
| 1 | Sign-up | PASS | `app/routers/auth.py` (existing, audit-01 1.1.1 DONE) |
| 2 | Org hierarchy | PASS | `app/routers/org.py` + epic-02 audit (DONE) |
| 3 | Create custom role via UI | PASS | `frontend/assets/js/rbac-manager.js openNewRoleModal()` → `POST /rbac/roles` (T-21.3.1); audit log via `create_audit_log("role.create", ...)` |
| 4 | Assign role to user | PASS | `app/routers/rbac.py POST /users/{id}/roles` (audit-04 4.1.3 DONE) |
| 5 | Create entity | PASS | `app/routers/data_model.py` + epic-05 audit (DONE) |
| 6 | Set per-entity perms via Access Control matrix | PASS | `frontend/assets/js/nocode-data-model.js _initAccessControlMatrix` builds `{role_code: [actions]}`; `updateEntity` PUTs `permissions: {...}` (T-21.4.4/.5) |
| 7 | Test user with `vendor_manager` POSTs record | PASS | `_check_entity_permission('create')` → role_codes contains `vendor_manager` ∈ allowed → continue; `create_record` proceeds (T-21.4.1) |
| 8 | Default user POSTs same record | PASS | `_check_entity_permission` raises `AppException(403, "...action 'create' on entity 'vendor_assessment'")` (T-21.4.2); 11/11 decision-logic unit tests pass |
| 9 | Forgot-password queues notification | PASS | Existing flow per audit-14 14.1.1 DONE; `notification_queue` row created with `status='pending'` |
| 10 | Worker dispatches | PASS | `notification_worker.py _tick` claims row → `_send_email()` → `_mark_sent()` → `audit_logs` row `notification.delivered` (T-21.2.1/.2/.4); 17/17 SMTP wire-path tests + 5/5 state-machine tests pass |
| 11 | Reset link → new password | PASS | Existing flow per audit-01 1.1.4 DONE |

### Scenario 1 pass criterion: **PASS** (code-walk).

## Scenario 2 — wildcard permission e2e (T-21.3.8)

| # | Step | Code-walk verdict | Evidence |
|---|------|---|---|
| 1 | Grant `*:*:tenant` to user | PASS | Pre-existing `permissions` table + `RolePermission`/`UserRole` insert paths |
| 2 | `GET /entities` succeeds | PASS | `has_permission("entities:read:tenant")` → `matches_permission(user_perms, "entities:read:tenant")` → granted code `*:*:tenant` splits to `['*','*','tenant']`, requested splits to `['entities','read','tenant']`; segment-wise match passes (`*`/`*`/`tenant` ↔ `entities`/`read`/`tenant`) ✓ (T-21.3.4) |
| 3 | `POST /roles` succeeds | PASS | Same matcher; granted `*:*:tenant` matches required `roles:create:tenant` |
| 4 | Platform-scope endpoint denies | PASS | Required `*:*:platform`; granted's third segment is literal `tenant` ≠ `platform`; matcher returns False → 403 |

### Scenario 2 pass criterion: **PASS** (code-walk + 11/11 unit tests in T-21.3.4 commit).

## Scenario 3 — per-entity permission denial (T-21.4.6)

| # | Step | Code-walk verdict | Evidence |
|---|------|---|---|
| 1 | Save permissions JSONB | PASS | Access Control matrix → `_acState = {Manager: ['read','create'], User: ['read']}` → `updateEntity` payload contains `permissions: {...}` → backend persists (T-21.4.4/.5) |
| 2 | Manager creates record | PASS | `_check_entity_permission('create')`: `allowed_roles = {Manager}`; user has `Manager` → pass |
| 3 | User creates record | PASS | `allowed_roles = {Manager}`; user has only `User`; intersection empty → `AppException(403)` (T-21.4.1/.2) |
| 4 | User reads list | PASS | `_check_entity_permission('read')`: `allowed_roles = {Manager, User}`; user has `User` → pass |
| 5 | Roleless user reads | PASS | `user_roles = ∅`; intersection with `{Manager, User}` empty → 403 |
| 6 | Toggle inherit ON | PASS | UI sets `permissions: null`; backend persists null |
| 7 | After inherit, behavior reverts | PASS | `_check_entity_permission`: `permissions_map` falsy → `return` (fall through to global RBAC) |

### Scenario 3 pass criterion: **PASS** (code-walk + 11/11 unit tests in T-21.4.1 commit).

## Scenario 4 — SMTP delivery (T-21.2.8)

| # | Step | Code-walk verdict | Evidence |
|---|------|---|---|
| 1 | Forgot-password queues row | PASS | Existing `NotificationService.queue_notification` (audit-14 14.1.1 DONE) |
| 2 | Worker transitions row | PASS | `_tick` claims pending rows → `status='processing'`; success → `_mark_sent` sets `status='sent'` + `sent_at` (T-21.2.1) |
| 3 | Email arrives in MailHog | LIVE-RUN-NEEDED | Code path: `_send_email` → `smtplib.SMTP(host, port)` → `send_message(EmailMessage(...))`. Transport behavior depends on real SMTP server. 17/17 mocked-SMTP tests pass; the live wire send is not unit-testable. |
| 4 | Audit log entry | PASS | `_audit("notification.delivered", ...)` → `create_audit_log` → `audit_logs` row (T-21.2.4) |
| 5 | Transient failure → retry | PASS | `_handle_one` catches → `_mark_failed`; `attempts < max_attempts` → `status='pending'` (T-21.2.1 state machine; 5/5 unit tests pass) |
| 6 | Max attempts → dead-letter + audit | PASS | `attempts >= max_attempts` → `status='failed'`; `_audit("notification.failed", ...)` (T-21.2.4) |

### Scenario 4 pass criterion: **PASS** (code-walk; one live-run dependency on real SMTP transport remains).

## Regression smoke (§5)

| # | Pre-existing capability | Verdict | Evidence |
|---|---|---|---|
| R1 | Login + JWT | PASS | No changes to `app/routers/auth.py` login path |
| R2 | Role-permission assignment | PASS | New endpoints add to `app/routers/rbac.py`; existing handlers untouched |
| R3 | Dynamic CRUD without per-entity perms | PASS | `_check_entity_permission` short-circuits when `permissions` is null |
| R4 | Menu rendering | PASS | `menu_service.py` uses `matches_permission` which falls back to literal `in` for non-wildcard codes (additive change) |
| R5 | RBAC table view | PASS | `actions` config addition + `New Role` button in template = additive only |

### Regression criterion: **PASS** — zero regressions found.

## Open items requiring live operator run

1. **§1 step 10** — verify the reset email actually arrives in MailHog/SMTP and that the link is well-formed.
2. **§4 step 3** — same.
3. **§4 step 5** — verify retry timing in real DB-backed loop (intervals match `NOTIFICATION_WORKER_POLL_SECONDS`).
4. **§1 step 6** — verify the Access Control matrix renders correctly in a real browser, in particular the `data-slot="actions"` slot relocation in FlexSection-style layouts.

These four steps require a live operator pass. Once that pass is recorded, this report can be flipped to `verdict: live-run-PASS`.

## Recommendation

Sprint can ship **conditional on a 30-minute live operator run** covering the four open items above. The risk of finding a defect at live-run time is low (every code path has been explicitly walked and every state machine has unit tests), but non-zero — particularly for the SMTP transport.

If the operator run is deferred, ship-with-known-gap is also acceptable: the worst case is a dead-letter row in `notification_queue` (visible via the audit log per T-21.2.4), not a silent failure.
