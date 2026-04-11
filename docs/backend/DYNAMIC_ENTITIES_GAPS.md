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

### 1.1 Path discrepancy between docs and router
- **Priority**: 🔴 High
- **Problem**: `docs/backend/API_REFERENCE.md` documents paths as `/api/v1/dynamic-data/{entity}` but the actual router (`backend/app/routers/dynamic_data.py`) uses `/api/v1/dynamic-data/{entity}/records`. Any consumer (report engine, dashboard widget) built from the docs will receive 404s.
- [ ] Correct `docs/backend/API_REFERENCE.md` to use the `/records` suffix on all dynamic-data paths
- [ ] Audit all frontend JS files (`entity-manager.js`, `dynamic-table.js`, `dynamic-form.js`) that call the dynamic-data API and confirm they use the correct `/records` path
- [ ] Add a note in `API_REFERENCE.md` stating Swagger UI at `/docs` is always authoritative

---

### 1.2 Structured validation error response
- **Priority**: 🟡 Medium
- **Problem**: `DynamicEntityService._validate_and_prepare_data()` raises `ValueError("Validation errors: field A is required; field B max length exceeded")` — a single concatenated string. FastAPI wraps this as `{"detail": "..."}`. Dashboard inline forms cannot highlight the specific failing field from a flat string.
- **File**: `backend/app/services/dynamic_entity_service.py` → `_validate_and_prepare_data()`
- [ ] Change the error collection from a string list to a structured list: `[{"field": "email", "message": "Email is required"}]`
- [ ] Raise a custom exception (e.g. `ValidationException`) with the structured list instead of `ValueError`
- [ ] Map the custom exception to a `422` response with body `{"errors": [{"field": ..., "message": ...}]}` in the router or via a FastAPI exception handler
- [ ] Update `ValidationErrorResponse` Pydantic schema in `backend/app/schemas/dynamic_data.py` to reflect the new shape

---

## 2. Entity Lifecycle

### 2.1 `migrating` status — mechanics undocumented and potentially incomplete
- **Priority**: 🔴 High
- **Problem**: The `migrating` status exists on `EntityDefinition` but it is unclear whether: (a) the transition to `migrating` is set before the migration runs, (b) whether runtime `GET` requests are blocked or pass through during migration, and (c) whether the status auto-transitions to `published` on completion or requires a manual step. A dashboard widget backed by a migrating entity may fail silently.
- **Files**: `backend/app/services/data_model_service.py`, `backend/app/services/migration_generator.py` (or equivalent), `backend/app/routers/dynamic_data.py`
- [ ] Confirm that `status` is set to `migrating` **before** DDL execution and to `published` **after** in the same transaction boundary
- [ ] In `RuntimeModelGenerator.get_model()`, decide and implement the behaviour for `migrating` entities: return the last valid model (read-only), raise a specific `503` error, or block only write operations
- [ ] Add `migrating` handling in the dynamic-data router — return `{"detail": "Entity schema migration in progress, try again shortly"}` with `503` status for write operations
- [ ] Expose the current entity `status` in the `GET /dynamic-data/{entity}/metadata` response so consumers can react programmatically

---

### 2.2 `is_versioned` — implementation unclear
- **Priority**: 🟡 Medium
- **Problem**: The `is_versioned` flag exists on `EntityDefinition` but there is no visible versioning table, no version column in generated tables, and no API to retrieve historical record states. It is unknown whether this is a planned feature or partially implemented.
- **File**: `backend/app/services/dynamic_entity_service.py` → `update_record()`
- [ ] Audit `update_record()` to confirm whether `is_versioned = True` triggers any history storage currently
- [ ] If not implemented: add to `docs/GAPS.md` and set `is_versioned` as a read-only no-op field with a deprecation note until implemented
- [ ] If implementing: define a `{entity_name}_versions` shadow table pattern, insert old row before each update, expose via `GET /dynamic-data/{entity}/records/{id}/versions`
- [ ] Document how reports should query versioned data — e.g. whether `list_records` returns only current versions by default

---

### 2.3 `virtual` entity type — undefined behaviour
- **Priority**: 🟡 Medium
- **Problem**: `entity_type` accepts `system`, `custom`, and `virtual` but `virtual` is never explained in code comments or docs. It is unclear whether virtual entities have a DB table, whether they are read-only, and whether `RuntimeModelGenerator` handles them differently.
- **File**: `backend/app/models/data_model.py`, `backend/app/services/runtime_model_generator.py`
- [ ] Search codebase for all `entity_type == "virtual"` branches and document what actually happens
- [ ] If virtual entities map to DB views: document that `table_name` must be an existing view name, set `CREATE TABLE` migration skip for virtual entities in `MigrationGenerator`, and enforce read-only (block `POST`/`PUT`/`DELETE`) in the dynamic-data router
- [ ] If virtual entities are not yet implemented: treat them as `custom` (or raise an error) and add to `docs/GAPS.md`
- [ ] Virtual entities backed by DB views are ideal for cross-entity report data — document this pattern explicitly if implemented

---

## 3. Field System

### 3.1 `allowed_values` — JSONB schema undefined
- **Priority**: 🔴 High
- **Problem**: `allowed_values` is JSONB but its structure is not defined anywhere. Report filter dropdowns and dashboard chart category axes need to read this field to populate option lists. The shape must be defined and consistent.
- **File**: `backend/app/models/data_model.py`, `backend/app/utils/field_type_mapper.py`
- [ ] Define and enforce a canonical schema: `[{"value": "active", "label": "Active"}, ...]` with an optional `label_i18n` key: `{"en": "Active", "es": "Activo"}`
- [ ] Add a Pydantic validator on `FieldDefinitionCreate` schema that validates `allowed_values` matches this shape when `field_type` is `select` or `enum`
- [ ] In `_validate_and_prepare_data()`, enforce that submitted values for `select`/`enum` fields are members of `allowed_values`
- [ ] Expose `allowed_values` in the `GET /dynamic-data/{entity}/metadata` response so report/dashboard consumers can auto-populate filter dropdowns without a separate API call

---

### 3.2 `validation_rules` — JSONB schema undefined
- **Priority**: 🟡 Medium
- **Problem**: `validation_rules` is a JSONB array on `FieldDefinition` but its rule schema is not documented. It is unclear which rule types are supported and whether they are enforced in `_validate_and_prepare_data()`.
- **File**: `backend/app/utils/field_type_mapper.py` → `validate_value()`, `backend/app/services/dynamic_entity_service.py`
- [ ] Define the rule schema: `[{"type": "regex", "pattern": "^[A-Z]", "message": "Must start with uppercase"}, {"type": "min_length", "value": 3, "message": "Min 3 characters"}]`
- [ ] Supported rule types to implement/confirm: `regex`, `min_length`, `max_length`, `min_value`, `max_value`, `custom_expression`
- [ ] Confirm `validate_value()` in `FieldTypeMapper` actually iterates and applies `validation_rules` — if not, implement it
- [ ] Add rule type to the structured error response from item 1.2 above so the client knows which rule failed

---

### 3.3 `visibility_rules` — server-side enforcement absent
- **Priority**: 🟡 Medium
- **Problem**: `visibility_rules` on `FieldDefinition` and `FieldGroup` controls conditional field visibility. If only evaluated client-side (form rendering), a record can be saved with a value in a field that should be hidden/irrelevant — corrupting data that reports then read.
- **File**: `backend/app/services/dynamic_entity_service.py` → `_validate_and_prepare_data()`
- [ ] Decide enforcement policy: **client-side UX only** (no server enforcement) vs **server enforced** (field is skipped/nulled if its visibility condition is not met based on sibling field values in the same request payload)
- [ ] If server-enforced: implement condition evaluation in `_validate_and_prepare_data()` before the required-field check — a hidden field must not trigger a "required" error
- [ ] Document the enforcement decision clearly so report builders know whether field values are guaranteed to be consistent with visibility conditions

---

### 3.4 `calculation_formula` — syntax and evaluation not implemented or undocumented
- **Priority**: 🟡 Medium
- **Problem**: `is_calculated` and `calculation_formula` columns exist but there is no visible implementation in `DynamicEntityService` or `RuntimeModelGenerator` that evaluates formulas. Calculated fields are highly valuable for reports — a `total_with_tax` field removes the need for post-query computation.
- **File**: `backend/app/services/dynamic_entity_service.py`, `backend/app/services/runtime_model_generator.py`
- [ ] Audit whether any formula evaluation exists currently — search for `calculation_formula` usage across the codebase
- [ ] Decide evaluation strategy:
  - **DB-level** (PostgreSQL generated column): best for filtering/sorting in reports; requires migration support
  - **Service-level on read** (Python evaluation after fetch): simpler but result is not filterable/sortable
  - **Service-level on write** (compute and store): filterable/sortable but stale if dependencies change
- [ ] Define and document the formula syntax — recommended: a restricted expression language referencing `{field_name}` tokens, e.g. `{unit_price} * {quantity} * (1 + {tax_rate})`
- [ ] In `GET /dynamic-data/{entity}/metadata`, flag calculated fields (`"is_calculated": true`) and their formula so report builders know not to treat them as user-editable inputs
- [ ] Report engine must know: can calculated fields be used in `filters` and `sort`? Document this explicitly

---

### 3.5 `depends_on_field` / `filter_expression` — cascading fields undefined
- **Priority**: 🟢 Low
- **Problem**: Columns for cascading field dependencies exist but their evaluation mechanism is not documented.
- **File**: `backend/app/models/data_model.py`, `backend/app/utils/field_type_mapper.py`
- [ ] Define `filter_expression` syntax — likely a SQL-like `WHERE` fragment, e.g. `country_id = {depends_on_field_value}`
- [ ] Implement server-side filtering of lookup options when `depends_on_field` is set — `GET /dynamic-data/{ref_entity}/records?filters={filter_expression with parent value injected}`
- [ ] In the `metadata` endpoint, expose `depends_on_field` and `filter_expression` so the frontend form builder can wire up cascading dropdowns

---

## 4. Soft Delete

### 4.1 List query does not document soft-delete filter behaviour
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

### 5.1 `permissions` JSONB on `EntityDefinition` — not enforced
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

### 6.1 No aggregation API
- **Priority**: 🔴 High
- **Problem**: `list_records()` returns raw rows only. Reports and dashboards need aggregate queries — `COUNT(*)`, `SUM(amount)`, `AVG(value)`, `GROUP BY status` — which cannot be assembled from paginated row results without fetching all data.
- **File**: `backend/app/routers/dynamic_data.py`, `backend/app/services/dynamic_entity_service.py`
- [ ] Add a `GET /api/v1/dynamic-data/{entity}/aggregate` endpoint
- [ ] Request parameters: `group_by` (array of field names), `metrics` (array of `{field, function}` where function is `count`, `sum`, `avg`, `min`, `max`, `count_distinct`), `filters` (same format as list), `date_trunc` (for time-series grouping: `day`, `week`, `month`, `year`)
- [ ] Response shape: `{"groups": [{"status": "active", "count": 42, "total_amount": 10500.00}]}`
- [ ] Enforce org-scope filters (same `SCOPE_HIERARCHY` logic as `list_records`) so users cannot aggregate across tenant/company boundaries
- [ ] Apply soft-delete exclusion by default
- [ ] Expose in `metadata` which fields are numeric (aggregatable) and which are categorical (groupable) — the `field_type` values already encode this

---

### 6.2 No cross-entity join for reports
- **Priority**: 🟡 Medium
- **Problem**: Reports often need data spanning multiple entities — e.g. "invoices joined to customers joined to regions." The current API requires separate queries and client-side joining, which is impractical at scale.
- **File**: `backend/app/routers/dynamic_data.py`
- [ ] Evaluate two approaches:
  - **Virtual entities** (see item 2.3): point `table_name` at a DB view that pre-joins tables — simplest, best performance, but requires DBA to create views
  - **`expand` parameter on list/aggregate**: `?expand=customer_id,region_id` causes the service to join and inline the referenced record's fields — more flexible, more complex to implement
- [ ] If implementing `expand`: in `list_records()`, detect lookup fields with `reference_entity_id` set, fetch related records in a single `IN` query (not N+1), and inline as `{field_name}_data: {...}` in the response
- [ ] Limit `expand` depth to 1 level to avoid unbounded join chains
- [ ] For the aggregate endpoint (item 6.1), allow `group_by` to reference expanded fields: `group_by=customer_id.region`

---

### 6.3 `table_config` aggregation hints undefined
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

### 6.4 Relationship traversal returns 501
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

### 7.1 Tenant access to platform-level entities undefined
- **Priority**: 🟡 Medium
- **Problem**: Platform-level entities (`tenant_id = NULL`) are intended as shared reference data (e.g. currencies, countries) but the current `RuntimeModelGenerator._load_entity_definition()` and `_get_org_context()` behaviour for these entities is undocumented. It is unclear whether tenant users can query them.
- **File**: `backend/app/services/runtime_model_generator.py`, `backend/app/services/dynamic_entity_service.py`
- [ ] Confirm that `_load_entity_definition()` returns platform-level entities to all authenticated users regardless of `tenant_id`
- [ ] Confirm `_get_org_context()` returns empty filters (`{}`) for `data_scope = "platform"` entities — tenant users must not have their `tenant_id` injected as a filter on platform data
- [ ] Enforce read-only access for non-superusers on platform-level entities: block `POST`/`PUT`/`DELETE` in the router or service with `403`
- [ ] For reports: document that platform-level entities can be queried freely and used as lookup/join targets in cross-entity reports

---

## 8. Attachments & Comments

### 8.1 `supports_attachments` and `supports_comments` — APIs missing
- **Priority**: 🟢 Low
- **Problem**: Feature toggles exist on `EntityDefinition` but no sub-resource API endpoints exist. Dashboard record-detail widgets cannot display attachment counts or comment threads.
- [ ] Confirm whether any attachment/comment tables exist in the DB schema — search models for `attachments`, `record_comments`, or similar
- [ ] If not yet implemented: add to `docs/GAPS.md` and mark `supports_attachments` / `supports_comments` as reserved flags for a future release
- [ ] If implementing: add endpoints `GET|POST /dynamic-data/{entity}/records/{id}/attachments` and `GET|POST /dynamic-data/{entity}/records/{id}/comments`
- [ ] For dashboard list widgets: add an `include_counts=true` query parameter to `list_records` that appends `_attachment_count` and `_comment_count` to each row — avoids N+1 queries when rendering a list

---

## Summary Table

| # | Gap | Priority | Effort | Blocks Reports/Dashboard |
|---|-----|----------|--------|--------------------------|
| 1.1 | API path discrepancy | 🔴 High | Low | Yes — 404 on all calls |
| 1.2 | Structured validation errors | 🟡 Medium | Low | Partial |
| 2.1 | `migrating` status mechanics | 🔴 High | Medium | Yes — silent failures |
| 2.2 | `is_versioned` implementation | 🟡 Medium | High | Partial |
| 2.3 | `virtual` entity type | 🟡 Medium | Medium | Yes — view-backed reports |
| 3.1 | `allowed_values` schema | 🔴 High | Low | Yes — filter dropdowns |
| 3.2 | `validation_rules` schema | 🟡 Medium | Low | No |
| 3.3 | `visibility_rules` server enforcement | 🟡 Medium | Medium | Yes — data integrity |
| 3.4 | `calculation_formula` | 🟡 Medium | High | Yes — computed metrics |
| 3.5 | Cascading field dependencies | 🟢 Low | Medium | No |
| 4.1 | Soft-delete list filtering | 🔴 High | Low | Yes — wrong counts |
| 5.1 | `permissions` JSONB enforcement | 🔴 High | Medium | Yes — security |
| 6.1 | Aggregation API | 🔴 High | High | Yes — KPIs, charts |
| 6.2 | Cross-entity join | 🟡 Medium | High | Yes — multi-entity reports |
| 6.3 | `table_config` aggregation hints | 🟡 Medium | Low | Yes — chart axis config |
| 6.4 | Relationship traversal (501) | 🟡 Medium | Medium | Yes — related record widgets |
| 7.1 | Platform entity tenant access | 🟡 Medium | Low | Yes — shared lookup data |
| 8.1 | Attachments & comments APIs | 🟢 Low | High | No |

---

## Related Documents

- [Dynamic Entity System](./DYNAMIC_ENTITIES.md)
- [Backend Architecture](./README.md)
- [RBAC System](./RBAC.md)
- [Known Gaps](../GAPS.md)
