---
artifact_id: research-02-tenant-isolation-hardening
type: research
producer: A2 Business Analyst
consumers: [A3 Product Owner]
upstream: [vision-02-tenant-isolation-hardening]
downstream: []
status: review
created: 2026-05-08
updated: 2026-05-08
recommendation: proceed
decisions:
  - Cooper goal-directed personas (per A2 spec §9)
  - "Competitor matrix" is a pattern matrix (architectural alternatives) since this is an internal-architecture decision, not a market-facing product
  - Recommendation: PROCEED with one caveat — early performance benchmark gate before broad RLS rollout
open_questions:
  - Number of tenant-scoped tables in scope: count not yet inventoried (B1 will produce in arch-22 §2 / §7)
  - Whether to expose the escape-hatch role via a separate connection pool or a single SET ROLE call — operational decision for B1
---

# Research Brief — Tenant Isolation Hardening (research-02)

> **Upstream**: [`vision-02-tenant-isolation-hardening`](../vision/vision-02-tenant-isolation-hardening.md). This brief validates the vision with personas, a "before/after" developer journey, an architectural-pattern matrix, constraints, and a proceed/pivot/kill recommendation.

## Recommendation: **PROCEED** (with one caveat)

The vision targets a real, sec-review-flagged gap that is invisible to end users but existential to the platform's stated guarantees. The proposed defense-in-depth design (helper + SQLAlchemy listener + Postgres RLS) has well-understood trade-offs, no realistic alternative offers the same coverage, and the work has bounded scope (one architectural change, one sprint). **Proceed**, but the first task in the sprint must be a **performance benchmark on a representative load** so the +5% p95 budget is verified before RLS rolls broadly. If the benchmark exceeds budget, scope must narrow to top-N most sensitive tables before sprint close.

---

## 1. Personas

Tenant-isolation hardening is invisible to end users when it works. The interesting personas are the ones who *build*, *operate*, and *attest to* the guarantee — not the ones who consume the data day-to-day.

### 1.1 Persona A — "Pradeep the Platform Engineer" *(PRIMARY)*

**Role**: Senior Backend Developer at the platform vendor (or in-house IT). Adds new entities + services to the platform monthly. Daily user of `DynamicEntityService`, the RBAC layer, and the audit log. Reads PRs from teammates.

**Goals**
- Ship new tenant-scoped tables without writing the same `filter(Model.tenant_id == user.tenant_id)` boilerplate every time
- Trust that a forgotten filter in a code review will be caught — by tooling, not by another reviewer's vigilance
- Have a single, well-documented escape hatch when admin tooling legitimately needs cross-tenant access

**Frustrations**
- Today every service implements the same scoping logic with subtle variations; some use `_get_org_context()` helpers, some don't
- Code review is the only safety net; one missed `WHERE` clause and the regression silently leaks data
- No way to verify in a test that a new feature didn't introduce a tenant leak — the platform has no test framework yet

**Primary tasks**
- Define a new entity (or service method) that touches tenant-scoped data
- Confirm that the centralized helper or session-event listener auto-applies tenant scoping
- Write a (manual or inline-harness) cross-tenant adversarial test before merging
- Use the escape hatch when writing an admin script that legitimately reads across tenants

**Why he'd choose vision-02's approach**
- Three independent enforcement layers means his individual mistakes (which happen) don't cause leaks
- Postgres RLS gives him an answer for "what stops a future teammate from bypassing the ORM via raw SQL?"
- The named escape-hatch role keeps cross-tenant tooling honest and audit-logged

**Why he might churn from the design**
- If the helper API is more boilerplate than the current ad-hoc approach, he'll bypass it
- If RLS adds visible latency to dashboard queries, his users will complain
- If the SQLAlchemy listener has surprising edge cases (e.g. silently dropping `bulk_insert_mappings` calls) he'll lose trust

### 1.2 Persona B — "Diego the Module Developer" *(SECONDARY)*

**Role**: Same as in `research-01` — senior backend dev, builds platform modules.

**Goals (specific to this vision)**
- Extend `BaseModule` to declare which of his module's tables are tenant-scoped
- Trust that the platform handles RLS deployment for his module's tables (per-DB if `DATABASE_STRATEGY=separate`)
- Not write any tenant-scoping code in his module — let the platform contract handle it

**Frustrations**
- Today the financial module hand-rolls tenant filters; if vision-02 doesn't auto-cover modules, he keeps the boilerplate
- Module DB strategies (`shared` vs `separate` per ADR-001) double the operational complexity of any RLS deployment
- The `BaseModule` contract is frozen per `vision-01` §6 — adding a new method must be backwards-compatible

**Why he'd choose vision-02**
- The contract addition (declare tenant-scoped tables on the module manifest) is small and additive — no break to existing modules
- Module-installation hook handles per-DB RLS setup automatically
- His new modules ship with the same isolation guarantees as the core platform from day one

### 1.3 Persona C — "Yelena the Compliance Officer" *(NEW)*

**Role**: Compliance / security officer at a tenant org or at the platform vendor. Reviews the platform vendor's security posture during procurement and during annual audits. Doesn't write code; reads architecture documents and security review reports.

**Goals**
- Get a *structural* answer to "how do you prevent cross-tenant data exposure?" — not "every developer follows the convention"
- Cite the platform's tenant-isolation guarantee in her own customers' compliance documents (SOC2-adjacent, ISO 27001-adjacent)
- Have an audit trail when cross-tenant access *does* happen (legitimate admin tooling) so she can produce evidence on demand

**Frustrations**
- The current state ("every service hand-applies a filter") is what she has to *defend* in audits — and she knows it's fragile
- `sec-review-21` flagged this as the highest residual risk; her auditors will read that and ask for a remediation plan
- No policy-level (DB-side) control exists today

**Why she'd advocate for vision-02**
- Postgres RLS is the kind of structural control auditors recognize — "the database itself enforces the boundary"
- The defense-in-depth design gives her three independent answers for the same audit question
- The `BYPASSRLS` named role + audit logging on every cross-tenant operation is exactly the evidence trail she needs

### 1.4 Other personas (summary)

| Persona | Visibility into vision-02 | Critical need |
|---------|----------------------------|---------------|
| **Tenant Administrator** | None (invisible when working) | Trust that the guarantee holds |
| **Maya the Power User** | None (invisible when working) | Same |
| **Platform Operator (DevOps)** | Sees the new `platform_admin` role + the migration to enable RLS | A migration runbook with maintenance-window guidance for large tables |

---

## 2. Developer Journey — "Adding a new tenant-scoped table" *(before vs after)*

Maps to **success metric #7** ("Module developer onboarding time ≤ 1 day to add a new tenant-scoped entity with full isolation"). Persona: **Pradeep**. Format: Job Stories per step.

| Step | Today (before vision-02) | After vision-02 | Delta |
|------|--------------------------|-----------------|-------|
| 1. Define table | `tenant_id = Column(GUID, ForeignKey(...))` — manual, identical to every other table | Same — table shape unchanged | none |
| 2. Service create method | Write `filter(Model.tenant_id == self.current_user.tenant_id)` | Use `apply_tenant_scope(query, Model, user)` from `app.core.scope` | -1 line of boilerplate; +1 helper call |
| 3. Service list method | Same hand-rolled filter | Same helper call | same |
| 4. Forgot to add filter on a new method (real failure mode) | **Silent cross-tenant leak**. Code review may or may not catch it. | SQLAlchemy listener detects unscoped query against tenant-scoped table → raises `TenantScopeMissingError` → 500 to caller, audit-log entry | failure mode flips from silent leak to loud crash |
| 5. Direct psql access for debugging | No safeguard — DBA can run `SELECT * FROM users` and see all tenants | RLS policy filters by `current_setting('app.current_tenant_id')`; without `SET app.current_tenant_id`, the query returns **0 rows** unless DBA uses the `platform_admin` role; that use is logged | DB-direct path also secured |
| 6. Admin script (legitimate cross-tenant op, e.g. global notification scan) | Hand-rolled `noqa`-style bypass; no audit trail | Use `with platform_admin_session() as db:` context manager — explicitly named, audit-logged on entry/exit | escape-hatch is honest and auditable |
| 7. Add a new tenant-scoped table to a module | Hand-roll filter in module service; manual SQL to add RLS if DBA insists | Module manifest gains `tenant_scoped_tables: [users, audits]`; `BaseModule.install()` registers RLS + listener bindings automatically | first-class module support |

**Headline finding**: today's flow (rows 4–6 in particular) **assumes** developer discipline at the moment data leaks — which is the worst possible failure mode. After vision-02, the same mistakes produce loud crashes or zero-row reads, which are observable, alertable, and recoverable. **The work flips the failure mode from "silent breach" to "noisy bug"** — that alone justifies the sprint.

---

## 3. Architectural Pattern Matrix

This vision is an internal-architecture decision (not a market-facing product), so the "competitor matrix" enumerates **architectural alternatives** rather than vendor products.

| # | Pattern | Strength | Weakness | Fit for App-Buildify |
|---|---------|----------|----------|----------------------|
| 1 | **Postgres Row-Level Security (RLS)** | DB-level enforcement; transparent to ORM; works with existing connection pool via session variable; auditable at policy level; recognized control by SOC2 auditors | Performance overhead (varies — must benchmark); harder to debug ("why are no rows returned?"); Postgres-specific (not portable to MySQL/SQLite) | **Chosen.** Single-Postgres deployment fits cleanly; session-variable model fits existing FastAPI dependency-injection pattern. |
| 2 | **Schema-per-tenant** (one `tenant_<id>` schema per tenant) | Strong logical isolation; per-tenant backups easy | Per-request schema switching breaks the existing single `SessionLocal` pool; thousands of schemas at scale; migration complexity per schema | **Rejected.** Would require auth-time connection routing — invasive change. |
| 3 | **Database-per-tenant** | Strongest possible isolation; per-tenant tuning + scaling | Operational nightmare at scale; backup/restore N times; doesn't fit shared platform model; massive infra cost | **Rejected.** Only `DATABASE_STRATEGY=separate` (per ADR-001) approaches this and only at the module boundary, not the tenant boundary. |
| 4 | **Application-only filters** (status quo) | Zero infrastructure cost; full developer control | Single line of defense; no safety net for forgotten filter; no DB-level enforcement; no audit trail for direct DB access | **Failing.** This is what `sec-review-21` and `arch-platform.md` §9 risk #1 flag as inadequate. |
| 5 | **ORM session-event listener only** (no RLS) | Simpler than RLS; covers most ORM-level bypasses; no Postgres-specific code | Doesn't cover raw SQL via `SQLAlchemy.text(...)`, `db.execute(...)`, or direct psql; module DBs harder to coordinate | **Partial.** Used as middle layer in vision-02's defense-in-depth, but insufficient alone. |
| 6 | **View-based isolation** (per-tenant views with `WHERE tenant_id = ...`) | Familiar SQL pattern; auditable | Blows up at hundreds of tenants; view materialization overhead; doesn't help with INSERT/UPDATE | **Rejected.** Worse than RLS in every dimension. |
| 7 | **Citus / extension-based horizontal sharding** | Horizontal scale + strong isolation across nodes | Heavyweight; extension-specific; tenant-scoped to *shards* not rows; over-engineered for ~hundreds-of-tenants scale | **Rejected.** Premature optimization for current scale. |

**Pattern**: vision-02 chose RLS because it's the **only pattern** that defends against direct DB access *and* fits the existing single-pool architecture *and* is recognized by external compliance auditors. The defense-in-depth stack (#1 + #5 + a centralized application helper) covers the failure modes that any single layer leaves open.

---

## 4. Constraints

### Technical
- **Postgres-only deployment.** Vision-02 is unportable to MySQL/SQLite. Acceptable per `arch-platform.md` (Postgres is the canonical DB); SQLite is dev-only and out of scope for tenant isolation.
- **Single SessionLocal pool.** RLS via session variable fits; schema-per-tenant would not.
- **`BaseModule` contract is frozen** (per `vision-01` §6). Adding a `tenant_scoped_tables` declaration is an *additive* extension — backwards-compatible with existing modules that don't declare it (their tables would not gain RLS until they migrate).
- **No automated test framework yet** (last 🔴 from `vision-01` §7). Adversarial scenarios will run via inline assertion harnesses + manual runbooks (same pattern as epic-21). A future test-framework epic enables CI for these.
- **`DATABASE_STRATEGY=separate`** (per ADR-001) is wired but unused; modules using it will need their own RLS deployment. Module-installation hook must handle per-DB setup.

### Organizational
- Single backend agent / engineer pool — the same team that built epic-21 is available
- No dedicated security operations function visible in the repo — Compliance Officer persona is forward-looking but not actively driving today
- Sprint capacity will be similar to epic-21 (~10 working days, ~200 dev-hours)

### Performance
- `arch-platform.md` §7 baseline: API p95 < 500 ms
- `vision-02` budget: ≤ +5% regression → ≤ 525 ms
- Recommend a benchmark-first sub-task in early sprint planning so the budget is verified *before* RLS rolls broadly

### Regulatory / compliance
- No formal SOC2 / ISO certification today, but the structural controls in vision-02 are SOC2-adjacent (CC6.1 logical access controls)
- Audit-log coverage already exists (per `audit-13` 13.1 DONE) — vision-02 extends it with `BYPASSRLS` access events

---

## 5. Recommendation: PROCEED (justification)

The vision is validated:

- **Real demand**: every persona faces concrete pain that vision-02 materially reduces. Pradeep gets safety nets; Diego gets a clean module contract; Yelena gets a structural answer for auditors.
- **No realistic alternative**: pattern matrix shows that any single layer leaves the others' failure modes open. RLS alone misses ORM-level bypasses; ORM listener alone misses direct DB access; application filters alone are exactly what's failing today.
- **Bounded scope**: one architectural change, one sprint, one canonical migration. Scope OUT explicitly names six things this is NOT.
- **Risks acknowledged**: vision-02 §7 names performance regression, implicit cross-tenant reads, module DB coordination, SQLAlchemy edge cases, migration locking, developer ergonomics — each with a mitigation.

**Caveat — performance benchmark first**: vision-02's success metric #5 is "p95 regression ≤ +5%". The first task in the sprint must be a representative-load benchmark; if RLS exceeds the budget, scope must narrow to top-N most sensitive tables (with N to be set after the benchmark) before sprint close. Without this gate, there's a real risk of merging an RLS deployment that degrades dashboard performance for tenant administrators.

If the stakeholder cannot commit to that benchmark gate, the recommendation downgrades to **PIVOT** — narrow vision-02 to "centralized scope helper + ORM listener only" (drop RLS) and accept the weaker DB-direct-access protection.

---

## Hand-off

This brief is `status: review`. Next: A3 Product Owner reads `vision-02` + this brief and authors `epic-22-tenant-isolation-hardening.md` (likely structured as a single-feature epic with stories for: scope helper, ORM listener, RLS migration, BaseModule contract addition, adversarial test plan, and the benchmark gate as story #1).
