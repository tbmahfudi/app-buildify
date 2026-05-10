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
  - **Revised 2026-05-08**: pattern matrix updated post-stakeholder review. RLS rejected for the shared core DB (portability cost + operational debugging cost outweigh the third-layer benefit; direct-DB-access caveat accepted). Per-tenant module DBs promoted to chosen for module data. See §3 + §5.
  - Recommendation: PROCEED with one caveat — first sprint task should be a per-tenant-module-DB provisioning prototype to validate the fan-out tooling before broad rollout (replaces the previous "RLS benchmark gate")
open_questions:
  - Module DB provisioning timing (eager at tenant-create vs lazy at module-enable) — operational decision for B1
  - Connection-pool topology for hundreds of (tenant × module) DBs — needs benchmarking before sprint
  - Number of existing modules to migrate from `shared` to `per_tenant` — currently only Financial; survey for others
---

# Research Brief — Tenant Isolation Hardening (research-02)

> **Upstream**: [`vision-02-tenant-isolation-hardening`](../vision/vision-02-tenant-isolation-hardening.md). This brief validates the vision with personas, a "before/after" developer journey, an architectural-pattern matrix, constraints, and a proceed/pivot/kill recommendation.

## Recommendation: **PROCEED** (with one caveat)

> **Revised 2026-05-08** — original v1 of this brief recommended PROCEED with an RLS-benchmark gate. After stakeholder pivot to "ORM-level for shared core + DB-per-tenant for modules", the recommendation stands as PROCEED but the caveat changes: the first sprint task should be a **per-tenant-module-DB provisioning prototype** (financial module against a clean tenant) to validate the fan-out + connection-pool tooling before broad rollout. If provisioning takes > 60 s per (tenant, module) under representative load, the operational story needs rework before sprint close.

The vision targets a real, sec-review-flagged gap that is invisible to end users but existential to the platform's stated guarantees. The chosen design (centralized helper + SQLAlchemy session-event listener for the shared core DB + database-per-tenant for module data) accepts a documented trade-off — direct DBA / `psql` / raw-SQL access against the shared core remains unprotected — in exchange for portability, operational simplicity, and stronger physical isolation where module data is most domain-sensitive. Bounded scope (one sprint) and explicit acceptance of the residual core-DB caveat keep the work tractable.

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
| 1 | **Postgres Row-Level Security (RLS)** | DB-level enforcement; transparent to ORM; works with existing connection pool via session variable; auditable at policy level; recognized control by SOC2 auditors | Performance overhead (varies — must benchmark); harder to debug ("why are no rows returned?"); Postgres-specific (not portable to MySQL/SQLite); operational complexity for `BYPASSRLS` escape-hatch role | **Rejected for shared core DB (revised 2026-05-08).** Stakeholder pivot accepted the direct-DB-access caveat in exchange for portability + operational simplicity. May be revisited if a regulated tenant ever demands DB-level isolation for core data. |
| 2 | **Schema-per-tenant** (one `tenant_<id>` schema per tenant) | Strong logical isolation; per-tenant backups easy | Per-request schema switching breaks the existing single `SessionLocal` pool; thousands of schemas at scale; migration complexity per schema | **Rejected.** Same auth-time connection-routing problem as DB-per-tenant but with weaker guarantees. |
| 3 | **Database-per-tenant** | Strongest possible isolation (different physical DBs); per-tenant tuning + per-tenant backups; no risk of cross-tenant queries at all | Operational cost grows with N tenants × M modules; backup/restore N times; cross-DB FKs impossible; no shared-platform queries possible | **Chosen for module DBs (revised 2026-05-08).** Each tenant gets its own DB per module via `DATABASE_STRATEGY=per_tenant` (extends ADR-001). Module data is typically domain-sensitive (financial records, etc.) — physical isolation matches the threat model. Login + identity stay in the shared core DB. |
| 4 | **Application-only filters** (status quo) | Zero infrastructure cost; full developer control | Single line of defense; no safety net for forgotten filter; no DB-level enforcement; no audit trail for direct DB access | **Failing.** This is what `sec-review-21` and `arch-platform.md` §9 risk #1 flag as inadequate. |
| 5 | **ORM session-event listener** | Simpler than RLS; covers ORM-level bypasses (auto-injects tenant filter on tenant-scoped queries); fail-loud on unset scope context; no Postgres-specific code | Doesn't cover raw SQL via `SQLAlchemy.text(...)`, `db.execute(...)`, or direct psql access | **Chosen for shared core DB** as the second layer (paired with #6 the centralized helper). Together they cover application-layer failure modes; the direct-DB-access path is a documented operational-control concern. |
| 6 | **Centralized scope helper** at `backend/app/core/scope.py` *(new entry — was implied in v1)* | Single API surface for tenant-scoped queries; supersedes ad-hoc `_get_org_context()` per service; enforces fail-loud convention; testable in isolation | Requires every `*Service` migration; backwards-compat concerns during rollout | **Chosen for shared core DB** as the first layer (paired with #5). Closes `audit-04` 4.2.2 medium gap. |
| 7 | **View-based isolation** (per-tenant views with `WHERE tenant_id = ...`) | Familiar SQL pattern; auditable | Blows up at hundreds of tenants; view materialization overhead; doesn't help with INSERT/UPDATE | **Rejected.** Worse than every other option. |
| 8 | **Citus / extension-based horizontal sharding** | Horizontal scale + strong isolation across nodes | Heavyweight; extension-specific; tenant-scoped to *shards* not rows; over-engineered for ~hundreds-of-tenants scale | **Rejected.** Premature optimization for current scale. |

**Pattern (revised 2026-05-08)**: the chosen design is a **hybrid by data sensitivity** — shared core DB with a two-layer logical isolation stack (helper + ORM listener) for high-frequency, low-isolation-need data (identity, system catalog, RBAC); database-per-tenant for module data where the threat model justifies physical separation. The trade-off is honest: the shared core DB has a documented direct-access caveat that operational controls (audit-logged tooling, DBA discipline, backup-job review) must cover. RLS was considered and rejected for the core because the portability cost + operational debugging cost outweigh the marginal protection over what helper + listener already provide for application-level access.

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

- **Real demand**: every persona faces concrete pain that vision-02 materially reduces. Pradeep gets safety nets at the application layer; Diego gets a clean per-tenant module-DB contract; Yelena gets a structural answer for auditors on module data and a documented operational-controls answer for core data.
- **Bounded scope**: one architectural change, one sprint, well-defined boundaries (helper + listener for core; DB-per-tenant for modules). Scope OUT explicitly names six things this is NOT.
- **Honest trade-off**: the chosen design accepts a known gap (direct-DB-access against the core) in exchange for portability + operational simplicity + zero RLS performance overhead. The gap is documented, not hidden, and operational controls cover it.
- **Risks acknowledged**: vision-02 §7 names per-(tenant × module) DB count growth, implicit cross-tenant reads, SQLAlchemy edge cases, migration fan-out failure modes, cross-DB FK impossibility, developer ergonomics — each with a mitigation.

**Caveat — provisioning prototype first** *(revised 2026-05-08)*: vision-02's success metric #5 is "per-tenant module DB provisioning time ≤ 60 s". The first sprint task should be a provisioning prototype against the existing financial module on a clean tenant. If provisioning exceeds 60 s under representative load, the operational story (Alembic fan-out, connection-pool initialization, secrets distribution for module-DB credentials) needs rework before sprint close. Without this gate, there's a real risk of shipping a provisioning flow that becomes the new bottleneck for tenant onboarding.

If the stakeholder cannot commit to that provisioning gate, the recommendation downgrades to **PIVOT** — narrow vision-02 to "centralized scope helper + ORM listener only on the shared core DB" and defer the per-tenant-module-DB work to a separate epic. The core-DB hardening alone retires the headline `sec-review-21` finding even without the module-DB split.

---

## Hand-off

This brief is `status: review`. Next: A3 Product Owner reads `vision-02` + this brief and authors `epic-22-tenant-isolation-hardening.md` (likely structured as a single-feature epic with stories for: scope helper, ORM listener, RLS migration, BaseModule contract addition, adversarial test plan, and the benchmark gate as story #1).
