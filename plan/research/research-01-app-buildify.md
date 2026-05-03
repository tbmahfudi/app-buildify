---
artifact_id: research-01-app-buildify
type: research
producer: A2 Business Analyst
consumers: [A3 Product Owner]
upstream: [vision-01-app-buildify]
downstream: []
status: review
created: 2026-04-29
updated: 2026-04-29
recommendation: proceed
decisions:
  - Cooper goal-directed personas (per A2 spec §9)
  - Job Stories for the user journey ("when… I want… so I can…")
  - Competitor matrix bounded to 6 entries
  - Recommendation: proceed with caveats — prioritize 🔴 audit gaps from vision-01 §7 before net-new features
open_questions:
  - Persona research is qualitative (no field interviews yet) — confirm with stakeholder before committing to persona-led roadmap
  - Pricing model not analyzed — out of scope for engineering research, owned by GTM
---

# Research Brief — App-Buildify Platform (research-01)

> **Upstream**: [`vision-01-app-buildify`](../vision/vision-01-app-buildify.md). This brief validates the vision with personas, user-journey analysis, competitive scan, and a proceed/pivot/kill recommendation.

## Recommendation: **PROCEED** (with caveats)

The vision addresses a real, validated gap in the market: enterprise teams need internal apps faster than custom dev allows, but generic NoCode tools fundamentally do not model multi-tenant + multi-company + multi-branch + multi-department hierarchy with proper RBAC. The platform is ~70% built and the gaps that remain (per the audit suite) are concrete and addressable. **Proceed** — but the next sprint should retire 🔴 risks from `vision-01` §7 before shipping any new feature epic. Adding features on a foundation with broken role CRUD, missing wildcard permissions, dead per-entity perms, and zero tests is technical debt accumulation.

---

## 1. Personas

Two personas are expanded in depth below (the primary buyer and the primary daily user). The other two from the vision (Tenant Administrator, Module Developer) are summarized.

### 1.1 Persona A — "Maya the Power User" *(PRIMARY)*

**Role**: Operations / Business Analyst at a mid-sized organization (200-2,000 employees, multi-subsidiary). Reports to COO or VP Operations. No formal CS background; comfortable in Excel, Airtable, basic SQL.

**Goals**
- Ship a working tool to her colleagues *this week*, not next quarter
- Match the tool to how the org actually works (subsidiaries, branches, departments)
- Avoid begging IT for every change
- Make sure only the right people see the right data

**Frustrations**
- IT backlog is 6+ weeks for any custom app
- "Generic NoCode" requires her to flatten her org's hierarchy into a single-tenant app
- Spreadsheet sprawl: 40 tabs, no audit trail, broken on every reorg
- Off-the-shelf SaaS requires committee-level procurement and still doesn't fit

**Primary tasks**
- Design a new entity (e.g. "Vendor Risk Assessment") with fields, validation, lookups
- Configure who can see/edit which records (by company, branch, department)
- Build a dashboard for her director showing rollups across subsidiaries
- Hand off the app to end users with confidence it won't break

**Why she'd choose App-Buildify over alternatives**
- Hierarchy-aware out of the box — she doesn't have to invent "company_id" everywhere
- Visual designer for entities + workflows + dashboards in one place
- Audit log + RBAC give her director's compliance team confidence

**Why she might churn**
- If the NoCode designer keeps surfacing technical concepts (migration revisions, JSONB, ALTER TABLE) she'd lose trust
- If RBAC is opaque or wrong (e.g. wildcards don't actually wildcard, per `audit-04` 4.2.1) she'd hit a wall
- If a dashboard takes > 10 seconds to load, she'd bail

### 1.2 Persona B — "Diego the Module Developer" *(SECONDARY)*

**Role**: Senior Backend Developer at a partner firm or in-house IT, 8+ years experience. Python + JS comfort. Ships internal tools and integrations.

**Goals**
- Add a new domain capability (HR, CRM, Inventory) that becomes available to multiple tenants
- Work within a stable contract (BaseModule SDK) and avoid forking the core
- Ship in days, not months, and not get blocked on platform-team review for every change

**Frustrations**
- "Plugin architectures" that look clean in docs but require platform-team escalations for every non-trivial change
- Module systems where you can't run/test in isolation (must boot the whole platform)
- No clear contract — you find out an interface changed when prod breaks

**Primary tasks**
- Read the manifest spec and `BaseModule` ABC, scaffold via `scripts/create-module.sh`
- Write his module's models, routers, services in the standard 3-tier layout
- Run his module standalone (distributed mode per ADR-001) AND in-process (monolith mode) without code changes
- Publish via the module registry with a single command

**Why he'd choose App-Buildify**
- Frozen `BaseModule` contract (per ADR-001) — no churn risk
- Single artifact runs as monolith OR distributed → small tenants are cheap, big tenants scale
- Per-module Alembic version table → his migrations don't fight the core's

**Why he might churn**
- If event bus is a stub (it is — `audit-11` flags the LISTEN/NOTIFY placeholder), distributed mode is a marketing claim, not reality
- If module dev guide doesn't exist (it doesn't — `audit-18.2.3` PARTIAL), he has to read source code to learn the contract

### 1.3 Other personas (summary)

| Persona | Primary use | Critical need from platform |
|---------|-------------|-----------------------------|
| **Tenant Administrator** | Provisions tenants/companies/branches/departments; manages users + roles; enables modules | Fast provisioning workflow; clear RBAC model; reliable audit log |
| **End User** | Operates the resulting business apps daily | Fast page loads; clear error messages; doesn't see UI elements they can't use (per Epic 4.2.3) |

---

## 2. User Journey Map — "First business app, day 0 to day 14"

Maps to vision-01 success metric #1 ("time-to-first-business-app per new tenant ≤ 14 days"). Persona: **Maya the Power User**. Format: Job Stories per step.

| Step | Job Story | Touchpoint | Emotion | Friction today (per audits) |
|------|-----------|-----------|---------|------------------------------|
| 1. Sign-up | When I sign up for App-Buildify, I want a working tenant in < 5 min so I can start exploring without waiting on a sales call | Sign-up form + email confirmation | 😊 hopeful | Tenant admin can't create users via API (`audit-03` story 3.1.1 MISSING) — she may need to seed users from DB |
| 2. Org modeling | When I configure my org, I want to mirror my real hierarchy (companies → branches → departments) so subsequent permissions make sense | Org admin page (`epic-02` Feature 2.2) | 😊 confident | Works (audit-02 DONE) |
| 3. Roles & users | When I invite my team, I want them to land in roles that match their job, not be admins of everything | RBAC page (`epic-04`) | 😟 anxious | Role CRUD MISSING (`audit-04` 4.1.1); only system roles available; wildcards don't work (4.2.1) |
| 4. Entity design | When I design "Vendor Risk Assessment", I want to define fields, validation, and a few lookups visually | Entity Designer (`epic-05`) | 😊 in flow | Mostly works (audit-05 mostly DONE); per-entity perms are dead schema (4.2.4) so she can't lock it down |
| 5. Workflow | When I add an approval workflow to my entity, I want to set states, transitions, and approvers in a designer | Workflow Designer (`epic-07`) | 😊 satisfied | Works (audit-07 DONE) |
| 6. Dashboard | When my director asks "how many open assessments?", I want to drag a KPI widget on a dashboard and pick a filter | Dashboard Designer (`epic-09`) | 😊 proud | Works (audit-09 DONE) |
| 7. Hand-off | When I share the app with my team, I want only the right people to see the right records, with an audit trail my compliance team trusts | Permissions page + audit log | 😟 worried | Audit log works (audit-13.1 DONE); per-entity perms broken (4.2.4) — she can't enforce row-level scope; wildcards broken (4.2.1) |
| 8. First incident | When a colleague forgets her password, I want her to reset herself in 2 minutes, not call me | Password reset email | 😡 frustrated | `POST /auth/forgot-password` writes to queue; queue has no delivery worker (`audit-14` Feature 14.2 MISSING) — email never arrives |

**Headline finding**: the journey is **structurally sound but emotionally broken at steps 3, 7, and 8**. RBAC + per-entity perms + notification delivery are all flagged 🔴 in `vision-01` §7 — and they all hit Maya's primary use case. These three should be the next sprint's focus.

---

## 3. Competitor Matrix

Six entries spanning generic NoCode, enterprise low-code, suite ERPs, and the spreadsheet/database hybrid category.

| # | Competitor | Strength | Weakness | App-Buildify differentiator |
|---|-----------|----------|----------|-----------------------------|
| 1 | **Retool** | Fast UI builder; rich integrations; great DX for devs | Single-tenant model; weak RBAC; no native multi-company hierarchy; pricing scales with users | Native tenant→company→branch→department isolation; RBAC scope hierarchy; fixed deploy cost |
| 2 | **Appsmith** (open-source) | Free; self-hostable; visual app builder | No first-class module SDK; weak hierarchy modeling; community plugins not enterprise-grade | `BaseModule` SDK with frozen contract; deployable as monolith OR distributed (ADR-001) |
| 3 | **Airtable** | Polished UX; great for small teams; many templates | Database/spreadsheet hybrid, not an app platform; weak workflow engine; row-level perms paid only | True app platform with workflows, dashboards, reports; entity definitions become real Postgres tables |
| 4 | **NetSuite** (Oracle) | Mature ERP; broad domain coverage | Expensive; rigid; long implementation cycle; customization requires partners | NoCode entity designer + workflow + RBAC by-the-hour, not by-the-quarter |
| 5 | **OutSystems** | Enterprise low-code; strong governance; established vendor | Per-developer license cost; vendor lock-in; not NoCode for business analysts | Same enterprise governance with NoCode designer accessible to non-developers; OSS-friendly stack (Python + Vanilla JS) |
| 6 | **Microsoft Power Platform** | Tight Microsoft 365 integration; Power Apps + Power Automate breadth | Microsoft-stack lock-in; complex licensing; multi-tenant story is per-environment, not native | Cross-cloud; native multi-tenancy + per-tenant module activation; no Microsoft dependency |

**Pattern**: every direct competitor either (a) treats multi-tenancy as a deployment concern rather than a first-class data model (Retool, Appsmith, Airtable), or (b) achieves enterprise governance at the cost of NoCode accessibility and vendor lock-in (NetSuite, OutSystems, Power Platform). App-Buildify's defensible position is the **intersection**: native enterprise hierarchy + true NoCode + module SDK + deployment flexibility.

---

## 4. Constraints

Hard constraints that bound any future epic. These are derived from `arch-platform.md` and the audit suite.

### Technical
- **Vanilla JS frontend, no bundler** — limits the library ecosystem; talent pool slightly narrower than React/Vue. Any frontend agent (B3, C3) must work within this.
- **Single Postgres today** (`DATABASE_STRATEGY=shared`). `separate` is wired but unused; switching is an ADR (per ADR-001).
- **`BaseModule` contract is frozen** — modules cannot rely on importing core-platform internals. This is good for boundary integrity but constrains module ergonomics.
- **Multi-tenancy via explicit `tenant_id` filters** — no SQLAlchemy-level safeguard. One missed filter = cross-tenant leak. Cited as 🟡 risk in vision-01.
- **No CI/CD today** (`audit-19.4`). Quality gates are manual via `manage.sh`.

### Organizational
- Single primary product owner (the human stakeholder). No dedicated GTM/marketing/sales function visible in the repo.
- Engineering velocity is unknown — this is the first iteration of the multi-agent SDLC. Conservative sprint sizing recommended.

### Regulatory / compliance
- Audit log + RBAC + multi-tenant isolation imply GDPR/SOC2-adjacent controls. Not certified, but architecturally aligned.
- No PII data residency requirement currently scoped.

---

## 5. Recommendation: PROCEED (justification)

The vision is validated:

- **Real demand**: every persona faces concrete pain that App-Buildify materially reduces (Maya's IT-backlog dependency; Diego's plugin-system frustrations).
- **Defensible position**: the competitive matrix shows no alternative occupies the multi-tenant + true-NoCode + module-SDK intersection.
- **Buildable**: 70% is shipped; remaining 🔴 risks are concrete and bounded (RBAC fixes, Flex layout suite, notification worker, CI/CD). None require architectural redesign.
- **Risks acknowledged**: `vision-01` §7 already names the gaps; this brief confirms they are also the user-journey blockers (steps 3, 7, 8 of the journey map).

**Caveat**: PROCEED **with the constraint that the next sprint retires the 🔴 audit risks before any new feature epic is opened**. Specifically: ship role CRUD (4.1.1), wildcard permissions (4.2.1), per-entity permission enforcement (4.2.4), the Flex layout suite (15.1.1), and at least one notification delivery channel (14.2.1 SMTP). Without these, the user journey is structurally broken at three of its eight steps regardless of how many new features ship on top.

If the stakeholder cannot commit to that sprint discipline, the recommendation downgrades to **PIVOT** — narrow the platform's positioning to "multi-tenant orchestration over a NoCode builder" and walk back any RBAC marketing claims until the implementation matches.

---

## Hand-off

This research is `status: review`. Next: A3 Product Owner reads `vision-01` + this brief and decides which epic(s) the recommendation translates into. Given the PROCEED-with-caveats finding, the most likely first action is a "🔴 Risk Retirement" epic (cross-cutting across epics 4, 14, 15, 19) rather than a net-new feature epic.
