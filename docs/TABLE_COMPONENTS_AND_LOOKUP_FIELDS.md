# Table Components and Displaying Lookup Table Fields

## Overview

This guide explains the table components available in the app and how to display fields from lookup/related tables (foreign key relationships).

---

## Table Components Available

### 1. **DynamicTable** Component (Recommended)

Located at: `frontend/assets/js/dynamic-table.js`

**Best for**: Metadata-driven tables with automatic rendering

**Features**:
- Automatic table generation from metadata
- Built-in pagination
- Sorting support
- Filter support
- Action buttons (view, edit, delete)
- Responsive layout

**Usage**:
```javascript
import { DynamicTable } from './dynamic-table.js';

const table = new DynamicTable(
  document.getElementById('table-container'),
  'users',  // entity name
  metadata  // metadata object
);

await table.render();
```

### 2. **EntityManager** Component (Full CRUD)

Located at: `frontend/assets/js/entity-manager.js`

**Best for**: Complete CRUD interfaces with table + form

**Features**:
- Uses DynamicTable internally
- Automatic form generation (DynamicForm)
- Modal dialogs for create/edit
- Full CRUD operations

**Usage**:
```javascript
import { EntityManager } from './entity-manager.js';

const manager = new EntityManager(container, 'companies');
await manager.init();
```

### 3. **Manual Table Rendering** (Most Flexible)

**Best for**: Custom table layouts with specific requirements

**Example** (from `users.js:102-178`):
```javascript
function renderUsers(items) {
  const tbody = document.getElementById('users-tbody');

  tbody.innerHTML = items.map(user => `
    <tr>
      <td>${escapeHtml(user.email)}</td>
      <td>${escapeHtml(user.role)}</td>
      <td>
        <button onclick="editUser('${user.id}')">Edit</button>
      </td>
    </tr>
  `).join('');
}
```

---

## Displaying Lookup Table Fields

When you have a foreign key relationship (e.g., `user.company_id` → `companies.name`), you need to show the related table's data, not just the ID.

### Method 1: Backend API Returns Joined Data (Recommended)

**How it works**: The backend API performs a SQL JOIN and returns the lookup field in the response.

**Backend Example**:
```python
# In your data service endpoint
SELECT
    users.id,
    users.email,
    users.company_id,
    companies.name AS company_name  # Include lookup field
FROM users
LEFT JOIN companies ON users.company_id = companies.id
```

**Response Structure**:
```json
{
  "items": [
    {
      "id": "123",
      "email": "user@example.com",
      "company_id": "abc",
      "company_name": "Acme Corp"  ← Lookup field
    }
  ]
}
```

**Frontend Usage**:
```javascript
// In your table column configuration
{
  "field": "company_name",  // Use the joined field
  "title": "Company"
}

// Or manually in renderRow:
tbody.innerHTML = items.map(user => `
  <tr>
    <td>${user.email}</td>
    <td>${user.company_name || 'N/A'}</td>  ← Display lookup field
  </tr>
`).join('');
```

### Method 2: Frontend Fetches Lookup Data

**How it works**: Frontend loads lookup table data separately and maps it to display values.

**Implementation**:
```javascript
// Step 1: Load users and companies
async function loadUsersWithCompanies() {
  const [usersRes, companiesRes] = await Promise.all([
    apiFetch('/data/users/list'),
    apiFetch('/data/companies')
  ]);

  const users = await usersRes.json();
  const companies = await companiesRes.json();

  // Step 2: Create lookup map
  const companyMap = {};
  companies.items.forEach(c => {
    companyMap[c.id] = c.name;
  });

  // Step 3: Render with lookup values
  renderUsersWithLookup(users.items, companyMap);
}

function renderUsersWithLookup(users, companyMap) {
  tbody.innerHTML = users.map(user => `
    <tr>
      <td>${user.email}</td>
      <td>${companyMap[user.company_id] || 'Unknown'}</td>
    </tr>
  `).join('');
}
```

### Method 3: Dynamic Lookup Using DynamicTable

**Metadata Configuration**:

Create a metadata file for your entity with lookup field definitions:

```json
{
  "entity": "users",
  "display_name": "Users",
  "table": {
    "columns": [
      {
        "field": "email",
        "title": "Email",
        "sortable": true
      },
      {
        "field": "company_name",
        "title": "Company",
        "sortable": true,
        "lookup": {
          "table": "companies",
          "key": "company_id",
          "display": "name"
        }
      }
    ],
    "page_size": 25,
    "default_sort": [["email", "asc"]],
    "actions": ["view", "edit", "delete"]
  }
}
```

**Enhanced DynamicTable** (you need to extend it):

```javascript
// In dynamic-table.js, modify formatValue method
formatValue(value, column, row) {
  if (value === null || value === undefined) return '';

  // Handle lookup fields
  if (column.lookup) {
    const lookupKey = row[column.lookup.key];
    return this.lookupCache[column.lookup.table]?.[lookupKey] || value;
  }

  switch (column.format) {
    case 'date':
      return new Date(value).toLocaleDateString();
    case 'datetime':
      return new Date(value).toLocaleString();
    default:
      return value;
  }
}

// Add method to load lookup data
async loadLookupData(column) {
  const { table, key, display } = column.lookup;
  const res = await apiFetch(`/data/${table}`);
  const data = await res.json();

  this.lookupCache[table] = {};
  data.items.forEach(item => {
    this.lookupCache[table][item.id] = item[display];
  });
}
```

---

## Complete Example: Users Table with Company Lookup

### Backend Approach (Recommended)

**API Endpoint** (`/data/users/list`):
```python
@router.post("/data/users/list")
async def list_users(request: ListRequest):
    query = (
        select(User, Company.name.label('company_name'))
        .outerjoin(Company, User.company_id == Company.id)
    )

    results = await db.execute(query)
    items = []
    for row in results:
        user_dict = {
            "id": str(row.User.id),
            "email": row.User.email,
            "company_id": str(row.User.company_id) if row.User.company_id else None,
            "company_name": row.company_name  # ← Lookup field
        }
        items.append(user_dict)

    return {"items": items, "total": len(items)}
```

**Frontend** (`users.js`):
```javascript
function renderUsers(items) {
  const tbody = document.getElementById('users-tbody');

  tbody.innerHTML = items.map(user => `
    <tr>
      <td>
        <div class="flex items-center">
          <i class="bi bi-person-fill text-blue-600"></i>
          <span>${escapeHtml(user.email)}</span>
        </div>
      </td>
      <td>
        <!-- Display lookup field from joined data -->
        <span class="badge bg-primary">
          ${escapeHtml(user.company_name || 'No Company')}
        </span>
      </td>
      <td>${formatDate(user.created_at)}</td>
      <td>
        <button onclick="editUser('${user.id}')">Edit</button>
      </td>
    </tr>
  `).join('');
}
```

### Frontend-Only Approach

```javascript
class UsersPage {
  constructor() {
    this.users = [];
    this.companies = {};
  }

  async init() {
    await this.loadData();
    this.render();
  }

  async loadData() {
    // Load both entities
    const [usersRes, companiesRes] = await Promise.all([
      apiFetch('/data/users/list'),
      apiFetch('/org/companies')
    ]);

    const usersData = await usersRes.json();
    const companiesData = await companiesRes.json();

    this.users = usersData.items;

    // Build lookup map
    companiesData.items.forEach(company => {
      this.companies[company.id] = company.name;
    });
  }

  render() {
    const tbody = document.getElementById('users-tbody');

    tbody.innerHTML = this.users.map(user => `
      <tr>
        <td>${user.email}</td>
        <td>
          ${this.getCompanyName(user.company_id)}
        </td>
        <td>
          <button onclick="window.usersPage.edit('${user.id}')">
            Edit
          </button>
        </td>
      </tr>
    `).join('');
  }

  getCompanyName(companyId) {
    if (!companyId) return '<span class="text-gray-400">No Company</span>';
    return this.companies[companyId] || '<span class="text-red-400">Unknown</span>';
  }

  edit(userId) {
    // Edit logic
  }
}

// Initialize
window.usersPage = new UsersPage();
document.addEventListener('route:loaded', (e) => {
  if (e.detail.route === 'users') {
    window.usersPage.init();
  }
});
```

---

## Best Practices

### 1. **Choose the Right Approach**

| Scenario | Recommended Method |
|----------|-------------------|
| Small lookup tables (<100 records) | Frontend-only approach |
| Large lookup tables (>1000 records) | Backend JOIN approach |
| Multiple lookup fields | Backend JOIN approach |
| Real-time data updates | Backend JOIN approach |

### 2. **Performance Optimization**

**Backend JOIN**:
```python
# Use indexes on foreign keys
class User(Base):
    company_id = Column(GUID, ForeignKey("companies.id"), index=True)
```

**Frontend Caching**:
```javascript
class LookupCache {
  constructor() {
    this.cache = {};
    this.ttl = 5 * 60 * 1000; // 5 minutes
  }

  async get(table, id) {
    const key = `${table}:${id}`;
    const cached = this.cache[key];

    if (cached && Date.now() - cached.timestamp < this.ttl) {
      return cached.value;
    }

    const value = await this.fetch(table, id);
    this.cache[key] = { value, timestamp: Date.now() };
    return value;
  }

  async fetch(table, id) {
    const res = await apiFetch(`/data/${table}/${id}`);
    return await res.json();
  }
}
```

### 3. **Handle Missing Data Gracefully**

```javascript
function displayLookupValue(value, fallback = 'N/A') {
  if (!value || value === null) {
    return `<span class="text-gray-400">${fallback}</span>`;
  }
  return escapeHtml(value);
}

// Usage
tbody.innerHTML = items.map(user => `
  <tr>
    <td>${displayLookupValue(user.company_name, 'No Company')}</td>
  </tr>
`).join('');
```

### 4. **Use Proper Data Types**

```javascript
// ✅ Good: Use objects for clarity
const lookup = {
  table: 'companies',
  key: 'company_id',
  display: 'name'
};

// ❌ Bad: Hardcoded strings
const companyName = row['company_name'];
```

---

## Common Patterns

### Multiple Lookups in One Table

```javascript
function renderEmployees(items, lookupData) {
  const { companies, departments, positions } = lookupData;

  tbody.innerHTML = items.map(emp => `
    <tr>
      <td>${emp.name}</td>
      <td>${companies[emp.company_id]?.name || 'N/A'}</td>
      <td>${departments[emp.department_id]?.name || 'N/A'}</td>
      <td>${positions[emp.position_id]?.title || 'N/A'}</td>
    </tr>
  `).join('');
}
```

### Nested Lookups

```javascript
// User → Department → Company
function renderUsersWithNestedLookup(users, departments, companies) {
  tbody.innerHTML = users.map(user => {
    const dept = departments[user.department_id];
    const company = dept ? companies[dept.company_id] : null;

    return `
      <tr>
        <td>${user.name}</td>
        <td>${dept?.name || 'N/A'}</td>
        <td>${company?.name || 'N/A'}</td>
      </tr>
    `;
  }).join('');
}
```

---

## Troubleshooting

### Issue: Lookup Values Not Showing

**Check**:
1. Is the lookup field included in the API response?
2. Is the field name spelled correctly?
3. Is the data null/undefined?

**Debug**:
```javascript
console.log('API Response:', await res.json());
console.log('Row data:', row);
console.log('Lookup value:', row.company_name);
```

### Issue: Performance Problems with Large Tables

**Solution**: Implement server-side pagination and JOIN:
```python
@router.post("/data/users/list")
async def list_users(request: ListRequest):
    # Paginate
    offset = (request.page - 1) * request.page_size

    query = (
        select(User, Company.name.label('company_name'))
        .outerjoin(Company)
        .offset(offset)
        .limit(request.page_size)
    )
```

---

## Summary

**For displaying lookup table fields:**

1. **Backend JOIN** (Recommended) - Best performance, cleaner code
2. **Frontend Lookup** - Good for small datasets, more flexible
3. **DynamicTable with Metadata** - Best for standardized interfaces

**Key Files**:
- `frontend/assets/js/dynamic-table.js` - Reusable table component
- `frontend/assets/js/entity-manager.js` - Full CRUD with table
- `frontend/assets/js/users.js` - Example of manual table rendering

**Next Steps**:
- Choose your approach based on data size and requirements
- Implement proper error handling for missing lookup data
- Add caching for frequently accessed lookup tables
- Consider using the DynamicTable component for consistency
