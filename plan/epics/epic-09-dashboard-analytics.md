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
- Route: `#/dashboards/new` → `dashboard-designer.html` + `dashboard-designer-page.js`
- Layout: FlexSplitPane(initial-split=25%) > wizard-panel, preview-panel
  - wizard-panel: FlexStack(direction=vertical) > stepper-header, step-content, step-footer
    - stepper-header: FlexStepper(steps=4) — Metadata | Pages | Widgets | Filters
    - step-content: renders per active step (see specs below)
    - step-footer: FlexToolbar — "Save Draft" FlexButton(ghost) | Back FlexButton | Next / Publish FlexButton(primary)
  - preview-panel: FlexContainer(fill) — live dashboard canvas; updates as widgets are added/configured

- `StepMetadata` (Step 1):
  - fields: Dashboard Name (FlexInput, required) | Description (FlexTextarea) | Category (FlexSelect) | Tags (FlexInput, multi-tag) | Theme (FlexRadio: Light / Dark / Auto)

- `StepPages` (Step 2):
  - pages list: FlexStack(gap=sm) — page row per item (FlexInput for rename + delete icon)
  - per page: Layout Type FlexSelect (Grid / Freeform)
  - "+ Add Page" FlexButton(ghost) appends a new page row

- `StepWidgets` (Step 3):
  - sub-layout: FlexSplitPane(initial-split=20%) > widget-palette, canvas
    - widget-palette: FlexStack — draggable widget type cards (KPI, Chart, Table, Text)
    - canvas: FlexContainer(fill) — drop target; placed widgets with resize handles; selected widget opens properties FlexDrawer(position=right, size=sm, overlay=false)

- `StepFilters` (Step 4):
  - filter params list: FlexStack(gap=sm) — add-filter rows (param name + type per row)
  - "+ Add Filter Parameter" FlexButton(ghost)

- Interactions:
  - click Next: FlexStepper advances; step-content swaps to next step
  - drag widget card from palette onto canvas: widget placed at drop position; properties FlexDrawer opens
  - resize widget via handle: widget bounds update live
  - any config change: preview-panel re-renders within 1 second (debounced)
  - click "Save Draft" (any step): POST /dashboards {status: draft} → toast "Dashboard saved"
  - click "Publish" (Step 4): POST /dashboards/{id}/publish → redirect to `#/dashboards/{id}`

- States:
  - step-1-invalid: Next button disabled until Dashboard Name is filled
  - saving: step-footer buttons show spinner; form disabled during save
  - published: redirect to dashboard detail page on successful publish

---

### Story 9.1.2 — KPI Widget Configuration `[DONE]`

#### Backend
*As an API, I want to execute KPI widget queries using the aggregate endpoint and return a single metric value with optional trend comparison, so that KPI cards display live data.*
- Widget `config` JSONB: `{entity_name, metric_field, metric_function, filters?, compare_period?}`
- `POST /api/v1/dashboards/{id}/execute` resolves each widget's config and returns `{widget_id: {value, trend_value, trend_pct}}`

#### Frontend
*As a dashboard designer adding a KPI widget, I want to select an entity, choose a metric field and aggregation function, and immediately see a preview of the number in the widget, so that I can validate my configuration without saving first.*
- Route: `#/dashboards/new` and `#/dashboards/{id}/edit` → dashboard designer; KPI config panel shown in FlexDrawer(position=right, size=sm, overlay=false) when a KPI widget is selected
- Layout: FlexDrawer > config-form, preview-card
  - config-form: FlexForm — entity, metric-field, function, filters, comparison-period, display fields
  - preview-card: FlexCard — large metric value | label below | trend arrow + % FlexBadge (green/red)

- `KPIConfigForm`:
  - Entity (FlexSelect, searchable, published entities only)
  - Metric Field (FlexSelect, filtered to `aggregatable: true` fields from entity metadata)
  - Function (FlexSelect: Sum / Count / Average / Min / Max; auto-selected based on field type)
  - Filters (filter-row builder — same UI as list page)
  - Comparison Period (FlexSelect: Previous period / Previous year / None)
  - Label (FlexInput) | Prefix (FlexInput, e.g. `$`) | Suffix (FlexInput, e.g. `%`) | Decimal Places (FlexInput, type=number, range 0–4)

- Interactions:
  - select Entity: Metric Field options reload from entity metadata
  - select Metric Field: Function auto-selected based on field type
  - change any config field: debounced 1 s → POST /dashboards/{id}/execute → preview-card updates
  - execute returns no value: preview-card shows "—" placeholder

- States:
  - loading-preview: preview-card shows skeleton while execute call resolves
  - no-data: preview-card shows "No data" placeholder
  - error-preview: FlexAlert(type=error, inline) "Could not load preview"

---

### Story 9.1.3 — Chart Widget Configuration `[DONE]`

#### Backend
*As an API, I want to execute chart widget queries using the aggregate endpoint with grouping and optional date-trunc, so that chart widgets display series data.*
- Chart widget `config` JSONB: `{chart_type, entity_name, x_axis_field, y_axis_metric, group_by?, date_trunc?, filters?, refresh_interval?}`
- Execute returns `{labels: [], datasets: [{label, data: []}]}` — compatible with Chart.js format

#### Frontend
*As a dashboard designer adding a chart widget, I want to pick a chart type, configure X and Y axes from a field picker, and see the chart render instantly with live data in the designer preview, so that I can iterate on the visualization quickly.*
- Route: `#/dashboards/new` and `#/dashboards/{id}/edit` → dashboard designer; chart config panel shown in FlexDrawer(position=right, size=sm, overlay=false) when a chart widget is selected
- Layout: FlexDrawer > config-form, chart-preview
  - config-form: FlexForm — chart-type picker, entity, axis fields, group-by, filters, auto-refresh
  - chart-preview: FlexContainer — live chart rendering; "No data" placeholder with sample chart outline if query returns no results

- `ChartConfigForm`:
  - Chart Type (icon-card grid: Bar / Line / Pie / Donut / Area / Scatter / Gauge / Funnel / Heatmap)
  - Entity (FlexSelect, searchable)
  - X Axis (FlexSelect; when date field selected, Date Grouping sub-select appears: Day / Week / Month / Quarter / Year)
  - "Swap X/Y" FlexButton(ghost, icon-only) between axis selects
  - Y Axis (FlexSelect, metric field) + Function FlexSelect (Sum / Count / Average / Min / Max)
  - Group By (FlexSelect, optional second dimension)
  - Filters (filter-row builder)
  - Auto Refresh (FlexSelect: Off / 30s / 1m / 5m / 15m / 30m / 1h)

- Interactions:
  - select Chart Type icon card: chart-preview re-renders with selected chart type
  - select Entity: X Axis and Y Axis options reload from entity metadata
  - select date field for X Axis: Date Grouping sub-select appears
  - click "Swap X/Y": X and Y axis selections swap; chart-preview updates
  - change any config field: debounced → POST /dashboards/{id}/execute → chart-preview re-renders
  - execute returns empty groups: chart-preview shows "No data" placeholder with sample outline

- States:
  - loading-preview: chart-preview shows skeleton spinner
  - no-data: placeholder with sample chart outline + "No data available"
  - error-preview: FlexAlert(type=error, inline) "Could not load chart data"

---

### Story 9.1.4 — Dashboard Sharing and Access Control `[DONE]`

#### Backend
*As an API, I want dashboards to have configurable visibility and per-user/role sharing, so that dashboards can be personal, team-wide, or company-wide.*
- `Dashboard.visibility`: `private` / `tenant` / `company` / `public`
- `dashboard_access` table for per-user or per-role sharing overrides
- RBAC: `dashboards:read:company` to view; `dashboards:write:tenant` to create/edit

#### Frontend
*As a manager who has built a dashboard for my team, I want a Share button that lets me choose visibility and optionally invite specific team members by name, so that I can give my team access without involving the administrator.*
- Route: `#/dashboards/{id}` → dashboard viewer page; "Share" FlexButton(ghost) in page-header toolbar triggers share modal
- Layout (share trigger): FlexToolbar in page-header — dashboard title | "Share" FlexButton(ghost) | Edit FlexButton

- `ShareModal` FlexModal(size=md):
  - body:
    - Visibility (FlexRadio: Private / My Company / All Tenant / Public)
    - "Share with specific people" FlexSection:
      - user search FlexInput — typeahead results → select adds chip
      - chips: user name + "View only" label + × remove
    - Current access list: FlexStack(gap=xs) — one row per user showing name + access level FlexBadge + × revoke
  - footer: "Copy link" FlexButton(ghost) | Cancel FlexButton | Save FlexButton(primary)

- Interactions:
  - click "Share": opens ShareModal; GET /dashboards/{id}/access → access list populates
  - type in user search input: typeahead matches users → click result adds chip to pending share list
  - click × on pending chip: removes chip before save
  - click × revoke on access-list row: DELETE /dashboards/{id}/access/{user_id} → row removed immediately
  - click "Copy link": copies dashboard URL to clipboard → button label changes to "Copied ✓" for 3 s
  - click "Save": PUT /dashboards/{id} {visibility, shared_users} → modal closes; toast "Sharing updated"

- States:
  - loading (access list): skeleton rows while GET /dashboards/{id}/access resolves
  - no-shares: "Only you have access" message below current access list

---

## Feature 9.2 — Dashboard Interactivity `[DONE]`

### Story 9.2.1 — Global Filter Panel `[DONE]`

#### Backend
*As an API, I want dashboard execution to accept global filter parameters that override widget-level filters, so that a single filter panel controls all widgets.*
- `POST /api/v1/dashboards/{id}/execute` accepts `{global_filters: {param_name: value, ...}}`
- Global filters merged with widget-level filters before query execution

#### Frontend
*As a dashboard viewer, I want a filter bar at the top of the dashboard where I can select a date range and dimension values, and see all charts and KPIs update simultaneously, so that I can do ad-hoc analysis without opening individual widget settings.*
- Route: `#/dashboards/{id}` → dashboard viewer page; filter bar rendered at top when dashboard has global filter parameters defined
- Layout: FlexStack(direction=vertical) > filter-bar, active-chips-row, widget-grid
  - filter-bar: FlexCluster — From / To FlexDatepicker | preset chips (Today / This Week / This Month / This Quarter) | one FlexSelect per dimension parameter | "Apply Filters" FlexButton(primary) | "Clear All" FlexButton(ghost)
  - active-chips-row: FlexCluster — FlexBadge chip per active filter + × remove; hidden when no filters are active
  - widget-grid: dashboard widget canvas

- Interactions:
  - click preset chip (Today / This Week / etc.): date range inputs populate with preset values
  - click "Apply Filters": POST /dashboards/{id}/execute {global_filters} → widget-grid shows loading skeleton → widgets re-render; URL updated with `?filters=...`
  - click × on active chip: removes that filter; execute fires automatically with remaining filters
  - click "Clear All": all filter inputs reset; active-chips-row clears; URL `?filters` param removed; widgets re-fetch unfiltered

- States:
  - loading (after apply): all widgets show skeleton cards simultaneously during fetch
  - no-filters-defined: filter-bar and active-chips-row not rendered
  - url-restored: on page load with `?filters=...` in URL, inputs pre-populated and execute fires immediately

---

### Story 9.2.2 — Widget Drill-Down `[DONE]`

#### Backend
*As an API, I want drill-down to return the underlying records matching a widget's segment filters, so that users can investigate aggregated data.*
- Clicking a chart segment or KPI sends the segment's filter values to `GET /dynamic-data/{entity}/records` with those filters applied
- Response is the standard paginated record list

#### Frontend
*As a dashboard viewer who sees an unexpected spike in a chart bar, I want to click that bar and see the actual records that make up that data point in a side drawer, so that I can investigate without leaving the dashboard.*
- Route: `#/dashboards/{id}` → dashboard viewer; drill-down FlexDrawer triggered by clicking a widget data point
- Layout: FlexDrawer(position=right, size=md, overlay=true) > drill-down-header, drill-down-body
  - drill-down-header: FlexToolbar — segment label (e.g. "Status: Submitted — 47 records") | "Export these records" FlexButton(ghost) | × close
  - drill-down-body: FlexDataGrid(server-side) — records from GET /dynamic-data/{entity}/records with segment filters applied

- `DrillDownGrid` FlexDataGrid:
  - columns: auto-generated from entity field definitions
  - search: FlexInput above grid
  - pagination: server-side
  - row action: "View" icon → opens record detail in new browser tab

- Interactions:
  - hover chart bar / slice / point or KPI value: cursor changes to pointer
  - click chart bar / slice / point or KPI value: FlexDrawer opens; GET /dynamic-data/{entity}/records with segment filters → grid loads
  - click "Export these records": GET /dynamic-data/{entity}/records?format=csv (segment filters applied) → CSV download
  - click "View" on grid row: opens `#/dynamic/{entity}/{id}` in new browser tab
  - click × or click outside drawer: drawer closes

- States:
  - loading: FlexDataGrid shows skeleton rows while records fetch
  - empty: "No records match this segment"
  - error: FlexAlert(type=error) "Could not load records. Retry?"

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
- Route: `#/dashboards/{id}` → dashboard viewer page; materialized-view controls shown in page-header when any widget uses a virtual entity
- Layout addition: FlexToolbar in page-header — (existing controls) | "Data as of [timestamp]" FlexBadge(color=neutral) | "Refresh Data" FlexButton(ghost)

- Interactions:
  - click "Refresh Data": POST /procedures/refresh/{view_name} → "Refresh Data" button shows spinner; all widgets show skeleton overlay; on completion timestamp FlexBadge updates to new timestamp; widgets re-fetch and re-render

- States:
  - refreshing: "Refresh Data" button disabled + spinner; widgets show skeleton overlay
  - refreshed: timestamp FlexBadge shows updated time; "Refresh Data" button re-enabled
  - designer-mode: virtual entity widget headers show FlexBadge(color=neutral) "Materialized View" label
