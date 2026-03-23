# Practical Guide: Displaying Lookup Fields (Tenant Name from tenant_id)

## Your Problem

You have company data like this:
```json
{
  "id": "e634fe9d-7673-4c2b-bb1d-b43e8bae9cbe",
  "tenant_id": "4ff4a3fa-33c2-474f-b264-987d047e4502",
  "code": "CLOUDWORK",
  "name": "CloudWork Solutions"
}
```

**You want to display**: Tenant name (e.g., "Acme Corporation")
**Not**: `tenant_id` (UUID)
**Without**: Making additional API calls

## Solution: Modify Backend to Return Joined Data

The solution is to have your backend API use **SQL JOIN** to include tenant fields in the response.

---

## Step-by-Step Implementation

### Step 1: Update the Response Schema

**File**: `backend/app/schemas/org.py`

**Add new response schema with tenant info**:

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

# Add this new schema for tenant info
class TenantInfo(BaseModel):
    """Tenant information for lookup"""
    id: str
    name: str
    code: str

    model_config = ConfigDict(from_attributes=True)

# Update CompanyResponse to include tenant info
class CompanyResponseWithTenant(BaseModel):
    """Company response with tenant information"""
    id: str = Field(..., description="Company unique identifier")
    tenant_id: str = Field(..., description="Tenant ID")
    code: str = Field(..., max_length=32, description="Company code")
    name: str = Field(..., max_length=255, description="Company name")
    description: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None
    registration_number: Optional[str] = None
    is_active: bool = True
    extra_data: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    # Lookup fields from tenant table
    tenant_name: Optional[str] = Field(None, description="Tenant name (from join)")
    tenant_code: Optional[str] = Field(None, description="Tenant code (from join)")

    model_config = ConfigDict(from_attributes=True)

# Update list response
class CompanyListResponseWithTenant(BaseModel):
    """Company list response with tenant info"""
    items: List[CompanyResponseWithTenant]
    total: int
```

### Step 2: Update the API Endpoint with JOIN

**File**: `backend/app/routers/org.py`

**Modify the list_companies endpoint**:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
import uuid

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.company import Company
from app.models.tenant import Tenant
from app.schemas.org import (
    CompanyCreate, CompanyUpdate, CompanyResponse,
    CompanyResponseWithTenant, CompanyListResponseWithTenant
)

router = APIRouter(prefix="/org", tags=["org"])

@router.get("/companies", response_model=CompanyListResponseWithTenant)
def list_companies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all companies with tenant information"""

    # Query with LEFT JOIN to get tenant info
    query = (
        db.query(
            Company,
            Tenant.name.label('tenant_name'),
            Tenant.code.label('tenant_code')
        )
        .outerjoin(Tenant, Company.tenant_id == Tenant.id)
    )

    # Count total
    total = query.count()

    # Get paginated results
    results = query.offset(skip).limit(limit).all()

    # Transform results to include tenant info
    items = []
    for company, tenant_name, tenant_code in results:
        company_dict = {
            "id": str(company.id),
            "tenant_id": str(company.tenant_id),
            "code": company.code,
            "name": company.name,
            "description": company.description,
            "email": company.email,
            "phone": company.phone,
            "website": company.website,
            "address_line1": company.address_line1,
            "address_line2": company.address_line2,
            "city": company.city,
            "state": company.state,
            "postal_code": company.postal_code,
            "country": company.country,
            "tax_id": company.tax_id,
            "registration_number": company.registration_number,
            "is_active": company.is_active,
            "extra_data": company.extra_data,
            "created_at": company.created_at,
            "updated_at": company.updated_at,
            "deleted_at": company.deleted_at,
            # Lookup fields from tenant
            "tenant_name": tenant_name,
            "tenant_code": tenant_code
        }
        items.append(company_dict)

    return CompanyListResponseWithTenant(items=items, total=total)
```

### Step 3: Frontend Display

**File**: `frontend/assets/js/companies.js`

**Now you can display tenant name directly**:

```javascript
function renderCompanies(companies) {
  const tbody = document.querySelector('#companies-table tbody');
  if (!tbody) return;

  tbody.innerHTML = '';

  if (!companies.length) {
    tbody.innerHTML = renderEmptyState();
    return;
  }

  companies.forEach((company) => {
    const row = document.createElement('tr');
    row.className = 'border-b border-gray-200 hover:bg-gray-50 transition';

    // Company Code
    const codeCell = document.createElement('td');
    codeCell.className = 'px-6 py-4 text-sm font-medium text-gray-900';
    codeCell.textContent = company.code;

    // Company Name
    const nameCell = document.createElement('td');
    nameCell.className = 'px-6 py-4 text-sm text-gray-600';
    nameCell.textContent = company.name;

    // Tenant Name (from lookup - no additional API call needed!)
    const tenantCell = document.createElement('td');
    tenantCell.className = 'px-6 py-4 text-sm text-gray-600';
    tenantCell.innerHTML = company.tenant_name
      ? `<span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">${company.tenant_name}</span>`
      : '<span class="text-gray-400">No Tenant</span>';

    // Created Date
    const dateCell = document.createElement('td');
    dateCell.className = 'px-6 py-4 text-sm text-gray-600';
    dateCell.textContent = formatDate(company.created_at);

    // Actions
    const actionsCell = document.createElement('td');
    actionsCell.className = 'px-6 py-4 text-sm flex gap-2';

    const editBtn = document.createElement('button');
    editBtn.className = 'edit-btn px-3 py-1 text-blue-600 border border-blue-600 rounded hover:bg-blue-50 transition text-sm';
    editBtn.setAttribute('data-company-id', company.id);
    editBtn.innerHTML = '<i class="bi bi-pencil-square"></i> Edit';

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'delete-btn px-3 py-1 text-red-600 border border-red-600 rounded hover:bg-red-50 transition text-sm';
    deleteBtn.setAttribute('data-company-id', company.id);
    deleteBtn.innerHTML = '<i class="bi bi-trash"></i> Delete';

    actionsCell.appendChild(editBtn);
    actionsCell.appendChild(deleteBtn);

    row.appendChild(codeCell);
    row.appendChild(nameCell);
    row.appendChild(tenantCell);  // ← Tenant name displayed here!
    row.appendChild(dateCell);
    row.appendChild(actionsCell);

    tbody.appendChild(row);
  });

  // Wire up event handlers
  tbody.querySelectorAll('.edit-btn').forEach((button) => {
    button.addEventListener('click', () => editCompany(button.dataset.companyId));
  });

  tbody.querySelectorAll('.delete-btn').forEach((button) => {
    button.addEventListener('click', () => deleteCompany(button.dataset.companyId));
  });
}
```

### Step 4: Update HTML Template (if needed)

**File**: `frontend/assets/templates/companies.html`

**Add tenant column to table header**:

```html
<table id="companies-table" class="w-full">
  <thead>
    <tr class="border-b border-gray-200 bg-gray-50">
      <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
        Code
      </th>
      <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
        Name
      </th>
      <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
        Tenant
      </th>
      <th class="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
        Created
      </th>
      <th class="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">
        Actions
      </th>
    </tr>
  </thead>
  <tbody>
    <!-- Rows will be inserted here -->
  </tbody>
</table>
```

---

## Alternative: Using SQLAlchemy Relationships (Cleaner)

If you prefer using SQLAlchemy relationships instead of manual JOIN:

### Option A: Load with joinedload

```python
from sqlalchemy.orm import joinedload

@router.get("/companies", response_model=CompanyListResponseWithTenant)
def list_companies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all companies with tenant information"""

    # Query with eager loading of tenant relationship
    query = db.query(Company).options(joinedload(Company.tenant))

    total = query.count()
    companies = query.offset(skip).limit(limit).all()

    # Transform to include tenant info
    items = []
    for company in companies:
        company_dict = {
            **company.__dict__,
            "tenant_name": company.tenant.name if company.tenant else None,
            "tenant_code": company.tenant.code if company.tenant else None
        }
        items.append(company_dict)

    return CompanyListResponseWithTenant(items=items, total=total)
```

### Option B: Using Pydantic with from_orm

```python
from pydantic import computed_field

class CompanyResponseWithTenant(BaseModel):
    """Company response with computed tenant fields"""
    id: str
    tenant_id: str
    code: str
    name: str
    # ... other fields ...

    # Computed fields from relationship
    @computed_field
    @property
    def tenant_name(self) -> Optional[str]:
        """Get tenant name from relationship"""
        # This works if you use joinedload
        return getattr(self, '_tenant_name', None)

    @computed_field
    @property
    def tenant_code(self) -> Optional[str]:
        """Get tenant code from relationship"""
        return getattr(self, '_tenant_code', None)

    model_config = ConfigDict(from_attributes=True)
```

---

## API Response Example

**Before** (without lookup):
```json
{
  "items": [
    {
      "id": "e634fe9d-7673-4c2b-bb1d-b43e8bae9cbe",
      "tenant_id": "4ff4a3fa-33c2-474f-b264-987d047e4502",
      "code": "CLOUDWORK",
      "name": "CloudWork Solutions"
    }
  ],
  "total": 1
}
```

**After** (with lookup):
```json
{
  "items": [
    {
      "id": "e634fe9d-7673-4c2b-bb1d-b43e8bae9cbe",
      "tenant_id": "4ff4a3fa-33c2-474f-b264-987d047e4502",
      "code": "CLOUDWORK",
      "name": "CloudWork Solutions",
      "tenant_name": "Acme Corporation",
      "tenant_code": "ACME"
    }
  ],
  "total": 1
}
```

---

## Multiple Lookup Fields Example

If you need to show multiple related tables (e.g., tenant AND branch):

```python
@router.get("/users", response_model=UserListResponse)
def list_users(db: Session = Depends(get_db)):
    """List users with multiple lookups"""

    query = (
        db.query(
            User,
            Tenant.name.label('tenant_name'),
            Company.name.label('company_name'),
            Branch.name.label('branch_name'),
            Department.name.label('department_name')
        )
        .outerjoin(Tenant, User.tenant_id == Tenant.id)
        .outerjoin(Company, User.default_company_id == Company.id)
        .outerjoin(Branch, User.branch_id == Branch.id)
        .outerjoin(Department, User.department_id == Department.id)
    )

    results = query.all()

    items = []
    for user, tenant_name, company_name, branch_name, dept_name in results:
        user_dict = {
            **user.__dict__,
            "tenant_name": tenant_name,
            "company_name": company_name,
            "branch_name": branch_name,
            "department_name": dept_name
        }
        items.append(user_dict)

    return {"items": items, "total": len(items)}
```

---

## Performance Considerations

### 1. Add Database Indexes

```python
# In your model
class Company(Base):
    __tablename__ = "companies"

    # Add index on foreign key for faster joins
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False, index=True)
```

### 2. Use LIMIT for Large Datasets

```python
# Always use pagination for large datasets
results = query.offset(skip).limit(limit).all()
```

### 3. Consider Caching for Frequently Accessed Lookups

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_tenant_name(tenant_id: str, db: Session) -> str:
    """Cache tenant names to avoid repeated queries"""
    tenant = db.query(Tenant.name).filter(Tenant.id == tenant_id).first()
    return tenant.name if tenant else "Unknown"
```

---

## Testing Your Changes

### 1. Test the API Endpoint

```bash
# Test with curl
curl -X GET "http://localhost:8000/org/companies" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected response**:
```json
{
  "items": [
    {
      "id": "...",
      "tenant_id": "...",
      "code": "CLOUDWORK",
      "name": "CloudWork Solutions",
      "tenant_name": "Acme Corporation",
      "tenant_code": "ACME",
      ...
    }
  ],
  "total": 1
}
```

### 2. Test in Frontend

```javascript
// In browser console
async function testCompaniesAPI() {
  const res = await fetch('/org/companies');
  const data = await res.json();
  console.log('First company:', data.items[0]);
  console.log('Tenant name:', data.items[0].tenant_name); // Should show tenant name
}

testCompaniesAPI();
```

---

## Summary

### What You Changed:

1. **Backend Schema** - Added `tenant_name` and `tenant_code` fields to response
2. **Backend Router** - Used SQL JOIN to include tenant data in query
3. **Frontend** - Display `tenant_name` directly from API response

### Benefits:

✅ **Single API Call** - No additional requests needed
✅ **Better Performance** - Database handles JOIN efficiently
✅ **Cleaner Code** - No frontend mapping logic required
✅ **Type Safety** - Pydantic validates response structure

### Next Steps:

1. Apply this pattern to other entities (users, branches, departments)
2. Add indexes on all foreign keys
3. Consider implementing a base service class for common lookup patterns
4. Add caching for frequently accessed lookup data

---

## Common Mistakes to Avoid

### ❌ Don't do this:
```javascript
// Making separate API call for each company's tenant
companies.forEach(async (company) => {
  const tenant = await fetch(`/tenants/${company.tenant_id}`);
  // This creates N+1 query problem!
});
```

### ✅ Do this:
```python
# Include tenant data in the initial query
query = db.query(Company, Tenant.name).join(Tenant)
```

---

## Need More Fields from Tenant?

Just add them to the query:

```python
query = (
    db.query(
        Company,
        Tenant.name.label('tenant_name'),
        Tenant.code.label('tenant_code'),
        Tenant.subscription_tier.label('tenant_tier'),  # ← Add more fields
        Tenant.is_active.label('tenant_is_active')      # ← Add more fields
    )
    .outerjoin(Tenant, Company.tenant_id == Tenant.id)
)
```

And update the schema:

```python
class CompanyResponseWithTenant(BaseModel):
    # ... existing fields ...
    tenant_name: Optional[str] = None
    tenant_code: Optional[str] = None
    tenant_tier: Optional[str] = None           # ← Add to schema
    tenant_is_active: Optional[bool] = None     # ← Add to schema
```
