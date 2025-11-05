# Troubleshooting: Module Management Page Not Showing

## Issue
The Module Management page (#modules) is not appearing in the navigation menu.

## Root Cause
The menu item requires the `modules:manage:tenant` permission, which hasn't been created yet in the database.

## Solution Options

### Option 1: Access Directly (Superusers)

If you're a **superuser**, the page should work even without running the permission seed. Just navigate directly:

```
http://localhost:8000/app#modules
```

Or in your browser console:
```javascript
window.location.hash = 'modules';
```

The permission check has been updated so superusers automatically bypass permission requirements.

### Option 2: Run Permission Seeder (Recommended)

This creates all the necessary permissions in the database:

```bash
cd /home/user/app-buildify/backend
python -m app.seeds.seed_module_management_rbac
```

After running this, the menu item will appear for:
- All superusers
- Any user/role with the `modules:manage:tenant` permission

### Option 3: Temporarily Remove Permission Check

Edit `frontend/config/menu.json` and remove the permission line:

```json
{
  "title": "Module Management",
  "route": "modules",
  "icon": "ph ph-package"
  // Remove: "permission": "modules:manage:tenant"
}
```

This will show the menu item to all users (not recommended for production).

## Verification Steps

### 1. Check if you're a superuser

Open browser console (F12) and run:
```javascript
// After logging in
fetch('/api/v1/auth/me', {
  headers: {
    'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('tokens')).access_token
  }
})
.then(r => r.json())
.then(user => console.log('Is superuser:', user.is_superuser));
```

### 2. Test direct route access

Navigate to: `http://localhost:8000/app#modules`

If you see a loading spinner or the module management page, the route works!

### 3. Check menu visibility

The menu item should appear if:
- You're a superuser (always has access)
- OR you have the `modules:manage:tenant` permission

### 4. Check browser console

Look for errors in the browser console (F12):
```
- Module not found errors
- Permission denied errors
- 404 errors on JavaScript files
```

## Common Issues

### Issue: "Module Management" not in menu

**Cause**: Permission not granted or not seeded.

**Fix**:
1. Run the permission seeder (Option 2 above)
2. OR access directly via `#modules` (superusers only)

### Issue: Clicking link shows 404 or blank page

**Cause**: Template file missing or JavaScript import error.

**Fix**: Check these files exist:
```bash
ls -la frontend/assets/templates/modules.html
ls -la frontend/assets/js/module-manager-enhanced.js
```

### Issue: Permission check fails even as superuser

**Cause**: Old permission check logic.

**Fix**: Already fixed! The RBAC code now properly checks `user.is_superuser`.

### Issue: Menu shows but page is blank

**Cause**: JavaScript import error.

**Fix**: Check browser console for:
- `Failed to load module`
- `Import not found`
- CORS errors

## Quick Test Script

Run this in browser console after logging in:

```javascript
// Test 1: Check user status
const user = window.appState?.user || JSON.parse(localStorage.getItem('user_info'));
console.log('User:', user?.email);
console.log('Is Superuser:', user?.is_superuser);

// Test 2: Navigate to modules
window.location.hash = 'modules';

// Test 3: Check if page loaded
setTimeout(() => {
  const content = document.getElementById('app-content');
  console.log('Page content:', content?.innerHTML?.substring(0, 100));
}, 1000);
```

## Expected Behavior

### For Superusers (Before Seeding Permissions)
✅ Can access via direct link (`#modules`)
✅ Menu item shows (permission check passes for superusers)
✅ Can install/uninstall modules
✅ Can enable/disable modules

### For Regular Users (Before Seeding Permissions)
❌ Menu item hidden (no permission)
❌ Cannot access page

### After Seeding Permissions
✅ Superusers: Full access
✅ Users with permission: Can manage modules
❌ Users without permission: No access

## Files to Check

Ensure these files are present and correct:

```bash
# Frontend files
frontend/assets/js/module-manager-enhanced.js
frontend/assets/templates/modules.html
frontend/config/menu.json

# Backend files
backend/app/seeds/seed_module_management_rbac.py
backend/app/routers/modules.py
```

## Still Not Working?

1. **Clear browser cache**: Hard refresh (Ctrl+Shift+R)
2. **Check server logs**: Look for errors in backend logs
3. **Restart backend**: Reload menu configuration
4. **Check network tab**: Look for failed API requests
5. **Console errors**: Check browser console for JavaScript errors

## Contact Support

If none of these solutions work, provide:
- Browser console errors
- Backend server logs
- User role/permissions
- Steps to reproduce

---

**TL;DR for Superusers**: Just go to `http://localhost:8000/app#modules` directly. The menu item will show up after you run the permission seeder.
