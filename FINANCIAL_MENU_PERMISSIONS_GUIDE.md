# Financial Module Menu Not Showing - Permissions Guide

## Issue Summary

**Problem:** The financial module loads successfully (5 routes registered, 5 menu items registered) but the Financial menu doesn't appear in the sidebar.

**Root Cause:** The menu items are being filtered out due to missing permissions. The financial module requires specific permissions that the current user doesn't have.

## How Menu Filtering Works

1. **Module Loads**: Financial module successfully loads and registers 5 menu items
2. **Permission Check**: When rendering the menu, the system calls `getAccessibleMenuItems()`
3. **Filter**: Each menu item with a `permission` field is checked against the user's permissions
4. **Result**: Menu items the user doesn't have permission for are hidden (security feature)

## Financial Module Required Permissions

The financial module requires these permissions:

```
financial:accounts:read:company   - View accounts and dashboard
financial:invoices:read:company   - View invoices
financial:payments:read:company   - View payments
financial:reports:read:company    - View financial reports
```

## Diagnostic Steps

### 1. Check Console Logs

Refresh the page and open browser console (F12). Look for:

```
[User] Current user: {email, is_superuser, permissions: [...]}
```

Check if `permissions` array contains the financial permissions listed above.

### 2. Check Menu Filtering

Look for these logs:

```
[Menu Filter] Checking X menu items for permissions
[Menu Filter] ✗ "Financial" - missing permission: financial:accounts:read:company
[Menu Filter] Result: Y/X items accessible
```

The `✗` indicates which permissions are missing.

### 3. Check Permission Checks

For each missing permission, you'll see:

```
[Permission] ✗ Unknown action 'read' - denying permission: financial:accounts:read:company
```

This means the user doesn't have the permission in their permissions array.

## Solution: Grant Financial Permissions

### Option 1: Run RBAC Seed Script (Recommended for Development)

This creates test users with financial permissions:

```bash
cd /home/user/app-buildify/backend
python -m app.seeds.seed_financial_rbac
```

This creates users like:
- `cfo@fashionhub.com` / `password123` - Full financial access
- `accountant@fashionhub.com` / `password123` - Accounts access
- `billing@fashionhub.com` / `password123` - Invoice access

Log in with one of these users and the financial menu should appear.

### Option 2: Grant Permissions to Existing User (Production)

If you want your current user to have financial access:

1. **Via API** (requires admin/superuser):
```bash
# Get user's groups
curl -X GET "http://localhost:8000/api/v1/rbac/users/{user_id}/groups" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Add user to Financial Users group
curl -X POST "http://localhost:8000/api/v1/rbac/users/{user_id}/groups/{group_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

2. **Via Database** (development only):
```sql
-- Find the Financial Users group
SELECT id, name FROM groups WHERE name LIKE '%Financial%';

-- Find your user
SELECT id, email FROM users WHERE email = 'your@email.com';

-- Add user to group
INSERT INTO user_group_roles (user_id, group_id, role_id, granted_by_user_id)
SELECT
  (SELECT id FROM users WHERE email = 'your@email.com'),
  g.id,
  r.id,
  (SELECT id FROM users WHERE is_superuser = true LIMIT 1)
FROM groups g
JOIN roles r ON r.name = 'Financial Manager'
WHERE g.name = 'Financial Users';
```

3. **Via Admin UI** (if RBAC management page exists):
   - Go to RBAC Management
   - Find your user
   - Add them to "Financial Users" group with "Financial Manager" or "Financial Viewer" role

### Option 3: Make User Superuser (Development Only)

Superusers bypass all permission checks:

```sql
UPDATE users SET is_superuser = true WHERE email = 'your@email.com';
```

**Warning**: This grants full system access. Only use in development!

## Understanding the RBAC System

### Structure

```
Users → User-Group-Role Mappings → Groups → Roles → Permissions
```

### Example: Financial Access

1. **Permission**: `financial:accounts:read:company`
2. **Role**: "Financial Manager" role contains this permission
3. **Group**: "Financial Users" group for organizing users
4. **Mapping**: User + Group + Role → grants permissions to user

### How Permissions Are Checked

```javascript
// 1. Check if user is superuser (bypass all checks)
if (user.is_superuser) return true;

// 2. Check if permission is in user's permissions array
if (user.permissions.includes(permission)) return true;

// 3. Fallback to role checks (only works for simple permissions)
// This won't work for module-specific permissions like "financial:accounts:read:company"
```

## Verification

After granting permissions:

1. **Log out and log back in** - This refreshes the user's permissions
2. **Hard refresh** the browser (Ctrl+Shift+R or Cmd+Shift+R)
3. **Check console logs** - Should now show:
   ```
   [Permission] ✓ User has permission in permissions array: financial:accounts:read:company
   [Menu Filter] ✓ "Financial" - has permission: financial:accounts:read:company
   ```
4. **Financial menu appears** in the sidebar

## Troubleshooting

### Financial Menu Still Not Showing

1. **Check you're logged in as the right user**:
   ```
   [User] Current user: {email: 'cfo@fashionhub.com', ...}
   ```

2. **Check permissions array is not empty**:
   ```
   [User] Current user: {..., permissions_count: 20, permissions: ['financial:accounts:read:company', ...]}
   ```

3. **Clear browser cache and local storage**:
   ```javascript
   // In browser console:
   localStorage.clear();
   // Then refresh
   ```

4. **Verify module is enabled for your tenant**:
   - Go to Module Management page
   - Check "Enabled Modules" tab
   - Financial Management should be listed
   - If not, enable it from "Available Modules" tab

### Permission Checks Failing

If you see:
```
[Permission] ✗ Unknown action 'read' - denying permission: financial:accounts:read:company
```

This means the `can()` function doesn't recognize the permission format. The permission needs to be in the user's `permissions` array - the fallback logic only works for simple permissions.

**Solution**: Grant the permission via RBAC system (see Option 2 above).

## Related Files

- **Menu Filtering**: `frontend/assets/js/core/module-system/module-registry.js` (getAccessibleMenuItems)
- **Permission Checks**: `frontend/assets/js/rbac.js` (can, hasPermission)
- **Module Manifest**: `frontend/modules/financial/manifest.json` (defines required permissions)
- **RBAC Seed**: `backend/app/seeds/seed_financial_rbac.py` (creates test users and permissions)
- **Backend Auth**: `backend/app/routers/auth.py` (/auth/me endpoint returns user with permissions)

## Quick Reference

### Console Debug Commands

```javascript
// Check current user
getCurrentUser()

// Check if user has specific permission
hasPermission('financial:accounts:read:company')

// Check user's permissions array
getCurrentUser().permissions

// Check all menu items
moduleRegistry.menuItems

// Check accessible menu items
await moduleRegistry.getAccessibleMenuItems()
```

### Test Users (after running RBAC seed)

| Email | Password | Access Level |
|-------|----------|--------------|
| `cfo@fashionhub.com` | `password123` | Full financial access (all permissions) |
| `accountant@fashionhub.com` | `password123` | Accounts and reports |
| `ar-clerk@fashionhub.com` | `password123` | Invoices only |
| `ap-clerk@fashionhub.com` | `password123` | Payments only |
| `billing-clerk@fashionhub.com` | `password123` | Invoices (read only) |

## Summary

The financial module IS working correctly - it's loading, registering routes and menus. The menu is hidden because:

1. **By Design**: The system filters menus based on user permissions (security feature)
2. **Missing Permissions**: Current user doesn't have financial permissions
3. **Solution**: Grant the user financial permissions via RBAC system

This is the correct behavior - users should only see menus they have permission to access.
