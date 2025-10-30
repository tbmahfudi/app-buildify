# Module Development Guide

Complete guide for developing pluggable modules for the platform.

## Table of Contents

- [Overview](#overview)
- [Module Architecture](#module-architecture)
- [Quick Start](#quick-start)
- [Backend Development](#backend-development)
- [Frontend Development](#frontend-development)
- [Permissions & RBAC](#permissions--rbac)
- [Configuration](#configuration)
- [Lifecycle Hooks](#lifecycle-hooks)
- [Best Practices](#best-practices)
- [Examples](#examples)

---

## Overview

The platform supports pluggable modules that can be installed, enabled, and disabled independently. Each module consists of:

- **Backend**: FastAPI routers, models, services, and business logic
- **Frontend**: Pages, components, and UI
- **Permissions**: RBAC integration
- **Configuration**: Per-tenant settings

### Key Features

- ✅ Hot-loading without server restart
- ✅ Per-tenant enable/disable
- ✅ Complete RBAC integration
- ✅ Dependency management
- ✅ Subscription tier requirements
- ✅ Lifecycle hooks for customization
- ✅ Database migrations

---

## Module Architecture

### Directory Structure

```
/backend/modules/{module-name}/
├── module.py              # Module class definition
├── manifest.json          # Module metadata
├── permissions.py         # Permission definitions
├── models/                # SQLAlchemy models
│   └── __init__.py
├── schemas/               # Pydantic schemas
│   └── __init__.py
├── routers/               # FastAPI routers
│   └── __init__.py
├── services/              # Business logic
│   └── __init__.py
├── migrations/            # Alembic migrations
├── seeds/                 # Seed data
├── tests/                 # Tests
└── README.md

/frontend/modules/{module-name}/
├── module.js              # Module class definition
├── manifest.json          # Frontend metadata
├── pages/                 # Page components
│   └── dashboard-page.js
├── components/            # Reusable components
├── services/              # API services
└── templates/             # HTML templates
```

---

## Quick Start

### 1. Create a New Module

Use the module creation script:

```bash
cd /home/user/app-buildify
./scripts/create-module.sh my-module
```

This creates:
- Complete backend structure
- Complete frontend structure
- Manifest files
- Sample code

### 2. Develop Your Module

Edit the generated files:

**Backend** (`backend/modules/my-module/module.py`):
```python
class MyModuleModule(BaseModule):
    def get_router(self) -> APIRouter:
        router = APIRouter(prefix="/api/v1/my-module", tags=["my-module"])
        # Add your routes
        return router

    def get_permissions(self) -> List[Dict]:
        return self.manifest.get("permissions", [])
```

**Frontend** (`frontend/modules/my-module/module.js`):
```javascript
export default class MyModuleModule extends BaseModule {
    async init() {
        await super.init();
        // Initialize your module
    }
}
```

### 3. Install and Enable

```bash
# Restart server to discover module
# Then via API:

POST /api/v1/modules/install
{
  "module_name": "my-module"
}

POST /api/v1/modules/enable
{
  "module_name": "my-module"
}
```

---

## Backend Development

### Module Class

Every module must have a class that inherits from `BaseModule`:

```python
from core.module_system.base_module import BaseModule
from fastapi import APIRouter

class FinancialModule(BaseModule):
    def get_router(self) -> APIRouter:
        """Return FastAPI router"""
        router = APIRouter(prefix="/api/v1/financial", tags=["financial"])
        router.include_router(accounts_router)
        router.include_router(invoices_router)
        return router

    def get_permissions(self) -> List[Dict]:
        """Return permission definitions"""
        return self.manifest.get("permissions", [])

    def get_models(self) -> List:
        """Return SQLAlchemy models"""
        return [Account, Transaction, Invoice]
```

### Database Models

Create SQLAlchemy models in `models/`:

```python
from sqlalchemy import Column, String, Numeric, ForeignKey
from models.base import Base, GUID, generate_uuid

class FinancialAccount(Base):
    __tablename__ = "financial_accounts"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False)
    company_id = Column(GUID, ForeignKey("companies.id"), nullable=False)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    current_balance = Column(Numeric(18, 2), default=0)
```

### API Routers

Create routers in `routers/`:

```python
from fastapi import APIRouter, Depends
from core.dependencies import has_permission
from ..permissions import FinancialPermissions

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("/")
async def list_accounts(
    current_user = Depends(has_permission(FinancialPermissions.ACCOUNTS_READ))
):
    # Your logic here
    return accounts
```

### Permissions

Define permissions in `permissions.py`:

```python
from enum import Enum

class FinancialPermissions(str, Enum):
    ACCOUNTS_READ = "financial:accounts:read:company"
    ACCOUNTS_CREATE = "financial:accounts:create:company"
    INVOICES_READ = "financial:invoices:read:company"
```

---

## Frontend Development

### Module Class

```javascript
import { BaseModule } from '../../assets/js/core/module-system/base-module.js';

export default class FinancialModule extends BaseModule {
    constructor(manifest) {
        super(manifest);
    }

    async init() {
        await super.init();
        console.log('Financial module initialized');

        // Custom initialization
        this.initDashboardWidget();
    }

    initDashboardWidget() {
        // Register widgets, etc.
    }
}
```

### Pages

Create pages in `pages/`:

```javascript
export default class AccountsPage {
    async render() {
        const container = document.getElementById('app-content');
        container.innerHTML = `
            <div class="accounts-page">
                <h1>Accounts</h1>
                <!-- Your UI here -->
            </div>
        `;

        this.setupEventListeners();
        await this.loadData();
    }

    setupEventListeners() {
        // Add event listeners
    }

    async loadData() {
        // Load data from API
    }
}
```

### Calling Backend APIs

Use the module's built-in API helper:

```javascript
// In your module class
async getAccounts(companyId) {
    const response = await this.apiRequest(`/accounts?company_id=${companyId}`, {
        method: 'GET'
    });

    if (response.ok) {
        return await response.json();
    }
    return [];
}
```

---

## Permissions & RBAC

### Backend Permission Checking

```python
from core.dependencies import has_permission
from ..permissions import FinancialPermissions

@router.post("/")
async def create_account(
    data: AccountCreate,
    current_user = Depends(has_permission(FinancialPermissions.ACCOUNTS_CREATE))
):
    # Only users with permission can access
    pass
```

### Frontend Permission Checking

```javascript
import { hasPermission } from '../../../assets/js/core/rbac.js';

export default class AccountsPage {
    async render() {
        const canCreate = await hasPermission('financial:accounts:create:company');

        container.innerHTML = `
            <div>
                ${canCreate ? '<button>Create Account</button>' : ''}
            </div>
        `;
    }
}
```

### Permission Format

```
{resource}:{action}:{scope}

Examples:
- financial:accounts:read:company
- financial:invoices:create:company
- financial:reports:export:tenant
```

**Scopes:**
- `all` - Superuser only
- `tenant` - Across entire tenant
- `company` - Within company
- `department` - Within department
- `own` - User's own data

---

## Configuration

### Backend Manifest (`manifest.json`)

```json
{
  "name": "financial",
  "display_name": "Financial Management",
  "version": "1.0.0",
  "description": "Complete financial management system",

  "category": "finance",
  "tags": ["accounting", "invoicing"],

  "permissions": [
    {
      "code": "financial:accounts:read:company",
      "name": "View Accounts",
      "description": "View chart of accounts",
      "category": "financial",
      "scope": "company"
    }
  ],

  "configuration": {
    "settings": [
      {
        "key": "default_currency",
        "type": "string",
        "default": "USD",
        "description": "Default currency"
      }
    ]
  },

  "subscription_tier": "premium",
  "dependencies": {
    "required": [],
    "optional": ["reporting"]
  }
}
```

### Frontend Manifest

```json
{
  "name": "financial",
  "display_name": "Financial Management",
  "version": "1.0.0",

  "entry_point": "module.js",

  "routes": [
    {
      "path": "#/financial/dashboard",
      "name": "Financial Dashboard",
      "component": "pages/dashboard-page.js",
      "permission": "financial:accounts:read:company",
      "menu": {
        "label": "Financial",
        "icon": "💰",
        "order": 10
      }
    }
  ]
}
```

---

## Lifecycle Hooks

### Backend Hooks

```python
class FinancialModule(BaseModule):
    def pre_install(self, db_session) -> tuple[bool, str | None]:
        """Called before installation - return False to abort"""
        # Check prerequisites
        return True, None

    def post_install(self, db_session):
        """Called after installation"""
        # Create default data
        pass

    def pre_enable(self, db_session, tenant_id) -> tuple[bool, str | None]:
        """Called before enabling for tenant"""
        # Check tenant subscription
        return True, None

    def post_enable(self, db_session, tenant_id):
        """Called after enabling for tenant"""
        # Create tenant-specific data
        pass

    def pre_disable(self, db_session, tenant_id) -> tuple[bool, str | None]:
        """Called before disabling"""
        # Check if can be disabled
        return True, None

    def post_disable(self, db_session, tenant_id):
        """Called after disabling"""
        # Cleanup
        pass
```

### Frontend Hooks

```javascript
export default class FinancialModule extends BaseModule {
    async init() {
        await super.init();
        // Called when module is loaded
    }

    cleanup() {
        // Called when module is unloaded
        super.cleanup();
    }
}
```

---

## Best Practices

### 1. Module Naming

- Use lowercase with hyphens: `financial`, `warehouse-management`
- Class names in PascalCase: `FinancialModule`
- Table names prefixed: `financial_accounts`

### 2. Multi-Tenancy

Always include tenant_id and company_id in your models:

```python
class MyModel(Base):
    id = Column(GUID, primary_key=True, default=generate_uuid)
    tenant_id = Column(GUID, ForeignKey("tenants.id"), nullable=False)
    company_id = Column(GUID, ForeignKey("companies.id"), nullable=False)
```

### 3. Error Handling

```python
@router.get("/{id}")
async def get_item(id: str, current_user = Depends(get_current_user)):
    item = db.query(MyModel).filter(
        MyModel.id == id,
        MyModel.tenant_id == current_user.tenant_id  # Tenant isolation!
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return item
```

### 4. Frontend State Management

```javascript
export default class MyPage {
    constructor() {
        this.data = [];
        this.loading = false;
    }

    async loadData() {
        this.loading = true;
        try {
            this.data = await this.fetchFromAPI();
            this.render();
        } catch (error) {
            console.error('Error loading data:', error);
        } finally {
            this.loading = false;
        }
    }
}
```

### 5. Permissions

- Check permissions on both frontend and backend
- Use granular permissions (read/create/update/delete)
- Include scope in permission code

---

## Examples

See the `financial` module for a complete example:

- **Backend**: `/backend/modules/financial/`
- **Frontend**: `/frontend/modules/financial/`

Key files to review:
- `backend/modules/financial/module.py` - Module definition
- `backend/modules/financial/manifest.json` - Configuration
- `backend/modules/financial/routers/accounts.py` - API endpoints
- `frontend/modules/financial/module.js` - Frontend module
- `frontend/modules/financial/pages/accounts-page.js` - Page component

---

## Troubleshooting

### Module Not Discovered

1. Check directory structure is correct
2. Ensure `manifest.json` exists
3. Ensure `module.py` exists with correct class name
4. Restart backend server

### Module Not Loading in Frontend

1. Check browser console for errors
2. Verify module is enabled for tenant
3. Check manifest.json paths are correct
4. Verify module.js exports default class

### Permission Denied

1. Check permission code matches exactly
2. Verify user has required role
3. Check RBAC configuration in backend
4. Verify permission was registered during install

---

## API Reference

### Module Management

```bash
# List available modules
GET /api/v1/modules/available

# List enabled modules
GET /api/v1/modules/enabled

# Get module info
GET /api/v1/modules/{module_name}

# Install module (superuser)
POST /api/v1/modules/install
{ "module_name": "financial" }

# Enable for tenant
POST /api/v1/modules/enable
{ "module_name": "financial", "configuration": {} }

# Disable for tenant
POST /api/v1/modules/disable
{ "module_name": "financial" }

# Update configuration
PUT /api/v1/modules/{module_name}/configuration
{ "configuration": { "key": "value" } }
```

---

## Support

For questions or issues:
- Check the examples in `/backend/modules/financial/`
- Review this documentation
- Contact the platform team

---

**Happy Module Development!** 🚀
