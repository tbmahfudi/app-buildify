# Financial Module

## Overview

The Financial module is a fully implemented, self-contained FastAPI microservice that adds financial management capabilities to App-Buildify. It ships with complete double-entry bookkeeping, invoicing, payments, and financial reporting.

**Status**: Production Ready (v1.0.0)
**Port**: 9001
**API prefix**: `/api/v1/financial/`

---

## Features

| Feature | Status |
|---------|--------|
| Chart of Accounts (hierarchical) | ✅ Implemented |
| Customer management | ✅ Implemented |
| Invoicing with status workflow | ✅ Implemented |
| Payment recording and allocation | ✅ Implemented |
| Journal entries (double-entry) | ✅ Implemented |
| Tax rate management | ✅ Implemented |
| Trial Balance report | ✅ Implemented |
| Balance Sheet report | ✅ Implemented |
| Income Statement (P&L) | ✅ Implemented |
| Aged Receivables report | ✅ Implemented |
| Cash Flow Statement | ✅ Implemented |
| Account Ledger | ✅ Implemented |
| Frontend pages (6) | ✅ Implemented |
| PostgreSQL event bus integration | ✅ Implemented |

---

## Module Structure

```
modules/financial/
├── manifest.json                   # Module registration manifest
├── Dockerfile                      # Module container
├── SETUP_GUIDE.md                  # Setup instructions
├── setup_tenants.sh                # Tenant setup script
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app factory
│   │   ├── config.py               # Settings (DATABASE_STRATEGY, etc.)
│   │   ├── models/
│   │   │   ├── account.py          # Chart of accounts
│   │   │   ├── customer.py         # Customer master data
│   │   │   ├── invoice.py          # Invoices and line items
│   │   │   ├── journal_entry.py    # Double-entry journal
│   │   │   ├── payment.py          # Payments and allocations
│   │   │   └── tax_rate.py         # Tax rates
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── account_service.py       # Account CRUD, hierarchy, balances
│   │   │   ├── chart_setup_service.py   # Default chart templates (50 accounts)
│   │   │   ├── customer_service.py      # Customer CRUD, credit limits
│   │   │   ├── invoice_service.py       # Invoice lifecycle, payment application
│   │   │   ├── journal_entry_service.py # Double-entry posting and reversal
│   │   │   ├── payment_service.py       # Payment recording, allocation, voiding
│   │   │   ├── report_service.py        # All financial reports
│   │   │   └── tax_rate_service.py      # Tax rate management and calculation
│   │   └── routers/
│   │       ├── accounts.py         # 10 endpoints
│   │       ├── customers.py        # 8 endpoints
│   │       ├── invoices.py         # 7 endpoints
│   │       ├── journal_entries.py  # 7 endpoints
│   │       ├── payments.py         # 9 endpoints
│   │       ├── reports.py          # 6 endpoints
│   │       └── tax_rates.py        # 7 endpoints
│   ├── alembic/                    # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/
    ├── module.js                   # Module registration + routes
    ├── pages/
    │   ├── accounts.js
    │   ├── customers.js
    │   ├── invoices.js
    │   ├── journal-entries.js
    │   ├── payments.js
    │   └── reports.js
    ├── components/
    │   ├── data-table.js           # Reusable data table
    │   └── form-builder.js         # Reusable form builder
    └── styles/
        └── financial.css
```

---

## API Endpoints

All endpoints are prefixed `/api/v1/financial/`.

### Accounts

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/accounts` | List chart of accounts |
| `POST` | `/accounts` | Create account |
| `GET` | `/accounts/{id}` | Get account |
| `PUT` | `/accounts/{id}` | Update account |
| `DELETE` | `/accounts/{id}` | Delete account |
| `GET` | `/accounts/hierarchy` | Get hierarchical chart |
| `GET` | `/accounts/{id}/balance` | Get account balance |
| `POST` | `/accounts/setup/default` | Install default chart (50 accounts) |
| `GET` | `/accounts/types` | List account types |
| `GET` | `/accounts/search` | Search accounts |

### Customers

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/customers` | List customers |
| `POST` | `/customers` | Create customer |
| `GET` | `/customers/{id}` | Get customer |
| `PUT` | `/customers/{id}` | Update customer |
| `DELETE` | `/customers/{id}` | Delete customer |
| `GET` | `/customers/{id}/balance` | Get outstanding balance |
| `GET` | `/customers/{id}/invoices` | Get customer invoices |
| `GET` | `/customers/overdue` | List customers with overdue invoices |

### Invoices

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/invoices` | List invoices |
| `POST` | `/invoices` | Create invoice |
| `GET` | `/invoices/{id}` | Get invoice with line items |
| `PUT` | `/invoices/{id}` | Update invoice |
| `DELETE` | `/invoices/{id}` | Delete draft invoice |
| `POST` | `/invoices/{id}/post` | Post (finalize) invoice |
| `POST` | `/invoices/{id}/void` | Void invoice |

**Invoice status flow**: `DRAFT` → `POSTED` → `PARTIALLY_PAID` → `PAID` (or `VOID`)

### Payments

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/payments` | List payments |
| `POST` | `/payments` | Record payment |
| `GET` | `/payments/{id}` | Get payment detail |
| `PUT` | `/payments/{id}` | Update payment |
| `DELETE` | `/payments/{id}` | Delete payment |
| `POST` | `/payments/{id}/allocate` | Allocate to invoices |
| `POST` | `/payments/{id}/clear` | Clear/match payment |
| `POST` | `/payments/{id}/void` | Void payment |
| `GET` | `/payments/unallocated` | List unallocated payments |

### Journal Entries

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/journal-entries` | List journal entries |
| `POST` | `/journal-entries` | Create journal entry |
| `GET` | `/journal-entries/{id}` | Get entry with lines |
| `PUT` | `/journal-entries/{id}` | Update draft entry |
| `DELETE` | `/journal-entries/{id}` | Delete draft entry |
| `POST` | `/journal-entries/{id}/post` | Post entry to accounts |
| `POST` | `/journal-entries/{id}/reverse` | Create reversal entry |

### Tax Rates

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/tax-rates` | List tax rates |
| `POST` | `/tax-rates` | Create tax rate |
| `GET` | `/tax-rates/{id}` | Get tax rate |
| `PUT` | `/tax-rates/{id}` | Update tax rate |
| `DELETE` | `/tax-rates/{id}` | Delete tax rate |
| `GET` | `/tax-rates/active` | List active rates |
| `POST` | `/tax-rates/calculate` | Calculate tax for amount |

### Reports

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/reports/trial-balance` | Trial balance report |
| `GET` | `/reports/balance-sheet` | Balance sheet |
| `GET` | `/reports/income-statement` | Profit & Loss statement |
| `GET` | `/reports/aged-receivables` | Aged receivables aging |
| `GET` | `/reports/cash-flow` | Cash flow statement |
| `GET` | `/reports/account-ledger/{id}` | Account ledger with running balance |

---

## Database Strategy

The module supports two database strategies, controlled by `DATABASE_STRATEGY`:

| Strategy | Value | Description |
|----------|-------|-------------|
| **Shared** | `shared` (default) | Module tables in the core platform database |
| **Separate** | `separate` | Module uses its own dedicated database |

### Shared (Default)

```env
DATABASE_STRATEGY=shared
DATABASE_URL=postgresql://appuser:apppass@postgres:5432/appdb
```

All financial tables are created in the core database with no schema prefix.

### Separate

```env
DATABASE_STRATEGY=separate
MODULE_DATABASE_URL=postgresql://appuser:apppass@financial-db:5432/financial
```

---

## Event Bus Integration

The financial module integrates with the core platform's PostgreSQL event bus:

```env
EVENT_BUS_CONNECTION_STRING=postgresql://appuser:apppass@postgres:5432/appdb
```

Events published by the financial module:
- `financial.invoice.created`
- `financial.invoice.posted`
- `financial.invoice.paid`
- `financial.payment.recorded`
- `financial.journal.posted`

Events consumed:
- `tenant.created` — initialize default chart of accounts
- `company.created` — set up company-level financial configuration

---

## Frontend Integration

The module registers itself via `frontend/module.js`:

```javascript
// Routes added to the core platform router
const routes = [
  { path: '#/financial/accounts', page: 'pages/accounts.js', permission: 'financial:accounts:read:company' },
  { path: '#/financial/customers', page: 'pages/customers.js', permission: 'financial:customers:read:company' },
  { path: '#/financial/invoices', page: 'pages/invoices.js', permission: 'financial:invoices:read:company' },
  { path: '#/financial/payments', page: 'pages/payments.js', permission: 'financial:payments:read:company' },
  { path: '#/financial/journal-entries', page: 'pages/journal-entries.js', permission: 'financial:journal:read:company' },
  { path: '#/financial/reports', page: 'pages/reports.js', permission: 'financial:reports:read:company' },
]
```

Frontend assets are served via Nginx from:
```
/modules/financial/pages/accounts.js
/modules/financial/styles/financial.css
```

---

## Permissions

All financial permissions use the format `financial:<resource>:<action>:<scope>`.

| Permission | Description |
|-----------|-------------|
| `financial:accounts:read:company` | View chart of accounts |
| `financial:accounts:write:company` | Create/update accounts |
| `financial:customers:read:company` | View customers |
| `financial:customers:write:company` | Manage customers |
| `financial:invoices:read:company` | View invoices |
| `financial:invoices:write:company` | Create/update invoices |
| `financial:invoices:post:company` | Post/finalize invoices |
| `financial:payments:read:company` | View payments |
| `financial:payments:write:company` | Record payments |
| `financial:journal:read:company` | View journal entries |
| `financial:journal:post:company` | Post journal entries |
| `financial:reports:read:company` | View financial reports |
| `financial:*:*:company` | Full financial access |

---

## Setup

```bash
# Start the financial module
docker-compose -f infra/docker-compose.dev.yml up -d financial-module

# Run financial module migrations
docker-compose exec financial-module alembic upgrade head

# Set up default chart of accounts for a tenant
POST /api/v1/financial/accounts/setup/default
  { "tenant_id": "<uuid>", "template": "standard" }
```

---

## Related Documents

- [Module Development Guide](../MODULE_DEVELOPMENT_GUIDE.md)
- [Module Registration](../MODULE_REGISTRATION.md)
- [RBAC System](../backend/RBAC.md)
