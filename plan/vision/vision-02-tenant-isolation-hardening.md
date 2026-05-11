---
artifact_id: vision-02-tenant-isolation-hardening
type: vision
producer: A1 Product Manager
consumers: [A2 Business Analyst]
upstream: [vision-01-app-buildify, sec-review-21]
downstream: [research-02-tenant-isolation-hardening, epic-22-tenant-isolation-hardening]
status: approved
created: 2026-05-08
updated: 2026-05-08
decisions:
  - Targeted vision (single-risk focus) — not the broad foundational style of vision-01
  - Scope chosen because sec-review-21 flagged tenant-isolation as the highest residual risk after epic-21
  - **Revised 2026-05-08**: rejected Postgres RLS as a defense layer in favor of "ORM-level filtering for the shared core DB + database-per-tenant for module DBs". Trade-off: weaker DB-direct-access protection for core (DBA / raw SQL paths unprotected) in exchange for portability + operational simplicity + stronger physical isolation where it matters most (module data). Recorded as a stakeholder-driven architectural choice; B1 to issue formal ADR in epic-22.
  - Defense-in-depth posture for core: 2 redundant enforcement layers (centralized scope helper + SQLAlchemy session-event listener)
  - Defense-by-physical-isolation for modules: each tenant gets its own module DB per `DATABASE_STRATEGY=per_tenant` (extends ADR-001)
  - Scope OUT lists encryption / multi-region / GDPR explicitly so this doesn't drift into a "platform security" mega-epic
open_questions:
  - Per-tenant module DB provisioning workflow — at tenant-create or lazy on first module-enable? B1 architecture call.
  - Module migration fan-out — Alembic per module DB; how is the run orchestrated for a 100-tenant deployment? E1 DevOps + B1.
  - When a regulated tenant eventually demands DB-level isolation for *core* data too, what's the upgrade path from shared-core to per-tenant-core? Future ADR.
---

# Product Vision — Tenant Isolation Hardening (vision-02)

> **Revised 2026-05-08** — original v1 of this vision (preserved in git history) proposed Postgres RLS as a third defense layer. After stakeholder review, the approach was narrowed to "ORM-level enforcement for the shared core DB + database-per-tenant for module DBs". The two-layer + physical-isolation design below is the canonical version. See §8 Decisions for the rationale.

## Vision Statement (Geoffrey Moore template)

**For** the App-Buildify platform engineering team and every tenant who relies on the platform's promise that their data stays within their tenant boundary, **vision-02** is **a tenant-isolation hardening initiative** that **(a) replaces the current single-line-of-defense in the shared core DB (every service hand-applies a `tenant_id` filter) with two redundant enforcement layers — a centralized scope helper plus a SQLAlchemy session-event listener — and (b) moves module data to a database-per-tenant model so module records are physically segregated, not just logically filtered**.

**Unlike** the current "discipline-only" approach where one missed `WHERE tenant_id = ?` clause produces silent cross-tenant data exposure, **vision-02 makes core-DB leakage require two simultaneous application-layer failures, and makes module-DB leakage architecturally impossible (different physical databases)**. The trade-off is honest: the shared core DB remains exposed to direct DB access (DBA / `psql` / raw-SQL bypasses); the team accepts this in exchange for portability, operational simplicity, and zero RLS performance overhead.

---

## 1. Problem

`vision-01` §6 declares tenant data isolation **the platform's existential guarantee**. Today, that guarantee is sustained by exactly one mechanism: every service method that touches a tenant-scoped table is required to manually apply a `tenant_id` filter. This is fragile in three concrete ways, all documented:

- **`arch-platform.md` §9 risk #1** — there is no SQLAlchemy-level safeguard. A single missed `filter(Model.tenant_id == current_user.tenant_id)` produces silent cross-tenant data exposure.
- **`audit-04` story 4.2.2** — `_get_org_context()` lives only in `DynamicEntityService`. Every other service implements ad-hoc tenant filtering. Tag-drift count between services is unknown.
- **`sec-review-21`** flagged this as the **highest residual platform risk after epic-21**, calling out specifically that it remains unaddressed by the risk-retirement sprint.

The platform has been lucky so far — no known incident. But "no incident" is not "secure"; it's "untested under adversarial conditions". A single regression, a single new feature with a developer who forgets the convention, a single admin script run without scope context — any of these could trigger the leak.

## 2. Target Users

Same personas as `vision-01`, with one adjustment: this vision is **invisible to end users when it works**. The audience for *trusting* the guarantee is broad; the audience for *delivering* it is narrow.

| Persona | Interest in vision-02 |
|---------|------------------------|
| **End user / Maya the Power User** | Trusts that their data stays in their tenant. Does not see any UI from this work. Notices nothing if it succeeds; notices a breach if it fails. |
| **Tenant Administrator** | Same as end user, plus a compliance posture they can show their auditors ("we have RLS policies on all tenant-scoped tables"). |
| **Module Developer / Diego** | Receives an updated `BaseModule` contract that auto-wires tenant scoping. Less boilerplate per module. |
| **Platform Engineer / Backend Developer** | Primary stakeholder. Gains a centralized helper so they stop hand-rolling tenant filters per service. |
| **Compliance Officer** *(new)* | Can finally answer "how do you guarantee tenant isolation?" with a structural answer rather than "every developer follows the convention". |

## 3. Success Metrics (SMART)

| # | Metric | Target | Notes |
|---|--------|--------|-------|
| 1 | Tenant-isolation incidents in production | **Zero** since deployment | Floor metric (same posture as vision-01 §6 guardrail) |
| 2 | Adversarial cross-tenant test scenarios passing | ≥ 30 scenarios for the shared core DB; ≥ 10 for module DB provisioning; 100% pass | Core scenarios: forgotten filter, ORM bypass attempt, scope-context-unset fail-loud, etc. Module scenarios: tenant A's module connection cannot reach tenant B's module DB at all. |
| 3 | `*Service` classes consolidated onto centralized scope helper | 100% migrated; zero ad-hoc `Model.tenant_id == ...` literals outside the helper | Closes `audit-04` 4.2.2 medium gap |
| 4 | Per-tenant module DB provisioning at tenant create | 100% of new tenants get module DBs auto-provisioned at first module-enable | Replaces the previous "Postgres RLS coverage" metric. Provisioning includes: create DB, run module Alembic migrations, register connection in tenant's module-db registry. |
| 5 | Per-tenant module DB provisioning time | ≤ 60 s end-to-end per (tenant, module) pair on a representative deployment | New metric; replaces the previous "p95 RLS-perf budget". Measured with the financial module as the canonical workload. |
| 6 | Zero functional regressions | All e2e tests in `test-plan-21` + a new `test-plan-22` pass | Re-runs `test-plan-21` to verify epic-21 features still work; especially the role-CRUD + per-entity-perm flows that span the new core/tenant boundary. |
| 7 | Module developer onboarding time | ≤ 1 day to add a new tenant-scoped entity with full isolation | Measures whether the new helper + per-tenant DB convention is actually easier than hand-rolling |

## 4. Scope IN

### Shared core DB (existing single Postgres instance)

- **Centralized scope helper** at `backend/app/core/scope.py` — exposes `apply_tenant_scope(query, model, user)` and `tenant_scope_dependency(user)` for FastAPI; supersedes `_get_org_context()` from `DynamicEntityService` (audit-04 4.2.2)
- **SQLAlchemy session-event listener** that intercepts queries against tenant-scoped tables and auto-injects the tenant filter when a session-level scope context is set; raises a loud error (`TenantScopeMissingError` → 500 + audit-log entry) if scope is unset on a tenant-scoped query — no fail-open
- **Service-layer migration** — every existing `*Service` class converted to use the centralized helper; zero ad-hoc `Model.tenant_id == user.tenant_id` literals remain outside the helper
- **Documented direct-DB-access caveat** — `docs/platform/TENANT_ISOLATION.md` is explicit that DBA, `psql`, and raw-SQL paths are **NOT** structurally protected against cross-tenant access on the core DB; access to those paths is governed operationally (DBA discipline, audit-logged tooling, backup-job review) rather than by the database itself

### Per-tenant module DBs (new)

- **`DATABASE_STRATEGY=per_tenant`** — extends ADR-001's module-DB strategy options; supersedes `separate` (which was wired but unused) for module DBs in production deployments
- **Tenant-scoped module DB provisioning** — when a tenant enables a module for the first time, the platform: (1) creates a new database named `{tenant_id}_{module_id}`, (2) runs the module's Alembic migrations against it, (3) registers the connection string in a `tenant_module_databases` table in the core DB, (4) wires module-routing middleware to pick the right DB per request based on `tenant_id` from JWT
- **Module connection-pool management** — per-(tenant, module) pool with bounded total size; LRU-evict idle pools to keep memory usage manageable for hundreds of tenants
- **Tenant offboarding** — when a tenant is deactivated or deleted, all their module DBs are dropped (or archived, per platform retention policy); single command via `manage.sh tenant deactivate <id>`
- **Module migration fan-out** — `alembic upgrade head` for a module runs across all that tenant×module DBs in parallel-with-bounded-concurrency; failure on any one tenant rolls forward (does not block other tenants) but is logged + alerted

### Cross-cutting

- **`BaseModule` contract update** — modules optionally declare `tenant_scoped: true` (default) and the platform handles the per-tenant-DB provisioning automatically; modules with `tenant_scoped: false` (rare; e.g. system-wide telemetry) get a single shared DB
- **Adversarial test plan (`test-plan-22`)** — ~40 scenarios across: forgotten filter (core), scope-context-unset (core), ORM-bypass attempt (core), tenant-A-cannot-reach-tenant-B-module-DB (modules), provisioning-failure-recovery (modules), offboarding-cleanup (modules), connection-pool-exhaustion (modules), Alembic-fan-out-partial-failure (modules)
- **Migration tooling** — Alembic migration in core to add `tenant_module_databases` table; module Alembic configs gain a "fan-out runner" that iterates connections from that table
- **Documentation** — `docs/platform/TENANT_ISOLATION.md` documenting the 2-layer core defense, the per-tenant module model, the documented direct-DB caveat, the test scenarios, and how to add a new tenant-scoped table or module

## 5. Scope OUT

Explicit non-goals so this vision doesn't sprawl into a "platform security" mega-epic:

1. **Encryption at rest for sensitive PII fields** — separate concern, separate epic. Use the platform's at-rest encryption story when it lands.
2. **Audit-log forensics tooling** for breach detection — useful but distinct from prevention; track separately.
3. **Multi-region replication / data residency** — strategic feature, not a security gap. Not in scope.
4. **Tenant data export / GDPR right-to-be-forgotten** — operational tooling on top of isolation, not isolation itself.
5. **SMTP password / module API key encryption** — `sec-review-21` finding M-1; tracked under Epic 14.
6. **CI/CD + automated test framework** — last open 🔴 from `vision-01` §7; deserves its own vision.

## 6. Guardrails

- **No backwards-incompatible API surface changes.** Internal architecture changes only; consumers see the same responses.
- **Login flow stays unchanged.** Identity, password validation, JWT issuance all continue to use the shared core DB. Only post-login data access for module endpoints fans out to per-tenant DBs.
- **Existing tenants migrate automatically.** No hand-applied DB changes required. Existing modules ship in `shared` mode until they're explicitly migrated to `per_tenant` (one-shot migration command per module).
- **Defense-in-depth for core, not defense-instead-of.** Both core layers (helper + SQLAlchemy listener) deploy together. Removing either is not allowed.
- **Fail-loud, not fail-open.** If the scope context is unset when a tenant-scoped query runs against the core DB, the request fails with a 500 + audit-log entry — does NOT silently return all tenants' rows.
- **Honest about the direct-DB-access caveat.** `docs/platform/TENANT_ISOLATION.md` explicitly states that DBA / `psql` / raw-SQL paths are NOT structurally protected on the core DB. Operational controls (audit-logged tooling, DBA discipline, backup-job review) cover this gap.
- **No `# noqa` / `# tenant-skip` magic comments.** If a service legitimately needs cross-tenant access (e.g. system-wide notification scan), it goes through an explicit named API in the helper, audit-logged at every call.
- **Module DBs are immutable per-tenant boundaries.** A connection to tenant A's module DB cannot reach tenant B's module DB at all — different physical databases, different connection strings. No "escape hatch" exists for cross-tenant module data.

## 7. Risks

| 🚦 | Risk | Mitigation |
|----|------|-----------|
| 🔴 | **Direct-DB-access path remains unprotected on the core DB.** Accepted trade-off; explicitly documented. A rogue DBA, a buggy backup script, or a teammate running `psql` can read across tenants on the core DB. | Operational controls: audit-log every direct-DB session; restrict DB credentials to a small named group; review backup jobs quarterly. If a regulated tenant ever demands DB-level isolation, that triggers a future epic to revisit (likely RLS-on-core or hybrid split). |
| 🔴 | Per-(tenant × module) DB count grows linearly. With 100 tenants × 5 modules = 500 DBs to manage. | Bounded LRU connection pools; bounded-concurrency Alembic fan-out; tenant-onboarding automation; explicit upper bound documented (e.g. soft cap at 1000 module DBs per Postgres instance, sharded above that). |
| 🔴 | Existing services may have implicit cross-tenant reads (admin tooling, support runbooks) that break under the SQLAlchemy listener's fail-loud behavior | Survey first (B1 + audit cross-cutting); convert legitimate cross-tenant reads to explicit named-API calls in the helper. |
| 🟡 | SQLAlchemy session-event listener edge cases with `bulk_insert_mappings` / Core-API queries that bypass the ORM Query path | Document known unsafe APIs; require code review to flag them; or augment listener to cover Core insert/update too. |
| 🟡 | Module migration fan-out partial failure (some tenants migrated, some not) leaves the deployment in a mixed-version state | Idempotent migrations; status tracker per (tenant, module, migration_version); explicit retry tooling; alerting on stuck migrations. |
| 🟡 | Cross-DB foreign keys are impossible — module data references core `user_id` / `tenant_id` as plain UUIDs, not FKs | Logical-FK convention documented in `BaseModule` SDK; periodic reconciliation job to surface orphaned references. |
| 🟢 | Developer ergonomics — the new helper API + per-tenant-DB convention must be easier than hand-rolling, otherwise team won't adopt | Treat helper API as a UX surface; measure adoption (metric #3); iterate. |

## 8. Decisions

- **Targeted, not foundational.** vision-02 is intentionally narrow: one risk, one architectural change, one sprint. Contrast with vision-01 which was a foundational scope statement.
- **Two-layer defense for core; physical isolation for modules.** Stakeholder-driven choice (2026-05-08) after weighing trade-offs. Original v1 of this vision proposed a third layer (Postgres RLS) on the core DB; rejected for portability cost (PG-only, awkward to defend if MySQL ever became real), operational debugging cost (RLS "no rows returned" failures are confusing), and explicit acceptance of the direct-DB-access caveat (operational controls cover the residual gap). Per-tenant module DBs deliver stronger-than-RLS isolation where the data is most domain-sensitive (financial records, etc.).
- **Login + identity stay in the shared core DB.** The shared core lookup-by-email path is preserved; per-tenant DB selection happens *after* JWT issuance based on the JWT's `tenant_id` claim. This avoids the "user picks tenant before login" UX problem and keeps the existing auth flow intact.
- **Postgres RLS rejected** for the shared core DB — see above. Pattern matrix in `research-02` §3 records all 7 alternatives evaluated.
- **Cross-DB FKs accepted as logical, not enforced.** Module DB tables reference `user_id` / `tenant_id` as plain UUID columns; reconciliation is application-layer + periodic job, not DB-level constraint.
- **Risks reference upstream artifacts** (sec-review-21, arch-platform §9, audit-04 4.2.2) rather than restating findings.

## 9. Open Questions

- **Module DB provisioning timing**: at tenant create (eager — every tenant has every module DB whether enabled or not) or at first module-enable (lazy — DBs created on demand)? Lazy is cheaper at scale; eager is simpler to reason about. Defer to B1 architecture.
- **Module migration fan-out orchestration**: how does `alembic upgrade head` for the financial module run across N tenants? Sequential (slow, simple) or parallel-with-bounded-concurrency (faster, more failure modes)? Defer to E1 DevOps.
- **Connection-pool sizing**: with potentially hundreds of (tenant × module) DBs, what's the right pool topology? One small pool per (tenant, module), or one shared pool that switches DBs per request? Defer to B1 + benchmarking.
- **When a regulated tenant demands DB-level isolation for *core* data too**, what's the upgrade path from shared-core to per-tenant-core? Future ADR; the vision-02 design deliberately defers this rather than over-engineering for hypothetical regulated tenants today.
- **Existing modules in `shared` mode**: do we force-migrate to `per_tenant` or grandfather existing deployments? Per-tenant adds operational complexity that some small deployments may not want. Recommend: opt-in per module, default `per_tenant` for new modules, `shared` retained as a deprecated mode.

---

## Hand-off

This vision is `status: review`. Next: human stakeholder (or A2 Business Analyst on dry-run) flips to `status: approved`, then **A2 Business Analyst** consumes it to produce `research-02.md` (target users, current-state survey of services for tenant-filter discipline, competitor matrix of multi-tenant DB-level isolation patterns, proceed/pivot/kill recommendation).
