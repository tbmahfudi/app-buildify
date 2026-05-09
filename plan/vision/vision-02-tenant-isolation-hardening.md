---
artifact_id: vision-02-tenant-isolation-hardening
type: vision
producer: A1 Product Manager
consumers: [A2 Business Analyst]
upstream: [vision-01-app-buildify, sec-review-21]
downstream: [research-02-tenant-isolation-hardening]
status: approved
created: 2026-05-08
updated: 2026-05-08
decisions:
  - Targeted vision (single-risk focus) — not the broad foundational style of vision-01
  - Scope chosen because sec-review-21 flagged tenant-isolation as the highest residual risk after epic-21
  - Defense-in-depth posture: 3 redundant enforcement layers (explicit filter, SQLAlchemy event, Postgres RLS)
  - Scope OUT lists encryption / multi-region / GDPR explicitly so this doesn't drift into a "platform security" mega-epic
open_questions:
  - Should RLS apply to ALL tenant-scoped tables or only the top-N most sensitive? Defer to A2 research + B1 architecture
  - DATABASE_STRATEGY=separate (per ADR-001) — does each module DB get RLS too, or only the platform DB? Open architectural call
  - Performance budget for RLS: is the existing arch-platform §7 p95 < 500 ms still met? Needs measurement
---

# Product Vision — Tenant Isolation Hardening (vision-02)

## Vision Statement (Geoffrey Moore template)

**For** the App-Buildify platform engineering team and every tenant who relies on the platform's promise that their data stays within their tenant boundary, **vision-02** is **a defense-in-depth tenant-isolation hardening initiative** that **replaces the current single-line-of-defense (every service hand-applies a `tenant_id` filter) with three redundant layers — application-level helper, SQLAlchemy session-event listener, and Postgres Row-Level Security policies — so that no single missed filter, no single buggy migration, and no single rogue admin script can leak cross-tenant data**.

**Unlike** the current "discipline-only" approach which is one missed `WHERE tenant_id = ?` away from a breach, **vision-02 makes cross-tenant leakage architecturally impossible without three simultaneous failures across independent enforcement layers**.

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
| 2 | Adversarial cross-tenant test scenarios passing | ≥ 50 scenarios; 100% pass | Includes: forgotten filter, malicious admin script, raw SQL via psql, ORM-level bypass attempts, module-side vs platform-side, distributed-mode boundary |
| 3 | `*Service` classes consolidated onto centralized scope helper | 100% migrated; zero ad-hoc `Model.tenant_id == ...` literals outside the helper | Closes `audit-04` 4.2.2 medium gap |
| 4 | Postgres RLS policies enabled on tenant-scoped tables | **All** tenant-scoped tables in the platform DB; **all** tenant-scoped tables in any module DB | "Tenant-scoped" defined as: table has a `tenant_id` column and at least one row whose access is tenant-bounded |
| 5 | API p95 latency regression budget | ≤ +5% over `arch-platform.md` §7 baseline (500 ms) → ≤ 525 ms | Must measure before/after; if regression exceeds budget, narrow RLS scope or use partial indexes |
| 6 | Zero functional regressions | All e2e tests in `test-plan-21` + a new `test-plan-22` pass | Re-runs `test-plan-21` to verify epic-21 features still work |
| 7 | Module developer onboarding time | ≤ 1 day to add a new tenant-scoped entity with full isolation | Measures whether the new helper is actually easier than hand-rolling |

## 4. Scope IN

- **Centralized scope helper** at `backend/app/core/scope.py` — exposes `apply_tenant_scope(query, model, user)` and `tenant_scope_dependency(user)` for FastAPI; supersedes `_get_org_context()` from `DynamicEntityService` (audit-04 4.2.2)
- **SQLAlchemy session-event listener** that intercepts queries against tenant-scoped tables and auto-injects the tenant filter when a session-level scope context is set; raises a loud error if scope is unset (no fail-open)
- **Postgres Row-Level Security (RLS) policies** on tenant-scoped tables; activated via `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` + per-table policy referencing a session variable (`current_setting('app.current_tenant_id')`)
- **Database-role separation** — application connections set the session variable; an explicit `BYPASSRLS` role exists for legitimate cross-tenant operations (admin tooling, backups) and is used only via a documented escape hatch
- **`BaseModule` contract update** — modules declare which of their tables are tenant-scoped; the framework wires the RLS policies + the SQLAlchemy listener registration on module install/enable
- **Adversarial test plan** — at least 50 scenarios across: explicit-filter-skip, raw SQL bypass attempt, ORM-level bypass, cross-module reads, distributed-mode boundary crossing, race-condition timing, scope-unset fail-loud, RLS-bypass via SECURITY DEFINER misuse
- **Migration tooling** — Alembic migration that enables RLS on each tenant-scoped table; safe to run on a populated DB; reversible
- **Documentation** — single page `docs/platform/TENANT_ISOLATION.md` documenting the 3 layers, the escape hatch, the test scenarios, and how to add a new tenant-scoped table

## 5. Scope OUT

Explicit non-goals so this vision doesn't sprawl into a "platform security" mega-epic:

1. **Encryption at rest for sensitive PII fields** — separate concern, separate epic. Use the platform's at-rest encryption story when it lands.
2. **Audit-log forensics tooling** for breach detection — useful but distinct from prevention; track separately.
3. **Multi-region replication / data residency** — strategic feature, not a security gap. Not in scope.
4. **Tenant data export / GDPR right-to-be-forgotten** — operational tooling on top of isolation, not isolation itself.
5. **SMTP password / module API key encryption** — `sec-review-21` finding M-1; tracked under Epic 14.
6. **CI/CD + automated test framework** — last open 🔴 from `vision-01` §7; deserves its own vision.

## 6. Guardrails

- **No backwards-incompatible API surface changes.** RLS is internal; consumers see the same responses.
- **No manual tenant migration required.** A tenant who installs the new platform version must work without hand-applied DB changes. The Alembic migration handles everything.
- **Defense-in-depth, not defense-instead-of.** All three layers (helper + SQLAlchemy listener + RLS) deploy together. Removing any one without removing the others is not allowed.
- **Fail-loud, not fail-open.** If the scope context is unset when a tenant-scoped query runs, the request fails with a 500 (and an audit log entry), it does NOT silently return all tenants' rows.
- **Performance budget.** ≤ +5% p95 latency regression. Larger regressions trigger a scope narrow (e.g. RLS only on the top-10 most sensitive tables).
- **One escape hatch, well-documented.** A single named DB role (`platform_admin`) with `BYPASSRLS` exists for backups, migrations, and superuser operations. Every use is audit-logged.
- **No `# noqa` / `# tenant-skip` magic comments.** If a service legitimately needs cross-tenant access, it goes through the named escape hatch, not a comment-driven bypass.

## 7. Risks

| 🚦 | Risk | Mitigation |
|----|------|-----------|
| 🔴 | RLS performance regression on hot queries (e.g. dashboards aggregating across many tenant rows) | Benchmark required before broad rollout; Postgres `LEAKPROOF` annotation on the policy function; partial indexes on `(tenant_id, ...)` |
| 🔴 | Existing services may have implicit cross-tenant reads (admin tooling, support runbooks) that break under RLS | Survey first (B1 + audit cross-cutting); explicitly migrate each to the escape-hatch role |
| 🟡 | Modules with `DATABASE_STRATEGY=separate` (per ADR-001) need their own RLS deployment; coordinate with module-system epic | Module-installation hook handles per-DB RLS setup |
| 🟡 | SQLAlchemy session-event listener edge cases with `bulk_insert_mappings` / `core` queries that bypass the ORM Query path | Document known unsafe APIs; require code review to flag them; or augment listener to cover Core insert/update too |
| 🟡 | Migration to enable RLS on a populated table can lock the table briefly; large tables (`audit_logs`, `notification_queue`) need careful timing | Migration runbook with maintenance-window guidance; consider `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` followed by separate policy creation under low-traffic windows |
| 🟢 | Developer ergonomics — the new helper API must be easier than hand-rolling, otherwise team won't adopt | Treat helper API as a UX surface; measure adoption (metric #3); iterate |

## 8. Decisions

- **Targeted, not foundational.** vision-02 is intentionally narrow: one risk, one architectural change, one sprint. Contrast with vision-01 which was a foundational scope statement.
- **Defense-in-depth over single-layer.** Three layers chosen because each has a different failure mode: application bugs (helper), ORM misuse (SQLAlchemy listener), DB-direct-access (RLS). Any one alone would have a known bypass.
- **Postgres RLS chosen over schema-per-tenant.** Schema-per-tenant would mean a different connection per tenant request, which doesn't fit the existing SessionLocal pool architecture. RLS uses a session variable that's set per request — fits cleanly with existing FastAPI dependency injection.
- **Risks reference upstream artifacts** (sec-review-21, arch-platform §9, audit-04 4.2.2) rather than restating findings.

## 9. Open Questions

- Should RLS apply to ALL tenant-scoped tables or only the top-N most sensitive (where N = some agreed threshold like "tables with PII or financial data")? Defer to A2 research + B1 architecture review.
- DATABASE_STRATEGY=separate (per ADR-001): does each module DB get its own RLS deployment, or only the platform DB? Open architectural call — record as new ADR if needed.
- Performance budget: existing baseline is `arch-platform.md` §7 p95 < 500 ms. Is +5% acceptable to all consumers, including dashboard-heavy tenants? May need stakeholder ratification.
- Should we ship a "shadow mode" first — RLS policies installed but in audit-only (log violations, don't block) — for a soak period before enforcement? B1 architecture decision.

---

## Hand-off

This vision is `status: review`. Next: human stakeholder (or A2 Business Analyst on dry-run) flips to `status: approved`, then **A2 Business Analyst** consumes it to produce `research-02.md` (target users, current-state survey of services for tenant-filter discipline, competitor matrix of multi-tenant DB-level isolation patterns, proceed/pivot/kill recommendation).
