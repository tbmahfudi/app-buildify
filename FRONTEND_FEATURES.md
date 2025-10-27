# Frontend Features Documentation

## Overview

This document describes the comprehensive frontend features implemented for the multi-tenant, RBAC-enabled application. All features integrate with the backend multi-tenant architecture and role-based access control system.

## Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [User Management](#user-management)
3. [RBAC System](#rbac-system)
4. [Multi-Tenant Support](#multi-tenant-support)
5. [Audit Trail](#audit-trail)
6. [Dynamic Forms & Tables](#dynamic-forms--tables)
7. [Organization Management](#organization-management)
8. [Settings](#settings)

---

## Authentication & Authorization

### Features

- **JWT Token Management**: Automatic token refresh on expiration
- **Secure Storage**: Tokens stored with automatic cleanup
- **Session Validation**: Validates user session on app initialization
- **Login Page**: Clean, modern login interface with tenant selection

### Implementation

- **Files**: `frontend/assets/js/api.js`, `frontend/assets/templates/login.html`
- **Key Functions**:
  - `login(email, password, tenant)` - Authenticates user
  - `apiFetch(path, options)` - Handles authenticated API requests with auto-refresh
  - `logout()` - Clears session and redirects to login

### Usage

```javascript
import { apiFetch, login, logout } from './api.js';

// Login
await login('user@example.com', 'password', 'tenant-id');

// Make authenticated request
const response = await apiFetch('/api/data/users/list', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ page: 1, page_size: 25 })
});
```

---

## User Management

### Features

- **User CRUD Operations**: Create, read, update, and delete users
- **Role Assignment**: Assign multiple roles to users (admin, user, viewer, manager)
- **Status Management**: Activate/deactivate user accounts
- **Superuser Flag**: Grant unrestricted access to specific users
- **Advanced Filtering**: Filter by role, status, email
- **Pagination**: Navigate through large user lists
- **Search**: Real-time search by email and name

### Implementation

- **Files**:
  - `frontend/assets/templates/users.html`
  - `frontend/assets/js/users.js`
- **Route**: `#users` (Admin only)

### Features Breakdown

#### User List View
- Displays all users with their roles and status
- Visual indicators for active/inactive users
- Superuser badge for elevated accounts
- Sortable and filterable columns

#### User Form
- Email (required, validated)
- Password (required for new users, optional for edits)
- Full Name
- Phone Number
- Role Selection (checkbox grid):
  - Admin - Full system access
  - User - Standard user access
  - Viewer - Read-only access
  - Manager - Team management
- Active Status Toggle
- Superuser Toggle (admin only)

#### Permissions
- View: All authenticated users
- Create/Edit/Delete: Admin role only
- Superuser toggle: Admin role only

---

## RBAC System

### Overview

Comprehensive Role-Based Access Control system that enforces permissions at multiple levels:
- **Route Level**: Hide menu items based on user roles
- **UI Element Level**: Show/hide buttons, forms, and sections
- **Field Level**: Control visibility and editability of individual form fields
- **API Level**: Backend enforces all permissions (frontend is complementary)

### Implementation

- **File**: `frontend/assets/js/rbac.js`

### Key Functions

#### Role Checking

```javascript
import { hasRole, hasAnyRole, hasAllRoles, isSuperuser } from './rbac.js';

// Check single role
if (hasRole('admin')) {
  // User has admin role
}

// Check multiple roles (OR)
if (hasAnyRole(['admin', 'manager'])) {
  // User has admin OR manager role
}

// Check multiple roles (AND)
if (hasAllRoles(['admin', 'superuser'])) {
  // User has both admin AND superuser
}

// Check superuser
if (isSuperuser()) {
  // User is a superuser
}
```

#### Permission Checking

```javascript
import { can } from './rbac.js';

// Check permission (format: resource:action)
if (can('users:create')) {
  // User can create users
}

if (can('companies:delete')) {
  // User can delete companies
}
```

#### Field-Level RBAC

```javascript
import { canViewField, canEditField } from './rbac.js';

const fieldMeta = {
  field: 'salary',
  rbac_view: ['admin', 'manager'],
  rbac_edit: ['admin']
};

if (canViewField(fieldMeta)) {
  // Show field
}

if (canEditField(fieldMeta)) {
  // Enable editing
} else {
  // Make read-only
}
```

#### UI Element Control

```javascript
import { showIfHasRole, enableIfHasRole, applyRBACToElements } from './rbac.js';

// Show element only for admins
const deleteButton = document.getElementById('btn-delete');
showIfHasRole(deleteButton, 'admin');

// Enable element only for specific roles
const editButton = document.getElementById('btn-edit');
enableIfHasRole(editButton, ['admin', 'manager']);

// Apply RBAC to all elements with data attributes
applyRBACToElements(document);
```

### HTML Data Attributes

Use data attributes to automatically apply RBAC:

```html
<!-- Show only for admin role -->
<button data-rbac-role="admin">Admin Only</button>

<!-- Show for multiple roles -->
<div data-rbac-role="admin,manager">Admin or Manager</div>

<!-- Show based on permission -->
<button data-rbac-permission="users:delete">Delete User</button>
```

### Menu Filtering

The menu system automatically filters items based on user roles:

```json
{
  "items": [
    {
      "title": "User Management",
      "route": "users",
      "icon": "bi-people-fill",
      "roles": ["admin"]
    }
  ]
}
```

---

## Multi-Tenant Support

### Features

- **Tenant Isolation**: All data is scoped to the user's tenant
- **Tenant Header**: `X-Tenant-Id` header automatically added to all API requests
- **Tenant Switcher**: UI component for superusers to switch tenants (placeholder in navbar)
- **Tenant Info Display**: Shows current tenant in user dropdown

### Implementation

- **Files**:
  - `frontend/assets/js/api.js` (setTenant function)
  - `frontend/assets/js/rbac.js` (belongsToTenant function)

### Usage

```javascript
import { setTenant } from './api.js';
import { belongsToTenant, getUserTenantId } from './rbac.js';

// Set current tenant (usually after login)
setTenant('tenant-uuid');

// Check if user belongs to tenant
if (belongsToTenant('tenant-uuid')) {
  // User can access this tenant's data
}

// Get user's tenant ID
const tenantId = getUserTenantId();
```

---

## Audit Trail

### Features

- **Comprehensive Logging**: All CRUD operations, logins, and system events
- **Advanced Filtering**:
  - Action (CREATE, UPDATE, DELETE, LOGIN, LOGOUT)
  - Entity Type (users, companies, branches, departments)
  - Status (success, failure, warning)
  - User Email
  - Date Range (from/to)
  - Full-text search in details
- **Summary Statistics**:
  - Total events
  - Successful events
  - Failed events
  - Unique users
- **Event Details**:
  - Before/After comparison for UPDATE operations
  - IP address and user agent
  - Timestamps with relative time
  - Full JSON diff viewer
- **Pagination**: Navigate through large event logs
- **Real-time Updates**: Refresh to see latest events

### Implementation

- **Files**:
  - `frontend/assets/templates/audit.html`
  - `frontend/assets/js/audit-enhanced.js`
- **Route**: `#audit`

### Event Types

| Action | Description | Icon |
|--------|-------------|------|
| CREATE | New record created | Green plus circle |
| UPDATE | Record modified | Blue pencil |
| DELETE | Record deleted | Red trash |
| LOGIN | User logged in | Purple arrow right |
| LOGOUT | User logged out | Gray arrow left |

### Filters

#### Action Filter
Select specific action types to filter events

#### Entity Type Filter
Filter by data model (users, companies, branches, departments)

#### Status Filter
- Success: Operation completed successfully
- Failure: Operation failed (with error details)
- Warning: Operation completed with warnings

#### User Filter
Search for events by specific user email

#### Date Range
Filter events within a specific time period

#### Search
Full-text search across all event details

---

## Dynamic Forms & Tables

### Dynamic Forms

Automatically generate forms from metadata with RBAC support.

#### Features

- **Auto-generation**: Creates forms from backend metadata
- **Field Types**: text, email, url, number, textarea, select, boolean, date
- **Validation**: HTML5 validation with custom validators
- **RBAC Integration**:
  - Hide fields user cannot view
  - Make fields read-only if user cannot edit
  - Visual indicators (lock icon) for restricted fields
- **Error Handling**: Field-level error messages

#### Implementation

**File**: `frontend/assets/js/dynamic-form.js`

```javascript
import { DynamicForm } from './dynamic-form.js';

// Metadata with RBAC
const metadata = {
  form: {
    fields: [
      {
        field: 'email',
        title: 'Email',
        type: 'email',
        required: true,
        rbac_view: ['admin', 'user'],
        rbac_edit: ['admin']
      },
      {
        field: 'salary',
        title: 'Salary',
        type: 'number',
        rbac_view: ['admin', 'manager'],
        rbac_edit: ['admin']
      }
    ]
  }
};

// Create form
const container = document.getElementById('form-container');
const form = new DynamicForm(container, metadata, existingRecord);
form.render();

// Get values
const values = form.getValues();

// Validate
if (form.validate()) {
  // Submit
}
```

### Dynamic Tables

Display data in sortable, paginated tables.

#### Features

- **Auto-generation**: Creates tables from metadata
- **Sorting**: Click column headers to sort
- **Pagination**: Configurable page size
- **Row Actions**: Edit and Delete buttons
- **Empty State**: Graceful handling of no data
- **Loading States**: Visual feedback during data fetch

#### Implementation

**File**: `frontend/assets/js/dynamic-table.js`

---

## Organization Management

### Features

#### Companies
- **CRUD Operations**: Full create, read, update, delete
- **Unique Codes**: Each company has a unique identifier
- **Search**: Real-time filtering
- **Modern UI**: Tailwind-styled with smooth animations

#### Branches
- **Company Association**: Each branch belongs to a company
- **Optional**: Companies can exist without branches
- **Hierarchical Display**: Shows company relationship

#### Departments
- **Branch Association**: Each department can belong to a branch
- **Optional**: Branches can exist without departments
- **Full Hierarchy**: Company > Branch > Department

### Implementation

- **Files**:
  - Companies: `frontend/assets/templates/companies.html`, `frontend/assets/js/companies.js`
  - Branches: `frontend/assets/templates/branches.html`
  - Departments: `frontend/assets/templates/departments.html`
  - Generic Handler: `frontend/assets/js/generic-entity-page.js`
- **Routes**: `#companies`, `#branches`, `#departments`

### Permissions

- View: All authenticated users
- Create/Edit/Delete: Admin role only

---

## Settings

### Features

#### User Settings
- **Theme**: Light/Dark mode toggle
- **Language**: UI language selection
- **Timezone**: User timezone preference
- **Display Density**: Compact/Normal/Comfortable

#### Tenant Settings (Admin Only)
- **Tenant Name**: Organization name
- **Logo**: Company logo upload (placeholder)
- **Colors**: Primary and secondary brand colors
- **Features**: Toggle feature flags
- **Theme**: Tenant-wide theme settings

### Implementation

- **Files**:
  - `frontend/assets/templates/settings.html`
  - `frontend/assets/js/settings.js`
- **Route**: `#settings`

---

## Architecture & Design Patterns

### Technology Stack

- **Framework**: Vanilla JavaScript (ES6 modules)
- **Styling**: Tailwind CSS (CDN) + Bootstrap 5 (transitioning)
- **Icons**: Bootstrap Icons
- **State Management**: localStorage + window.appState
- **Routing**: Hash-based routing (#route)
- **HTTP Client**: Fetch API with custom wrapper

### Module Structure

```
frontend/
├── assets/
│   ├── js/
│   │   ├── app.js              # Main app initialization
│   │   ├── api.js              # Authentication & API wrapper
│   │   ├── rbac.js             # RBAC utilities
│   │   ├── users.js            # User management
│   │   ├── audit-enhanced.js   # Enhanced audit viewer
│   │   ├── companies.js        # Companies CRUD
│   │   ├── dynamic-form.js     # Form builder
│   │   ├── dynamic-table.js    # Table builder
│   │   ├── ui-utils.js         # Toast, loading, etc.
│   │   ├── settings.js         # Settings management
│   │   └── ...
│   ├── templates/
│   │   ├── main.html           # App shell
│   │   ├── login.html          # Login page
│   │   ├── users.html          # User management
│   │   ├── audit.html          # Audit trail
│   │   └── ...
│   └── css/
│       └── app.css             # Custom styles
├── config/
│   └── menu.json               # Navigation menu
└── index.html                  # Entry point
```

### Design Principles

1. **Modularity**: Each feature is a separate ES6 module
2. **RBAC-First**: All UI components check permissions
3. **Progressive Enhancement**: Graceful degradation for missing features
4. **Responsive**: Mobile-first design with Tailwind
5. **Accessibility**: ARIA labels, keyboard navigation
6. **Performance**: Pagination, lazy loading, optimized rendering

---

## API Integration

### Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/login` | POST | User authentication |
| `/auth/refresh` | POST | Token refresh |
| `/auth/me` | GET | Get current user |
| `/data/users/list` | POST | List users with filters |
| `/data/users` | POST | Create user |
| `/data/users/:id` | GET | Get single user |
| `/data/users/:id` | PUT | Update user |
| `/data/users/:id` | DELETE | Delete user |
| `/org/companies` | GET | List companies |
| `/org/companies` | POST | Create company |
| `/org/companies/:id` | PUT | Update company |
| `/org/companies/:id` | DELETE | Delete company |
| `/audit/list` | POST | List audit events |
| `/audit/summary` | GET | Audit statistics |
| `/settings/user` | GET/PUT | User preferences |
| `/settings/tenant` | GET/PUT | Tenant settings |

### Request Format

```javascript
// Standard list request
{
  filters: [
    { field: 'email', operator: 'like', value: '%@example.com' },
    { field: 'is_active', operator: 'eq', value: true }
  ],
  sort: [['created_at', 'desc']],
  page: 1,
  page_size: 25
}
```

### Filter Operators

- `eq` - Equals
- `ne` - Not equals
- `gt` - Greater than
- `gte` - Greater than or equal
- `lt` - Less than
- `lte` - Less than or equal
- `like` - SQL LIKE (use % wildcards)
- `in` - In array
- `contains` - Array contains value

---

## Future Enhancements

### Planned Features

1. **Real-time Updates**: WebSocket integration for live updates
2. **Advanced Analytics**: Dashboard with charts and graphs
3. **Bulk Operations**: Multi-select and batch actions
4. **Export/Import**: CSV, JSON, Excel export
5. **Activity Feed**: Real-time activity stream
6. **Notifications Center**: In-app notification system
7. **Dark Mode**: Complete dark theme implementation
8. **Keyboard Shortcuts**: Power user shortcuts
9. **Mobile App**: React Native or PWA
10. **Internationalization**: Multi-language support

### Technical Debt

1. **Build System**: Add Vite/Rollup for bundling and optimization
2. **State Management**: Consider Zustand or similar lightweight store
3. **Testing**: Add unit and integration tests
4. **Documentation**: JSDoc comments for all functions
5. **Accessibility**: Full WCAG AA compliance
6. **Performance**: Implement virtual scrolling for large lists

---

## Contributing

### Code Style

- Use ES6+ features (modules, arrow functions, async/await)
- Follow existing naming conventions (camelCase for variables/functions)
- Add JSDoc comments for public functions
- Keep functions small and focused (single responsibility)
- Use const/let, never var

### Adding New Features

1. Create HTML template in `frontend/assets/templates/`
2. Create JavaScript module in `frontend/assets/js/`
3. Add route to menu in `frontend/config/menu.json`
4. Import module in `frontend/assets/templates/main.html`
5. Apply RBAC using `data-rbac-role` or `applyRBACToElements()`
6. Test with different user roles
7. Update this documentation

### Testing Checklist

- [ ] Test with admin role
- [ ] Test with user role
- [ ] Test with viewer role
- [ ] Test with no roles
- [ ] Test RBAC field visibility
- [ ] Test RBAC field editability
- [ ] Test pagination
- [ ] Test search/filters
- [ ] Test error handling
- [ ] Test responsive design (mobile, tablet, desktop)

---

## Support

For issues, questions, or feature requests, please refer to the backend documentation or create an issue in the project repository.

---

**Version**: 1.0.0
**Last Updated**: 2024-10-27
**Author**: Claude (Anthropic)
