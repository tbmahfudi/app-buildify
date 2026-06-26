---
artifact_id: arch-24
type: arch
producer: B1 Software Architect
consumers: [B3 UX Designer, C1 Tech Lead, C3 Frontend Developer]
upstream: [epic-24-frontend-capability-surfacing, arch-platform]
downstream: [tasks-24]
status: approved
created: 2026-06-26
updated: 2026-06-26
---

# Architecture - Epic 24: Frontend Capability Surfacing (arch-24)

---

## 1. Context

App-Buildify backend is approximately 85% feature-complete while the frontend exposes only 55% of it (per pm-review-frontend-screens-01). This epic closes the gap by wiring existing backend endpoints to new or improved frontend surfaces. No new backend code is required -- every story is a pure frontend change.

The following capability gaps are addressed:

| Feature | Gap |
|---|---|
| 24.1 P0 Trust and Navigation Fixes | Forgot-password flow dead-ends (reset endpoints exist, UI does not); notification settings misleads users; duplicate route causes broken navigation |
| 24.2 Auth and Password UX | No live password-strength feedback during reset or change flows |
| 24.3 Data Model Publish UX | publish and preview-migration endpoints exist but are unreachable from the entity editor |
| 24.4 Automation Visibility | Rule test endpoint and execution history endpoints exist but no UI panel exposes them |
| 24.5 Scheduler Log Viewer | Scheduler execution and log endpoints exist; job rows in the scheduler UI have no history affordance |
| 24.6 Builder Version History | Version list, detail, and restore endpoints exist; builder toolbar has no history button |
| 24.7 Dev Tool Cleanup | Dev-tool routes appear in production nav |

Platform constraint: the frontend is vanilla JS ES modules with no bundler, hash-based routing, and a Flex Component Library built on BaseComponent. All new UI work must follow this convention (arch-platform section 4).

P0 gate: Features 24.2 through 24.7 are blocked until Stories 24.1.1, 24.1.2, and 24.1.3 are marked DONE. C1 must enforce this sequencing in the sprint backlog.

---

## 2. Goals and Non-Goals

### Goals

- Surface every backend endpoint listed in epic-24 via a corresponding UI element.
- Add no new backend endpoints, schema migrations, or server-side logic.
- Reuse existing Flex Component Library primitives (FlexSplitPane, FlexDrawer, FlexModal, FlexTable, FlexProgress, etc.).
- Eliminate the duplicate #reports-designer route and remove dev-tool entries from production nav.
- Deliver password-strength-indicator.js as a reusable standalone module. The file already exists at frontend/assets/js/password-strength-indicator.js; C3 must verify it matches the Story 24.2.1 spec before implementation.

### Non-Goals

- SMTP email delivery wiring (separate epic).
- OAuth or API-key integrations.
- New backend endpoints or database migrations.
- Full designer-grade UIs for automation builder or workflow simulator (deferred; epic-24 ships thin MVP panels only).
- Permission matrix redesign, org-chart tree, module dependency graph, dashboard share/snapshot, report export.

---

## 3. Architecture Decisions

### 3.1 Feature 24.1 - P0: Trust and Navigation Fixes

#### 24.1.1 - Forgot-password UI flow

Backend endpoints confirmed in backend/app/routers/auth.py:

- POST /api/v1/auth/reset-password-request (line 687) - accepts {email}; returns 200 regardless of whether email exists (user-enumeration safe, confirmed at source).
- POST /api/v1/auth/reset-password-confirm (line 785) - accepts {token, new_password}.
- GET /api/v1/auth/password-policy (line 296) - used by the password-strength indicator in the confirm view.

Frontend decision: extend login.html with two additional view states (request-view and confirm-view) driven by the hash fragment. Route #reset-password maps to login.html in request-view mode. Route #reset-password-confirm maps to login.html in confirm-view mode, reading the token from the hash query string. No new HTML template file is required; view-content is swapped in-place within login.html.

No conflict with Epic 23 routes.

Security note on token in hash: after reading the reset token from window.location.hash, C3 must call history.replaceState immediately to remove the token from browser history. Document in impl-notes.

#### 24.1.2 - Notification settings honesty banner

Static FlexAlert(type=warning, persistent) prepended to settings-notifications.html content. No new routes or JS logic. settings-notifications.js receives a one-line prepend on render.

#### 24.1.3 - Duplicate report-designer route cleanup

- Delete: frontend/assets/templates/reports-designer.html
- Canonical route: #report-designer
- Add redirect guard in app.js loadRoute(): if route is reports-designer, redirect hash to report-designer and return early.
- Audit all sidebar/menu href values for #reports-designer and #reports/designer; rewrite to #report-designer.

### 3.2 Feature 24.2 - Auth and Password UX

#### 24.2.1 - Live password-strength feedback

Backend endpoint confirmed: GET /api/v1/auth/password-policy (auth.py line 296). Returns {min_length, max_length, require_uppercase, require_lowercase, require_digit, require_special_char, min_unique_chars}.

Decision: password-strength-indicator.js is a standalone JS module, not a Flex component, because it couples tightly to a single input element and a submit button. It is not registered in assets/js/components/index.js.

Public API for C3: passwordStrengthIndicator.attach(inputEl, submitBtn)

- Fetches /auth/password-policy once on first attach; caches result in module-scope variable for the session lifetime.
- Disables submitBtn until all active policy rules pass.
- Fail-open: if policy fetch fails, component is not rendered and submitBtn remains enabled.

Attachment points:

1. settings-security.js - New password field in the Change Password form
2. login-page.js confirm-reset view - New password field

### 3.3 Feature 24.3 - Data Model Publish UX

Backend endpoints confirmed in backend/app/routers/data_model.py:

- GET /api/v1/data-model/entities/{entity_id}/preview-migration (line 359)
- POST /api/v1/data-model/entities/{entity_id}/publish (line 411)

Frontend decision: extend nocode-data-model.js and nocode-data-model.html to add a FlexToolbar row above the entity field editor containing a status-badge (FlexBadge), a Preview changes button, and a Publish button. On either button click, fetch the migration diff, then open a FlexModal(size=lg) containing the diff tables. Publish now inside the modal calls POST /publish; on success, update entity.status in local page state without a full page reload.

No new route required. This is an enhancement to the existing #nocode-data-model route.

### 3.4 Feature 24.4 - Automation Visibility

Backend endpoints confirmed in backend/app/routers/automations.py:

- POST /api/v1/automations/rules/{rule_id}/test (line 103)
- GET /api/v1/automations/executions (line 129) - filterable by rule_id and status
- GET /api/v1/automations/executions/{execution_id} (line 142)

Story 24.4.1 - Rule test panel: inline FlexAccordion added below the condition builder section in nocode-automations.js. No new route or template file.

Story 24.4.2 - Execution history: the existing #nocode-automations route gains a third tab Execution History via FlexTabs. Tab activation triggers GET /automations/executions. A right-side FlexDrawer opens on row click and loads execution detail.

FlexDatepicker dependency: the spec references FlexDatepicker(range) for the date-range filter. C3 must verify this component is exported from components/index.js before implementing. If absent, a pair of FlexInput(type=date) fields is an acceptable MVP fallback; flag to B3.

### 3.5 Feature 24.5 - Scheduler Log Viewer

Backend endpoints confirmed in backend/app/routers/scheduler.py:

- GET /api/v1/scheduler/jobs/{job_id}/executions (line 442)
- GET /api/v1/scheduler/executions/{execution_id} (line 489)
- GET /api/v1/scheduler/executions/{execution_id}/logs (line 517)

FlexSplitPane verification: FlexSplitPane exists and is confirmed ready for Story 24.5.1. It ships at two paths:

- frontend/assets/js/layout/flex-split-pane.js - canonical implementation, extends BaseComponent
- frontend/assets/js/components/flex-split-pane.js - re-export

The component supports direction vertical, drag-resizable panes, and initial size via panes[].size. This resolves the open question in the A-to-B Gate Note. C3 imports from ../layout/flex-split-pane.js. No B3 escalation required for this component.

Usage sketch for Story 24.5.1:

    import FlexSplitPane from "../layout/flex-split-pane.js";
    const split = new FlexSplitPane(drawerBodyEl, {
      direction: "vertical",
      panes: [
        { id: "executions", content: executionsTableEl, size: "40%", minSize: "120px" },
        { id: "log",        content: logPreEl,          size: "60%", minSize: "80px"  }
      ]
    });

Frontend decision: scheduler.js gains a Job History FlexDrawer positioned right, size large. The drawer body uses a vertical FlexSplitPane. The drawer holds execution context (currentJobId) in a module-scope variable set on row button click.

### 3.6 Feature 24.6 - Builder Version History

Backend endpoints confirmed in backend/app/routers/builder_pages.py:

- GET /api/v1/builder-pages/{page_id}/versions (line 340)
- GET /api/v1/builder-pages/{page_id}/versions/{version_number} (line 372)
- POST /api/v1/builder-pages/{page_id}/restore/{version_number} (line 409)

Pre-existing file: frontend/assets/js/builder-version-history.js already exists. C3 must review its contents before writing new code. If it partially implements Story 24.6.1, extend it; if incompatible, supersede and delete it in this story.

Frontend decision: builder.js gains a History ghost button in the toolbar right cluster. Clicking opens a right-side FlexDrawer(size=sm). A version preview opens in FlexModal(size=xl) with the existing canvas renderer set to pointer-events: none. Inline restore confirmation replaces the action row in the drawer; no second modal required.

### 3.7 Feature 24.7 - Dev Tool Cleanup

Changes:

1. Remove routes flex-layout-sandbox, builder-showcase, components-showcase, datatable, debug-financial-module from all menu/nav config arrays in app.js and any static nav arrays.
2. Add a dev-banner guard in app.js loadRoute() for the same five routes (defensive, for developer environments that navigate to them directly via URL bar).
3. Verify and delete frontend/debug-financial-module.html if unreferenced.

No new components or routes.

---

## 4. Frontend Architecture

### 4.1 Routing

All routes in epic-24 use the existing hash-based router (assets/js/router.js). New and changed routes:

| Hash | Template | Handler | Change type |
|---|---|---|---|
| #reset-password | login.html | login-page.js | New (view-mode switch) |
| #reset-password-confirm | login.html | login-page.js | New (view-mode switch) |
| #report-designer | report-designer.html | report-designer-page.js | Canonical (unchanged) |
| #reports-designer | -- | app.js redirect | New redirect; template deleted |
| #nocode-data-model | nocode-data-model.html | nocode-data-model.js | Enhanced |
| #nocode-automations | nocode-automations.html | nocode-automations.js | Enhanced |
| #scheduler | scheduler.html | scheduler.js | Enhanced |
| #builder | builder.html | builder.js | Enhanced |

No route conflicts with Epic 23. Epic 23 routes are module-lifecycle specific.

### 4.2 JS Module Structure

Files to create or verify:

    frontend/assets/js/password-strength-indicator.js  (exists -- verify against Story 24.2.1 spec)

Files to modify:

    frontend/assets/js/app.js                    -- redirect guard; dev-route banner; DEV_ROUTES list
    frontend/assets/js/login-page.js             -- forgot-password request/confirm views; token cleanup
    frontend/assets/js/settings-notifications.js -- prepend honesty banner on render
    frontend/assets/js/nocode-data-model.js      -- publish toolbar + migration diff modal
    frontend/assets/js/nocode-automations.js     -- test panel accordion + execution history tab + drawer
    frontend/assets/js/scheduler.js              -- history drawer + FlexSplitPane log viewer
    frontend/assets/js/builder.js                -- version history toolbar button + drawer + preview modal
    frontend/assets/js/router.js                 -- two new route entries

Files to delete:

    frontend/assets/templates/reports-designer.html
    frontend/debug-financial-module.html  (if unreferenced -- verify first)

### 4.3 Reuse of Existing Flex Components

| Component | Stories | Source path |
|---|---|---|
| FlexSplitPane | 24.5.1 | frontend/assets/js/layout/flex-split-pane.js (confirmed) |
| FlexDrawer | 24.4.2, 24.5.1, 24.6.1 | Flex library -- verify in components/index.js |
| FlexModal | 24.3.1, 24.6.1 | Flex library |
| FlexAccordion | 24.4.1 | Flex library -- verify exists; fallback: details element |
| FlexTabs | 24.4.2 | Flex library -- verify exists; fallback: plain div tab strip |
| FlexDatepicker | 24.4.2 | Flex library -- verify exists; fallback: FlexInput(type=date) pair |
| FlexTable | 24.4.2, 24.5.1 | frontend/assets/js/components/ |
| FlexProgress | 24.2.1, 24.3.1 | Flex library |
| FlexAlert | 24.1.2, 24.2.1, 24.3.1, 24.4.1, 24.4.2, 24.5.1, 24.6.1 | Flex library |
| FlexBadge | 24.3.1, 24.4.2, 24.5.1, 24.6.1 | Flex library |
| FlexStack | most stories | frontend/assets/js/layout/flex-stack.js (confirmed) |
| FlexToolbar | 24.3.1, 24.6.1 | frontend/assets/js/layout/flex-toolbar.js (confirmed) |
| FlexCluster | 24.4.2, 24.6.1 | frontend/assets/js/layout/flex-cluster.js (confirmed) |
| FlexInput | 24.1.1, 24.2.1 | frontend/assets/js/components/ |
| FlexButton | all interactive stories | frontend/assets/js/components/ |

C3 action before picking up any P1 story: run the following check and flag missing components to B3:

    grep -r "FlexAccordion|FlexTabs|FlexDatepicker|FlexDrawer" frontend/assets/js/components/index.js

### 4.4 State Management

Epic-24 adds no global state store. Per-feature state lives in module-scope variables:

- login-page.js: resetToken (parsed from hash, cleared from URL immediately); passwordPolicy (session cache)
- nocode-automations.js: last test-run results object; isStale boolean flag
- scheduler.js: currentJobId (which job history drawer is open)
- builder.js: currentVersionNumber (for inline restore confirmation)

---

## 5. Backend Impacts

No new endpoints, models, or migrations are required.

All endpoints referenced in epic-24 are confirmed to exist at the lines listed below. C1 and C3 should smoke-test each endpoint against the running stack before beginning implementation of the dependent story.

| Endpoint | Router file | Line | Story |
|---|---|---|---|
| POST /api/v1/auth/reset-password-request | auth.py | 687 | 24.1.1 |
| POST /api/v1/auth/reset-password-confirm | auth.py | 785 | 24.1.1 |
| GET /api/v1/auth/password-policy | auth.py | 296 | 24.1.1, 24.2.1 |
| GET /api/v1/data-model/entities/{id}/preview-migration | data_model.py | 359 | 24.3.1 |
| POST /api/v1/data-model/entities/{id}/publish | data_model.py | 411 | 24.3.1 |
| POST /api/v1/automations/rules/{rule_id}/test | automations.py | 103 | 24.4.1 |
| GET /api/v1/automations/executions | automations.py | 129 | 24.4.2 |
| GET /api/v1/automations/executions/{execution_id} | automations.py | 142 | 24.4.2 |
| GET /api/v1/scheduler/jobs/{job_id}/executions | scheduler.py | 442 | 24.5.1 |
| GET /api/v1/scheduler/executions/{execution_id}/logs | scheduler.py | 517 | 24.5.1 |
| GET /api/v1/builder-pages/{page_id}/versions | builder_pages.py | 340 | 24.6.1 |
| GET /api/v1/builder-pages/{page_id}/versions/{version_number} | builder_pages.py | 372 | 24.6.1 |
| POST /api/v1/builder-pages/{page_id}/restore/{version_number} | builder_pages.py | 409 | 24.6.1 |

Potential backend gap: GET /automations/executions at automations.py line 129 must support from/to date query parameters for the date-range filter in Story 24.4.2. C3 should verify this before implementation. If the parameters are absent, a client-side filter on the response array is an acceptable MVP fallback.

---

## 6. FlexSplitPane Verification

Gate Note claim: "The FlexSplitPane component used in Story 24.5.1 is referenced but not confirmed in LAYOUT_CONVENTION.md. B1 should verify it exists or flag to B3 for resolution before C3 picks up that story."

Verification result: FlexSplitPane exists and is ready for use in Story 24.5.1.

Confirmed paths:

- frontend/assets/js/layout/flex-split-pane.js - canonical implementation (extends BaseComponent)
- frontend/assets/js/components/flex-split-pane.js - components re-export

The component supports horizontal and vertical splits, drag-resizable panes with min-size constraints, keyboard navigation, and size persistence. The direction vertical option (executions-pane over log-pane) and panes[].size percentage values work as specified in the epic. This component was delivered as part of the Flex layout suite referenced in arch-platform section 9 risk 11.

No B3 escalation required for this component.

---

## 7. NFRs

| Category | Requirement | How met |
|---|---|---|
| Bundle size | No increase in page-load JS budget; no new CDN dependencies | All new code is vanilla JS modules; zero new third-party libraries introduced |
| Accessibility | Interactive components (modals, drawers, accordions) must trap focus and support keyboard dismiss; ARIA roles required | C3 must verify FlexModal and FlexDrawer set aria-modal, manage focus on open/close, and handle Esc; flag gaps to B3 |
| Performance | Expensive API calls (migration diff, execution logs) deferred to user-triggered interactions; no prefetch on page load | Password policy cached in module scope for session lifetime; migration diff and log lines fetched on-demand per user action |
| Security | Reset token must not persist in browser history; user-enumeration safe on reset-password-request | history.replaceState immediately after reading token from hash (section 3.1); reset-password-request returns 200 regardless of email existence (confirmed auth.py line 687) |
| Multi-tenancy | All new API calls go through apiFetch which injects X-Tenant-Id from localStorage | No new auth or tenant plumbing needed; api.js handles this globally |
| Observability | No new metrics surfaces required; existing audit log captures publish, restore, and execution events | create_audit_log() called in backend service layer for data-model publish and builder page restore |
| Scalability | Execution history tables paginated server-side; log output is per-run not streamed | FlexPagination page size 25 for execution history; scheduler logs fetched per execution_id only |
| i18n | All new UI strings must have keys in at minimum assets/i18n/en/pages.json | C3 adds English keys; other language files deferred; no string literals in JS render functions |

---

## 8. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| FlexAccordion, FlexTabs, FlexDrawer, or FlexDatepicker not yet implemented in the Flex library | Medium -- audit-15 noted incomplete layout suite; FlexSplitPane confirmed shipped but others unverified | C3 runs grep check (section 4.3) before picking up P1 stories; missing components use documented fallbacks; B3 UX approves fallbacks before C3 implements |
| password-strength-indicator.js exists but does not match Story 24.2.1 spec | Low -- file confirmed at frontend/assets/js/password-strength-indicator.js | C3 reads the file first; extends rather than replaces if partial; full rewrite only if fundamentally incompatible |
| builder-version-history.js partially implements 24.6.1 in an incompatible way | Low | C3 reviews file before implementing; supersede and delete if incompatible |
| Reset token exposed in browser history via hash fragment | Medium | history.replaceState immediately after token read; documented in impl-notes |
| GET /automations/executions does not support from/to date query parameters | Low | C3 checks automations.py list endpoint signature; client-side filter is acceptable MVP fallback if params absent |
| P1 stories started before P0 gate is cleared | Low (process risk) | C1 Tech Lead blocks P1 stories in sprint backlog until 24.1.1, 24.1.2, and 24.1.3 are DONE |

---

## 9. Reference Map

| Concern | File |
|---|---|
| Auth endpoints (reset, policy) | backend/app/routers/auth.py lines 296, 687, 785 |
| Data model endpoints (publish, preview) | backend/app/routers/data_model.py lines 359, 411 |
| Automation endpoints (test, executions) | backend/app/routers/automations.py lines 103, 129, 142 |
| Scheduler endpoints (executions, logs) | backend/app/routers/scheduler.py lines 442, 489, 517 |
| Builder page version endpoints | backend/app/routers/builder_pages.py lines 340, 372, 409 |
| FlexSplitPane canonical | frontend/assets/js/layout/flex-split-pane.js |
| FlexSplitPane re-export | frontend/assets/js/components/flex-split-pane.js |
| Flex component re-exports | frontend/assets/js/components/index.js |
| Hash router | frontend/assets/js/router.js |
| App bootstrap and loadRoute | frontend/assets/js/app.js |
| API fetch client | frontend/assets/js/api.js |
| Login page handler | frontend/assets/js/login-page.js |
| Password strength indicator | frontend/assets/js/password-strength-indicator.js |
| Notifications settings handler | frontend/assets/js/settings-notifications.js |
| Data model page handler | frontend/assets/js/nocode-data-model.js |
| Automations page handler | frontend/assets/js/nocode-automations.js |
| Scheduler page handler | frontend/assets/js/scheduler.js |
| Builder page handler | frontend/assets/js/builder.js |
| Builder version history pre-existing | frontend/assets/js/builder-version-history.js |
| Platform architecture | plan/architecture/arch-platform.md |
| Epic | plan/epics/epic-24-frontend-capability-surfacing.md |
