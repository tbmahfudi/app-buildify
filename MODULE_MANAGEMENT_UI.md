# Module Management UI Documentation

Complete frontend interface for managing modules with RBAC permissions.

## Features

### For Superusers
- **Install/Uninstall Modules**: Platform-wide module installation
- **Sync Modules**: Discover new modules from filesystem
- **Full Control**: Access to all module management features

### For Tenant Admins
- **Enable/Disable Modules**: Activate modules for their tenant
- **Configure Modules**: Update module settings
- **View Module Details**: See available modules and their status

### For All Users
- **View Available Modules**: Browse the module catalog
- **See Enabled Modules**: Check which modules are active

## RBAC Permissions

The following permissions control access to module management:

### Platform-Wide Operations (Superuser Only)
```
modules:install:all       - Install modules platform-wide
modules:uninstall:all     - Uninstall modules platform-wide
modules:sync:all          - Sync modules from filesystem
```

### Tenant Operations
```
modules:list:tenant       - View list of available modules
modules:view:tenant       - View detailed module information
modules:enable:tenant     - Enable modules for tenant
modules:disable:tenant    - Disable modules for tenant
modules:configure:tenant  - Update module configuration
modules:manage:tenant     - Access module management page
```

## Setup Instructions

### 1. Seed Module Management Permissions

```bash
# From the backend directory
python -m app.seeds.seed_module_management_rbac
```

This creates all necessary permissions in the database.

### 2. Grant Permissions to Roles

For **Superusers**: Permissions are automatically granted.

For **Tenant Admins**: Grant the `modules:manage:tenant` permission:

```python
from app.models.permission import Permission
from app.models.role import Role
from app.models.rbac_junctions import RolePermission
from app.core.db import SessionLocal

db = SessionLocal()

# Get the admin role
admin_role = db.query(Role).filter(Role.code == "ADMIN").first()

# Get module management permission
perm = db.query(Permission).filter(Permission.code == "modules:manage:tenant").first()

# Assign permission to role
role_perm = RolePermission(
    role_id=admin_role.id,
    permission_id=perm.id
)
db.add(role_perm)
db.commit()
```

### 3. Access the Module Management Page

Navigate to: `http://localhost:8000/app#modules`

The menu item will only appear for users with the `modules:manage:tenant` permission.

## UI Components

### Available Modules Tab

Displays all modules discovered by the system with:
- Module name, version, and description
- Status badge (stable, beta, available, deprecated)
- Category and subscription tier
- Install button (superuser only)
- Enable button (after installation)

### Enabled Modules Tab

Shows modules currently enabled for your tenant:
- Module details and version
- Enable date
- Configure button
- Disable button

### Module Cards

Each module card displays:
- **Status Badge**: Visual indicator of module stability
- **Version**: Current module version
- **Category**: Module classification
- **Subscription Tier**: Required subscription level (if any)
- **Actions**: Context-sensitive buttons based on permissions

## User Experience

### Installation Flow (Superuser)
1. Navigate to Module Management
2. Find module in Available Modules tab
3. Click "Install" button
4. Confirm installation
5. Module becomes available for tenant enablement

### Enablement Flow (Tenant Admin)
1. Navigate to Module Management
2. Find installed module in Available Modules tab
3. Click "Enable" button
4. Module is enabled with default configuration
5. Page reloads to load the new module
6. Module appears in navigation menu

### Configuration Flow
1. Go to Enabled Modules tab
2. Click "Configure" on any enabled module
3. Update module settings
4. Save configuration

### Disablement Flow
1. Go to Enabled Modules tab
2. Click "Disable" on module
3. Confirm disablement
4. Page reloads to unload the module

## Visual Design

The module management UI features:

- **Modern Card Layout**: Clean, responsive grid design
- **Icon-Based Navigation**: Phosphor icons for clarity
- **Status Badges**: Color-coded indicators
- **Permission Indicators**: Clear visual cues for access levels
- **Loading States**: Smooth loading animations
- **Error Handling**: User-friendly error messages
- **Toast Notifications**: Non-intrusive feedback

### Color Scheme

- **Blue**: Primary actions (install, enable)
- **Green**: Success states (enabled modules)
- **Yellow**: Warning states (beta modules)
- **Red**: Destructive actions (uninstall, disable)
- **Gray**: Neutral states (core modules, disabled features)

## Permission Checks

The UI implements multiple permission checks:

```javascript
// Check if user can access management page
const canManage = await hasPermission('modules:manage:tenant');

// Check if user is superuser (for install/uninstall)
const isSuperUser = isSuperuser();
```

Buttons and features are shown/hidden based on these checks.

## API Integration

The module manager communicates with these backend endpoints:

```javascript
GET  /api/v1/modules/available     // List all modules
GET  /api/v1/modules/enabled       // List enabled modules
GET  /api/v1/modules/{name}        // Get module details
POST /api/v1/modules/install       // Install module (superuser)
POST /api/v1/modules/uninstall     // Uninstall module (superuser)
POST /api/v1/modules/enable        // Enable for tenant
POST /api/v1/modules/disable       // Disable for tenant
POST /api/v1/modules/sync          // Sync from filesystem (superuser)
PUT  /api/v1/modules/{name}/config // Update configuration
```

## Files Modified

### Backend
- `backend/app/seeds/seed_module_management_rbac.py` - Permission seeder
- `backend/app/models/permission.py` - Permission model (reference)

### Frontend
- `frontend/config/menu.json` - Added module management menu item
- `frontend/assets/templates/modules.html` - Page template
- `frontend/assets/js/module-manager-enhanced.js` - Enhanced UI component
- `frontend/assets/js/rbac.js` - Updated permission filtering

## Troubleshooting

### Menu Item Not Showing

**Issue**: Module Management doesn't appear in the navigation menu.

**Solution**:
1. Check user has `modules:manage:tenant` permission
2. Run permission seed script
3. Clear browser cache and reload

### Cannot Install Modules

**Issue**: Install button is disabled or missing.

**Solution**: Only superusers can install modules platform-wide.

### Modules Not Loading

**Issue**: Available modules list is empty.

**Solution**:
1. Check that modules exist in `backend/modules/` directory
2. Run sync from the UI (superuser only)
3. Restart backend to trigger module discovery

### Enable Fails

**Issue**: Cannot enable module for tenant.

**Solution**:
1. Ensure module is installed first (superuser operation)
2. Check tenant subscription tier matches module requirements
3. Verify no dependency conflicts

## Next Steps

1. **Implement Configuration UI**: Modal for editing module settings
2. **Add Module Marketplace**: Browse and download modules
3. **Module Analytics**: Track usage and performance
4. **Bulk Operations**: Enable/disable multiple modules at once
5. **Module Dependencies**: Visual dependency graph

## Related Documentation

- `FINANCIAL_MODULE_SETUP.md` - Financial module setup guide
- `QUICK_START_MODULES.md` - Quick start for modules
- `backend/app/core/module_system/` - Module system architecture
