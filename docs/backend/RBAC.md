# RBAC System

## Overview

App-Buildify uses a **Role-Based Access Control (RBAC)** system. Every API operation is guarded by a specific permission, and users receive permissions through their assigned roles.

---

## Permission Format

Permissions follow the pattern:

```
resource:action:scope
```

| Part | Examples | Description |
|------|---------|-------------|
| `resource` | `users`, `data`, `financial.invoices` | The entity being accessed |
| `action` | `create`, `read`, `update`, `delete`, `*` | The operation |
| `scope` | `platform`, `tenant`, `company`, `branch`, `department` | Data boundary |

### Examples

| Permission Code | Meaning |
|----------------|---------|
| `users:create:tenant` | Create users anywhere in the tenant |
| `users:read:company` | Read users only within the current company |
| `data:*:branch` | Full CRUD on data within the current branch |
| `financial:invoices:read:company` | Read financial invoices at company level |
| `admin:security:update:tenant` | Modify security policies for the tenant |

---

## Data Model

```
User
 ├── UserRole (m:m)
 │    └── Role
 │         └── RolePermission (m:m)
 │              └── Permission
 └── UserGroup (m:m)
      └── Group
           └── GroupRole (m:m)
                └── Role
                     └── RolePermission (m:m)
                          └── Permission
```

**Effective permissions** = permissions from direct roles + permissions from group roles.

---

## System vs Tenant Roles

| Type | Description | Editable |
|------|-------------|---------|
| `system` | Built-in, immutable roles (e.g. `SuperAdmin`) | No |
| `tenant` | Created by tenant admins | Yes |

System roles are seeded during installation and cannot be deleted or modified.

---

## Default Roles (Seeded)

| Role | Scope | Permissions |
|------|-------|-------------|
| `SuperAdmin` | Platform | `*:*:platform` — full access |
| `TenantAdmin` | Tenant | All operations within the tenant |
| `CompanyAdmin` | Company | All operations within the company |
| `Manager` | Company | Read/write most resources at company level |
| `User` | Company | Read-only on most resources |

---

## Permission Checking

### Backend (Dependency Injection)

```python
# In a router
@router.post("/invoices")
def create_invoice(
    _: None = Depends(require_permission("financial:invoices:create:company")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ...
```

The `require_permission` dependency:
1. Loads `current_user.effective_permissions` (cached on the request)
2. Iterates permissions, checking for an exact or wildcard match
3. Also validates the scope against the user's current company/branch context
4. Returns `403 Forbidden` on failure

### Frontend (UI Filtering)

```javascript
// Filter menu items
filterMenuByRole(menuItems, currentUser)

// Check before rendering a button
if (hasPermission('financial:invoices:create:company')) {
    renderCreateButton()
}
```

> **Note**: Frontend RBAC is for UX only. All enforcement happens backend.

---

## API Endpoints

### Role Management

```
GET    /api/v1/rbac/roles                  List roles
POST   /api/v1/rbac/roles                  Create role
GET    /api/v1/rbac/roles/{id}             Get role
PUT    /api/v1/rbac/roles/{id}             Update role
DELETE /api/v1/rbac/roles/{id}             Delete role
POST   /api/v1/rbac/roles/{id}/permissions Assign permissions to role
DELETE /api/v1/rbac/roles/{id}/permissions/{perm_id}  Remove permission
```

### Permission Management

```
GET    /api/v1/rbac/permissions            List permissions
POST   /api/v1/rbac/permissions            Create permission
GET    /api/v1/rbac/permissions/{id}       Get permission
PUT    /api/v1/rbac/permissions/{id}       Update permission
DELETE /api/v1/rbac/permissions/{id}       Delete permission
```

### Group Management

```
GET    /api/v1/rbac/groups                 List groups
POST   /api/v1/rbac/groups                 Create group
GET    /api/v1/rbac/groups/{id}            Get group
PUT    /api/v1/rbac/groups/{id}            Update group
DELETE /api/v1/rbac/groups/{id}            Delete group
POST   /api/v1/rbac/groups/{id}/roles      Assign roles to group
POST   /api/v1/rbac/groups/{id}/users      Add users to group
```

### User Role Assignment

```
POST   /api/v1/users/{id}/roles            Assign role to user
DELETE /api/v1/users/{id}/roles/{role_id}  Remove role from user
```

---

## Adding a New Permission

1. **Define** the permission string following the convention: `resource:action:scope`
2. **Create** it via `POST /api/v1/rbac/permissions`:
   ```json
   {
     "code": "inventory:items:create:company",
     "name": "Create Inventory Items",
     "description": "Allows creating inventory items at company level",
     "resource": "inventory",
     "action": "create",
     "scope": "company"
   }
   ```
3. **Assign** it to appropriate roles
4. **Guard** the API endpoint with `Depends(require_permission("inventory:items:create:company"))`
5. **Filter** the corresponding UI element with `hasPermission('inventory:items:create:company')`

---

## Multi-Tenant Isolation

- Each tenant has its own isolated set of roles and groups
- `tenant_id` is automatically injected into all RBAC queries
- System roles exist at the platform level and are shared read-only
- A user cannot access another tenant's roles even with `TenantAdmin`

---

## Wildcard Permissions

The `*` wildcard is supported in action and scope:

| Pattern | Matches |
|---------|---------|
| `users:*:tenant` | Any action on users within tenant |
| `data:read:*` | Read data at any scope |
| `*:*:platform` | Full platform access (SuperAdmin) |

Wildcard matching is evaluated in the backend permission checker after exact matching.
