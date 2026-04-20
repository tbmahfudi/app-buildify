# Epic 5 — NoCode Entity Designer

> Visual interface for designing custom database tables (entities) with fields, relationships, constraints, and lifecycle management.

---

## Feature 5.1 — Entity Lifecycle Management `[DONE]`

### Story 5.1.1 — Entity Creation `[DONE]`

#### Backend
*As an API, I want to create entity definitions in draft status, so that designers can configure entities before committing a real database table.*
- `POST /api/v1/data-model/entities` accepts `{name, label, plural_label, icon, category, entity_type, data_scope, module_id?}`
- `name` must be snake_case, globally unique per tenant; validated with regex `^[a-z][a-z0-9_]*$`
- Entity created with `status = "draft"` — invisible to the runtime CRUD API
- Audit log records creation

#### Frontend
*As a tenant administrator on the data model page, I want to click "New Entity", fill in the entity's display name and icon, and be taken to the field designer, so that I can start building my data model immediately.*
- Route: `#/nocode/data-model` renders entity list with cards per entity showing status badge, field count, and module name
- "New Entity" button opens a `FlexModal` with: Display Name (required), Internal Name (auto-derived from display name in snake_case, editable), Plural Label, Icon (icon picker grid), Category (select), Module assignment (select)
- Internal Name field: live preview showing the API path it will generate, e.g. `GET /dynamic-data/sales_order/records`
- On save: modal closes, entity card appears in the list with a "Draft" badge; user auto-navigated to the entity's field designer page
- Entity list filter bar: tabs for All / My Module / Platform, with status filter chips (Draft / Published / Archived)

---

### Story 5.1.2 — Entity Publishing and Migration `[DONE]`

#### Backend
*As an API, I want to publish an entity by running DDL to create the physical database table, so that the entity can store real records.*
- `POST /api/v1/data-model/entities/{id}/publish` transitions `status → migrating`, runs Alembic DDL via `MigrationGenerator`, then transitions to `published`
- On failure: status reverts to `draft`; error details returned
- While `migrating`: write operations return 503; reads return last valid model

#### Frontend
*As a tenant administrator who has finished designing an entity, I want to click "Publish" and see a real-time status indicator while the database table is being created, so that I know when the entity is ready to use.*
- Entity field designer page has a "Publish Entity" button in the page header (disabled if no fields have been defined)
- Clicking opens a confirmation modal: "Publishing will create a database table for [Entity Name]. This action cannot be easily undone. Continue?"
- After confirming: button replaced with a progress indicator ("Creating database table…")
- Status polling: `GET /data-model/entities/{id}` polled every 2 seconds; when `status = "published"`, progress indicator replaced with a green "Published" badge and a toast "Entity is ready to use"
- On failure: red "Migration Failed" badge + expandable error details section; a "View Error" button shows the migration error message

---

### Story 5.1.3 — Entity Archival `[DONE]`

#### Backend
*As an API, I want to archive entities so that they are hidden from the runtime API without dropping data.*
- `POST /api/v1/data-model/entities/{id}/archive` transitions status to `archived`
- Blocked if other published entities have active FK relationships to this entity (returns 409 with list of dependent entities)

#### Frontend
*As a tenant administrator, I want to archive an obsolete entity from its detail page, with a warning if other entities depend on it, so that I don't accidentally break data relationships.*
- Entity detail page has an "Archive Entity" option in the "⋮" (more actions) menu
- If the entity has dependents: modal shows a warning list of dependent entities and blocks archival — "Remove the following relationships first: [list]"
- If no dependents: confirmation modal "Archive [Entity Name]? It will no longer appear in reports or forms. Historical data is preserved."
- After archiving: entity card on the list page shows an "Archived" grey badge; entity hidden from all dropdown/select lists in the rest of the UI

---

### Story 5.1.4 — Virtual Entity (PostgreSQL View Mapping) `[DONE]`

#### Backend
*As an API, I want to map a virtual entity to an existing database view, so that complex SQL queries are accessible through the standard CRUD API.*
- `entity_type = "virtual"` and `table_name` set to an existing view name; optionally `meta_data.view_sql` provides the `CREATE OR REPLACE VIEW` DDL
- `POST`, `PUT`, `DELETE` on virtual entities return 405 Method Not Allowed
- `GET` list, single-record, metadata, and aggregate endpoints work identically to regular entities

#### Frontend
*As a tenant administrator creating an entity, I want a "Virtual Entity" option that lets me enter a view name or SQL definition, so that I can expose complex reporting data without duplicating API logic.*
- "New Entity" modal has an "Entity Type" radio group: "Standard" (default) / "Virtual (read-only)"
- When "Virtual" is selected: the form adapts to show a "PostgreSQL View Name" text input and an optional "View SQL Definition" code textarea
- View SQL textarea has syntax highlighting (CodeMirror or similar) and a "Validate SQL" button (dry-runs against the DB)
- Virtual entities shown with a "Virtual" purple badge on the entity list; no "Publish" button needed — they appear immediately once the view exists
- Field designer for virtual entities is read-only — fields are auto-introspected from the view's columns

---

### Story 5.1.5 — Entity Versioning (Record History) `[OPEN]`

#### Backend
*As an API, I want entities with `is_versioned = true` to store a full history of record changes in a shadow table, so that data changes are auditable at the record level.*
- On `update_record()` for a versioned entity: previous row inserted into `{entity_name}_versions` shadow table before applying the update
- `GET /api/v1/dynamic-data/{entity}/records/{id}/versions` returns version history in reverse chronological order
- Each version record: `version_number`, `changed_by`, `changed_at`, `changes` (JSON diff of modified fields only)

#### Frontend
*As a user viewing a record detail page for a versioned entity, I want a "History" tab that shows me a timeline of every change made to this record with the before/after values, so that I can understand how the data evolved.*
- Record detail page for versioned entities shows a "History" tab alongside "Details" and "Related"
- History tab renders a vertical timeline component: each entry shows timestamp, who changed it, and a diff table (old value → new value per changed field)
- Changed fields highlighted in amber; unchanged fields not shown (diff view, not full record)
- "Restore this version" button on each history entry (admin only) opens a confirmation modal before reverting

---

## Feature 5.2 — Field System `[DONE / OPEN]`

### Story 5.2.1 — Field Types and Constraints `[DONE]`

#### Backend
*As an API, I want to support a rich set of field types with configurable constraints, so that custom entities can model any business data accurately.*
- Supported `field_type`: `text`, `number`, `decimal`, `boolean`, `date`, `datetime`, `email`, `phone`, `url`, `select`, `multi_select`, `relationship`, `lookup`, `calculated`, `uuid`, `json`
- Constraints per field: `is_required`, `is_unique`, `is_indexed`, `is_nullable`, `max_length`, `min_length`, `max_value`, `min_value`, `precision`, `decimal_places`
- Constraints enforced at DB level (DDL) and in `_validate_and_prepare_data()`

#### Frontend
*As a tenant administrator in the field designer, I want to add fields by selecting a field type from a type palette and then configure its constraints in a properties panel, so that defining a data model feels like filling out a form.*
- Entity field designer page: left panel = list of defined fields (draggable to reorder); right panel = field property form
- "Add Field" button opens a type picker modal with icon-cards for each field type grouped by category (Text, Number, Date, Selection, Relationship, Advanced)
- Selecting a type creates a new field and opens its property panel: Name, Label, Required toggle, Unique toggle, and type-specific options (e.g. Max Length for text, Min/Max for number)
- Constraint violations shown inline: if `is_unique` is toggled on a `multi_select` field, a warning tooltip appears "Unique constraint not supported for multi-select fields"
- Field list shows a summary chip per field: type icon + name + constraint badges (Required, Unique, Indexed)

---

### Story 5.2.2 — Select/Enum Fields with Allowed Values `[OPEN]`

#### Backend
*As an API, I want select fields to validate submitted values against a defined list, so that data integrity is enforced for enumerable fields.*
- `allowed_values` JSONB schema: `[{"value": "active", "label": "Active", "label_i18n": {"en": "Active", "de": "Aktiv"}}]`
- `_validate_and_prepare_data()` rejects values not in the list; error: `"Invalid value. Allowed: active, inactive, pending"`
- `allowed_values` exposed in `GET /dynamic-data/{entity}/metadata`

#### Frontend
*As a tenant administrator configuring a select field, I want to add allowed values using a tag-like input where I can type a value, add a display label, and optionally add translated labels, so that dropdown options are defined visually.*
- When `field_type = "select"` or `"multi_select"` is chosen: the property panel shows an "Allowed Values" section
- Value entry: tag-input component — type a value key (e.g. `active`), press Enter to add; display label auto-fills from the key
- Each value tag shows the `value` key and `label` inline; clicking a tag opens a mini-editor for the label and i18n translations
- Drag handles on tags for reordering the dropdown option order
- "Import from CSV" button to bulk-add values from a two-column CSV (value, label)
- Preview at the bottom of the panel: renders the actual `FlexSelect` dropdown with all defined values

---

### Story 5.2.3 — Calculated Fields `[DONE]`

#### Backend
*As an API, I want to generate PostgreSQL `GENERATED ALWAYS AS` columns from formula expressions, so that derived values are always consistent.*
- `is_calculated = true` and `calculation_formula` (e.g. `{unit_price} * {quantity}`) generates DDL computed column
- `{field_name}` tokens replaced with bare column names; validated before migration
- Calculated fields flagged as `read_only: true` in metadata response

#### Frontend
*As a tenant administrator adding a calculated field, I want to write a formula using field name tokens and see a preview of what the calculation will produce, so that I can verify the formula before publishing.*
- Calculated field type shows a "Formula" textarea in the property panel
- Token auto-complete: typing `{` shows a dropdown of existing field names in the entity
- Formula preview: a sample row (using dummy values) shows the computed result below the formula input
- Field preview labeled "Computed value (read-only)" — rendered as a greyed, disabled input in form mockups
- Validation: if a referenced `{field_name}` doesn't exist in the entity, an inline error is shown before save

---

### Story 5.2.4 — Custom Validation Rules `[OPEN]`

#### Backend
*As an API, I want to apply custom validation rules from `validation_rules` JSONB on field definitions, so that business-specific constraints are enforced on data entry.*
- `validation_rules`: `[{"type": "regex", "pattern": "^[A-Z]{2}\\d{4}$", "message": "Must be 2 letters + 4 digits"}]`
- Supported types: `regex`, `min_length`, `max_length`, `min_value`, `max_value`
- Applied in `FieldTypeMapper.validate_value()` after standard constraint checks

#### Frontend
*As a tenant administrator, I want to add custom validation rules to a field using a rule builder interface, so that I can enforce business-specific patterns like invoice number formats without writing code.*
- Field property panel has an "Advanced Validation" section (collapsed by default)
- "Add Rule" button shows a rule-type select and type-specific inputs:
  - `regex`: pattern input + test string input with live pass/fail indicator
  - `min_length` / `max_length`: number input
  - `min_value` / `max_value`: number input
- Each rule shows a human-readable summary: "Must match pattern: `^[A-Z]{2}`" with an error message field
- Rules listed as chips; click to edit, × to delete

---

## Feature 5.3 — Relationships and Lookups `[DONE]`

### Story 5.3.1 — Foreign Key Relationship Fields `[DONE]`

#### Backend
*As an API, I want relationship fields to generate PostgreSQL FK constraints and support inline record expansion, so that related data is linkable and queryable.*
- Relationship field: `ref_entity_name`, `ref_field`, `relationship_type` (`many-to-one`, `one-to-many`, `many-to-many`), `on_delete` (`CASCADE`/`SET NULL`/`RESTRICT`)
- `GET /dynamic-data/{entity}/records?expand=customer_id` inlines related records as `customer_id_data` (1 IN query, no N+1)

#### Frontend
*As a tenant administrator adding a relationship field, I want to select the target entity and field from dropdowns and preview the generated FK, so that I can define relationships without knowing SQL.*
- Relationship field type opens a property panel with: Related Entity (searchable select of all published entities), Display Field (select of fields in the target entity, auto-defaults to the first `text` field), Relationship Type (radio: Many-to-One / One-to-Many), On Delete Behavior (select)
- Live preview: "This field creates a foreign key → `{target_entity}.{target_field}`"
- In record forms: relationship fields render as a searchable `FlexSelect` that queries `GET /dynamic-data/{ref_entity}/records?search=`

---

### Story 5.3.2 — Lookup Fields `[DONE]`

#### Backend
*As an API, I want lookup fields to resolve options from configurable lookup tables, so that dropdown values can be managed centrally.*
- Lookup field config: `lookup_entity`, `value_field`, `label_field`
- `GET /api/v1/lookups/{name}?search=&parent_value=` returns filtered options

#### Frontend
*As a tenant administrator managing lookups, I want a dedicated Lookups page where I can create lookup tables and add values, so that dropdown options are managed in one place.*
- Route: `#/nocode/lookups` shows a list of lookup configurations
- "New Lookup" opens a modal: Lookup Name, Source (entity-based or static list), if entity-based: select entity + value field + label field
- Static list lookup: tag-input for values (similar to select field allowed values)
- In record forms: lookup fields render as `FlexSelect` with lazy-load search; selecting an option shows both the value key and label

---

## Feature 5.4 — Soft Delete `[OPEN]`

### Story 5.4.1 — Soft Delete Implementation `[OPEN]`

#### Backend
*As an API, I want entities with `supports_soft_delete = true` to mark records as deleted without removing the row, so that accidental deletions can be recovered.*
- `DELETE /dynamic-data/{entity}/records/{id}` sets `deleted_at = NOW()` instead of `DELETE FROM`
- `list_records()` appends `WHERE deleted_at IS NULL` automatically for soft-delete entities
- `include_deleted=true` query parameter shows soft-deleted records (admin permission required)
- Aggregate queries also filter out soft-deleted records by default

#### Frontend
*As a tenant administrator, I want a "Show Deleted" toggle on entity list pages for entities with soft-delete enabled, so that I can recover accidentally deleted records.*
- Entity list page toolbar has a "Show Deleted" toggle (only rendered if `entity.supports_soft_delete = true`)
- When "Show Deleted" is ON: deleted rows shown with a red strikethrough background and a "Restore" action button instead of "Edit/Delete"
- "Restore" button sends `POST /dynamic-data/{entity}/records/{id}/restore` and moves the row back to normal display
- Permanent "Delete forever" button available in the deleted row's action menu (admin only) with a strong confirmation modal: "This cannot be undone. Type DELETE to confirm."
