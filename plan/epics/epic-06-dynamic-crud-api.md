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
- `dynamic-route-registry.js` auto-registers 4 routes per published entity: `#/dynamic/{entity}/list`, `#/dynamic/{entity}/create`, `#/dynamic/{entity}/{id}`, `#/dynamic/{entity}/{id}/edit`
- **List page**: `FlexDataGrid` table with columns auto-generated from `table_config` metadata; action column with Edit / View / Delete icons per row; "New [Entity Label]" button in the page header
- **Create/Edit page**: `FlexForm` with fields auto-generated from `FieldDefinition` list; field type determines widget (`FlexInput`, `FlexSelect`, `FlexDatepicker`, etc.); Required fields marked with *; Submit and Cancel buttons in a sticky footer
- **Detail page**: read-only card layout with field labels and values; "Edit" and "Delete" buttons in header; "Related Records" section if the entity has relationship fields
- Empty state on list page: illustration + "No [Entity Label] found" + "Create the first one" button

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
- List page toolbar: search input (magnifying glass icon, queries `?search=`), "Filters" button showing a filter count badge, Sort controls
- "Filters" button opens a filter drawer with: field selector (select), operator selector (equals / contains / greater than / etc.), value input; multiple filters can be added as rows; "AND/OR" toggle between filters
- Applying filters updates the URL query string so filtered views are bookmarkable
- Column headers in the table are clickable to sort; active sort column shows an arrow icon (↑ ↓)
- Pagination: `FlexPagination` component at the bottom; "Showing X–Y of Z results" text beside it
- "Reset Filters" button clears all active filters and returns to default view

---

### Story 6.1.3 — Structured Validation Error Responses `[IN-PROGRESS]`

#### Backend
*As an API, I want to return per-field validation errors in a structured format, so that UIs can highlight exactly which fields are invalid.*
- On 400 validation failure: `{"detail": "Validation failed", "errors": [{"field": "email", "message": "Email is required"}, ...]}`
- All validation paths (`_validate_and_prepare_data`, Pydantic, FK checks) must populate the `errors` array

#### Frontend
*As a user filling out a create/edit form, I want validation errors to appear directly below the relevant field with a red border and descriptive message immediately after I click Save, so that I know exactly what to fix.*
- `entity-manager.js` `saveRecord()` catches the 400 response and calls `form.showFieldErrors(error.errors)`
- `showFieldErrors()` iterates `errors[]`, finds the matching `FlexInput`/`FlexSelect` by `name`, and sets its `error` attribute to the message
- Fields with errors: red border, red error text below the input, field scrolled into view if off-screen
- General non-field errors (e.g. "Unique constraint violated") shown in a `FlexAlert` banner at the top of the form
- On re-submit: previous error states cleared before new validation runs

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
- `data-service.js` exposes `aggregate(entityName, groupBy, metrics, filters, dateTrunc)` which calls `GET /dynamic-data/{entity}/aggregate` and returns parsed results
- Widget configuration UI (in the dashboard designer) uses this service as the data source
- Empty aggregate response (no groups returned) causes the widget to show an "No data available" state with a chart placeholder illustration

---

### Story 6.2.2 — Aggregation Hints in Entity Metadata `[OPEN]`

#### Backend
*As an API, I want entity metadata to include `table_config` with per-field aggregation hints, so that UIs can auto-populate axis and metric selectors for chart builders.*
- `table_config` JSONB: `{columns: [{field, label, visible, sortable, filterable, aggregatable, aggregate_functions, format, width}]}`
- `aggregatable: true` and `aggregate_functions` auto-populated for numeric field types
- `format` auto-derived: `"currency"` if field has a `$` prefix, `"percentage"` if `%` suffix

#### Frontend
*As a dashboard designer selecting a metric for a KPI widget, I want the field picker to show only aggregatable fields and auto-suggest the most relevant aggregate function for each, so that I can set up a widget in under 30 seconds.*
- Dashboard widget config panel: "Metric" field picker filters to only fields where `aggregatable: true`
- Each metric field in the picker shows recommended functions (e.g. "Amount → sum, avg, min, max" vs. "Count → count")
- Selecting a field auto-selects the most common function (`sum` for currency, `count` for IDs)
- Format preview: widget preview panel shows the value with the correct format (e.g. "$12,450" vs. "12,450")

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
- "Import" button in the entity list page toolbar (only shown if user has `create` permission)
- Clicking opens a 3-step `FlexStepper` modal:
  - Step 1: File upload (`FlexFileUpload` drag-drop); CSV preview table shows first 5 rows
  - Step 2: Column mapping — left column shows CSV headers, right column shows entity fields (select per row); auto-maps when column name matches field name
  - Step 3: Import summary after submission — `FlexProgress` bar during upload; results: "X records created, Y failed"; failed rows downloadable as a CSV with an "Error" column appended
- "Cancel" at any step closes the modal without importing

---

### Story 6.3.2 — Bulk Update and Bulk Delete `[OPEN]`

#### Backend
*As an API, I want bulk update and delete endpoints, so that batch operations on many records are performant.*
- `PUT /api/v1/dynamic-data/{entity}/records/bulk` accepts `{"records": [{id, ...fields}]}` — validates and updates each
- `DELETE /api/v1/dynamic-data/{entity}/records/bulk` accepts `{"ids": [...]}` — soft or hard deletes each
- Both operations audit-logged with `{action: "bulk_update", count: N}` and `{action: "bulk_delete", ids: [...]}`

#### Frontend
*As a user on an entity list page, I want to select multiple rows using checkboxes and then choose a bulk action (delete or field update) from a toolbar that appears when rows are selected, so that I can make batch corrections without opening each record.*
- `FlexTable` checkbox column enables row selection; selecting any row shows the bulk action toolbar above the table
- Bulk action toolbar: "X selected" count, "Deselect All" link, action buttons: "Delete Selected" and "Update Field"
- "Delete Selected" opens a confirmation modal: "Delete X records? This cannot be undone." — calls `DELETE /dynamic-data/{entity}/records/bulk`
- "Update Field" opens a mini-form modal: field selector + new value input — calls `PUT /dynamic-data/{entity}/records/bulk` with the chosen field set to the new value for all selected IDs
- After bulk action: selected rows removed/updated in the table; toast "X records deleted/updated"
