---
artifact_id: research-03-module-lifecycle-and-activation
type: research
producer: A2 Business Analyst
consumers: [A3 Product Owner]
upstream: [vision-03-module-lifecycle-and-activation]
downstream: []
status: approved
created: 2026-06-18
updated: 2026-06-18
recommendation: proceed
---

# Research Brief — Module Lifecycle & Activation (research-03)

> Validates `vision-03-module-lifecycle-and-activation`. Covers personas, user journey maps, competitor patterns, platform constraints, and a proceed/pivot/kill recommendation.

---

## 1. Personas

### Persona A — Tariq, the Platform Developer (you)

**Role**: SaaS platform owner and sole module developer.

**Goals**:
- Ship a new module to production with zero manual steps — one command, done.
- Be confident that a failed install cannot leave the platform in a broken state.
- Test a module locally in dev, know it will behave identically in prod.
- Uninstall a module completely when it is sunset, with no orphaned rows.

**Frustrations**:
- Today there is no defined packaging format — each module deploy is improvised.
- Running Alembic migrations manually on prod is fragile; forgetting a step breaks the module silently.
- The `post_install` / `post_enable` hooks exist in `BaseModule` but never fire, so module initialisation logic cannot be relied on.
- No way to verify a production install was clean without querying the DB by hand.

**Primary tasks**:
1. `git tag v1.0.0 && git push` → expects CI to produce an artifact and install it on prod automatically.
2. Verify install: see the module appear as `status=available` in `module_registry` with correct version.
3. Roll back a bad install without downtime.

**Job story**: *When I finish testing a module in dev and want to ship it, I want to run one command (or push a tag) so that the module is available to tenants in production within minutes — with no SSH, no manual SQL, and no risk of partial state.*

---

### Persona B — Amira, the Tenant Administrator

**Role**: Admin for a mid-size company using App-Buildify as their operations platform. Non-technical; comfortable with SaaS admin panels but does not know what an API is.

**Goals**:
- Enable a new module to unlock features her team is asking for.
- Understand what a module will do to her account before she turns it on (permissions added, new menu items).
- Turn off a module her team stopped using without worrying about data loss.

**Frustrations**:
- Today the activation UI is broken (wrong API contract, no feedback on failure).
- No way to preview what activating a module will change.
- No confirmation that deactivation is safe — will it delete her data? (The answer is no, but it is not communicated.)

**Primary tasks**:
1. Browse the list of installed modules, read a short description, see current status.
2. Activate a module: review the permissions + menu items summary, confirm, see features appear in the nav.
3. Deactivate a module: confirm it will not delete data, toggle off, features disappear.

**Job story**: *When my team asks me to enable a new module, I want to see exactly what it will add to our account and activate it in under two minutes — without needing to contact support or understand the underlying platform.*

---

### Persona C — Diego, the Company Administrator

**Role**: Manages one company within a tenant that has multiple companies. Needs module control at the company level, not just tenant level.

**Goals**:
- Activate a module for his company only, without affecting other companies in the tenant.
- See a module his tenant has available but his company has not yet activated.

**Frustrations**:
- The current module system is tenant-scoped only. Company-level activation is not implemented.
- No visibility into which companies within the tenant have which modules active.

**Primary tasks**:
1. View tenant-available modules, see which are active for his company.
2. Activate/deactivate at company scope.

**Job story**: *When I want to roll out a new module to my company before the whole tenant, I want company-level activation so that other companies are not affected during my evaluation period.*

---

## 2. User Journey Maps

### Journey 1 — Tariq ships a new module version to production

| Step | Action | Touchpoint | Emotion |
|---|---|---|---|
| 1 | Finishes dev + tests pass locally | Dev environment, `manage.sh` | Satisfied |
| 2 | Tags the release: `git tag v1.2.0 && git push` | Git / CI | Neutral |
| 3 | CI pipeline picks up the tag, runs `manage.sh module pack` | CI runner | Watching |
| 4 | Pack command validates the manifest against JSON schema; fails fast if malformed | CI log | Relieved (early failure) |
| 5 | CI runs `manage.sh module install <artifact>` on the production host | SSH / deploy script | Tense |
| 6 | Install command: validates manifest, runs Alembic migrations, wires hooks, registers in `module_registry` | Production DB | Tense |
| 7 | Install succeeds; post-install integrity check confirms `module_registry.install_status = ready` | CI output | Relieved |
| 8 | Module appears as `status=available` for all tenants | Platform admin view | Confident |
| 9 | (If step 6 fails) Install rolls back; platform is in pre-install state; CI marks deploy failed | CI output | Frustrated but not panicked — no manual cleanup needed |

**Pain point today**: Steps 3-7 do not exist as a defined process. Tariq does all of this manually and has no rollback.

---

### Journey 2 — Amira activates a module for her tenant

| Step | Action | Touchpoint | Emotion |
|---|---|---|---|
| 1 | Hears from her team that a "Financial Reporting" module is available | Colleague message | Curious |
| 2 | Navigates to Settings -> Modules | Sidebar nav | Neutral |
| 3 | Sees list of installed modules with name, description, category, current status | Modules page | Oriented |
| 4 | Finds "Financial Reporting", reads description, sees status = Available | Module card | Interested |
| 5 | Clicks "Activate" | Module card button | Hopeful |
| 6 | Pre-activation modal shows: permissions to be added, new menu items, dependency check | Modal | Careful |
| 7 | Confirms activation | Modal confirm button | Committed |
| 8 | Activation completes; "Financial Reporting" appears in sidebar nav | Nav updates live | Delighted |
| 9 | Audit log shows `module.activated` event | Audit log | Reassured |

**Pain point today**: Step 6 and 8 do not work (11.1.2 DRIFT). Amira gets a silent failure or a 404.

---

### Journey 3 — Amira deactivates a module

| Step | Action | Touchpoint | Emotion |
|---|---|---|---|
| 1 | Team stops using the Inventory module | Colleague feedback | Decisive |
| 2 | Goes to Settings -> Modules, finds Inventory | Modules page | Neutral |
| 3 | Clicks "Deactivate" | Module card | Slightly anxious (will data be deleted?) |
| 4 | Confirmation modal explicitly states: "Your data will not be deleted. Menu items and permissions will be removed." | Modal | Reassured |
| 5 | Confirms deactivation | Modal confirm button | Confident |
| 6 | Inventory menu items disappear from nav; RBAC seeds for Inventory are disabled | Nav + permissions | Satisfied |
| 7 | Audit log shows `module.deactivated` event | Audit log | Done |

---

## 3. Competitor Analysis

*Scope: how established SaaS platforms handle operator-side module packaging/deployment and tenant-side activate/deactivate. Not a marketplace comparison — that is out of scope per vision-03.*

| Platform | Packaging approach | Tenant activation model | Strengths | Weaknesses | Differentiator for App-Buildify |
|---|---|---|---|---|---|
| **Odoo (on-prem/SaaS)** | Python package (`__manifest__.py`), installed via `pip` + `odoo-bin -u`. Alembic-equivalent runs on restart. | Tenant admin activates from Settings -> Apps UI; one-click, immediate. | Well-understood packaging; dependency graph enforced at install time. | Restart required for install; no atomic rollback; production installs are manual ops. | App-Buildify should support zero-downtime install (no restart) and atomic rollback. |
| **Frappe / ERPNext** | `bench install-app <repo>` clones repo, runs migrations, restarts. Artifacts are Git repos. | Site-level activation via Desk -> App list or `bench --site install-app`. | Clean CLI, well-documented. Git-as-package is simple for open source. | Git-as-package is not a sealed artifact; prod can drift from dev. No pre-activation summary for tenants. | App-Buildify should use a sealed tarball/OCI artifact so prod = dev exactly. |
| **Salesforce (Managed Packages)** | ISV creates a managed package; installed on org via URL + namespace. Metadata deployed via MDAPI. | Org admin installs from AppExchange or install URL; post-install script runs. | Atomic install; namespace isolation; strong dependency model. | Extremely complex packaging; requires Salesforce org for development; long certification process. | App-Buildify is far simpler -- no namespace isolation needed, no AppExchange gatekeeping. Borrow the "post-install script runs automatically" pattern. |
| **HubSpot (Private Apps / Extensions)** | Developer builds app, deploys via HubSpot CLI (`hs deploy`). Tenant activates in Marketplace tab. | Tenant admin connects the app from their HubSpot account; OAuth flow; permissions summary shown before approval. | Excellent permissions-summary UX before activation. Clean CLI deploy. | HubSpot apps are integrations (OAuth), not platform modules -- different model. | Borrow the pre-activation permissions summary UX (Amira journey step 6). |
| **Shopify (Private / Custom Apps)** | Developer creates app in Partner Dashboard; distributes via install link. No public listing required for private apps. | Merchant clicks install link; OAuth permissions screen shown; one-click approve. | Simple install for operators; permissions screen is well-understood pattern. | Requires internet-accessible OAuth endpoint; not suitable for self-hosted SaaS modules. | Same pre-install permissions review pattern; skip the OAuth complexity since modules are first-party. |

**Key patterns to adopt:**
1. **Sealed artifact** (not Git clone) — guarantees dev = prod. Take from Salesforce/HubSpot CLI model.
2. **Post-install script runs automatically** — not manually. Take from Salesforce managed package pattern.
3. **Pre-activation permissions + menu summary** — tenant admin sees exactly what will change before confirming. Take from HubSpot / Shopify permissions screen UX.
4. **Dependency enforcement at activation** — not just at install. Take from Odoo/Frappe.
5. **CLI-first for operator, UI-first for tenant** — clear role separation. Industry standard.

---

## 4. Platform Constraints

| Constraint | Source | Implication for this vision |
|---|---|---|
| **API contract drift (11.1.2)** | audit-11 | The first story must be "decide and document the canonical lifecycle API" before any UI or pipeline work. Both frontend and backend must align on it. |
| **`BaseModule` hook wiring gap** | audit-11 cross-cutting | The packaging pipeline cannot claim `post_install` fires until the event subscription is wired. This is a hard dependency for journey 1 step 6. |
| **Epic 22 `per_tenant` DB strategy in-flight** | epic-22 status | Module install/uninstall must call the same provisioning/cleanup service as epic-22 stories 22.4.2 and 22.4.5. The two epics must not build parallel DB provisioning code paths. Coordinate via shared service. |
| **No CI/CD pipeline exists** | audit-18 DX gaps | `manage.sh module install` is the right first target. A CI/CD webhook can be layered on top later (vision-03 scope note). The `manage.sh` command is the atomic unit. |
| **Company-level activation (Persona C)** | Current model is tenant-scoped only | The data model (`tenant_module_activations`) should have a nullable `company_id` column from day one to avoid a future migration. UI for company-level toggle can be deferred to a follow-up story if needed. |
| **`DATABASE_STRATEGY` env var** | adr-001, epic-22 | Install must read this flag and skip per-tenant DB provisioning when `strategy=shared`. Must not hardcode assumptions. |

---

## 5. Open Questions Resolved

| Question (from vision-03) | Research finding | Recommendation |
|---|---|---|
| Deactivation immediate or deferred? | HubSpot/Shopify: immediate. Odoo: requires restart (avoid). | **Immediate** -- menu items removed from next request; JWT-cached permissions expire at token TTL (document this; do not force a session purge). |
| Uninstall: soft-delete or immediate? | Salesforce: soft-flag first, hard cleanup on confirmation. | **Two-phase** -- deactivate all tenants first (immediate), then hard cleanup runs as a background job after operator explicit confirmation. Same pattern as epic-22 story 22.4.5. |
| All tenants see installed module by default? | Odoo/Frappe: yes. Salesforce: namespace scoping. | **Yes, visible to all tenants by default** -- no whitelist needed for v1. Add a `visibility` flag to the data model so it can be restricted later without a migration. |
| Pre-activation summary: required or optional? | HubSpot: always shown. Shopify: always shown. | **Always shown on first activation per tenant**; skippable (remembered) on re-activation. Industry standard. |

---

## 6. Recommendation

**PROCEED.**

The vision is technically sound, fills a confirmed and audited gap (audit-11 findings 11.1.2 DRIFT, 11.1.1 PARTIAL, cross-cutting hook gap), and targets a workflow the platform developer experiences on every module ship. The competitor analysis confirms the patterns are well-understood: sealed artifact packaging, automated post-install hooks, CLI-first for operators, and a permissions-summary UX for tenant activation are all proven in production systems.

There is no market-validation risk here -- this is not a speculative feature. The platform is already designed as pluggable; this epic delivers on that architectural promise. The primary execution risk (API contract drift, Epic 22 coordination) is known and mitigable by sequencing correctly: API contract decision first, then pipeline, then activation UI.

**Pivot consideration**: the only reason to pivot would be if the `BaseModule` hook wiring gap turns out to require a deeper architectural change (e.g. the event bus is insufficient for distributed mode). This should be spike-tested in the first story of the epic before the full backlog is committed. If the spike fails, scope the epic to the packaging pipeline + activation UI only and defer hook wiring to a follow-up.

**Suggested epic structure for A3:**
1. API contract decision + frontend fix (11.1.2 drift) -- prerequisite for everything else
2. `manage.sh module pack` + manifest JSON schema validation
3. `manage.sh module install` with atomic rollback + post-install hook wiring
4. Tenant activation UI (module list, activate with preview, deactivate with safety message)
5. Operator uninstall (two-phase: deactivate all, then hard cleanup via shared epic-22 service)
6. Audit trail for all lifecycle events
7. Company-level activation (Persona C) -- can be deferred to v2 if time-constrained

**A3 caveat**: story 1 (API contract) must complete and be approved before any other story begins. All other stories depend on the contract being settled.
