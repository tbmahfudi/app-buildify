# Dynamic Entity System

## Overview

The Dynamic Entity system is the core of App-Buildify's NoCode capability. It lets tenant admins design custom database tables (entities) and fields through a UI or API without writing code. Once an entity is **published**, records can be created, read, updated, and deleted at runtime through a generic REST API.

The system has two layers:

| Layer | Purpose | API prefix |
|-------|---------|-----------|
| **Design-time** — Data Model Designer | Define entities, fields, relationships, indexes | `/api/v1/data-model/` |
| **Runtime** — Dynamic Data | CRUD on records of published entities | `/api/v1/dynamic-data/` |

---

## Database Models

### `EntityDefinition` — `entity_definitions`

The blueprint for a custom table.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `tenant_id` | UUID \| NULL | NULL = platform-level (shared); set = tenant-specific |
| `module_id` | UUID \| NULL | Optional: associates entity with a NocodeModule |
| `name` | String(100) | Technical name in snake_case — used in API paths |
| `label` | String(200) | Display name shown in the UI |
| `plural_label` | String(200) | Plural display name |
| `description` | Text | Optional description |
| `icon` | String(50) | Phosphor icon name |
| `entity_type` | String(50) | `system` \| `custom` \| `virtual` |
| `category` | String(100) | Grouping label for the UI |
| `data_scope` | String(20) | `platform` \| `tenant` \| `company` \| `branch` \| `department` — controls org isolation |
| `table_name` | String(100) | Actual DB table name (auto-prefixed with module prefix if applicable) |
| `schema_name` | String(100) | DB schema, default `public` |
| `is_audited` | Boolean | Writes generate audit log entries |
| `is_versioned` | Boolean | Enable record versioning |
| `supports_soft_delete` | Boolean | Use `deleted_at` instead of hard DELETE |
| `supports_attachments` | Boolean | Allow file attachments on records |
| `supports_comments` | Boolean | Allow comments on records |
| `primary_field` | String(100) | Field used as the record title in dropdowns/lists |
| `default_sort_field` | String(100) | Default sort column |
| `default_sort_order` | String(10) | `ASC` or `DESC` |
| `records_per_page` | Integer | Default pagination size |
| `status` | String(50) | `draft` → `published` → `migrating` → `archived` |
| `is_active` | Boolean | Soft-disable without archiving |
| `table_config` | JSONB | Auto-generated grid/table UI configuration |
| `form_config` | JSONB | Auto-generated form UI configuration |
| `permissions` | JSONB | Per-entity RBAC map: `{role: [actions]}` |
| `version` | Integer | Current schema version number |
| `parent_version_id` | UUID \| NULL | Links to previous version for lineage tracking |
| `meta_data` | JSONB | Extended/custom configuration |

> **Only `published` entities are accessible at runtime.** Draft and archived entities return a 404 from the dynamic data API.

> **Platform-level entities** (`tenant_id = NULL`) are visible to all tenants read-only and require superuser to create.

#### Entity Lifecycle

```
draft → published → migrating → archived
```

- `draft` — being designed, not yet accessible at runtime
- `published` — live and accessible via `/api/v1/dynamic-data/`
- `migrating` — schema change in progress
- `archived` — deactivated, no longer accessible

---

### `FieldDefinition` — `field_definitions`

A column within an entity's table.

#### Core

| Column | Description |
|--------|-------------|
| `name` | Technical column name (snake_case) |
| `label` | Display label |
| `field_type` | Logical type — see Field Types below |
| `data_type` | DB type: `VARCHAR`, `INTEGER`, `TIMESTAMP`, `BOOLEAN`, `NUMERIC`, `UUID`, `JSONB`, etc. |
| `display_order` | Ordering on forms/grids |
| `is_system` | System fields cannot be deleted |
| `is_readonly` | Shown but not editable |
| `is_calculated` | Value computed via `calculation_formula` |

#### Constraints

| Column | Description |
|--------|-------------|
| `is_required` | Field must be provided on create |
| `is_unique` | DB UNIQUE constraint |
| `is_indexed` | Create a DB index on this column |
| `is_nullable` | Allow NULL |
| `max_length` / `min_length` | String length bounds |
| `max_value` / `min_value` | Numeric value bounds |
| `precision` / `decimal_places` | DECIMAL/NUMERIC precision and scale |
| `allowed_values` | JSONB array — restricts input to a fixed set (enum-like) |
| `validation_rules` | JSONB array of custom validation rules |

#### Defaults

| Column | Description |
|--------|-------------|
| `default_value` | Static default |
| `default_expression` | SQL expression for dynamic defaults (e.g. `NOW()`) |

#### Lookup / Reference Fields

For fields that reference another entity or system table:

| Column | Description |
|--------|-------------|
| `reference_entity_id` | FK to `EntityDefinition` — reference a custom entity |
| `reference_table_name` | Direct table name for system tables (e.g. `users`, `companies`) |
| `reference_field` | Target column for the FK constraint (e.g. `id`) |
| `display_field` | Column to display in UI dropdowns (e.g. `full_name`, `email`) |
| `relationship_type` | `many-to-one` \| `one-to-one` |
| `on_delete` | `CASCADE` \| `SET NULL` \| `RESTRICT` \| `NO ACTION` |
| `on_update` | `CASCADE` \| `SET NULL` \| `RESTRICT` \| `NO ACTION` |
| `lookup_display_template` | Template string, e.g. `"{name} ({email})"` |
| `lookup_search_fields` | JSONB array of fields to search, e.g. `["name", "email"]` |
| `lookup_allow_create` | Show a quick-create button in the lookup dropdown |
| `lookup_recent_count` | Number of recent items to pre-load in dropdown (default 5) |
| `lookup_filter_field` | Filter the lookup list by a specific field |

#### UI / Form Behaviour

| Column | Description |
|--------|-------------|
| `input_type` | `text` \| `textarea` \| `select` \| `date-picker` \| etc. |
| `placeholder` | Input placeholder text |
| `prefix` / `suffix` | Visual decorators (e.g. `$`, `kg`) |
| `help_text` | Helper text shown below the field |

#### Conditional Visibility

```json
{
  "operator": "AND",
  "conditions": [
    { "field": "account_type", "operator": "eq", "value": "business" }
  ]
}
```

Stored in `visibility_rules` (JSONB). The field is only shown/required when conditions are met.

#### Cascading Dependencies

| Column | Description |
|--------|-------------|
| `depends_on_field` | Parent field name — this field's options depend on the parent's value |
| `filter_expression` | Expression to filter this field's options based on the parent value |

#### Multi-language Labels

| Column | Description |
|--------|-------------|
| `label_i18n` | JSONB: `{"en": "Name", "es": "Nombre", "de": "Name"}` |
| `help_text_i18n` | JSONB: per-language help text |
| `placeholder_i18n` | JSONB: per-language placeholder |

#### Field Groups

`field_group_id` — assigns the field to a `FieldGroup` for collapsible section grouping on forms.

#### Field Types

| `field_type` | DB type | Notes |
|-------------|---------|-------|
| `string` | VARCHAR | Short text |
| `text` / `textarea` | TEXT | Long text |
| `integer` | INTEGER | Whole number |
| `decimal` | NUMERIC | Decimal number, uses `precision` + `decimal_places` |
| `boolean` | BOOLEAN | True/false |
| `date` | DATE | Date only |
| `datetime` | TIMESTAMP | Date + time |
| `email` | VARCHAR | String with email format validation |
| `url` | VARCHAR | String with URL format validation |
| `phone` | VARCHAR | String with phone format validation |
| `uuid` | UUID | UUID value |
| `json` | JSONB | Arbitrary JSON |
| `select` / `enum` | VARCHAR | Uses `allowed_values` for options |
| `lookup` | UUID | References another entity or system table |

---

### `FieldGroup` — `field_groups`

Organizes fields into collapsible sections on forms.

| Column | Description |
|--------|-------------|
| `name` | Technical name |
| `label` | Display label |
| `icon` | Phosphor icon name |
| `is_collapsible` | Allow collapsing the section |
| `is_collapsed_default` | Start collapsed by default |
| `display_order` | Ordering among groups |
| `visibility_rules` | Same format as field `visibility_rules` — hide the whole group conditionally |

---

### `RelationshipDefinition` — `relationship_definitions`

Defines a relationship between two entities.

| Column | Description |
|--------|-------------|
| `relationship_type` | `one-to-many` \| `many-to-many` \| `one-to-one` |
| `source_entity_id` | The owning entity |
| `source_field_name` | Field name to create on source |
| `target_entity_id` | The referenced entity |
| `target_field_name` | Field name to create on target |
| `junction_table_name` | Junction table name (many-to-many only) |
| `junction_source_field` | Junction table FK to source |
| `junction_target_field` | Junction table FK to target |
| `on_delete` / `on_update` | Cascade behaviour |
| `display_in_source` / `display_in_target` | Show related records tab on each side |

> **Note**: The relationship traversal API endpoint (`GET /{entity}/records/{id}/{relationship}`) is defined but returns **501 Not Implemented**.

---

### `IndexDefinition` — `index_definitions`

Manages DB indexes on entity tables.

| Column | Description |
|--------|-------------|
| `index_type` | `btree` \| `hash` \| `gin` \| `gist` |
| `field_names` | JSONB ordered array of column names |
| `is_unique` | UNIQUE index |
| `is_partial` | Partial index (uses `where_clause`) |
| `where_clause` | SQL WHERE clause for partial indexes |

---

### `EntityMigration` — `entity_migrations`

Tracks every schema change applied to an entity's table.

| Column | Description |
|--------|-------------|
| `migration_type` | `create` \| `alter` \| `drop` |
| `from_version` / `to_version` | Version numbers before and after |
| `up_script` | SQL to apply the migration |
| `down_script` | SQL to roll it back |
| `status` | `pending` → `running` → `completed` \| `failed` \| `rolled_back` |
| `execution_time_ms` | How long it took |
| `error_message` | Error detail on failure |
| `changes` | JSONB detailed change log |

---

## Services

### `RuntimeModelGenerator`

Reads `EntityDefinition` + `FieldDefinition` rows from the DB and constructs a live SQLAlchemy ORM class at runtime:

1. Loads the entity definition (must be `published`)
2. Maps each `FieldDefinition` to a SQLAlchemy `Column` via `FieldTypeMapper`
3. Adds system columns (`id`, org hierarchy columns, `created_at`, `updated_at`, etc.) based on `data_scope`
4. Registers relationships from `RelationshipDefinition`
5. Returns the generated class (or retrieves from cache)

**Caching**: Models are cached in `ModelCache` (keyed by a hash of the entity definition). The cache is invalidated when the definition changes.

**Separate base**: Uses its own `DynamicBase = declarative_base()` to avoid conflicts with static platform models.

**Virtual entities**: When `entity_type = "virtual"`, the generator maps `table_name` directly to an existing database view. No table-creation validation is performed. The generated model class has `__is_virtual__ = True` set as a class attribute so the router layer can enforce read-only access.

**`entity_type` in metadata**: All generated model classes carry `__entity_definition__['entity_type']` so downstream code can inspect the entity type without re-querying the database.

---

### `DataModelService`

Design-time CRUD for entity definitions, field definitions, relationships, and indexes.

Key behaviours:
- **Name uniqueness**: checked against both tenant-level and platform-level entities to prevent conflicts
- **Module prefix**: if `module_id` is set, the module's `table_prefix` is automatically prepended to `table_name`
- **Platform-level entities**: `tenant_id = NULL`; requires `is_superuser = True`

---

### `MigrationGenerator`

Generates SQL DDL for entity tables, views, and field changes.

- **Regular entities** (`custom`, `system`): emits `CREATE TABLE` on first publish and `ALTER TABLE` on schema changes.
- **Virtual entities** (`virtual`): emits `CREATE OR REPLACE VIEW` from `meta_data.view_sql` (if present) or a no-op comment reminding the operator to create the view manually.
- **Calculated fields**: when `is_calculated = True` and `calculation_formula` is set, emits `GENERATED ALWAYS AS (...) STORED` on PostgreSQL. Formula tokens `{field_name}` are compiled to bare SQL column references.

---

### `DynamicEntityService`

Runtime CRUD on records of published entities. Every operation:

1. Calls `RuntimeModelGenerator.get_model()` to get the SQLAlchemy class
2. Applies **org scope filters** automatically (see Data Scope below)
3. Validates and prepares data via `FieldTypeMapper`
4. Executes the DB operation
5. Writes an **audit log** entry (`CREATE` / `UPDATE` / `DELETE` with before/after state)
6. Fires **automation rules** matching `trigger_type = "database"` + `entity_name` + event

**Protected fields on update** — these are never overwritten by client data:
`id`, `created_at`, `created_by`, `tenant_id`, `company_id`, `branch_id`, `department_id`, calculated fields.

**`aggregate_records()`** — runs a GROUP BY query with metric functions (count, sum, avg, min, max, count_distinct) and optional date truncation. Org-scope isolation is applied with the same `SCOPE_HIERARCHY` logic as list operations. Works on both regular and virtual entities.

**`_apply_expand()`** — resolves `?expand=field_name` by detecting lookup fields with `reference_entity_name` in their `lookup_config`, then batch-fetching all related records in a single `IN` query and inlining them as `{field_name}_data` on each row. Depth is capped at 1 level.

---

### `ProcedureService`

**File:** `backend/app/services/procedure_service.py`

A tenant-aware wrapper for calling named PostgreSQL functions and refreshing materialized views. Use this for queries that are too complex or expensive to express through `aggregate_records()`:

| Scenario | Recommended approach |
|----------|---------------------|
| Simple aggregation on one entity | `aggregate_records()` via the Aggregate API |
| Cross-entity join read model | Virtual entity + DB view |
| Recursive CTE (hierarchy, BOM) | `ProcedureService.call()` |
| Complex financial calc (AR aging) | `ProcedureService.call()` |
| Real-time dashboard < 50 ms | Materialized view + `refresh_materialized_view()` |

```python
service = ProcedureService(db, current_user)

# Set-returning function → list of dicts
rows = await service.call("fn_ar_aging", {"as_of_date": "2026-04-15"})

# Scalar function → single value
balance = await service.call_scalar("fn_account_balance", {"account_id": "..."})

# Refresh a materialized view
await service.refresh_materialized_view("mv_dashboard_kpis", concurrently=True)
```

`tenant_id` is automatically injected into every call from the current user. Register new functions in the `PROCEDURE_REGISTRY` dict at the top of `procedure_service.py`.

---

## Data Scope — Org Isolation

`data_scope` on `EntityDefinition` controls which org columns are automatically added to the table and injected into every query:

| `data_scope` | Org columns added | Filter applied on every query |
|-------------|------------------|-------------------------------|
| `platform` | none | none |
| `tenant` | `tenant_id` | `tenant_id = current_user.tenant_id` |
| `company` | `tenant_id`, `company_id` | + `company_id = current_user.default_company_id` |
| `branch` | `tenant_id`, `company_id`, `branch_id` | + `branch_id = current_user.branch_id` |
| `department` | `tenant_id`, `company_id`, `branch_id`, `department_id` | + `department_id = current_user.department_id` |

Users can never query or write records outside their own org scope regardless of what they send in the request body.

---

## API Reference

### Design-time: Data Model

All endpoints require `Authorization: Bearer <token>`.

#### Entity Definitions

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/data-model/entities` | List all entity definitions |
| `POST` | `/api/v1/data-model/entities` | Create entity definition |
| `GET` | `/api/v1/data-model/entities/{id}` | Get entity definition |
| `PUT` | `/api/v1/data-model/entities/{id}` | Update entity definition |
| `DELETE` | `/api/v1/data-model/entities/{id}` | Delete entity definition |

#### Fields

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/data-model/entities/{id}/fields` | Add field to entity |
| `PUT` | `/api/v1/data-model/entities/{id}/fields/{fid}` | Update field |
| `DELETE` | `/api/v1/data-model/entities/{id}/fields/{fid}` | Remove field |

---

### Runtime: Dynamic Data

#### CRUD

| Method | Path | Permission | Description |
|--------|------|-----------|-------------|
| `POST` | `/api/v1/dynamic-data/{entity}/records` | `{entity}:create:tenant` | Create record |
| `GET` | `/api/v1/dynamic-data/{entity}/records` | `{entity}:read:tenant` | List records |
| `GET` | `/api/v1/dynamic-data/{entity}/records/{id}` | `{entity}:read:tenant` | Get record |
| `PUT` | `/api/v1/dynamic-data/{entity}/records/{id}` | `{entity}:update:own` or `:tenant` | Update record (partial) |
| `DELETE` | `/api/v1/dynamic-data/{entity}/records/{id}` | `{entity}:delete:own` or `:tenant` | Delete record |

> **Virtual entities** (`entity_type = "virtual"`) are read-only. `POST`, `PUT`, and `DELETE` return `405 Method Not Allowed`.

#### Aggregation

| Method | Path | Permission | Description |
|--------|------|-----------|-------------|
| `GET` | `/api/v1/dynamic-data/{entity}/aggregate` | `{entity}:read:tenant` | Run GROUP BY aggregation |

| Parameter | Type | Description |
|-----------|------|-------------|
| `group_by` | string | Comma-separated field names to group by |
| `metrics` | JSON array | **Required.** `[{"field":"amount","function":"sum","alias":"total"}]` |
| `filters` | JSON string | Same format as list filters |
| `date_trunc` | string | `hour` \| `day` \| `week` \| `month` \| `quarter` \| `year` |
| `date_field` | string | Which `group_by` field to apply `date_trunc` to |

**Supported `function` values**: `count`, `sum`, `avg`, `min`, `max`, `count_distinct`

Use `"field": "*"` with `"function": "count"` for `COUNT(*)`.

**Example — monthly revenue:**
```
GET /api/v1/dynamic-data/orders/aggregate
    ?group_by=created_at
    &metrics=[{"field":"amount","function":"sum","alias":"revenue"}]
    &date_trunc=month&date_field=created_at
```

**Response:**
```json
{
  "groups": [{"created_at": "2026-01-01T00:00:00", "revenue": 84200.00}],
  "total_groups": 3,
  "entity_name": "orders"
}
```

#### Bulk Operations

| Method | Path | Permission | Description |
|--------|------|-----------|-------------|
| `POST` | `/api/v1/dynamic-data/{entity}/records/bulk` | `{entity}:create:tenant` | Bulk create |
| `PUT` | `/api/v1/dynamic-data/{entity}/records/bulk` | `{entity}:update:tenant` | Bulk update (each record needs `id`) |
| `DELETE` | `/api/v1/dynamic-data/{entity}/records/bulk` | `{entity}:delete:tenant` | Bulk delete (list of `ids`) |

Bulk operations continue on per-record errors and return a summary:
```json
{ "created": 10, "failed": 2, "errors": [{ "index": 3, "error": "..." }], "ids": [...] }
```

#### Metadata

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/dynamic-data/{entity}/metadata` | Get field definitions and relationships |

---

### List Records — Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | int | Page number, default `1` |
| `page_size` | int | Items per page, default `25`, max `100` |
| `sort` | string | e.g. `name:asc,created_at:desc` |
| `search` | string | Global search across all text fields |
| `filters` | JSON string | Filter specification (see below) |
| `expand` | string | Comma-separated lookup field names to inline (see below) |

#### Filter Format

```json
{
  "operator": "AND",
  "conditions": [
    { "field": "status", "operator": "eq", "value": "active" },
    { "field": "email", "operator": "contains", "value": "@example.com" },
    { "field": "created_at", "operator": "gte", "value": "2026-01-01" }
  ]
}
```

**Supported operators**:

| Category | Operators |
|----------|-----------|
| Comparison | `eq`, `ne`, `gt`, `gte`, `lt`, `lte` |
| String | `contains`, `starts_with`, `ends_with`, `like`, `ilike` |
| List | `in`, `not_in` |
| Null | `is_null`, `is_not_null` |

**Response envelope**:
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 25,
  "pages": 6
}
```

#### `expand` — Inline Related Records

`?expand=customer_id,region_id` fetches related entities for the listed lookup fields and inlines them into every row of the response. Each field must be of type `lookup` and have a `reference_entity_name` in its `lookup_config`.

- Related records are fetched in a **single `IN` query** per expanded field — no N+1 queries.
- Depth is limited to **1 level**. The inlined `_data` dict is a plain record and is not itself expanded.
- If a referenced record is not found (e.g. deleted), the corresponding `_data` key is `null`.

```json
{
  "items": [
    {
      "id": "uuid-1",
      "customer_id": "uuid-cust",
      "customer_id_data": {
        "id": "uuid-cust",
        "name": "Acme Corp",
        "email": "billing@acme.com"
      }
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 25,
  "pages": 1
}
```

---

## Virtual Entities — DB View Backing

Set `entity_type = "virtual"` to map an `EntityDefinition` to an existing database view instead of a managed table.

### How it works

1. Create the `EntityDefinition` with `entity_type = "virtual"` and `table_name = "<view_name>"`.
2. Optionally include `view_sql` in `meta_data` so `MigrationGenerator` creates the view automatically on publish.
3. Define `FieldDefinition` rows that mirror the view's columns — the generator uses these for filtering, sorting, type-coercion, and API documentation.
4. Publish the entity. The dynamic-data API now exposes it as a read-only endpoint.

### When to use virtual entities

| Use case | Better fit |
|----------|-----------|
| Cross-entity join for reporting | Virtual entity + view |
| Pre-computed aggregation (e.g. sales by region) | Virtual entity + materialized view |
| Shared read model across modules | Virtual entity + view |
| Simple aggregation on one entity | `aggregate_records()` API |
| UI lookup dropdown | `expand` parameter |

### Example

```json
POST /api/v1/data-model/entities
{
  "name": "v_invoice_summary",
  "label": "Invoice Summary",
  "entity_type": "virtual",
  "table_name": "v_invoice_summary",
  "data_scope": "company",
  "meta_data": {
    "view_sql": "CREATE OR REPLACE VIEW v_invoice_summary AS SELECT i.id, i.invoice_number, i.total_amount, i.status, c.name AS customer_name FROM financial_invoices i JOIN financial_customers c ON c.id = i.customer_id",
    "view_dependencies": ["financial_invoices", "financial_customers"]
  }
}
```

The `MigrationGenerator` will emit the `CREATE OR REPLACE VIEW` SQL when the entity is published. Once published, the entity is queryable via `GET /api/v1/dynamic-data/v_invoice_summary/records` and aggregatable via `.../aggregate`.

---

## Calculated Fields — PostgreSQL Generated Columns

Fields with `is_calculated = true` and a `calculation_formula` are emitted as `GENERATED ALWAYS AS (...) STORED` columns on PostgreSQL.

- **Formula syntax**: `{field_name}` tokens are compiled to bare SQL column references.
  - `{unit_price} * {quantity} * (1 + {tax_rate})` → `unit_price * quantity * (1 + tax_rate)`
- **Stored on disk**: the computed value is persisted and updated automatically by the DB engine whenever its source columns change.
- **Filterable and sortable**: because the value is stored, it can be used in `filters`, `sort`, and aggregation `metrics` queries.
- **Read-only**: the field is included in the `protected_fields` list and cannot be overwritten by client data on `PUT`.

### Example field definition

```json
{
  "name": "line_total",
  "label": "Line Total",
  "field_type": "decimal",
  "data_type": "NUMERIC(18,2)",
  "is_calculated": true,
  "calculation_formula": "{unit_price} * {quantity} * (1 + {tax_rate})"
}
```

> **Note**: PostgreSQL-specific. On MySQL and SQLite the field is created as a regular column; you must populate it via a trigger or application logic.

---

## Delete Behaviour

Delete is **soft** if the entity has a `deleted_at` column (`supports_soft_delete = true`), **hard** otherwise:

| Condition | Behaviour |
|-----------|-----------|
| `deleted_at` column exists | Sets `deleted_at = now()` and `deleted_by = user.id` |
| No `deleted_at` column | `DELETE FROM table WHERE id = ?` |

---

## Automation Integration

After every write, `DynamicEntityService` queries `AutomationRule` for rules with:
- `trigger_type = "database"`
- `trigger_config.entity_name == entity_name`
- `trigger_config.event == event`

Events fired: `onCreate`, `onUpdate`, `onDelete`.

Matching rules are executed via `AutomationService.execute_rule()` with context:
```json
{
  "entity": "customers",
  "event": "onCreate",
  "record": { ... },
  "user_id": "uuid",
  "tenant_id": "uuid"
}
```

Automation errors are logged but do **not** fail the original operation.

---

## Related Documents

- [Backend Architecture](./README.md)
- [API Reference](./API_REFERENCE.md)
- [RBAC System](./RBAC.md)
- [Dynamic Entity Gaps & Enhancement Checklist](./DYNAMIC_ENTITIES_GAPS.md)

---

*Last updated: 2026-04-15 — added virtual entities, aggregation API, expand parameter, calculated fields, and procedure service.*
