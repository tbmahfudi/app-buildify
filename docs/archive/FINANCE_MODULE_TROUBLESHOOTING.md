# Financial Module Troubleshooting Guide

## Problem: Finance Module Menu Not Showing in Sidebar

This guide helps you diagnose and fix issues when the financial module menu doesn't appear in the sidebar.

---

## Quick Diagnosis

### Option 1: Browser-Based Diagnostic (Recommended)

1. Open your browser and navigate to:
   ```
   http://localhost:[PORT]/debug-financial-module.html
   ```

2. The diagnostic tool will automatically check:
   - Authentication status
   - Backend module enablement
   - Frontend module loading
   - Permission status
   - Menu item registration

3. Follow the recommendations shown in the results

### Option 2: Shell Script

```bash
# Set your auth token
export AUTH_TOKEN="your_access_token_here"

# Run the enable script
./enable_finance_module.sh
```

---

## Common Issues and Solutions

### Issue 1: Module Not Enabled for Tenant

**Symptoms:**
- API call `/api/v1/modules/enabled/names` doesn't include "financial"
- Backend shows module as available but not enabled

**Solution:**

#### Via API (cURL):
```bash
curl -X POST http://localhost:8000/api/v1/modules/enable \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "financial",
    "configuration": {
      "default_currency": "USD",
      "fiscal_year_start": "01-01",
      "enable_multi_currency": false,
      "tax_rate": 0,
      "invoice_prefix": "INV"
    }
  }'
```

#### Via Python:
```bash
cd /home/user/app-buildify
python setup_financial_module.py
```

#### Via Browser:
1. Log in as a superuser or tenant admin
2. Navigate to Module Management (if available)
3. Find "Financial Management" and click Enable

---

### Issue 2: Module Not Installed Platform-Wide

**Symptoms:**
- Module registered but `is_installed = false`
- Enable endpoint returns error

**Solution:**

#### Via API (Requires Superuser):
```bash
curl -X POST http://localhost:8000/api/v1/modules/install \
  -H "Authorization: Bearer SUPERUSER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"module_name": "financial"}'
```

#### Via Python:
```bash
cd /home/user/app-buildify/backend
python -c "
from app.core.db import SessionLocal
from app.core.module_system.registry import ModuleRegistryService
from pathlib import Path

db = SessionLocal()
modules_path = Path('/home/user/app-buildify/backend/modules')
registry = ModuleRegistryService(db, modules_path)

# Sync modules
registry.sync_modules()

# Install financial module (requires superuser ID)
success, error = registry.install_module('financial', 'SUPERUSER_ID_HERE')
print('Success!' if success else f'Error: {error}')

db.close()
"
```

---

### Issue 3: User Lacks Financial Permissions

**Symptoms:**
- Module enabled and loaded
- Menu items exist but not visible
- Permission check returns false

**Solution:**

#### Set up RBAC (Recommended):
```bash
cd /home/user/app-buildify
python -m backend.app.seeds.seed_financial_rbac.py
```

This script:
- Creates financial roles (Financial Manager, Accountant, Billing Clerk, Financial Viewer)
- Creates financial groups
- Assigns users to groups
- Sets up all permissions

**Users created/updated:**
- `cfo@fashionhub.com` → Full Access (Financial Manager)
- `accountant1@fashionhub.com` → Accountant Access
- `accountant2@fashionhub.com` → Accountant Access
- `billing@fashionhub.com` → Billing Access
- `ar@fashionhub.com` → Billing Access
- `ceo@fashionhub.com` → View-Only Access
- `manager.nyc1@fashionhub.com` → View-Only Access

Default password for all: `password123`

---

### Issue 4: Frontend Module Not Loading

**Symptoms:**
- Backend shows module enabled
- Browser console shows module load errors
- `moduleLoader.getModule('financial')` returns null

**Possible Causes:**

#### A. Manifest not found
```
Error: Failed to load manifest: 404
```

**Solution:** Check that `/modules/financial/manifest.json` exists
```bash
ls -la /home/user/app-buildify/frontend/modules/financial/
```

#### B. Module.js has errors
```
Error: Module class not found
```

**Solution:** Check `/modules/financial/module.js`:
```bash
cat /home/user/app-buildify/frontend/modules/financial/module.js
```

Ensure it exports a default class:
```javascript
export default class FinancialModule extends BaseModule {
  // ...
}
```

#### C. Permission issues (file not readable)

**Solution:**
```bash
chmod -R 755 /home/user/app-buildify/frontend/modules/financial/
```

---

### Issue 5: Cache Issues

**Symptoms:**
- Module was working before
- Changes don't appear
- Old menu still showing

**Solution:**

1. **Hard refresh browser:**
   - Chrome/Firefox: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
   - Or: Open DevTools → Right-click refresh button → "Empty Cache and Hard Reload"

2. **Clear localStorage:**
   ```javascript
   // In browser console
   localStorage.clear();
   // Then refresh
   ```

3. **Clear backend cache** (if applicable):
   ```bash
   # Restart the backend server
   ```

---

## Verification Checklist

Use this checklist to verify each component:

### Backend Checks

- [ ] **Module registered in database**
  ```bash
  curl http://localhost:8000/api/v1/modules/financial \
    -H "Authorization: Bearer TOKEN"
  ```
  Expected: `"name": "financial"` with details

- [ ] **Module installed**
  ```bash
  # Response should show: "is_installed": true
  ```

- [ ] **Module enabled for tenant**
  ```bash
  curl http://localhost:8000/api/v1/modules/enabled/names \
    -H "Authorization: Bearer TOKEN"
  ```
  Expected: `["financial", ...]` (financial in the list)

- [ ] **Permissions exist in database**
  ```bash
  curl http://localhost:8000/api/v1/permissions?search=financial \
    -H "Authorization: Bearer TOKEN"
  ```
  Expected: List of financial permissions

### Frontend Checks

- [ ] **Module manifest accessible**
  ```
  Open: http://localhost:PORT/modules/financial/manifest.json
  ```
  Expected: Valid JSON manifest

- [ ] **Module JS file accessible**
  ```
  Open: http://localhost:PORT/modules/financial/module.js
  ```
  Expected: JavaScript module code

- [ ] **Module loaded in browser**
  ```javascript
  // In browser console after login
  window.moduleLoader.getModule('financial')
  ```
  Expected: Module object (not null)

- [ ] **Module registered**
  ```javascript
  // In browser console
  window.moduleRegistry.isModuleRegistered('financial')
  ```
  Expected: true

- [ ] **Menu items exist**
  ```javascript
  // In browser console
  window.moduleRegistry.getAllMenuItems()
    .filter(item => item.moduleName === 'financial')
  ```
  Expected: Array with 5+ items (Dashboard, Accounts, Invoices, Payments, Reports)

### Permission Checks

- [ ] **User has financial permissions**
  ```javascript
  // In browser console
  await window.hasPermission('financial:accounts:read:company')
  ```
  Expected: true

- [ ] **Accessible menu items include financial**
  ```javascript
  // In browser console
  const items = await window.moduleRegistry.getAccessibleMenuItems();
  items.filter(item => item.moduleName === 'financial')
  ```
  Expected: Array with items (not empty)

---

## Step-by-Step Fix Procedure

If you're not sure where the problem is, follow these steps in order:

### Step 1: Enable Module (if needed)
```bash
./enable_finance_module.sh
```

### Step 2: Set Up Permissions (if needed)
```bash
python -m backend.app.seeds.seed_financial_rbac.py
```

### Step 3: Verify Backend
```bash
curl http://localhost:8000/api/v1/modules/enabled/names \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Should include "financial"

### Step 4: Clear Browser Cache
- Hard refresh: `Ctrl+Shift+R` or `Cmd+Shift+R`

### Step 5: Check Browser Console
1. Open DevTools (F12)
2. Go to Console tab
3. Look for any red errors
4. Look for module loading messages

### Step 6: Run Browser Diagnostic
```
Open: http://localhost:PORT/debug-financial-module.html
```

### Step 7: Check User Permissions
Log in with a user that has financial permissions:
- `cfo@fashionhub.com` / `password123` (FashionHub tenant)

---

## Manual Database Check (Advanced)

If you have direct database access:

```sql
-- Check if module exists
SELECT name, display_name, is_installed, is_enabled
FROM module_registry
WHERE name = 'financial';

-- Check tenant modules
SELECT tm.*, t.name as tenant_name
FROM tenant_modules tm
JOIN tenants t ON t.id = tm.tenant_id
JOIN module_registry mr ON mr.id = tm.module_id
WHERE mr.name = 'financial' AND tm.is_enabled = true;

-- Check financial permissions
SELECT code, name, description
FROM permissions
WHERE code LIKE 'financial:%';

-- Check users with financial access (example for FashionHub)
SELECT u.email, u.full_name, g.name as group_name, r.name as role_name
FROM users u
JOIN user_groups ug ON ug.user_id = u.id
JOIN groups g ON g.id = ug.group_id
JOIN group_roles gr ON gr.group_id = g.id
JOIN roles r ON r.id = gr.role_id
WHERE u.tenant_id IN (
  SELECT tenant_id FROM tenant_modules tm
  JOIN module_registry mr ON mr.id = tm.module_id
  WHERE mr.name = 'financial' AND tm.is_enabled = true
);
```

---

## Still Not Working?

If the menu still doesn't show after following all steps:

1. **Check Backend Logs:**
   - Look for module loading errors
   - Check for permission errors

2. **Check Browser Console:**
   - Any JavaScript errors?
   - Module loader warnings?

3. **Verify File Permissions:**
   ```bash
   ls -la /home/user/app-buildify/frontend/modules/financial/
   ```

4. **Test with Different User:**
   - Try logging in as `cfo@fashionhub.com` / `password123`
   - This user should have full financial access

5. **Restart Everything:**
   ```bash
   # Restart backend server
   # Clear browser cache completely
   # Log out and log back in
   ```

---

## Contact/Support

If you've tried everything and it still doesn't work:

1. Run the browser diagnostic and save the output
2. Check the browser console for errors
3. Check backend logs for errors
4. Provide this information for further troubleshooting

---

## Files Reference

- **Frontend Module:** `/home/user/app-buildify/frontend/modules/financial/`
- **Backend Module:** `/home/user/app-buildify/backend/modules/financial/`
- **Diagnostic Tool:** `/home/user/app-buildify/frontend/debug-financial-module.html`
- **Enable Script:** `/home/user/app-buildify/enable_finance_module.sh`
- **RBAC Seed:** `/home/user/app-buildify/backend/app/seeds/seed_financial_rbac.py`
- **Module Setup:** `/home/user/app-buildify/setup_financial_module.py`
