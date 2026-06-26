---
artifact_id: tasks-24
type: tasks
producer: C1 Tech Lead
consumers: [C2 Backend Developer, C3 Frontend Developer, D1 QA Engineer, E1 DevOps Engineer]
upstream: [epic-24-frontend-capability-surfacing, arch-24, uildc-24]
downstream: []
status: approved
created: 2026-06-26
updated: 2026-06-26
sprint:
  goal: Surface the 45% of backend capability that is invisible to users -- shipping the forgot-password flow, notification honesty banner, data-model publish UX, automation test/history panels, scheduler log viewer, and builder version history in a single pure-frontend sprint
  length_days: 10
  capacity_assumption: 1 FE + 0.25 BE + 0.25 QA + 0.1 DevOps approx 128 dev-hours
decisions:
  - P0 gate (T-24.001 through T-24.008) must be DONE before any P1 story begins -- mirrors arch-24 section 1 gate requirement
  - T-24.002 (component grep check) runs at sprint start and is a hard blocker on all stories that use FlexAccordion, FlexTabs, FlexDatepicker, or FlexDrawer
  - T-24.003 (password-strength-indicator.js review) gates T-24.009 -- extend or rewrite based on compatibility verdict
  - T-24.004 (builder-version-history.js review) gates T-24.025 -- extend or supersede decision
  - FlexSplitPane(direction=vertical) must NOT be used in T-24.023 -- use FlexStack + CSS resize handle per uildc-24 section 1.3
  - Reset token must be cleared via history.replaceState immediately on page load (arch-24 section 3.1) -- document in impl-notes-T-24-007.md
  - GET /automations/executions date-range query-param support must be verified in T-24.017 before T-24.019 implements the filter -- client-side fallback acceptable per arch-24 section 5
open_questions:
  - Forgot-password email template: plain text or branded HTML? Recommend plain text for MVP -- escalate to E2 Tech Writer after sprint.
  - FlexAccordion / FlexTabs / FlexDatepicker / FlexDrawer absent from components/index.js? T-24.002 resolves this; missing components require B3 fallback approval before implementing affected stories.
  - FlexSplitPane direction=vertical option: not available in Epic 24 (uildc-24 section 1.3). Flag for Epic 25 backlog.
  - builder-version-history.js compatibility verdict (T-24.004): extend vs supersede; gates T-24.025.
  - GET /automations/executions from/to date params: confirm in T-24.017 before T-24.019; client-side filter fallback if absent.
---

# tasks-24 -- Sprint Backlog for Frontend Capability Surfacing

> **Upstream**: [`epic-24-frontend-capability-surfacing`](../epics/epic-24-frontend-capability-surfacing.md), [`arch-24`](../architecture/arch-24.md), [`uildc-24`](../architecture/uildc-24.md).

---

## Sprint Goal

Surface what the backend already does. Ship the forgot-password flow, notification honesty banner, duplicate-route cleanup, data-model publish/preview UX, automation rule test panel and execution history tab, scheduler job-execution log viewer, and builder version history panel -- all wiring existing backend endpoints to new or improved frontend surfaces, with zero backend changes.

## Capacity Plan

| Role | Headcount | Hours over 10-day sprint |
|------|----------:|------------------------:|
| C3 Frontend Developer | 1 | 80 |
| C2 Backend Developer | 0.25 | 20 |
| D1 QA Engineer | 0.25 | 20 |
| E1 DevOps Engineer | 0.1 | 8 |
| **Total** | -- | **128** |

Task estimates sum to ~79 hours net coding and QA time. Remaining capacity covers code review, integration testing, and discovery surprises. Sprint is achievable with a frontend-heavy team; C2 support is endpoint-verification only (arch-24 section 5 identifies no missing endpoints, but date-param support on /automations/executions must be confirmed in T-24.017).

---

## Task Table

Status legend: `OPEN` = not started | `IN-PROGRESS` = picked up | `BLOCKED` = waiting | `REVIEW` = PR open | `DONE` = merged.

---

### Sprint-Start Verification (Day 1 AM) -- run before any story work

> **T-24.001 through T-24.004 must be DONE before story implementation begins.** These four tasks take at most a half-day and resolve all component-availability and pre-existing-file decisions that would otherwise block mid-sprint.

| Task ID | Description | Owner | Depends on | Est (h) | Reference | Status |
|---------|-------------|-------|-----------|---------|-----------|--------|
| T-24.001 | Smoke-test all 13 backend endpoints listed in arch-24 section 5 against running dev stack; record HTTP status (200/404/500) in impl-notes-T-24-001.md | C2 | -- | 2 | arch-24 section 5 endpoint table | DONE |
| T-24.002 | Run `grep -r "FlexAccordion|FlexTabs|FlexDatepicker|FlexDrawer" frontend/assets/js/components/index.js`; record which are present and which are absent; flag absences to B3 for fallback approval; update impl-notes-T-24-002.md | C3 | -- | 1 | arch-24 section 4.3 C3 action | DONE |
| T-24.003 | Read `frontend/assets/js/password-strength-indicator.js`; verify it matches Story 24.2.1 spec (attach API, policy fetch, rule list, FlexProgress strength bar, fail-open behaviour); document extend vs rewrite verdict in impl-notes-T-24-003.md | C3 | -- | 1 | arch-24 section 3.2 pre-existing file | DONE |
| T-24.004 | Read `frontend/assets/js/builder-version-history.js`; verify partial vs incompatible status against Story 24.6.1 spec; document extend vs supersede verdict in impl-notes-T-24-004.md | C3 | T-24.002 | 1 | arch-24 section 3.6 pre-existing file | DONE |

**Subtotal: 5 hrs**

---

### Item 24.1 -- P0: Trust & Navigation Fixes (Stories 24.1.1, 24.1.2, 24.1.3) -- P0 GATE

> **P1 stories (Items 24.2 through 24.7) are BLOCKED until T-24.005 through T-24.008 are all DONE.**

| Task ID | Description | Owner | Depends on | Est (h) | Reference | Status |
|---------|-------------|-------|-----------|---------|-----------|--------|
| T-24.005 | Add routes `#reset-password` and `#reset-password-confirm` in `router.js`; both map to `login.html` + `login-page.js` with a mode discriminator; add redirect guard in `app.js loadRoute()` for legacy password-reset paths | C3 | T-24.001 | 2 | epic-24 section 24.1.1 routing | DONE |
| T-24.006 | Implement `login-page.js` request-reset view: FlexInput(email) form; submit calls `POST /auth/reset-password-request`; on success replace form with email-sent confirmation state (ph-envelope-open icon, "Check your inbox" heading, user-enumeration-safe body copy, "Back to sign in" link) per uildc-24 section 2.1.1 Gap A | C3 | T-24.005 | 3 | epic-24 section 24.1.1 request view | DONE |
| T-24.007 | Implement `login-page.js` confirm-reset view: read token from `window.location.hash`; call `history.replaceState` immediately to remove token from browser history (security -- arch-24 section 3.1; document in impl-notes-T-24-007.md); if token absent or expired show FlexAlert(type=error) "Reset link has expired" with "Request new link" FlexButton and hidden password fields per uildc-24 section 2.1.1 Gap B; new-password FlexInput calls `POST /auth/reset-password-confirm`; attach `passwordStrengthIndicator` to new-password field (T-24.003 verdict applies) | C3 | T-24.006, T-24.003 | 4 | epic-24 section 24.1.1 confirm view | DONE |
| T-24.008 | Prepend persistent `FlexAlert(type=warning)` to `settings-notifications.js` render path with ph-envelope-simple-slash icon and copy "Email notifications are not yet active -- configuration in progress."; delete `frontend/assets/templates/reports-designer.html`; add redirect `#reports-designer` -> `#report-designer` in `app.js loadRoute()`; audit all sidebar/menu hrefs for `#reports-designer` variants and rewrite to `#report-designer`; verify `frontend/debug-financial-module.html` is unreferenced then delete it | C3 | T-24.005 | 3 | epic-24 sections 24.1.2 and 24.1.3 | DONE |

**Subtotal: 12 hrs**

---

### Item 24.2 -- Auth & Password UX (Story 24.2.1)

> Requires T-24.003 verdict and P0 gate complete (T-24.008 DONE).

| Task ID | Description | Owner | Depends on | Est (h) | Reference | Status |
|---------|-------------|-------|-----------|---------|-----------|--------|
| T-24.009 | Extend or rewrite `password-strength-indicator.js` per T-24.003 verdict: confirm `attach(inputEl, submitBtn)` public API; policy fetch with session-scope cache; rule checklist with ph-circle/ph-x-circle/ph-check-circle icons and colour classes per uildc-24 section 2.2; FlexProgress strength bar with red/amber/yellow/green colour mapping; fail-open if policy fetch fails; each rule list item must have `aria-label="{rule}: {passed|not met}"` per uildc-24 section 5.2 | C3 | T-24.003, T-24.008 | 4 | epic-24 section 24.2.1 | OPEN |
| T-24.010 | Attach `passwordStrengthIndicator` to the Change Password new-password field in `settings-security.js`; verify submit button gating works end-to-end in dev browser | C3 | T-24.009 | 2 | epic-24 section 24.2.1 attachment points | OPEN |
| T-24.011 | QA: verify strength meter in forgot-password confirm view (T-24.007) and in Change Password settings (T-24.010); test fail-open by blocking /auth/password-policy; test all rule pass/fail icon states; verify history.replaceState clears token on page load | D1 | T-24.007, T-24.010 | 2 | epic-24 section 24.2.1 AC | OPEN |

**Subtotal: 8 hrs**

---

### Item 24.3 -- Data Model Publish UX (Story 24.3.1)

> Requires P0 gate complete (T-24.008 DONE).

| Task ID | Description | Owner | Depends on | Est (h) | Reference | Status |
|---------|-------------|-------|-----------|---------|-----------|--------|
| T-24.012 | Add FlexToolbar row above the entity field editor in `nocode-data-model.js`: FlexBadge entity status chip; "Preview changes" button (ph-eye); "Publish" button (ph-rocket-launch, disabled when entity clean); both buttons trigger migration diff fetch from `GET /data-model/entities/{id}/preview-migration` | C3 | T-24.008 | 3 | epic-24 section 24.3.1 toolbar | DONE |
| T-24.013 | Build migration diff FlexModal(size=lg) in `nocode-data-model.js`: fields-to-add table (text-green-600); fields-to-remove table (text-red-600 + border-l-4 border-red-500 + ph-warning icon in field name cell per uildc-24 section 2.3.2); FlexSpinner loading skeleton; "Publish now" button calls `POST /data-model/entities/{id}/publish`; on success update entity.status in local page state without full reload; FlexNotification success toast; role=dialog, aria-modal=true, aria-labelledby set; Escape closes unless publish in-flight; aria-live="assertive" on in-progress overlay | C3 | T-24.012 | 4 | epic-24 section 24.3.1 diff modal | OPEN |
| T-24.014 | Implement drag-reorder on entity field list in `nocode-data-model.js`: render fields as `<ul id="entity-fields-list">` with `<li draggable="true">`; drag handle button (ph-dots-six-vertical, aria-label="Drag to reorder {name}"); HTML5 DnD (dragstart opacity+ring, dragover border-t indicator, drop reorders array and re-renders); keyboard fallback Alt+ArrowUp/Down with aria-live="polite" announcement "Field {name} moved to position {n} of {total}"; empty state: ph-table icon + "No fields yet" + "Add first field" FlexButton(variant=primary) per uildc-24 section 2.3.1 | C3 | T-24.012 | 4 | epic-24 section 24.3.1 drag-reorder | OPEN |
| T-24.015 | QA: verify publish flow (toolbar -> diff modal -> "Publish now" -> status badge update without reload); verify destructive field rows show border-l-4 + ph-warning icon; verify drag-reorder persists field order in local state and marks entity dirty; verify empty state renders when entity has no fields; verify Alt+ArrowUp/Down keyboard reorder announces via aria-live | D1 | T-24.013, T-24.014 | 2 | epic-24 section 24.3.1 AC | OPEN |

**Subtotal: 13 hrs**

---

### Item 24.4 -- Automation Visibility (Stories 24.4.1, 24.4.2)

> Requires T-24.002 verdict (FlexAccordion, FlexTabs, FlexDatepicker, FlexDrawer availability) and P0 gate (T-24.008 DONE).

| Task ID | Description | Owner | Depends on | Est (h) | Reference | Status |
|---------|-------------|-------|-----------|---------|-----------|--------|
| T-24.016 | Add inline Rule Test Panel to `nocode-automations.js` as FlexAccordion (or `<details>` fallback if FlexAccordion absent per T-24.002) below the condition-builder section: "Run test" FlexButton (ph-play); optional sample-payload FlexInput(type=textarea); calls `POST /automations/rules/{rule_id}/test`; FlexSpinner while in-flight; success/error result as FlexAlert; ph-funnel empty state "No test run yet" before first run; when results are stale (rule edited after run) show role=alert FlexAlert stale banner + opacity-60 on prior results (uildc-24 section 2.4.1 -- opacity is supplementary, aria alert is primary) | C3 | T-24.002, T-24.008 | 4 | epic-24 section 24.4.1 | OPEN |
| T-24.017 | Verify `GET /automations/executions` (automations.py line 129) accepts `from` and `to` date query parameters; document result in impl-notes-T-24-017.md; if params absent, confirm client-side filter on response array is the approved MVP fallback per arch-24 section 5 | C2 | T-24.001 | 1 | arch-24 section 5 potential gap | OPEN |
| T-24.018 | Add Execution History third tab to `nocode-automations.js` via FlexTabs (or plain div tab-strip fallback per T-24.002); tab activation fetches `GET /automations/executions?rule_id={id}`; FlexTable columns: Started, Status (FlexBadge with aria-label="Status: {value}"), Duration, Trigger; FlexPagination page size 25; FlexSpinner loading; ph-clock empty state "No executions yet"; table rows keyboard-focusable (tabindex=0), Enter opens drawer, ArrowUp/ArrowDown navigates | C3 | T-24.002, T-24.016 | 3 | epic-24 section 24.4.2 history tab | OPEN |
| T-24.019 | Add date-range filter row above Execution History table: FlexDatepicker(range) if range mode confirmed, else two FlexDatepicker instances in FlexCluster(gap=xs) per uildc-24 section 2.4.2; FlexSelect(status) filter; filter values passed as query params or applied client-side per T-24.017 verdict | C3 | T-24.018, T-24.017 | 2 | epic-24 section 24.4.2 filters | OPEN |
| T-24.020 | Add Execution Detail FlexDrawer (position=right, size=lg, per T-24.002 result) in `nocode-automations.js`: opens on table row click; calls `GET /automations/executions/{execution_id}`; displays trigger payload, result JSON, error message; FlexBadge status chip; FlexSpinner; Escape closes; focus trapped; aria-modal set (uildc-24 section 5.1) | C3 | T-24.018, T-24.002 | 3 | epic-24 section 24.4.2 drawer | OPEN |
| T-24.021 | QA: verify rule test panel success and error cases; verify stale banner has role=alert when rule changes after test; verify execution history tab loads and paginates; verify date filter narrows results; verify execution detail drawer opens on row click and closes on Escape; verify keyboard row navigation (Enter/ArrowUp/ArrowDown) | D1 | T-24.016, T-24.019, T-24.020 | 2 | epic-24 section 24.4 AC | OPEN |

**Subtotal: 15 hrs**

---

### Item 24.5 -- Scheduler Log Viewer (Story 24.5.1)

> Requires T-24.002 verdict (FlexDrawer) and P0 gate (T-24.008 DONE). FlexSplitPane(direction=vertical) is NOT available -- use FlexStack + CSS resize handle per uildc-24 section 1.3.

| Task ID | Description | Owner | Depends on | Est (h) | Reference | Status |
|---------|-------------|-------|-----------|---------|-----------|--------|
| T-24.022 | Add "History" action button (ph-clock-clockwise) to each job row in `scheduler.js`; clicking sets module-scope `currentJobId` and opens Job History FlexDrawer (position=right, size=lg, per T-24.002 result); calls `GET /scheduler/jobs/{job_id}/executions`; FlexTable(compact, clickable-rows) columns: Started, Status (FlexBadge aria-label="Status: {value}"), Duration; FlexSpinner loading; ph-clock empty state "No runs yet"; Escape closes drawer; focus trapped | C3 | T-24.002, T-24.008 | 4 | epic-24 section 24.5.1 drawer and execution list | OPEN |
| T-24.023 | Implement vertical split log viewer inside drawer body using FlexStack(direction=vertical) + CSS: executions pane (max-height: 45%; overflow-y: auto); resize divider (border-t bg-gray-50 h-1 cursor-ns-resize); log pane (flex: 1; min-height: 120px); clicking an execution row calls `GET /scheduler/executions/{execution_id}/logs`; renders per-line colour-coded output in `<pre role="log" aria-label="Job execution log" aria-live="polite">`; ERROR/CRITICAL -> text-red-400; WARN/WARNING -> text-yellow-400; all others -> text-green-400 per uildc-24 section 2.5; each line wrapped in `<span class="{colourClass}">`; do NOT use FlexSplitPane(direction=vertical) | C3 | T-24.022 | 3 | epic-24 section 24.5.1 log pane | OPEN |
| T-24.024 | QA: verify History button opens drawer for correct job; verify execution list loads and row click populates log pane; verify colour coding for ERROR/WARN/default log lines; verify Escape closes drawer; verify focus trap and aria attributes on drawer; confirm FlexSplitPane(direction=vertical) is absent from implementation | D1 | T-24.022, T-24.023 | 2 | epic-24 section 24.5.1 AC | OPEN |

**Subtotal: 9 hrs**

---

### Item 24.6 -- Builder Version History (Story 24.6.1)

> Requires T-24.004 verdict (extend vs supersede builder-version-history.js) and P0 gate (T-24.008 DONE).

| Task ID | Description | Owner | Depends on | Est (h) | Reference | Status |
|---------|-------------|-------|-----------|---------|-----------|--------|
| T-24.025 | Add "History" ghost button (ph-clock-clockwise) to right cluster of builder toolbar in `builder.js`; clicking opens Version History FlexDrawer(overlay=true, position=right, size=sm, 320px); calls `GET /builder-pages/{page_id}/versions`; renders `<ul role="list">` version items each with `aria-label="Version {N}, saved {relative time} by {author}"`; ph-files empty state "No versions saved yet"; FlexSpinner loading | C3 | T-24.004, T-24.008 | 3 | epic-24 section 24.6.1 toolbar and drawer | OPEN |
| T-24.026 | Implement version preview: ph-eye "Preview" button per version item calls `GET /builder-pages/{page_id}/versions/{version_number}`; opens FlexModal(size=xl) with existing canvas renderer set to pointer-events: none; role=dialog, aria-modal=true, aria-labelledby pointing to modal h2; Escape closes unless action in-flight (uildc-24 section 5.1) | C3 | T-24.025 | 3 | epic-24 section 24.6.1 preview modal | OPEN |
| T-24.027 | Implement inline restore confirmation: ph-arrow-counter-clockwise "Restore" button per version item; clicking shows inline confirm row replacing the action row for that item (no second modal); when confirmation is visible all other version items' Restore buttons become disabled + opacity-50 (uildc-24 section 2.6 concurrent-restore prevention); focus moves to "Yes, restore" on show; "Cancel" returns focus to triggering button; "Yes, restore" calls `POST /builder-pages/{page_id}/restore/{version_number}`; on success store currentVersionNumber in module scope, show FlexNotification success toast, reload builder canvas | C3 | T-24.025 | 4 | epic-24 section 24.6.1 restore flow | OPEN |
| T-24.028 | If T-24.004 verdict is SUPERSEDE: delete `frontend/assets/js/builder-version-history.js` after confirming all functionality is replaced by code in `builder.js`; update any remaining import references; add deletion note to commit message | C3 | T-24.027 | 1 | arch-24 section 3.6 supersede path | OPEN |
| T-24.029 | QA: verify History toolbar button opens drawer; verify version list loads with correct aria-labels; verify Preview modal opens with pointer-events:none canvas and Escape closes it; verify Restore inline confirm disables all other Restore buttons; verify successful restore reloads canvas; verify Cancel returns focus to triggering button | D1 | T-24.026, T-24.027 | 2 | epic-24 section 24.6.1 AC | OPEN |

**Subtotal: 13 hrs**

---

### Item 24.7 -- Dev Tool Cleanup (Story 24.7.1)

> Can run in parallel with any P1 story; only dependency is P0 gate complete.

| Task ID | Description | Owner | Depends on | Est (h) | Reference | Status |
|---------|-------------|-------|-----------|---------|-----------|--------|
| T-24.030 | Remove routes `flex-layout-sandbox`, `builder-showcase`, `components-showcase`, `datatable`, `debug-financial-module` from all menu/nav config arrays in `app.js` and any static nav arrays; add a dev-banner guard in `app.js loadRoute()` for the same five routes so direct-URL navigation in developer environments shows an informational banner rather than a broken page (arch-24 section 3.7) | C3 | T-24.008 | 2 | epic-24 section 24.7.1 | DONE |
| T-24.031 | QA: verify removed routes are absent from production nav; verify direct-URL navigation to each of the five removed routes hits the dev-banner guard and not a broken page; verify no JS console errors on initial page load after deletions | D1 | T-24.030 | 1 | epic-24 section 24.7.1 AC | OPEN |

**Subtotal: 3 hrs**

---

### Sprint Close

| Task ID | Description | Owner | Depends on | Est (h) | Reference | Status |
|---------|-------------|-------|-----------|---------|-----------|--------|
| T-24.032 | Run `scripts/regen-pipeline.py`; verify `plan/PIPELINE.md` reflects tasks-24 status approved and all upstream artifact statuses are accurate; commit updated pipeline file alongside any final status updates | E1 | T-24.029, T-24.031 | 1 | AGENT_STANDARD section 6 rule 4 | OPEN |

**Subtotal: 1 hr**

---

## Dependency Graph (critical path)

```
Sprint-Start Verification (Day 1 AM)
T-24.001 (endpoint smoke-test)
T-24.002 (component grep -- FlexAccordion/Tabs/Datepicker/Drawer)
T-24.003 (password-strength-indicator.js review)
T-24.004 (builder-version-history.js review)  <- T-24.002

P0 Gate (Stories 24.1.1 + 24.1.2 + 24.1.3)
T-24.005 (router entries)  <- T-24.001
    |
    +-- T-24.006 (request-reset view)
    |       |
    |       +-- T-24.007 (confirm-reset view)  <- also T-24.003
    |
    +-- T-24.008 (honesty banner + route cleanup)  [P0 gate complete]
              |
              +-- Story 24.2 ----------------------------------------
              |   T-24.009 (password-strength-indicator.js)  <- T-24.003
              |       +-- T-24.010 (attach to settings-security.js)
              |               +-- T-24.011 (D1 QA)
              |
              +-- Story 24.3 ----------------------------------------
              |   T-24.012 (FlexToolbar + preview/publish trigger)
              |       +-- T-24.013 (diff modal + publish)
              |       |       +-- T-24.015 (D1 QA)
              |       +-- T-24.014 (drag-reorder + empty state)
              |               +-- T-24.015 (D1 QA)
              |
              +-- Story 24.4 ----------------------------------------
              |   T-24.016 (rule test panel)  <- also T-24.002
              |   T-24.017 (date-param verification)  <- also T-24.001
              |   T-24.018 (execution history tab)  <- T-24.002 + T-24.016
              |       +-- T-24.019 (date-range filter)  <- also T-24.017
              |       +-- T-24.020 (execution detail drawer)  <- T-24.002
              |               +-- T-24.021 (D1 QA)
              |
              +-- Story 24.5 ----------------------------------------
              |   T-24.022 (history drawer + execution list)  <- T-24.002
              |       +-- T-24.023 (vertical split log viewer -- FlexStack NOT FlexSplitPane)
              |               +-- T-24.024 (D1 QA)
              |
              +-- Story 24.6 ----------------------------------------
              |   T-24.025 (toolbar button + version list drawer)  <- T-24.004
              |       +-- T-24.026 (preview modal)
              |       +-- T-24.027 (inline restore confirmation)
              |               +-- T-24.028 (file deletion if supersede verdict)
              |               +-- T-24.029 (D1 QA)
              |
              +-- Story 24.7 ----------------------------------------
                  T-24.030 (dev route removal)
                      +-- T-24.031 (D1 QA)

Sprint Close
T-24.032 (pipeline regen)  <- T-24.029 + T-24.031
```

**Critical path (longest serial chain):**
T-24.001 -> T-24.005 -> T-24.008 -> T-24.025 -> T-24.027 -> T-24.029 -> T-24.032

The builder version history story (Item 24.6) is the longest P1 chain at 4 serial frontend tasks. Password reset confirm (T-24.007) is a secondary critical path risk because it has two upstream dependencies (T-24.003 and T-24.005) and carries the security-critical history.replaceState requirement.

---

## Sprint Summary

| Item | Stories | Tasks | Est. hrs | Owner(s) |
|------|---------|------:|--------:|---------|
| Verification Gate | -- | 4 | 5 | C2, C3 |
| 24.1 Trust & Nav Fixes (P0 Gate) | 24.1.1, 24.1.2, 24.1.3 | 4 | 12 | C3 |
| 24.2 Password Strength UX | 24.2.1 | 3 | 8 | C3, D1 |
| 24.3 Data Model Publish UX | 24.3.1 | 4 | 13 | C3, D1 |
| 24.4 Automation Visibility | 24.4.1, 24.4.2 | 6 | 15 | C2, C3, D1 |
| 24.5 Scheduler Log Viewer | 24.5.1 | 3 | 9 | C3, D1 |
| 24.6 Builder Version History | 24.6.1 | 5 | 13 | C3, D1 |
| 24.7 Dev Tool Cleanup | 24.7.1 | 2 | 3 | C3, D1 |
| Sprint Close | -- | 1 | 1 | E1 |
| **TOTAL** | **10 stories** | **32** | **79** | |

> Note: 79 hours is net coding and QA time (C3 approx 62h, C2 approx 3h, D1 approx 13h, E1 approx 1h). Well within the 128 hr total sprint capacity.

---

## Follow-up Backlog (out of sprint scope)

- `FlexSplitPane direction=vertical` option: uildc-24 section 1.3 flags this as absent; CSS workaround ships in Epic 24; proper resize-handle component option should be added in Epic 25 engineering backlog
- D3.js module dependency graph: text-list MVP used in Epic 23; D3 visualisation deferred per uildc-24 section 3 Decision 1; re-evaluate at Epic 25
- Forgot-password branded email template: plain text ships now; E2 Technical Writer to design HTML template in a parallel epic; SMTP delivery is also explicitly out of scope for this epic
- Mobile-responsive markup for Epic 24 screens: all layouts are desktop-first per uildc-24 section 6; mobile targets deferred
- D3 Security Engineer sec-review-24.md: to be commissioned after sprint completes; reset-token flow (T-24.007 history.replaceState) and builder restore endpoint are primary review targets
- E2 Technical Writer release-notes-epic-24.md: to be commissioned after D3 sign-off
