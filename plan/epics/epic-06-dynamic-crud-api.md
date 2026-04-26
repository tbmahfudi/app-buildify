# Epic 6 — Dynamic CRUD & API Layer

> Auto-generated REST API for all published entities with filtering, sorting, searching, pagination, aggregation, and bulk operations.

---

## Feature 6.1 — Standard CRUD Operations `[DONE]`

### Story 6.1.1 — Record Create, Read, Update, Delete `[DONE]`

#### Backend
*As an API, I want auto-generated CRUD endpoints for every published entity, so that record management works immediately after entity publication.*
- `POST /api/v1/dynamic-data/{entity}/records` — validates against field definitions, creates record, returns created object
- `GET /api/v1/dynamic-data/{entity}/records/{id}` — single record; 404 if not found or soft-deleted
- `PUT /api/v1/dynamic-data/{entity}/records/{id}` — partial update; calculated/system fields ignored
- `DELETE /api/v1/dynamic-data/{entity}/records/{id}` — hard or soft delete per entity config
- List response envelope: `{items: [], total: N, page: 1, page_size: 20, pages: N}`

#### Frontend
*As a user working with a custom entity, I want auto-generated list, create, edit, and detail pages that feel consistent across all entities, so that I can manage custom data without any custom development.*
- Routes (auto-registered by `dynamic-route-registry.js` per published entity):
  - `#/dynamic/{entity}/list` — list page
  - `#/dynamic/{entity}/create` — create page
  - `#/dynamic/{entity}/{id}` — detail page
  - `#/dynamic/{entity}/{id}/edit` — edit page

- Layout (list page): FlexStack(direction=vertical) > page-header, content-area
  - page-header: FlexToolbar — "[Entity Label]" title | "New [Entity Label]" FlexButton(primary)
  - content-area: FlexDataGrid(server-side, columns auto-generated from table_config metadata) — action column: Edit | View | Delete icons per row

- Layout (create/edit page): FlexStack(direction=vertical) > form-body, sticky-footer
  - form-body: FlexForm — fields auto-generated from FieldDefinition list; field type → widget (FlexInput, FlexSelect, FlexDatepicker…); required fields marked *
  - sticky-footer: FlexToolbar — Cancel | Save [Entity Label] (primary, spinner on submit)

- Layout (detail page): FlexStack(direction=vertical) > detail-header, field-values, related-section
  - detail-header: FlexToolbar — FlexBreadcrumb | "Edit" FlexButton | "Delete" FlexButton(danger)
  - field-values: FlexGrid(columns=2) — label + value per field (read-only)
  - related-section: FlexSection — "Related Records" (shown only if entity has relationship fields)

- Interactions:
  - click "New [Entity Label]": navigates to create page
  - click Edit on row / "Edit" in detail header: navigates to edit page
  - click View on row: navigates to detail page
  - click Delete on row: opens confirm FlexModal(size=sm) → DELETE /dynamic-data/{entity}/records/{id}
  - submit create/edit form: POST or PUT /dynamic-data/{entity}/records → on success redirect to detail page

- States:
  - loading (list): FlexDataGrid shows skeleton rows
  - empty (list): illustration + "No [Entity Label] found" + "Create the first one" FlexButton(primary)
  - error (list): FlexAlert(type=error) "Could not load records. Retry?"

---

### Story 6.1.2 — Filtering, Sorting, Searching, Pagination `[DONE]`

#### Backend
*As an API, I want flexible query parameters for filtering, sorting, searching, and paginating entity records, so that UIs can display large datasets efficiently.*
- `?filters={"operator":"AND","conditions":[{"field":"status","operator":"eq","value":"active"}]}` — structured filter JSON
- `?sort_by=created_at&sort_order=desc` — column sort; defaults to entity's `default_sort_field`
- `?search=acme` — full-text search across entity's `searchable_fields`
- `?page=1&page_size=20` — pagination; max `page_size` configurable (default 100)

#### Frontend
*As a user on a dynamic entity list page, I want a filter bar above the table where I can add multiple filters, search by keyword, and sort by any column header click, so that finding records in large datasets is fast.*
- Route: `#/dynamic/{entity}/list` — extends the list page layout from Story 6.1.1

- FlexDrawer(position=right, size=sm) — filter panel, triggered by "Filters" button
  - AND/OR FlexRadio toggle at top
  - filter rows: Field (FlexSelect) | Operator (FlexSelect: equals/contains/greater than/…) | Value (FlexInput or FlexSelect)
  - "Add Filter" FlexButton(ghost) appends a new row
  - footer: Reset Filters | Apply Filters (primary)

- Interactions:
  - type in search input: debounced 300ms → GET /dynamic-data/{entity}/records?search=[term] → grid refreshes
  - click "Filters" button: opens filter FlexDrawer; badge shows active filter count
  - click "Apply Filters": updates URL query string (bookmarkable) + GET with structured filters JSON → grid refreshes
  - click "Reset Filters": clears all filters; URL cleared; grid returns to default view
  - click column header: toggles sort asc/desc (↑ ↓ icon); GET with sort_by + sort_order → grid refreshes
  - FlexPagination page change: GET /dynamic-data/{entity}/records?page=N → grid refreshes; "Showing X–Y of Z results" updates

---

### Story 6.1.3 — Structured Validation Error Responses `[IN-PROGRESS]`

#### Backend
*As an API, I want to return per-field validation errors in a structured format, so that UIs can highlight exactly which fields are invalid.*
- On 400 validation failure: `{"detail": "Validation failed", "errors": [{"field": "email", "message": "Email is required"}, ...]}`
- All validation paths (`_validate_and_prepare_data`, Pydantic, FK checks) must populate the `errors` array

#### Frontend
*As a user filling out a create/edit form, I want validation errors to appear directly below the relevant field with a red border and descriptive message immediately after I click Save, so that I know exactly what to fix.*
- Route: `#/dynamic/{entity}/create` and `#/dynamic/{entity}/{id}/edit` — extends create/edit pages from Story 6.1.1

- Interactions:
  - submit form → 400 response: `saveRecord()` calls `form.showFieldErrors(errors[])` — each errored FlexInput/FlexSelect gets red border + error message below; first errored field scrolled into view
  - non-field error (e.g. unique constraint): FlexAlert(type=error) banner at top of form with the error message
  - re-submit: all previous error states cleared before new validation runs

- States:
  - field-error: red border + red message text below the input
  - form-error: FlexAlert(type=error) banner above form fields

---

## Feature 6.2 — Aggregation API `[DONE]`

### Story 6.2.1 — Server-Side GROUP BY Analytics `[DONE]`

#### Backend
*As an API, I want a dedicated aggregate endpoint that runs server-side GROUP BY queries, so that dashboards can display KPIs and charts without fetching all records.*
- `GET /api/v1/dynamic-data/{entity}/aggregate?group_by=status&metrics=[{"field":"amount","function":"sum","alias":"total"}]`
- Supported functions: `count`, `sum`, `avg`, `min`, `max`, `count_distinct`; `COUNT(*)` via `field="*"`
- `date_trunc` + `date_field` parameters enable time-series grouping
- Org-scope isolation applied identically to `list_records`
- Response: `{groups: [{group_value, metrics: {alias: value}}, ...], total_groups: N}`

#### Frontend
*As a developer building a custom widget, I want a `DataService.aggregate()` method that I can call with group-by and metric config, and get back structured data ready to feed into a chart component, so that I can build analytics without writing raw API calls.*
- No dedicated route — `DataService.aggregate()` is a shared service used by dashboard widgets and chart builders

- Interactions:
  - widget config save: calls `DataService.aggregate(entityName, groupBy, metrics, filters, dateTrunc)` → GET /dynamic-data/{entity}/aggregate → parsed results fed to chart component
  - aggregate returns empty groups: widget renders "No data available" state with chart placeholder illustration

- States:
  - loading: chart area shows skeleton / spinner while aggregate call resolves
  - empty: illustration + "No data available for the selected filters"
  - error: FlexAlert(type=error) "Could not load chart data" within the widget frame

---

### Story 6.2.2 — Aggregation Hints in Entity Metadata `[OPEN]`

#### Backend
*As an API, I want entity metadata to include `table_config` with per-field aggregation hints, so that UIs can auto-populate axis and metric selectors for chart builders.*
- `table_config` JSONB: `{columns: [{field, label, visible, sortable, filterable, aggregatable, aggregate_functions, format, width}]}`
- `aggregatable: true` and `aggregate_functions` auto-populated for numeric field types
- `format` auto-derived: `"currency"` if field has a `$` prefix, `"percentage"` if `%` suffix

#### Frontend
*As a dashboard designer selecting a metric for a KPI widget, I want the field picker to show only aggregatable fields and auto-suggest the most relevant aggregate function for each, so that I can set up a widget in under 30 seconds.*
- Route: dashboard designer widget config panel (see Epic 9)

- Interactions:
  - open "Metric" field picker in widget config: list filtered to fields where `aggregatable: true` only
  - hover a metric field in picker: shows recommended functions (e.g. "Amount → sum, avg, min, max")
  - select a field: aggregate function auto-selected (sum for currency fields, count for ID fields)
  - any config change: widget preview panel updates immediately showing value with correct format (e.g. "$12,450" vs "12,450")

---

## Feature 6.3 — Bulk Operations `[OPEN]`

### Story 6.3.1 — Bulk Create (CSV Import) `[OPEN]`

#### Backend
*As an API, I want a bulk create endpoint that accepts an array of records in a single transaction, so that data migration is efficient.*
- `POST /api/v1/dynamic-data/{entity}/records/bulk` accepts `{"records": [...]}`; runs all validations in a loop; creates all in one DB transaction
- Partial success: `{created: N, failed: M, errors: [{row: N, field: "x", message: "..."}]}`
- Limited to 1000 records per request; larger payloads return 400 with `BATCH_TOO_LARGE`

#### Frontend
*As a tenant administrator on an entity list page, I want to click "Import CSV", map my CSV columns to entity fields in a preview table, and see a progress bar and import summary after uploading, so that data migration from spreadsheets is self-service.*
- Route: `#/dynamic/{entity}/list` — "Import" FlexButton in toolbar (shown only if user has `create` permission)

- FlexModal(size=lg) — CSV import wizard, triggered by "Import" button
  - FlexStepper(steps=3):
    - Step 1 "Upload": FlexFileUpload drag-drop (CSV only) | CSV preview table showing first 5 rows
    - Step 2 "Map Columns": two-column table — CSV header (left) | entity field FlexSelect (right); auto-maps when header name matches field name
    - Step 3 "Import": FlexProgress bar during POST /dynamic-data/{entity}/records/bulk | results summary "X records created, Y failed" | "Download failed rows" FlexButton (CSV with Error column appended)
  - footer: Cancel (any step, closes without importing) | Next / Import (primary)

- Interactions:
  - drop or select CSV file (Step 1): parse headers + preview first 5 rows in table
  - click "Next" (Step 1 → Step 2): render column mapping table; auto-map matching names
  - change field FlexSelect in mapping (Step 2): live updates which entity field that column maps to
  - click "Import" (Step 3): POST bulk → FlexProgress fills; results shown on completion
  - click "Download failed rows": generates CSV download of only failed rows with appended Error column

---

### Story 6.3.2 — Bulk Update and Bulk Delete `[OPEN]`

#### Backend
*As an API, I want bulk update and delete endpoints, so that batch operations on many records are performant.*
- `PUT /api/v1/dynamic-data/{entity}/records/bulk` accepts `{"records": [{id, ...fields}]}` — validates and updates each
- `DELETE /api/v1/dynamic-data/{entity}/records/bulk` accepts `{"ids": [...]}` — soft or hard deletes each
- Both operations audit-logged with `{action: "bulk_update", count: N}` and `{action: "bulk_delete", ids: [...]}`

#### Frontend
*As a user on an entity list page, I want to select multiple rows using checkboxes and then choose a bulk action (delete or field update) from a toolbar that appears when rows are selected, so that I can make batch corrections without opening each record.*
- Route: `#/dynamic/{entity}/list` — bulk action toolbar appears above FlexDataGrid when ≥1 row selected

- FlexDataGrid — checkbox column enabled for row selection
  - bulk action toolbar (visible when rows selected): "X selected" | "Deselect All" link | "Delete Selected" FlexButton(danger) | "Update Field" FlexButton

- FlexModal(size=sm) — bulk delete confirm
  - body: "Delete X records? This cannot be undone."
  - footer: Cancel | Delete (FlexButton, variant=danger)
  - on confirm: DELETE /dynamic-data/{entity}/records/bulk → selected rows fade out; toast "X records deleted"

- FlexModal(size=sm) — bulk update field
  - fields: Field (FlexSelect, entity fields) | New Value (FlexInput or FlexSelect, type depends on field)
  - footer: Cancel | Update X Records (primary)
  - on confirm: PUT /dynamic-data/{entity}/records/bulk → affected rows update in place; toast "X records updated"

- Interactions:
  - check row checkbox: adds to selection; bulk toolbar appears
  - click "Deselect All": clears selection; bulk toolbar hides
  - click "Delete Selected": opens bulk delete confirm FlexModal
  - click "Update Field": opens bulk update FlexModal
  - select Field in update modal: New Value input adapts to the field's type
