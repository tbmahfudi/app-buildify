# Epic 10 — Reporting

> Report designer for tabular, summary, cross-tab, and chart reports with parameterization, scheduling, and multi-format export.

---

## Feature 10.1 — Report Designer `[DONE]`

### Story 10.1.1 — Report Definition Creation `[DONE]`

#### Backend
*As an API, I want to create report definitions with data source, column, and filter configuration, so that reports can be executed on demand or on a schedule.*
- `POST /api/v1/reports` accepts `{name, report_type, entity_id, columns: [], filters: [], group_by: [], sort_by: [], parameters: []}`
- `report_type`: `tabular` / `summary` / `crosstab` / `metric` / `chart`
- Column config: `{field, label, aggregation_type, format, width, visible}`
- Report definition versioned; `PUT /api/v1/reports/{id}` increments version

#### Frontend
*As a tenant administrator opening the report designer, I want a 6-step wizard that walks me through naming the report, choosing a data source, configuring filters, selecting columns, defining parameters, and setting the visualization type, so that building reports is guided and I don't miss any configuration.*
- Route: `#/reports/new` → `report-designer.html` + `report-designer-page.js`
- Layout: FlexSplitPane(initial-split=60%) > wizard-panel, preview-panel
  - wizard-panel: FlexStack(direction=vertical) > stepper-header, step-content, step-footer
    - stepper-header: FlexStepper(steps=6) — Metadata | Data Source | Query | Columns | Parameters | Visualization
    - step-content: renders per active step (see specs below)
    - step-footer: FlexToolbar — "Preview" FlexButton(ghost) | Back FlexButton | Next / Save FlexButton(primary)
  - preview-panel: FlexContainer(fill) — live report preview; updates when "Preview" is clicked

- `StepMetadata` (Step 1):
  - fields: Report Name (FlexInput, required) | Description (FlexTextarea) | Category (FlexSelect) | Report Type (FlexRadio: Tabular / Summary / Chart / Cross-Tab)

- `StepDataSource` (Step 2):
  - Entity (FlexSelect, all published + module entities)
  - optional join panel: "+ Add Join" FlexButton(ghost) → join config row (entity + join field)

- `StepQuery` (Step 3):
  - Filter builder (filter-row UI, same as list page) | Sort By (FlexSelect + asc/desc) | Group By (FlexSelect, shown only for Summary report type)

- `StepColumns` (Step 4):
  - dual-pane drag-drop: available fields list (left) | selected columns list (right)
  - per selected column: Label (FlexInput) | Format (FlexSelect) | Aggregation (FlexSelect) | Width (FlexInput) | Visible (FlexCheckbox)

- `StepParameters` (Step 5):
  - parameters list: FlexStack(gap=sm) — one row per parameter
  - "+ Add Parameter" FlexButton(ghost) → parameter type picker → appends row with: Name | Label | Type (FlexSelect) | Default Value | Required (FlexCheckbox)

- `StepVisualization` (Step 6):
  - chart reports: Chart Type icon-card picker + X/Y axis FlexSelect mapping
  - tabular reports: column width + alignment tweaks per column
  - summary reports: subtotal configuration (FlexCheckbox per group level)

- Interactions:
  - click Next: FlexStepper advances; step-content swaps
  - click "Preview": POST /reports/preview with current config → preview-panel renders sample data
  - drag field from available list to selected list: column appended; drag within selected list reorders
  - click Save (Step 6): POST /reports → redirect to `#/reports/{id}/view`

- States:
  - step-1-invalid: Next disabled until Report Name is filled
  - previewing: preview-panel shows skeleton while preview call resolves
  - saving: step-footer buttons disabled + spinner

---

### Story 10.1.2 — Report Parameters `[DONE]`

#### Backend
*As an API, I want report parameters to be defined on the report definition and accepted at execution time, so that one report definition serves multiple use cases.*
- Parameter types: `string`, `integer`, `decimal`, `date`, `datetime`, `boolean`, `lookup`, `multi_select`
- `POST /api/v1/reports/{id}/run` accepts `{parameters: {param_name: value, ...}}`
- Date parameters: supports relative values `today`, `this_week`, `this_month`, `last_30_days` resolved server-side

#### Frontend
*As a user running a parameterized report, I want to see a clean parameter input form with appropriate controls for each parameter type, and be able to select relative date ranges like "This Month" without knowing specific dates, so that running reports is fast and intuitive.*
- Route: `#/reports/{id}/view` → `report-viewer.html` + `report-viewer-page.js`
- Layout: FlexStack(direction=vertical) > parameter-panel (conditional), results-area
  - parameter-panel: FlexForm — one field per report parameter + "Run Report" FlexButton(primary); shown only when report has parameters
  - results-area: report output table / chart; hidden until first run

- `ParameterForm` field type mapping:
  - `date` / `datetime` → FlexDatepicker + Quick Select chip bar (Today / Yesterday / This Week / This Month / Last 30 Days / This Quarter / This Year)
  - `lookup` → FlexSelect (searchable, loads lookup options)
  - `multi_select` → FlexSelect (multi-select mode)
  - `boolean` → FlexCheckbox toggle
  - `string` / `integer` / `decimal` → FlexInput

- Interactions:
  - click Quick Select chip (date params): FlexDatepicker populates with resolved date range
  - click "Run Report": POST /reports/{id}/run {parameters} → parameter-panel hides; results-area renders output
  - click "Change Parameters" (shown above results): parameter-panel re-appears pre-filled with previous values; results-area hides

- States:
  - loading: results-area shows skeleton while report executes
  - no-parameters: parameter-panel not rendered; report runs automatically on page load
  - empty-results: "No records match the selected parameters" in results-area
  - error: FlexAlert(type=error) "Report failed to run. Check parameters and try again."

---

### Story 10.1.3 — Report Export `[DONE]`

#### Backend
*As an API, I want to export report results in multiple formats, so that reports can be consumed outside the platform.*
- `POST /api/v1/reports/{id}/export?format=pdf` triggers `ReportExport` service
- Supported formats: `pdf`, `excel_formatted`, `excel_raw`, `csv`, `json`, `html`
- For large reports (> 50,000 rows): async export; returns `{export_id}` — poll `GET /reports/exports/{export_id}` for status
- PDF includes tenant branding (logo, colors) from `TenantSettings`

#### Frontend
*As a user viewing a report, I want an "Export" dropdown button where I can choose my format and have the file download start immediately for small reports or be notified when a large export is ready, so that sharing report results is straightforward.*
- Route: `#/reports/{id}/view` → report viewer page; export controls in the results-area toolbar
- Layout addition: FlexToolbar in results-area — "Export" FlexButton(split, default=Excel) with dropdown | "Past Exports" link

- `ExportDropdown` options: PDF | Excel (formatted) | Excel (raw) | CSV | JSON

- Interactions:
  - click "Export" (default or dropdown option): POST /reports/{id}/export?format=X
    - small report (sync): file download starts immediately via `Content-Disposition: attachment`
    - large report (async): FlexAlert(type=info) banner "Your export is being prepared. We'll notify you when it's ready."
  - export ready (async): in-app notification appears in notification bell → click notification → file downloads
  - click "Past Exports": FlexDrawer(position=right, size=sm) opens with list of past exports — columns: Format, Timestamp, "Download" FlexButton(ghost); expired entries (>24 h) show "Expired" FlexBadge(color=neutral)

- States:
  - exporting (sync): Export button shows spinner during download preparation
  - async-pending: FlexAlert(type=info) banner shown; Export button re-enabled immediately
  - past-exports-empty: "No exports yet" in drawer

---

## Feature 10.2 — Report Scheduling `[DONE]`

### Story 10.2.1 — Scheduled Report Delivery `[DONE]`

#### Backend
*As an API, I want reports to be generated and delivered on a schedule, so that stakeholders receive regular updates automatically.*
- `POST /api/v1/scheduler/jobs` with `{job_type: "report_generation", report_id, parameters: {}, schedule_type, cron_expression, delivery: {method: "email", recipients: []}}`
- Generated report delivered via `NotificationService` (requires SMTP config)
- Failed generation retried up to `max_retries`; admin notified on persistent failure

#### Frontend
*As a manager who wants a weekly sales summary emailed every Monday morning, I want a "Schedule" button on the report page that opens a scheduling wizard, so that I can set it up once and receive it automatically.*
- Route: `#/reports/{id}/view` → report viewer page; "Schedule" FlexButton(ghost) in results-area toolbar triggers schedule modal; active schedules shown in "Schedules" FlexTabs tab
- Layout addition (Schedules tab): FlexDataGrid — columns: Schedule Name, Next Run, Recipients, Last Status FlexBadge, Enabled toggle

- `ScheduleModal` FlexModal(size=md):
  - body sections (FlexStack):
    - Frequency: FlexTabs — Daily | Weekly | Monthly | Custom cron (same cron UI as automation rules)
    - Parameters: FlexForm pre-filled from last run; each date param shows Quick Select chips
    - Delivery: Recipients (FlexInput, user-search chips) | Subject (FlexInput) | Format (FlexSelect: PDF / Excel / CSV)
    - Summary: read-only FlexAlert(type=info) — human-readable schedule string (e.g. "Every Monday at 08:00 AM → emailed to 3 recipients as PDF")
  - footer: Cancel FlexButton | "Save Schedule" FlexButton(primary)

- Interactions:
  - click "Schedule": opens ScheduleModal; Summary section updates live as frequency/delivery fields change
  - change frequency tab or any field: Summary text recalculates immediately
  - click "Save Schedule": POST /scheduler/jobs → modal closes; new row appears in Schedules tab; toast "Schedule created"
  - toggle Enabled on schedule row: PATCH /scheduler/jobs/{id} {is_active} → toggle updates

- States:
  - schedules-loading: Schedules tab shows skeleton rows while GET /scheduler/jobs resolves
  - schedules-empty: "No active schedules" + "Create Schedule" FlexButton(primary)
  - saving: "Save Schedule" button shows spinner; form disabled

---

### Story 10.2.2 — Report Job History and Monitoring `[DONE]`

#### Backend
*As an API, I want to return the execution history of scheduled report jobs, so that admins can diagnose delivery failures.*
- `GET /api/v1/scheduler/jobs/{id}/runs` returns `[{status, started_at, completed_at, output, error, duration_ms}]`

#### Frontend
*As a tenant administrator, I want a scheduler monitoring page that lists all scheduled jobs with their last run status and next run time, so that I can quickly spot failures without checking each job individually.*
- Route: `#/scheduler` → `scheduler.html` + `scheduler-page.js`
- Layout: FlexStack(direction=vertical) > page-header, filter-row, jobs-grid
  - page-header: FlexToolbar — "Scheduled Jobs" title
  - filter-row: FlexCluster — "Failed Jobs" FlexButton(chip, toggle) filter
  - jobs-grid: FlexDataGrid(server-side, expandable-rows) — jobs via GET /scheduler/jobs

- `JobsGrid` FlexDataGrid:
  - columns: Job Name (link to report) | Type | Next Run (relative, e.g. "in 3 hours") | Last Run Status (FlexBadge: Success / Failed / Running) | Last Run At
  - failed rows: red border highlight
  - expanded row: error message text block + "History" FlexTabs tab (runs table: Status FlexBadge | Started At | Duration | output/error expandable sub-row)
  - row action: "Run Now" FlexButton(ghost)

- Interactions:
  - click "Failed Jobs" chip: GET /scheduler/jobs?status=failed → grid filters to failed rows only; chip toggles active state
  - click row expand chevron: expanded row reveals error message (failed jobs) or last output
  - click "History" tab in expanded row: GET /scheduler/jobs/{id}/runs → runs table renders
  - click "Run Now": POST /scheduler/jobs/{id}/run → row Last Run Status updates to "Running" FlexBadge

- States:
  - loading: FlexDataGrid shows skeleton rows while jobs fetch
  - empty: "No scheduled jobs configured"
  - empty (failed filter): "No failed jobs" illustration
