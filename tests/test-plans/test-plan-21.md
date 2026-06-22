---
artifact_id: test-plan-21
type: test-plan
producer: D1 QA Engineer
consumers: [stakeholders, operators, future automation engineers]
upstream: [epic-21-risk-retirement, tasks-21, vision-01-app-buildify, research-01-app-buildify]
downstream: [test-report-21]
status: approved
created: 2026-05-08
updated: 2026-06-18
covers_tasks: [T-21.X.1, T-21.2.8, T-21.3.8, T-21.4.6]
---

# Test Plan — epic-21 Risk Retirement Sprint 1

> **Format**: manual smoke-test runbook for operators. No automated test framework exists yet (per `audit-13` 13.4) so each scenario is a hand-runnable script with explicit prerequisites, steps, and expected outcomes. Each step is also code-walkable: an inspector can verify the implementation will produce the expected behavior by reading the cited source. The companion [`test-report-21`](../test-reports/test-report-21.md) records the results.

## 1. Headline scenario — Maya's full journey (T-21.X.1)

**Goal**: prove that the four user-journey steps that were broken pre-sprint (per `research-01-app-buildify` §2) now work end-to-end on a fresh tenant.

### Prerequisites

- A clean Postgres database with the platform's migrations applied (`alembic upgrade head` runs automatically in `lifespan`)
- The platform API running on port 8000 (or behind nginx on port 80)
- Either an SMTP server reachable at `SMTP_HOST` (production) **or** MailHog running on `localhost:1025` with `SMTP_USE_TLS=false` (dev)
- The `notification-worker` running — either in-process (`NOTIFICATION_WORKER_INPROCESS=true`) or as a separate container
- A superuser account to bootstrap the first tenant + tenant admin

### Steps

| # | Step | Expected outcome | Maya journey step |
|---|------|------------------|-------------------|
| 1 | Sign up the first tenant + tenant admin via existing tenant onboarding | Tenant + admin user exist; admin can log in | step 1 (sign-up) |
| 2 | Tenant admin defines an org hierarchy (one company, two branches) | `companies` + `branches` rows present; admin sees them in the org page | step 2 (org modeling) |
| 3 | Tenant admin opens **Access Control → Roles** tab; clicks **New Role**; creates `vendor_manager` with description "Manages vendor records"; copy permissions from `Manager` | New row in `roles` with `is_system=false`, `tenant_id=<current>`; permission rows copied; success toast; `audit_logs` shows `role.create` | step 3 (RBAC, was broken) |
| 4 | Tenant admin assigns `vendor_manager` to a new test user via existing user-management UI | `user_roles` row created | step 3 (RBAC) |
| 5 | Tenant admin opens NoCode → Data Model; creates entity `vendor_assessment` with fields `name`, `risk_score` | Entity table created; entity definition published | step 4 (entity design) |
| 6 | Tenant admin edits the new entity; toggles **Inherit from global RBAC** OFF; sets matrix to `vendor_manager: [create, read, update]`, `User: [read]`; clicks Save | `EntityDefinition.permissions` JSONB = `{vendor_manager: [create, read, update], user: [read]}` | step 7 (per-entity perms, was broken) |
| 7 | Log in as the test user (the one with `vendor_manager` role); call `POST /api/v1/data/{entity}/records` with sample data | 201 Created; record persisted with `created_by=<test_user>` | step 7 |
| 8 | Log in as a user with only the default `User` role; call `POST /api/v1/data/{entity}/records` | **403 Forbidden** with `AppException` detail `"Per-entity permission denied: action 'create' on entity 'vendor_assessment'"` | step 7 |
| 9 | As an unauthenticated user, hit `POST /auth/forgot-password` with the test user's email | 200 OK (per existing flow); a row appears in `notification_queue` with `status='pending'`, `delivery_method='email'`, `notification_type='password_reset'` | step 8 (password reset, was broken) |
| 10 | Within ~5 s, the notification-worker picks up the row | DB row `status='processing'` → `status='sent'`; `audit_logs` shows `notification.delivered`; the email arrives in MailHog (or the configured SMTP inbox) | step 8 |
| 11 | Click the reset link in the email; submit a new password | 200 OK; user can log in with the new password | step 8 |

### Pass criteria

All 11 steps produce the listed expected outcome with no error toast / 500 response / dead-letter row.

---

## 2. Sub-scenario A — wildcard permission e2e (T-21.3.8)

**Goal**: prove `*:*:tenant` grants behave like a true wildcard rather than a literal segment match.

### Steps

| # | Step | Expected outcome |
|---|------|------------------|
| 1 | As superuser, grant a test user the permission code `*:*:tenant` (pre-existing seed in `permissions` table or insert via SQL) | `RolePermission` or direct `UserRole` row exists |
| 2 | Log in as the test user; hit `GET /api/v1/data-model/entities` | 200 OK with the tenant's entity list (would be 403 under literal-`in` matching since the user has no `entities:read:tenant` literal grant) |
| 3 | Hit `POST /api/v1/rbac/roles` with valid body | 201 Created (since `roles:create:tenant` is matched by `*:*:tenant`) |
| 4 | Hit any endpoint requiring `*:*:platform` (e.g. cross-tenant admin) | **403 Forbidden** — wildcard at tenant scope must NOT escalate to platform |

### Pass criteria

Steps 2 + 3 succeed; step 4 returns 403. Demonstrates that wildcard matches the requested code's scope but does not escalate scope.

### Verification path
Code-walk: `backend/app/core/dependencies.py matches_permission()` — segments split on `:`, granted `*` matches any literal at the same position; `tenant` segment in granted does not match `platform` in required.

---

## 3. Sub-scenario B — per-entity permission denial (T-21.4.6)

**Goal**: prove a user without the requisite role gets 403 when their action isn't listed in `EntityDefinition.permissions`.

### Steps

| # | Step | Expected outcome |
|---|------|------------------|
| 1 | Define entity `secret_log` with permissions JSONB `{Manager: [read, create], User: [read]}` | Saved successfully via Access Control matrix UI (T-21.4.4/.5) |
| 2 | As a user holding `Manager` role: `POST /api/v1/data/secret_log/records` | 201 Created |
| 3 | As a user holding only `User` role: `POST /api/v1/data/secret_log/records` | **403 Forbidden** with `AppException` detail mentioning `'create'` and `'secret_log'` |
| 4 | As the same `User`: `GET /api/v1/data/secret_log/records` | 200 OK with the list |
| 5 | As a user with **no** roles in the JSONB at all: `GET /api/v1/data/secret_log/records` | **403 Forbidden** |
| 6 | Toggle the entity's "Inherit from global RBAC" ON, save | `EntityDefinition.permissions` becomes null |
| 7 | Repeat step 5 | 200 OK if global RBAC grants read; 403 if global denies. Per-entity check is no longer in effect. |

### Pass criteria

Steps 2, 4, 6, 7 behave per global RBAC rules; steps 3, 5 return 403.

### Verification path
Code-walk: `backend/app/services/dynamic_entity_service.py _check_entity_permission()` — superuser bypass first, then null/malformed JSONB → fall through, then `user_roles ∩ allowed_roles[action]` membership check.

---

## 4. Sub-scenario C — SMTP delivery (T-21.2.8)

**Goal**: prove a queued email actually arrives at the configured SMTP destination.

### Prerequisites for local-dev verification
- Run MailHog: `docker run -p 1025:1025 -p 8025:8025 mailhog/mailhog`
- Set in `.env`: `SMTP_HOST=mailhog` (or `localhost`), `SMTP_PORT=1025`, `SMTP_FROM=test@local`, `SMTP_USE_TLS=false`
- Ensure either `NOTIFICATION_WORKER_INPROCESS=true` OR the `notification-worker` container is running

### Steps

| # | Step | Expected outcome |
|---|------|------------------|
| 1 | Trigger `POST /auth/forgot-password` with a registered user's email | 200 OK; new row in `notification_queue` |
| 2 | Wait ≤ 10 s (worker poll interval is 5 s + dispatch time) | Row transitions: `pending` → `processing` → `sent` |
| 3 | Open MailHog UI at `http://localhost:8025` | The reset email appears in the inbox; subject and body rendered from `notification_queue.message`/`subject` (via jinja2 `template_data`) |
| 4 | Check `audit_logs` table | One `notification.delivered` row with `entity_type='notification_queue'`, `entity_id=<row_id>`, `status='success'` |
| 5 | Stop MailHog mid-burst (simulate transient failure); trigger another forgot-password; wait | Worker logs transient failure; row stays at `pending` with incremented `attempts`; restart MailHog → next tick retries successfully |
| 6 | With MailHog stopped: trigger forgot-password; let it exhaust `max_attempts` (default 3) | Row transitions to `status='failed'` (dead-letter); `audit_logs` has `notification.failed` row with `error_message` populated |

### Pass criteria

Steps 1–4 succeed (happy path). Steps 5–6 demonstrate retry + dead-letter semantics.

### Verification path
Code-walk: `backend/app/workers/notification_worker.py` — `_tick()` claims pending rows; `_handle_one()` invokes `_send_email()`; success → `_mark_sent` + `notification.delivered` audit; failure → `_mark_failed` increments attempts, falls back to `pending` until max → `failed` + `notification.failed` audit.

---

## 5. Regression smoke (no-new-feature impact)

Verify that previously-DONE behaviors still work after the sprint's changes:

| # | Pre-existing capability | Quick check |
|---|-------------------------|-------------|
| R1 | Login + JWT token issuance (audit-01 1.1.1 DONE) | `POST /auth/login` with valid creds returns 200 + tokens |
| R2 | Existing role assignment (audit-04 4.1.2 DONE) | Hit `POST /api/v1/rbac/roles/{id}/permissions` — works as before |
| R3 | Dynamic CRUD on entities WITHOUT per-entity perms set (existing default) | Permissions JSONB = null → behavior identical to pre-sprint |
| R4 | Existing menu rendering (audit-04 4.2.3 DONE) | Menu still filters items by user permissions; new wildcard support is additive |
| R5 | RBAC table view (audit-04 4.1.2 DONE) | Roles table renders normally; new "New Role" button + delete action are additive |

### Pass criteria
R1–R5 behave identically to pre-sprint. The sprint introduces zero regressions.

---

## 6. What this plan does NOT cover

- **Performance under load.** NFRs from `arch-21` §5 are documented but only spot-tested (e.g. wildcard hot path measured at 6.1 µs/call in T-21.3.4 commit; SMTP latency target was set but not load-tested).
- **Production SMTP-provider compatibility.** The dev path was verified with MailHog + plain SMTP. Real providers (SendGrid, AWS SES, Office365 SMTP) need a separate compatibility pass.
- **Tenant-isolation defense-in-depth** (`arch-platform.md` §9 risk #1). Pre-existing concern; out of scope.
- **Email-template variations** (story 14.2.2 still MISSING). The sprint ships inline jinja2 rendering of the queue row's `message`/`subject`; richer per-event templates with per-tenant overrides are deferred.

---

## 7. How to run

1. Set up the prereqs in §1.
2. Walk through §1 step-by-step in a real browser + DB session.
3. Optionally execute §2, §3, §4 individually if specific story-level verification is needed.
4. Record outcomes in [`test-report-21`](../test-reports/test-report-21.md). Each failed step should reproduce a clear error (not silent), per the audit-log coverage shipped in T-21.2.4.
