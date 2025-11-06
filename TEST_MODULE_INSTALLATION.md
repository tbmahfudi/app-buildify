# Module Installation Testing Guide

## Prerequisites
✅ All code changes are committed and pushed to branch: `claude/initialize-module-system-011CUqKEgmWDvWvRdsk5XomM`

✅ Files verified:
- Backend: `backend/app/core/module_system/registry.py` (UUID fix at line 453)
- Backend: `backend/app/seeds/seed_module_management_rbac.py` (9 permissions)
- Frontend: `frontend/assets/js/module-manager-enhanced.js` (20KB UI)
- Frontend: `frontend/assets/js/modules.js` (route handler)
- Frontend: `frontend/assets/templates/modules.html` (container)

## Step 1: Restart Backend

**Important**: The backend must be restarted to load all the fixes.

```bash
# If using Docker:
cd /home/user/app-buildify/infra
docker-compose -f docker-compose.dev.yml restart backend

# If using direct Python:
# Kill existing process and restart
pkill -f uvicorn
cd /home/user/app-buildify/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 2: Verify Backend Started Successfully

Check the logs for:
```
✓ Module system initialized
✓ Discovered modules: ['financial']
✓ Financial module loaded successfully
```

## Step 3: Access Module Manager UI

1. Open browser: `http://localhost:8000/app`
2. Login as superuser
3. Look for "Module Management" in the navigation menu
4. Click it or navigate to: `http://localhost:8000/app#modules`

**Expected Result**: You should see the module manager UI with two tabs:
- "Available Modules" (showing financial module card)
- "Enabled Modules" (initially empty)

## Step 4: Install Financial Module

1. In the "Available Modules" tab, find the "Financial Management" card
2. Click the "Install" button
3. Watch for success notification

**What Happens**:
- Backend checks database connection (pre-install)
- Creates module registry entry
- Registers 22 financial permissions
- Sets status to "installed"

**Expected Logs**:
```
[info] Pre-install check passed for module: financial
[info] Module financial installed successfully
[info] Registered permission: financial:accounts:read:company
[info] Registered permission: financial:accounts:create:company
... (20 more permissions)
```

## Step 5: Verify Installation

Check these endpoints:

```bash
# List all modules
curl http://localhost:8000/api/v1/modules

# Should show:
# {
#   "modules": [{
#     "name": "financial",
#     "display_name": "Financial Management",
#     "version": "1.0.0",
#     "is_installed": true,
#     "is_enabled": false,  ← Not enabled yet!
#     ...
#   }]
# }

# Check enabled modules (should still be empty)
curl http://localhost:8000/api/v1/modules/enabled/names
# Expected: []
```

## Step 6: Enable Module for Tenant

1. In the UI, switch to the "Enabled Modules" tab
2. The financial module should now appear in "Available Modules" with status "installed"
3. Click "Enable" button
4. The module should move to "Enabled Modules" tab

**What Happens**:
- Backend runs pre-enable hooks
- Creates tenant_module entry
- Runs post-enable hooks (creates default accounts)
- Module is now active for your tenant

**Expected Logs**:
```
[info] Pre-enable check passed for module: financial
[info] Module financial enabled for tenant: <tenant_id>
[info] Created 50 default financial accounts
```

## Step 7: Verify Financial Module is Active

```bash
# Check enabled modules
curl http://localhost:8000/api/v1/modules/enabled/names
# Expected: ["financial"]

# Check financial API is accessible
curl -H "Authorization: Bearer <your_token>" \
     -H "X-Tenant-Id: <your_tenant>" \
     http://localhost:8000/api/v1/financial/accounts
# Expected: List of accounts
```

## Step 8: Verify Navigation Menu

1. Refresh the browser
2. Look for "Financial" section in the navigation menu
3. Should see sub-items:
   - Chart of Accounts
   - Transactions
   - Invoices
   - Payments
   - Reports

## Troubleshooting

### Issue: Menu item "Module Management" not showing
**Solution**:
```bash
# Run permission seeder
cd /home/user/app-buildify/backend
python -m app.seeds.seed_module_management_rbac
```
Or access directly: `http://localhost:8000/app#modules` (superusers bypass permission checks)

### Issue: Installation fails with UUID error
**Status**: ✅ FIXED - `db.flush()` added at line 453

### Issue: Installation fails with NULL constraint on permissions
**Status**: ✅ FIXED - Permission parsing added at lines 422-434

### Issue: Installation fails with SQLAlchemy text() error
**Status**: ✅ FIXED - `text()` wrapper added in financial module

### Issue: Installation fails with validation error
**Status**: ✅ FIXED - Content-Type header added to all API requests

### Issue: 404 on #modules route
**Status**: ✅ FIXED - Requires backend restart (Step 1)

### Issue: JavaScript not loading
**Status**: ✅ FIXED - Separate modules.js file created

## Success Criteria

- ✅ Module Manager UI loads without errors
- ✅ Financial module shows in "Available Modules"
- ✅ Installation completes successfully
- ✅ Module moves to "Enabled Modules" after enable
- ✅ Financial menu appears in navigation
- ✅ Financial API endpoints are accessible
- ✅ `/api/v1/modules/enabled/names` returns `["financial"]`

## Next Steps After Success

1. Test other module operations:
   - Disable module
   - Re-enable module
   - Configure module settings
   - View module details

2. Test permission system:
   - Login as non-superuser
   - Verify they can only enable/disable (not install/uninstall)
   - Test financial permissions (view accounts, create transactions, etc.)

3. Create additional modules:
   - Use financial module as a template
   - Test multi-module installation
   - Test module dependencies

## Support

If you encounter any issues not covered here:
1. Check backend logs for detailed error messages
2. Check browser console for frontend errors
3. Verify database connection is working
4. Ensure all migrations have run

---

**Current Branch**: `claude/initialize-module-system-011CUqKEgmWDvWvRdsk5XomM`

**Last Fix**: UUID mismatch error (line 453: added `db.flush()`)

**Status**: Ready for testing! 🚀
