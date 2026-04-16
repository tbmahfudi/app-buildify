# API Reference

All endpoints are prefixed with `/api/v1/`. The interactive Swagger UI is available at `/docs` and Redoc at `/redoc`.

---

## Authentication

### POST `/auth/login`

Authenticate a user and receive JWT tokens.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "Password@123"
}
```

**Response** `200`:
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "tenant_id": "uuid",
    "roles": [],
    "permissions": []
  }
}
```

**Errors**: `401` invalid credentials | `423` account locked | `429` rate limit exceeded

---

### POST `/auth/refresh`

Exchange a refresh token for a new access token.

**Request**:
```json
{ "refresh_token": "<jwt>" }
```

**Response** `200`:
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

---

### POST `/auth/logout`

Revoke the current access token.

**Headers**: `Authorization: Bearer <token>`

**Response** `200`:
```json
{ "message": "Logged out successfully" }
```

---

### POST `/auth/forgot-password`

Initiate a password reset flow.

**Request**:
```json
{ "email": "user@example.com" }
```

---

### POST `/auth/reset-password`

Complete password reset with a reset token.

**Request**:
```json
{
  "token": "<reset-token>",
  "new_password": "NewPassword@456"
}
```

---

## Users

All user endpoints require `Authorization: Bearer <token>`.

| Method | Path | Permission | Description |
|--------|------|-----------|-------------|
| `GET` | `/users` | `users:read:tenant` | List all users in tenant |
| `POST` | `/users` | `users:create:tenant` | Create a new user |
| `GET` | `/users/{id}` | `users:read:tenant` | Get user by ID |
| `PUT` | `/users/{id}` | `users:update:tenant` | Update user profile |
| `DELETE` | `/users/{id}` | `users:delete:tenant` | Deactivate a user |
| `POST` | `/users/{id}/roles` | `users:assign_roles:tenant` | Assign roles to user |
| `DELETE` | `/users/{id}/roles/{role_id}` | `users:assign_roles:tenant` | Remove role from user |
| `POST` | `/users/{id}/reset-password` | `users:update:tenant` | Admin password reset |

---

## RBAC

### Roles

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/rbac/roles` | List all roles |
| `POST` | `/rbac/roles` | Create a role |
| `GET` | `/rbac/roles/{id}` | Get role by ID |
| `PUT` | `/rbac/roles/{id}` | Update a role |
| `DELETE` | `/rbac/roles/{id}` | Delete a role |
| `POST` | `/rbac/roles/{id}/permissions` | Assign permissions to role |
| `DELETE` | `/rbac/roles/{id}/permissions/{perm_id}` | Remove permission from role |

### Permissions

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/rbac/permissions` | List all permissions |
| `POST` | `/rbac/permissions` | Create a permission |
| `GET` | `/rbac/permissions/{id}` | Get permission by ID |
| `PUT` | `/rbac/permissions/{id}` | Update a permission |
| `DELETE` | `/rbac/permissions/{id}` | Delete a permission |

### Groups

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/rbac/groups` | List all groups |
| `POST` | `/rbac/groups` | Create a group |
| `GET` | `/rbac/groups/{id}` | Get group by ID |
| `PUT` | `/rbac/groups/{id}` | Update a group |
| `DELETE` | `/rbac/groups/{id}` | Delete a group |
| `POST` | `/rbac/groups/{id}/roles` | Assign roles to group |
| `POST` | `/rbac/groups/{id}/users` | Add users to group |

---

## Organization

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/org/tenants` | List tenants (admin only) |
| `POST` | `/org/tenants` | Create tenant |
| `GET` | `/org/companies` | List companies in tenant |
| `POST` | `/org/companies` | Create company |
| `GET` | `/org/branches` | List branches |
| `POST` | `/org/branches` | Create branch |
| `GET` | `/org/departments` | List departments |
| `POST` | `/org/departments` | Create department |

---

## NoCode Data Model

Design-time API for defining custom entities, fields, relationships, and indexes.

### Entity Definitions

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/data-model/entities` | List all entity definitions |
| `POST` | `/data-model/entities` | Create entity definition |
| `GET` | `/data-model/entities/{id}` | Get entity definition |
| `PUT` | `/data-model/entities/{id}` | Update entity definition |
| `DELETE` | `/data-model/entities/{id}` | Delete entity definition |

**Entity types** (`entity_type` field):
- `custom` — standard user-defined table (default)
- `system` — platform-managed, read-only for tenants
- `virtual` — maps to an existing database view; read-only at runtime (no `POST`/`PUT`/`DELETE`)

For virtual entities, set `table_name` to the view name. To have the platform create the view automatically, include `view_sql` in `meta_data`:
```json
{
  "meta_data": {
    "view_sql": "CREATE OR REPLACE VIEW v_invoice_summary AS SELECT ...",
    "view_dependencies": ["financial_invoices", "financial_customers"]
  }
}
```

### Fields

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/data-model/entities/{id}/fields` | Add field to entity |
| `PUT` | `/data-model/entities/{id}/fields/{fid}` | Update field |
| `DELETE` | `/data-model/entities/{id}/fields/{fid}` | Remove field |

**Calculated fields** — set `is_calculated: true` and `calculation_formula` using `{field_name}` tokens:
```json
{
  "name": "line_total",
  "field_type": "decimal",
  "data_type": "NUMERIC(18,2)",
  "is_calculated": true,
  "calculation_formula": "{unit_price} * {quantity} * (1 + {tax_rate})"
}
```
On PostgreSQL, this emits `GENERATED ALWAYS AS (unit_price * quantity * (1 + tax_rate)) STORED` — the value is stored on disk and is filterable/sortable in aggregation queries.

### Relationships

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/data-model/entities/{id}/relationships` | Add relationship |
| `PUT` | `/data-model/entities/{id}/relationships/{rid}` | Update relationship |
| `DELETE` | `/data-model/entities/{id}/relationships/{rid}` | Remove relationship |

### Indexes

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/data-model/entities/{id}/indexes` | Add index |
| `PUT` | `/data-model/entities/{id}/indexes/{iid}` | Update index |
| `DELETE` | `/data-model/entities/{id}/indexes/{iid}` | Remove index |

---

## Dynamic Data

Runtime CRUD, aggregation, and relationship traversal for published NoCode entities.

> **Authoritative source**: The interactive Swagger UI at `/api/docs` always reflects the live router.
> All paths include the `/records` segment — earlier versions of this doc omitted it.

### CRUD

| Method | Path | Permission | Description |
|--------|------|-----------|-------------|
| `POST` | `/dynamic-data/{entity}/records` | `{entity}:create:tenant` | Create record |
| `GET` | `/dynamic-data/{entity}/records` | `{entity}:read:tenant` | List records (filter / sort / search / expand) |
| `GET` | `/dynamic-data/{entity}/records/{id}` | `{entity}:read:tenant` | Get single record |
| `PUT` | `/dynamic-data/{entity}/records/{id}` | `{entity}:update:own` or `:tenant` | Update record (partial) |
| `DELETE` | `/dynamic-data/{entity}/records/{id}` | `{entity}:delete:own` or `:tenant` | Delete record (soft if supported) |

> **Virtual entities** (`entity_type = "virtual"`) are read-only — `POST`, `PUT`, `DELETE` return `405 Method Not Allowed`.

### Bulk Operations

| Method | Path | Permission | Description |
|--------|------|-----------|-------------|
| `POST` | `/dynamic-data/{entity}/records/bulk` | `{entity}:create:tenant` | Bulk create |
| `PUT` | `/dynamic-data/{entity}/records/bulk` | `{entity}:update:tenant` | Bulk update (each record needs `id`) |
| `DELETE` | `/dynamic-data/{entity}/records/bulk` | `{entity}:delete:tenant` | Bulk delete (list of `ids`) |

Bulk operations continue on per-record errors and return a summary:
```json
{ "created": 10, "failed": 2, "errors": [{ "index": 3, "error": "..." }], "ids": [...] }
```

### Aggregation

```
GET /dynamic-data/{entity}/aggregate
```

**Required Permission:** `{entity}:read:tenant`

Run GROUP BY aggregations without fetching all rows. Supports virtual (view-backed) entities.

| Parameter | Type | Description |
|-----------|------|-------------|
| `group_by` | string | Comma-separated field names to group by, e.g. `status,region` |
| `metrics` | JSON array | **Required.** Array of `{field, function, alias?}` objects |
| `filters` | JSON string | Filter specification (same format as list endpoint) |
| `date_trunc` | string | Date truncation unit: `hour`, `day`, `week`, `month`, `quarter`, `year` |
| `date_field` | string | Which `group_by` field to apply `date_trunc` to |

**Supported `function` values:** `count`, `sum`, `avg`, `min`, `max`, `count_distinct`
Use `"field": "*"` with `"function": "count"` for `COUNT(*)`.

**Example — orders by status:**
```
GET /api/v1/dynamic-data/orders/aggregate
    ?group_by=status
    &metrics=[{"field":"id","function":"count","alias":"total"}]
```

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
  "groups": [
    { "status": "active", "total": 42 },
    { "status": "pending", "total": 7 }
  ],
  "total_groups": 2,
  "entity_name": "orders"
}
```

### List Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | int | Page number, default `1` |
| `page_size` | int | Items per page, default `25`, max `100` |
| `sort` | string | e.g. `name:asc,created_at:desc` |
| `search` | string | Global search across all text fields |
| `filters` | JSON string | Filter specification (see below) |
| `expand` | string | Comma-separated lookup field names to inline, e.g. `customer_id,region_id` |

**Filter format:**
```json
{
  "operator": "AND",
  "conditions": [
    { "field": "status", "operator": "eq", "value": "active" },
    { "field": "created_at", "operator": "gte", "value": "2026-01-01" }
  ]
}
```

**Supported filter operators:** `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `contains`, `starts_with`, `ends_with`, `like`, `ilike`, `in`, `not_in`, `is_null`, `is_not_null`

**`expand` — inline related records (depth = 1):**

`?expand=customer_id` fetches the related entity in a single `IN` query and inlines it as `customer_id_data: {...}` on every row. Unknown or non-lookup fields in `expand` are silently skipped.

**Response envelope:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 25,
  "pages": 6
}
```

### Metadata

```
GET /dynamic-data/{entity}/metadata
```

Returns field definitions, relationships, and display configuration for an entity.

```json
{
  "entity_name": "customers",
  "display_name": "Customers",
  "fields": [...],
  "relationships": [...]
}
```

### Validation Errors

When field validation fails on `POST` or `PUT`, the response is `400` with per-field detail:

```json
{
  "detail": "Validation failed: 2 errors",
  "errors": [
    { "field": "email", "message": "Email is required" },
    { "field": "phone", "message": "Must be 20 characters or less" }
  ]
}
```

`errors` is absent on all other error types so existing callers that read only `detail` are unaffected.

---

## Workflows

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/workflows` | List workflows |
| `POST` | `/workflows` | Create workflow |
| `GET` | `/workflows/{id}` | Get workflow |
| `PUT` | `/workflows/{id}` | Update workflow |
| `DELETE` | `/workflows/{id}` | Delete workflow |
| `POST` | `/workflows/{id}/trigger` | Manually trigger workflow |

---

## Automations

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/automations` | List automation rules |
| `POST` | `/automations` | Create rule |
| `GET` | `/automations/{id}` | Get rule |
| `PUT` | `/automations/{id}` | Update rule |
| `DELETE` | `/automations/{id}` | Delete rule |
| `PUT` | `/automations/{id}/toggle` | Enable/disable rule |

---

## Dashboards

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/dashboards` | List dashboards |
| `POST` | `/dashboards` | Create dashboard |
| `GET` | `/dashboards/{id}` | Get dashboard config |
| `PUT` | `/dashboards/{id}` | Update dashboard |
| `DELETE` | `/dashboards/{id}` | Delete dashboard |
| `GET` | `/dashboards/{id}/data` | Fetch widget data |
| `POST` | `/dashboards/{id}/widgets` | Add widget |
| `PUT` | `/dashboards/{id}/widgets/{wid}` | Update widget |
| `DELETE` | `/dashboards/{id}/widgets/{wid}` | Remove widget |

---

## Reports

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/reports` | List reports |
| `POST` | `/reports` | Create report |
| `GET` | `/reports/{id}` | Get report definition |
| `PUT` | `/reports/{id}` | Update report |
| `DELETE` | `/reports/{id}` | Delete report |
| `POST` | `/reports/{id}/run` | Execute report and get results |
| `GET` | `/reports/{id}/export/pdf` | Export as PDF |
| `GET` | `/reports/{id}/export/excel` | Export as Excel |

---

## Lookup Configuration

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/lookups` | List lookup sources |
| `POST` | `/lookups` | Create lookup source |
| `GET` | `/lookups/{id}` | Get lookup config |
| `PUT` | `/lookups/{id}` | Update lookup |
| `DELETE` | `/lookups/{id}` | Delete lookup |
| `GET` | `/lookups/{id}/values` | Resolve lookup values |

---

## Scheduler

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/scheduler/jobs` | List scheduled jobs |
| `POST` | `/scheduler/jobs` | Create job |
| `PUT` | `/scheduler/jobs/{id}` | Update job |
| `DELETE` | `/scheduler/jobs/{id}` | Delete job |
| `POST` | `/scheduler/jobs/{id}/run` | Trigger job immediately |

---

## Audit Logs

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/audit` | List audit log entries |
| `GET` | `/audit/{id}` | Get audit entry detail |

**Query Parameters**: `user_id`, `action`, `resource`, `date_from`, `date_to`, `page`, `page_size`

---

## Modules

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/modules` | List registered modules |
| `POST` | `/modules/register` | Register a module |
| `GET` | `/modules/{name}` | Get module info |
| `POST` | `/modules/{name}/enable` | Enable module for tenant |
| `POST` | `/modules/{name}/disable` | Disable module for tenant |

---

## Admin: Security Policy

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/security/policy` | Get security policy |
| `PUT` | `/admin/security/policy` | Update security policy |
| `GET` | `/admin/security/policy/password` | Get password policy |
| `PUT` | `/admin/security/policy/password` | Update password policy |
| `GET` | `/admin/security/policy/session` | Get session policy |
| `PUT` | `/admin/security/policy/session` | Update session policy |
| `GET` | `/admin/security/policy/lockout` | Get lockout policy |
| `PUT` | `/admin/security/policy/lockout` | Update lockout policy |

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created |
| `400` | Bad request / validation error |
| `401` | Unauthenticated |
| `403` | Forbidden (insufficient permissions) |
| `404` | Resource not found |
| `405` | Method not allowed (e.g. write on a virtual entity) |
| `409` | Conflict (duplicate resource) |
| `422` | Unprocessable entity (schema error) |
| `423` | Locked (account locked out) |
| `429` | Too many requests (rate limited) |
| `500` | Internal server error |

---

## Pagination

List endpoints support pagination via query parameters:

```
GET /api/v1/users?page=1&page_size=20&sort_by=created_at&sort_order=desc
```

**Response envelope**:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```
