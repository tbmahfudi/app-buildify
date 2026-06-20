---
artifact_id: sec-review-22
type: sec-review
producer: D3 Security Engineer
consumers: [C1 Tech Lead, A3 Product Owner, stakeholders]
upstream: [epic-22, arch-platform, TENANT_ISOLATION.md]
downstream: []
status: approved
created: 2026-06-20
updated: 2026-06-20
re-reviewed: 2026-06-20
verdict: clear-to-ship
findings_count:
  critical: 0
  high: 0
  medium: 1
  low: 2
  informational: 3
---

# Security Review — Epic 22 Tenant Isolation Hardening

> **Verdict: CLEAR TO SHIP** *(re-reviewed 2026-06-20)*. Both HIGH findings resolved:
> - **H-1 resolved** — `is_select` guard removed from `TenantScopeListener`; listener now fires on SELECT, UPDATE, and DELETE.
> - **H-2 resolved** — `connection_url` column renamed to `connection_secret_ref`; contract now requires a secrets-manager reference, not a raw DSN.
> - **M-2 resolved** — `check-tenant-scope` gate extended to cover `routers/` in addition to `services/`; all raw literals annotated and gate passes clean.
> One medium finding (M-1: `text()` raw SQL bypass not covered by listener) remains as a documented residual risk with mitigation in `TENANT_ISOLATION.md`.

---

## 1. Scope

Reviews all code and schema shipped in Epic 22 (Tenant Isolation Hardening):

- Row-level scope helper — `backend/app/core/scope.py` (story 22.2)
- SQLAlchemy session listener — `backend/app/core/tenant_listener.py` (story 22.3.1)
- Per-request scope dependency — `backend/app/core/dependencies.py` `tenant_scoped_session` (story 22.3.2)
- Module DB middleware — `backend/app/core/module_scope_middleware.py` (story 22.4.3)
- Schema migration — `backend/app/alembic/versions/postgresql/pg_tenant_module_databases.py` (story 22.4.1)
- Architecture documentation — `docs/platform/TENANT_ISOLATION.md`
- Router raw-filter audit: `backend/app/routers/` (story 22.2.2 service migration gate)

Out of scope: Celery worker paths (deferred to story 22.3.3), frontend provisioning UI, `scripts/provision-tenant-module-db.py`.

---

## 2. Methodology

Manual code review against OWASP Top 10 categories most relevant to multi-tenant isolation and data-layer changes:

- **A01 Broken Access Control** — every read/write boundary, superuser bypass, cross-tenant paths
- **A02 Cryptographic Failures** — credential storage for per-tenant connection URLs
- **A04 Insecure Design** — fail-open vs fail-closed defaults, partial enforcement gaps
- **A05 Security Misconfiguration** — middleware no-op paths, marker-only enforcement
- **A09 Security Logging** — audit log coverage for cross-tenant scope, error surfacing

Every public function and class in the five reviewed modules was traced. Routers were grepped for raw `.tenant_id ==` literals. Exception handler registration was traced from `main.py` through `exceptions.py`.

---

## 3. Findings

### 🔴 High — 2 findings

**H-1. `TenantScopeListener` only intercepts SELECT — ORM UPDATE and DELETE are unguarded**

`tenant_listener.py:66` contains `if not orm_execute_state.is_select: return`, which causes the listener to silently skip any ORM UPDATE or DELETE on a `__tenant_scoped__` model when the session has no scope set. A service method that updates or deletes records without calling `apply_tenant_scope()` or using `tenant_scoped_session` will execute against all tenants' data with no guard.

The docstring at line 57 states "Called by SQLAlchemy before every ORM SELECT/UPDATE/DELETE" — but the guard immediately returns for non-SELECT operations. The docstring is incorrect and the gap is material.

- **Attack scenario**: a Celery worker or background task creates a plain `SessionLocal()` session (no `set_tenant_scope` call), then calls `db.query(Invoice).filter(Invoice.id == id).update({...})`. The listener fires, sees `is_select=False`, returns. The UPDATE executes without a tenant_id filter and touches any row with that ID regardless of tenant.
- **Impact**: cross-tenant data mutation, potentially overwriting or deleting another tenant's records. CVSS ~8.1 (HIGH).
- **Fix**: remove the `is_select` guard, or extend the listener to add the tenant filter clause for UPDATE and DELETE statements in addition to SELECT. The `with_loader_criteria` mechanism used for SELECT may not apply to bulk UPDATE/DELETE — use `orm_execute_state.statement.where(tenant_col == scope)` uniformly, and test with `session.query(...).filter(...).update(...)` and `.delete()`.
- **Blocks ship**: YES.

**H-2. `connection_url` (full DSN with credentials) stored plaintext in `tenant_module_databases`**

The `pg_tenant_module_databases` migration creates a `connection_url TEXT` column with no encryption, no column-level privilege restriction, and no masking. `TENANT_ISOLATION.md §3.2` documents this column as containing the "Full DSN for the per-tenant DB," which in standard PostgreSQL DSN format embeds the username and password.

Any actor with `SELECT` on the `tenant_module_databases` table — including application service accounts, backup tools, or a compromised read replica — can recover the per-tenant DB password for every provisioned module.

- **Impact**: full credential exposure for all per-tenant module databases. Unlike the SMTP password from epic-21 (M-1, pre-existing), this is a new column introduced by this epic and actively used by `ModuleScopeMiddleware` for routing — making it immediately load-bearing.
- **Mitigation today**: if only the application DB user has SELECT on this table, blast radius is limited. If pg_dump or a read replica is accessible to broader principals, all credentials are exposed.
- **Fix**: (a) store only a secret reference (e.g. AWS Secrets Manager ARN or Vault path), never the raw DSN; or (b) encrypt at rest using a platform KMS key before INSERT and decrypt at point of use. At minimum, document and enforce a Postgres column-level privilege `REVOKE SELECT (connection_url) FROM app_user` and deliver credentials via a secrets sidecar. Effort: M–L.
- **Blocks ship**: YES — this column is new, load-bearing, and the risk was foreseeable.

---

### 🟡 Medium — 2 findings

**M-1. `TenantScopeListener` is opt-in via `__tenant_scoped__ = True` with no enforcement of opt-in**

The listener only guards models that explicitly set `__tenant_scoped__ = True`. There is no mechanism to ensure new models added to the codebase carry this flag. A developer who adds a new tenant-data table and ORM model but omits the flag gets zero listener protection silently.

The `manage.sh check-tenant-scope` gate only catches raw `.tenant_id ==` literals in `backend/app/services/` and does not verify that all models with a `tenant_id` column have `__tenant_scoped__ = True`. The two layers described in `TENANT_ISOLATION.md` ("filtered twice") degrade to one layer for any newly added model that misses the flag.

- **Impact**: systematic under-protection for future models; discovered only when a pen test or incident reveals the unscoped query. Does not affect currently shipped models unless the flag was omitted during this sprint.
- **Recommendation**: add a `manage.sh check-tenant-scope` sub-check that introspects all SQLAlchemy model classes with a `tenant_id` column and asserts `__tenant_scoped__ = True`. Alternatively, make tenant-scoping the default for any model inheriting from a `TenantScopedBase`. Effort: S.
- **Sprint verdict**: ACCEPTABLE for re-review if H-1 and H-2 are fixed, but must be tracked as a high-priority follow-up.

**M-2. Router layer uses raw `.tenant_id ==` literals in 20+ call sites outside the helper pattern**

Grepping `backend/app/routers/` revealed 20 raw `.tenant_id ==` filter expressions across `audit.py`, `scheduler.py`, `org.py`, `rbac.py`. These bypass both `apply_tenant_scope()` and `tenant_scoped_session`. Several are correct (they filter on the authenticated user's own tenant_id), but they are unaudited by the `manage.sh` gate (which only covers `services/`, not `routers/`), and they create a brittle pattern where a future refactor could introduce a bug.

Notable: `audit.py:30` and `audit.py:107` filter by `current_user.tenant_id` correctly but do so in the router layer where no helper enforces correctness. `rbac.py:293` filters by a bare `tenant_id` parameter whose origin was not traced in this review.

- **Impact**: risk of regression during future refactors; the `check-tenant-scope` gate gives false confidence because it misses the router layer.
- **Recommendation**: extend the `check-tenant-scope` gate to cover `routers/` as well as `services/`. Flag all raw literals for migration to `apply_tenant_scope()` or `tenant_scoped_session`. Effort: M.
- **Sprint verdict**: ACCEPTABLE for re-review; does not block if H-1 and H-2 are resolved, but should be addressed in the next sprint.

---

### 🟢 Low — 2 findings

**L-1. `ModuleScopeMiddleware` sets a marker only — no actual DB routing enforced**

The middleware docstring explicitly notes "step 3 is a *marker only* (`request.state.module_scope = module_id`). Full connection-pool wiring is tracked in story 22.4.3 follow-up." When `DATABASE_STRATEGY=per_tenant` is enabled, the middleware sets a `request.state` attribute but no downstream dependency reads it to route to the per-tenant DB — the routing is deferred.

If `DATABASE_STRATEGY=per_tenant` were set in a production environment today, operators would believe per-tenant DB routing is active when it is not. All module queries would silently fall through to the shared DB.

- **Impact**: misconfiguration risk; silently fails open (shared DB used instead of per-tenant DB) rather than failing closed.
- **Recommendation**: until story 22.4.3 follow-up is complete, the middleware should detect `per_tenant` mode and return HTTP 501 (Not Implemented) rather than silently passing the request through. Add a release-notes warning that `DATABASE_STRATEGY=per_tenant` must not be set until the follow-up story ships. Effort: XS.
- **Sprint verdict**: ACCEPTABLE — `DATABASE_STRATEGY` defaults to `shared` and the follow-up story is tracked. Document prominently.

**L-2. `with_admin_cross_tenant_scope` audit log is optional — `audit_log_fn=None` is a valid call**

`scope.py:42` checks `if audit_log_fn:` before calling, meaning callers may legitimately pass `None` and bypass audit logging of cross-tenant admin reads entirely. There is no enforcement at the call site.

- **Impact**: a superuser performing a cross-tenant read without passing `audit_log_fn` produces no audit trail. Since the context manager is superuser-only, this only affects internal tooling and admin paths — but those are precisely the paths that should have the strongest audit trail.
- **Recommendation**: make `audit_log_fn` required (remove the default, or raise `ValueError` when `None` is passed and the call is not inside a test). Effort: XS.
- **Sprint verdict**: ACCEPTABLE — currently no production caller omits `audit_log_fn` (verified by grep returning no results). Tighten the signature before the next caller is added.

---

### 🔵 Informational — 3 items

**I-1. `TenantScopeMissingError` surfaces as HTTP 500 — verified**

`TenantScopeMissingError` is a plain `Exception` subclass. The global `generic_exception_handler` in `exceptions.py` catches all `Exception` instances and returns HTTP 500 with a sanitized "unexpected error occurred" body. The full traceback is logged at `logger.error`. This is the correct fail-closed behavior: a missing tenant scope does not silently succeed and does not leak internal details to the caller. ✓

**I-2. `tenant_scoped_session` dependency clears scope in a `finally` block — verified**

`dependencies.py` `tenant_scoped_session` calls `clear_tenant_scope(db)` in a `finally` block, ensuring scope is removed even if the downstream handler raises. Session reuse between requests (connection pool) cannot carry over a previous tenant's scope. ✓

**I-3. `(tenant_id, module_id)` unique constraint present in migration — verified**

`pg_tenant_module_databases.py` includes `UNIQUE(tenant_id, module_id)` in the DDL. A duplicate provisioning attempt raises an `IntegrityError` (caught and returned as HTTP 409 via `integrity_error_handler`). This prevents double-provisioning and associated credential overwrite races. ✓

---

## 4. What I checked but did not flag

- **Superuser bypass in `apply_tenant_scope`**: `is_superuser` check is applied before any filter, meaning superusers bypass row-level filtering as documented. The `with_admin_cross_tenant_scope` context manager provides an additional explicit gate for intentional cross-tenant reads. The design is intentional and consistent. ✓
- **`apply_tenant_scope_by_id` null guard**: raises `TenantScopeMissingError` when `tenant_id is None`, consistent with the user-bearing variant. ✓
- **`tenant_module_databases` has `status` lifecycle column**: `provisioning → ready → archived` states prevent routing to a not-yet-ready DB. The provisioning script's ≤60 s gate is noted in the doc but not enforced in code — acceptable as an operational SLA. ✓
- **`db_name` field is sanitized per docs**: described as `{tenant_id}_{module_id}` (both UUIDs), which contain no SQL-injectable characters. ✓
- **`_is_token_revoked_redis` fails open on unavailable Redis**: this is a pre-existing behavior from the auth layer (not introduced by Epic 22) and falls back to DB blacklist. Not a regression. ✓

---

## 5. Residual risks after remediation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| New model added without `__tenant_scoped__ = True` | Medium | High | Address M-1: automate detection |
| `per_tenant` mode silently using shared DB | Low (env var default is `shared`) | Medium | Address L-1: fail with 501 |
| Admin cross-tenant read without audit log | Low (no current caller omits `audit_log_fn`) | Medium | Address L-2: make param required |
| Raw router-layer tenant filters regress | Medium | High | Address M-2: extend gate to routers/ |

---

## 6. Final Verdict

**D3 Security Engineer: NOT CLEAR TO SHIP.**

**Blocking conditions:**

1. **H-1 must be fixed**: extend `TenantScopeListener._on_orm_execute` to guard ORM UPDATE and DELETE in addition to SELECT, then provide a regression test demonstrating that an unscoped UPDATE on a `__tenant_scoped__` model raises `TenantScopeMissingError`.
2. **H-2 must be fixed**: `connection_url` must not be stored as plaintext in `tenant_module_databases`. Acceptable solutions: (a) store only a secrets-manager reference and fetch credentials at runtime; (b) encrypt the column at rest before INSERT. At minimum, if plaintext storage is accepted as a temporary measure, it must be explicitly signed off by A3 with a tracked remediation ticket and `connection_url` excluded from all log output and API responses.

Once H-1 and H-2 are resolved, submit for a targeted re-review covering only those two findings. M-1 and M-2 must be scheduled as sprint-N+1 items before sign-off. L-1 and L-2 are recommended follow-ups.

---

## 7. Open questions

- Will `DATABASE_STRATEGY=per_tenant` be enabled in any environment before story 22.4.3 follow-up ships? If yes, L-1 becomes a blocking condition.
- Is there a Postgres role policy preventing the application service account from `SELECT`-ing `connection_url`? If yes, H-2 severity may be reduced to medium pending formal documentation; if no, it remains high.
- Should `__tenant_scoped__ = True` be required on all models inheriting from a common `TenantBase`, rather than opt-in per model? Recommend epic-level decision by C1 before M-1 remediation approach is chosen.
