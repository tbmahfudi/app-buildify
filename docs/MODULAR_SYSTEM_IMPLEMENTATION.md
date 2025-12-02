# Modular System Implementation Guide

## Overview

This document describes the **complete modular architecture implementation** for the Buildify platform, where modules are developed in separate directories (ready to be moved to separate repositories), run their own backend services, and can be customized at tenant and company levels.

## What We've Built

### ✅ Core Infrastructure

1. **CompanyModule Database Model** - Company-level module customization
2. **PostgreSQL Event Bus** - Minimal event-driven architecture
3. **Module Registry Service** - Module lifecycle management
4. **API Gateway** - Nginx-based request routing
5. **Frontend Module Loader** - Dynamic module loading (Option 1: Integrated SPA)

### ✅ Modules Directory Structure

```
modules/
└── financial/              # Sample module (ready to move to own repo)
    ├── manifest.json       # Module metadata
    ├── backend/            # Independent FastAPI service
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app/
    │       ├── main.py     # FastAPI application
    │       ├── config.py   # Configuration (shared/separate DB)
    │       ├── core/
    │       │   ├── database.py
    │       │   └── event_handler.py
    │       ├── routers/    # API endpoints
    │       ├── models/     # Database models
    │       ├── schemas/    # Pydantic schemas
    │       └── services/   # Business logic
    └── frontend/           # Frontend module
        ├── module.js       # Module class
        ├── pages/          # Page components
        ├── components/     # UI components
        └── services/       # API clients
```

### ✅ Deployment Configuration

- **Docker Compose** for multi-service deployment
- **Nginx API Gateway** for intelligent routing
- **Database Strategy** toggle (shared vs separate DB)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                       Nginx API Gateway                      │
│  - Routes /api/v1/financial/* -> Financial Module            │
│  - Routes /api/v1/* -> Core Platform                         │
│  - Rate limiting & security                                  │
└────────────────┬───────────────────────┬────────────────────┘
                 │                       │
    ┌────────────▼─────────┐  ┌─────────▼─────────────┐
    │   Core Platform      │  │  Financial Module     │
    │   (FastAPI:8000)     │  │  (FastAPI:8001)       │
    │   - User management  │  │  - Accounts           │
    │   - RBAC             │  │  - Invoices           │
    │   - Module Registry  │  │  - Payments           │
    │   - Event Bus        │  │  - Reports            │
    └────────────┬─────────┘  └─────────┬─────────────┘
                 │                       │
                 └───────────┬───────────┘
                             │
                  ┌──────────▼──────────┐
                  │    PostgreSQL       │
                  │  - Event Bus        │
                  │  - Shared/Separate  │
                  └─────────────────────┘
```

---

## Key Features

### 1. Database Strategy

Modules support **two database strategies** via configuration:

#### **Shared Database** (Default - Simpler)
```env
DATABASE_STRATEGY=shared
DATABASE_URL=postgresql://user:pass@postgres/buildify
SCHEMA_PREFIX=financial_
```

**Pros:**
- Single database to manage
- Easier backups and maintenance
- Lower cost
- Simpler for small-medium deployments

**Tables:**
- `financial_accounts`
- `financial_transactions`
- `financial_invoices`

#### **Separate Database** (Scalable)
```env
DATABASE_STRATEGY=separate
MODULE_DATABASE_URL=postgresql://user:pass@postgres/financial_module
```

**Pros:**
- Complete data isolation
- Independent scaling
- Better security
- Can use different database versions

### 2. 3-Tier Configuration Model

Configuration is resolved in this order:

```
Module Defaults (manifest.json)
         ↓ (overridden by)
Tenant Configuration (TenantModule.configuration)
         ↓ (overridden by)
Company Configuration (CompanyModule.configuration)
```

**Example:**

```javascript
// Module Default
{
  "currency": "USD",
  "tax_rate": 0,
  "invoice_prefix": "INV"
}

// Tenant Override (European company)
{
  "currency": "EUR",
  "tax_rate": 0.20
}

// Company Override (German subsidiary)
{
  "tax_rate": 0.19,  // German VAT
  "invoice_prefix": "DE-INV"
}

// Final Result for this company
{
  "currency": "EUR",           // From tenant
  "tax_rate": 0.19,            // From company
  "invoice_prefix": "DE-INV"   // From company
}
```

### 3. PostgreSQL Event Bus

Minimal event-driven architecture using PostgreSQL:

**Features:**
- Unlogged tables for performance
- LISTEN/NOTIFY for real-time delivery
- Background polling for reliability
- Pattern matching for subscriptions
- Automatic cleanup

**Publishing Events:**
```python
from app.core.event_bus import EventPublisher

publisher = EventPublisher(db_session)
await publisher.publish(
    event_type="financial.invoice.created",
    payload={"invoice_id": "123", "total": 1000.00},
    tenant_id=tenant_id,
    company_id=company_id
)
```

**Subscribing to Events:**
```python
from app.core.event_bus import EventSubscriber, EventHandler

subscriber = EventSubscriber(db, "financial-module", conn_str)
handler = EventHandler(subscriber)

@handler.on("core.company.created", priority=8)
async def handle_company_created(event):
    company_id = event['payload']['company_id']
    await create_default_accounts(company_id)

await subscriber.start_listening()
```

### 4. Frontend Module Loader

**Dynamic Module Loading (Option 1: Integrated SPA)**

Modules are loaded dynamically as ES6 modules for seamless UX:

```javascript
// In core platform
const moduleLoader = new ModuleLoader();

// Load enabled modules
await moduleLoader.loadEnabledModules();

// Navigate to module page
moduleLoader.navigate('financial/dashboard');
```

**Module Structure:**
```javascript
export default class FinancialModule {
    async init() {
        // Initialize module
    }

    cleanup() {
        // Cleanup resources
    }
}
```

---

## Deployment

### Development (Docker Compose)

1. **Start all services:**
```bash
docker-compose up -d
```

2. **Services:**
- Core Platform: http://localhost:8000
- Financial Module: http://localhost:8001
- API Gateway: http://localhost
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432
- Redis: localhost:6379

3. **View logs:**
```bash
docker-compose logs -f financial-module
```

### Configuration

**Environment Variables:**

```env
# Database Strategy
DATABASE_STRATEGY=shared  # or 'separate'

# Shared Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/buildify

# Separate Database (if strategy=separate)
MODULE_DATABASE_URL=postgresql://postgres:postgres@postgres:5432/financial_module

# Core Platform Integration
CORE_PLATFORM_URL=http://core-platform:8000
MODULE_API_KEY=financial-module-secret-key

# Event Bus
EVENT_BUS_CONNECTION_STRING=postgresql://postgres:postgres@postgres:5432/buildify

# JWT (shared with core)
JWT_SECRET_KEY=your-secret-key-change-in-production
```

---

## Module Development

### Creating a New Module

1. **Create Directory Structure:**
```bash
mkdir -p modules/warehouse/{backend,frontend,docs}
mkdir -p modules/warehouse/backend/app/{models,routers,services}
mkdir -p modules/warehouse/frontend/{pages,components}
```

2. **Create manifest.json:**
```json
{
  "name": "warehouse",
  "display_name": "Warehouse Management",
  "version": "1.0.0",
  "backend": {
    "type": "microservice",
    "api_prefix": "/api/v1/warehouse",
    "port": 8002
  },
  "database": {
    "strategy": "shared",
    "schema_prefix": "warehouse_"
  }
}
```

3. **Create Backend Service:**
```python
# backend/app/main.py
from fastapi import FastAPI

app = FastAPI(title="Warehouse Module")

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

4. **Add to Docker Compose:**
```yaml
warehouse-module:
  build: ./modules/warehouse/backend
  ports:
    - "8002:8002"
  environment:
    - DATABASE_STRATEGY=shared
```

5. **Update Nginx Config:**
```nginx
location /api/v1/warehouse/ {
    proxy_pass http://warehouse-module:8002;
}
```

### Module Lifecycle

**1. Development:**
```bash
cd modules/financial/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**2. Registration:**
```python
# Register module in database
await module_registry.register_module(manifest)
```

**3. Tenant Activation:**
```python
# Enable for tenant
await module_registry.enable_for_tenant(
    module_name="financial",
    tenant_id=tenant_id,
    configuration={"currency": "EUR"}
)
```

**4. Company Customization:**
```python
# Customize for company
await module_registry.enable_for_company(
    module_name="financial",
    company_id=company_id,
    tenant_id=tenant_id,
    configuration={"invoice_prefix": "ACME-"}
)
```

---

## API Gateway Routing

Nginx intelligently routes requests based on URL path:

| Request Path | Routed To | Service |
|--------------|-----------|---------|
| `/` | Frontend | Vite Dev Server |
| `/api/v1/financial/*` | Financial Module | :8001 |
| `/api/v1/warehouse/*` | Warehouse Module | :8002 |
| `/api/v1/*` | Core Platform | :8000 |
| `/health/financial` | Financial Health | :8001/health |

**Features:**
- Rate limiting (100 req/sec)
- CORS handling
- Security headers
- Health check aggregation

---

## Database Schema

### Core Tables

```sql
-- Company module configuration
CREATE TABLE company_modules (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    tenant_module_id UUID NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    configuration JSONB,
    enabled_features JSONB,
    disabled_features JSONB,
    customized_at TIMESTAMP,
    customized_by_user_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Event bus tables
CREATE UNLOGGED TABLE events (
    id UUID PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    event_source VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    tenant_id UUID NOT NULL,
    company_id UUID,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

CREATE TABLE event_subscriptions (
    id UUID PRIMARY KEY,
    module_name VARCHAR(100) NOT NULL,
    event_pattern VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 5,
    callback_url VARCHAR(500)
);
```

---

## Testing

### Test Module Endpoints

```bash
# Health check
curl http://localhost:8001/health

# List accounts
curl http://localhost/api/v1/financial/accounts?company_id=123 \
  -H "Authorization: Bearer $TOKEN"

# Create invoice
curl -X POST http://localhost/api/v1/financial/invoices \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"company_id": "123", "customer": "Acme Corp", "total": 1500}'
```

### Test Event Bus

```python
# Publish event
await publisher.publish(
    event_type="financial.invoice.created",
    payload={"invoice_id": "inv-123"},
    tenant_id=tenant_id
)

# Verify in database
SELECT * FROM events WHERE event_type = 'financial.invoice.created';
```

---

## Migration Path

### Moving Module to Separate Repository

1. **Create new repository:**
```bash
git init financial-module
```

2. **Copy module files:**
```bash
cp -r modules/financial/* financial-module/
```

3. **Update manifest.json:**
```json
{
  "repository": {
    "url": "https://github.com/company/financial-module.git"
  }
}
```

4. **Deploy independently:**
```bash
cd financial-module
docker build -t financial-module:latest .
docker push registry.company.com/financial-module:latest
```

5. **Update docker-compose.yml:**
```yaml
financial-module:
  image: registry.company.com/financial-module:latest
```

---

## Troubleshooting

### Module Not Loading

1. Check module is enabled for tenant:
```sql
SELECT * FROM tenant_modules WHERE tenant_id = '...' AND is_enabled = TRUE;
```

2. Check health endpoint:
```bash
curl http://localhost:8001/health
```

3. Check docker logs:
```bash
docker-compose logs financial-module
```

### Database Connection Issues

1. Test connection:
```bash
docker exec -it buildify-postgres psql -U postgres -d buildify
```

2. Verify environment variables:
```bash
docker exec buildify-financial env | grep DATABASE
```

### Event Bus Not Working

1. Check events table:
```sql
SELECT * FROM events ORDER BY created_at DESC LIMIT 10;
```

2. Check subscriptions:
```sql
SELECT * FROM event_subscriptions WHERE is_active = TRUE;
```

3. Test LISTEN/NOTIFY:
```sql
LISTEN events;
NOTIFY events, 'test';
```

---

## Next Steps

1. **Add More Modules:**
   - Warehouse Management
   - CRM
   - HR Management

2. **Enhance Event Bus:**
   - Add retry logic
   - Implement dead letter queue
   - Add monitoring dashboard

3. **Production Deployment:**
   - Kubernetes deployment
   - CI/CD pipeline
   - Monitoring and logging

4. **Module Marketplace:**
   - Module discovery UI
   - Installation workflow
   - Version management

---

## Resources

- [Module Development Guide](./MODULE_DEVELOPMENT_GUIDE.md)
- [Modular Architecture Design](./MODULAR_ARCHITECTURE_DESIGN.md)
- [PostgreSQL Event Bus Design](./POSTGRES_EVENT_BUS_DESIGN.md)
- [Docker Compose Configuration](../docker-compose.yml)

---

**Congratulations! You now have a fully functional modular architecture!** 🎉

Modules can be developed independently, deployed as microservices, and customized at tenant/company levels.
