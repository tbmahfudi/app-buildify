# Financial Module - Complete Setup Guide

This guide walks you through setting up the Financial Module with sample data for a demo tenant.

## Prerequisites

- Docker and Docker Compose installed
- Git repository cloned locally

## Quick Start (5 Minutes)

### Step 1: Start All Services

```bash
cd /path/to/app-buildify

# Start services
docker-compose up -d

# Wait for services to be ready (about 30 seconds)
docker-compose ps
```

### Step 2: Run Database Migrations

```bash
# Enter the financial module container
docker exec -it buildify-financial bash

# Run Alembic migrations
cd /app
alembic upgrade head

# Exit container
exit
```

### Step 3: Setup Sample Data

```bash
# Run the setup script
docker exec -it buildify-financial python setup_sample_data.py
```

This will create:
- ✅ **50 accounts** - Default chart of accounts
- ✅ **2 tax rates** - VAT and Sales Tax
- ✅ **3 customers** - Sample companies
- ✅ **3 invoices** - With line items and tax
- ✅ **2 payments** - Customer payments
- ✅ **1 journal entry** - Opening balance

### Step 4: Access the API

Open your browser to:
- **API Documentation:** http://localhost:9001/docs
- **Health Check:** http://localhost:9001/health

## Sample Data Created

### Tenant & Company

```
Tenant ID:  tenant-demo-001
Company ID: company-acme-corp
User ID:    user-admin-001
```

### Customers

| Customer Number | Name | Credit Limit | Payment Terms |
|----------------|------|--------------|---------------|
| CUST-001 | Acme Corporation | $50,000 | 30 days |
| CUST-002 | TechCorp Industries | $75,000 | 15 days |
| CUST-003 | Global Solutions Ltd | $100,000 | 30 days |

### Invoices

| Invoice Number | Customer | Amount | Status | Due Date |
|---------------|----------|---------|--------|----------|
| INV-2025-001 | Acme Corporation | $8,031.25 | sent | Today |
| INV-2025-002 | TechCorp Industries | $10,750.00 | sent | +15 days |
| INV-2025-003 | Global Solutions Ltd | $2,148.43 | draft | +25 days |

### Payments

| Payment Number | Customer | Amount | Method | Status |
|---------------|----------|---------|--------|--------|
| PMT-2025-001 | Acme Corporation | $3,000 | Bank Transfer | cleared |
| PMT-2025-002 | TechCorp Industries | $5,000 | Check | pending |

## Testing the API

### 1. List All Accounts

```bash
curl "http://localhost:9001/api/v1/accounts?tenant_id=tenant-demo-001&company_id=company-acme-corp"
```

### 2. Get Chart of Accounts Tree

```bash
curl "http://localhost:9001/api/v1/accounts/tree?tenant_id=tenant-demo-001&company_id=company-acme-corp"
```

### 3. List Customers

```bash
curl "http://localhost:9001/api/v1/customers?tenant_id=tenant-demo-001&company_id=company-acme-corp"
```

### 4. List Invoices

```bash
curl "http://localhost:9001/api/v1/invoices?tenant_id=tenant-demo-001&company_id=company-acme-corp"
```

### 5. Get Trial Balance Report

```bash
curl "http://localhost:9001/api/v1/reports/trial-balance?tenant_id=tenant-demo-001&company_id=company-acme-corp&as_of_date=2025-12-31"
```

### 6. Get Balance Sheet

```bash
curl "http://localhost:9001/api/v1/reports/balance-sheet?tenant_id=tenant-demo-001&company_id=company-acme-corp&as_of_date=2025-12-31"
```

### 7. Get Income Statement

```bash
curl "http://localhost:9001/api/v1/reports/income-statement?tenant_id=tenant-demo-001&company_id=company-acme-corp&from_date=2025-01-01&to_date=2025-12-31"
```

## Using the API with Query Parameters

All endpoints require these query parameters:
- `tenant_id` - Tenant identifier
- `company_id` - Company identifier

Example:
```bash
GET http://localhost:9001/api/v1/customers?tenant_id=tenant-demo-001&company_id=company-acme-corp
```

## Create New Records via API

### Create a New Customer

```bash
curl -X POST "http://localhost:9001/api/v1/customers" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-demo-001",
    "company_id": "company-acme-corp",
    "customer_number": "CUST-004",
    "name": "New Customer Inc",
    "email": "billing@newcustomer.com",
    "payment_terms_days": 30,
    "credit_limit": 25000,
    "created_by": "user-admin-001"
  }'
```

### Create a New Invoice

```bash
curl -X POST "http://localhost:9001/api/v1/invoices" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-demo-001",
    "company_id": "company-acme-corp",
    "customer_id": "<customer-id>",
    "invoice_number": "INV-2025-004",
    "invoice_date": "2025-12-01",
    "due_date": "2025-12-31",
    "created_by": "user-admin-001",
    "line_items": [
      {
        "line_number": 1,
        "description": "Consulting Services",
        "quantity": 10,
        "unit_price": 150,
        "tax_percentage": 7.5
      }
    ]
  }'
```

### Record a Payment

```bash
curl -X POST "http://localhost:9001/api/v1/payments" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-demo-001",
    "company_id": "company-acme-corp",
    "customer_id": "<customer-id>",
    "payment_number": "PMT-2025-003",
    "payment_date": "2025-12-01",
    "payment_method": "bank_transfer",
    "payment_amount": 1000,
    "deposit_account_id": "<cash-account-id>",
    "created_by": "user-admin-001"
  }'
```

## Viewing Data in Database

```bash
# Access PostgreSQL
docker exec -it buildify-postgres psql -U postgres -d buildify

# List all financial tables
\dt financial_*

# View customers
SELECT customer_number, name, current_balance FROM financial_customers;

# View invoices
SELECT invoice_number, total_amount, balance_due, status FROM financial_invoices;

# View accounts
SELECT code, name, current_balance FROM financial_accounts ORDER BY code;

# Exit
\q
```

## Troubleshooting

### Services not starting

```bash
# Check logs
docker-compose logs financial-module

# Restart services
docker-compose restart financial-module
```

### Database connection errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check database URL in config
docker exec buildify-financial env | grep DATABASE
```

### Migration errors

```bash
# Check current migration version
docker exec buildify-financial alembic current

# View migration history
docker exec buildify-financial alembic history

# Downgrade and re-run
docker exec buildify-financial alembic downgrade -1
docker exec buildify-financial alembic upgrade head
```

### Reset all data

```bash
# Stop services
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Start fresh
docker-compose up -d
docker exec -it buildify-financial alembic upgrade head
docker exec -it buildify-financial python setup_sample_data.py
```

## Integration with Core Platform

The Financial Module is designed to integrate with the core platform:

1. **Authentication**: Uses shared JWT tokens
2. **Multi-tenancy**: Tenant/company isolation
3. **Event Bus**: PostgreSQL LISTEN/NOTIFY for real-time updates
4. **API Gateway**: Nginx routes `/api/v1/financial/*` to the module

## Next Steps

1. **Explore the API**: Visit http://localhost:9001/docs
2. **Test Reports**: Generate financial reports
3. **Create Workflows**: Test invoice → payment → journal entry flow
4. **Customize Data**: Modify `setup_sample_data.py` for your needs
5. **Frontend**: Access the UI at http://localhost:8080/financial

## Production Considerations

Before deploying to production:

1. **Change Secrets**: Update JWT keys and database passwords
2. **Configure Backups**: Set up automated database backups
3. **Enable SSL**: Configure HTTPS for all endpoints
4. **Monitor Logs**: Set up log aggregation and monitoring
5. **Scale Services**: Configure horizontal scaling if needed
6. **Security Review**: Review permissions and access controls

## Support

For issues or questions:
- API Documentation: http://localhost:9001/docs
- Module Status: http://localhost:9001/health
- Logs: `docker-compose logs -f financial-module`
