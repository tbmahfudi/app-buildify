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

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/data-model/entities` | List all entity definitions |
| `POST` | `/data-model/entities` | Create entity definition |
| `GET` | `/data-model/entities/{id}` | Get entity definition |
| `PUT` | `/data-model/entities/{id}` | Update entity definition |
| `DELETE` | `/data-model/entities/{id}` | Delete entity definition |
| `POST` | `/data-model/entities/{id}/fields` | Add field to entity |
| `PUT` | `/data-model/entities/{id}/fields/{fid}` | Update field |
| `DELETE` | `/data-model/entities/{id}/fields/{fid}` | Remove field |

---

## Dynamic Data

Perform CRUD on runtime entity instances.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/dynamic-data/{entity_name}` | List records |
| `POST` | `/dynamic-data/{entity_name}` | Create record |
| `GET` | `/dynamic-data/{entity_name}/{id}` | Get record |
| `PUT` | `/dynamic-data/{entity_name}/{id}` | Update record |
| `DELETE` | `/dynamic-data/{entity_name}/{id}` | Delete record |

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
