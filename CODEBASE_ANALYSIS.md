# App-Buildify Codebase: Comprehensive Menu & RBAC Analysis

## Executive Summary

App-Buildify is a multi-tenant NoCode/LowCode platform featuring:
- **Sophisticated RBAC System**: Three-layer architecture (User → Roles → Permissions)
- **Hybrid Menu Architecture**: Static JSON config + dynamic module-driven menus
- **Permission Format**: Standardized `resource:action:scope` format
- **Tenant Isolation**: Every user belongs to one tenant, can access multiple companies
- **Permission Seeding**: Security permissions automatically seeded during initialization
- **Frontend-Backend Consistency**: Same permission codes used for both UI visibility and access control

---

## 1. DOCUMENTATION FILES

**Primary Location**: `/home/user/app-buildify/docs/`

### Main Documentation:
- **README.md** - Flex Component Library overview
- **ARCHITECTURE.md** - Component design patterns and architecture  
- **FUNCTIONAL_SPECIFICATION.md** - Platform feature specifications
- **TECHNICAL_SPECIFICATION.md** - Technical implementation details
- **MODULE_DEVELOPMENT_GUIDE.md** - Creating custom modules
- **CHANGELOG.md** - Version history
- **DATABASE_MIGRATIONS.md** - Schema changes

---

## 2. MENU STRUCTURE & IMPLEMENTATION

### 2.1 Static Core Menu

**File**: `/home/user/app-buildify/frontend/config/menu.json` (85 lines)

**Format**: Hierarchical JSON with role/permission filtering

**Main Sections**:
```
Dashboard
Administration
├── Companies, Branches, Departments
├── Users (admin only)
├── Groups
├── Roles & Permissions (admin only)
└── Auth Policies

System Management
├── System Settings (General, Integration, Security, Notifications)
├── Module Management (Installed, Marketplace, Updates, Builder)
└── Monitoring & Audit (Trail, Logs, API Activity, Analytics)

Reports & Analytics
Developer Tools
Help & Support
```

### 2.2 Menu Loading Process

**File**: `/home/user/app-buildify/frontend/assets/js/app.js` (lines 228-273)

**Steps**:
1. Fetch `/config/menu.json` (core menu)
2. Load module menus via `moduleRegistry.getAccessibleMenuItems()`
3. Merge core + module menu items
4. Filter via `filterMenuByRole()` from rbac.js
5. Render filtered items in sidebar

### 2.3 Menu Item Properties

```javascript
{
  "title": "Display Label",
  "route": "hash-route",              // e.g., "dashboard"
  "icon": "ph-duotone ph-gauge",     // Phosphor icon
  "roles": ["admin"],                 // Optional: required roles
  "permission": "resource:action:scope", // Optional: required permission
  "submenu": [                        // Optional: child items
    { ... }
  ]
}
```

### 2.4 Module Menu Integration

**Modules contribute menus via manifest.json**:
- Routes define menu labels, icons, and permissions
- Module loader integrates them with core menu
- Same filtering applied to module menu items

**Example (Financial Module)**:
- Routes: /financial/dashboard, /financial/accounts, /financial/invoices
- Each route has `permission: "financial:accounts:read:company"`
- Menus only appear if user has the permission

---

## 3. RBAC SYSTEM ARCHITECTURE

### 3.1 Database Models

**Core Models**:
- **Role**: Job function/position with permissions
  - System roles (tenant_id=NULL): superuser, admin
  - Tenant roles (tenant_id=UUID): custom roles
  
- **Permission**: Atomic access right
  - Format: `resource:action:scope`
  - Examples: "users:create:tenant", "financial:invoices:read:company"
  
- **Group**: Team/collection of users
  - Tenant-scoped or company-scoped
  - Users → Groups → Roles → Permissions
  
- **Junction Tables**: 
  - RolePermission, UserRole, UserGroup, GroupRole

**File Locations**:
- Role: `/backend/app/models/role.py`
- Permission: `/backend/app/models/permission.py`
- Group: `/backend/app/models/group.py`
- Junctions: `/backend/app/models/rbac_junctions.py`

### 3.2 Permission Format Standard

**Format**: `resource:action:scope`

**Components**:
- **Resource**: What (users, invoices, reports, security_policy)
- **Action**: How (read, create, update, delete, export, manage)
- **Scope**: Where (all, tenant, company, branch, department, own)

**Examples**:
```
financial:accounts:read:company
users:create:tenant
security_policy:manage:all
audit:export:tenant
modules:manage:tenant
```

### 3.3 Backend RBAC API

**Router**: `/backend/app/routers/rbac.py` (1058 lines)

**Endpoints**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/rbac/permissions` | GET | List all permissions |
| `/rbac/permissions/{id}` | GET | Get permission with role mappings |
| `/rbac/permission-categories` | GET | Get categories with counts |
| `/rbac/roles` | GET | List roles (tenant-filtered) |
| `/rbac/roles/{id}` | GET | Get role with permissions and assignments |
| `/rbac/roles/{id}/permissions` | POST | Assign permissions to role |
| `/rbac/roles/{id}/permissions/{pid}` | DELETE | Remove permission from role |
| `/rbac/groups` | GET | List groups |
| `/rbac/groups/{id}` | GET | Get group with members and effective permissions |
| `/rbac/groups/{id}/members` | POST | Add users to group |
| `/rbac/groups/{id}/members/{uid}` | DELETE | Remove user from group |
| `/rbac/groups/{id}/roles` | POST | Assign roles to group |
| `/rbac/groups/{id}/roles/{rid}` | DELETE | Remove role from group |
| `/rbac/users/{id}/roles` | GET | Get user's all roles (direct + via groups) |
| `/rbac/users/{id}/permissions` | GET | Get user's effective permissions |
| `/rbac/users/{id}/roles` | POST | Assign roles to user |
| `/rbac/users/{id}/roles/{rid}` | DELETE | Remove role from user |
| `/rbac/organization-structure` | GET | Get full tenant org hierarchy |

### 3.4 Backend Permission Checking

**File**: `/backend/app/core/dependencies.py` (185 lines)

**Functions**:
```python
def has_permission(permission: str)
    # Returns dependency for route protection
    # Checks user permissions via roles + groups
    # Superusers automatically pass
    
def has_any_permission(permissions: List[str])
    # Checks if user has ANY of listed permissions
    
def has_role(role_code: str)
    # Checks if user has specific role
```

**Usage**:
```python
@router.get("/accounts")
async def list_accounts(
    current_user: User = Depends(has_permission("financial:accounts:read:company"))
):
    ...
```

### 3.5 Frontend RBAC Module

**File**: `/frontend/assets/js/rbac.js` (306 lines)

**Key Functions**:

```javascript
// Role/Permission checking
hasRole(role)                      // Check if user has role
hasAnyRole(roles)                  // Check if user has any role
hasAllRoles(roles)                 // Check if user has all roles
can(permission)                    // Check if user has permission
hasPermission(permission)          // Alias for can()

// Field-level RBAC
canViewField(fieldMeta)            // Check view permission
canEditField(fieldMeta)            // Check edit permission

// DOM manipulation
showIfHasRole(element, roles)      // Show/hide element
enableIfHasRole(element, roles)    // Enable/disable element
applyRBACToElements(container)     // Apply RBAC to data-attributes

// Menu filtering
filterMenuByRole(menuItems)        // Recursively filter menu items
```

**Data Attribute Usage**:
```html
<button data-rbac-role="admin">Admin Only</button>
<button data-rbac-permission="users:create:tenant">Create User</button>
```

---

## 4. AUTHENTICATION & AUTHORIZATION

### 4.1 Auth Flow

**File**: `/backend/app/routers/auth.py` (600+ lines)

1. **Login** (`POST /auth/login`):
   - Validate credentials
   - Check account lockout
   - Record login attempt
   - Generate JWT tokens with tenant_id
   - Create session

2. **Token Structure**:
   - **Access Token**: HS256, short-lived (configurable minutes)
   - **Refresh Token**: HS256, long-lived (configurable days)
   - Both include JTI for revocation tracking

3. **User Profile** (`GET /auth/me`):
   - Returns UserResponse with all user data
   - Includes `roles` field populated with permission codes
   - Frontend caches in localStorage

### 4.2 User Model

**File**: `/backend/app/models/user.py`

**Key Fields**:
```python
- id, email, hashed_password
- full_name, display_name (max 50 chars)
- tenant_id (required, single tenant)
- default_company_id, branch_id, department_id (optional)
- is_active, is_superuser, is_verified
- failed_login_attempts, locked_until (security)
- last_login, password_expires_at
```

**Methods**:
- `get_permissions()` - Calculate all effective permissions
- `has_company_access(company_id, level)` - Check company access
- `get_accessible_companies()` - List all accessible companies

---

## 5. DYNAMIC MODULE SYSTEM

### 5.1 Module Manifest

**Example**: `/frontend/modules/financial/manifest.json`

```json
{
  "name": "financial",
  "display_name": "Financial Management",
  "version": "1.0.0",
  "entry_point": "module.js",
  
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
  ],
  
  "navigation": {
    "primary_menu": true,
    "dashboard_widgets": [...]
  }
}
```

### 5.2 Module Permissions

**File**: `/backend/modules/financial/permissions.py`

```python
class FinancialPermissions(str, Enum):
    ACCOUNTS_READ = "financial:accounts:read:company"
    ACCOUNTS_CREATE = "financial:accounts:create:company"
    INVOICES_READ = "financial:invoices:read:company"
    INVOICES_SEND = "financial:invoices:send:company"
    # ... etc
```

### 5.3 Module Menu Integration

**Frontend Flow**:
1. Load core menu from `/config/menu.json`
2. Get module menus: `moduleRegistry.getAccessibleMenuItems()`
3. Each module's routes are converted to menu items
4. Permission checked: `hasPermission(route.permission)`
5. Merge and filter all items
6. Render combined menu

---

## 6. TENANT ISOLATION & MULTI-TENANCY

### 6.1 Tenant Scoping

**Users**:
- Belong to exactly ONE tenant
- Can access multiple companies within that tenant
- Cannot access other tenants' data

**Roles**:
- System Roles: tenant_id=NULL (superuser, admin, user)
- Tenant Roles: tenant_id=UUID (custom tenant roles)

**Groups**:
- Tenant-wide: company_id=NULL
- Company-specific: company_id=UUID

**Permissions**:
- Format includes scope (tenant, company, branch, etc.)
- Backend enforces tenant isolation
- Frontend checks in RBAC module

### 6.2 Permission Scopes

```
all              - System-wide (superuser only)
tenant           - Entire tenant
company          - Specific company
branch           - Specific branch
department       - Specific department
own              - User's own resources
```

---

## 7. EXISTING PERMISSIONS & SEED DATA

### 7.1 Security Permissions

**File**: `/backend/app/scripts/seed_security_permissions.py`

- **Security Policy**: read, write, delete
- **Account Lockout**: view_locked_accounts, unlock_account
- **Session Management**: view_sessions, revoke_session
- **Login Audit**: view_login_attempts
- **Notifications**: read, write

### 7.2 Financial Module Permissions

- **Accounts**: read, create, update, delete
- **Transactions**: read, create, update, delete, post
- **Invoices**: read, create, update, delete, send
- **Payments**: read, create, update, delete
- **Reports**: read, export

### 7.3 Expected Core Permissions

Based on menu structure:
```
users:manage:tenant                 - User management
groups:manage:tenant                - Group management
roles:manage:tenant                 - Role/permission management
companies:manage:tenant             - Company management
branches:manage:tenant              - Branch management
departments:manage:tenant           - Department management
modules:manage:tenant               - Module management
audit:read:tenant                   - Audit trail access
settings:manage:tenant              - System settings
auth_policies:manage:tenant         - Auth policies
```

---

## 8. MENU MANAGEMENT SUMMARY

### 8.1 Current Approach

| Aspect | Implementation | Location |
|--------|-----------------|----------|
| **Core Menu** | Static JSON | `/config/menu.json` |
| **Core Filtering** | Client-side (rbac.js) | `filterMenuByRole()` |
| **Module Menus** | Dynamic from manifest | Each module manifest.json |
| **Module Filtering** | Client-side permission check | `module-registry.js` |
| **Sidebar Rendering** | JavaScript DOM | `app.js` |
| **Sidebar State** | localStorage | `loadSidebarState()` |

### 8.2 Database vs Configuration

- **Menus**: Configuration-driven (no database)
- **Roles**: Database-driven (CRUD via API)
- **Permissions**: Database-driven (seeded + managed via API)
- **Assignments**: Database-driven (role-permission, user-role, group-role)

### 8.3 User → Menu Visibility Flow

```
1. User logs in
2. Backend returns permissions in UserResponse
3. Frontend stores in appState.user
4. Menu loading begins:
   - Load core menu JSON
   - Get module menus via moduleRegistry
   - filterMenuByRole() checks user roles/permissions
   - Only accessible items rendered
5. At runtime:
   - dynamicUI uses hasPermission() for visibility
   - Backend enforces permissions on API calls
```

---

## 9. KEY FILES REFERENCE

### Frontend Files

| File | Purpose | Lines |
|------|---------|-------|
| `/frontend/config/menu.json` | Core menu configuration | 85 |
| `/frontend/assets/js/app.js` | App initialization, menu loading | 900+ |
| `/frontend/assets/js/rbac.js` | RBAC utilities and menu filtering | 306 |
| `/frontend/assets/js/core/module-system/module-registry.js` | Module menu management | 350+ |
| `/frontend/modules/financial/manifest.json` | Module configuration | 80+ |

### Backend Files

| File | Purpose | Lines |
|------|---------|-------|
| `/backend/app/routers/rbac.py` | RBAC endpoints | 1058 |
| `/backend/app/routers/auth.py` | Auth endpoints | 600+ |
| `/backend/app/routers/modules.py` | Module management endpoints | 300+ |
| `/backend/app/models/role.py` | Role model | 73 |
| `/backend/app/models/permission.py` | Permission model | 57 |
| `/backend/app/models/group.py` | Group model | 75 |
| `/backend/app/models/rbac_junctions.py` | Junction models | 133 |
| `/backend/app/models/user.py` | User model | 200+ |
| `/backend/app/core/dependencies.py` | Permission checking | 185 |
| `/backend/app/scripts/seed_security_permissions.py` | Permission initialization | 200+ |

---

## 10. ARCHITECTURE DIAGRAMS

### Permission Resolution Flow
```
User
  ├─ Direct Roles
  │   └─ Permissions
  └─ Group Memberships
      └─ Group Roles
          └─ Permissions

Result: Set of effective permission codes
Used for: Both UI visibility and API access control
```

### Menu Visibility Decision Tree
```
Menu Item
  ├─ No roles/permission specified?
  │   └─ Show to all authenticated users
  ├─ Has 'roles' property?
  │   └─ User has ANY of the roles?
  │       ├─ YES → Show
  │       └─ NO → Hide
  └─ Has 'permission' property?
      └─ User has permission?
          ├─ YES → Show
          └─ NO → Hide
```

### Module Integration
```
Core Menu (JSON)
     +
Module Menus (manifests)
     ↓
Merge & Combine
     ↓
Filter by User Permissions
     ↓
Render Sidebar
```

---

## 11. PERMISSION BEST PRACTICES

### Resource Naming
- Use lowercase with underscores
- Singular for CRUD operations (user, invoice, account)
- Clear and descriptive (financial_account, security_policy)

### Action Naming
- **read**: View/list operations
- **create**: New resource creation
- **update**: Modify existing resource
- **delete**: Remove resource
- **export**: Download/export data
- **manage**: Full control
- Custom actions: send, post, approve, reject

### Scope Selection
- **all**: System-wide, rarely used outside superuser
- **tenant**: Most common for tenant admins
- **company**: Multi-company scenarios
- **branch**: Org hierarchies
- **department**: Smaller scopes
- **own**: User's personal resources

---

## 12. IMPLEMENTATION CHECKLIST

For new features requiring menu + permissions:

- [ ] Define permission codes (resource:action:scope)
- [ ] Add to module/core permissions enum
- [ ] Register in database (seed script or API)
- [ ] Create/update role with permissions
- [ ] Add menu item to config/manifest with permission
- [ ] Implement frontend visibility (rbac.js checks)
- [ ] Implement backend checks (dependencies.py)
- [ ] Test with different user roles
- [ ] Document in menu structure
- [ ] Update permission matrix

---

## 13. SUPPORT & RESOURCES

### For Menu Documentation:
- See: `/docs/README.md` - Component overview
- See: `/docs/ARCHITECTURE.md` - Design patterns

### For RBAC Documentation:
- See: `/docs/FUNCTIONAL_SPECIFICATION.md` - Features
- See: `/docs/TECHNICAL_SPECIFICATION.md` - Technical details

### For Module Development:
- See: `/docs/MODULE_DEVELOPMENT_GUIDE.md`

### For Permission Management:
- API: `GET /rbac/permissions` - List all permissions
- API: `GET /rbac/organization-structure` - Full org structure
- Seed: `/backend/app/scripts/seed_security_permissions.py`

---

**Report Generated**: 2024
**Analysis Scope**: Full codebase review including frontend + backend
**Key Finding**: Well-structured RBAC system with hybrid menu architecture
