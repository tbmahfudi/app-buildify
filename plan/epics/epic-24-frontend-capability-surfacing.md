---
artifact_id: epic-24-frontend-capability-surfacing
type: epic
producer: A3 Product Owner
consumers: [B1 Software Architect, B3 UX Designer, C1 Tech Lead, C3 Frontend Developer]
upstream: [pm-review-frontend-screens-01]
downstream: []
status: approved
created: 2026-06-19
updated: 2026-06-26
shape: feature
sprint_target: epic-24 sprint 1
decisions:
  - Scope is front-end only — all backend endpoints already exist; no schema migrations required
  - P0 items (forgot-password, notification honesty banner, duplicate route fix) are gate stories; they must ship before P1 work begins
  - Notification email delivery (SMTP wiring) is explicitly OUT OF SCOPE — that is a separate epic; this epic only adds the "not yet available" honesty banner
  - Story IDs are stable; no renumbering once epic is approved
  - NoCode module builder and Workflow Simulator are scoped to thin MVP panels — full designer-grade UIs are deferred
  - Dev-tool screen removal from production nav is a single one-story cleanup, not a feature of its own
open_questions:
  - Forgot-password email: does the reset link need a custom branded template or plain text is acceptable for MVP? Recommend plain text first — escalate to E2 Tech Writer.
  - Module dependency graph: D3.js vis or a simple indented text list? Recommend text list first — B3 UX call.
  - Builder version history sidebar: inline panel or full-page route? B3 UX call.
---

# Epic 24 — Frontend Capability Surfacing

> **Surface what the backend already does.** Per the A1 PM review (`pm-review-frontend-screens-01`), the backend is ~85% ready while the frontend exposes ~55% of it. This epic delivers the P0/P1 gap closures: a forgot-password flow, notification honesty, duplicate-route cleanup, data-model publish UX, automation test/history panels, and scheduler log viewer. No new backend code is required — every story wires an existing endpoint to a new or updated UI element.

---

## Feature 24.1 — P0: Trust & Navigation Fixes `[OPEN]`

> Gate feature. Stories 24.1.1–24.1.3 must be DONE before Feature 24.2 work begins.

### Story 24.1.1 — Forgot-password UI flow `[OPEN]`

*As a user who has forgotten their password, I want a "Forgot password?" link on the login screen that leads me through a reset flow so that I can regain access without contacting support.*

#### Backend
- Endpoints already exist: `POST /api/v1/auth/reset-password-request` (accepts `{email}`) and `POST /api/v1/auth/reset-password-confirm` (accepts `{token, new_password}`).
- No backend changes required.
- AC: `reset-password-request` returns `200` regardless of whether the email exists (prevents user enumeration — confirm this is the current behaviour; if not, file a security story).

#### Frontend

- Route: `#reset-password` → `login.html` (request view) | `#reset-password-confirm` → `login.html` (confirm view)
- Layout: FlexStack(direction=vertical, align=center) > auth-card
  - auth-card: FlexSection(max-w=sm, mx=auto, mt=24) — logo | view-content | back-link
    - logo: app logo mark (same as login page), centred
    - view-content: switches between request-view and confirm-view based on route hash
    - back-link: plain anchor "← Back to login" → `#login`, centred below card

- **Component Spec — Request View** (shown at `#reset-password`):
  - `FlexStack(direction=vertical, gap=md)` containing:
    - Page title `<h1>` "Reset your password" (text-xl, font-semibold)
    - Subtitle `<p>` "Enter your email and we'll send a reset link." (text-sm, text-gray-500)
    - `FlexInput(type=email, name=email, label="Email address", required, autofocus)`
    - `FlexButton(variant=primary, full-width)` "Send reset link"
    - `FlexAlert(type=error, id=request-error)` — hidden until API error; shown inline below button
  - On success API response: replace entire view-content zone with a `FlexAlert(type=success, persistent)`:
    - Icon: ph-envelope-open
    - Title: "Check your inbox"
    - Body: "If that address is registered, a reset link is on its way."
    - No dismiss button (persistent — user must navigate away)

- **Component Spec — Confirm View** (shown at `#reset-password-confirm?token=…`):
  - `FlexStack(direction=vertical, gap=md)` containing:
    - Page title `<h1>` "Set a new password"
    - `FlexInput(type=password, name=new_password, label="New password", required, autofocus)`
    - Password strength indicator (see Story 24.2.1) — rendered immediately below new_password field
    - `FlexInput(type=password, name=confirm_password, label="Confirm new password", required)`
    - Inline validation message "Passwords do not match" (text-red-500, text-sm) — shown only when confirm_password is dirty and values differ
    - `FlexButton(variant=primary, full-width, disabled=until-valid)` "Set new password"
    - `FlexAlert(type=error, id=confirm-error)` — hidden until API error

- **Login page change (diff only):**
  - Below the `FlexInput(type=password)` field: add `<a href="#reset-password" class="text-sm text-blue-600 hover:underline">Forgot password?</a>` right-aligned
  - No other layout change to login.html

- **States:**
  - loading (request submit): FlexButton shows built-in spinner; input disabled
  - loading (confirm submit): FlexButton spinner; both inputs disabled
  - empty/no-token (confirm view loaded without `?token=`): immediately show `FlexAlert(type=error)` "This reset link is invalid or missing. Request a new one." with link to `#reset-password`; hide the form
  - token-expired (API 400 on confirm): show `FlexAlert(type=error)` "This link has expired. Request a new one." with link; keep form hidden
  - error (network): `FlexAlert(type=error)` "Something went wrong. Please try again." below the button

- **Interactions:**
  - on [submit request form]: prevent default; disable button; POST `/reset-password-request`; handle success/error
  - on [keyup confirm_password]: compare values; show/hide mismatch message; toggle button disabled state
  - on [all password rules satisfied AND passwords match]: enable submit button
  - on [submit confirm form]: prevent default; disable both inputs and button; POST `/reset-password-confirm`; on success navigate to `#login` and fire `FlexNotification(type=success)` "Password updated — please log in."

---

### Story 24.1.2 — Notification settings honesty banner `[OPEN]`

*As a tenant admin, I want a clear notice on the Notifications settings page that email delivery is not yet active so that I don't configure notification rules expecting emails that will never arrive.*

#### Backend
- No backend changes. The notification stub endpoints remain as-is.

#### Frontend

- Route: `#settings` (notifications tab) → `settings-notifications.html`
- Layout: FlexStack(direction=vertical) > honesty-banner, existing-content
  - honesty-banner: `FlexAlert(type=warning, persistent, icon=ph-envelope-simple-slash)` — full-width, no dismiss
    - Title slot: "Email notifications are not yet active"
    - Body slot: "Your preferences are saved and will apply once email delivery is configured by your administrator. In-app notifications are active now."
  - existing-content: current notification toggle sections — unchanged

- **States:** static — banner is always visible; no loading/empty/error variants
- **Interactions:** none — informational only; no links, no buttons on the banner itself

---

### Story 24.1.3 — Duplicate report-designer route cleanup `[OPEN]`

*As a user navigating to a report designer, I want a single consistent route so that I don't land on different or broken pages depending on which link I clicked.*

#### Backend
- No backend changes.

#### Frontend

- No new UI components. This story is a codebase cleanup.
- Canonical route: `#report-designer` (singular). All other forms are aliases that redirect.
- Redirect rule in `app.js` `loadRoute()`:
  ```
  if (route === 'reports-designer') { window.location.hash = 'report-designer'; return; }
  ```
- File to delete: `frontend/assets/templates/reports-designer.html`
- File to keep: `frontend/assets/templates/report-designer.html`
- All sidebar/menu hrefs pointing to `#reports-designer` or `#reports/designer` updated to `#report-designer`

- **States:** n/a
- **Interactions:** n/a

---

## Feature 24.2 — P1: Auth & Password UX `[OPEN]`

### Story 24.2.1 — Live password-strength feedback `[OPEN]`

*As a user changing my password, I want to see a live strength indicator as I type so that I know whether my new password will be accepted before I submit.*

#### Backend
- `GET /api/v1/auth/password-policy` already returns the active policy: `{min_length, max_length, require_uppercase, require_lowercase, require_digit, require_special_char, min_unique_chars}`.
- Call this endpoint once on page load (or on component mount); cache the result for the session.
- No new backend endpoints required.

#### Frontend

- This is a **reusable inline component** — not a route. Rendered below any `FlexInput(type=password)` field designated as "new password".
- Implemented as a vanilla JS module `password-strength-indicator.js` (new file, not a Flex component — too tightly coupled to a single field).

- **Component Spec — PasswordStrengthIndicator:**
  - Container: `<div class="password-strength mt-2 space-y-1">` rendered immediately after the target `FlexInput`
  - Loading state: single line `<p class="text-xs text-gray-400"><span class="ph ph-spinner animate-spin"></span> Loading rules…</p>`
  - Rule list (after policy loads): `<ul>` of `<li>` items, one per active policy rule
    - Each `<li>`: icon `ph-check-circle` (green) or `ph-x-circle` (red) or `ph-circle` (grey/neutral) + rule label
    - Rule labels:
      - `require_uppercase` → "One uppercase letter (A–Z)"
      - `require_lowercase` → "One lowercase letter (a–z)"
      - `require_digit` → "One number (0–9)"
      - `require_special_char` → "One special character (!@#…)"
      - always shown → "At least {min_length} characters"
    - Only rules where the policy value is `true` (or `min_length > 0`) are rendered
  - Strength meter bar: `FlexProgress(variant=bar, color=auto, size=xs)` below the list; value = (rules_passed / rules_total) × 100

- **Integration points:**
  - Settings → Security "Change password" form: attach to "New password" field
  - Story 24.1.1 Confirm Reset "New password" field: attach same component
  - Call `passwordStrengthIndicator.attach(inputEl, submitBtn)` — disables `submitBtn` until all rules pass

- **States:**
  - neutral (no input yet): all rule icons grey `ph-circle`; progress bar at 0, color=gray
  - partial: mixed green/red icons; progress bar color=auto (red→amber→green)
  - complete (all rules pass): all icons green; progress bar 100% green; `submitBtn` enabled
  - loading: spinner placeholder row; `submitBtn` disabled
  - error (policy fetch fails): component not rendered; `submitBtn` enabled (fail-open — don't block the user)

- **Interactions:**
  - on [input event on password field]: re-evaluate all rules; update icons and progress bar; toggle submitBtn
  - on [policy fetch success]: render rule list; re-evaluate against current field value immediately
  - on [policy fetch error]: remove loading placeholder; enable submitBtn silently

---

## Feature 24.3 — P1: Data Model Publish UX `[OPEN]`

### Story 24.3.1 — Publish button with migration diff preview `[OPEN]`

*As a tenant admin who has edited an entity's field definitions, I want a clearly labelled "Publish" button that shows me a migration diff before I confirm so that I understand what schema changes will be applied.*

#### Backend
- `GET /api/v1/data-model/entities/{entity_id}/preview-migration` returns the pending diff.
- `POST /api/v1/data-model/entities/{entity_id}/publish` applies the migration.
- No backend changes.

#### Frontend

- Route: `#nocode-data-model` (entity editor view) → `nocode-data-model.html`
- Layout (diff only — entity editor toolbar row):
  - entity-toolbar: FlexToolbar — entity-name-heading | FlexCluster(gap=sm, align=right) > status-badge | preview-btn | publish-btn
    - status-badge: `FlexBadge(variant=amber)` "Draft" OR `FlexBadge(variant=green)` "Published" — driven by `entity.status`
    - preview-btn: `FlexButton(variant=secondary, size=sm, icon=ph-eye)` "Preview changes"
    - publish-btn: `FlexButton(variant=primary, size=sm, icon=ph-rocket-launch)` "Publish" — disabled when status=Published and no pending changes

- **Component Spec — Migration Diff Modal** (`FlexModal(size=lg, id=migration-diff-modal)`):
  - Trigger: both "Preview changes" button and "Publish" button open this modal (Publish button fetches diff first)
  - Header slot: "Schema changes to apply" | entity name (subtitle)
  - Body slot: `FlexStack(direction=vertical, gap=lg)` with up to three sub-sections:
    - Each sub-section: `<h3>` label ("Fields to add" / "Fields to modify" / "Fields to remove") + `FlexTable`
    - "Fields to add" table columns: Field Name | Type | Nullable | Default
    - "Fields to modify" table columns: Field Name | Current Type | New Type | Change
    - "Fields to remove" table columns: Field Name | Type | Warning ("Data will be lost")
    - Rows in "Fields to remove" shown with `text-red-600` and a `ph-warning` icon
    - Empty sub-section (no changes of that type): section not rendered
  - Footer slot:
    - `FlexButton(variant=secondary)` "Close" — always visible
    - `FlexButton(variant=primary, icon=ph-rocket-launch)` "Publish now" — hidden when no changes pending

- **Component Spec — Publish In-Progress Overlay** (inside modal footer, replaces buttons):
  - `FlexProgress(variant=bar, indeterminate, size=xs)` with label "Applying migration…"
  - Shown while `POST /publish` is in-flight; dismissed on response

- **States:**
  - loading (diff fetch, modal open): modal body shows `FlexSpinner` centred + "Fetching pending changes…" label
  - empty (no pending changes): modal body shows `FlexAlert(type=info, icon=ph-check-circle)` "No unpublished changes. Your schema is up to date."; "Publish now" button hidden; toolbar "Publish" button disabled
  - error (diff fetch fails): modal body shows `FlexAlert(type=error)` "Could not load migration preview. Try again." + retry link; "Publish now" button hidden
  - publishing: in-progress overlay replaces footer buttons; modal not dismissable (backdrop click blocked)
  - publish-success: modal closes; status-badge updates to `FlexBadge(variant=green)` "Published"; `FlexNotification(type=success)` "Schema published successfully."
  - publish-error: in-progress overlay removed; `FlexAlert(type=error)` inserted above footer buttons with API error message; modal stays open

- **Interactions:**
  - on [click "Preview changes"]: fetch `GET /entities/{id}/preview-migration`; open modal with result
  - on [click "Publish" in toolbar]: same as "Preview changes" — always shows diff before committing
  - on [click "Publish now" in modal]: show in-progress overlay; POST `/entities/{id}/publish`; handle success/error
  - on [click "Close"]: close modal; no state change
  - on [publish success]: update entity.status in page state; re-evaluate toolbar badge and button disabled state

---

## Feature 24.4 — P1: Automation Visibility `[OPEN]`

### Story 24.4.1 — Automation rule test panel `[OPEN]`

*As a tenant admin building an automation rule, I want to click "Test Rule" and see which records matched and what actions fired so that I can validate my rule logic without waiting for a real event.*

#### Backend
- `POST /api/v1/automations/rules/{rule_id}/test` exists; returns test execution results.
- No backend changes.

#### Frontend

- Route: `#nocode-automations` (rule detail view) → `nocode-automations.html`
- Layout (diff only — below the rule condition builder section):
  - rule-test-panel: `FlexAccordion(id=rule-test-panel, initially-collapsed)` — "Test this rule"
    - accordion-header: FlexToolbar — "Test this rule" label | last-run-timestamp (text-xs text-gray-400) | `FlexButton(variant=secondary, size=sm, icon=ph-play)` "Run test"
    - accordion-body: test-results-zone

- **Component Spec — Test Results Zone** (inside accordion body):
  - Default (never run): `<p class="text-sm text-gray-400">Run the test to see which records match and which actions would fire.</p>`
  - Loading: `FlexStack(direction=horizontal, gap=sm, align=center)` — `FlexSpinner(size=sm)` | "Running test…" (text-sm)
  - Results layout: `FlexGrid(columns=2, gap=md)`:
    - Left cell — "Records matched" `FlexBadge(variant=blue)` count + scrollable `<ul>` of record names (max 10); if >10 show "+ N more" link
    - Right cell — "Actions that would fire" `<ul>` of action names with resolved parameter snippets (`<code>` inline)
  - Stale indicator: `FlexAlert(type=warning, size=sm, dismissable=false)` "Rule changed — results may be outdated. Run test again." — shown when rule conditions are edited after a test run; cleared on next test run

- **States:**
  - collapsed (default): accordion shows only header row
  - expanded-idle: accordion open; default never-run message shown
  - expanded-loading: spinner row; "Run test" button disabled
  - expanded-results: grid with matched records + actions
  - expanded-empty: `FlexAlert(type=info, icon=ph-funnel)` "No records matched this rule's conditions." (not an error)
  - expanded-error: `FlexAlert(type=error)` with API error message; "Run test" button re-enabled
  - stale: stale-indicator banner shown above results (results still visible but dimmed opacity-60)

- **Interactions:**
  - on [click accordion header]: toggle collapsed/expanded
  - on [click "Run test"]: clear stale indicator; show loading; POST `/rules/{id}/test`; render results
  - on [any change to rule condition fields]: if results are showing, add stale indicator without clearing results
  - on [click "+ N more" in records list]: expand list inline (no pagination nav)"

---

### Story 24.4.2 — Automation execution history `[OPEN]`

*As a tenant admin, I want to see a history of when my automation rules have fired and what happened so that I can confirm rules are working and diagnose failures.*

#### Backend
- `GET /api/v1/automations/executions` (list, filterable by rule_id).
- `GET /api/v1/automations/executions/{execution_id}` (detail).
- No backend changes.

#### Frontend

- Route: `#nocode-automations` → `nocode-automations.html` (adds a third tab)
- Layout: FlexStack(direction=vertical) > page-tabs, tab-content
  - page-tabs: `FlexTabs(id=automations-tabs)` — tab labels: "Rules" | "Execution History" | "Webhooks"
  - tab-content: renders active tab panel below the tab strip

- Tab panel: "Execution History"
  - Layout: FlexStack(direction=vertical, gap=md) > filter-bar, execution-table, detail-panel
    - filter-bar: FlexCluster(gap=sm) — `FlexSelect(id=rule-filter, placeholder="All rules", clearable)` | `FlexSelect(id=status-filter, options=[All,Success,Failed,Partial])` | `FlexDatepicker(range, placeholder="Date range")`
    - execution-table: `FlexTable(id=execution-table, clickable-rows)` — see Component Spec below
    - detail-panel: `FlexDrawer(position=right, size=md, overlay=false)` — see Component Spec below; hidden by default

- **Component Spec — Execution Table** (`FlexTable`):
  - Columns: Triggered At (sortable, default desc) | Rule Name | Status | Duration | Records Affected
  - Status cell: `FlexBadge(variant=green)` "Success" / `FlexBadge(variant=red)` "Failed" / `FlexBadge(variant=amber)` "Partial"
  - Duration cell: formatted as "1.2s" or "342ms"
  - Row click → open detail drawer; selected row highlighted with `bg-blue-50`
  - `FlexPagination` below table, page size 25

- **Component Spec — Execution Detail Drawer** (`FlexDrawer`):
  - Header: Rule name (font-semibold) | triggered-at timestamp (text-sm text-gray-500) | close button (ph-x)
  - Body: `FlexStack(direction=vertical, gap=md)`:
    - "Actions taken" sub-section: `<h4>` + `<ul>` of action names with parameter summary
    - "Records affected" sub-section: `<h4>` + count badge + first 5 record names (expandable)
    - "Error" sub-section (shown only when status=Failed): `<h4>` "Error" + `<pre class="text-xs bg-gray-50 p-3 rounded overflow-auto">` with raw error message
  - Footer: `FlexButton(variant=secondary, full-width)` "Close"
  - Loading state (while fetching detail): body replaced with `FlexSpinner` centred

- **States:**
  - loading (initial table fetch): `FlexSpinner` centred in table zone
  - empty (no executions): `FlexAlert(type=info, icon=ph-clock)` "No executions recorded yet. Automation rules will appear here after they fire."
  - error (table fetch fails): `FlexAlert(type=error)` with retry button
  - drawer-loading: spinner in drawer body while `GET /executions/{id}` is in-flight
  - drawer-error: `FlexAlert(type=error)` in drawer body; close button still available

- **Interactions:**
  - on [tab "Execution History" activated]: fetch `GET /automations/executions`; render table
  - on [select rule in filter]: re-fetch with `?rule_id=…`
  - on [select status filter]: re-fetch with `?status=…` (if server-side) or client-filter
  - on [select date range]: re-fetch with `?from=…&to=…`
  - on [click table row]: open drawer; fetch `GET /executions/{id}`; render detail
  - on [click "Close" or backdrop]: close drawer; deselect row

---

## Feature 24.5 — P1: Scheduler Log Viewer `[OPEN]`

### Story 24.5.1 — Job execution log viewer `[OPEN]`

*As an operator, I want to click on a scheduled job's past run and see the full log output so that I can diagnose failures without accessing the server directly.*

#### Backend
- `GET /api/v1/scheduler/jobs/{job_id}/executions` — list of past runs.
- `GET /api/v1/scheduler/executions/{execution_id}/logs` — log lines for a run.
- No backend changes.

#### Frontend

- Route: `#scheduler` → `scheduler.html`
- Layout (diff only — each job row in the job list table):
  - job-row actions cell: append `FlexButton(variant=ghost, size=sm, icon=ph-clock-clockwise, tooltip="Run history")` — clicking opens the Job History Drawer

- **Component Spec — Job History Drawer** (`FlexDrawer(position=right, size=lg, id=job-history-drawer)`):
  - Header: "Run history" | job name subtitle (text-sm text-gray-500) | close button (ph-x)
  - Body: `FlexSplitPane(direction=vertical, initial-split=40%)` > executions-pane, log-pane
    - executions-pane: `FlexTable(id=job-executions-table, clickable-rows, compact)` — columns: Started At | Status | Duration | Trigger
      - Status badge: `FlexBadge(variant=green)` "Success" / `FlexBadge(variant=red)` "Failed" / `FlexBadge(variant=amber)` "Running"
      - Selected row: `bg-blue-50`; clicking fetches log for that run
    - log-pane: log output area (below the table, separated by a resize handle)
      - Default (no run selected): `<p class="text-xs text-gray-400 text-center mt-8">Select a run above to view its log output.</p>`
      - Loaded: `<pre class="text-xs font-mono bg-gray-950 text-green-400 p-4 h-full overflow-auto rounded-b">` with log lines
      - Log line colouring: lines containing "ERROR" or "CRITICAL" → `text-red-400`; "WARN" → `text-yellow-400`; others → `text-green-400`
  - Footer: `FlexButton(variant=secondary)` "Close"

- **States:**
  - drawer-closed: not rendered (removed from DOM)
  - drawer-loading (executions fetch): `FlexSpinner` centred in executions-pane; log-pane shows default prompt
  - drawer-empty (no runs): `FlexAlert(type=info, icon=ph-clock)` "No runs recorded for this job yet." in executions-pane
  - drawer-error (executions fetch fails): `FlexAlert(type=error)` in executions-pane; log-pane unchanged
  - log-loading (log fetch for selected run): spinner in log-pane; executions table still interactive
  - log-empty (run has no log output): `<p class="text-xs text-gray-400">No log output captured for this run.</p>` in log-pane
  - log-error (log fetch fails): `FlexAlert(type=error, size=sm)` in log-pane

- **Interactions:**
  - on [click "View history" in job row]: open drawer; fetch `GET /jobs/{id}/executions`; render table
  - on [click execution row]: deselect previous row; highlight clicked row; fetch `GET /executions/{id}/logs`; render in log-pane
  - on [drag split handle]: resize executions-pane and log-pane proportionally (FlexSplitPane built-in)
  - on [click "Close" or backdrop]: close drawer; clear selected job context

---

## Feature 24.6 — P1: Builder Version History `[OPEN]`

### Story 24.6.1 — Page version history sidebar `[OPEN]`

*As a page builder user, I want to open a version history panel and restore a previous version so that I can recover from accidental changes without losing my work.*

#### Backend
- `GET /api/v1/builder-pages/{page_id}/versions` — list of versions.
- `GET /api/v1/builder-pages/{page_id}/versions/{version_number}` — version detail/preview.
- `POST /api/v1/builder-pages/{page_id}/restore/{version_number}` — restore.
- No backend changes.

#### Frontend

- Route: `#builder` → `builder.html`
- Layout (diff only — builder toolbar right cluster):
  - builder-toolbar-right: FlexCluster(gap=sm) — … existing save/publish buttons … | `FlexButton(variant=ghost, size=sm, icon=ph-clock-clockwise, tooltip="Version history")` "History"
  - history-drawer: `FlexDrawer(position=right, size=sm, overlay=true, id=version-history-drawer)` — rendered outside the canvas, overlaps it

- **Component Spec — Version History Drawer** (`FlexDrawer`):
  - Header: "Version history" | page name subtitle | close button (ph-x)
  - Body: `FlexStack(direction=vertical, gap=none)` — scrollable version list
    - Each version item: `<div class="version-item border-b py-3 px-4">` containing:
      - Row 1: `FlexBadge(variant=green)` "Live" (only on currently published version) | version number `#N` (text-sm font-mono) | save-type chip: `FlexBadge(variant=gray, size=xs)` "Autosave" or "Manual"
      - Row 2: relative timestamp "2 hours ago" (text-xs text-gray-500) | author email (text-xs text-gray-400)
      - Row 3 (action row): `FlexButton(variant=ghost, size=xs, icon=ph-eye)` "Preview" | `FlexButton(variant=ghost, size=xs, icon=ph-arrow-counter-clockwise)` "Restore"
    - Restore confirmation (shown inline, replaces action row on "Restore" click):
      - `<p class="text-xs text-amber-700">Unsaved changes will be lost.</p>`
      - `FlexButton(variant=danger, size=xs)` "Yes, restore" | `FlexButton(variant=ghost, size=xs)` "Cancel"
  - Footer: `FlexButton(variant=secondary, full-width)` "Close"

- **Component Spec — Version Preview Modal** (`FlexModal(size=xl, id=version-preview-modal)`):
  - Trigger: "Preview" button on any version item
  - Header: "Version #N — preview" | timestamp
  - Body: read-only canvas render of the version JSON (same builder canvas renderer, `pointer-events=none`)
  - `FlexAlert(type=info, size=sm, persistent)` pinned at top of body: "This is a preview. No changes have been made."
  - Footer: `FlexButton(variant=secondary)` "Close" | `FlexButton(variant=primary, icon=ph-arrow-counter-clockwise)` "Restore this version"
  - "Restore this version" in modal triggers the same inline confirmation flow as the drawer button

- **States:**
  - drawer-loading: `FlexSpinner` centred in drawer body
  - drawer-empty: `FlexAlert(type=info, icon=ph-files)` "No versions saved yet. Save the page to create the first version."
  - drawer-error: `FlexAlert(type=error)` with retry button
  - restore-confirming: action row replaced by inline confirmation (other items' action rows remain visible)
  - restore-in-progress: "Yes, restore" button shows spinner; drawer not dismissable
  - restore-success: drawer closes; canvas reloads with restored JSON; `FlexNotification(type=success)` "Restored to version #N."
  - restore-error: `FlexAlert(type=error, size=sm)` inline below confirmation row; confirmation buttons re-enabled

- **Interactions:**
  - on [click "History" in toolbar]: open drawer; fetch `GET /builder-pages/{id}/versions`
  - on [click "Preview"]: fetch `GET /versions/{version_number}`; open preview modal with rendered canvas
  - on [click "Restore" in drawer or modal]: show inline confirmation; disable other restore buttons
  - on [click "Yes, restore"]: POST `/restore/{version_number}`; on success reload canvas and close drawer
  - on [click "Cancel"]: hide confirmation; restore action row
  - on [click "Close" in drawer]: close drawer; no canvas change

---

## Feature 24.7 — Cleanup: Dev Tools & Duplicate Nav `[OPEN]`

### Story 24.7.1 — Remove dev-tool screens from production navigation `[OPEN]`

*As a tenant user, I want the application navigation to contain only production-ready features so that I'm not confused by internal developer tools.*

#### Backend
- No backend changes.

#### Frontend

- No new page layouts or components.
- Change 1 — **Sidebar / menu data**: remove entries for routes `flex-layout-sandbox`, `builder-showcase`, `components-showcase`, `datatable`, `debug-financial-module` from all menu config objects and any static nav arrays in `app.js`.
- Change 2 — **Dev-tool banner**: in `app.js` `loadRoute()`, add a post-render step for the five routes above:
  ```
  const DEV_ROUTES = ['flex-layout-sandbox','builder-showcase','components-showcase','datatable','debug-financial-module'];
  if (DEV_ROUTES.includes(route)) {
    const banner = document.createElement('div');
    banner.className = 'fixed bottom-4 right-4 z-50';
    banner.innerHTML = '<div class="bg-gray-800 text-white text-xs px-3 py-2 rounded shadow">🛠 Internal developer tool</div>';
    document.body.appendChild(banner);
  }
  ```
- Change 3 — **HTML files**: `debug-financial-module.html` is in the root frontend directory, not under `assets/templates/` — remove from root (keep only if referenced by a template path); if unreferenced, delete the file.

- **States:** n/a
- **Interactions:** n/a

---

## Story Count & Estimates

| Feature | Stories | Rough Effort |
|---|---|---|
| 24.1 P0 Trust & Nav | 3 | 8h |
| 24.2 Password UX | 1 | 4h |
| 24.3 Data Model Publish | 1 | 8h |
| 24.4 Automation Visibility | 2 | 10h |
| 24.5 Scheduler Logs | 1 | 5h |
| 24.6 Builder History | 1 | 6h |
| 24.7 Cleanup | 1 | 2h |
| **Total** | **10 stories** | **~43h** |

---

## Out of Scope (Explicitly Deferred)

- SMTP email delivery wiring — separate epic
- OAuth / API-key integrations — separate epic
- Permission matrix table redesign — requires B3 UX design before story can be written
- Org-chart tree visualisation — deferred to Epic 25+ (org hierarchy)
- Module dependency graph — deferred to Epic 25+ (module UX v2)
- Dashboard Share + Snapshot — deferred to dashboards v2 epic
- Report export button — deferred (low backend risk; high design variation)
- Subscription tier enforcement — separate epic (High effort, Low priority per backlog)


---

## A-to-B Gate Note (A3 to B-stage, 2026-06-26)

**Approved by:** A3 Product Owner
**Gate decision:** Proceed to B-stage (B1 Architecture + B3 UX Design in parallel)

### What B1 (Software Architect) should focus on

- No new backend endpoints are required. Confirm each story endpoint reference against the live API contract before C3 begins implementation.
- The FlexSplitPane component used in Story 24.5.1 (Scheduler log viewer) is referenced but not confirmed in LAYOUT_CONVENTION.md. B1 should verify it exists or flag to B3 for resolution before C3 picks up that story.
- Routing: Epic 24 uses hash-based routing (#reset-password, #report-designer) consistent with existing patterns. B1 should confirm no route conflicts with anything registered in Epic 23.

### What B3 (UX Designer) should focus on

Open questions requiring B3 decisions (carried over from frontmatter):

1. Module dependency graph: D3.js vis or indented text list. Resolve before any dependent story; deferred to Epic 25 but B3 should record the decision now.
2. Builder version history: Story 24.6.1 assumes a right drawer. B3 should confirm or flag a deviation to inline panel or full-page route.

Password strength indicator (Story 24.2.1): component layout is specified. B3 should confirm the icon set (ph-check-circle / ph-x-circle / ph-circle) aligns with the global design token palette before C3 implements.

Notification honesty banner (Story 24.1.2): static and persistent with no interactive states. B3 sign-off is lightweight here.

### P0 gate reminder

Features 24.2 through 24.7 (P1) are blocked until Stories 24.1.1, 24.1.2, and 24.1.3 are marked [DONE]. C1 Tech Lead must enforce this sequencing in the sprint backlog.
