# Quick Start: Module System

## Why `/api/v1/modules/enabled/names` Returns Empty Array

The module system has a **2-step activation process**:

1. **Install** (platform-wide) ← You need to do this
2. **Enable** (per-tenant) ← And this

## Quick Setup (5 minutes)

### Step 1: Get Your Auth Token

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}'

# Save the access_token
export TOKEN="your_token_here"
```

### Step 2: Install Module (Superuser Only)

```bash
curl -X POST http://localhost:8000/api/v1/modules/install \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"module_name":"financial"}'
```

### Step 3: Enable for Your Tenant

```bash
curl -X POST http://localhost:8000/api/v1/modules/enable \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"module_name":"financial"}'
```

### Step 4: Verify

```bash
curl -X GET http://localhost:8000/api/v1/modules/enabled/names \
  -H "Authorization: Bearer $TOKEN"

# Should return: ["financial"]
```

## All-in-One Script

```bash
./setup_financial_module.sh $TOKEN
```

## What You Get

After setup, these endpoints become available:

```
GET  /api/v1/financial/health
GET  /api/v1/financial/accounts
POST /api/v1/financial/accounts
GET  /api/v1/financial/invoices
POST /api/v1/financial/invoices
GET  /api/v1/financial/transactions
POST /api/v1/financial/transactions
GET  /api/v1/financial/payments
POST /api/v1/financial/payments
GET  /api/v1/financial/reports
```

## Module System Architecture

```
📁 /app/modules/
├── financial/                    ← Your module
│   ├── manifest.json            ← Module metadata & config
│   ├── module.py                ← Main module class (FinancialModule)
│   ├── models/                  ← SQLAlchemy models
│   ├── routers/                 ← API endpoints
│   ├── schemas/                 ← Pydantic schemas
│   └── permissions.py           ← Permission definitions
│
└── your-new-module/             ← Add new modules here
    ├── manifest.json            ← Required
    ├── module.py                ← Required (inherit from BaseModule)
    └── ...                      ← Your code

App startup:
1. ModuleLoader discovers modules
2. Validates manifest.json & module.py
3. Syncs with database (module_registries table)
4. Loads installed modules into memory
5. Registers routers for enabled modules
```

## Creating a New Module

See: `FINANCIAL_MODULE_SETUP.md` for full documentation

```bash
# 1. Create module directory
mkdir backend/modules/my-module

# 2. Create manifest.json
# 3. Create module.py (inherit from BaseModule)
# 4. Restart app (auto-discovers new module)
# 5. Install & enable via API
```

## Useful Commands

```bash
# List all available modules
curl http://localhost:8000/api/v1/modules/available \
  -H "Authorization: Bearer $TOKEN"

# Get module details
curl http://localhost:8000/api/v1/modules/financial \
  -H "Authorization: Bearer $TOKEN"

# List enabled modules for your tenant
curl http://localhost:8000/api/v1/modules/enabled \
  -H "Authorization: Bearer $TOKEN"

# Disable module
curl -X POST http://localhost:8000/api/v1/modules/disable \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"module_name":"financial"}'

# Update module configuration
curl -X PUT http://localhost:8000/api/v1/modules/financial/configuration \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"configuration":{"default_currency":"EUR"}}'
```

## For More Details

- Full setup guide: `FINANCIAL_MODULE_SETUP.md`
- Code reference:
  - `backend/app/core/module_system/` - Module system core
  - `backend/modules/financial/` - Financial module implementation
  - `backend/app/routers/modules.py` - Module management API
