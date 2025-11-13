# Menu & RBAC Quick Reference Guide

## 1. PERMISSION FORMAT

**Template**: `resource:action:scope`

**Examples**:
```
financial:accounts:read:company
users:create:tenant
audit:export:tenant
security_policy:manage:all
```

---

## 2. MENU ITEM STRUCTURE

```json
{
  "title": "Display Label",
  "route": "dashboard",
  "icon": "ph-duotone ph-gauge",
  "roles": ["admin"],                           // Optional
  "permission": "users:manage:tenant",          // Optional
  "submenu": [                                  // Optional
    { "title": "Sub Item", "route": "..." }
  ]
}
```

---

## 3. RBAC HIERARCHY

```
User
├─ Superuser? → All permissions
└─ Regular User
   ├─ Direct Roles → Permissions
   └─ Groups
      └─ Group Roles → Permissions
```

---

## 4. KEY FILES AT A GLANCE

### Frontend
- **Menu Config**: `/frontend/config/menu.json`
- **App Logic**: `/frontend/assets/js/app.js` (lines 228-273 for loading)
- **RBAC Logic**: `/frontend/assets/js/rbac.js`
- **Module Menus**: `/frontend/modules/{name}/manifest.json`

### Backend
- **RBAC API**: `/backend/app/routers/rbac.py`
- **Auth API**: `/backend/app/routers/auth.py`
- **Models**: `/backend/app/models/{role,permission,group,user}.py`
- **Permissions**: `/backend/app/core/dependencies.py` (has_permission, etc)

---

## 5. COMMON RBAC OPERATIONS

### Check User Role (Frontend)
```javascript
import { hasRole } from './rbac.js';

if (hasRole('admin')) {
  // Show admin UI
}
```

### Check User Permission (Frontend)
```javascript
import { hasPermission } from './rbac.js';

if (hasPermission('users:create:tenant')) {
  // Show create button
}
```

### Filter Menu Items (Frontend)
```javascript
import { filterMenuByRole } from './rbac.js';

const filteredMenu = filterMenuByRole(menuItems);
```

### Protect Route (Backend)
```python
from app.core.dependencies import has_permission

@router.get("/users")
async def list_users(
    current_user: User = Depends(has_permission("users:read:tenant"))
):
    # Only users with permission can access
```

---

## 6. MENU LOADING SEQUENCE

```
1. Page loads → initApp() in app.js
2. loadMenu() function executes:
   a. Fetch /config/menu.json
   b. Get module menu items via moduleRegistry
   c. Merge core + module menus
   d. filterMenuByRole() to remove restricted items
   e. createMenuItem() to render each item
   f. Attach click handlers
3. Sidebar displays filtered menu
```

---

## 7. PERMISSION SCOPES EXPLAINED

| Scope | Usage | Example |
|-------|-------|---------|
| `all` | System-wide | `security_policy:manage:all` |
| `tenant` | Tenant-level | `users:manage:tenant` |
| `company` | Company-level | `financial:accounts:read:company` |
| `branch` | Branch-level | `reports:read:branch` |
| `department` | Department-level | `documents:edit:department` |
| `own` | User's own | `profile:update:own` |

---

## 8. ROLE TYPES

```python
System Roles (tenant_id = NULL):
  - superuser
  - admin
  - user

Tenant Roles (tenant_id = UUID):
  - finance_manager
  - department_lead
  - custom roles
```

---

## 9. RBAC API ENDPOINTS QUICK LOOKUP

### Get Data
```
GET /rbac/roles                      List all roles
GET /rbac/permissions                List all permissions
GET /rbac/users/{user_id}/roles      User's roles
GET /rbac/users/{user_id}/permissions User's permissions
GET /rbac/groups                     List groups
GET /rbac/organization-structure     Full org with users/roles
```

### Manage Roles
```
POST /rbac/roles/{role_id}/permissions         Add permissions
DELETE /rbac/roles/{role_id}/permissions/{pid} Remove permission
```

### Manage Users
```
POST /rbac/users/{user_id}/roles     Assign roles
DELETE /rbac/users/{user_id}/roles/{rid} Remove role
```

### Manage Groups
```
POST /rbac/groups/{group_id}/members      Add users
DELETE /rbac/groups/{group_id}/members/{uid} Remove user
POST /rbac/groups/{group_id}/roles        Assign roles
DELETE /rbac/groups/{group_id}/roles/{rid} Remove role
```

---

## 10. FRONTEND RBAC FUNCTIONS

```javascript
hasRole(role)                    // → boolean
hasAnyRole(roles)                // → boolean
hasAllRoles(roles)               // → boolean
can(permission)                  // → boolean
hasPermission(permission)        // → boolean (alias for can)

canViewField(fieldMeta)          // → boolean
canEditField(fieldMeta)          // → boolean

showIfHasRole(element, roles)    // Show/hide element
enableIfHasRole(element, roles)  // Enable/disable element
applyRBACToElements(container)   // Apply data-rbac attributes

filterMenuByRole(menuItems)      // → filtered array
getUserRoles()                   // → string[]
getUserTenantId()                // → string
belongsToTenant(tenantId)        // → boolean
isSuperuser()                    // → boolean
```

---

## 11. BACKEND PERMISSION CHECKING

```python
from app.core.dependencies import (
    has_permission,
    has_any_permission,
    has_role,
    get_current_user,
    require_superuser
)

# Single permission
@router.get("/accounts")
async def list_accounts(
    current_user: User = Depends(has_permission("financial:accounts:read:company"))
):

# Multiple permissions (any)
@router.post("/accounts")
async def create_account(
    current_user: User = Depends(has_any_permission([
        "financial:accounts:create:company",
        "financial:accounts:manage:company"
    ]))
):

# Role-based
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(has_role("admin"))
):

# Superuser only
@router.post("/security-policies")
async def create_policy(
    current_user: User = Depends(require_superuser)
):
```

---

## 12. USER RESPONSE STRUCTURE

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "display_name": "John",
  "is_active": true,
  "is_superuser": false,
  "tenant_id": "uuid",
  "default_company_id": "uuid",
  "branch_id": "uuid",
  "department_id": "uuid",
  "roles": [
    "financial:accounts:read:company",
    "financial:invoices:create:company",
    "users:read:tenant"
  ],
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-02T00:00:00",
  "last_login": "2024-01-02T10:00:00"
}
```

Note: `roles` field contains permission codes (not role names)

---

## 13. DATA ATTRIBUTES FOR RBAC

```html
<!-- Show/hide based on role -->
<button data-rbac-role="admin">Admin Only</button>
<button data-rbac-role="admin,finance_manager">Admin or Finance</button>

<!-- Show/hide based on permission -->
<button data-rbac-permission="users:create:tenant">Create User</button>
<button data-rbac-permission="audit:export:tenant">Export Audit</button>
```

Applied via: `applyRBACToElements(container)`

---

## 14. MODULE MANIFEST ROUTES

```json
{
  "routes": [
    {
      "path": "#/financial/accounts",
      "name": "Chart of Accounts",
      "component": "pages/accounts-page.js",
      "permission": "financial:accounts:read:company",
      "menu": {
        "label": "Accounts",
        "icon": "📊",
        "order": 11,
        "parent": "financial"
      }
    }
  ]
}
```

Each route with a `menu` object appears in the sidebar (if permission granted).

---

## 15. ADDING NEW PERMISSIONS

**Step-by-step**:

1. Define permission codes:
   ```python
   # In module or core
   MODULE_ACTION_READ_SCOPE = "module:action:scope"
   ```

2. Seed to database:
   ```python
   # In seed script or API
   db.add(Permission(
       code="module:action:scope",
       name="Permission Name",
       resource="module",
       action="action",
       scope="scope"
   ))
   ```

3. Assign to role:
   ```python
   # Via API
   POST /rbac/roles/{role_id}/permissions
   {
     "permission_ids": ["uuid1", "uuid2"]
   }
   ```

4. Update menu items (if needed):
   ```json
   {
     "title": "Feature",
     "route": "feature",
     "permission": "module:action:scope"
   }
   ```

5. Add frontend checks:
   ```javascript
   if (hasPermission("module:action:scope")) {
     // Show UI
   }
   ```

6. Add backend checks:
   ```python
   @router.get("/feature")
   async def get_feature(
       current_user: User = Depends(has_permission("module:action:scope"))
   ):
   ```

---

## 16. TENANT ISOLATION

**Key Rules**:
- User belongs to exactly ONE tenant
- Can access multiple companies within that tenant
- Cannot see other tenants' data
- Superusers can access any tenant

**Where Enforced**:
- Backend: `verify_tenant_access()` in dependencies.py
- Queries: `filter(Model.tenant_id == current_user.tenant_id)`
- Frontend: `belongsToTenant()` check
- JWT: tenant_id embedded in token

---

## 17. COMMON SCENARIOS

### Scenario: Admin-Only Feature
```json
{
  "title": "Users",
  "route": "users",
  "icon": "ph-duotone ph-users",
  "roles": ["admin"]
}
```

### Scenario: Permission-Based Feature
```json
{
  "title": "Financial",
  "route": "financial",
  "permission": "financial:accounts:read:company"
}
```

### Scenario: Complex Backend Route
```python
@router.post("/invoices/{id}/send")
async def send_invoice(
    id: str,
    current_user: User = Depends(
        has_any_permission([
            "financial:invoices:send:company",
            "financial:invoices:manage:company"
        ])
    )
):
    # Check tenant access
    invoice = db.query(Invoice).filter(
        Invoice.id == id,
        Invoice.tenant_id == current_user.tenant_id
    ).first()
    
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    
    # Send invoice...
```

---

## 18. DEBUGGING PERMISSION ISSUES

### Frontend Debug
```javascript
// In browser console
import { getCurrentUser } from './app.js';
const user = getCurrentUser();
console.log(user.roles);  // See permission codes
console.log(user.is_superuser);  // Check superuser status

import { hasPermission } from './rbac.js';
console.log(hasPermission("financial:accounts:read:company"));
```

### Backend Debug
```python
# In route
from sqlalchemy import inspect

user = get_current_user(...)
print(f"User roles: {[r.code for r in user.user_roles]}")
print(f"User permissions: {user.get_permissions()}")
print(f"Tenant ID: {user.tenant_id}")
```

---

## 19. PERMISSION NAMING CONVENTIONS

| Resource | Actions | Example |
|----------|---------|---------|
| users | read, create, update, delete, manage | users:create:tenant |
| invoices | read, create, update, delete, send, manage | invoices:send:company |
| audit | read, export | audit:read:tenant |
| settings | read, write, manage | settings:manage:tenant |
| roles | read, create, update, delete, manage | roles:manage:tenant |

---

## 20. QUICK TROUBLESHOOTING

| Issue | Cause | Solution |
|-------|-------|----------|
| Menu item not showing | No permission or wrong role | Check menu.json permission, check user permissions |
| 403 Forbidden on API | Missing permission | Check backend route has_permission dependency |
| User can't see any menu | Superuser=false but no roles | Assign role with permissions |
| Module menu not appearing | Permission denied | Check module manifest permission, verify user has it |
| Sidebar won't load | JSON parse error | Validate menu.json syntax |

---

**Last Updated**: 2024
**Version**: 1.0
