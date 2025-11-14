# Backend-Driven RBAC Menu System - Implementation Guide

## Overview

This document describes the implementation of the backend-driven RBAC menu system for App-Buildify. This new system moves menu management from static JSON files to a database-driven approach with server-side RBAC filtering.

## What Was Implemented

### 1. Database Layer

#### MenuItem Model
**File**: `/backend/app/models/menu_item.py`

A new `MenuItem` model with the following features:
- Hierarchical structure (parent-child relationships)
- Multi-tenancy support (system menus + tenant-specific menus)
- RBAC integration (permission + required_roles fields)
- Module integration support
- Extensible metadata (JSONB field for custom properties)

**Key Fields**:
- `code`: Unique identifier
- `title`, `icon`, `route`: Display properties
- `permission`: Required permission code (e.g., "users:read:tenant")
- `required_roles`: Array of required roles
- `parent_id`: For hierarchical menu structure
- `order`: Display order
- `tenant_id`: NULL for system menus, UUID for tenant-specific
- `module_code`: For module-provided menus
- `is_active`, `is_visible`: Status flags

#### Database Migrations
**Files**:
- `/backend/app/alembic/versions/postgresql/pg_create_menu_items.py`
- `/backend/app/alembic/versions/mysql/mysql_create_menu_items.py`

Migrations for both PostgreSQL and MySQL to create the `menu_items` table with:
- All necessary columns
- Foreign key constraints (tenant_id, parent_id)
- Performance indexes (composite indexes for common queries)

### 2. Service Layer

#### MenuService
**File**: `/backend/app/services/menu_service.py`

Business logic for menu operations:

**Key Methods**:
- `get_user_menu()`: Get RBAC-filtered menu for a user
- `_get_accessible_menu_items()`: Filter menus by permissions/roles
- `_is_menu_accessible()`: Check if user can access a menu item
- `_get_module_menu_items()`: Integrate module menus
- `_build_menu_tree()`: Build hierarchical structure
- `get_all_menu_items()`: Admin: Get all menus (unfiltered)
- `create_menu_item()`: Create new menu item
- `update_menu_item()`: Update menu item
- `delete_menu_item()`: Soft delete menu item
- `reorder_menu_items()`: Reorder menus

**RBAC Filtering Logic**:
1. Superusers see everything
2. No restrictions = visible to all authenticated users
3. If `required_roles` specified, user must have at least one
4. If `permission` specified, user must have that permission

### 3. API Layer

#### Menu Router
**File**: `/backend/app/routers/menu.py`

RESTful API endpoints:

| Endpoint | Method | Permission | Description |
|----------|--------|------------|-------------|
| `/api/v1/menu` | GET | Authenticated | Get user's accessible menu (RBAC-filtered) |
| `/api/v1/menu/admin` | GET | `menu:manage:tenant` | Get all menu items for admin |
| `/api/v1/menu/{id}` | GET | `menu:read:tenant` | Get specific menu item |
| `/api/v1/menu` | POST | `menu:create:tenant` | Create menu item |
| `/api/v1/menu/{id}` | PUT | `menu:update:tenant` | Update menu item |
| `/api/v1/menu/{id}` | DELETE | `menu:delete:tenant` | Delete menu item (soft) |
| `/api/v1/menu/reorder` | POST | `menu:update:tenant` | Reorder menu items |

**Features**:
- Automatic RBAC enforcement via dependencies
- Tenant isolation
- Audit logging for all operations
- Error handling with appropriate HTTP status codes

#### Schemas
**File**: `/backend/app/schemas/menu.py`

Pydantic schemas for validation:
- `MenuItemBase`: Base menu properties
- `MenuItemCreate`: For creating menus
- `MenuItemUpdate`: For updating menus
- `MenuItemResponse`: Full menu response
- `MenuItemTree`: Hierarchical menu structure
- `MenuReorderRequest`: For reordering operations

### 4. Frontend Layer

#### Updated Menu Loading
**File**: `/frontend/assets/js/app.js`

Updated `loadMenu()` function with:

**Feature Flag**: `window.APP_CONFIG.useDynamicMenu`
- `true` (default): Use backend-driven menu system
- `false`: Use legacy static JSON menu

**New Functions**:
- `loadMenuFromBackend()`: Fetch menu from API
- `loadMenuFromStatic()`: Legacy static JSON loading
- `convertBackendMenuFormat()`: Convert API response to frontend format

**Fallback Strategy**: If backend fails, automatically falls back to static menu

### 5. Data Migration

#### Seeder Script
**File**: `/backend/app/seeds/seed_menu_items.py`

Script to import current `menu.json` into database:

**Features**:
- Reads `/frontend/config/menu.json`
- Recursively creates menu items with parent-child relationships
- Handles existing items (with confirmation prompt)
- Creates menu management permissions
- Maintains order from JSON file

**Usage**:
```bash
cd /home/user/app-buildify/backend
python -m app.scripts.seed_menu_items
```

**What it does**:
1. Checks if menu items already exist
2. Prompts for confirmation if re-seeding
3. Creates all menu items from JSON
4. Creates menu management permissions
5. Maintains hierarchical structure

### 6. Permissions

#### New Permissions Created

| Permission Code | Name | Description |
|-----------------|------|-------------|
| `menu:read:tenant` | View Menu Items | View menu items for tenant |
| `menu:create:tenant` | Create Menu Items | Create new menu items |
| `menu:update:tenant` | Update Menu Items | Update menu items |
| `menu:delete:tenant` | Delete Menu Items | Delete menu items |
| `menu:manage:tenant` | Manage Menus | Full menu management access |

These permissions are automatically created by the seeder script.

---

## How to Deploy

### Step 1: Run Database Migrations

```bash
cd /home/user/app-buildify/backend

# For PostgreSQL
alembic upgrade head -x db=postgresql

# For MySQL
alembic upgrade head -x db=mysql
```

This creates the `menu_items` table.

### Step 2: Run Seeder Script

#### Local Development

```bash
cd /home/user/app-buildify/backend
python -m app.seeds.seed_menu_items
```

#### Docker Environment

The seeder script needs access to `menu.json` from the frontend. Ensure your `docker-compose.dev.yml` includes the frontend volume mount:

```yaml
backend:
  volumes:
    - ../backend:/app
    - ../frontend:/frontend:ro  # This line is required for seeder
```

Then run the seeder inside the container:

```bash
# Enter backend container
docker exec -it app_buildify_backend bash

# Run seeder
python -m app.seeds.seed_menu_items
```

The seeder will automatically search for `menu.json` in these locations:
1. `/frontend/config/menu.json` (Docker with frontend volume mounted)
2. `/app/frontend/config/menu.json` (Docker with frontend in app directory)
3. `../frontend/config/menu.json` (Local development)
4. `frontend/config/menu.json` (Working directory)
5. `backend/app/config/menu.json` (Backend fallback)

**Custom Path Option**:
If your setup is different, you can specify a custom path:

```bash
python -m app.seeds.seed_menu_items --path /custom/path/to/menu.json
```

**Options**:
- Default: Skip existing menu items (safe for re-runs)
- `--clear` or `-c`: Delete existing menu items before seeding (fresh start)
- `--path` or `-p`: Specify custom path to menu.json

This will:
1. Create menu management permissions
2. Import all menu items from menu.json
3. Display progress and summary

**Expected Output**:
```
🚀 Starting Menu System Seed...
================================================================================

================================================================================
MENU MANAGEMENT PERMISSIONS SETUP
================================================================================

📋 Step 1: Registering Menu Management permissions...
  ✓ Created permission: menu:read:tenant
  ✓ Created permission: menu:create:tenant
  ✓ Created permission: menu:update:tenant
  ✓ Created permission: menu:delete:tenant
  ✓ Created permission: menu:manage:tenant

✓ Created 5 new permissions
✓ Found 0 existing permissions

================================================================================
MENU ITEMS SEED
================================================================================

📋 Step 1: Loading menu.json...
  ✓ Loaded 6 top-level menu items from menu.json

📋 Step 2: Creating menu items...
  ✓ Created menu item: dashboard (ID: ...)
  ✓ Created menu item: administration (ID: ...)
  ...

✓ Successfully seeded 40 menu items

================================================================================

================================================================================
✅ MENU SYSTEM SEED COMPLETE!
================================================================================

Summary:
  • Permissions created: 5
  • Menu items created: 40

Next steps:
  1. Assign 'menu:manage:tenant' permission to admin roles
  2. Restart backend application
  3. Test menu API: GET /api/v1/menu
================================================================================
```

### Step 3: Assign Permissions to Roles

Give admin users the menu management permissions:

```bash
# Via API or admin UI
POST /api/v1/rbac/roles/{admin_role_id}/permissions
{
  "permission_codes": [
    "menu:read:tenant",
    "menu:manage:tenant"
  ]
}
```

Or use the RBAC admin interface in the frontend.

### Step 4: Enable Backend Menu System

The backend menu system is enabled by default. To disable it (rollback to static):

```html
<!-- In your HTML template -->
<script>
  window.APP_CONFIG = {
    useDynamicMenu: false  // Set to false to use static menu.json
  };
</script>
```

Or keep default (true) for backend-driven menus.

### Step 5: Restart Backend

```bash
# Restart your FastAPI application
# The exact command depends on your deployment
```

The new `/api/v1/menu` endpoint is now available!

---

## How It Works

### Request Flow

```
User Logs In
     ↓
Frontend: loadMenu() called
     ↓
API Request: GET /api/v1/menu?include_modules=true
     ↓
Backend: MenuService.get_user_menu()
     ↓
Get user's permissions and roles
     ↓
Query database for menu_items
     ↓
Filter by RBAC (permission + required_roles)
     ↓
Include module menus if enabled
     ↓
Build hierarchical tree structure
     ↓
Return JSON to frontend
     ↓
Frontend: Convert format and render
```

### Menu Visibility Rules

For each menu item, the backend checks:

1. **Is user superuser?** → Show all items
2. **No permission/role requirements?** → Show to all authenticated users
3. **Has `required_roles`?** → User must have at least one of the roles
4. **Has `permission`?** → User must have that exact permission

All checks must pass for the item to be included.

### Module Menu Integration

The backend automatically:
1. Queries `TenantModule` for enabled modules
2. Reads module manifests for routes with menu configuration
3. Checks permissions for each route
4. Converts to `MenuItem` objects
5. Merges with core menu items

---

## API Examples

### Get User's Menu

```bash
GET /api/v1/menu?include_modules=true
Authorization: Bearer {token}

Response:
[
  {
    "id": "uuid",
    "code": "dashboard",
    "title": "Dashboard",
    "icon": "ph-duotone ph-gauge",
    "route": "dashboard",
    "order": 0,
    "target": "_self",
    "children": []
  },
  {
    "id": "uuid",
    "code": "administration",
    "title": "Administration",
    "icon": "ph-duotone ph-buildings",
    "route": null,
    "order": 10,
    "target": "_self",
    "children": [
      {
        "code": "companies",
        "title": "Companies",
        "icon": "ph-duotone ph-building",
        "route": "companies",
        ...
      }
    ]
  }
]
```

### Create Menu Item (Admin)

```bash
POST /api/v1/menu
Authorization: Bearer {token}
Content-Type: application/json

{
  "code": "custom_reports",
  "title": "Custom Reports",
  "icon": "ph-duotone ph-chart-bar",
  "route": "reports/custom",
  "permission": "reports:custom:read:tenant",
  "parent_id": null,
  "order": 100,
  "is_active": true,
  "is_visible": true
}

Response:
{
  "id": "new-uuid",
  "code": "custom_reports",
  "title": "Custom Reports",
  ...
}
```

### Update Menu Item

```bash
PUT /api/v1/menu/{menu_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Updated Title",
  "icon": "ph-duotone ph-new-icon",
  "order": 50
}
```

### Delete Menu Item

```bash
DELETE /api/v1/menu/{menu_id}
Authorization: Bearer {token}

Response:
{
  "success": true,
  "message": "Menu item deleted successfully"
}
```

### Reorder Menu Items

```bash
POST /api/v1/menu/reorder
Authorization: Bearer {token}
Content-Type: application/json

{
  "items": [
    {"id": "uuid1", "order": 0},
    {"id": "uuid2", "order": 10},
    {"id": "uuid3", "order": 20}
  ]
}
```

---

## Benefits

### Security
- ✅ Only authorized menu items sent to client
- ✅ Server-side RBAC enforcement (can't be bypassed)
- ✅ Consistent permission checking (backend + frontend)
- ✅ Audit trail for all menu operations

### Performance
- ✅ Smaller payloads (only accessible items)
- ✅ Server-side caching opportunities
- ✅ Reduced client-side processing

### Flexibility
- ✅ Dynamic menu management without deployments
- ✅ Tenant-specific menu customization
- ✅ Runtime menu modifications
- ✅ Easy to add new menu items programmatically

### Maintenance
- ✅ Centralized menu configuration
- ✅ Single source of truth (database)
- ✅ Version-controlled via migrations
- ✅ Easy to backup and restore

---

## Backward Compatibility

### Feature Flag

The implementation includes a feature flag to maintain backward compatibility:

```javascript
// Enable backend menu (default)
window.APP_CONFIG = { useDynamicMenu: true };

// Disable backend menu (use static JSON)
window.APP_CONFIG = { useDynamicMenu: false };
```

### Fallback Mechanism

If backend API fails, the frontend automatically falls back to static `menu.json`:

```javascript
async function loadMenuFromBackend() {
  try {
    // Try backend API
    return await api.get('/menu');
  } catch (error) {
    // Fallback to static menu
    console.warn('Falling back to static menu');
    return await loadMenuFromStatic();
  }
}
```

### Static Menu Still Works

The original `/config/menu.json` is preserved and still works:
- Can be used as fallback
- Seeder imports from it
- Legacy mode uses it directly

---

## Testing

### Manual Testing Steps

1. **Superuser Test**:
   - Login as superuser
   - Verify all menu items visible
   - Check `/api/v1/menu` returns full menu

2. **Admin Test**:
   - Login as admin (non-superuser)
   - Verify admin-only items visible
   - Check role-restricted items appear

3. **Regular User Test**:
   - Login as regular user (no admin role)
   - Verify only accessible items appear
   - Check admin items are hidden

4. **Permission Test**:
   - Create user with specific permissions
   - Verify only permitted items show
   - Remove permission, verify item disappears

5. **Module Menu Test**:
   - Enable a module (e.g., Financial)
   - Verify module menus appear
   - Disable module, verify menus disappear

6. **Fallback Test**:
   - Stop backend or break `/menu` endpoint
   - Verify frontend falls back to static menu
   - Check error handling works

### API Testing

```bash
# Test user menu endpoint
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/v1/menu

# Test admin endpoint (requires permission)
curl -H "Authorization: Bearer {admin_token}" \
  http://localhost:8000/api/v1/menu/admin

# Test create menu item
curl -X POST \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{"code":"test","title":"Test Menu","icon":"ph-test"}' \
  http://localhost:8000/api/v1/menu
```

---

## Troubleshooting

### Menu items not showing

**Check**:
1. Run seeder script: `python -m app.seeds.seed_menu_items`
2. Verify permissions assigned to user's roles
3. Check `/api/v1/menu` response in browser DevTools
4. Verify `useDynamicMenu` is not set to false

### Permission denied errors

**Check**:
1. User has required permissions (via roles)
2. Menu item `permission` field matches actual permission codes
3. User's tenant_id matches (for tenant-scoped permissions)

### Module menus not appearing

**Check**:
1. Module is enabled for tenant: `GET /api/v1/modules/enabled`
2. User has module permissions
3. Module manifest has routes with `menu` configuration
4. `include_modules=true` in API call

### Backend fallback to static menu

**Causes**:
1. Backend API not running
2. Migration not run (table doesn't exist)
3. Seeder not run (no menu items in DB)
4. Authentication token invalid

**Solution**: Check backend logs and verify deployment steps completed

### Docker: Seeder cannot find menu.json

**Error**: `❌ ERROR: menu.json not found!`

**Causes**:
1. Frontend volume not mounted in backend container
2. Frontend is in a separate container without shared volume

**Solutions**:

**Option 1 - Mount Frontend Volume (Recommended)**:
Update `docker-compose.dev.yml` to include frontend volume in backend service:

```yaml
backend:
  volumes:
    - ../backend:/app
    - ../frontend:/frontend:ro  # Add this line
```

Then restart containers:
```bash
cd infra
docker-compose down
docker-compose up -d
```

**Option 2 - Copy menu.json to Backend**:
```bash
# Copy menu.json to backend config directory
mkdir -p backend/app/config
cp frontend/config/menu.json backend/app/config/

# In container, use custom path
docker exec -it app_buildify_backend bash
python -m app.seeds.seed_menu_items --path /app/app/config/menu.json
```

**Option 3 - Specify Custom Path**:
If you've mounted frontend at a different location, specify the path:
```bash
docker exec -it app_buildify_backend bash
python -m app.seeds.seed_menu_items --path /your/custom/path/menu.json
```

---

## Future Enhancements

### Phase 2 Features (Not Yet Implemented)

- [ ] **Menu Analytics**: Track which menu items are most used
- [ ] **User Customization**: Users can hide/reorder their own menus
- [ ] **Favorites**: Quick access to frequently used items
- [ ] **Menu Search**: Search menu items by keyword
- [ ] **Contextual Menus**: Different menus based on selected company/branch
- [ ] **Admin UI**: Full menu management interface in frontend
- [ ] **Drag-and-Drop**: Visual menu reordering
- [ ] **Multi-language**: Localized menu titles
- [ ] **Menu Caching**: Client-side cache with TTL
- [ ] **Breadcrumbs**: Auto-generate from menu hierarchy

### Potential Improvements

- GraphQL API for more flexible menu queries
- Real-time menu updates via WebSockets
- Menu templates for common configurations
- Import/export menu configurations
- Menu versioning and rollback

---

## Files Changed/Created

### Backend

**Created**:
- `/backend/app/models/menu_item.py` - MenuItem model
- `/backend/app/services/menu_service.py` - Menu business logic
- `/backend/app/schemas/menu.py` - Pydantic schemas
- `/backend/app/routers/menu.py` - API endpoints
- `/backend/app/alembic/versions/postgresql/pg_create_menu_items.py` - PostgreSQL migration
- `/backend/app/alembic/versions/mysql/mysql_create_menu_items.py` - MySQL migration
- `/backend/app/seeds/seed_menu_items.py` - Seeder script

**Modified**:
- `/backend/app/models/__init__.py` - Added MenuItem import
- `/backend/app/main.py` - Registered menu router

### Frontend

**Modified**:
- `/frontend/assets/js/app.js` - Updated loadMenu() with backend support

### Documentation

**Created**:
- `/MENU_RBAC_RECOMMENDATIONS.md` - Detailed recommendations
- `/CODEBASE_ANALYSIS.md` - Current state analysis
- `/MENU_RBAC_QUICK_REFERENCE.md` - Quick reference guide
- `/BACKEND_MENU_IMPLEMENTATION.md` - This file

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review API documentation: `/api/docs`
3. Check backend logs for errors
4. Verify permissions via `/api/v1/rbac/users/{user_id}/permissions`

---

**Implementation Date**: 2025-11-13
**Version**: 1.0
**Author**: Backend-Driven RBAC Menu System Implementation
