---
artifact_id: test-plan-22
type: test-plan
producer: D1 QA Engineer
consumers: [stakeholders, operators, future automation engineers]
upstream: [epic-22-tenant-isolation, tasks-22, vision-01-app-buildify]
downstream: [test-report-22]
status: approved
created: 2026-06-20
updated: 2026-06-20
covers_tasks: [22.2.1, 22.2.2, 22.2.3, 22.3.1, 22.3.2, 22.1.1, 22.4.1, 22.4.2, 22.4.3, 22.4.4, 22.4.5, 22.4.6, 22.5.2]
---

# Test Plan — Epic 22: Tenant Isolation Hardening

> **Format**: adversarial manual runbook. Each scenario is independently executable. Prerequisites call out any seed data needed. Expected outcomes include both the happy-path result and the assertion that proves tenant data did NOT leak. Companion: [`test-report-22`](../test-reports/test-report-22.md).

---

## Part A — Shared-core-DB hardening (30 scenarios)

### A-01: `apply_tenant_scope` filters correctly for normal user

**Prerequisites**: Two tenants (T-A, T-B). Each has one `Invoice` record. Authenticated as T-A user.

**Steps**:
1. Call `apply_tenant_scope(db.query(Invoice), Invoice, user_a)`.
2. Execute and collect results.

**Expected**: Only T-A invoices returned. T-B invoices absent. `COUNT = 1`.

---

### A-02: `apply_tenant_scope` is no-op for superuser

**Prerequisites**: Same as A-01. Authenticated as superuser.

**Steps**:
1. Call `apply_tenant_scope(db.query(Invoice), Invoice, superuser)`.
2. Execute.

**Expected**: All invoices from all tenants returned. `COUNT = 2`.

---

### A-03: `apply_tenant_scope` is no-op for models without `tenant_id`

**Prerequisites**: A model `SystemConfig` with no `tenant_id` column.

**Steps**:
1. Call `apply_tenant_scope(db.query(SystemConfig), SystemConfig, user_a)`.

**Expected**: No filter added. Query executes normally.

---

### A-04: `apply_tenant_scope` raises `TenantScopeMissingError` when user has no tenant_id

**Prerequisites**: A user with `tenant_id = None` and `is_superuser = False`.

**Steps**:
1. Call `apply_tenant_scope(db.query(Invoice), Invoice, user_no_tenant)`.

**Expected**: `TenantScopeMissingError` raised immediately, no DB query issued.

---

### A-05: `tenant_scope_dependency` passes for user with tenant_id

**Prerequisites**: Regular user with valid `tenant_id`.

**Steps**:
1. Invoke `tenant_scope_dependency(user)`.

**Expected**: Returns `user` unchanged. No exception.

---

### A-06: `tenant_scope_dependency` raises for user with no tenant_id

**Prerequisites**: User with `tenant_id = None`, `is_superuser = False`.

**Steps**:
1. Invoke `tenant_scope_dependency(user)`.

**Expected**: `TenantScopeMissingError` raised.

---

### A-07: `tenant_scope_dependency` passes for superuser with no tenant_id

**Prerequisites**: Superuser with `tenant_id = None`.

**Steps**:
1. Invoke `tenant_scope_dependency(superuser)`.

**Expected**: Returns `superuser`. No exception.

---

### A-08: `with_admin_cross_tenant_scope` allows superuser with reason

**Prerequisites**: Superuser. Audit log callable (mock).

**Steps**:
1. Enter `with_admin_cross_tenant_scope(superuser, "support ticket #123", audit_fn)`.
2. Perform a cross-tenant query inside the block.
3. Exit the block.

**Expected**: No exception. `audit_fn` called twice — once on enter (`tenant.cross_scope.enter`), once on exit (`tenant.cross_scope.exit`).

---

### A-09: `with_admin_cross_tenant_scope` blocks non-superuser

**Prerequisites**: Regular tenant user.

**Steps**:
1. Attempt `with_admin_cross_tenant_scope(regular_user, "reason", None)`.

**Expected**: `PermissionError` raised on enter.

---

### A-10: `with_admin_cross_tenant_scope` requires non-empty reason

**Prerequisites**: Superuser.

**Steps**:
1. Attempt `with_admin_cross_tenant_scope(superuser, "", None)`.

**Expected**: `ValueError` raised.

---

### A-11: `with_admin_cross_tenant_scope` audit-logs even on exception inside block

**Prerequisites**: Superuser. Audit log callable (mock).

**Steps**:
1. Enter the context manager.
2. Raise an arbitrary exception inside.
3. Catch it outside.

**Expected**: `tenant.cross_scope.exit` audit event still fired (finally block).

---

### A-12: `TenantScopeListener` auto-filters SELECT on `__tenant_scoped__` model

**Prerequisites**: Engine with listener installed. Session has `_tenant_scope = T-A-uuid`. Two tenants with records.

**Steps**:
1. Execute `db.query(Invoice).all()`.

**Expected**: Only T-A records returned. No explicit filter in application code.

---

### A-13: `TenantScopeListener` raises when scope unset on `__tenant_scoped__` model

**Prerequisites**: Engine with listener installed. Session has no `_tenant_scope`.

**Steps**:
1. Execute `db.query(Invoice).all()`.

**Expected**: `TenantScopeMissingError` raised before SQL is issued.

---

### A-14: `TenantScopeListener` skips non-`__tenant_scoped__` models

**Prerequisites**: Model without `__tenant_scoped__ = True`. Session with no scope.

**Steps**:
1. Execute `db.query(SystemConfig).all()`.

**Expected**: Query succeeds. No `TenantScopeMissingError`.

---

### A-15: `TenantScopeListener` skips when scope is `__superuser__`

**Prerequisites**: Session with `_tenant_scope = '__superuser__'`.

**Steps**:
1. Execute `db.query(Invoice).all()`.

**Expected**: All records returned from all tenants.

---

### A-16: `set_tenant_scope` / `clear_tenant_scope` correctly manage session state

**Steps**:
1. Call `set_tenant_scope(session, 'abc-123')`.
2. Assert `session._tenant_scope == 'abc-123'`.
3. Call `clear_tenant_scope(session)`.
4. Assert `hasattr(session, '_tenant_scope') is False`.

**Expected**: Both assertions pass.

---

### A-17: `tenant_scoped_session` dependency binds scope for normal user

**Prerequisites**: Authenticated user with `tenant_id = T-A`. Listener installed.

**Steps**:
1. Use `Depends(tenant_scoped_session)` in a test endpoint.
2. Inside the endpoint, execute `db.query(Invoice).all()`.

**Expected**: Scope bound; only T-A invoices returned. Scope cleared after response.

---

### A-18: `tenant_scoped_session` binds `__superuser__` for superuser

**Prerequisites**: Superuser. Listener installed.

**Steps**:
1. Same as A-17 but with superuser credentials.

**Expected**: `session._tenant_scope == '__superuser__'` during request. All invoices returned.

---

### A-19: `tenant_scoped_session` raises when user has no tenant_id

**Prerequisites**: User with `tenant_id = None`, not superuser.

**Steps**:
1. Hit endpoint with `Depends(tenant_scoped_session)`.

**Expected**: `TenantScopeMissingError` raised; HTTP 500 or a mapped 403 (depending on exception handler).

---

### A-20: Cross-tenant ID guessing is blocked

**Prerequisites**: User A (T-A) knows invoice ID `inv-99` belonging to T-B.

**Steps**:
1. `GET /api/v1/financial/invoices/inv-99` as T-A user.

**Expected**: 404 Not Found (record filtered out, not visible).

---

### A-21: URL path manipulation cannot escape tenant scope

**Prerequisites**: T-A user. T-B tenant ID known.

**Steps**:
1. `GET /api/v1/org/tenants/<T-B-id>/invoices` as T-A user.

**Expected**: 403 Forbidden or 404 — never T-B data.

---

### A-22: `manage.sh check-tenant-scope` PASS when no raw filters exist

**Prerequisites**: Clean checkout with no `.tenant_id ==` literals in `services/`.

**Steps**:
1. `./manage.sh check-tenant-scope`

**Expected**: Exits 0. Prints "PASS".

---

### A-23: `manage.sh check-tenant-scope` FAIL when raw filter introduced

**Prerequisites**: Introduce `Model.tenant_id == user.tenant_id` in any service file.

**Steps**:
1. `./manage.sh check-tenant-scope`

**Expected**: Exits 1. Prints "ERROR" with the offending file path.

---

### A-24: Unauthenticated request cannot reach any tenant-scoped endpoint

**Steps**:
1. `GET /api/v1/financial/invoices` with no Authorization header.

**Expected**: 401 Unauthorized. No data returned.

---

### A-25: JWT tenant mismatch is rejected

**Prerequisites**: Forge a JWT with a different `tenant_id` than the user's DB record.

**Steps**:
1. Send request with forged JWT.

**Expected**: 401 "Token tenant mismatch - please re-authenticate".

---

### A-26: Revoked token cannot access tenant data

**Prerequisites**: Valid token, then revoke it (blacklist).

**Steps**:
1. Revoke token via logout.
2. Retry `GET /api/v1/financial/invoices` with the old token.

**Expected**: 401 "Token has been revoked".

---

### A-27: `apply_tenant_scope` is idempotent (calling twice doesn't double-filter)

**Steps**:
1. Apply scope once, inspect the generated SQL.
2. Apply scope a second time.

**Expected**: Only one `WHERE tenant_id = ...` clause in the final SQL.

---

### A-28: Service layer test — `InvoiceService.list()` enforces scope without explicit call

**Prerequisites**: `InvoiceService` uses `tenant_scoped_session` or calls `apply_tenant_scope`.

**Steps**:
1. Call `InvoiceService.list(db, user_a)`.
2. Assert T-B records absent.

**Expected**: Isolation confirmed.

---

### A-29: Audit log created on every cross-tenant scope entry

**Steps**:
1. Execute three separate `with_admin_cross_tenant_scope(...)` blocks.
2. Query `audit_logs` for `action = 'tenant.cross_scope.enter'`.

**Expected**: Exactly 3 rows found, one per block.

---

### A-30: Concurrent requests from different tenants don't bleed scope

**Prerequisites**: Two concurrent HTTP clients (T-A, T-B) hitting the same endpoint.

**Steps**:
1. Fire 50 concurrent requests alternating between T-A and T-B tokens.
2. Assert each response contains only that tenant's data.

**Expected**: Zero cross-tenant records in any response. Scopes are per-session, not global.

---

## Part B — Per-tenant module DB (10 scenarios)

### B-01: `provision-tenant-module-db.py` creates database within 60 s gate

**Prerequisites**: Postgres accessible. `DATABASE_URL` set.

**Steps**:
1. `python3 scripts/provision-tenant-module-db.py tenant_alpha financial`

**Expected**: Prints "Gate (≤60s): PASS". DB `tenant_alpha_financial` created in Postgres.

---

### B-02: `tenant_module_databases` row inserted on provision

**Steps**:
1. After B-01, query `SELECT status FROM tenant_module_databases WHERE db_name = 'tenant_alpha_financial'`.

**Expected**: Row exists with `status = 'ready'` (or `provisioning` if async).

---

### B-03: `GET /api/v1/modules/{id}/provisioning-status` returns `not_provisioned` initially

**Prerequisites**: T-A user. Module not yet provisioned.

**Steps**:
1. `GET /api/v1/modules/<module_id>/provisioning-status`

**Expected**: `{"status": "not_provisioned", "db_name": null, "error_message": null}`

---

### B-04: Provisioning status endpoint returns `ready` after successful provision

**Prerequisites**: Row inserted with `status = 'ready'`.

**Steps**:
1. `GET /api/v1/modules/<module_id>/provisioning-status`

**Expected**: `{"status": "ready", "db_name": "...", "error_message": null}`

---

### B-05: `ModuleScopeMiddleware` is no-op in `shared` strategy

**Prerequisites**: `DATABASE_STRATEGY=shared` (default).

**Steps**:
1. `GET /api/v1/modules/<id>/provisioning-status`

**Expected**: `request.state` has no `module_scope` attribute. Normal shared-DB path used.

---

### B-06: `ModuleScopeMiddleware` sets `module_scope` in `per_tenant` strategy

**Prerequisites**: `DATABASE_STRATEGY=per_tenant`.

**Steps**:
1. Hit any `/api/v1/modules/<id>/...` endpoint.
2. Assert `request.state.module_scope == '<id>'`.

**Expected**: Attribute set. Request proceeds normally.

---

### B-07: `migrate-module.py` fan-out executes for all registered tenants

**Prerequisites**: 3 tenant rows in `tenant_module_databases` for `module_id = financial`.

**Steps**:
1. `python3 scripts/migrate-module.py financial`

**Expected**: Script logs 3 "OK" lines. Exit code 0.

---

### B-08: `migrate-module.py` exits 1 when any tenant migration fails

**Prerequisites**: 1 of 3 tenants has an invalid `connection_url`.

**Steps**:
1. `python3 scripts/migrate-module.py financial`

**Expected**: 2 "OK" lines, 1 "FAIL" line. Exit code 1.

---

### B-09: `manage.sh tenant deactivate` archives module DB rows

**Prerequisites**: 2 `tenant_module_databases` rows for T-A, status = `ready`.

**Steps**:
1. `./manage.sh tenant deactivate <T-A-id>`
2. Query `SELECT status FROM tenant_module_databases WHERE tenant_id = '<T-A-id>'`.

**Expected**: Both rows have `status = 'archived'`. Physical DB still exists.

---

### B-10: Tenant B cannot query Tenant A's per-tenant module DB via the API

**Prerequisites**: T-A has a provisioned `financial` module DB. T-B does not.

**Steps**:
1. As T-B user, `GET /api/v1/modules/<T-A-financial-module-id>/provisioning-status`.

**Expected**: Returns `{"status": "not_provisioned"}` for T-B — not T-A's status. No cross-tenant data visible.

---

*End of test plan — 40 scenarios total (30 core-DB + 10 module-DB)*
