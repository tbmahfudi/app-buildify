# Dynamic Entity System — Gaps & Enhancement Checklist

Use this document as a working checklist when enhancing the dynamic entity system.
Items are grouped by area and ordered by priority within each group.

> **Context**: The dynamic entity system is a primary data source for the Reports and Dashboard modules.
> Many gaps below directly affect what reports can query and how dashboards display data.

Last audited: 2026-04-11

---

## Legend

- 🔴 **High** — blocks or degrades reports/dashboard functionality
- 🟡 **Medium** — important for correctness and developer experience
- 🟢 **Low** — quality-of-life, future-proofing

---

## 1. API Correctness

### 1.1 Path discrepancy, dead bulk method, and filter format bug — (ON-PROGRESS)
- **Priority**: 🔴 High
- **Problem A — Docs**: `docs/backend/API_REFERENCE.md` documents paths as `/api/v1/dynamic-data/{entity}` but the actual router uses `/api/v1/dynamic-data/{entity}/records`. Any consumer built from the docs will receive 404s.
- **Problem B — Dead bulk method**: `data-service.js` defines a `bulk()` method that is **never called anywhere** in the frontend. The method also has three issues:
  1. Path: calls `/dynamic-data/${entity}/bulk` → should be `/dynamic-data/${entity}/records/bulk`
  2. HTTP method: always uses `POST` → backend uses `POST` / `PUT` / `DELETE` per operation type
  3. Body: sends `{ operation, records }` → backend expects `{ records }` or `{ ids }` depending on endpoint
- **Problem C — Filter format bug (silent data loss)**: `data-service.js` `list()` (line ~36) sends `{ conditions: filters }` to the backend. `DynamicQueryBuilder._build_filter_clause()` requires a top-level `operator` key (`AND`/`OR`); when it is absent the method now raises a `ValueError` (previously returned `None` silently). Every filter applied in `dynamic-table.js` was previously silently ignored; now it returns a 400 error.
  - **Root cause (frontend)**: `data-service.js` sends `{ conditions: filters }` — fix is to send `{ operator: "AND", conditions: filters }` instead
  - **Backend fix applied**: `dynamic_query_builder.py` `_build_filter_clause()` now raises `ValueError` with a clear message when `operator` key is missing

**Frontend audit results (already verified):**
- `entity-manager.js` ✅ uses correct `/records` paths
- `dynamic-table.js` ✅ uses correct `/records` paths
- `dynamic-form.js` ✅ uses correct `/records` paths
- `dynamic-route-registry.js` ✅ uses correct `/records` paths
- `data-service.js` ❌ `list()` sends filters without `operator` key — returns 400 after backend fix (was silent)
- `data-service.js` ❌ `bulk()` method has wrong path, wrong method, wrong body — and is never called

**Bulk use cases — recommended functionality to build:**

The bulk API endpoints exist on the backend but have no frontend integration. Recommended use cases to implement:

| Use Case | Operation | Entry point |
|----------|-----------|-------------|
| CSV / spreadsheet import | Bulk create | "Import" button on entity list page |
| Mass status change (select N rows → set field) | Bulk update | Table row checkbox selection → bulk action toolbar |
| Batch field reassignment (reassign owner/region across records) | Bulk update | Table bulk action toolbar |
| Multi-select delete | Bulk delete | Table row checkbox selection → bulk action toolbar |
| Report-driven correction (fix N records surfaced by a report) | Bulk update | Report result action |
| Demo / seed data population | Bulk create | Admin tooling |

> Note: `flex-table.js` already has a `bulkActions` option and selection UI wired up — it emits a `bulkAction` event with selected rows. The missing piece is connecting this to the bulk API endpoints.

**Backend tasks:**
- [x] **Harden query builder**: `DynamicQueryBuilder._build_filter_clause()` now raises `ValueError` instead of silently returning `None` when filter object is malformed — `backend/app/core/dynamic_query_builder.py`

**Docs tasks:**
- [ ] Correct `docs/backend/API_REFERENCE.md` — update all 5 dynamic-data paths to include `/records`
- [ ] Add a note in `API_REFERENCE.md` that Swagger UI at `/api/docs` is always the authoritative source

**Frontend tasks (separate ticket):**
- [ ] **Fix filter bug**: In `data-service.js` `list()`, change `JSON.stringify({ conditions: filters })` to `JSON.stringify({ operator: 'AND', conditions: filters })` — one-line fix that unblocks all filtering in `dynamic-table.js`
- [ ] In `data-service.js`: remove the broken `bulk()` method and replace with three explicit methods — `bulkCreate(entity, records)`, `bulkUpdate(entity, records)`, `bulkDelete(entity, ids)` — each calling the correct path and HTTP verb
- [ ] Wire `flex-table.js` `bulkAction` event in `entity-manager.js` to call the appropriate bulk method based on action type (delete, status-change, etc.)
- [ ] Add an "Import" button to the entity list page template that accepts CSV, maps columns to entity fields via `metadata`, and calls `bulkCreate()`

---

### 1.2 Structured validation error response — (ON-PROGRESS)
- **Priority**: 🟡 Medium
- **Problem**: `DynamicEntityService._validate_and_prepare_data()` previously raised `ValueError("Validation errors: field A is required; field B max length exceeded")` — a single concatenated string. Dashboard inline forms could not highlight the specific failing field.

**Implemented response shape (400 on create/update):**

```json
{
  "detail": "Validation failed: 2 errors",
  "errors": [
    { "field": "email", "message": "Email is required" },
    { "field": "phone", "message": "Must be 20 characters or less" }
  ]
}
```

`error.errors` is **absent** on all other error types (404, 403, 500) so existing code that reads only `error.detail` is completely unaffected.

**Backend tasks — DONE:**
- [x] In `_validate_and_prepare_data()`, collect errors as `[{"field": field_name, "message": "..."}]` — `backend/app/services/dynamic_entity_service.py`
- [x] Add `EntityValidationError(errors, detail)` exception class — `backend/app/core/exceptions.py`
- [x] Handle in router with `JSONResponse(400, {"detail": ..., "errors": ...})` for `create_record` and `update_record` — `backend/app/routers/dynamic_data.py`
- [x] Update `ValidationErrorResponse` schema — added `FieldError` model, `errors: Optional[List[FieldError]]` — `backend/app/schemas/dynamic_data.py`

**Backend tasks — remaining:**
- [ ] For `allowed_values` violations in `FieldTypeMapper.validate_value()`, include the allowed list in the message: `"Invalid value. Allowed: active, inactive, pending"` (links to item 3.1)

**Frontend tasks (separate ticket):**

> ⚠️ No frontend code currently reads `error.errors`. All error handling reads only `error.detail` as a flat string. The backend change is non-breaking — `error.detail` still works as before. The following changes are needed to surface per-field highlighting:

| File | Change needed |
|------|---------------|
| `services/base-service.js` | `_fetchWithAuth()` discards structured errors — update to attach `error.errors` to the thrown error object instead of `throw new Error(error.detail)` |
| `data-service.js` | `create()` and `update()` do `throw new Error(error.detail)` — replace with a custom `ApiError(detail, errors)` class so `error.errors` survives to the caller |
| `dynamic-form.js` | Add `showFieldErrors(errors)` that maps each `{field, message}` to its input element and renders an inline error below it |
| `entity-manager.js` | In `saveRecord()` catch: if `error.errors` is present, call `form.showFieldErrors(error.errors)` in addition to `showError(error.message)` |
| `dynamic-route-registry.js` | In create/edit form submit catch: replace `alert('Error: ...')` with inline form error rendering using `error.errors` when present |

---

## 2. Entity Lifecycle

### 2.1 `migrating` status — mechanics undocumented and potentially incomplete — (OPEN)
- **Priority**: 🔴 High
- **Problem**: The `migrating` status exists on `EntityDefinition` but it is unclear whether: (a) the transition to `migrating` is set before the migration runs, (b) whether runtime `GET` requests are blocked or pass through during migration, and (c) whether the status auto-transitions to `published` on completion or requires a manual step. A dashboard widget backed by a migrating entity may fail silently.
- **Files**: `backend/app/services/data_model_service.py`, `backend/app/services/migration_generator.py` (or equivalent), `backend/app/routers/dynamic_data.py`
- [ ] Confirm that `status` is set to `migrating` **before** DDL execution and to `published` **after** in the same transaction boundary
- [ ] In `RuntimeModelGenerator.get_model()`, decide and implement the behaviour for `migrating` entities: return the last valid model (read-only), raise a specific `503` error, or block only write operations
- [ ] Add `migrating` handling in the dynamic-data router — return `{"detail": "Entity schema migration in progress, try again shortly"}` with `503` status for write operations
- [ ] Expose the current entity `status` in the `GET /dynamic-data/{entity}/metadata` response so consumers can react programmatically

---

### 2.2 `is_versioned` — implementation unclear — (OPEN)
- **Priority**: 🟡 Medium
- **Problem**: The `is_versioned` flag exists on `EntityDefinition` but there is no visible versioning table, no version column in generated tables, and no API to retrieve historical record states. It is unknown whether this is a planned feature or partially implemented.
- **File**: `backend/app/services/dynamic_entity_service.py` → `update_record()`
- [ ] Audit `update_record()` to confirm whether `is_versioned = True` triggers any history storage currently
- [ ] If not implemented: add to `docs/GAPS.md` and set `is_versioned` as a read-only no-op field with a deprecation note until implemented
- [ ] If implementing: define a `{entity_name}_versions` shadow table pattern, insert old row before each update, expose via `GET /dynamic-data/{entity}/records/{id}/versions`
- [ ] Document how reports should query versioned data — e.g. whether `list_records` returns only current versions by default

---

### 2.3 `virtual` entity type — (DONE)
- **Priority**: 🟡 Medium
- **Implemented**: `entity_type = "virtual"` entities map to existing PostgreSQL views (or any SQL-queryable object with the same name).
  - `RuntimeModelGenerator._entity_to_dict()` now includes `entity_type` in the entity dict and sets `__is_virtual__` on the generated model class.
  - `MigrationGenerator.generate_migration()` detects `entity_type == "virtual"` and:
    - If `meta_data.view_sql` is present: emits `CREATE OR REPLACE VIEW ...` (up) and `DROP VIEW IF EXISTS ... CASCADE` (down).
    - Otherwise: emits a no-op comment reminding the operator to create the view manually.
  - Dynamic-data router: `POST`, `PUT`, `DELETE` on virtual entities raise `405 Method Not Allowed`. `GET` list, single-record, metadata, and aggregate are all allowed.
- **Usage**: Set `entity_type = "virtual"`, `table_name = "<view_name>"`, and optionally `meta_data.view_sql = "CREATE OR REPLACE VIEW ..."`.
- **Files changed**: `backend/app/services/runtime_model_generator.py`, `backend/app/services/migration_generator.py`, `backend/app/routers/dynamic_data.py`

---

## 3. Field System

### 3.1 `allowed_values` — JSONB schema undefined — (OPEN)
- **Priority**: 🔴 High
- **Problem**: `allowed_values` is JSONB but its structure is not defined anywhere. Report filter dropdowns and dashboard chart category axes need to read this field to populate option lists. The shape must be defined and consistent.
- **File**: `backend/app/models/data_model.py`, `backend/app/utils/field_type_mapper.py`
- [ ] Define and enforce a canonical schema: `[{"value": "active", "label": "Active"}, ...]` with an optional `label_i18n` key: `{"en": "Active", "es": "Activo"}`
- [ ] Add a Pydantic validator on `FieldDefinitionCreate` schema that validates `allowed_values` matches this shape when `field_type` is `select` or `enum`
- [ ] In `_validate_and_prepare_data()`, enforce that submitted values for `select`/`enum` fields are members of `allowed_values`
- [ ] Expose `allowed_values` in the `GET /dynamic-data/{entity}/metadata` response so report/dashboard consumers can auto-populate filter dropdowns without a separate API call

---

### 3.2 `validation_rules` — JSONB schema undefined — (OPEN)
- **Priority**: 🟡 Medium
- **Problem**: `validation_rules` is a JSONB array on `FieldDefinition` but its rule schema is not documented. It is unclear which rule types are supported and whether they are enforced in `_validate_and_prepare_data()`.
- **File**: `backend/app/utils/field_type_mapper.py` → `validate_value()`, `backend/app/services/dynamic_entity_service.py`
- [ ] Define the rule schema: `[{"type": "regex", "pattern": "^[A-Z]", "message": "Must start with uppercase"}, {"type": "min_length", "value": 3, "message": "Min 3 characters"}]`
- [ ] Supported rule types to implement/confirm: `regex`, `min_length`, `max_length`, `min_value`, `max_value`, `custom_expression`
- [ ] Confirm `validate_value()` in `FieldTypeMapper` actually iterates and applies `validation_rules` — if not, implement it
- [ ] Add rule type to the structured error response from item 1.2 above so the client knows which rule failed

---

### 3.3 `visibility_rules` — server-side enforcement absent — (OPEN)
- **Priority**: 🟡 Medium
- **Problem**: `visibility_rules` on `FieldDefinition` and `FieldGroup` controls conditional field visibility. If only evaluated client-side (form rendering), a record can be saved with a value in a field that should be hidden/irrelevant — corrupting data that reports then read.
- **File**: `backend/app/services/dynamic_entity_service.py` → `_validate_and_prepare_data()`
- [ ] Decide enforcement policy: **client-side UX only** (no server enforcement) vs **server enforced** (field is skipped/nulled if its visibility condition is not met based on sibling field values in the same request payload)
- [ ] If server-enforced: implement condition evaluation in `_validate_and_prepare_data()` before the required-field check — a hidden field must not trigger a "required" error
- [ ] Document the enforcement decision clearly so report builders know whether field values are guaranteed to be consistent with visibility conditions

---

### 3.4 `calculation_formula` — (DONE — DB-level generated columns)
- **Priority**: 🟡 Medium
- **Implemented**: `MigrationGenerator._generate_field_definition()` detects `is_calculated = True` and `calculation_formula` on a `FieldDefinition` and emits a PostgreSQL `GENERATED ALWAYS AS (...) STORED` column.
  - Formula syntax: `{field_name}` tokens replaced with bare column names, e.g. `{unit_price} * {quantity} * (1 + {tax_rate})` → `unit_price * quantity * (1 + tax_rate)`.
  - Generated columns are stored on disk — they are **filterable and sortable** (can be used in aggregate `metrics` and `filters`).
  - `_compile_formula()` helper performs the token substitution.
  - Calculated fields are protected on write by the existing `protected_fields` list in `update_record()` — clients cannot overwrite them.
- **Limitation**: PostgreSQL-only (MySQL and SQLite do not support STORED generated columns). For non-PG databases, the field is defined as a regular column and must be populated manually or via a trigger.
- **Remaining**: Flag `is_calculated` fields in the `metadata` endpoint response so UI and report builders know not to render them as editable inputs.
- **File changed**: `backend/app/services/migration_generator.py`

---

### 3.5 `depends_on_field` / `filter_expression` — cascading fields undefined — (OPEN)
- **Priority**: 🟢 Low
- **Problem**: Columns for cascading field dependencies exist but their evaluation mechanism is not documented.
- **File**: `backend/app/models/data_model.py`, `backend/app/utils/field_type_mapper.py`
- [ ] Define `filter_expression` syntax — likely a SQL-like `WHERE` fragment, e.g. `country_id = {depends_on_field_value}`
- [ ] Implement server-side filtering of lookup options when `depends_on_field` is set — `GET /dynamic-data/{ref_entity}/records?filters={filter_expression with parent value injected}`
- [ ] In the `metadata` endpoint, expose `depends_on_field` and `filter_expression` so the frontend form builder can wire up cascading dropdowns

---

## 4. Soft Delete

### 4.1 List query does not document soft-delete filter behaviour — (OPEN)
- **Priority**: 🔴 High
- **Problem**: `list_records()` in `DynamicEntityService` does not visibly apply a `WHERE deleted_at IS NULL` filter. If soft-deleted records are returned by default, report "total count" widgets will be wrong.
- **File**: `backend/app/services/dynamic_entity_service.py` → `list_records()`
- [ ] Confirm whether `list_records()` automatically excludes soft-deleted records — search for `deleted_at` filter in `DynamicQueryBuilder`
- [ ] If not automatic: add `WHERE deleted_at IS NULL` as a base filter in `list_records()` for entities where `supports_soft_delete = True`
- [ ] Add an `include_deleted: bool = False` query parameter to `GET /{entity}/records` for explicit opt-in (useful for deletion audit reports)
- [ ] Apply the same soft-delete exclusion to `get_record()` — a direct `GET /{entity}/records/{id}` for a soft-deleted record should return `404`, not the record
- [ ] Document the default behaviour and `include_deleted` parameter in `DYNAMIC_ENTITIES.md`

---

## 5. Permissions

### 5.1 `permissions` JSONB on `EntityDefinition` — not enforced — (OPEN)
- **Priority**: 🔴 High
- **Problem**: `EntityDefinition.permissions` stores a per-entity RBAC map `{role: [actions]}` but there is no visible enforcement of this in `DynamicEntityService` or the dynamic-data router. The global RBAC (`require_permission`) is also not wired to dynamic entities — permission codes like `{entity_name}:create:tenant` are referenced in router docstrings but not enforced via `Depends(require_permission(...))`.
- **File**: `backend/app/routers/dynamic_data.py`, `backend/app/services/dynamic_entity_service.py`
- [ ] Confirm whether the dynamic-data router uses `Depends(require_permission(...))` — if not, every authenticated user can read/write any published entity, which is a security gap
- [ ] Implement permission check in `DynamicEntityService` using the entity's `permissions` JSONB as the first check, falling back to global RBAC
- [ ] Define precedence rule: entity-level `permissions` overrides global RBAC, or additive (both must pass)?
- [ ] For reports and dashboards: if a report runs as the requesting user, entity-level permissions will restrict what data is returned — document this so report builders know to handle partial-access gracefully
- [ ] Define what happens when `permissions` is `null` on the entity: inherit global RBAC only (recommended default)

---

## 6. Reports & Dashboard Integration

### 6.1 No aggregation API — (DONE)
- **Priority**: 🔴 High
- **Implemented**: `GET /api/v1/dynamic-data/{entity}/aggregate`
  - Query params: `group_by`, `metrics` (JSON array of `{field, function, alias?}`), `filters`, `date_trunc`, `date_field`
  - Supported functions: `count`, `sum`, `avg`, `min`, `max`, `count_distinct`; `COUNT(*)` via `field="*"`
  - Org-scope isolation applied via same `SCOPE_HIERARCHY` as `list_records`
  - Date-series truncation: `hour`, `day`, `week`, `month`, `quarter`, `year`
  - Response shape: `{"groups": [...], "total_groups": N, "entity_name": "..."}`
- **Files changed**: `backend/app/routers/dynamic_data.py`, `backend/app/services/dynamic_entity_service.py`, `backend/app/core/dynamic_query_builder.py`, `backend/app/schemas/dynamic_data.py`
- **Remaining**: Expose aggregatable/groupable field hints in `metadata` endpoint (`table_config` — see 6.3)

---

### 6.2 No cross-entity join for reports — (DONE — both approaches implemented)
- **Priority**: 🟡 Medium
- **Approach A — Virtual entities**: `entity_type = "virtual"` now points `table_name` at any existing DB view. The `RuntimeModelGenerator` maps to the view transparently. `MigrationGenerator` emits `CREATE OR REPLACE VIEW` from `meta_data.view_sql` (or a no-op if absent). The router enforces read-only (`POST`/`PUT`/`DELETE` → 405). See Gap 2.3.
- **Approach B — `expand` parameter**: `GET /{entity}/records?expand=customer_id,region_id` inlines related records as `{field}_data` in each row. Uses a single `IN` query (no N+1). Depth is limited to 1 level.
- **Files changed**: `backend/app/routers/dynamic_data.py`, `backend/app/services/dynamic_entity_service.py`
- **Remaining**: Cross-field `group_by` on expanded fields (e.g. `group_by=customer_id.region`) not yet supported — requires join in aggregate query.

---

### 6.3 `table_config` aggregation hints undefined — (OPEN)
- **Priority**: 🟡 Medium
- **Problem**: `table_config` JSONB on `EntityDefinition` is auto-generated but its schema is not defined. For dashboards, this config should carry hints about which fields can be used as chart axes, which are numeric (for Y-axis), and what display format to apply (currency, percentage, date).
- **File**: `backend/app/services/data_model_service.py` (where `table_config` is generated), `backend/app/models/data_model.py`
- [ ] Define `table_config` schema and document it — suggested structure:
  ```json
  {
    "columns": [
      {
        "field": "amount",
        "label": "Amount",
        "visible": true,
        "sortable": true,
        "filterable": true,
        "aggregatable": true,
        "aggregate_functions": ["sum", "avg", "min", "max"],
        "format": "currency",
        "currency_code": "USD",
        "width": 120
      }
    ],
    "default_sort": "created_at",
    "default_sort_order": "desc"
  }
  ```
- [ ] Auto-populate `aggregatable: true` and `aggregate_functions` based on `field_type` (numeric types only) when generating `table_config`
- [ ] Auto-populate `format` based on `field_type` and `prefix`/`suffix` (e.g. `prefix = "$"` → `format: "currency"`)
- [ ] Expose `table_config` in the `metadata` endpoint so dashboard widgets can self-configure without hardcoding field names

---

### 6.4 Relationship traversal returns 501 — (OPEN)
- **Priority**: 🟡 Medium
- **Problem**: `GET /api/v1/dynamic-data/{entity}/records/{id}/{relationship}` is defined in the router but raises `501 Not Implemented`. Dashboard record-detail widgets that show related records (e.g. a customer's orders) cannot use this endpoint.
- **File**: `backend/app/routers/dynamic_data.py` → `get_related_records()`
- [ ] Implement relationship traversal:
  1. Load `RelationshipDefinition` where `source_entity_id = entity` and `name = relationship_name`
  2. Determine relationship type (`one-to-many`, `many-to-many`, `one-to-one`)
  3. For `one-to-many`: query target entity with `WHERE {source_field} = record_id`
  4. For `many-to-many`: query junction table for matching IDs, then fetch target records via `IN`
  5. Apply org-scope filters and soft-delete exclusion on target entity
  6. Return paginated `DynamicDataListResponse`
- [ ] Apply `{target_entity}:read:tenant` permission check
- [ ] Support `page`, `page_size`, `sort`, `filters`, `search` parameters consistent with `list_records`

---

## 7. Platform-Level Entities

### 7.1 Tenant access to platform-level entities undefined — (OPEN)
- **Priority**: 🟡 Medium
- **Problem**: Platform-level entities (`tenant_id = NULL`) are intended as shared reference data (e.g. currencies, countries) but the current `RuntimeModelGenerator._load_entity_definition()` and `_get_org_context()` behaviour for these entities is undocumented. It is unclear whether tenant users can query them.
- **File**: `backend/app/services/runtime_model_generator.py`, `backend/app/services/dynamic_entity_service.py`
- [ ] Confirm that `_load_entity_definition()` returns platform-level entities to all authenticated users regardless of `tenant_id`
- [ ] Confirm `_get_org_context()` returns empty filters (`{}`) for `data_scope = "platform"` entities — tenant users must not have their `tenant_id` injected as a filter on platform data
- [ ] Enforce read-only access for non-superusers on platform-level entities: block `POST`/`PUT`/`DELETE` in the router or service with `403`
- [ ] For reports: document that platform-level entities can be queried freely and used as lookup/join targets in cross-entity reports

---

## 8. Attachments & Comments

### 8.1 `supports_attachments` and `supports_comments` — APIs missing — (OPEN)
- **Priority**: 🟢 Low
- **Problem**: Feature toggles exist on `EntityDefinition` but no sub-resource API endpoints exist. Dashboard record-detail widgets cannot display attachment counts or comment threads.
- [ ] Confirm whether any attachment/comment tables exist in the DB schema — search models for `attachments`, `record_comments`, or similar
- [ ] If not yet implemented: add to `docs/GAPS.md` and mark `supports_attachments` / `supports_comments` as reserved flags for a future release
- [ ] If implementing: add endpoints `GET|POST /dynamic-data/{entity}/records/{id}/attachments` and `GET|POST /dynamic-data/{entity}/records/{id}/comments`
- [ ] For dashboard list widgets: add an `include_counts=true` query parameter to `list_records` that appends `_attachment_count` and `_comment_count` to each row — avoids N+1 queries when rendering a list

---

## Summary Table

| # | Gap | Priority | Effort | Status | Blocks Reports/Dashboard |
|---|-----|----------|--------|--------|--------------------------|
| 1.1 | API path discrepancy + dead/broken bulk method + filter format bug + bulk UI missing | 🔴 High | Medium | ON-PROGRESS (backend hardened; frontend fix pending) | Yes — filter drops fixed on backend; frontend still sends wrong format |
| 1.2 | Structured validation errors (backend done; frontend wiring pending) | 🟡 Medium | Low–Medium | ON-PROGRESS (backend done; frontend pending) | Partial |
| 2.1 | `migrating` status mechanics | 🔴 High | Medium | OPEN | Yes — silent failures |
| 2.2 | `is_versioned` implementation | 🟡 Medium | High | OPEN | Partial |
| 2.3 | `virtual` entity type | 🟡 Medium | Medium | **DONE** | ✅ view-backed reports enabled |
| 3.1 | `allowed_values` schema | 🔴 High | Low | OPEN | Yes — filter dropdowns |
| 3.2 | `validation_rules` schema | 🟡 Medium | Low | OPEN | No |
| 3.3 | `visibility_rules` server enforcement | 🟡 Medium | Medium | OPEN | Yes — data integrity |
| 3.4 | `calculation_formula` | 🟡 Medium | High | **DONE** | ✅ filterable/sortable generated columns |
| 3.5 | Cascading field dependencies | 🟢 Low | Medium | OPEN | No |
| 4.1 | Soft-delete list filtering | 🔴 High | Low | OPEN | Yes — wrong counts |
| 5.1 | `permissions` JSONB enforcement | 🔴 High | Medium | OPEN | Yes — security |
| 6.1 | Aggregation API | 🔴 High | High | **DONE** | ✅ KPIs, charts, time-series |
| 6.2 | Cross-entity join | 🟡 Medium | High | **DONE** | ✅ virtual entities + expand param |
| 6.3 | `table_config` aggregation hints | 🟡 Medium | Low | OPEN | Yes — chart axis config |
| 6.4 | Relationship traversal (501) | 🟡 Medium | Medium | OPEN | Yes — related record widgets |
| 7.1 | Platform entity tenant access | 🟡 Medium | Low | OPEN | Yes — shared lookup data |
| 8.1 | Attachments & comments APIs | 🟢 Low | High | OPEN | No |

---

---

## 9. DB Functions / Stored Procedures

### 9.1 Procedure service layer — (DONE)
- **Priority**: 🟡 Medium
- **Implemented**: `backend/app/services/procedure_service.py` — a tenant-aware wrapper for calling named PostgreSQL functions.
  - `PROCEDURE_REGISTRY` maps logical names to DB function names (financial defaults pre-registered).
  - `ProcedureService.call(name, params)` → `List[Dict]` — set-returning functions.
  - `ProcedureService.call_scalar(name, params)` → scalar value.
  - `ProcedureService.refresh_materialized_view(view_name, concurrently=False)` — refresh materialized views.
  - `tenant_id` is automatically injected into every call — DB functions can enforce isolation without trusting callers.
  - All `Decimal` / `datetime` / `date` values are coerced to JSON-serialisable types.
- **When to use vs Python service**:
  | Scenario | Use |
  |----------|-----|
  | Simple aggregation on one entity | Aggregate API (Gap 6.1) |
  | Cross-entity join for report | Virtual entity + DB view (Gap 2.3) |
  | Recursive CTE (hierarchy, BOM) | `ProcedureService.call()` |
  | Complex financial calc (AR aging, amortisation) | `ProcedureService.call()` |
  | Real-time dashboard < 50 ms | Materialized view + `refresh_materialized_view()` |
- **To add a new function**: register it in `PROCEDURE_REGISTRY` in `procedure_service.py`.

---

## Related Documents

- [Dynamic Entity System](./DYNAMIC_ENTITIES.md)
- [Backend Architecture](./README.md)
- [RBAC System](./RBAC.md)
- [Known Gaps](../GAPS.md)
