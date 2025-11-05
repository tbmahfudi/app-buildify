# Module Management UI - Quick Setup Guide

Complete module management interface for superusers and tenant admins.

## What Was Created

### Backend (RBAC Permissions)
- `backend/app/seeds/seed_module_management_rbac.py` - Permission seeder
- 9 new permissions for module management

### Frontend (UI Components)
- `frontend/assets/js/module-manager-enhanced.js` - Enhanced module manager
- `frontend/assets/templates/modules.html` - Page template
- `frontend/config/menu.json` - Added "Module Management" menu item
- `frontend/assets/js/rbac.js` - Updated for permission-based menu filtering

### Documentation
- `MODULE_MANAGEMENT_UI.md` - Complete documentation
- `MODULE_MANAGEMENT_SETUP.md` - This file

## Quick Setup (3 Steps)

### Step 1: Create Permissions

```bash
cd /home/user/app-buildify/backend
python -m app.seeds.seed_module_management_rbac
```

Expected output:
```
✓ Created 9 new permissions
  - modules:install:all (superuser only)
  - modules:uninstall:all (superuser only)
  - modules:sync:all (superuser only)
  - modules:enable:tenant
  - modules:disable:tenant
  - modules:configure:tenant
  - modules:manage:tenant
  - modules:list:tenant
  - modules:view:tenant
```

### Step 2: Restart Backend

```bash
# Restart your backend server to pick up the new menu configuration
docker-compose restart backend
# or
./manage.sh restart
```

### Step 3: Access Module Management

1. Login as a superuser
2. Navigate to: `http://localhost:8000/app#modules`
3. The "Module Management" menu item should appear in the sidebar

## Features by User Type

### Superusers

**Can Do:**
- ✅ Install modules platform-wide
- ✅ Uninstall modules
- ✅ Sync modules from filesystem
- ✅ Enable modules for their tenant
- ✅ Disable modules for their tenant
- ✅ Configure module settings

**UI Elements:**
- "Sync Modules" button in header
- "Install" buttons on uninstalled modules
- "Uninstall" buttons on installed modules
- Blue superuser mode badge

### Tenant Admins (with `modules:manage:tenant` permission)

**Can Do:**
- ✅ View available modules
- ✅ Enable installed modules for their tenant
- ✅ Disable modules for their tenant
- ✅ Configure module settings

**UI Elements:**
- "Enable" buttons on installed modules
- "Disable" buttons in Enabled Modules tab
- "Configure" buttons for enabled modules

### Regular Users

**Cannot access** module management page (menu item hidden).

## UI Screenshots

### Available Modules Tab
```
┌─────────────────────────────────────────────────────┐
│ 🔷 Module Management                    [Sync] 🔄   │
│ Install and configure modules for your platform     │
│                                                      │
│ [Available Modules] [Enabled Modules]               │
│                                                      │
│ 🔍 [Search modules...]                              │
│                                                      │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│ │ Financial    │ │ Inventory    │ │ HR Module    │ │
│ │ v1.0.0       │ │ v1.2.0       │ │ v2.0.0       │ │
│ │ [Install] 📥 │ │ [Enable] ✅  │ │ [Install] 📥 │ │
│ └──────────────┘ └──────────────┘ └──────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Enabled Modules Tab
```
┌─────────────────────────────────────────────────────┐
│ Financial Management          v1.0.0    Enabled ✓   │
│ Enabled: Jan 15, 2024                               │
│                                [Configure] [Disable]│
├─────────────────────────────────────────────────────┤
│ Inventory Management         v1.2.0    Enabled ✓    │
│ Enabled: Jan 20, 2024                               │
│                                [Configure] [Disable]│
└─────────────────────────────────────────────────────┘
```

## Permission Matrix

| Action | Permission Required | User Type |
|--------|-------------------|-----------|
| View module list | `modules:list:tenant` | All with `modules:manage:tenant` |
| View module details | `modules:view:tenant` | All with `modules:manage:tenant` |
| Install module | `modules:install:all` | **Superuser only** |
| Uninstall module | `modules:uninstall:all` | **Superuser only** |
| Sync modules | `modules:sync:all` | **Superuser only** |
| Enable for tenant | `modules:enable:tenant` | Tenant Admin |
| Disable for tenant | `modules:disable:tenant` | Tenant Admin |
| Configure module | `modules:configure:tenant` | Tenant Admin |
| Access management page | `modules:manage:tenant` | Tenant Admin |

## API Endpoints Used

```
GET  /api/v1/modules/available      - List all modules
GET  /api/v1/modules/enabled        - List enabled for tenant
POST /api/v1/modules/install        - Install (superuser)
POST /api/v1/modules/uninstall      - Uninstall (superuser)
POST /api/v1/modules/enable         - Enable for tenant
POST /api/v1/modules/disable        - Disable for tenant
POST /api/v1/modules/sync           - Sync (superuser)
PUT  /api/v1/modules/{name}/config  - Update config
```

## Testing Checklist

### As Superuser
- [ ] Navigate to Module Management
- [ ] See "Sync Modules" button
- [ ] See "Superuser Mode" blue badge
- [ ] Click "Install" on financial module
- [ ] Click "Enable" on financial module
- [ ] See module in Enabled Modules tab
- [ ] Click "Configure" (shows coming soon message)
- [ ] Click "Disable" on module
- [ ] Click "Uninstall" on module

### As Tenant Admin (if you grant them permission)
- [ ] Navigate to Module Management
- [ ] No "Sync Modules" button (superuser only)
- [ ] No "Superuser Mode" badge
- [ ] Can see installed modules
- [ ] Can enable installed modules
- [ ] Can disable enabled modules
- [ ] Cannot install/uninstall (buttons hidden)

### As Regular User
- [ ] "Module Management" NOT in menu

## Troubleshooting

### Menu item not showing

```bash
# 1. Check permissions were created
psql -d your_db -c "SELECT * FROM permissions WHERE resource = 'modules';"

# 2. Check user has permission
# Login and check browser console for RBAC errors

# 3. Clear cache
# Hard refresh browser (Ctrl+Shift+R)
```

### Install button missing

**Solution**: Only superusers see install buttons. Check `user.is_superuser = true`.

### Cannot enable module

**Possible causes**:
1. Module not installed (install first as superuser)
2. Subscription tier mismatch (financial module requires "premium")
3. Module has unmet dependencies

**Check**:
```bash
# Check module installation status
curl http://localhost:8000/api/v1/modules/available \
  -H "Authorization: Bearer $TOKEN" | jq '.modules[] | select(.name=="financial")'
```

## Next Steps

1. **Run permission seeder** (if not done):
   ```bash
   python -m app.seeds.seed_module_management_rbac
   ```

2. **Install and enable financial module**:
   - See `FINANCIAL_MODULE_SETUP.md` for detailed steps
   - Or use the new UI!

3. **Grant permission to tenant admins** (optional):
   ```sql
   -- Grant module management permission to a role
   INSERT INTO role_permissions (role_id, permission_id)
   SELECT r.id, p.id
   FROM roles r, permissions p
   WHERE r.code = 'TENANT_ADMIN'
   AND p.code = 'modules:manage:tenant';
   ```

4. **Test the UI**:
   - Login as superuser
   - Go to `#modules`
   - Install and enable modules

## Related Files

- `MODULE_MANAGEMENT_UI.md` - Full documentation
- `QUICK_START_MODULES.md` - Quick start guide
- `FINANCIAL_MODULE_SETUP.md` - Financial module setup
- `frontend/assets/js/module-manager-enhanced.js` - UI code
- `backend/app/seeds/seed_module_management_rbac.py` - Permission seeder

## Support

If you encounter issues:
1. Check browser console for errors
2. Check backend logs for permission errors
3. Verify permissions exist in database
4. Ensure user is superuser or has `modules:manage:tenant`

---

**Success!** 🎉 You now have a complete module management interface with proper RBAC controls.
