# Epic 9 — Dashboard & Analytics

> Visual dashboard builder with KPI cards, charts, report tables, and live data from any published entity or module.

---

## Feature 9.1 — Dashboard Builder `[DONE]`

### Story 9.1.1 — Dashboard Creation and Layout `[DONE]`

#### Backend
*As an API, I want to persist dashboard configurations with pages and widget layouts, so that custom dashboards survive page reloads.*
- `POST /api/v1/dashboards` accepts `{name, layout_type, theme, category?, tags?}`
- Dashboard supports multiple pages: `POST /api/v1/dashboards/{id}/pages`
- Widget layout stored as JSONB per page: `{widgets: [{widget_id, x, y, w, h}]}`

#### Frontend
*As a tenant administrator opening the dashboard designer, I want a 4-step wizard that takes me through naming, adding pages, placing widgets, and setting global filters, so that creating a dashboard feels structured and not overwhelming.*
- Route: `#/dashboards/new` renders `dashboard-designer.html` + `dashboard-designer-page.js`
- 4-step `FlexStepper` wizard in the left panel; live preview in the right panel (split-pane layout)
- **Step 1 — Metadata**: Dashboard Name, Description, Category, Tags, Theme (Light/Dark/Auto)
- **Step 2 — Pages**: list of pages with add/rename/delete; each page has a layout type selector (Grid / Freeform)
- **Step 3 — Widgets**: widget palette on the left; drag to canvas to place; resize handles on placed widgets; selected widget properties in a right panel
- **Step 4 — Filters**: global filter configuration — add filter parameters that cascade to all widgets
- "Save Draft" at any step; "Publish" button on Step 4 activates the dashboard
- Live preview updates in real time as widgets are added/configured

---

### Story 9.1.2 — KPI Widget Configuration `[DONE]`

#### Backend
*As an API, I want to execute KPI widget queries using the aggregate endpoint and return a single metric value with optional trend comparison, so that KPI cards display live data.*
- Widget `config` JSONB: `{entity_name, metric_field, metric_function, filters?, compare_period?}`
- `POST /api/v1/dashboards/{id}/execute` resolves each widget's config and returns `{widget_id: {value, trend_value, trend_pct}}`

#### Frontend
*As a dashboard designer adding a KPI widget, I want to select an entity, choose a metric field and aggregation function, and immediately see a preview of the number in the widget, so that I can validate my configuration without saving first.*
- KPI widget config panel (right panel of designer when a KPI widget is selected):
  - Entity: searchable select (only published entities)
  - Metric Field: select filtered to `aggregatable: true` fields from entity metadata
  - Function: select (Sum / Count / Average / Min / Max) — auto-selected based on field type
  - Filters: add-filter row builder (same UI as list page filters)
  - Comparison Period: select (Previous period / Previous year / None)
  - Display: Label input, Prefix (e.g. `$`), Suffix (e.g. `%`), Decimal Places (0–4)
- Preview KPI card updates within 1 second of any config change (debounced API call)
- Preview shows: large metric value, label below, trend arrow + % change (green/red)

---

### Story 9.1.3 — Chart Widget Configuration `[DONE]`

#### Backend
*As an API, I want to execute chart widget queries using the aggregate endpoint with grouping and optional date-trunc, so that chart widgets display series data.*
- Chart widget `config` JSONB: `{chart_type, entity_name, x_axis_field, y_axis_metric, group_by?, date_trunc?, filters?, refresh_interval?}`
- Execute returns `{labels: [], datasets: [{label, data: []}]}` — compatible with Chart.js format

#### Frontend
*As a dashboard designer adding a chart widget, I want to pick a chart type, configure X and Y axes from a field picker, and see the chart render instantly with live data in the designer preview, so that I can iterate on the visualization quickly.*
- Chart widget config panel:
  - Chart Type: visual icon picker grid (Bar, Line, Pie, Donut, Area, Scatter, Gauge, Funnel, Heatmap)
  - Entity: searchable select
  - X Axis: field select (date fields show a "Date grouping" sub-select: Day/Week/Month/Quarter/Year)
  - Y Axis: metric field + function (same as KPI)
  - Group By: optional second dimension for grouped/stacked charts
  - Filters: add-filter builder
  - Auto Refresh: select (Off / 30s / 1m / 5m / 15m / 30m / 1h)
- Chart preview renders using live data; a "No data" placeholder with a sample chart outline shown if the query returns no results
- "Swap X/Y" button for quick axis transposition

---

### Story 9.1.4 — Dashboard Sharing and Access Control `[DONE]`

#### Backend
*As an API, I want dashboards to have configurable visibility and per-user/role sharing, so that dashboards can be personal, team-wide, or company-wide.*
- `Dashboard.visibility`: `private` / `tenant` / `company` / `public`
- `dashboard_access` table for per-user or per-role sharing overrides
- RBAC: `dashboards:read:company` to view; `dashboards:write:tenant` to create/edit

#### Frontend
*As a manager who has built a dashboard for my team, I want a Share button that lets me choose visibility and optionally invite specific team members by name, so that I can give my team access without involving the administrator.*
- Dashboard detail page `#/dashboards/{id}` has a "Share" button in the header
- Share modal: Visibility radio (Private / My Company / All Tenant / Public) + "Share with specific people" section
- "Share with specific people": user search input → add as chip; each chip has a permission level select (View only)
- Current share list shows all people with access + their access level + revoke (×) button
- "Copy link" button copies the dashboard URL to clipboard; link only works for users who have access

---

## Feature 9.2 — Dashboard Interactivity `[DONE]`

### Story 9.2.1 — Global Filter Panel `[DONE]`

#### Backend
*As an API, I want dashboard execution to accept global filter parameters that override widget-level filters, so that a single filter panel controls all widgets.*
- `POST /api/v1/dashboards/{id}/execute` accepts `{global_filters: {param_name: value, ...}}`
- Global filters merged with widget-level filters before query execution

#### Frontend
*As a dashboard viewer, I want a filter bar at the top of the dashboard where I can select a date range and dimension values, and see all charts and KPIs update simultaneously, so that I can do ad-hoc analysis without opening individual widget settings.*
- Dashboards with global filters render a filter bar at the top (below the dashboard name)
- Filter bar components rendered from the dashboard's parameter definitions:
  - Date Range: two date pickers (From / To) or preset chips (Today / This Week / This Month / This Quarter)
  - Dimension: one `FlexSelect` per dimension parameter
- Applying filters: "Apply Filters" button re-fetches all widget data; a loading skeleton shown during fetch
- Active filters shown as chips below the filter bar with × to remove individual ones; "Clear All" button
- Filter state persisted in the URL (`?filters=...`) so filtered dashboards can be bookmarked and shared

---

### Story 9.2.2 — Widget Drill-Down `[DONE]`

#### Backend
*As an API, I want drill-down to return the underlying records matching a widget's segment filters, so that users can investigate aggregated data.*
- Clicking a chart segment or KPI sends the segment's filter values to `GET /dynamic-data/{entity}/records` with those filters applied
- Response is the standard paginated record list

#### Frontend
*As a dashboard viewer who sees an unexpected spike in a chart bar, I want to click that bar and see the actual records that make up that data point in a side drawer, so that I can investigate without leaving the dashboard.*
- Chart bars/slices/points and KPI values are clickable (cursor changes to pointer on hover)
- Clicking opens a `FlexDrawer` from the right: header shows the segment label (e.g. "Status: Submitted — 47 records")
- Drawer body: `FlexDataGrid` table with the records; pagination, sorting, and search controls
- Each row has a "View" icon that opens the full record detail in a new browser tab
- Drawer has a "Export these records" button that downloads the filtered records as CSV

---

## Feature 9.3 — Materialized Views and Performance `[DONE]`

### Story 9.3.1 — Materialized View Support `[DONE]`

#### Backend
*As an API, I want to support virtual entities backed by materialized views, so that pre-aggregated data can power fast dashboard queries.*
- Virtual entity with `table_name = mv_name` queries the materialized view instead of a base table
- `ProcedureService.refresh_materialized_view(view_name, concurrently=False)` available for manual and scheduled refresh
- Scheduler job type `data_sync` can trigger a materialized view refresh on a schedule

#### Frontend
*As a tenant administrator managing a high-traffic dashboard, I want to see when the materialized view behind a widget was last refreshed and manually trigger a refresh, so that I can balance data freshness against query performance.*
- Dashboard viewer page header shows: "Data as of [timestamp]" label for dashboards backed by materialized views
- "Refresh Data" button calls the scheduler or procedure service to refresh the materialized view
- While refreshing: button shows a spinner; when done, the timestamp updates and all widgets re-fetch
- In the dashboard designer, virtual entity widgets show a "Materialized View" badge in the widget header so it's clear they use cached data
