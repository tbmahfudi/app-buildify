---
artifact_id: adr-003
type: adr
producer: B1 Software Architect
consumers: [C1 Tech Lead, C2 Backend Developer, E1 DevOps Engineer]
upstream: [adr-001-deployment-modes, arch-platform, arch-22, epic-22-tenant-isolation-hardening]
downstream: []
status: proposed
created: 2026-05-08
updated: 2026-05-08
---

# ADR-003 — Per-Tenant Module Databases

## Status

Proposed. (Will flip to **accepted** once team review on epic-22 completes.)

## Context

[`adr-001-deployment-modes`](adr-001-deployment-modes.md) introduced `DATABASE_STRATEGY` with two values:

- `shared` — modules use the core platform DB (default; what every existing deployment uses)
- `separate` — each module has its own DB (wired but never exercised end-to-end)

Both values are *tenant-shared*: all tenants for a given module read/write the same database, isolated only by `tenant_id` filters in service code. `sec-review-21` flagged the resulting single-line-of-defense as the highest residual platform risk after epic-21, and `vision-02` (revised 2026-05-08) commits to a hybrid response: keep the shared core DB with two-layer logical isolation (helper + ORM listener) but move **module data** to physical-isolation-per-tenant.

Three options were on the table:

1. **Stay `shared` and add Postgres RLS** — the original vision-02 v1 proposal. Rejected after stakeholder review for portability cost + operational debugging cost (see `research-02` §3 pattern matrix, RLS row).
2. **Promote `separate` to per-tenant** — i.e. each `(tenant_id, module_id)` pair gets its own database. Strongest physical isolation; matches the threat model where module data is domain-sensitive (financial records etc.).
3. **Schema-per-tenant** — rejected because it breaks the single `SessionLocal` pool and requires auth-time connection routing.

`adr-001` deliberately left the door open: *"second module will force the operational choice"*. Epic-22 now forces it.

## Decision

Extend `DATABASE_STRATEGY` to a third value: **`per_tenant`**.

| `DATABASE_STRATEGY` | Behavior | Status |
|---|---|---|
| `shared` (default) | Modules share the core platform DB; tenant isolation via `tenant_id` filter + new helper + new ORM listener | **Active** |
| `separate` | Each module has one DB shared across all tenants | **Deprecated** (one-release window; remove in next major) |
| `per_tenant` *(new)* | Each `(tenant, module)` pair gets its own database; physical isolation | **Active** |

Mechanics (full design in [`arch-22`](arch-22.md)):

- A new registry table `tenant_module_databases (tenant_id, module_id, db_name, status, created_at, last_migrated_at, error_message)` in the core DB tracks every per-tenant module DB
- **Lazy provisioning**: on a tenant's first enable of a given module, the platform creates database `tm_{12hex hash of tenant_id}_{module_id}`, runs the module's Alembic migrations against it, and writes the registry row with `status='ready'`
- **Single `platform_app` Postgres role** owns all module DBs (CREATE at the cluster + per-DB CONNECT GRANT). Trade-off vs per-tenant role rotation documented as residual risk
- **Bounded LRU connection pool cache** (default 50 active engines, 10-minute idle TTL) prevents unbounded connection growth at scale
- **Module-routing middleware** reads JWT `tenant_id` + URL prefix `/api/v1/modules/{module_id}/...` and opens a session against the right (tenant, module) DB
- **Alembic fan-out** via `scripts/migrate-module.py {module_id}` runs migrations across all (tenant, module) DBs with bounded concurrency (default 4)
- **Tenant offboarding** via `manage.sh tenant deactivate <id>` cleans up per `TENANT_DELETION_POLICY=drop|archive` (default `archive`)
- **Cross-DB FKs are impossible** — module rows reference core `user_id` / `tenant_id` as plain UUID columns; reconciliation is a daily app-layer job, not a DB constraint
- **`BaseModule.tenant_scoped: bool = True`** (default) declares whether a module participates; modules with `tenant_scoped=False` (rare; e.g. system-wide telemetry) keep the existing shared DB

## Consequences

### Positive
- ✅ Physical tenant isolation for module data — different physical databases means a query in tenant A's module DB *cannot reach* tenant B's data, regardless of code bugs
- ✅ Per-tenant backups, per-tenant tuning, per-tenant restore become natural operations
- ✅ No Postgres-specific RLS code in the application — the platform stays portable to other databases for the *core* DB (modules remain Postgres-specific because Alembic+psycopg2 are the only path tested)
- ✅ Tenant offboarding becomes a clean operation: drop or archive N databases, done

### Negative
- ❌ **Linear growth of (tenant × module) database count.** 100 tenants × 5 modules = 500 module DBs. Bounded LRU pool cache caps the in-memory cost; backup tooling and migration fan-out must handle the count
- ❌ **Cross-DB queries are structurally impossible.** Analytics scans that previously could `JOIN` core to module data now require app-layer fan-out + aggregation
- ❌ **Single `platform_app` role concentration risk.** Compromising the platform's DB credentials gives access to every module DB. Per-tenant Postgres roles would eliminate this; deferred as a backlog item
- ❌ **Cold-start latency on cache-evicted tenant returns.** First request after eviction = ~200 ms engine init. Pool warm-up on lifespan startup helps but doesn't eliminate

### Neutral
- Logical FK absence requires a reconciliation job. Acceptable per `arch-22` decisions.
- `separate` mode gains a deprecation banner in `.env.example` and is removed in the next major release.

## Alternatives considered

- **A — Stay `shared` + add Postgres RLS.** Original `vision-02` v1. Rejected for portability + operational debugging cost; `sec-review-21`'s `M-1` finding can be addressed by RLS but at the cost of locking the platform to Postgres for the core DB too.
- **B — Schema-per-tenant.** Rejected — breaks single SessionLocal pool; requires auth-time connection routing; thousands of schemas at scale is operationally worse than thousands of databases (PG has tools for the latter, less for the former).
- **C — Citus / sharded Postgres.** Rejected for current scale; revisit if tenant count exceeds 10⁵.
- **D — DB-per-tenant for *core* too, not just modules.** Rejected for now — login + identity flows require a system-wide lookup, splitting users-by-tenant breaks the simple "POST /auth/login with email" path. Future regulated-tenant demand could revisit.

## References

- [`adr-001-deployment-modes`](adr-001-deployment-modes.md) — the regime this ADR extends
- [`arch-platform.md`](arch-platform.md) §7 NFRs, §9 risk #1 (the residual risk this addresses)
- [`vision-02-tenant-isolation-hardening`](../vision/vision-02-tenant-isolation-hardening.md) §4 + §8 — the chosen scope IN and the rationale for the hybrid decision
- [`research-02-tenant-isolation-hardening`](../research/research-02-tenant-isolation-hardening.md) §3 pattern matrix — all 8 alternatives evaluated
- [`arch-22`](arch-22.md) — full system design that operationalizes this decision
- [`epic-22-tenant-isolation-hardening`](../epics/epic-22-tenant-isolation-hardening.md) Feature 22.4 — the stories implementing this ADR
- [`sec-review-21`](sec-review-21.md) — the highest-residual-risk finding that motivated `vision-02`
