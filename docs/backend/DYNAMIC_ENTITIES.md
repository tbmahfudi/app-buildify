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

---

### `DataModelService`

Design-time CRUD for entity definitions, field definitions, relationships, and indexes.

Key behaviours:
- **Name uniqueness**: checked against both tenant-level and platform-level entities to prevent conflicts
- **Module prefix**: if `module_id` is set, the module's `table_prefix` is automatically prepended to `table_name`
- **Platform-level entities**: `tenant_id = NULL`; requires `is_superuser = True`

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
`id`, `created_at`, `created_by`, `tenant_id`, `company_id`, `branch_id`, `department_id`

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
