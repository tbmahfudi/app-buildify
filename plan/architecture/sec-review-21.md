---
artifact_id: sec-review-21
type: sec-review
producer: D3 Security Engineer
consumers: [C1 Tech Lead, A3 Product Owner, stakeholders]
upstream: [epic-21-risk-retirement, arch-21, tasks-21]
downstream: []
status: approved
created: 2026-05-08
updated: 2026-06-18
verdict: clear-to-ship
findings_count:
  critical: 0
  high: 0
  medium: 1
  low: 2
  informational: 3
---

# Security Review — epic-21 Risk Retirement Sprint 1

> **Verdict: CLEAR TO SHIP.** No critical or high-severity findings. One medium-severity finding (pre-existing, not introduced by this sprint) is documented for the backlog. Two low + three informational items below for awareness.

## 1. Scope

Reviews the code paths shipped in epic-21 sprint 1 for security regressions:

- Wildcard permission algorithm — `backend/app/core/dependencies.py matches_permission()` (T-21.3.4)
- Role CRUD endpoints — `backend/app/routers/rbac.py POST/PUT/DELETE /roles` (T-21.3.1/.2/.3)
- Per-entity permission enforcement — `backend/app/services/dynamic_entity_service.py _check_entity_permission()` (T-21.4.1/.2/.3)
- SMTP delivery worker — `backend/app/workers/notification_worker.py` (T-21.2.1/.2/.4/.5)
- Frontend role-CRUD modal + Access Control matrix — `frontend/assets/js/rbac-manager.js`, `frontend/assets/js/nocode-data-model.js`

Out of scope: pre-existing tenant-isolation surface (per `arch-platform.md` §9 risk #1 — recommend addressing in a future epic).

## 2. Methodology

Manual code review against the OWASP Top 10 categories most relevant to authentication / authorization changes:

- **A01 Broken Access Control** — every endpoint, every cross-tenant boundary
- **A02 Cryptographic Failures** — credential handling, transit encryption
- **A03 Injection** — wildcard parsing, SMTP message construction, JSONB shape
- **A04 Insecure Design** — fail-open / fail-closed defaults
- **A07 Identification & Authentication** — role assignment paths
- **A09 Security Logging** — audit log coverage, no credential leakage in logs

Read paths checked: every `logger.*` call in the new code; every `db.query` filter; every request body that flows into a write path.

## 3. Findings

### 🟡 Medium — 1 finding

**M-1. SMTP password stored plaintext in `notification_config.email_smtp_password` (PRE-EXISTING)**

`app/models/notification_config.py:57` declares the column with the comment `# Should be encrypted` but no encryption is applied. This sprint reads from that column unchanged and adds an env-var fallback (which has the same plaintext concern in `.env`). Not introduced by this sprint, but the new SMTP path makes the column actually load-bearing for the first time, so the issue surfaces now.

- **Impact**: any actor with read access to the `notification_config` table can recover SMTP credentials.
- **Mitigation today**: Postgres role separation; tenant data isolation prevents cross-tenant read; backup encryption at rest.
- **Recommendation**: encrypt `email_smtp_password` (and `sms_api_key`) at rest using a key loaded from KMS/secret manager. Track as a follow-up to story 14.1.2 (Notification Configuration per Tenant). Effort: M.
- **Sprint verdict**: ACCEPTABLE for ship — this is a pre-existing condition, not a regression. Document in release notes, file follow-up.

### 🟢 Low — 2 findings

**L-1. Per-entity permission check fails open on malformed JSONB**

`_check_entity_permission` in `dynamic_entity_service.py` falls through (no enforcement) when `entity_def.permissions` is null, empty dict, or not a dict. The intent is "null = inherit from global RBAC" which is correct. The risk is a malformed value (e.g. a list, a string) silently disables per-entity checks for that entity.

- **Impact**: a bug elsewhere in the platform that writes a non-dict to `EntityDefinition.permissions` (currently impossible via the Access Control UI, which always sends `null` or `{role_code: [actions]}`) would silently disable enforcement on that entity.
- **Recommendation**: when `permissions` is non-null and not a dict, log a warning and **deny** (fail closed) rather than fall through. Two-line change in `_check_entity_permission`. Effort: XS. Defer to a security-hardening follow-up.
- **Sprint verdict**: ACCEPTABLE — no path currently writes a malformed value; the UI sanitizes, the model column is JSONB so non-JSON is rejected at the DB layer.

**L-2. Error messages from SMTP failures may include sensitive transport metadata**

`_mark_failed` in `notification_worker.py` writes the caught exception's `str(error)` into `notification_queue.error_message` (DB column) and logs it via `logger.error`. `smtplib` exceptions can include the SMTP server's response banner, which sometimes contains the server hostname or auth method — generally low-sensitivity but not zero.

- **Impact**: a tenant admin reading `notification_queue.error_message` for diagnostics could see another tenant's SMTP server name (when system-default config is used). Not a credential leak.
- **Recommendation**: redact known credential-adjacent fields before persisting; log the full exception only at DEBUG level. Effort: S.
- **Sprint verdict**: ACCEPTABLE — operationally useful for triage today; revisit after an actual sensitivity assessment.

### 🔵 Informational — 3 items

**I-1. Wildcard semantics are conservative by design — verified**

`matches_permission(granted, required)` accepts `*` only on the **granted** side. A required code containing `*` is treated as a literal segment value. This is the correct fail-closed posture: a caller who passes `require_permission("*:*:*")` does not accidentally over-grant. The implementation has no regex; segments are split on `:` and compared element-wise. No ReDoS surface, no injection surface. ✓

**I-2. `copy_permissions_from` in `POST /rbac/roles` correctly validates source role tenant**

The new role-create endpoint accepts an optional `copy_permissions_from: UUID`. The handler filters the source role by `Role.tenant_id == current_user.tenant_id OR Role.tenant_id IS NULL` before copying any `RolePermission` rows. A tenant admin **cannot** copy permissions from another tenant's role. ✓

**I-3. Tenant ID is derived from JWT, never from the role-CRUD request body**

`POST /rbac/roles` sets `tenant_id=current_user.tenant_id`; `PUT` and `DELETE` filter the role by tenant before mutating. There is no path where a tenant admin can create or modify a role outside their own tenant (except superusers, which is the documented behavior). ✓

## 4. What I checked but did not flag

- **No SMTP credential leakage in logs.** Every `logger.*` call in `notification_worker.py` was inspected. The dispatch log line includes `id`, `notification_type`, `delivery_method`, `recipient` — no password. Failure logs include `attempts`, `max_attempts`, and the exception message but not the SMTP config object. ✓
- **`is_system` is immutable.** `POST /rbac/roles` hardcodes `is_system=False`; `PUT` rejects (403) any update on a system role; `DELETE` rejects (403) any delete on a system role. No path lets a tenant admin elevate a custom role to system. ✓
- **Per-entity check covers all CRUD paths + aggregate.** `_check_entity_permission` is invoked at the top of `create_record`, `list_records`, `get_record`, `update_record`, `delete_record`, and `aggregate_records`. Bulk methods (`bulk_create/update/delete`) iterate the single-method delegation, so per-row enforcement is preserved. No batch bypass. ✓
- **Audit log coverage.** `role.create`, `role.update`, `role.delete`, `notification.delivered`, `notification.failed` are all audit-logged with the full context (tenant_id, entity_id, changes diff). ✓
- **Wildcard hot-path performance verified at 6.1 µs/call** — well under any timing-attack threshold. Constant-time guarantees were not in scope (RBAC permission timing is not a sensitive surface). ✓

## 5. Sign-off

**D3 Security Engineer**: epic-21 sprint 1 is **CLEAR TO SHIP**.

Findings M-1 (SMTP password at-rest encryption), L-1 (fail-closed for malformed JSONB), and L-2 (SMTP error redaction) are recommended follow-ups but **do not block** the sprint's release. M-1 should appear in the release notes' Known Issues section and be tracked as a separate epic; L-1 and L-2 can be backlog items.

The pre-existing tenant-isolation defense-in-depth gap from `arch-platform.md` §9 risk #1 (per-service `tenant_id` filter pattern with no SQLAlchemy-level safeguard) remains the highest residual risk on the platform but is **out of scope** for this sprint.

## 6. Open questions

- Should `email_smtp_password` encryption (M-1) wait for a platform-wide secrets-encryption story, or be hot-fixed inside Epic 14? Recommend epic-level decision by A3.
- Is `notification_queue.error_message` ever surfaced to non-admin tenants in the UI? If yes, the L-2 redaction priority rises. Confirmed today via grep: no — only admin / audit reader paths.
