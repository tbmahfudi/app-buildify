# Database Migrations

This directory contains Alembic database migrations for the Financial Module.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/dbname"
# OR for shared database with schema prefix
export DATABASE_STRATEGY="shared"
export CORE_DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/dbname"
```

## Creating Migrations

### Auto-generate migration from model changes:
```bash
cd /path/to/modules/financial/backend
alembic revision --autogenerate -m "Description of changes"
```

### Create empty migration:
```bash
alembic revision -m "Description of changes"
```

## Running Migrations

### Upgrade to latest version:
```bash
alembic upgrade head
```

### Upgrade one version:
```bash
alembic upgrade +1
```

### Downgrade one version:
```bash
alembic downgrade -1
```

### View current version:
```bash
alembic current
```

### View migration history:
```bash
alembic history
```

## Initial Migration

The initial migration creates all Financial Module tables:

- `financial_accounts` - Chart of accounts
- `financial_customers` - Customer master data
- `financial_journal_entries` - Journal entry headers
- `financial_journal_entry_lines` - Journal entry lines
- `financial_invoices` - Customer invoices
- `financial_invoice_line_items` - Invoice line items
- `financial_payments` - Customer payments
- `financial_payment_allocations` - Payment allocations to invoices
- `financial_tax_rates` - Tax rate definitions

All tables include:
- Multi-tenancy support (tenant_id, company_id)
- Audit fields (created_by, updated_by, created_at, updated_at)
- Appropriate indexes and constraints

## Database Strategy

The module supports two database strategies:

1. **Separate Database** (`DATABASE_STRATEGY=separate`):
   - Module has its own database
   - Use `DATABASE_URL` environment variable

2. **Shared Database** (`DATABASE_STRATEGY=shared`):
   - Module shares database with core platform
   - Tables prefixed with `financial_`
   - Use `CORE_DATABASE_URL` environment variable

The effective database URL is determined by the `DATABASE_STRATEGY` setting in config.

## Notes

- Migrations are version controlled
- Always review auto-generated migrations before running them
- Test migrations on development environment first
- Backup production database before running migrations
