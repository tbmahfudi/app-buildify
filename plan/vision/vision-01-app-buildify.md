---
artifact_id: vision-01-app-buildify
type: vision
producer: A1 Product Manager
consumers: [A2 Business Analyst]
upstream: []
downstream: []
status: review
created: 2026-04-29
updated: 2026-04-29
decisions:
  - Foundational/retroactive vision — codifies what the platform IS so future epics align
  - Geoffrey Moore vision template (per A1 agent spec §9)
  - Risks reference audit files individually rather than duplicating findings
  - Tenant data isolation is positioned as an existential guardrail, not just a feature
open_questions:
  - North Star metric not yet chosen — held for stakeholder
  - OKR alignment deferred until > 1 quarter velocity history exists
  - Should we set a tenant-count or MRR target as a business-side success metric?
---

# Product Vision — App-Buildify Platform (vision-01)

## Vision Statement (Geoffrey Moore template)

**For** enterprise teams (SMBs and large-organization subsidiaries) who **need to ship internal business applications faster than custom development allows, but cannot use generic SaaS because their org structure has multi-company / multi-branch / multi-department hierarchy and granular access requirements**, **App-Buildify** is **a multi-tenant NoCode/LowCode platform with a first-class module system** that **lets non-developers design entities, workflows, dashboards, and reports — and lets developers extend the platform with packaged modules without forking the core**.

**Unlike** generic NoCode tools (Retool, Appsmith) that ignore enterprise hierarchy and access control, or rigid suite-ERPs (NetSuite, SAP) that are expensive and slow to customize, **App-Buildify combines a true tenant → company → branch → department isolation model with a clean `BaseModule` SDK and a single deployment artifact that runs as a monolith or distributed microservices (per ADR-001) — so the platform grows from one team to many without rewrite.**

---

## 1. Problem

Mid-to-large organizations need internal business applications faster than custom development can deliver them, but the available alternatives all fall short:

- **Off-the-shelf SaaS** (CRM, ERP, project tools) does not model the customer's actual organizational structure (subsidiaries, branches, departments) and forces ad-hoc workarounds for access control.
- **Custom development** is slow, expensive, and produces N siloed apps that drift in conventions, auth, and operations.
- **Generic NoCode** (Retool, Appsmith, Airtable) is fast for individual apps but ignores enterprise hierarchy, has no real RBAC scope model, and cannot be extended by the customer's own developers as first-class modules.
- **Suite ERPs** (NetSuite, SAP) cover the breadth but are rigid, expensive, and require dedicated implementation partners.

The result: organizations either suffer the cost of bespoke development or accept tools that don't model their reality.

## 2. Target Users

Four primary personas:

| Persona | Primary use |
|---------|-------------|
| **Tenant Administrator** | Provisions the platform, configures tenants/companies/branches/departments, manages users + roles, enables modules. |
| **Business Analyst / Power User** | Designs entities (NoCode), builds workflows + automation rules, configures dashboards and reports — without writing code. |
| **End User** | Uses the resulting business applications daily — creates records, runs workflows, views dashboards, executes reports. |
| **Module Developer** | Extends the platform via the `BaseModule` SDK — packages new domain modules (Financial today; HR, CRM, Inventory tomorrow) without forking the core. |

Secondary personas (relevant but not primary focus): Platform Operator (DevOps), Compliance Officer (auditing), Integration Engineer (event-bus consumers).

## 3. Success Metrics (SMART)

| # | Metric | Target | Notes |
|---|--------|--------|-------|
| 1 | Time-to-first-business-app per new tenant | ≤ 14 days from sign-up to a published custom entity with at least one workflow attached | Measured per tenant; tracks NoCode usability. |
| 2 | Active-tenant content density | ≥ 5 entities + 2 workflows + 1 dashboard within 90 days of tenant activation | Indicates the platform is "lived in", not just enabled. |
| 3 | Platform availability | ≥ 99.5% monthly | Per `arch-platform.md` §7 NFRs. |
| 4 | API performance | p95 latency < 500 ms; error rate < 0.5% | Per `arch-platform.md` §7. |
| 5 | Module developer onboarding | New module shippable end-to-end (manifest → routers → migrations → frontend page) ≤ 5 days | Tracks SDK quality. |
| 6 | Tenant isolation | Zero cross-tenant data exposure incidents | Floor metric, not a target to "improve". |

## 4. Scope IN

- **Multi-tenancy**: tenant → company → branch → department hierarchy with explicit `tenant_id` isolation
- **Authentication & Identity**: JWT (access + refresh), session lifecycle, password policy, account lockout (Epic 1; 2FA/SSO PLANNED)
- **RBAC**: `resource:action:scope` permissions, roles, groups, role-to-user assignment (Epic 4)
- **NoCode Entity Designer**: entity definition, field types, publishing/migration, archival, virtual entities (Epic 5)
- **Dynamic CRUD & API Layer**: filtering, sorting, search, pagination, server-side aggregation (Epic 6)
- **Workflow Engine**: state machines, approvals, execution history (Epic 7)
- **Automation Rules**: event-driven and scheduled triggers, configurable actions (Epic 8.1)
- **Dashboard & Analytics**: KPI + chart widgets, global filters, drill-down (Epic 9)
- **Reporting**: report definitions, parameters, export (CSV/PDF), scheduled delivery (Epic 10)
- **Module System**: `BaseModule` SDK, manifest-based registration, per-tenant activation, dependency management (Epic 11)
- **First-class Financial Module**: Chart of Accounts, invoicing, payments, journal entries, six standard reports (epic-12, lives in `plan-mod-finance/`)
- **Security & Compliance**: audit logging, security headers, rate limiting, per-tenant security policy (Epic 13)
- **Internationalization**: 5 languages (en/de/es/fr/id) with namespace coverage (Epic 16.1)
- **Settings & Configuration**: user preferences, tenant branding, menu management (Epic 17.1, 17.2)
- **Developer Experience & SDK**: module manifest, BaseModule contract, event bus integration, seed scripts (Epic 18.1)
- **Infrastructure & Deployment**: Docker Compose dev + prod, Nginx gateway, Alembic migrations (per-module version tables) (Epic 19.1, 19.2)
- **Deployment topology**: monolith **and** distributed (microservices) modes from one codebase via `DEPLOYMENT_MODE` env var (per ADR-001)

## 5. Scope OUT

Explicit non-goals for v1:

1. **AI/ML model training and inference as a platform capability.** Consumers may integrate external AI providers; the platform itself does not host models.
2. **Public module marketplace.** Module distribution is initially internal/private (Epic 11.2 is `[PLANNED]`).
3. **Mobile-first or native apps.** Web is the canonical surface today; PWA + offline are roadmap items (Epic 20 is `[PLANNED]`).
4. **Custom-domain full white-label.** Tenant branding (logo, colors, app name) is in scope; vanity domains, custom auth UI, and "remove all references to App-Buildify" are not (Epic 17.3 is `[PLANNED]`).

## 6. Guardrails

Non-negotiables that bind every future epic and ADR:

- **Tenant data isolation is the platform's existential guarantee.** Cross-tenant leakage is treated as the worst possible outcome. (See `arch-platform.md` §9 risk #1; defense-in-depth is an open architectural question but the floor is "no leakage".)
- **Audit log every sensitive operation.** Authentication events, RBAC changes, mutations of sensitive data must produce an audit-log entry.
- **Reuse Flex components first.** Frontend stories never inline custom DOM if a `Flex<X>` component exists or could exist.
- **`BaseModule` contract is frozen** (per ADR-001). New modules MUST conform; modules that cannot are rejected.
- **No breaking API change without an ADR.** Semver discipline; breaking releases require migration notes (Epic 18.2 / Epic 19).
- **No deployment on Friday after 14:00 unless hotfix** (per E1 DevOps spec).

## 7. Risks

Top risks distilled from the audits and architecture review. Each cites the source so the next agent can drill in.

| 🚦 | Risk | Source |
|----|------|--------|
| 🔴 | Wildcard permissions are not implemented; `has_permission()` does literal `in` check, undermining the stated RBAC model | `audit-04-rbac-permissions.md` story 4.2.1 |
| 🔴 | Per-entity permissions exist as a JSONB column but are not enforced (dead schema) | `audit-04-rbac-permissions.md` story 4.2.4 |
| 🔴 | Role CRUD endpoints (`POST/PUT/DELETE /rbac/roles`) are missing — tenant admins cannot create custom roles via API | `audit-04-rbac-permissions.md` story 4.1.1 |
| 🔴 | All 9 Flex layout components (`flex-stack`, `flex-grid`, `flex-split-pane`, …) are missing — every UILDC frontend story depends on them | `audit-15-flex-component-library.md` story 15.1.1 |
| 🔴 | No notification delivery (email/SMS/in-app); password-reset emails currently dead-letter despite Feature 14.1 being DONE | `audit-14-notification-system.md` Feature 14.2 |
| 🔴 | No CI/CD pipeline; no backend or frontend test suites located | `audit-19-infrastructure-deployment.md` 19.4.x; `audit-13-security-compliance.md` 13.4.x |
| 🟡 | Tenant isolation relies on per-service `tenant_id` filters with no SQLAlchemy-level safeguard; one missed filter = cross-tenant leak | `arch-platform.md` §9 risk #1 |
| 🟡 | LISTEN/NOTIFY event-bus subscriber is a stub; distributed deployment mode (ADR-001) is not production-ready until finished | `audit-11-module-system.md`; `arch-platform.md` §9 risk #14 |

## 8. Decisions

- This is a **foundational** vision (vision-01). It documents the platform that already exists (~70% of epics shipped per the audits) so future visions branch from a stable trunk rather than re-deriving scope each cycle.
- Risks reference audit files by name and story ID rather than restating findings — the audits are the source of truth.
- Geoffrey Moore template is used per the A1 agent spec; keep this format for consistency across future visions.
- Tenant data isolation is positioned as an existential guardrail (§6), not a feature, because every audit so far has flagged it as the highest-leverage risk.

## 9. Open Questions

- Should a North Star metric be chosen (e.g. "active tenants with ≥ 1 published business app")? Recommended once telemetry from Epic 13.3 ships.
- OKR alignment per quarter — defer until ≥ 1 quarter of velocity history.
- Business-side metrics (tenant count, MRR, churn) — out of scope for the engineering vision; track separately in the GTM document if/when one exists.
- Should the vision distinguish "core platform" from "module ecosystem" as separate sub-products? Not yet — keep one unified vision until the second module ships.

---

## Hand-off

This vision is `status: review`. Next: human stakeholder (or A2 Business Analyst on dry-run) flips to `status: approved`, then **A2 Business Analyst** consumes it to produce `research-01.md` (personas, user journey maps, competitor matrix, proceed/pivot/kill recommendation).
