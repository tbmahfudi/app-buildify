# Modular Architecture Design

## Overview

This document outlines the architecture for a fully modular platform where modules are:
- Developed and maintained in **separate repositories**
- Run their **own independent backend services**
- Registered and installed before use
- Customizable at **tenant and company levels**

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Module Structure](#module-structure)
- [Backend Architecture](#backend-architecture)
- [Frontend Architecture Options](#frontend-architecture-options)
- [Module Registry & Discovery](#module-registry--discovery)
- [Installation & Lifecycle](#installation--lifecycle)
- [Customization Levels](#customization-levels)
- [Communication Patterns](#communication-patterns)
- [Security & Isolation](#security--isolation)
- [Deployment Strategy](#deployment-strategy)
- [Migration Path](#migration-path)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                         │
│  - Request routing                                               │
│  - Authentication/Authorization                                  │
│  - Rate limiting                                                 │
└────────────────┬────────────────────────────────────────────────┘
                 │
    ┌────────────┴─────────────┬──────────────┬─────────────┐
    │                          │              │             │
┌───▼────────┐    ┌───────────▼──┐    ┌──────▼──────┐   ┌─▼─────────┐
│   Core     │    │  Financial   │    │  Warehouse  │   │  Custom   │
│  Platform  │    │   Module     │    │   Module    │   │  Modules  │
│  Service   │    │   Service    │    │   Service   │   │           │
└─────┬──────┘    └──────┬───────┘    └──────┬──────┘   └─────┬─────┘
      │                  │                   │                  │
      └──────────────────┴───────────────────┴──────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Shared Services   │
                    │  - Database         │
                    │  - Message Queue    │
                    │  - Cache (Redis)    │
                    │  - File Storage     │
                    └─────────────────────┘
```

### Module Independence

Each module:
- Lives in its own Git repository
- Runs as an independent microservice
- Has its own database schema (or separate database)
- Can be developed, tested, and deployed independently
- Registers with the core platform via Module Registry API

---

## Module Structure

### Repository Structure (Per Module)

```
my-module/
├── README.md
├── manifest.json              # Module metadata
├── docker-compose.yml         # Local development
├── Dockerfile                 # Container definition
│
├── backend/                   # Backend service
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI application
│   │   ├── config.py         # Configuration
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── routers/          # API endpoints
│   │   ├── services/         # Business logic
│   │   ├── dependencies.py   # Dependencies
│   │   └── permissions.py    # Permission definitions
│   ├── migrations/           # Alembic migrations
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                  # Frontend components
│   ├── module.js             # Module entry point
│   ├── manifest.json         # Frontend manifest
│   ├── pages/                # Page components
│   ├── components/           # Reusable UI components
│   ├── services/             # API clients
│   ├── styles/               # CSS/styles
│   └── assets/               # Images, icons
│
├── docs/                      # Documentation
│   ├── API.md
│   ├── SETUP.md
│   └── CUSTOMIZATION.md
│
├── scripts/                   # Utility scripts
│   ├── install.sh
│   └── seed-data.sh
│
└── kubernetes/                # K8s deployment configs
    ├── deployment.yaml
    ├── service.yaml
    └── ingress.yaml
```

### Module Manifest (manifest.json)

```json
{
  "name": "financial",
  "display_name": "Financial Management",
  "version": "1.2.0",
  "description": "Complete financial management system",

  "repository": {
    "type": "git",
    "url": "https://github.com/company/financial-module.git",
    "branch": "main"
  },

  "author": {
    "name": "Your Company",
    "email": "support@company.com",
    "website": "https://company.com"
  },

  "backend": {
    "type": "microservice",
    "runtime": "python:3.11",
    "framework": "fastapi",
    "entry_point": "app.main:app",
    "health_check": "/health",
    "api_prefix": "/api/v1/financial",
    "port": 8001
  },

  "frontend": {
    "type": "spa-module",
    "framework": "vanilla-js",
    "entry_point": "module.js",
    "bundle": "dist/financial.bundle.js"
  },

  "database": {
    "type": "postgresql",
    "schema_prefix": "financial_",
    "has_migrations": true,
    "requires_separate_db": false,
    "tables": [
      "financial_accounts",
      "financial_transactions",
      "financial_invoices"
    ]
  },

  "dependencies": {
    "platform_version": ">=2.0.0",
    "required_modules": [],
    "optional_modules": ["reporting", "notifications"],
    "external_services": ["redis", "postgresql"]
  },

  "permissions": [...],
  "routes": [...],
  "configuration": {...},

  "subscription_tier": "premium",
  "license": "proprietary",
  "category": "finance",
  "tags": ["accounting", "invoicing", "finance"]
}
```

---

## Backend Architecture

### 1. Independent Microservices

Each module runs as a separate FastAPI service:

```python
# backend/app/main.py (in module repo)

from fastapi import FastAPI, Depends
from app.routers import accounts, transactions, invoices
from app.core.auth import verify_module_token
from app.core.config import settings

app = FastAPI(
    title=f"{settings.MODULE_NAME} API",
    version=settings.MODULE_VERSION,
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "module": settings.MODULE_NAME,
        "version": settings.MODULE_VERSION
    }

# Register routers
app.include_router(
    accounts.router,
    prefix="/api/v1/financial/accounts",
    tags=["accounts"],
    dependencies=[Depends(verify_module_token)]
)

app.include_router(
    transactions.router,
    prefix="/api/v1/financial/transactions",
    tags=["transactions"],
    dependencies=[Depends(verify_module_token)]
)

# Module registration on startup
@app.on_event("startup")
async def register_with_platform():
    """Register this module instance with core platform"""
    await register_module_instance(
        module_name=settings.MODULE_NAME,
        instance_url=settings.MODULE_URL,
        health_check_url=f"{settings.MODULE_URL}/health"
    )
```

### 2. Database Strategy

**Option A: Shared Database with Schema Isolation**
- Each module has its own schema prefix (e.g., `financial_`, `warehouse_`)
- All modules connect to same PostgreSQL instance
- Cheaper, easier to manage
- Good for smaller deployments

```python
# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = f"postgresql://{user}:{password}@{host}/{database}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

**Option B: Separate Databases Per Module** (Recommended for large scale)
- Complete data isolation
- Independent scaling
- Better security
- More complex to manage

```python
# Each module has its own database
DATABASE_URL = f"postgresql://{user}:{password}@{host}/financial_module"
```

### 3. Inter-Service Communication

**REST API Calls**
```python
# app/services/platform_client.py
import httpx
from app.core.config import settings

class PlatformClient:
    def __init__(self):
        self.base_url = settings.CORE_PLATFORM_URL
        self.api_key = settings.MODULE_API_KEY

    async def get_company(self, company_id: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/companies/{company_id}",
                headers={"X-Module-API-Key": self.api_key}
            )
            return response.json()

    async def verify_permission(self, user_id: str, permission: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/rbac/verify",
                json={"user_id": user_id, "permission": permission},
                headers={"X-Module-API-Key": self.api_key}
            )
            return response.json()["has_permission"]
```

**Event-Driven Communication** (for async operations)
```python
# Using RabbitMQ or Redis Pub/Sub
from app.core.events import event_bus

# Publish event
await event_bus.publish(
    "financial.invoice.created",
    {
        "invoice_id": invoice.id,
        "tenant_id": invoice.tenant_id,
        "amount": invoice.total
    }
)

# Subscribe to events
@event_bus.subscribe("core.company.created")
async def handle_company_created(event_data):
    # Create default financial accounts for new company
    await create_default_accounts(event_data["company_id"])
```

### 4. Authentication & Authorization

Modules authenticate requests using:

1. **JWT tokens from core platform** (passed through API Gateway)
2. **Module API keys** (for inter-service communication)

```python
# app/core/auth.py
from fastapi import HTTPException, Header
from jose import JWTError, jwt
from app.core.config import settings

async def verify_access_token(authorization: str = Header(...)):
    """Verify JWT token from core platform"""
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401)

        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401)

async def verify_permission(
    permission: str,
    current_user: dict = Depends(verify_access_token)
):
    """Check if user has required permission"""
    platform_client = PlatformClient()
    has_perm = await platform_client.verify_permission(
        current_user["user_id"],
        permission
    )
    if not has_perm:
        raise HTTPException(status_code=403)
    return current_user
```

---

## Frontend Architecture Options

### Option 1: Integrated SPA Modules (Recommended for MVP)

**Architecture:**
- Core platform serves a shell application
- Modules are loaded dynamically as ES6 modules
- Shared component library
- Single-page experience

**Pros:**
- Simpler to implement
- Better UX (no page reloads)
- Shared state management
- Easier authentication

**Cons:**
- Tighter coupling
- All modules must use same framework
- Build process dependency

**Implementation:**

```javascript
// Core platform's module loader
class ModuleLoader {
    async loadModule(moduleName) {
        // Fetch module manifest
        const manifest = await fetch(`/api/v1/modules/${moduleName}/manifest`).then(r => r.json());

        // Load module bundle
        const module = await import(manifest.frontend.bundle_url);

        // Initialize module
        const moduleInstance = new module.default(manifest);
        await moduleInstance.init();

        // Register routes
        this.registerRoutes(manifest.routes, moduleInstance);

        return moduleInstance;
    }
}

// Module structure (in separate repo)
// financial-module/frontend/module.js
export default class FinancialModule {
    constructor(manifest) {
        this.manifest = manifest;
        this.config = {};
    }

    async init() {
        // Initialize module
        console.log('Financial module loaded');
    }

    async loadPage(pageName, container) {
        const PageClass = await import(`./pages/${pageName}.js`);
        const page = new PageClass(this.config);
        await page.render(container);
    }
}
```

### Option 2: Micro-Frontends (Full Independence)

**Architecture:**
- Each module is a complete standalone frontend
- Loaded via iframe or Web Components
- Complete framework freedom
- Module-to-module communication via events

**Pros:**
- Complete independence
- Any framework (React, Vue, Svelte, vanilla)
- Isolated deployments
- Team autonomy

**Cons:**
- More complex
- Potential UX inconsistencies
- Duplicated dependencies
- More difficult shared state

**Implementation:**

```javascript
// Core platform shell
class MicroFrontendLoader {
    loadModule(moduleName, containerEl) {
        // Option A: Web Components
        const moduleComponent = document.createElement('module-financial');
        moduleComponent.setAttribute('tenant-id', currentTenant);
        containerEl.appendChild(moduleComponent);

        // Option B: iframe
        const iframe = document.createElement('iframe');
        iframe.src = `${moduleServiceUrl}/ui?tenant=${tenantId}&token=${token}`;
        containerEl.appendChild(iframe);
    }
}

// Financial module serves its own UI
// Each module is a complete SPA at https://financial-service.com/ui
```

### Option 3: Hybrid Approach (Recommended for Scale)

**Architecture:**
- Core modules: Integrated (Option 1)
- Third-party/custom modules: Micro-frontends (Option 2)
- Progressive enhancement

**Benefits:**
- Balance between integration and independence
- Flexibility for different use cases
- Better DX for core modules, freedom for extensions

---

## Module Registry & Discovery

### Core Platform Module Registry Service

```python
# Core platform: app/services/module_registry.py

class ModuleRegistryService:
    """Manages module registration and discovery"""

    async def register_module_instance(
        self,
        module_name: str,
        instance_url: str,
        health_check_url: str
    ):
        """Register a running module instance"""
        # Store in registry
        await self.redis.hset(
            f"module:instances:{module_name}",
            instance_url,
            json.dumps({
                "url": instance_url,
                "health_check": health_check_url,
                "last_seen": datetime.utcnow().isoformat(),
                "status": "healthy"
            })
        )

    async def discover_module(self, module_name: str) -> str:
        """Get healthy instance URL for a module"""
        instances = await self.redis.hgetall(f"module:instances:{module_name}")

        # Health check and return healthy instance
        for instance_url, data in instances.items():
            if await self.check_health(json.loads(data)["health_check"]):
                return instance_url

        raise ModuleNotAvailableError(module_name)

    async def install_module(
        self,
        repository_url: str,
        version: str = "latest"
    ):
        """Install a module from repository"""
        # 1. Clone repository
        repo_path = await self.clone_repository(repository_url, version)

        # 2. Read manifest
        manifest = await self.read_manifest(repo_path)

        # 3. Validate manifest
        await self.validate_manifest(manifest)

        # 4. Check dependencies
        await self.check_dependencies(manifest)

        # 5. Register in database
        module = await self.db.create_module_registry(manifest)

        # 6. Deploy module (K8s/Docker)
        await self.deploy_module(module, repo_path)

        # 7. Run migrations
        await self.run_migrations(module)

        # 8. Register permissions
        await self.register_permissions(manifest.permissions)

        return module
```

### API Gateway Integration

```python
# API Gateway routes requests to appropriate module

class ModuleRouter:
    def __init__(self):
        self.registry = ModuleRegistryService()

    async def route_request(self, request: Request):
        # Parse path: /api/v1/financial/accounts -> module: financial
        module_name = self.extract_module_from_path(request.url.path)

        # Discover module instance
        instance_url = await self.registry.discover_module(module_name)

        # Forward request
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=f"{instance_url}{request.url.path}",
                headers=request.headers,
                content=await request.body()
            )

        return response
```

---

## Installation & Lifecycle

### Installation Flow

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Module Discovery                                          │
│    - Browse module marketplace/registry                      │
│    - Or provide Git repository URL                           │
└────────────────────────┬─────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. Pre-Installation Validation                               │
│    - Check platform compatibility                            │
│    - Verify dependencies                                     │
│    - Check subscription tier requirements                    │
└────────────────────────┬─────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. Installation (Platform-Level)                             │
│    - Clone repository                                        │
│    - Build Docker image                                      │
│    - Deploy container/pod                                    │
│    - Run database migrations                                 │
│    - Register permissions                                    │
│    - Store in ModuleRegistry                                 │
└────────────────────────┬─────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. Tenant Activation                                         │
│    - Enable module for tenant                                │
│    - Configure tenant-specific settings                      │
│    - Create tenant data (if needed)                          │
│    - Store in TenantModule table                             │
└────────────────────────┬─────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. Company Customization (Optional)                          │
│    - Apply company-specific configuration                    │
│    - Override tenant defaults                                │
│    - Store in CompanyModule table (new)                      │
└──────────────────────────────────────────────────────────────┘
```

### Module Lifecycle Hooks

```python
# Module can implement lifecycle hooks

class FinancialModule:
    async def pre_install(self, context: InstallContext) -> bool:
        """Called before module installation"""
        # Check if database schema is compatible
        return True

    async def post_install(self, context: InstallContext):
        """Called after module installation"""
        # Create default data
        await self.create_default_chart_of_accounts()

    async def pre_enable_tenant(self, tenant_id: str) -> bool:
        """Called before enabling for tenant"""
        # Check tenant subscription level
        tenant = await get_tenant(tenant_id)
        return tenant.subscription_tier in ['premium', 'enterprise']

    async def post_enable_tenant(self, tenant_id: str):
        """Called after enabling for tenant"""
        # Create tenant-specific data
        pass

    async def pre_enable_company(self, company_id: str) -> bool:
        """Called before enabling for company"""
        return True

    async def post_enable_company(self, company_id: str):
        """Called after enabling for company"""
        # Initialize company accounts
        await self.init_company_accounts(company_id)
```

---

## Customization Levels

### 3-Tier Customization Model

```
┌─────────────────────────────────────────────────────────────┐
│ Level 1: Module Defaults (manifest.json)                    │
│ - Default configuration                                     │
│ - Cannot be changed without module update                   │
└────────────────────────┬────────────────────────────────────┘
                         │ Overridden by ▼
┌─────────────────────────────────────────────────────────────┐
│ Level 2: Tenant Configuration (TenantModule.configuration)  │
│ - Tenant-wide settings                                      │
│ - Set by tenant admin                                       │
│ - Applies to all companies in tenant                        │
└────────────────────────┬────────────────────────────────────┘
                         │ Overridden by ▼
┌─────────────────────────────────────────────────────────────┐
│ Level 3: Company Configuration (CompanyModule.configuration)│
│ - Company-specific overrides                                │
│ - Set by company admin                                      │
│ - Highest priority                                          │
└─────────────────────────────────────────────────────────────┘
```

### New Database Model: CompanyModule

```python
# backend/app/models/company_module.py

class CompanyModule(Base):
    """
    Company-level module configuration and customization.
    Allows each company within a tenant to have custom module settings.
    """
    __tablename__ = "company_modules"

    id = Column(GUID, primary_key=True, default=generate_uuid)

    # Foreign keys
    company_id = Column(GUID, ForeignKey("companies.id"), nullable=False, index=True)
    tenant_module_id = Column(GUID, ForeignKey("tenant_modules.id"), nullable=False, index=True)

    # Customization
    is_enabled = Column(Boolean, default=True, nullable=False)  # Can disable at company level
    configuration = Column(JSON, nullable=True)  # Company-specific config overrides

    # Feature toggles
    enabled_features = Column(JSON, nullable=True)  # ["invoicing", "payments"]
    disabled_features = Column(JSON, nullable=True)  # ["reporting"]

    # Customization tracking
    customized_at = Column(DateTime, nullable=True)
    customized_by_user_id = Column(GUID, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    company = relationship("Company", backref="company_modules")
    tenant_module = relationship("TenantModule", backref="company_modules")
    customized_by = relationship("User", foreign_keys=[customized_by_user_id])
```

### Configuration Resolution Logic

```python
# app/services/config_resolver.py

class ModuleConfigResolver:
    """Resolves module configuration across tenant/company levels"""

    async def get_config(
        self,
        module_name: str,
        tenant_id: str,
        company_id: str = None
    ) -> dict:
        # 1. Get module defaults
        module = await self.get_module_registry(module_name)
        config = module.manifest.get("configuration", {}).get("defaults", {})

        # 2. Apply tenant configuration
        tenant_module = await self.get_tenant_module(module.id, tenant_id)
        if tenant_module and tenant_module.configuration:
            config = self.deep_merge(config, tenant_module.configuration)

        # 3. Apply company configuration (if specified)
        if company_id:
            company_module = await self.get_company_module(
                tenant_module.id,
                company_id
            )
            if company_module and company_module.configuration:
                config = self.deep_merge(config, company_module.configuration)

        return config

    def deep_merge(self, base: dict, override: dict) -> dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.deep_merge(result[key], value)
            else:
                result[key] = value
        return result
```

### Example: Configuration in Action

```python
# Module Default (manifest.json)
{
  "configuration": {
    "defaults": {
      "currency": "USD",
      "tax_rate": 0,
      "invoice_prefix": "INV",
      "payment_terms_days": 30
    }
  }
}

# Tenant Configuration (TenantModule.configuration)
{
  "currency": "EUR",
  "tax_rate": 0.20,
  "invoice_prefix": "ACME"
}

# Company Configuration (CompanyModule.configuration)
{
  "tax_rate": 0.19,  # German VAT for German subsidiary
  "invoice_prefix": "ACME-DE"
}

# Final resolved config for this company:
{
  "currency": "EUR",           # From tenant
  "tax_rate": 0.19,            # From company (overrides tenant)
  "invoice_prefix": "ACME-DE", # From company (overrides tenant)
  "payment_terms_days": 30     # From module default
}
```

---

## Communication Patterns

### 1. Synchronous: REST API

**Use for:** Direct queries, CRUD operations

```python
# Module calls core platform
async def get_user_info(user_id: str):
    client = PlatformClient()
    return await client.get(f"/api/v1/users/{user_id}")

# Core platform calls module
async def get_invoice(invoice_id: str):
    module_url = await registry.discover_module("financial")
    return await http_client.get(f"{module_url}/api/v1/financial/invoices/{invoice_id}")
```

### 2. Asynchronous: Event Bus

**Use for:** Notifications, background tasks, data sync

```python
# Publisher (Financial module)
await event_bus.publish("financial.invoice.paid", {
    "invoice_id": "123",
    "tenant_id": "tenant-1",
    "amount": 1000.00
})

# Subscriber (Notification module)
@event_bus.subscribe("financial.invoice.paid")
async def send_payment_notification(event):
    await send_email(
        to=event.customer_email,
        subject="Payment Received",
        template="payment_confirmation"
    )

# Subscriber (Reporting module)
@event_bus.subscribe("financial.invoice.paid")
async def update_revenue_report(event):
    await update_revenue_metrics(event.tenant_id, event.amount)
```

### 3. GraphQL Federation (Advanced)

**Use for:** Unified API, complex data requirements

```graphql
# Financial module schema
type Invoice {
  id: ID!
  number: String!
  customer: Customer! @provides(fields: "id")
  total: Float!
}

extend type Company {
  invoices: [Invoice!]!
}

# Core platform stitches schemas together
```

---

## Security & Isolation

### 1. Data Isolation

```python
# Every query MUST filter by tenant_id
@router.get("/invoices")
async def list_invoices(
    company_id: str,
    current_user: User = Depends(get_current_user)
):
    # Verify user has access to company
    if not await verify_company_access(current_user.id, company_id):
        raise HTTPException(403)

    # ALWAYS filter by tenant
    invoices = db.query(Invoice).filter(
        Invoice.tenant_id == current_user.tenant_id,
        Invoice.company_id == company_id
    ).all()

    return invoices
```

### 2. Module Authentication

```python
# Module-to-module authentication
class ModuleAuthMiddleware:
    async def __call__(self, request: Request, call_next):
        # Verify module API key
        api_key = request.headers.get("X-Module-API-Key")
        if not await self.verify_module_key(api_key):
            raise HTTPException(401)

        # Add module context
        request.state.calling_module = await self.get_module_by_key(api_key)

        return await call_next(request)
```

### 3. Permission Isolation

```python
# Module can only create permissions in its namespace
ALLOWED_PERMISSION_PREFIX = "financial:"

async def register_permission(permission_code: str):
    if not permission_code.startswith(ALLOWED_PERMISSION_PREFIX):
        raise ValueError(f"Permission must start with {ALLOWED_PERMISSION_PREFIX}")

    # Register permission
    await create_permission(permission_code)
```

---

## Deployment Strategy

### Development Environment

```yaml
# docker-compose.yml (for local development)

version: '3.8'

services:
  # Core platform
  core-platform:
    build: ./core-platform
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres/platform
      - REDIS_URL=redis://redis:6379

  # Financial module
  financial-module:
    build: ./financial-module/backend
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres/platform
      - CORE_PLATFORM_URL=http://core-platform:8000
      - MODULE_API_KEY=${FINANCIAL_MODULE_API_KEY}

  # Warehouse module
  warehouse-module:
    build: ./warehouse-module/backend
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres/platform
      - CORE_PLATFORM_URL=http://core-platform:8000
      - MODULE_API_KEY=${WAREHOUSE_MODULE_API_KEY}

  # Shared services
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: platform
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass

  redis:
    image: redis:7-alpine

  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
```

### Production: Kubernetes

```yaml
# kubernetes/financial-module/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: financial-module
  namespace: modules
spec:
  replicas: 3
  selector:
    matchLabels:
      app: financial-module
  template:
    metadata:
      labels:
        app: financial-module
        version: v1.2.0
    spec:
      containers:
      - name: financial-api
        image: registry.company.com/financial-module:1.2.0
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: financial-db-secret
              key: url
        - name: CORE_PLATFORM_URL
          value: "http://core-platform-service"
        - name: MODULE_API_KEY
          valueFrom:
            secretKeyRef:
              name: financial-module-secret
              key: api-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: financial-module-service
  namespace: modules
spec:
  selector:
    app: financial-module
  ports:
  - port: 80
    targetPort: 8001
  type: ClusterIP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: financial-module-hpa
  namespace: modules
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: financial-module
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Migration Path

### Phase 1: Preparation (Weeks 1-2)

1. **Update Core Platform:**
   - Add CompanyModule model
   - Enhance Module Registry Service
   - Implement API Gateway routing
   - Set up event bus (RabbitMQ/Redis)

2. **Create Module Template:**
   - Repository structure
   - Dockerfile template
   - CI/CD pipeline
   - Documentation

### Phase 2: Extract First Module (Weeks 3-4)

1. **Financial Module → Separate Repo:**
   - Create new repository
   - Set up independent backend service
   - Implement module registration
   - Test inter-service communication

2. **Deploy as Microservice:**
   - Dockerize
   - Deploy alongside core platform
   - Verify functionality

### Phase 3: Frontend Strategy Decision (Week 5)

1. **Evaluate Options:**
   - Test integrated modules (Option 1)
   - Test micro-frontends (Option 2)
   - Choose approach based on team size, complexity

2. **Implement Chosen Strategy:**
   - Update module loader
   - Migrate frontend code
   - Test UX

### Phase 4: Scale (Weeks 6-12)

1. **Extract Remaining Modules:**
   - One module at a time
   - Warehouse, CRM, etc.

2. **Implement Marketplace:**
   - Module discovery UI
   - Installation workflow
   - Configuration UI

3. **Documentation:**
   - Developer guide
   - API documentation
   - Deployment guides

---

## Recommendations

### For Your Use Case:

1. **Backend: Separate Microservices** ✅
   - Each module in own repo
   - Independent deployment
   - Use shared database with schema prefixes (easier to start)
   - Can migrate to separate DBs later

2. **Frontend: Start with Integrated Modules** ✅
   - Simpler implementation
   - Better UX
   - Can migrate to micro-frontends later if needed

3. **Communication:**
   - REST for synchronous
   - RabbitMQ for async events
   - Redis for caching/registry

4. **Customization:**
   - Implement 3-tier model (Module → Tenant → Company)
   - Use CompanyModule table

5. **Deployment:**
   - Docker Compose for dev
   - Kubernetes for production
   - One namespace per module

---

## Next Steps

1. **Review this design** with your team
2. **Make key decisions:**
   - Frontend architecture (Option 1 vs 2 vs 3)
   - Database strategy (shared vs separate)
   - Event bus technology
3. **Create proof of concept:**
   - Extract one module (Financial)
   - Test end-to-end flow
4. **Iterate and refine**
5. **Scale to all modules**

---

## Questions to Answer

1. **Frontend:** Which option works best for your team/scale?
2. **Database:** Shared with schema isolation, or fully separate DBs?
3. **Event Bus:** RabbitMQ, Kafka, or Redis Pub/Sub?
4. **Deployment:** Docker Compose, Kubernetes, or cloud-native (ECS, Cloud Run)?
5. **Module Marketplace:** Internal only, or allow third-party modules?

---

**This architecture provides a clear path to true modularity while maintaining your existing multi-tenancy and RBAC systems.**
