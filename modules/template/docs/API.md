# TEMPLATE Module — API Reference

Base path: `/api/v1/modules/TEMPLATE/`

All endpoints require:
- `Authorization: Bearer <token>`
- Active tenant context (automatically applied by the platform)

---

## Endpoints

### `GET /api/v1/modules/TEMPLATE/example`

List example records for the current tenant.

**Permissions required:** `TEMPLATE:read`

**Query params:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number (1-indexed) |
| `page_size` | int | 25 | Items per page (max 100) |

**Response `200 OK`:**
```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 25
}
```

**Error responses:**

| Status | Meaning |
|--------|---------|
| `401` | Missing or invalid token |
| `403` | Insufficient permissions |
| `422` | Invalid query params |
