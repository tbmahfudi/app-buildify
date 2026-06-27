---
artifact_id: test-plan-24
type: test-plan
producer: D1 QA Engineer
consumers: [C1 Tech Lead, A3 Product Owner, E2 Technical Writer]
upstream: [epic-24-frontend-capability-surfacing, arch-24, uildc-24, tasks-24]
downstream: [test-report-24]
status: approved
created: 2026-06-27
updated: 2026-06-27
---

# Test Plan -- Epic 24: Frontend Capability Surfacing

> **Format**: structured test plan covering automated integration coverage (endpoint
> contract guards, executed against SQLite in-memory via conftest) and the manual
> browser runbook required for the frontend-heavy stories of Epic 24. Each scenario
> maps to a story AC from epic-24-frontend-capability-surfacing.md. Epic 24 ships
> **zero backend changes** -- all backend endpoints are pre-existing (arch-24 section 5),
> so automated coverage is contract-level (auth guard, request shape, no-5xx, filter
> acceptance). The bulk of Epic 24 value is in new frontend surfaces, which are verified
> through the manual runbook (S2--S6) and smoke_checklist_24.md.

---

## 1. Scope

### In scope

| Story | Feature | D1 task | Coverage type |
|-------|---------|---------|---------------|
| 24.2.1 | Password strength UX -- meter, rule icons, fail-open, history.replaceState token clear | T-24.011 | Integration (contract) + manual (browser) |
| 24.3.1 | Data model publish UX -- toolbar, diff modal, drag-reorder, empty state, keyboard reorder | T-24.015 | Integration (contract) + manual (browser) |
| 24.4.1 / 24.4.2 | Automation rule test panel, execution history tab, date filter, detail drawer | T-24.021 | Integration (contract) + manual (browser) |
| 24.5.1 | Scheduler job-execution log viewer -- drawer, split pane, colour-coded log lines | T-24.024 | Integration (contract) + manual (browser) |
| 24.6.1 | Builder version history -- drawer, preview modal, inline restore confirmation | T-24.029 | Integration (contract) + manual (browser) |
| 24.7.1 | Dev tool cleanup -- removed routes, dev-banner guard | T-24.031 (DONE) | Manual (browser) |

### Out of scope

- Backend endpoint logic (no backend changes in Epic 24; endpoints verified live in T-24.001)
- SMTP / email delivery of reset links (explicitly out of epic scope)
- Branded HTML email template (plain-text MVP; deferred to E2 Tech Writer)
- Mobile-responsive layouts (desktop-first per uildc-24 section 6)
- D3.js dependency-graph visualisation (deferred per uildc-24)
- D3 Security Engineer sec-review-24 (commissioned separately; reset-token flow + builder restore are review targets)
- Performance / load testing

---

## 2. Test Environments

| Environment | Purpose | Notes |
|-------------|---------|-------|
| SQLite in-memory (pytest conftest `db_session` / `client` / `auth_headers`) | Integration contract tests -- fast, isolated, no Docker | Used by `test_epic24_auth_password.py`, `test_epic24_data_model.py`, `test_epic24_automations.py`, `test_epic24_scheduler.py`, `test_epic24_builder.py` |
| Dev stack (Docker Compose) | Manual browser runbook + live endpoint smoke | `docker compose up`; frontend at app_buildify_frontend, backend at app_buildify_backend, MailHog at app_buildify_mailhog for reset-link capture |

> **KNOWN COLLECTION BLOCKER (DEF-24-A):** at time of writing, `app.main` fails to import
> in both the venv and the backend container due to **pre-existing, uncommitted** changes
> outside Epic 24 frontend scope:
> 1. `app/routers/modules.py:989` references `TenantDBStatusResponse` without importing it
>    from `app.schemas.module` (T-22 ModuleDBProvisioner work).
> 2. `app/core/tenant/module_db_provisioner.py:37` raises `IndexError` from
>    `Path(__file__).resolve().parents[5]`.
>
> Both are in T-22 backend code, **not** in any Epic 24 frontend artifact. All five
> `test_epic24_*.py` files pass `py_compile` and are written against stable conftest
> fixtures; they will collect and run green once the T-22 import regression is resolved.
> Flagged to C2/E1 for the import fix. Epic 24 integration tests must be re-run to green
> as the gate before test-report-24 is signed.

---

## 3. Story 24.2.1 -- Password Strength UX (T-24.011)

### Automated (integration) -- `test_epic24_auth_password.py`

| TC | Class / focus | Asserts |
|----|---------------|---------|
| TC-24-001 | `TestPasswordPolicy` | `GET /auth/password-policy` is public (200 no auth); response has min_length, require_* fields; min_length is positive int; flags are bools; tenant_id param accepted |
| TC-24-002 | `TestResetPasswordRequest` | `POST /auth/reset-password-request` returns 200 for both known and unknown emails; **identical message body** (user-enumeration safety); missing email -> 422 |
| TC-24-003 | `TestResetPasswordConfirm` | invalid token -> 4xx (never 200); missing token/new_password -> 422; empty password rejected |

### Manual (browser runbook)

#### TC-24-M01 Strength meter in forgot-password confirm view (T-24.007)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Trigger reset request, capture link from MailHog, open `#reset-password-confirm` with the token in the hash | Confirm view renders; new-password field present |
| 2 | Inspect `window.location.hash` immediately after load | Token **removed** from hash and from browser history (history.replaceState fired -- arch-24 section 3.1) |
| 3 | Type a weak password ("abc") | FlexProgress bar red; failing rules show ph-x-circle / ph-circle with red colour class; submit disabled |
| 4 | Type a strong password meeting all policy rules | Each rule shows ph-check-circle green; bar progresses red->amber->yellow->green; submit enabled |
| 5 | Inspect each rule list item | `aria-label="{rule}: {passed|not met}"` present (uildc-24 section 5.2) |

#### TC-24-M02 Strength meter in Change Password settings (T-24.010)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open Settings -> Security -> Change Password | New-password field has strength indicator attached |
| 2 | Type partial/complete passwords | Rule icons + bar update live; submit button gated until all rules pass |

#### TC-24-M03 Fail-open on policy fetch failure

| Step | Action | Expected |
|------|--------|----------|
| 1 | Block `GET /auth/password-policy` (devtools network throttle/block) and load a page with the indicator | Indicator **fails open**: field stays usable, submit not permanently blocked, no JS crash |

#### TC-24-M04 Expired / missing token

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open `#reset-password-confirm` with no token | FlexAlert(error) "Reset link has expired" + "Request new link"; password fields hidden (uildc-24 2.1.1 Gap B) |

---

## 4. Story 24.3.1 -- Data Model Publish UX (T-24.015)

### Automated (integration) -- `test_epic24_data_model.py`

| TC | Class / focus | Asserts |
|----|---------------|---------|
| TC-24-004 | `TestPreviewMigrationEndpoint` | `GET /data-model/entities/{id}/preview-migration` requires auth; non-existent id -> 400/404 (never 5xx) |
| TC-24-005 | `TestPublishEntityEndpoint` | `POST .../publish` requires auth; non-existent id -> 400/404; missing body -> <500 |

### Manual (browser runbook)

| TC | Action | Expected |
|----|--------|----------|
| TC-24-M05 | Open an entity with pending changes; click "Preview changes" | FlexModal(lg) shows diff: fields-to-add green table, fields-to-remove red table |
| TC-24-M06 | Inspect destructive (remove) field rows | `border-l-4 border-red-500` + ph-warning icon in field-name cell (uildc-24 2.3.2) |
| TC-24-M07 | Click "Publish now" | Spinner overlay (aria-live="assertive"); on success status badge updates **without full reload**; success FlexNotification toast |
| TC-24-M08 | Modal a11y | role=dialog, aria-modal=true, aria-labelledby set; Escape closes unless publish in-flight |
| TC-24-M09 | Drag a field via ph-dots-six-vertical handle | dragstart opacity+ring; dragover border-t indicator; drop reorders array, re-renders, entity marked dirty |
| TC-24-M10 | Keyboard reorder: focus field, Alt+ArrowUp / Alt+ArrowDown | Field moves; aria-live="polite" announces "Field {name} moved to position {n} of {total}" |
| TC-24-M11 | Open an entity with no fields | Empty state: ph-table icon + "No fields yet" + "Add first field" primary button (uildc-24 2.3.1) |

---

## 5. Stories 24.4.1 / 24.4.2 -- Automation Visibility (T-24.021)

### Automated (integration) -- `test_epic24_automations.py`

| TC | Class / focus | Asserts |
|----|---------------|---------|
| TC-24-006 | `TestAutomationRuleTest` | `POST /automations/rules/{id}/test` requires auth; non-existent -> 400/404; empty payload accepted (not 422) |
| TC-24-007 | `TestAutomationExecutionsList` | `GET /automations/executions` requires auth; 200 + JSON array when authed; rule_id/status filters accepted; from/to date params never 5xx (documents T-24.017 verdict) |
| TC-24-008 | `TestAutomationExecutionDetail` | `GET /automations/executions/{id}` requires auth; non-existent -> 404 |

### Manual (browser runbook)

| TC | Action | Expected |
|----|--------|----------|
| TC-24-M12 | Expand Rule Test Panel, click "Run test" with valid rule | Spinner -> success FlexAlert with result |
| TC-24-M13 | Run test on a failing rule | Error FlexAlert with message |
| TC-24-M14 | Run test, then edit the rule | Stale banner appears with **role=alert** (primary signal); prior results opacity-60 (supplementary) (uildc-24 2.4.1) |
| TC-24-M15 | Before any run | ph-funnel empty state "No test run yet" |
| TC-24-M16 | Open Execution History tab | Fetches `?rule_id=`; FlexTable Started/Status/Duration/Trigger; Status FlexBadge has `aria-label="Status: {value}"`; pagination page size 25; ph-clock empty state |
| TC-24-M17 | Apply date-range + status filter | Results narrow (query param or client-side per T-24.017 verdict) |
| TC-24-M18 | Click a history row | Execution Detail FlexDrawer (right) opens; trigger payload + result JSON + error shown; Escape closes; focus trapped; aria-modal set |
| TC-24-M19 | Keyboard nav on rows | Rows tabindex=0; Enter opens drawer; ArrowUp/ArrowDown navigate |

---

## 6. Story 24.5.1 -- Scheduler Log Viewer (T-24.024)

### Automated (integration) -- `test_epic24_scheduler.py`

| TC | Class / focus | Asserts |
|----|---------------|---------|
| TC-24-009 | `TestSchedulerJobExecutions` | `GET /scheduler/jobs/{id}/executions` requires auth; non-existent -> 403/404 (never 5xx); status filter accepted; documents items/total shape |
| TC-24-010 | `TestSchedulerExecutionLogs` | `GET /scheduler/executions/{id}/logs` requires auth; non-existent -> 403/404; log_level filter accepted |

### Manual (browser runbook)

| TC | Action | Expected |
|----|--------|----------|
| TC-24-M20 | Click "History" (ph-clock-clockwise) on a job row | Job History FlexDrawer (right, lg) opens for **correct** currentJobId; FlexTable Started/Status/Duration; ph-clock empty state |
| TC-24-M21 | Click an execution row | Log pane below populates from `/executions/{id}/logs` |
| TC-24-M22 | Inspect log lines | ERROR/CRITICAL -> text-red-400; WARN/WARNING -> text-yellow-400; others -> text-green-400; each line in own `<span>`; `<pre role="log" aria-live="polite">` (uildc-24 2.5) |
| TC-24-M23 | Drawer a11y | Escape closes; focus trapped; aria-modal set |
| TC-24-M24 | Verify implementation | `FlexSplitPane(direction=vertical)` **absent**; split achieved via FlexStack + CSS resize handle (uildc-24 1.3) |

---

## 7. Story 24.6.1 -- Builder Version History (T-24.029)

### Automated (integration) -- `test_epic24_builder.py`

| TC | Class / focus | Asserts |
|----|---------------|---------|
| TC-24-011 | `TestBuilderVersionList` | `GET /builder-pages/{id}/versions` requires auth; non-existent -> 403/404; list when found |
| TC-24-012 | `TestBuilderVersionDetail` | `GET .../versions/{n}` requires auth; non-existent -> 403/404; non-integer version -> 422 |
| TC-24-013 | `TestBuilderRestore` | `POST .../restore/{n}` requires auth; non-existent -> 400/403/404 (never 5xx); non-integer version -> 422 |

### Manual (browser runbook)

| TC | Action | Expected |
|----|--------|----------|
| TC-24-M25 | Click "History" ghost button (ph-clock-clockwise) in builder toolbar | Version History FlexDrawer (right, sm 320px) opens |
| TC-24-M26 | Inspect version list | `<ul role="list">`; each item `aria-label="Version {N}, saved {relative time} by {author}"`; ph-files empty state "No versions saved yet" |
| TC-24-M27 | Click ph-eye "Preview" on a version | FlexModal(xl) opens; canvas renderer has `pointer-events: none`; role=dialog, aria-modal=true, aria-labelledby->h2; Escape closes |
| TC-24-M28 | Click ph-arrow-counter-clockwise "Restore" | Inline confirm row replaces action row (no second modal); **all other** Restore buttons disabled + opacity-50 (uildc-24 2.6); focus moves to "Yes, restore" |
| TC-24-M29 | Click "Cancel" on confirm | Returns focus to the triggering Restore button |
| TC-24-M30 | Click "Yes, restore" | `POST .../restore/{n}`; success toast; builder canvas reloads; currentVersionNumber stored |

---

## 8. Story 24.7.1 -- Dev Tool Cleanup (T-24.031, DONE)

| TC | Action | Expected |
|----|--------|----------|
| TC-24-M31 | Inspect production nav arrays | `flex-layout-sandbox`, `builder-showcase`, `components-showcase`, `datatable`, `debug-financial-module` absent |
| TC-24-M32 | Direct-URL navigate to each removed route | Dev-banner guard shows informational banner, **not** a broken page (arch-24 3.7) |
| TC-24-M33 | Load app, check console | No JS errors after deletions |

---

## 9. Traceability

| D1 Task | Story | Automated file | Manual TCs |
|---------|-------|----------------|-----------|
| T-24.011 | 24.2.1 | test_epic24_auth_password.py | M01-M04 |
| T-24.015 | 24.3.1 | test_epic24_data_model.py | M05-M11 |
| T-24.021 | 24.4.1/24.4.2 | test_epic24_automations.py | M12-M19 |
| T-24.024 | 24.5.1 | test_epic24_scheduler.py | M20-M24 |
| T-24.029 | 24.6.1 | test_epic24_builder.py | M25-M30 |
| T-24.031 | 24.7.1 | (manual only) | M31-M33 |

---

## 10. Exit Criteria

1. All five `test_epic24_*.py` modules collect and pass (gated on DEF-24-A import fix).
2. smoke_checklist_24.md fully checked on a live dev stack by D1 before sign-off.
3. Security-sensitive items independently confirmed: history.replaceState token clear (TC-24-M01 step 2) and concurrent-restore prevention (TC-24-M28).
4. No regression in console (TC-24-M33).
5. Results recorded in test-report-24.md.
