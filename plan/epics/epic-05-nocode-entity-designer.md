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
- Route: `#/nocode/data-model` → `data-model.html` + `data-model-page.js`
- Layout: FlexStack(direction=vertical) > page-header, filter-bar, entity-grid
  - page-header: FlexToolbar — "Data Model" title | "New Entity" FlexButton(primary)
  - filter-bar: FlexCluster — tabs (All | My Module | Platform) | status chips (Draft | Published | Archived)
  - entity-grid: FlexGrid(columns=3, gap=md) — FlexCard per entity (status FlexBadge, field count, module name)

- FlexModal(size=md) — "New Entity" form, triggered by toolbar button
  - fields: Display Name (FlexInput, required) | Internal Name (FlexInput, auto-derived snake_case, editable; live API path preview e.g. `GET /dynamic-data/sales_order/records`) | Plural Label (FlexInput) | Icon (icon picker grid) | Category (FlexSelect) | Module (FlexSelect)
  - footer: Cancel | Create Entity (primary)
  - on save: modal closes; entity card appears with FlexBadge "Draft"; user auto-navigated to field designer page

- Interactions:
  - click "New Entity": opens FlexModal(size=md)
  - type Display Name: Internal Name auto-derives (snake_case); API path preview updates
  - click status chip (filter): entity grid filters client-side
  - click tab (All/My Module/Platform): entity grid re-fetches with scope filter
  - click entity card: navigates to entity field designer `#/nocode/data-model/{id}`

- States:
  - loading: entity grid shows skeleton cards while GET /data-model/entities resolves
  - empty: illustration + "No entities yet. Create your first entity." + "New Entity" FlexButton(primary)
  - error: FlexAlert(type=error) "Could not load entities. Retry?"

---

### Story 5.1.2 — Entity Publishing and Migration `[DONE]`

#### Backend
*As an API, I want to publish an entity by running DDL to create the physical database table, so that the entity can store real records.*
- `POST /api/v1/data-model/entities/{id}/publish` transitions `status → migrating`, runs Alembic DDL via `MigrationGenerator`, then transitions to `published`
- On failure: status reverts to `draft`; error details returned
- While `migrating`: write operations return 503; reads return last valid model

#### Frontend
*As a tenant administrator who has finished designing an entity, I want to click "Publish" and see a real-time status indicator while the database table is being created, so that I know when the entity is ready to use.*
- Route: `#/nocode/data-model/{id}` → entity field designer page

- FlexModal(size=sm) — publish confirm, triggered by "Publish Entity" button in page header
  - body: "Publishing will create a database table for [Entity Name]. This action cannot be easily undone. Continue?"
  - footer: Cancel | Publish (FlexButton, primary)
  - on confirm: POST /data-model/entities/{id}/publish → button replaced with "Creating database table…" progress indicator

- Interactions:
  - click "Publish Entity" (disabled if no fields defined): opens confirm FlexModal(size=sm)
  - confirm publish: POST /data-model/entities/{id}/publish → polling every 2s via GET /data-model/entities/{id}
  - poll returns `status = "published"`: progress indicator → FlexBadge(color=success) "Published" + toast "Entity is ready to use"
  - poll returns failure: FlexBadge(color=danger) "Migration Failed" + "View Error" FlexButton → FlexAccordion expands with migration error message

- States:
  - draft: "Publish Entity" button enabled (if ≥1 field defined); disabled with tooltip "Add at least one field first" if empty
  - migrating: progress indicator shown; Publish button hidden; field editing disabled
  - published: FlexBadge(color=success) "Published" in header; Publish button replaced
  - migration-failed: FlexBadge(color=danger) "Migration Failed" + expandable error section

---

### Story 5.1.3 — Entity Archival `[DONE]`

#### Backend
*As an API, I want to archive entities so that they are hidden from the runtime API without dropping data.*
- `POST /api/v1/data-model/entities/{id}/archive` transitions status to `archived`
- Blocked if other published entities have active FK relationships to this entity (returns 409 with list of dependent entities)

#### Frontend
*As a tenant administrator, I want to archive an obsolete entity from its detail page, with a warning if other entities depend on it, so that I don't accidentally break data relationships.*
- Route: `#/nocode/data-model/{id}` → "⋮" more-actions menu in page header

- FlexModal(size=sm) — archive confirm (no dependents), triggered by "Archive Entity" in ⋮ menu
  - body: "Archive [Entity Name]? It will no longer appear in reports or forms. Historical data is preserved."
  - footer: Cancel | Archive (FlexButton, variant=danger)
  - on confirm: POST /data-model/entities/{id}/archive → redirect to entity list; card shows FlexBadge(color=grey) "Archived"

- FlexModal(size=sm) — archive blocked (has dependents)
  - body: FlexAlert(type=warning) "Remove the following relationships first:" + list of dependent entity names
  - footer: Close only (archive blocked)

- Interactions:
  - click "Archive Entity" in ⋮ menu: GET /data-model/entities/{id} to check dependents → opens blocked or confirm modal accordingly
  - confirm archive: POST /data-model/entities/{id}/archive → redirect to list; entity hidden from all dropdowns/selects site-wide

---

### Story 5.1.4 — Virtual Entity (PostgreSQL View Mapping) `[DONE]`

#### Backend
*As an API, I want to map a virtual entity to an existing database view, so that complex SQL queries are accessible through the standard CRUD API.*
- `entity_type = "virtual"` and `table_name` set to an existing view name; optionally `meta_data.view_sql` provides the `CREATE OR REPLACE VIEW` DDL
- `POST`, `PUT`, `DELETE` on virtual entities return 405 Method Not Allowed
- `GET` list, single-record, metadata, and aggregate endpoints work identically to regular entities

#### Frontend
*As a tenant administrator creating an entity, I want a "Virtual Entity" option that lets me enter a view name or SQL definition, so that I can expose complex reporting data without duplicating API logic.*
- Route: `#/nocode/data-model` — "New Entity" FlexModal (see Story 5.1.1), with Entity Type toggle

- FlexModal(size=md) — "New Entity" form (Virtual variant)
  - Entity Type: FlexRadio group — Standard (default) | Virtual (read-only)
  - when Virtual selected: form swaps to show PostgreSQL View Name (FlexInput) + View SQL Definition (code textarea, syntax highlighting, optional)
  - "Validate SQL" FlexButton(ghost): dry-runs SQL against the DB → inline pass/fail result
  - footer: Cancel | Create Virtual Entity (primary)

- Interactions:
  - select "Virtual" radio: form fields swap; standard fields hidden; view-specific fields shown
  - click "Validate SQL": POST /data-model/entities/validate-sql → inline "Valid ✓" or error message below textarea
  - save: virtual entity created; appears immediately on list with FlexBadge(color=purple) "Virtual" — no Publish step needed
  - open field designer for virtual entity: all fields read-only (auto-introspected from view columns; no Add Field button)

---

### Story 5.1.5 — Entity Versioning (Record History) `[OPEN]`

#### Backend
*As an API, I want entities with `is_versioned = true` to store a full history of record changes in a shadow table, so that data changes are auditable at the record level.*
- On `update_record()` for a versioned entity: previous row inserted into `{entity_name}_versions` shadow table before applying the update
- `GET /api/v1/dynamic-data/{entity}/records/{id}/versions` returns version history in reverse chronological order
- Each version record: `version_number`, `changed_by`, `changed_at`, `changes` (JSON diff of modified fields only)

#### Frontend
*As a user viewing a record detail page for a versioned entity, I want a "History" tab that shows me a timeline of every change made to this record with the before/after values, so that I can understand how the data evolved.*
- Route: `#/dynamic-data/{entity}/records/{id}` → record detail page (History tab, shown only when `entity.is_versioned = true`)

- FlexTabs — record detail tabs: Details | Related | History (versioned entities only)
  - History tab: vertical timeline (GET /dynamic-data/{entity}/records/{id}/versions, reverse chronological)
    - each entry: timestamp + actor avatar + name | diff table (old value → new value per changed field, amber highlight) | "Restore this version" FlexButton(ghost) [admin only]

- FlexModal(size=sm) — restore confirm, triggered by "Restore this version"
  - body: "Restore record to version from [date]? Current values will be overwritten."
  - footer: Cancel | Restore (FlexButton, variant=danger)
  - on confirm: POST /dynamic-data/{entity}/records/{id}/restore → record refreshes; new history entry appears at top

- Interactions:
  - click History tab: GET /dynamic-data/{entity}/records/{id}/versions → timeline renders
  - click "Restore this version" (admin only): opens restore confirm FlexModal
  - confirm restore: record reverts; page refreshes; FlexAlert(type=success) toast "Record restored to version [date]"

- States:
  - loading (History tab): timeline shows skeleton entries while version list resolves
  - no-history: "No changes recorded yet"

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
- Route: `#/nocode/data-model/{id}` → `entity-designer.html` + `entity-designer-page.js`
- Layout: FlexSplitPane(initial-split=35%) > fields-panel, properties-panel
  - fields-panel: FlexStack(direction=vertical) > fields-header, fields-list
    - fields-header: FlexToolbar — entity name | "Add Field" FlexButton(primary) | "Publish Entity" FlexButton
    - fields-list: FlexStack(gap=sm) — draggable field rows (type icon + name + constraint FlexBadge chips: Required, Unique, Indexed)
  - properties-panel: FlexSection — field property form for selected field (Name, Label, Required FlexCheckbox, Unique FlexCheckbox, type-specific options)

- FlexModal(size=md) — field type picker, triggered by "Add Field"
  - icon-card grid grouped by category: Text | Number | Date | Selection | Relationship | Advanced
  - click a type card: modal closes; new field created and selected; properties-panel loads its form

- Interactions:
  - click "Add Field": opens field type picker FlexModal(size=md)
  - click field type card: creates field; properties-panel opens with that field's form
  - drag field row in list: reorders fields; auto-saves order
  - click field row: loads its form in properties-panel
  - toggle `is_unique` on a multi_select field: FlexTooltip "Unique constraint not supported for multi-select fields"; toggle reverts

- States:
  - no-field-selected: properties-panel shows "Select a field to edit its properties"
  - empty (fields list): "No fields yet. Add a field to start." + "Add Field" FlexButton

---

### Story 5.2.2 — Select/Enum Fields with Allowed Values `[OPEN]`

#### Backend
*As an API, I want select fields to validate submitted values against a defined list, so that data integrity is enforced for enumerable fields.*
- `allowed_values` JSONB schema: `[{"value": "active", "label": "Active", "label_i18n": {"en": "Active", "de": "Aktiv"}}]`
- `_validate_and_prepare_data()` rejects values not in the list; error: `"Invalid value. Allowed: active, inactive, pending"`
- `allowed_values` exposed in `GET /dynamic-data/{entity}/metadata`

#### Frontend
*As a tenant administrator configuring a select field, I want to add allowed values using a tag-like input where I can type a value, add a display label, and optionally add translated labels, so that dropdown options are defined visually.*
- Route: `#/nocode/data-model/{id}` — properties-panel when field_type = "select" or "multi_select"

- Allowed Values section (inside field properties-panel):
  - tag-input: type a value key (e.g. `active`) + Enter to add; display label auto-fills from key
  - each tag: shows value key + label inline; drag handle for reorder; × to remove
  - click tag: opens mini FlexModal editor — Label (FlexInput) | i18n labels (FlexInput per locale)
  - "Import from CSV" FlexButton: opens file picker; accepts 2-column CSV (value, label); bulk-adds tags
  - preview panel at bottom: renders live FlexSelect dropdown with all defined values

- Interactions:
  - type value key + Enter: tag created; label auto-fills
  - drag tag: reorders allowed values list
  - click tag: opens mini label editor FlexModal
  - click "Import from CSV": file input → parses CSV → tags bulk-added
  - any change to tags: preview FlexSelect updates immediately

---

### Story 5.2.3 — Calculated Fields `[DONE]`

#### Backend
*As an API, I want to generate PostgreSQL `GENERATED ALWAYS AS` columns from formula expressions, so that derived values are always consistent.*
- `is_calculated = true` and `calculation_formula` (e.g. `{unit_price} * {quantity}`) generates DDL computed column
- `{field_name}` tokens replaced with bare column names; validated before migration
- Calculated fields flagged as `read_only: true` in metadata response

#### Frontend
*As a tenant administrator adding a calculated field, I want to write a formula using field name tokens and see a preview of what the calculation will produce, so that I can verify the formula before publishing.*
- Route: `#/nocode/data-model/{id}` — properties-panel when field_type = "calculated"

- Calculated field properties-panel:
  - Formula (FlexTextarea, monospace) — token auto-complete: typing `{` triggers a dropdown listing existing entity field names
  - formula preview: sample row with dummy values → computed result shown below formula textarea
  - field form preview: greyed disabled FlexInput labeled "Computed value (read-only)"

- Interactions:
  - type `{` in formula textarea: dropdown appears with existing field names; click to insert token
  - any formula change: preview recalculates with dummy values in real time
  - save with unknown `{field_name}` token: inline error "Field '[name]' does not exist in this entity" — save blocked

---

### Story 5.2.4 — Custom Validation Rules `[OPEN]`

#### Backend
*As an API, I want to apply custom validation rules from `validation_rules` JSONB on field definitions, so that business-specific constraints are enforced on data entry.*
- `validation_rules`: `[{"type": "regex", "pattern": "^[A-Z]{2}\\d{4}$", "message": "Must be 2 letters + 4 digits"}]`
- Supported types: `regex`, `min_length`, `max_length`, `min_value`, `max_value`
- Applied in `FieldTypeMapper.validate_value()` after standard constraint checks

#### Frontend
*As a tenant administrator, I want to add custom validation rules to a field using a rule builder interface, so that I can enforce business-specific patterns like invoice number formats without writing code.*
- Route: `#/nocode/data-model/{id}` — "Advanced Validation" FlexAccordion section in field properties-panel (collapsed by default)

- Advanced Validation section:
  - "Add Rule" FlexButton: shows rule-type FlexSelect → type-specific inputs appear:
    - regex: pattern (FlexInput) + test string (FlexInput) with live pass/fail indicator
    - min_length / max_length: number (FlexInput)
    - min_value / max_value: number (FlexInput)
  - each rule rendered as a chip: human-readable summary (e.g. "Must match `^[A-Z]{2}`") + error message FlexInput | × remove
  - click chip: expands inline editor for that rule

- Interactions:
  - click "Add Rule": rule-type FlexSelect appears; select type → type-specific inputs shown
  - type in regex test string: live pass ✓ / fail ✗ indicator updates in real time
  - click × on rule chip: removes rule from list
  - click rule chip body: expands inline editor

---

## Feature 5.3 — Relationships and Lookups `[DONE]`

### Story 5.3.1 — Foreign Key Relationship Fields `[DONE]`

#### Backend
*As an API, I want relationship fields to generate PostgreSQL FK constraints and support inline record expansion, so that related data is linkable and queryable.*
- Relationship field: `ref_entity_name`, `ref_field`, `relationship_type` (`many-to-one`, `one-to-many`, `many-to-many`), `on_delete` (`CASCADE`/`SET NULL`/`RESTRICT`)
- `GET /dynamic-data/{entity}/records?expand=customer_id` inlines related records as `customer_id_data` (1 IN query, no N+1)

#### Frontend
*As a tenant administrator adding a relationship field, I want to select the target entity and field from dropdowns and preview the generated FK, so that I can define relationships without knowing SQL.*
- Route: `#/nocode/data-model/{id}` — properties-panel when field_type = "relationship"

- Relationship field properties-panel:
  - Related Entity (FlexSelect, searchable, all published entities)
  - Display Field (FlexSelect, fields of selected entity, auto-defaults to first text field)
  - Relationship Type (FlexRadio): Many-to-One | One-to-Many
  - On Delete Behavior (FlexSelect): CASCADE | SET NULL | RESTRICT
  - live preview text: "This field creates a foreign key → `{target_entity}.{target_field}`"

- Interactions:
  - select Related Entity: Display Field FlexSelect repopulates with that entity's fields
  - any change to relationship config: live preview text updates immediately
  - in record forms (runtime): relationship field renders as FlexSelect (searchable) querying GET /dynamic-data/{ref_entity}/records?search=[term]

---

### Story 5.3.2 — Lookup Fields `[DONE]`

#### Backend
*As an API, I want lookup fields to resolve options from configurable lookup tables, so that dropdown values can be managed centrally.*
- Lookup field config: `lookup_entity`, `value_field`, `label_field`
- `GET /api/v1/lookups/{name}?search=&parent_value=` returns filtered options

#### Frontend
*As a tenant administrator managing lookups, I want a dedicated Lookups page where I can create lookup tables and add values, so that dropdown options are managed in one place.*
- Route: `#/nocode/lookups` → `lookups.html` + `lookups-page.js`
- Layout: FlexStack(direction=vertical) > page-header, lookups-list
  - page-header: FlexToolbar — "Lookups" title | "New Lookup" FlexButton(primary)
  - lookups-list: FlexDataGrid — Name, Source Type, Value Count, Actions

- FlexModal(size=md) — "New Lookup" form
  - fields: Lookup Name (FlexInput, required) | Source (FlexRadio): Entity-based | Static list
  - entity-based fields: Entity (FlexSelect) | Value Field (FlexSelect) | Label Field (FlexSelect)
  - static list: tag-input (same pattern as select field allowed values)
  - footer: Cancel | Save Lookup (primary)

- Interactions:
  - click "New Lookup": opens FlexModal(size=md)
  - toggle Source → Entity-based: entity/value/label FlexSelects shown; tag-input hidden
  - toggle Source → Static list: tag-input shown; entity fields hidden
  - in record forms (runtime): lookup field renders as FlexSelect with lazy-load search (GET /lookups/{name}?search=); selected option shows value key + label

- States:
  - loading: FlexDataGrid skeleton while GET /nocode/lookups resolves
  - empty: "No lookups yet" + "New Lookup" FlexButton(primary)

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
- Route: `#/dynamic-data/{entity}` → entity list page (toolbar augmented when `entity.supports_soft_delete = true`)

- Interactions:
  - "Show Deleted" FlexCheckbox toggle (only rendered when soft-delete enabled): appends `include_deleted=true` to GET /dynamic-data/{entity}/records → grid refreshes; deleted rows shown with red strikethrough row styling + "Restore" action instead of Edit/Delete
  - click "Restore" on deleted row: POST /dynamic-data/{entity}/records/{id}/restore → row transitions back to normal; "Restore" button removed
  - click "Delete forever" in deleted row ⋮ menu (admin only): opens strong confirm FlexModal(size=sm) — body "This cannot be undone. Type DELETE to confirm." + FlexInput for confirmation text; Delete button enabled only when input matches "DELETE"
  - confirm "Delete forever": DELETE /dynamic-data/{entity}/records/{id}?permanent=true → row removed from grid

- States:
  - show-deleted ON: deleted rows visible with red strikethrough; grid shows deleted count chip in toolbar
  - show-deleted OFF (default): only active records shown
