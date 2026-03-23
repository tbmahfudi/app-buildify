# Implementation Plan: Open Module Development with Core Protection

**Goal**: Enable external developers to build modules while keeping core backend and business logic protected.

**Strategy**:
- Backend: SaaS model - Core hosted by you, modules call Core API
- Frontend: Public infrastructure framework - Modules use global APIs
- Protection: Core code never leaves your server

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR CLOUD SERVER                     │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  Core API (Protected - Your Code)              │     │
│  │  ├── /api/v1/auth/*        (Authentication)    │     │
│  │  ├── /api/v1/rbac/*        (Permissions)       │     │
│  │  ├── /api/v1/org/*         (Organizations)     │     │
│  │  ├── /api/v1/menu/*        (Navigation)        │     │
│  │  ├── /api/v1/settings/*    (Settings)          │     │
│  │  └── /api/v1/core/*        (Core Services)     │     │
│  └────────────────┬───────────────────────────────┘     │
│                   │                                      │
│  ┌────────────────▼───────────────────────────────┐     │
│  │  PostgreSQL (Protected - Your Data)            │     │
│  └────────────────────────────────────────────────┘     │
└──────────────────┬───────────────────────────────────────┘
                   │ HTTPS API
                   │ (API Key Authentication)
        ┌──────────┴──────────┬──────────────┐
        │                     │              │
┌───────▼────────┐  ┌─────────▼──────┐  ┌──▼──────────┐
│ Financial      │  │ Inventory      │  │ CRM         │
│ Module         │  │ Module         │  │ Module      │
│ (Developer)    │  │ (Developer)    │  │ (Developer) │
│                │  │                │  │             │
│ Backend ───────┼──┼────────────────┼──┼─► Core API  │
│ Frontend       │  │ Frontend       │  │ Frontend    │
└────────────────┘  └────────────────┘  └─────────────┘
```

---

## PHASE 1: Define Core Boundaries

### Current State Analysis

**Backend Core Components (Keep Private):**
```
backend/app/
├── core/                      ✅ CORE - Infrastructure
│   ├── auth.py               (Authentication system)
│   ├── config.py             (Configuration)
│   ├── db.py                 (Database connection)
│   ├── dependencies.py       (DI system)
│   ├── security_*.py         (Security features)
│   ├── module_system/        (Module loading)
│   ├── audit.py              (Audit logging)
│   ├── exceptions.py         (Error handling)
│   └── rate_limiter.py       (Rate limiting)
│
├── models/                    ✅ CORE - Data models
│   ├── user.py
│   ├── role.py
│   ├── permission.py
│   ├── tenant.py
│   ├── module_registry.py
│   └── ...
│
├── routers/                   ✅ CORE - API endpoints
│   ├── auth.py               (All routers stay in core)
│   ├── org.py
│   ├── rbac.py
│   ├── modules.py
│   ├── menu.py
│   ├── settings.py
│   ├── data.py
│   ├── metadata.py
│   ├── dashboards.py
│   ├── reports.py
│   ├── scheduler.py
│   └── audit.py
│
└── main.py                    ✅ CORE - FastAPI app
```

**Frontend Core (Public Infrastructure):**
```
frontend/
├── assets/js/
│   ├── core/                  ✅ Infrastructure (okay to expose)
│   ├── auth-service.js       (API wrapper)
│   ├── router.js             (SPA routing)
│   ├── api-client.js         (HTTP client)
│   └── ui-components.js      (UI library)
├── components/                ✅ Reusable components
└── index.html                 ✅ Shell
```

**Module Structure (Developers Build):**
```
modules/{module_name}/
├── backend/
│   ├── app/
│   │   ├── main.py           (Uses SDK to call Core API)
│   │   ├── routers/          (Module routes)
│   │   ├── models/           (Module-specific models)
│   │   └── services/         (Business logic)
│   └── tests/
├── frontend/
│   ├── module.js             (Entry point)
│   ├── pages/                (UI pages)
│   └── components/           (UI components)
└── manifest.json             (Module metadata)
```

### Tasks

- [ ] Document core API surface (what modules can access)
- [ ] Define Core API contract (authentication, RBAC, data access)
- [ ] Create architecture diagram
- [ ] Define module manifest schema v2 (with Core API requirements)

---

## PHASE 2: Backend SDK Package

### Objective
Create `buildify-sdk` Python package that module developers install to interact with Core API.

### SDK Structure

```
backend/sdk/
├── setup.py
├── README.md
├── buildify_sdk/
│   ├── __init__.py
│   ├── client.py             # CoreAPIClient (main interface)
│   ├── auth.py               # Auth helpers
│   ├── dependencies.py       # FastAPI dependencies
│   ├── exceptions.py         # Exception classes
│   ├── schemas.py            # Pydantic base schemas
│   ├── permissions.py        # Permission decorators
│   ├── models.py             # Base SQLAlchemy models (if needed)
│   └── testing/
│       ├── __init__.py
│       ├── mock_core.py      # Mock Core API for unit tests
│       ├── fixtures.py       # Pytest fixtures
│       └── test_client.py    # Test client utilities
```

### Core Client Implementation

**buildify_sdk/client.py:**
```python
import httpx
from typing import Optional, Dict, Any, List

class CoreAPIClient:
    """
    Client for interacting with Buildify Core API.

    Module developers use this to:
    - Authenticate users
    - Check permissions
    - Access tenant data
    - Query core services
    """

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            headers={"X-API-Key": api_key},
            timeout=30.0
        )

    # Authentication
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and get user info"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/core/auth/verify",
            json={"token": token}
        )
        response.raise_for_status()
        return response.json()

    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """Get current user details"""
        user_data = await self.verify_token(token)
        return user_data["user"]

    # RBAC
    async def check_permission(
        self,
        user_id: int,
        permission: str,
        resource_id: Optional[int] = None
    ) -> bool:
        """Check if user has permission"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/core/rbac/check",
            json={
                "user_id": user_id,
                "permission": permission,
                "resource_id": resource_id
            }
        )
        response.raise_for_status()
        return response.json()["allowed"]

    async def get_user_permissions(self, user_id: int) -> List[str]:
        """Get all permissions for user"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/core/rbac/users/{user_id}/permissions"
        )
        response.raise_for_status()
        return response.json()["permissions"]

    # Tenant/Organization
    async def get_tenant_info(self, tenant_id: int) -> Dict[str, Any]:
        """Get tenant information"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/core/tenants/{tenant_id}"
        )
        response.raise_for_status()
        return response.json()

    async def is_module_enabled(
        self,
        tenant_id: int,
        module_name: str
    ) -> bool:
        """Check if module is enabled for tenant"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/core/tenants/{tenant_id}/modules/{module_name}"
        )
        return response.status_code == 200

    # Audit
    async def log_audit(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict] = None
    ):
        """Log audit event"""
        await self.client.post(
            f"{self.base_url}/api/v1/core/audit/log",
            json={
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details
            }
        )

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
```

**buildify_sdk/dependencies.py:**
```python
from fastapi import Depends, HTTPException, Header
from typing import Optional
import os

from .client import CoreAPIClient

def get_core_client() -> CoreAPIClient:
    """Dependency to get Core API client"""
    return CoreAPIClient(
        base_url=os.getenv("CORE_API_URL", "http://localhost:8000"),
        api_key=os.getenv("CORE_API_KEY")
    )

async def get_current_user(
    authorization: str = Header(...),
    core: CoreAPIClient = Depends(get_core_client)
):
    """
    Dependency to get current authenticated user.
    Module developers use this in their routes.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")

    token = authorization.replace("Bearer ", "")

    try:
        user = await core.get_current_user(token)
        return user
    except Exception as e:
        raise HTTPException(401, f"Authentication failed: {str(e)}")

async def require_permission(permission: str):
    """
    Dependency factory to check permissions.

    Usage:
        @router.get("/accounts")
        async def list_accounts(
            user = Depends(get_current_user),
            _ = Depends(require_permission("financial:accounts:read"))
        ):
            ...
    """
    async def check(
        user = Depends(get_current_user),
        core: CoreAPIClient = Depends(get_core_client)
    ):
        allowed = await core.check_permission(user["id"], permission)
        if not allowed:
            raise HTTPException(403, f"Missing permission: {permission}")
        return True

    return check
```

**buildify_sdk/testing/mock_core.py:**
```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse

def create_mock_core_api():
    """
    Create a mock Core API for module testing.
    Returns a FastAPI app that mimics Core API responses.
    """
    app = FastAPI(title="Mock Buildify Core API")

    @app.post("/api/v1/core/auth/verify")
    async def verify_token(data: dict):
        return {
            "user": {
                "id": 1,
                "email": "test@example.com",
                "tenant_id": 1,
                "tenant_code": "TEST001"
            }
        }

    @app.post("/api/v1/core/rbac/check")
    async def check_permission(data: dict):
        # Mock: always allow in tests
        return {"allowed": True}

    @app.get("/api/v1/core/tenants/{tenant_id}")
    async def get_tenant(tenant_id: int):
        return {
            "id": tenant_id,
            "code": f"TEST{tenant_id:03d}",
            "name": "Test Tenant"
        }

    return app
```

### Tasks

- [ ] Create `backend/sdk/` directory structure
- [ ] Implement `CoreAPIClient` class
- [ ] Implement FastAPI dependencies (get_current_user, require_permission)
- [ ] Create mock Core API for testing
- [ ] Write SDK documentation
- [ ] Create `setup.py` for package distribution
- [ ] Publish to private PyPI or GitHub packages

---

## PHASE 3: Core API Gateway

### Objective
Add new API endpoints to Core that modules call for authentication, RBAC, and data access.

### New Router: /api/v1/core/*

**File: backend/app/routers/core_api.py**

```python
"""
Core API Gateway for Modules

This router provides API endpoints that external modules can call
to access core services (auth, RBAC, tenant info, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.core.db import get_db
from app.core.auth import decode_access_token
from app.models.user import User
from app.models.tenant import Tenant
from app.models.permission import Permission
from app.services.rbac_service import RBACService

router = APIRouter(prefix="/core", tags=["core-services"])

# API Key Authentication for modules
def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify module API key"""
    # TODO: Implement proper API key management in database
    valid_keys = {
        "dev_key_123": "financial",  # Development key
        "prod_key_xyz": "financial"  # Production key
    }

    if x_api_key not in valid_keys:
        raise HTTPException(401, "Invalid API key")

    return valid_keys[x_api_key]

# Authentication Endpoints
@router.post("/auth/verify")
async def verify_token(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    module_name: str = Depends(verify_api_key)
):
    """
    Verify JWT token and return user information.

    Request:
        {"token": "eyJ..."}

    Response:
        {
            "user": {
                "id": 1,
                "email": "user@example.com",
                "tenant_id": 1,
                "tenant_code": "ACME001"
            }
        }
    """
    token = data.get("token")
    if not token:
        raise HTTPException(400, "Token required")

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(404, "User not found")

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "tenant_id": user.tenant_id,
                "tenant_code": user.tenant.code if user.tenant else None
            }
        }
    except Exception as e:
        raise HTTPException(401, f"Invalid token: {str(e)}")

# RBAC Endpoints
@router.post("/rbac/check")
async def check_permission(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    module_name: str = Depends(verify_api_key)
):
    """
    Check if user has permission.

    Request:
        {
            "user_id": 1,
            "permission": "financial:accounts:read",
            "resource_id": null
        }

    Response:
        {"allowed": true}
    """
    user_id = data.get("user_id")
    permission = data.get("permission")
    resource_id = data.get("resource_id")

    rbac = RBACService(db)
    allowed = rbac.check_permission(user_id, permission, resource_id)

    return {"allowed": allowed}

@router.get("/rbac/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    module_name: str = Depends(verify_api_key)
):
    """Get all permissions for a user"""
    rbac = RBACService(db)
    permissions = rbac.get_user_permissions(user_id)

    return {"permissions": [p.code for p in permissions]}

# Tenant Endpoints
@router.get("/tenants/{tenant_id}")
async def get_tenant_info(
    tenant_id: int,
    db: Session = Depends(get_db),
    module_name: str = Depends(verify_api_key)
):
    """Get tenant information"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(404, "Tenant not found")

    return {
        "id": tenant.id,
        "code": tenant.code,
        "name": tenant.name,
        "is_active": tenant.is_active
    }

@router.get("/tenants/{tenant_id}/modules/{module_name}")
async def check_module_enabled(
    tenant_id: int,
    module_name: str,
    db: Session = Depends(get_db),
    api_key_module: str = Depends(verify_api_key)
):
    """Check if module is enabled for tenant"""
    from app.models.module_registry import TenantModule

    tenant_module = db.query(TenantModule).filter(
        TenantModule.tenant_id == tenant_id,
        TenantModule.module_name == module_name,
        TenantModule.is_enabled == True
    ).first()

    if not tenant_module:
        raise HTTPException(404, "Module not enabled for tenant")

    return {"enabled": True}

# Audit Endpoints
@router.post("/audit/log")
async def log_audit_event(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    module_name: str = Depends(verify_api_key)
):
    """Log audit event from module"""
    from app.models.audit import AuditLog

    audit = AuditLog(
        user_id=data.get("user_id"),
        action=data.get("action"),
        resource_type=data.get("resource_type"),
        resource_id=data.get("resource_id"),
        details=data.get("details"),
        module=module_name  # Track which module logged this
    )
    db.add(audit)
    db.commit()

    return {"status": "logged"}
```

### Update main.py

```python
# Add to backend/app/main.py

from app.routers import core_api

# Include Core API Gateway router
app.include_router(core_api.router, prefix="/api/v1")
```

### API Key Management

**Create model: backend/app/models/api_key.py**
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

from .base import BaseModel

class APIKey(BaseModel):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    key = Column(String(255), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    module_name = Column(String(100))
    environment = Column(String(20))  # dev, staging, prod
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
```

### Tasks

- [ ] Create `backend/app/routers/core_api.py`
- [ ] Implement authentication endpoints
- [ ] Implement RBAC endpoints
- [ ] Implement tenant endpoints
- [ ] Implement audit endpoints
- [ ] Create API key model and management
- [ ] Add API key authentication middleware
- [ ] Add rate limiting for Core API
- [ ] Document all Core API endpoints (OpenAPI)
- [ ] Include router in main.py

---

## PHASE 4: Frontend Module System

### Objective
Formalize frontend module system with documented global APIs and module loading.

### Global API Definition

**File: frontend/assets/js/buildify-global-api.js**

```javascript
/**
 * Buildify Global API
 *
 * This object is exposed to all modules and provides
 * access to core services.
 */

window.buildify = {
    version: '1.0.0',

    // API Client
    api: {
        /**
         * Make authenticated GET request
         * @param {string} endpoint - API endpoint
         * @param {Object} options - Request options
         * @returns {Promise<any>}
         */
        async get(endpoint, options = {}) {
            const token = localStorage.getItem('auth_token');
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.statusText}`);
            }

            return response.json();
        },

        async post(endpoint, data, options = {}) {
            const token = localStorage.getItem('auth_token');
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.statusText}`);
            }

            return response.json();
        },

        async put(endpoint, data, options = {}) { /* ... */ },
        async delete(endpoint, options = {}) { /* ... */ }
    },

    // Router
    router: {
        /**
         * Navigate to route
         * @param {string} path - Route path (e.g., '#/financial/accounts')
         */
        navigate(path) {
            window.location.hash = path;
        },

        /**
         * Register route handler
         * @param {string} path - Route pattern
         * @param {Function} handler - Route handler function
         */
        registerRoute(path, handler) {
            window.router.routes[path] = handler;
        },

        /**
         * Get current route
         * @returns {string}
         */
        getCurrentRoute() {
            return window.location.hash;
        }
    },

    // Authentication
    auth: {
        /**
         * Get current authenticated user
         * @returns {Object} User object
         */
        getCurrentUser() {
            const userJson = localStorage.getItem('current_user');
            return userJson ? JSON.parse(userJson) : null;
        },

        /**
         * Check if user has permission
         * @param {string} permission - Permission code
         * @returns {boolean}
         */
        hasPermission(permission) {
            const user = this.getCurrentUser();
            if (!user || !user.permissions) return false;
            return user.permissions.includes(permission);
        },

        /**
         * Get auth token
         * @returns {string}
         */
        getToken() {
            return localStorage.getItem('auth_token');
        }
    },

    // UI Components
    ui: {
        /**
         * Create table component
         * @param {Object} options - Table options
         * @returns {HTMLElement}
         */
        createTable(options) {
            const { data, columns, actions } = options;

            const table = document.createElement('table');
            table.className = 'table table-striped';

            // Header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            columns.forEach(col => {
                const th = document.createElement('th');
                th.textContent = col.label;
                headerRow.appendChild(th);
            });
            if (actions) {
                const th = document.createElement('th');
                th.textContent = 'Actions';
                headerRow.appendChild(th);
            }
            thead.appendChild(headerRow);
            table.appendChild(thead);

            // Body
            const tbody = document.createElement('tbody');
            data.forEach(row => {
                const tr = document.createElement('tr');
                columns.forEach(col => {
                    const td = document.createElement('td');
                    td.textContent = row[col.key];
                    tr.appendChild(td);
                });
                if (actions) {
                    const td = document.createElement('td');
                    actions.forEach(action => {
                        const btn = document.createElement('button');
                        btn.className = `btn btn-sm ${action.class || 'btn-primary'}`;
                        btn.textContent = action.label;
                        btn.onclick = () => action.handler(row);
                        td.appendChild(btn);
                    });
                    tr.appendChild(td);
                }
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);

            return table;
        },

        /**
         * Show toast notification
         * @param {string} message - Message text
         * @param {string} type - Type (success, error, warning, info)
         */
        showToast(message, type = 'info') {
            window.showNotification(message, type);
        },

        /**
         * Show modal dialog
         * @param {Object} options - Modal options
         */
        showModal(options) {
            // Implementation
        }
    },

    // Events
    events: {
        /**
         * Subscribe to event
         * @param {string} eventName - Event name
         * @param {Function} handler - Event handler
         */
        on(eventName, handler) {
            window.addEventListener(eventName, handler);
        },

        /**
         * Emit event
         * @param {string} eventName - Event name
         * @param {any} data - Event data
         */
        emit(eventName, data) {
            const event = new CustomEvent(eventName, { detail: data });
            window.dispatchEvent(event);
        }
    }
};

// Freeze to prevent modifications
Object.freeze(window.buildify);
```

### Module Template

**File: module-template/frontend/module.js**

```javascript
/**
 * Module Template
 *
 * All modules must export a default class that implements:
 * - constructor(manifest)
 * - async init()
 */

export default class MyModule {
    constructor(manifest) {
        this.manifest = manifest;
        this.name = manifest.name;

        // Access global APIs
        this.api = window.buildify.api;
        this.router = window.buildify.router;
        this.auth = window.buildify.auth;
        this.ui = window.buildify.ui;
    }

    /**
     * Initialize module
     * Called after module is loaded
     */
    async init() {
        console.log(`Initializing ${this.name} module`);

        // Register routes
        this.registerRoutes();

        // Register menu items (if defined in manifest)
        this.registerMenuItems();

        // Subscribe to events
        this.subscribeToEvents();
    }

    registerRoutes() {
        // Register routes from manifest
        this.manifest.routes.forEach(route => {
            const path = route.path.replace('#/', '');

            this.router.registerRoute(path, async () => {
                // Check permission
                if (route.permission && !this.auth.hasPermission(route.permission)) {
                    this.ui.showToast('Access denied', 'error');
                    this.router.navigate('#/dashboard');
                    return;
                }

                // Load component
                await this.loadComponent(route.component);
            });
        });
    }

    async loadComponent(componentPath) {
        // Dynamically import component
        const component = await import(`./pages/${componentPath}`);

        // Render component
        const container = document.getElementById('main-content');
        container.innerHTML = '';

        const instance = new component.default();
        await instance.render(container);
    }

    registerMenuItems() {
        // Add menu items to navigation
        // Implementation depends on your menu system
    }

    subscribeToEvents() {
        // Listen to global events
        window.buildify.events.on('user-logged-in', (event) => {
            console.log('User logged in', event.detail);
        });
    }
}
```

### Tasks

- [ ] Create `frontend/assets/js/buildify-global-api.js`
- [ ] Implement all global API methods
- [ ] Update `frontend/assets/js/app.js` to initialize global API
- [ ] Create module template with example
- [ ] Document all global APIs
- [ ] Add TypeScript definitions for global API
- [ ] Test module loading with existing financial module

---

## PHASE 5: Module Development Environment

### Objective
Create complete development environment for module developers with testing infrastructure.

### Directory Structure for Module Developers

```
module-dev-kit/
├── README.md                    # Getting started guide
├── template/                    # Module template
│   ├── backend/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routers/
│   │   │   │   └── __init__.py
│   │   │   ├── models/
│   │   │   │   └── __init__.py
│   │   │   ├── schemas/
│   │   │   │   └── __init__.py
│   │   │   └── services/
│   │   │       └── __init__.py
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py
│   │   │   └── test_routes.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   ├── frontend/
│   │   ├── module.js
│   │   ├── pages/
│   │   │   └── home.js
│   │   ├── components/
│   │   │   └── example.js
│   │   └── styles/
│   │       └── module.css
│   ├── manifest.json
│   ├── docker-compose.yml
│   └── README.md
├── docs/
│   ├── getting-started.md
│   ├── backend-development.md
│   ├── frontend-development.md
│   ├── core-api-reference.md
│   ├── testing-guide.md
│   └── deployment.md
└── examples/
    ├── simple-module/
    └── advanced-module/
```

### docker-compose.yml for Module Testing

```yaml
version: '3.8'

services:
  # Mock Core API (for local development without real core)
  mock-core:
    build:
      context: ./mock-core
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENV=development
    networks:
      - module-network

  # Module Backend
  module-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "9000:9000"
    environment:
      - CORE_API_URL=http://mock-core:8000
      - CORE_API_KEY=dev_key_123
      - DATABASE_URL=postgresql://module:module@module-db:5432/module_db
    volumes:
      - ./backend:/app
    depends_on:
      - mock-core
      - module-db
    networks:
      - module-network

  # Module Database
  module-db:
    image: postgres:15
    environment:
      - POSTGRES_USER=module
      - POSTGRES_PASSWORD=module
      - POSTGRES_DB=module_db
    ports:
      - "5433:5432"
    volumes:
      - module-db-data:/var/lib/postgresql/data
    networks:
      - module-network

  # Frontend (nginx serving static files)
  frontend:
    image: nginx:alpine
    ports:
      - "3000:80"
    volumes:
      - ./frontend:/usr/share/nginx/html/modules/mymodule
      - ../core-frontend:/usr/share/nginx/html  # Core frontend files
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - module-backend
    networks:
      - module-network

networks:
  module-network:
    driver: bridge

volumes:
  module-db-data:
```

### Mock Core API

**File: mock-core/main.py**

```python
"""
Mock Buildify Core API for Module Development

This provides a simplified version of the Core API
for local module development and testing.
"""

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Mock Buildify Core API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
MOCK_USER = {
    "id": 1,
    "email": "dev@example.com",
    "username": "developer",
    "tenant_id": 1,
    "tenant_code": "DEV001"
}

MOCK_PERMISSIONS = [
    "financial:accounts:read",
    "financial:accounts:write",
    "financial:invoices:read",
    "financial:invoices:write"
]

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != "dev_key_123":
        raise HTTPException(401, "Invalid API key")

@app.get("/")
def root():
    return {"message": "Mock Buildify Core API", "version": "1.0.0"}

@app.post("/api/v1/core/auth/verify")
def verify_token(data: dict, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    return {"user": MOCK_USER}

@app.post("/api/v1/core/rbac/check")
def check_permission(data: dict, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    permission = data.get("permission")
    return {"allowed": permission in MOCK_PERMISSIONS}

@app.get("/api/v1/core/rbac/users/{user_id}/permissions")
def get_permissions(user_id: int, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    return {"permissions": MOCK_PERMISSIONS}

@app.get("/api/v1/core/tenants/{tenant_id}")
def get_tenant(tenant_id: int, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    return {
        "id": tenant_id,
        "code": f"DEV{tenant_id:03d}",
        "name": "Development Tenant",
        "is_active": True
    }

@app.get("/api/v1/core/tenants/{tenant_id}/modules/{module_name}")
def check_module_enabled(
    tenant_id: int,
    module_name: str,
    x_api_key: str = Header(...)
):
    verify_api_key(x_api_key)
    return {"enabled": True}

@app.post("/api/v1/core/audit/log")
def log_audit(data: dict, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    print(f"[AUDIT] {data}")
    return {"status": "logged"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Tasks

- [ ] Create module development kit structure
- [ ] Create module template with complete example
- [ ] Implement Mock Core API
- [ ] Create docker-compose.yml for local testing
- [ ] Write pytest configuration and example tests
- [ ] Create getting started guide
- [ ] Create video tutorial (optional)
- [ ] Package as downloadable ZIP or GitHub template

---

## PHASE 6: Documentation

### Objective
Create comprehensive documentation for module developers.

### Documentation Structure

```
docs/
├── index.md                          # Overview
├── getting-started/
│   ├── introduction.md
│   ├── prerequisites.md
│   ├── setup-environment.md
│   └── first-module.md
├── backend/
│   ├── architecture.md
│   ├── sdk-reference.md
│   │   ├── core-client.md
│   │   ├── dependencies.md
│   │   ├── permissions.md
│   │   └── testing.md
│   ├── core-api/
│   │   ├── authentication.md
│   │   ├── rbac.md
│   │   ├── tenants.md
│   │   └── audit.md
│   └── best-practices.md
├── frontend/
│   ├── architecture.md
│   ├── global-api-reference.md
│   │   ├── api-client.md
│   │   ├── router.md
│   │   ├── auth.md
│   │   └── ui-components.md
│   ├── module-structure.md
│   └── best-practices.md
├── manifest/
│   ├── schema.md
│   ├── routes.md
│   ├── permissions.md
│   └── navigation.md
├── testing/
│   ├── unit-testing.md
│   ├── integration-testing.md
│   └── e2e-testing.md
├── deployment/
│   ├── local-development.md
│   ├── staging.md
│   └── production.md
└── examples/
    ├── simple-crud-module.md
    ├── dashboard-widget.md
    └── background-jobs.md
```

### Key Documentation Files

**docs/backend/core-api/authentication.md:**

````markdown
# Core API: Authentication

## Overview

The Core API provides authentication endpoints that modules use to verify user tokens and get user information.

## Endpoints

### POST /api/v1/core/auth/verify

Verify a JWT token and retrieve user information.

**Request:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "tenant_id": 1,
    "tenant_code": "ACME001"
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired token
- `404 Not Found`: User not found

## Using in Your Module

### With SDK

```python
from buildify_sdk import get_current_user
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/my-resource")
async def get_resource(user = Depends(get_current_user)):
    # user is automatically authenticated
    print(f"User {user['email']} accessing resource")
    return {"data": "..."}
```

### Manual Usage

```python
from buildify_sdk import CoreAPIClient
import os

core = CoreAPIClient(
    base_url=os.getenv("CORE_API_URL"),
    api_key=os.getenv("CORE_API_KEY")
)

async def verify_user(token: str):
    user = await core.get_current_user(token)
    return user
```

## Best Practices

1. **Always use SDK dependencies** - Don't manually call Core API for auth
2. **Cache user info** - Core API calls have rate limits
3. **Handle errors gracefully** - User might be logged out
4. **Don't store tokens** - Let Core handle token management
````

### Tasks

- [ ] Write documentation index
- [ ] Document SDK API reference
- [ ] Document Core API endpoints
- [ ] Document Frontend global APIs
- [ ] Create getting started tutorial
- [ ] Create example modules with explanations
- [ ] Generate API docs from OpenAPI spec
- [ ] Setup documentation site (MkDocs or Docusaurus)
- [ ] Add inline code comments and docstrings

---

## PHASE 7: Deployment Strategy

### Objective
Define how Core and modules are deployed and hosted.

### Deployment Options

**Option 1: You Host Everything (Recommended Initially)**

```
Your Server:
├── Core API (FastAPI)
├── Core Frontend (Static files)
├── Module: Financial
├── Module: Inventory
├── Module: CRM
└── PostgreSQL Database
```

**Pros**: Full control, simpler management
**Cons**: You maintain all modules

---

**Option 2: Hybrid - Core + Selected Modules**

```
Your Server:                    Developer Server:
├── Core API                    ├── Custom Module API
├── Core Frontend               └── Custom Module Frontend
├── Module: Financial
├── Module: Inventory
└── PostgreSQL
```

**Pros**: You control core and standard modules, developers can self-host custom ones
**Cons**: More complex networking, security boundaries

---

### Core Deployment

**Infrastructure:**
- Cloud: AWS, GCP, Azure, or DigitalOcean
- Container: Docker + Docker Compose or Kubernetes
- CDN: CloudFlare for frontend assets
- Database: Managed PostgreSQL (AWS RDS, etc.)

**docker-compose.production.yml:**

```yaml
version: '3.8'

services:
  core-api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    restart: always
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./frontend:/usr/share/nginx/html
      - ./modules:/usr/share/nginx/html/modules
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - core-api
    restart: always
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

### Module Deployment

Modules can be deployed:
1. **Alongside Core** - You manage everything
2. **Separate Services** - Modules run independently, call Core API
3. **Serverless** - Module functions deployed to AWS Lambda, etc.

### CI/CD Pipeline

**GitHub Actions for Core:**

```yaml
# .github/workflows/deploy-core.yml
name: Deploy Core

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Build Docker image
        run: docker build -t buildify-core:latest ./backend

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker tag buildify-core:latest your-registry/buildify-core:latest
          docker push your-registry/buildify-core:latest

      - name: Deploy to production
        run: |
          ssh deploy@your-server.com "cd /app && docker-compose pull && docker-compose up -d"
```

**GitHub Actions for Module Validation:**

```yaml
# .github/workflows/validate-module.yml
name: Validate Module

on:
  pull_request:
    paths:
      - 'modules/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Run module tests
        run: |
          cd modules/${{ github.event.pull_request.head.ref }}
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit

      - name: Check manifest schema
        run: python scripts/validate_manifest.py modules/*/manifest.json

      - name: Security scan
        run: |
          pip install safety
          safety check -r modules/*/backend/requirements.txt
```

### Tasks

- [ ] Setup cloud hosting account
- [ ] Create production docker-compose configuration
- [ ] Setup nginx configuration for production
- [ ] Configure SSL certificates
- [ ] Setup CI/CD pipeline for core
- [ ] Setup module validation pipeline
- [ ] Create deployment documentation
- [ ] Setup monitoring (Sentry, DataDog, etc.)
- [ ] Setup backup strategy for database

---

## Implementation Timeline

### Week 1-2: Foundation
- ✅ Phase 1: Define boundaries
- ✅ Phase 2: Create SDK structure (basic)
- ✅ Phase 3: Implement Core API endpoints (auth, RBAC)

### Week 3-4: Module Infrastructure
- ✅ Phase 2: Complete SDK with all features
- ✅ Phase 4: Frontend global API
- ✅ Phase 5: Module dev kit and mock core

### Week 5-6: Testing & Documentation
- ✅ Phase 5: Complete testing infrastructure
- ✅ Phase 6: Write documentation
- ✅ Test with existing financial module

### Week 7-8: Deployment & Polish
- ✅ Phase 7: Setup deployment infrastructure
- ✅ Migrate existing financial module to new system
- ✅ Create second example module
- ✅ Beta test with external developer

---

## Success Criteria

### Developer Experience
- [ ] Developer can setup environment in < 30 minutes
- [ ] Developer can create basic module in < 2 hours
- [ ] Clear documentation for all APIs
- [ ] Working examples for common patterns

### Security
- [ ] Core code never exposed to developers
- [ ] API key authentication working
- [ ] Rate limiting on Core API
- [ ] Audit logging for all Core API calls

### Functionality
- [ ] Modules can authenticate users
- [ ] Modules can check permissions
- [ ] Modules can access tenant data
- [ ] Frontend modules load and render correctly
- [ ] All tests passing

---

## Risk Mitigation

### Risk: API Key Compromise
**Mitigation**:
- Short-lived API keys
- Key rotation system
- Rate limiting
- IP allowlisting for production keys

### Risk: Core API Downtime
**Mitigation**:
- High availability deployment
- Health checks
- Fallback mechanisms in modules
- Circuit breaker pattern in SDK

### Risk: Breaking Changes
**Mitigation**:
- API versioning (/api/v1/, /api/v2/)
- Deprecation warnings
- Maintain v1 for 6 months after v2 release
- Changelog for all API changes

### Risk: Module Security Issues
**Mitigation**:
- Code review required for all modules
- Automated security scanning
- Sandboxed execution (if possible)
- Module marketplace with vetting process

---

## Next Steps

1. **Review this plan** - Confirm approach and priorities
2. **Choose deployment strategy** - Where will you host Core?
3. **Start Phase 1** - Define Core API contract
4. **Create SDK** - Build `buildify-sdk` package
5. **Test with Financial Module** - Migrate existing module to new architecture

## Questions to Answer

1. **Hosting**: Where will you host Core API? (AWS, DigitalOcean, Fly.io, etc.)
2. **API Keys**: How will you distribute API keys to developers? (Manual, self-service portal?)
3. **Module Marketplace**: Will you have a marketplace? (Public, invite-only?)
4. **Pricing**: Will modules be paid/free? Does Core charge per module/tenant?
5. **Support**: How will you support module developers? (Forum, Slack, email?)

---

**Ready to start implementation? Let me know which phase you'd like to begin with!**
