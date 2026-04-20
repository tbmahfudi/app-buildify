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
- Route: `#/reports/new` renders `report-designer.html` + `report-designer-page.js`
- 6-step `FlexStepper` wizard with a live preview panel on the right (split-pane)
- **Step 1 — Metadata**: Report Name, Description, Category, Report Type (Tabular / Summary / Chart / Cross-Tab)
- **Step 2 — Data Source**: Entity selector (all published entities + module entities); optional join configuration panel for joining a second entity
- **Step 3 — Query**: Filter builder (same as list page filters) + Sort By + Group By (for summary reports)
- **Step 4 — Columns**: Drag-and-drop column selector — available fields on left, selected columns on right; each selected column has: Label, Format, Aggregation function, Width, Visible toggle
- **Step 5 — Parameters**: "Add Parameter" button opens a parameter type picker; each parameter shows: Name, Label, Type, Default Value, Required toggle
- **Step 6 — Visualization**: For chart reports — Chart Type picker + axis mapping; for tabular — column width/alignment tweaks; for summary — subtotal configuration
- "Preview" button in each step fetches sample data and renders the report in the right panel

---

### Story 10.1.2 — Report Parameters `[DONE]`

#### Backend
*As an API, I want report parameters to be defined on the report definition and accepted at execution time, so that one report definition serves multiple use cases.*
- Parameter types: `string`, `integer`, `decimal`, `date`, `datetime`, `boolean`, `lookup`, `multi_select`
- `POST /api/v1/reports/{id}/run` accepts `{parameters: {param_name: value, ...}}`
- Date parameters: supports relative values `today`, `this_week`, `this_month`, `last_30_days` resolved server-side

#### Frontend
*As a user running a parameterized report, I want to see a clean parameter input form with appropriate controls for each parameter type, and be able to select relative date ranges like "This Month" without knowing specific dates, so that running reports is fast and intuitive.*
- Report viewer page `#/reports/{id}/view` renders `report-viewer.js`
- Before showing results, if the report has parameters: a "Run Report" panel appears at the top with a form field per parameter
- Parameter field types → UI controls:
  - `date` / `datetime` → `FlexDatepicker`
  - `lookup` → searchable `FlexSelect` (loads lookup options)
  - `multi_select` → multi-select `FlexSelect`
  - `boolean` → toggle switch
  - `string` / `integer` / `decimal` → `FlexInput`
- Date parameters show a "Quick Select" chip bar: Today / Yesterday / This Week / This Month / Last 30 Days / This Quarter / This Year
- "Run Report" button at the bottom of the parameter form; results replace the panel with the report output
- "Change Parameters" link at the top of results opens the parameter form again

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
- Report viewer toolbar shows an "Export" split button: default action "Export as Excel"; dropdown options: PDF / Excel (formatted) / Excel (raw) / CSV / JSON
- Clicking an option calls the export endpoint; for small reports: file download starts in the browser immediately (`Content-Disposition: attachment`)
- For large reports (async): a `FlexAlert` banner appears: "Your export is being prepared. We'll notify you when it's ready."
- Export ready: in-app notification appears in the notification bell; clicking downloads the file
- Export history panel accessible via "Past Exports" link — shows format, timestamp, download button (expires after 24 hours)

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
- Report viewer toolbar has a "Schedule" button
- Clicking opens a `FlexModal` scheduling wizard:
  - **Frequency**: same cron UI as automation rules (Daily / Weekly / Monthly / Custom cron)
  - **Parameters**: pre-filled from the last run; adjustable (e.g. "Always use 'This Week' date range")
  - **Delivery**: Email recipients input (comma-separated or user-search chips), Subject line, Format select (PDF/Excel/CSV)
  - **Summary**: human-readable "This report will run every Monday at 8:00 AM and be emailed to 3 recipients as a PDF"
- "Save Schedule" button creates the scheduler job
- Active schedules listed on the report page in a "Schedules" tab: schedule name, next run, recipients, last status, toggle to enable/disable

---

### Story 10.2.2 — Report Job History and Monitoring `[DONE]`

#### Backend
*As an API, I want to return the execution history of scheduled report jobs, so that admins can diagnose delivery failures.*
- `GET /api/v1/scheduler/jobs/{id}/runs` returns `[{status, started_at, completed_at, output, error, duration_ms}]`

#### Frontend
*As a tenant administrator, I want a scheduler monitoring page that lists all scheduled jobs with their last run status and next run time, so that I can quickly spot failures without checking each job individually.*
- Route: `#/scheduler` renders `scheduler.html`
- Table columns: Job Name (linked to the report), Type, Next Run (relative: "in 3 hours"), Last Run Status (Success / Failed / Running), Last Run At
- "Failed" status rows highlighted in red; clicking the row expands a detail section showing the error message
- "Run Now" button on each row triggers an immediate execution (for testing)
- Per-job "History" tab: table of all runs with status and duration; expandable rows show output/error
- Global "Failed Jobs" filter chip at the top to quickly surface all failing schedules
