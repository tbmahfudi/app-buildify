---
artifact_id: pm-review-frontend-screens-01
type: product-review
producer: A1-product-manager
consumers: [A3-product-owner, B3-ux-designer, C3-frontend-developer]
status: review
created: 2026-06-19
---

# Product Manager Review — Frontend Screens
## Cross-check: UI vs Backend Capability vs Industry Practice

---

## Executive Summary

App-Buildify has **37 distinct screens** across 10 functional areas. The backend is
substantially more capable than what the frontend currently surfaces. Several
high-value backend features are either invisible to the user or have placeholder UIs.
Four areas have critical gaps that directly harm user trust and retention.

---

## Screen Inventory & Assessment

### ✅ Area 1: Authentication (login, profile, settings-security)

**Screens:** `login.html`, `profile.html`, `settings-security.html`

**Backend available:** login, logout, refresh, change-password, reset-password-request,
reset-password-confirm, password-policy, `/auth/me` (GET + PUT).

| Screen | Status | Gap |
|---|---|---|
| Login | Good — form with gradient CTA | No "Remember me", no SSO hint, no MFA prompt |
| Profile | Exists | PUT `/auth/me` is wired; but profile picture upload is not (no file endpoint) |
| Settings → Security | Exists | Password-policy endpoint exists but policy is never shown to user before they type |

**Recommendations (priority order):**
1. **HIGH** — Show live password-strength feedback on the change-password form using the `/auth/password-policy` endpoint. Backend already returns `min_length`, `require_uppercase`, etc. — render a checklist as user types. Industry standard (GitHub, Okta).
2. **MEDIUM** — Add "Forgot password?" link on login screen. Backend has `reset-password-request` and `reset-password-confirm` endpoints; no frontend screen exists for either flow.
3. **LOW** — Add "Remember me" (extend token TTL client-side) and a session list on the Security settings page.

---

### ⚠️ Area 2: Users & Roles (users, rbac, auth-policies)

**Screens:** `users.html`, `rbac.html`, `auth-policies-page.js`

**Backend available:** full CRUD for users, roles, permissions; user-role assignment;
permission bulk-patch; grouped permission listing; user's effective permissions.

| Screen | Status | Gap |
|---|---|---|
| Users list | Exists | Invite flow has no dedicated screen — user lands in modal only |
| RBAC roles | Exists | Role → permission matrix exists in backend but UI shows simple list |
| Auth policies | Exists as JS page | No visual indicator of which policy is currently active tenant-wide |

**Recommendations:**
1. **HIGH** — Add a dedicated **Invite User** screen/flow (multi-step: enter email → select role → confirm). Current single-modal approach is too compressed for onboarding new team members. Industry practice (Linear, Notion) uses a dedicated invite page.
2. **HIGH** — Replace the permissions checklist with a **permission matrix table** (role × permission group). Backend returns `GET /permissions/grouped` already — use it. Current UI forces tedious per-permission clicking.
3. **MEDIUM** — Add **effective permissions preview** on the user detail panel. Backend has `GET /users/{id}/permissions` — show a read-only list of what a user can actually do, not just what role they have.

---

### ✅ Area 3: Organisation Hierarchy (companies, branches, departments, tenants)

**Screens:** `companies.html`, `branches.html`, `departments.html`, `tenants.html`

**Backend available:** full CRUD for all four, plus tenant management (superadmin).

| Screen | Status | Gap |
|---|---|---|
| Companies | Exists | No hierarchy visualisation — user can't see which branches belong to which company at a glance |
| Branches / Departments | Exists | Separate screens; no tree/org-chart view |
| Tenants | Superadmin only — good | No tenant health indicators (active users, last login, module count) |

**Recommendations:**
1. **MEDIUM** — Add a collapsible **org-chart tree** on the Companies screen (Company → Branches → Departments). All data is already available; this is a pure frontend addition.
2. **MEDIUM** — On the Tenants list (superadmin), surface key health metrics per row: active user count, last login date, installed module count. Backend has audit logs and user data to derive these.
3. **LOW** — Add breadcrumb navigation on Branch and Department screens showing the parent Company.

---

### 🔴 Area 4: NoCode Platform (data-model, workflows, automations, lookups)

**Screens:** `nocode-data-model.html`, `nocode-workflows.html`, `nocode-automations.html`, `nocode-lookups.html`

**Backend available:** full entity/field CRUD, publish, migration, clone; workflow states/transitions, instances, simulate; automation rules with test/toggle, webhooks; lookups.

| Screen | Status | Gap |
|---|---|---|
| Data Model | Rich — entity + field builder | **Publish flow is hidden**. `POST /entities/{id}/publish` exists; no clear publish button with migration preview |
| Workflows | Exists | Workflow **simulator** (`POST /simulate`) is unimplemented in UI |
| Automations | Exists | Rule **test** (`POST /rules/{id}/test`) and execution history (`GET /executions`) are not surfaced |
| Lookups | Exists | Appears complete |

**Recommendations:**
1. **CRITICAL** — Add a prominent **"Publish" button** on the Data Model entity editor with a migration diff preview (backend: `GET /entities/{id}/preview-migration`). Without this, users don't know their schema changes are live or pending. Matches Airtable/Retool pattern.
2. **HIGH** — Build a **Workflow Simulator panel** (send a payload, trace the state transitions). Backend `POST /workflows/{id}/simulate` is ready. This is the primary debugging tool for workflow authors.
3. **HIGH** — Add **Automation test panel**: click "Test Rule" → see which records matched and what actions fired. Backend `POST /rules/{id}/test` exists. Industry standard (Zapier, Make).
4. **HIGH** — Surface **Automation execution history** in the UI (`GET /executions`). Currently invisible to the user after a rule runs.

---

### ⚠️ Area 5: Reports & Dashboards

**Screens:** `reports-list.html`, `report-designer.html`, `reports-designer.html` (duplicate!), `dashboard-designer.html`, `dashboards-list.html`, `sample-reports-dashboards.html`

**Backend available:** report definitions CRUD, preview, execute, export, schedules, templates; dashboard CRUD, widgets, sharing, snapshots, cloning.

| Screen | Status | Gap |
|---|---|---|
| Reports list | Exists | Schedule management is separate from definition — user must navigate away |
| Report designer | Exists | Export (`POST /execute/export`) has no UI trigger |
| Dashboard designer | Exists | Share (`POST /shares`) and Snapshot (`POST /snapshots`) have no UI |
| **Duplicate routes** | `reports-designer.html` AND `report-designer.html` exist | **Dead code / route confusion** — two templates for same feature |

**Recommendations:**
1. **CRITICAL** — Remove or redirect the duplicate `reports-designer.html` / `report-designer.html` routes. This is a UX defect that causes inconsistent navigation and dead-ends.
2. **HIGH** — Add **Export button** on Report Viewer (CSV/PDF). Backend `POST /execute/export` is ready. Export is the #1 feature request on every analytics tool.
3. **HIGH** — Add **Share** and **Snapshot** actions to Dashboard toolbar. Backend endpoints exist. Matches Metabase/Grafana pattern.
4. **MEDIUM** — Inline schedule management on the Report definition screen (not a separate navigator step).

---

### 🔴 Area 6: Page Builder

**Screens:** `builder.html`, `builder-pages.html`, `builder-showcase.html`

**Backend available:** page CRUD, publish, unpublish, version history, restore.

| Screen | Status | Gap |
|---|---|---|
| Builder canvas | Exists | **Version history** (`GET /{page_id}/versions`) has no UI — user cannot roll back |
| Builder pages list | Exists | Published vs draft state not visually distinguished |
| Showcase | Internal dev tool | Should not be in production navigation |

**Recommendations:**
1. **HIGH** — Add a **Version history sidebar** on the builder: list versions with timestamps, allow one-click restore. Backend has full version CRUD. Matches Webflow / Notion history panels.
2. **HIGH** — Visually distinguish **Published vs Draft** pages in the pages list (badge/colour). Currently all pages look the same.
3. **MEDIUM** — Hide `builder-showcase` from production menus (keep as `/builder-showcase` direct URL for internal use only).

---

### ⚠️ Area 7: Modules & Module Marketplace

**Screens:** `modules.html`, `settings/modules` (JS page), `nocode-modules.html`

**Backend available:** module lifecycle (install/enable/disable/uninstall), module store, tenant activation, manifest validation, dependency checks.

| Screen | Status | Gap |
|---|---|---|
| Settings/Modules | Exists (recently built) | Dependency graph is not visualised — user can't see why a module can't be deactivated |
| Modules list | Exists | No search/filter on the module store |
| NoCode Modules | Separate screen from main modules | **Confusing duplication** — two "modules" areas with different purposes |

**Recommendations:**
1. **HIGH** — Add a **dependency graph visualisation** when deactivation is blocked (`DEPENDENTS_ACTIVE`). Show which modules depend on the target. Currently the user gets a 409 error with no context.
2. **HIGH** — Unify or clearly label the two modules areas: "Platform Modules" (infra-level, admin) vs "NoCode Modules" (user-built, tenant-level). Navigation labels should not both say "Modules."
3. **MEDIUM** — Add search + category filter to the module store. Backend has `category` in manifests.

---

### ⚠️ Area 8: Audit Log

**Screen:** `audit.html`

**Backend available:** `POST /list` (filtered query), `GET /stats/summary`, `GET /{log_id}`.

| Screen | Status | Gap |
|---|---|---|
| Audit list | Exists | `/stats/summary` is not surfaced — no headline numbers |
| Audit detail | Not visible | Clicking a row should open `GET /{log_id}` detail panel — not implemented |

**Recommendations:**
1. **HIGH** — Add a **summary stats bar** at the top of the Audit screen: total events today, failures, top actors. Backend `GET /stats/summary` already returns this. Matches Datadog / Splunk pattern.
2. **MEDIUM** — Make audit rows clickable to open a detail panel with full `changes` diff (before/after JSON). Backend `GET /{log_id}` returns this; frontend ignores it.

---

### 🔴 Area 9: Scheduler & Settings

**Screens:** `scheduler.html`, `settings.html`, `settings-integration.html`, `settings-menu-sync.html`, `settings-notifications.html`, `settings-security.html`

**Backend available:** job CRUD, execute, configs, execution history + logs; tenant settings (PUT), user settings (PUT); notification settings (backend stub only — email not wired).

| Screen | Status | Gap |
|---|---|---|
| Scheduler | Exists | **Execution logs** (`GET /jobs/{id}/executions`, `GET /executions/{id}/logs`) have no UI |
| Settings → Notifications | Exists | Backend is a stub — user can toggle notifications but nothing actually sends |
| Settings → Integrations | Exists | Appears to be a static/placeholder page |
| Settings → Menu Sync | Internal tool | Should not be in end-user settings navigation |

**Recommendations:**
1. **HIGH** — Add **execution log viewer** on Scheduler: click a job → see run history with status, duration, log output. Backend has full log data. Essential for operators.
2. **HIGH** — Add a banner on Settings → Notifications: **"Email delivery not yet configured — notifications will appear in-app only."** Do not show toggles that imply email is working when it is not. This is a trust issue.
3. **MEDIUM** — Remove "Menu Sync" from end-user Settings navigation (move to superadmin area or internal tools).
4. **LOW** — Settings → Integrations needs actual integration cards (OAuth, webhooks, API keys). Currently a placeholder — either build it or hide it.

---

### ✅ Area 10: Internal / Dev Tools

**Screens:** `flex-layout-sandbox.html`, `components-showcase.html`, `datatable.html`, `builder-showcase.html`, `debug-financial-module.html`

These are development aids — no backend dependency. They should be **removed from production navigation** but kept as developer shortcuts (accessible via direct URL with a `?devtools` query param guard).

---

## Critical Gaps — Priority Matrix

| # | Gap | Impact | Effort | Priority |
|---|---|---|---|---|
| 1 | Forgot-password UI flow (screens missing) | **User lockout** | Low | 🔴 P0 |
| 2 | Notification banner (email not sent) | **User trust** | Low | 🔴 P0 |
| 3 | Duplicate report-designer routes | **Navigation broken** | Low | 🔴 P0 |
| 4 | Data Model publish button + migration preview | **Core feature hidden** | Medium | 🔴 P1 |
| 5 | Scheduler execution log viewer | **Operations blind** | Medium | 🔴 P1 |
| 6 | Automation test + history UI | **Developer experience** | Medium | 🔴 P1 |
| 7 | Password-strength live feedback on change-password | **Security UX** | Low | 🟡 P2 |
| 8 | Invite user dedicated flow | **Onboarding friction** | Medium | 🟡 P2 |
| 9 | Permission matrix table | **Admin efficiency** | Medium | 🟡 P2 |
| 10 | Report Export button | **Analyst workflow** | Low | 🟡 P2 |
| 11 | Builder version history sidebar | **Content safety** | Medium | 🟡 P2 |
| 12 | Dashboard Share + Snapshot | **Collaboration** | Low | 🟡 P2 |
| 13 | Audit stats bar + row detail | **Compliance UX** | Low | 🟡 P2 |
| 14 | Module dependency graph | **Deactivation clarity** | Medium | 🟠 P3 |
| 15 | Org-chart tree view | **Navigation** | Medium | 🟠 P3 |
| 16 | Dev-tool screens removed from nav | **Professionalism** | Low | 🟠 P3 |

---

## Screens With No Backend Coverage (Backend Gap → Not Frontend Issue)

| Screen | Missing Backend |
|---|---|
| `settings-notifications.html` | SMTP delivery not wired |
| `settings-integration.html` | No OAuth / API-key management router |
| Password reset (no screen) | Endpoints exist — frontend gap |
| Tenant health metrics | Derived query needed; no dedicated endpoint |

---

## Overall Verdict

**Backend maturity: ~85%.** The APIs are comprehensive and production-ready.
**Frontend maturity: ~55%.** Many backend capabilities are invisible or one-level too shallow.

The highest-ROI investment is **surfacing existing backend capability** with thin UI layers
(export button, log viewer, publish button, automation test panel) rather than building
new features. Three P0 items are regressions or trust issues that should ship in the
next sprint regardless of roadmap priority.
