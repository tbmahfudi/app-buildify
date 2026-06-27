---
artifact_id: adr-tenant-isolation-22
type: adr
producer: E2 Technical Writer
consumers: [Backend Engineer, DevOps, Tech Lead, Security Engineer]
upstream: [epic-22-tenant-isolation-hardening, arch-22, schema-22, sec-review-22]
downstream: []
status: approved
created: 2026-06-27
updated: 2026-06-27
---

# ADR-Tenant-Isolation-22 — Enforcing Shared-Core Tenant Scope: ContextVar + ORM Listener

## Status

Accepted. Implemented in Epic 22 (Story 22.1 + 22.2).

## Context

App-Buildify's shared core database is **soft multi-tenant**: every tenant-scoped
table carries a `tenant_id` UUID column, and isolation depends on every query
adding `WHERE tenant_id = :current_tenant`. `arch-platform.md` §9 risk #1 and
`sec-review-21.md` both flagged the obvious failure mode:

> "Filtering relies on every service writing `query.filter(Model.tenant_id == self.tenant_id)`. A missed filter is a cross-tenant data leak."

A single forgotten filter silently returns another tenant's rows. We need
enforcement that turns "forgot to filter" from a **silent leak** into a **loud
failure**, without rewriting every query in the codebase and without a heavy
runtime tax. Three approaches were considered.

### Requirements

1. A query against a scoped model with no tenant context must fail loud (HTTP 500), never return cross-tenant rows.
2. Must work across async request handlers, background tasks, and threads.
3. Must allow a narrow, audited cross-tenant path for legitimate superuser/admin reads.
4. Incremental adoption — no big-bang rewrite; existing queries keep working as they are migrated.
5. Database-portable (PostgreSQL in prod, SQLite in tests).

## Decision

Enforce shared-core tenant scope with **two cooperating layers**:

1. **A `ContextVar` (`_current_tenant_id`)** holding the active tenant id for the
   current execution context, set per-request by the `tenant_scoped_session`
   FastAPI dependency (and resettable by `with_tenant_scope` / cleared in a
   `finally`). The sentinel value `'__superuser__'` marks an audited
   cross-tenant scope established only via `with_admin_cross_tenant_scope()`.

2. **A SQLAlchemy ORM session listener (`TenantScopeListener`)** that reads the
   ContextVar and enforces scope on every model declaring `__tenant_scoped__ = True`:
   - `do_orm_execute` — intercepts ORM **SELECT / UPDATE / DELETE**, injects
     `WHERE tenant_id = :scope`, or raises `TenantScopeMissingError` when scope
     is unset.
   - `before_flush` — intercepts unit-of-work **INSERT / UPDATE / DELETE**
     (`session.add` / `session.delete` + flush), which do **not** pass through
     `do_orm_execute`; raises when scope is unset and blocks writes whose
     `tenant_id` differs from the active scope.

   The `'__superuser__'` sentinel bypasses both hooks.

A centralized helper, `apply_tenant_scope(query, model, user)`, gives service and
router authors an explicit, reviewable way to scope a query (no-op for
superusers and non-scoped models). The `check-tenant-scope` CI gate forbids new
raw `.tenant_id ==` literals so the convention is enforced forever after.

### Why ContextVar instead of session/thread-local state

The listener must resolve scope from wherever the query runs — async handlers,
`run_in_executor` threads, background tasks. A `ContextVar` propagates correctly
across `await` boundaries and is isolated per task, where a thread-local would
leak or be wrong under async. Scope is therefore authoritative on the ContextVar;
a per-session attribute is kept only as a fallback for background tasks that
construct a bare `SessionLocal`.

## Alternatives considered

### A. Middleware-only scoping (rejected as sole mechanism)

An HTTP middleware sets the tenant from the JWT and a base query class applies
the filter.

- **Pro**: simple, lives entirely in the request path.
- **Con**: only covers code that goes through the request middleware and the
  blessed base query. Background jobs, schedulers, and any direct `session.query`
  silently escape it — exactly the "someone forgot" case we must stop. It also
  cannot guard `before_flush` writes. Middleware is necessary for *setting* scope
  but insufficient for *enforcing* it. **We keep the middleware/dependency for
  setting scope, but enforcement lives at the ORM layer.**

### B. Database row-level security (RLS / `SET app.current_tenant`) (rejected for now)

PostgreSQL RLS policies on each table, with `SET LOCAL app.current_tenant = …`
per transaction.

- **Pro**: enforcement in the database — even raw SQL and ORM bypass are covered;
  the strongest isolation guarantee.
- **Con**: PostgreSQL-only (our test suite runs on SQLite and would lose all
  coverage of the isolation layer); per-table policy DDL and migrations add
  significant operational surface; connection-pool reuse requires careful
  `SET LOCAL`/`RESET` discipline or pooler-level support; debugging a policy
  denial is opaque compared to an application exception with a stack trace; and
  it does not help the **module-data** isolation story, which we solve with
  physically separate per-tenant databases (see ADR-003 / `arch-22` §Feature 22.4).
  RLS remains the recommended **future hardening** for defense-in-depth once the
  application layer is proven and the team is ready to operate it.

### C. Per-model mixin requiring explicit `.scoped()` calls (rejected)

A `TenantScopedQuery` that authors must call.

- **Pro**: explicit at the call site.
- **Con**: it is opt-in — the failure mode is identical to today (someone forgets
  to call `.scoped()`), with no loud failure. The listener flips this: forgetting
  is the loud path, not the silent one.

## Consequences

**Positive**

- A forgotten filter on a scoped model is now an HTTP 500, not a data leak (fail-loud).
- Enforcement is independent of the call path — request handlers, background tasks, and threads are all covered via the ContextVar.
- Incremental: models opt in with `__tenant_scoped__ = True`; queries migrate to `apply_tenant_scope()` over time; the CI gate ratchets the baseline down.
- Database-portable: works identically on PostgreSQL and SQLite, so the isolation layer is fully unit/integration tested (see `backend/tests/integration/tenant_isolation/`).

**Negative / trade-offs**

- Enforcement is **opt-in per model** (`__tenant_scoped__`); a new model that forgets the flag is unguarded. Tracked as **M-1** (automated introspection) for sprint N+1.
- Documented bypass surfaces remain: raw `text()` SQL, `bulk_insert_mappings`, and `Connection.execute(insert(...))` skip the ORM listener. These must use `with_admin_cross_tenant_scope` or carry an explicit tenant filter; they are called out in `docs/platform/TENANT_ISOLATION.md`.
- A small per-query cost (mapper inspection + statement rewrite). Negligible in practice.

## Follow-ups

- **M-1**: automated detection of scoped models missing the flag.
- **Defense-in-depth**: revisit PostgreSQL RLS (Alternative B) as a second enforcement layer once the application layer is established in production.
- **L-2**: make `audit_log_fn` required in `with_admin_cross_tenant_scope`.

## Related

- `arch-22` — system design (two-layer defense, Feature 22.4 per-tenant module DBs).
- ADR-001 — deployment modes (`DATABASE_STRATEGY`).
- `adr-003-per-tenant-module-databases.md` — physical isolation for module data.
- `docs/platform/TENANT_ISOLATION.md` — operator/developer guide.
- `docs/runbooks/runbook-tenant-isolation.md` — diagnosis and operations runbook.
