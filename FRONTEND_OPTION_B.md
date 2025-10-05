# Frontend Integration - Option B

## 🎉 What's New

Complete frontend integration for Option B features:

### New JavaScript Modules

1. **`metadata-service.js`** - Metadata fetching and caching
2. **`data-service.js`** - Generic CRUD operations
3. **`dynamic-form.js`** - Metadata-driven form builder
4. **`dynamic-table.js`** - Metadata-driven data tables
5. **`entity-manager.js`** - Complete CRUD UI for any entity
6. **`audit-widget.js`** - Audit trail visualization
7. **`generic-entity-page.js`** - Universal entity page handler
8. **`settings.js`** - User and tenant settings
9. **`audit-page.js`** - Audit log viewer

### New Pages

1. **Settings** (`settings.html`) - User preferences and tenant branding
2. **Audit Trail** (`audit.html`) - System-wide audit logs
3. **Generic Entity Pages** - Auto-generated for any entity

## 📦 File Structure

```
frontend/
├── assets/
│   ├── js/
│   │   ├── api.js                    ← Option A (updated)
│   │   ├── app.js                    ← Option A (updated)
│   │   ├── metadata-service.js       ← NEW
│   │   ├── data-service.js           ← NEW
│   │   ├── dynamic-form.js           ← NEW
│   │   ├── dynamic-table.js          ← NEW
│   │   ├── entity-manager.js         ← NEW
│   │   ├── audit-widget.js           ← NEW
│   │   ├── generic-entity-page.js    ← NEW
│   │   ├── settings.js               ← NEW
│   │   └── audit-page.js             ← NEW
│   ├── templates/
│   │   ├── dashboard.html
│   │   ├── settings.html             ← NEW
│   │   └── audit.html                ← NEW
│   └── css/
│       └── app.css
├── config/
│   └── menu.json                     ← UPDATED
└── index.html                        ← UPDATED
```

## 🚀 Features

### 1. Metadata Service

**Purpose**: Fetch and cache entity metadata from the backend.

**Usage**:
```javascript
import { metadataService } from './metadata-service.js';

// Get metadata for an entity
const metadata = await metadataService.getMetadata('companies');

// List all entities
const entities = await metadataService.listEntities();

// Check permissions
const canEdit = metadataService.hasPermission(metadata, 'edit', userRoles);

// Clear cache
metadataService.clearCache('companies');
```

**Features**:
- Automatic caching
- Permission checking
- Entity discovery

### 2. Data Service

**Purpose**: Generic CRUD operations for any entity.

**Usage**:
```javascript
import { dataService } from './data-service.js';

// List with filters and sorting
const data = await dataService.list('companies', {
  page: 1,
  pageSize: 25,
  filters: [
    { field: 'code', operator: 'like', value: 'ACME' }
  ],
  sort: [['name', 'asc']]
});

// Get single record
const record = await dataService.get('companies', id);

// Create
const created = await dataService.create('companies', {
  code: 'TEST',
  name: 'Test Company'
});

// Update
const updated = await dataService.update('companies', id, {
  name: 'Updated Name'
});

// Delete
await dataService.delete('companies', id);

// Bulk operations
const result = await dataService.bulk('companies', 'create', [
  { code: 'BULK1', name: 'Bulk 1' },
  { code: 'BULK2', name: 'Bulk 2' }
]);
```

### 3. Dynamic Form Builder

**Purpose**: Automatically generate forms from metadata.

**Usage**:
```javascript
import { DynamicForm } from './dynamic-form.js';

const container = document.getElementById('form-container');
const form = new DynamicForm(container, metadata, record);

// Render the form
form.render();

// Get values
const values = form.getValues();

// Validate
if (form.validate()) {
  // Form is valid
}

// Set field error
form.setFieldError('email', 'Invalid email format');

// Clear errors
form.clearErrors();
```

**Supported Field Types**:
- `text`, `email`, `url`
- `number`
- `textarea`
- `select`
- `boolean` (checkbox)
- `date`

### 4. Dynamic Table

**Purpose**: Render data tables with sorting, filtering, and pagination.

**Usage**:
```javascript
import { DynamicTable } from './dynamic-table.js';

const container = document.getElementById('table-container');
const table = new DynamicTable(container, 'companies', metadata);

// Render
await table.render();

// Handle row actions
table.onRowAction = (action, row) => {
  if (action === 'edit') {
    editRecord(row);
  }
};

// Add filter
await table.addFilter('status', 'eq', 'active');

// Clear filters
await table.clearFilters();

// Refresh
await table.refresh();
```

**Features**:
- Sortable columns (click to toggle)
- Pagination
- Action buttons (view, edit, delete)
- Value formatting (date, currency, number)
- Empty state handling

### 5. Entity Manager

**Purpose**: Complete CRUD UI for any entity.

**Usage**:
```javascript
import { EntityManager } from './entity-manager.js';

const container = document.getElementById('content');
const manager = new EntityManager(container, 'companies');

// Initialize and render
await manager.init();
```

**Features**:
- Automatic table rendering
- Create/Edit modal with dynamic form
- Delete confirmation
- Refresh button
- Error handling
- Loading states

### 6. Audit Widget

**Purpose**: Display audit trail with filters.

**Usage**:
```javascript
import { AuditWidget } from './audit-widget.js';

const container = document.getElementById('audit-container');

// Show all audit logs
const widget = new AuditWidget(container, {
  showFilters: true,
  pageSize: 20
});

// Show logs for specific entity
const widget = new AuditWidget(container, {
  entityType: 'companies',
  entityId: '123-456-789'
});

await widget.render();
```

**Features**:
- Timeline visualization
- Action filters
- Status filters
- Before/after diff display
- Relative timestamps
- Pagination

## 🎨 User Interface Components

### Settings Page

**Features**:
- User preferences (theme, language, timezone, density)
- Tenant settings (branding, colors, logo)
- Live preview
- Admin-only tenant settings
- Immediate theme application

**Access**: Navigate to `#settings` or click Settings in menu

### Audit Trail Page

**Features**:
- System-wide audit logs
- Action and status filters
- Timeline view with color coding
- Expandable change details
- Pagination

**Access**: Navigate to `#audit` or click Audit Trail in menu

### Generic Entity Pages

**Features**:
- Auto-generated from metadata
- Full CRUD operations
- Dynamic forms
- Sortable tables
- Responsive design

**Access**: Navigate to `#companies`, `#branches`, or `#departments`

## 🔧 Configuration

### Menu Configuration

Update `frontend/config/menu.json`:

```json
{
  "items": [
    { "title": "Dashboard", "route": "dashboard" },
    { "title": "Companies", "route": "companies" },
    { "title": "Branches", "route": "branches" },
    { "title": "Departments", "route": "departments" },
    { "title": "Audit Trail", "route": "audit" },
    { "title": "Settings", "route": "settings" }
  ]
}
```

### API Base URL

Update in `frontend/assets/js/api.js`:

```javascript
const API_BASE = 'http://localhost:8000/api';
```

## 📱 Responsive Design

All components are fully responsive using Bootstrap 5:
- Mobile-first design
- Collapsible sidebar (planned)
- Touch-friendly buttons
- Scrollable tables
- Adaptive forms

## 🎯 Adding a New Entity Page

To add a new entity (e.g., "products"):

### 1. Create Metadata (Backend)
```python
# In seed_metadata.py
PRODUCT_METADATA = {
  "entity_name": "products",
  "display_name": "Products",
  ...
}
```

### 2. Add to Menu
```json
{
  "title": "Products",
  "route": "products"
}
```

### 3. Register Route Handler
```javascript
// In generic-entity-page.js
const entityRoutes = ['companies', 'branches', 'departments', 'products'];
```

That's it! The page will automatically:
- Load metadata
- Render table with columns from metadata
- Generate form from metadata
- Handle CRUD operations
- Log to audit trail

## 🧪 Testing Frontend Features

### Test Metadata Service
```javascript
// Open browser console
import { metadataService } from './assets/js/metadata-service.js';
const metadata = await metadataService.getMetadata('companies');
console.log(metadata);
```

### Test Data Service
```javascript
import { dataService } from './assets/js/data-service.js';
const data = await dataService.list('companies', { page: 1, pageSize: 10 });
console.log(data);
```

### Test Dynamic Form
1. Navigate to Companies page
2. Click "Add Company"
3. Form renders from metadata
4. Fill and submit
5. Check audit logs

### Test Audit Widget
1. Navigate to Audit Trail
2. Apply filters
3. Expand change details
4. Check pagination

### Test Settings
1. Navigate to Settings
2. Change theme to Dark
3. Theme applies immediately
4. Check persistence (reload page)

## 🎨 Customization

### Custom Field Widgets

Add custom widget types in `dynamic-form.js`:

```javascript
case 'custom-widget':
  return this.createCustomWidget(fieldConfig, value);
```

### Custom Table Formatters

Add custom formats in `dynamic-table.js`:

```javascript
case 'custom-format':
  return this.customFormat(value);
```

### Custom Actions

Add custom actions in `entity-manager.js`:

```javascript
handleRowAction(action, row) {
  switch (action) {
    case 'custom-action':
      this.handleCustomAction(row);
      break;
  }
}
```

## 📊 Performance Tips

### Metadata Caching
- Metadata is cached after first fetch
- Clear cache when metadata changes:
  ```javascript
  metadataService.clearCache('companies');
  ```

### Lazy Loading
- Tables paginate automatically
- Forms render on demand
- Audit logs load incrementally

### Debouncing
Add debouncing for search/filter inputs:
```javascript
let debounceTimer;
searchInput.oninput = () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    table.addFilter('name', 'like', searchInput.value);
  }, 300);
};
```

## 🐛 Troubleshooting

### Forms Not Rendering
- Check metadata is loaded: `console.log(metadata)`
- Verify field configs are valid
- Check browser console for errors

### Tables Not Loading
- Check network tab for API responses
- Verify entity name matches backend
- Check authentication token is valid

### Audit Logs Empty
- Perform some CRUD operations first
- Check backend audit system is running
- Verify user has permission to view logs

### Settings Not Saving
- Check network tab for 401/403 errors
- Verify user is authenticated
- Check admin status for tenant settings

## ✅ Verification Checklist

After setup, verify:

- [ ] Can login successfully
- [ ] Menu loads all items
- [ ] Companies page renders with data
- [ ] Can create a new company
- [ ] Can edit existing company
- [ ] Can delete company
- [ ] Branches page works
- [ ] Departments page works
- [ ] Audit trail shows operations
- [ ] Can filter audit logs
- [ ] Settings page loads
- [ ] Can change theme
- [ ] Theme persists after reload
- [ ] Tenant settings visible (admin)
- [ ] Can update tenant branding

## 🚀 Next Steps

- Add real-time updates (WebSocket)
- Implement advanced filters UI
- Add bulk edit interface
- Create dashboard with charts
- Add export functionality
- Implement drag-drop file upload
- Add keyboard shortcuts
- Create mobile app wrapper

## 🎉 Summary

Your frontend now has:

- ✅ Metadata-driven UI components
- ✅ Generic entity management
- ✅ Dynamic forms and tables
- ✅ Complete audit trail
- ✅ User settings and preferences
- ✅ Tenant branding
- ✅ Responsive design
- ✅ Auto-refresh tokens
- ✅ Error handling

**Your NoCode platform frontend is complete! 🎊**