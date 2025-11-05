# Financial Module Setup Guide

The financial module was discovered and synced with the database during app startup. However, it needs to be **installed** (platform-wide) and **enabled** (per-tenant) before it can be used.

## Current Status

✅ Module discovered: `financial` v1.0.0
❌ Module installed: No (needs to be installed)
❌ Module enabled: No (needs to be enabled for a tenant)

## Module Activation Workflow

```
1. Discover & Sync (✓ Done at startup)
   └─> Module appears in database but is not usable yet

2. Install Platform-wide (Requires Superuser)
   └─> POST /api/v1/modules/install
   └─> Makes module available to all tenants
   └─> Registers permissions in the database

3. Enable for Tenant (Requires Tenant Admin)
   └─> POST /api/v1/modules/enable
   └─> Activates module for specific tenant
   └─> Creates tenant-specific configuration
```

## Setup Methods

### Method 1: Using API Endpoints (Recommended)

```bash
# 1. Login as superuser to get auth token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-admin@email.com",
    "password": "your-password"
  }'

# Copy the "access_token" from response
export TOKEN="your_access_token_here"

# 2. Check available modules
curl -X GET http://localhost:8000/api/v1/modules/available \
  -H "Authorization: Bearer $TOKEN"

# 3. Install the financial module (superuser only)
curl -X POST http://localhost:8000/api/v1/modules/install \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"module_name": "financial"}'

# 4. Enable module for your tenant
curl -X POST http://localhost:8000/api/v1/modules/enable \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "financial",
    "configuration": {
      "default_currency": "USD",
      "fiscal_year_start": "01-01",
      "enable_multi_currency": false,
      "tax_rate": 0,
      "invoice_prefix": "INV"
    }
  }'

# 5. Verify enabled modules
curl -X GET http://localhost:8000/api/v1/modules/enabled/names \
  -H "Authorization: Bearer $TOKEN"

# Should return: ["financial"]
```

### Method 2: Using Setup Script

```bash
# Run the automated setup script
./setup_financial_module.sh YOUR_AUTH_TOKEN
```

### Method 3: Direct Database Script (if running in container)

```bash
# If you have access to the container environment
python3 backend/install_financial.py
```

## Verification

After setup, these endpoints should work:

```bash
# Module health check
curl -X GET http://localhost:8000/api/v1/financial/health \
  -H "Authorization: Bearer $TOKEN"

# List financial accounts
curl -X GET http://localhost:8000/api/v1/financial/accounts \
  -H "Authorization: Bearer $TOKEN"

# Get enabled modules (should return ["financial"])
curl -X GET http://localhost:8000/api/v1/modules/enabled/names \
  -H "Authorization: Bearer $TOKEN"
```

## Available Endpoints

Once enabled, the financial module provides:

- **Accounts**: `/api/v1/financial/accounts`
  - Chart of accounts management
  - Account types: Asset, Liability, Equity, Revenue, Expense

- **Invoices**: `/api/v1/financial/invoices`
  - Create and manage invoices
  - Track invoice status (draft, sent, paid, overdue)
  - Generate invoice PDFs

- **Transactions**: `/api/v1/financial/transactions`
  - Record financial transactions
  - Double-entry bookkeeping
  - Journal entries

- **Payments**: `/api/v1/financial/payments`
  - Record payments against invoices
  - Track payment methods
  - Payment reconciliation

- **Reports**: `/api/v1/financial/reports`
  - Balance sheet
  - Income statement (P&L)
  - Cash flow statement
  - Trial balance

## Configuration Options

The module can be configured per-tenant:

```json
{
  "default_currency": "USD",           // Default currency code
  "fiscal_year_start": "01-01",        // Fiscal year start (MM-DD)
  "enable_multi_currency": false,      // Enable multiple currencies
  "tax_rate": 10.0,                    // Default tax rate percentage
  "invoice_prefix": "INV"              // Invoice number prefix
}
```

## Permissions

The module registers these permissions:

- `financial:accounts:*` - Manage chart of accounts
- `financial:transactions:*` - Manage transactions
- `financial:invoices:*` - Manage invoices
- `financial:payments:*` - Manage payments
- `financial:reports:*` - View/export reports

Default roles:
- **Financial Manager**: Full access
- **Accountant**: Accounts, transactions, reports
- **Billing Clerk**: Invoices and payments
- **Financial Viewer**: Read-only access

## Troubleshooting

**Q: `/api/v1/modules/enabled/names` returns empty array**
A: The module needs to be installed and enabled. Follow the setup steps above.

**Q: Getting "Module system not initialized" error**
A: The app needs to be restarted to initialize the module system.

**Q: Getting "Module requires premium subscription tier"**
A: The financial module requires a premium or enterprise subscription. Update your tenant's subscription tier in the database.

**Q: Installation fails with "Module already installed"**
A: The module is installed but may not be enabled for your tenant. Run step 4 (enable) only.

## Next Steps

After enabling the financial module:

1. Create your chart of accounts
2. Set up customers and vendors
3. Create your first invoice
4. Record transactions
5. Generate financial reports
