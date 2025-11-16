# Menu Management RBAC Guide

## Overview

This document explains how menu management permissions work for different user types in the NoCode Platform.

## User Types & Permissions

### 1. Superusers (Platform Administrators)

**Access Level**: Full automatic access to ALL permissions

**How it works**:
- Superusers have the `is_superuser=True` flag on their user account
- They **automatically bypass all permission checks** (see `backend/app/core/dependencies.py:120-122`)
- No explicit role or permission assignment needed
- They can manage menus across ALL tenants

**No action required** - Superusers automatically have menu management access!

### 2. Tenant Administrators

**Access Level**: Full menu management for their tenant

**How to grant access**:

Option A: Using the RBAC seed script (Recommended):
```bash
# Run the menu management RBAC seed for your tenant
python -m app.seeds.seed_menu_management_rbac [TENANT_CODE]

# Example:
python -m app.seeds.seed_menu_management_rbac FASHIONHUB
```

This creates:
- "Menu Administrator" role with all menu permissions
- "Menu Administrators" group
- Automatically assigns permissions to the role

Then add your admin users to the "Menu Administrators" group.

Option B: Manual permission assignment:
```bash
# List available roles
python assign_menu_permissions.py

# Assign to existing admin role
python assign_menu_permissions.py ADMIN FASHIONHUB
```

### 3. Regular Users (View-Only)

**Access Level**: Read-only access to menu items

**How to grant access**:

1. Run the RBAC seed (if not already done):
```bash
python -m app.seeds.seed_menu_management_rbac [TENANT_CODE]
```

2. Add users to the "Menu Viewers" group

This grants the `menu:read:tenant` permission.

### 4. No Access

Users not in any menu-related group have no menu management access.

## Menu Permissions Reference

| Permission Code | Description | Menu Admin | Menu Viewer | Superuser |
|----------------|-------------|------------|-------------|-----------|
| `menu:read:tenant` | View menu items | ✓ | ✓ | ✓ |
| `menu:create:tenant` | Create new menu items | ✓ | ✗ | ✓ |
| `menu:update:tenant` | Update existing menu items | ✓ | ✗ | ✓ |
| `menu:delete:tenant` | Delete menu items | ✓ | ✗ | ✓ |
| `menu:manage:tenant` | Full menu management access | ✓ | ✗ | ✓ |

## Implementation Details

### Automatic Permission Checking

The system uses a dependency injection pattern for permission checking:

```python
@router.get("/menu")
async def get_menus(
    current_user: User = Depends(has_permission("menu:read:tenant"))
):
    # Superusers automatically pass the permission check
    # Other users must have the permission via RBAC
    ...
```

### Code Reference

- Permission checking logic: `backend/app/core/dependencies.py:108-133`
- Superuser bypass: Lines 120-122
- Menu permissions seed: `backend/app/seeds/seed_menu_items.py:23-123`
- RBAC setup: `backend/app/seeds/seed_menu_management_rbac.py`

## Quick Start

### For a New Tenant

1. **Seed menu permissions** (creates the permission records):
```bash
python -m app.seeds.seed_menu_items
```

2. **Seed menu RBAC** (creates roles & groups for your tenant):
```bash
python -m app.seeds.seed_menu_management_rbac [TENANT_CODE]
```

3. **Add users to groups** (via admin UI or database):
   - Add tenant admins to "Menu Administrators" group
   - Add regular users to "Menu Viewers" group (optional)

4. **Superusers**: No action needed - they already have full access!

### For Existing Tenants

If you already have admin roles defined:

```bash
# Assign menu permissions to your existing admin role
python assign_menu_permissions.py [YOUR_ADMIN_ROLE_CODE] [TENANT_CODE]
```

## Troubleshooting

### "Permission 'menu:manage:tenant' required" Error

**For regular users**: Add them to the "Menu Administrators" group

**For superusers**: Check that `is_superuser=True` in the database:
```sql
SELECT email, is_superuser FROM users WHERE email = 'your@email.com';
```

### Menu Permissions Don't Exist

Run the menu items seed first:
```bash
python -m app.seeds.seed_menu_items
```

### Roles Not Found

List available roles and tenants:
```bash
python assign_menu_permissions.py
```

## API Endpoints

All menu management endpoints require appropriate permissions:

- `GET /api/v1/menu` - Requires `menu:read:tenant`
- `POST /api/v1/menu` - Requires `menu:create:tenant`
- `PUT /api/v1/menu/{id}` - Requires `menu:update:tenant`
- `DELETE /api/v1/menu/{id}` - Requires `menu:delete:tenant`

Superusers can access all endpoints without explicit permission assignments.
