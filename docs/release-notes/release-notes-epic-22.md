---
artifact_id: release-notes-epic-22
type: release-notes
producer: E2 Technical Writer
consumers: [stakeholders, tenant administrators, operators, platform developers, security]
upstream: [epic-22-tenant-isolation-hardening, tasks-22, arch-22, schema-22, adr-tenant-isolation-22]
downstream: []
status: draft
created: 2026-06-27
updated: 2026-06-27
sprint: epic-22 -- Tenant Isolation Hardening
---

# Release Notes -- Tenant Isolation Hardening (epic-22)

> **TL;DR**: A forgotten `tenant_id` filter used to be a silent cross-tenant data leak. It is now a loud HTTP 500. Epic 22 ships a two-layer shared-core defense (a centralized scope helper plus a SQLAlchemy ORM listener), per-tenant module-database provisioning and cleanup, and a `check-tenant-scope` CI gate that blocks new unguarded queries. **No breaking changes for tenant users.** Operators should note the new `DATABASE_STRATEGY=per_tenant` mode and three new environment variables, all of which default to the previous behavior.

---

## Overview

Epic 22 closes the highest residual platform risk identified in `sec-review-21`
and `arch-platform` §9: soft multi-tenancy that depended on every developer
remembering to write `query.filter(Model.tenant_id == ...)`. The epic hardens
isolation along two independent axes:

1. **Shared-core hardening** — a centralized `apply_tenant_scope()` helper and a
   session-scoped ORM listener (`TenantScopeListener`) that enforces tenant scope
   on every `__tenant_scoped__` model. A query (or write) with no tenant context
   fails loud instead of leaking rows.
2. **Per-tenant module databases** — module row data is now provisioned into
   physically separate databases keyed by `(tenant_id, module_id)`, so even an
   ORM bypass cannot reach another tenant's module data.

A static `check-tenant-scope` CI gate makes the convention permanent: new raw
`.tenant_id ==` literals in services or routers break the build.

---

## Security improvements

### Fail-loud tenant scope on the shared core

- All 18 tenant-owned models (`User`, `Company`, `Branch`, `Department`, `Group`,
  the Report* and Dashboard* families, `BuilderPage`, `ModuleServiceAccessLog`,
  `ModuleActivation`, …) now carry `__tenant_scoped__ = True`.
- The `TenantScopeListener` injects `WHERE tenant_id = :scope` into ORM
  SELECT/UPDATE/DELETE, and guards unit-of-work INSERT/UPDATE/DELETE at
  `before_flush`. A scoped query or write with no active scope raises
  `TenantScopeMissingError`, surfaced as a sanitized HTTP 500.
- Cross-tenant writes are blocked: a write whose `tenant_id` differs from the
  active scope is rejected.

### One audited cross-tenant path

`with_admin_cross_tenant_scope(user, admin_reason, audit_log_fn)` is the **only**
legitimate way to read across tenants. It requires a superuser, requires a
non-empty `admin_reason`, and writes `tenant.cross_scope.enter` /
`tenant.cross_scope.exit` audit entries (including the calling stack frame).

### Per-tenant module data isolation

Module data is provisioned into separate databases (`mod_{module}_{tid[:8]}`)
when `DATABASE_STRATEGY=per_tenant`. Connection references are stored as a
secrets-manager reference (`connection_secret_ref`), never a raw DSN
(`sec-review-22` H-2). A tenant deactivation cleanly archives or drops those
databases.

---

## Operational changes

### New `manage.sh` subcommands

- `manage.sh check-tenant-scope` — scans `services/` and `routers/` for
  unguarded raw `.tenant_id ==` literals; fails when the count exceeds the
  frozen baseline of 36. Wired into CI as the `tenant-scope-gate` job between
  `lint` and `test`.
- `manage.sh tenant deactivate <tenant_id>` — runs the module-DB cleanup service
  for a tenant (archive or drop per `TENANT_DELETION_POLICY`).
- `manage.sh module migrate-tenant <tenant_id> <module_id>` — placeholder for
  per-tenant module migration fan-out.

### Module-DB provisioning UI

The Modules page shows a per-module provisioning badge — **Provisioning…**,
**Ready**, or **Failed (retry)** — polling `GET /modules/{id}/provisioning-status`
while in flight.

---

## New environment variables

All three default to the **previous** behavior; no action is required to keep
running as before. See `docs/backend/ENV_VARS.md`.

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_STRATEGY` | `shared` | Adds `per_tenant` alongside the existing `shared` and `separate` modes. Per-tenant module databases activate only under `per_tenant`. |
| `MODULE_DB_POOL_MAX` | `50` | Upper bound on the LRU connection pool keyed by `(tenant_id, module_id)`. |
| `TENANT_DELETION_POLICY` | `archive` | `archive` renames the module DB and marks rows `archived`; `drop` removes the database and rows. |

> **Note**: `DATABASE_STRATEGY=per_tenant` sets a request marker but full
> connection-pool wiring is deferred (L-1); the middleware returns HTTP 501 where
> wiring is incomplete. Default `shared` is unaffected.

---

## For developers

- **Scope your queries with the helper, not raw literals.** Use
  `apply_tenant_scope(query, Model, current_user)` (or `apply_tenant_scope_by_id`
  in static methods). The CI gate rejects new raw `.tenant_id ==` literals unless
  annotated `# tenant-scope-ok`; see `docs/backend/TENANT_SCOPE_MIGRATION.md`.
- **New tenant-owned table?** Add `__tenant_scoped__ = True` to the model.
- **Need a cross-tenant read?** Use `with_admin_cross_tenant_scope` — nothing else.
- **Documented bypass surfaces** that skip the listener: raw `text()` SQL,
  `bulk_insert_mappings`, and `Connection.execute(insert(...))`. These must carry
  an explicit tenant filter or run under an audited admin scope.

---

## Testing

A dedicated adversarial suite lives in
`backend/tests/integration/tenant_isolation/`:

- `test_cross_tenant_select.py` — foreign-tenant SELECT returns empty; unscoped SELECT raises; superuser bypass.
- `test_scope_leak.py` — the `_current_tenant_id` ContextVar and the `__superuser__` sentinel never leak past their context manager, including on exception.
- `test_orm_listener_flush.py` — INSERT/UPDATE/DELETE on a scoped model without scope raise; the listener does not fire for non-scoped models.

---

## Known limitations / follow-ups

- **M-1**: `__tenant_scoped__` is opt-in; no automated detection yet of a model that forgets the flag (sprint N+1).
- **M-2**: the router layer still carries baseline raw literals (36) tracked for migration; the gate prevents new ones.
- **L-1**: `ModuleScopeMiddleware` full connection-pool wiring for production `per_tenant` operation (sprint N+1).
- **L-2**: `audit_log_fn` will become required in `with_admin_cross_tenant_scope`.
- **Future hardening**: PostgreSQL row-level security as a defense-in-depth second layer (see `adr-tenant-isolation-22`).
