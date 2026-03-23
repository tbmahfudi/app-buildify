# Financial Module - Functional Design

## Table of Contents

- [Overview](#overview)
- [Database Schema Design](#database-schema-design)
- [API Endpoint Specifications](#api-endpoint-specifications)
- [Service Layer Design](#service-layer-design)
- [Pydantic Schemas](#pydantic-schemas)
- [Business Rules & Validation](#business-rules--validation)
- [Event System Design](#event-system-design)
- [Frontend Component Design](#frontend-component-design)
- [Security & Permissions](#security--permissions)
- [Implementation Checklist](#implementation-checklist)

---

## Overview

The Financial Module provides comprehensive financial management capabilities including:
- **Chart of Accounts** - Account structure and management
- **Journal Entries** - Double-entry bookkeeping
- **Invoicing** - Sales invoices and accounts receivable
- **Payments** - Payment processing and recording
- **Financial Reports** - Balance sheet, P&L, trial balance
- **Multi-currency** - Support for multiple currencies
- **Tax Management** - Tax calculations and tracking

---

## Database Schema Design

### 1. **Accounts Table** (`financial_accounts`)

```sql
CREATE TABLE financial_accounts (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Multi-tenancy (REQUIRED)
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Account identification
    code VARCHAR(50) NOT NULL,              -- e.g., "1000", "1000-01"
    name VARCHAR(255) NOT NULL,             -- e.g., "Cash", "Bank Account"
    description TEXT,

    -- Account classification
    type VARCHAR(50) NOT NULL,              -- asset, liability, equity, revenue, expense
    category VARCHAR(100),                  -- cash, receivables, fixed_assets, etc.
    sub_category VARCHAR(100),              -- bank_accounts, petty_cash, etc.

    -- Account properties
    is_active BOOLEAN DEFAULT TRUE,
    is_header BOOLEAN DEFAULT FALSE,        -- Header/parent account (no transactions)
    parent_account_id UUID REFERENCES financial_accounts(id),

    -- Balance tracking
    current_balance NUMERIC(18, 2) DEFAULT 0.00,
    debit_balance NUMERIC(18, 2) DEFAULT 0.00,
    credit_balance NUMERIC(18, 2) DEFAULT 0.00,

    -- Currency
    currency_code VARCHAR(3) DEFAULT 'USD',

    -- Additional properties
    tax_category VARCHAR(50),               -- taxable, non_taxable, tax_exempt
    requires_department BOOLEAN DEFAULT FALSE,
    requires_project BOOLEAN DEFAULT FALSE,

    -- Metadata
    extra_data JSONB,                       -- Custom fields

    -- Audit
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,

    -- Constraints
    CONSTRAINT uq_account_code UNIQUE (tenant_id, company_id, code),
    CONSTRAINT chk_account_type CHECK (type IN ('asset', 'liability', 'equity', 'revenue', 'expense')),
    CONSTRAINT chk_balance CHECK (
        (type IN ('asset', 'expense') AND current_balance = debit_balance - credit_balance)
        OR (type IN ('liability', 'equity', 'revenue') AND current_balance = credit_balance - debit_balance)
    )
);

CREATE INDEX idx_accounts_tenant_company ON financial_accounts(tenant_id, company_id);
CREATE INDEX idx_accounts_type ON financial_accounts(type);
CREATE INDEX idx_accounts_parent ON financial_accounts(parent_account_id);
CREATE INDEX idx_accounts_active ON financial_accounts(is_active) WHERE is_active = TRUE;
```

---

### 2. **Journal Entries Table** (`financial_journal_entries`)

```sql
CREATE TABLE financial_journal_entries (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Multi-tenancy
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Entry identification
    entry_number VARCHAR(50) NOT NULL,      -- Auto-generated: JE-2024-0001
    reference_number VARCHAR(100),          -- External reference

    -- Entry details
    entry_date DATE NOT NULL,
    posting_date DATE,

    -- Description
    description TEXT NOT NULL,
    memo TEXT,

    -- Status
    status VARCHAR(20) DEFAULT 'draft',     -- draft, posted, reversed, void
    is_posted BOOLEAN DEFAULT FALSE,
    posted_at TIMESTAMP,
    posted_by UUID REFERENCES users(id),

    -- Reversal tracking
    is_reversal BOOLEAN DEFAULT FALSE,
    reversed_entry_id UUID REFERENCES financial_journal_entries(id),
    reversed_at TIMESTAMP,
    reversed_by UUID REFERENCES users(id),

    -- Source tracking
    source_type VARCHAR(50),                -- manual, invoice, payment, adjustment
    source_id UUID,                         -- ID of source document

    -- Totals
    total_debit NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    total_credit NUMERIC(18, 2) NOT NULL DEFAULT 0.00,

    -- Currency
    currency_code VARCHAR(3) DEFAULT 'USD',

    -- Metadata
    tags JSONB,
    extra_data JSONB,

    -- Audit
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,

    -- Constraints
    CONSTRAINT uq_entry_number UNIQUE (tenant_id, company_id, entry_number),
    CONSTRAINT chk_entry_status CHECK (status IN ('draft', 'posted', 'reversed', 'void')),
    CONSTRAINT chk_balanced CHECK (total_debit = total_credit)
);

CREATE INDEX idx_journal_entries_tenant_company ON financial_journal_entries(tenant_id, company_id);
CREATE INDEX idx_journal_entries_date ON financial_journal_entries(entry_date);
CREATE INDEX idx_journal_entries_status ON financial_journal_entries(status);
CREATE INDEX idx_journal_entries_source ON financial_journal_entries(source_type, source_id);
```

---

### 3. **Journal Entry Lines Table** (`financial_journal_entry_lines`)

```sql
CREATE TABLE financial_journal_entry_lines (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    journal_entry_id UUID NOT NULL REFERENCES financial_journal_entries(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES financial_accounts(id),

    -- Line details
    line_number INTEGER NOT NULL,
    description TEXT,

    -- Amounts
    debit_amount NUMERIC(18, 2) DEFAULT 0.00,
    credit_amount NUMERIC(18, 2) DEFAULT 0.00,

    -- Dimensions (optional)
    department_id UUID REFERENCES departments(id),
    project_id UUID,                        -- Reference to projects table if exists

    -- Metadata
    extra_data JSONB,

    -- Constraints
    CONSTRAINT chk_line_amount CHECK (
        (debit_amount > 0 AND credit_amount = 0) OR
        (credit_amount > 0 AND debit_amount = 0)
    )
);

CREATE INDEX idx_journal_lines_entry ON financial_journal_entry_lines(journal_entry_id);
CREATE INDEX idx_journal_lines_account ON financial_journal_entry_lines(account_id);
```

---

### 4. **Customers Table** (`financial_customers`)

```sql
CREATE TABLE financial_customers (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Multi-tenancy
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Customer identification
    customer_number VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),

    -- Contact information
    email VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(255),

    -- Address
    billing_address_line1 VARCHAR(255),
    billing_address_line2 VARCHAR(255),
    billing_city VARCHAR(100),
    billing_state VARCHAR(100),
    billing_postal_code VARCHAR(20),
    billing_country VARCHAR(100),

    shipping_address_line1 VARCHAR(255),
    shipping_address_line2 VARCHAR(255),
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(100),
    shipping_postal_code VARCHAR(20),
    shipping_country VARCHAR(100),

    -- Financial details
    currency_code VARCHAR(3) DEFAULT 'USD',
    payment_terms_days INTEGER DEFAULT 30,
    credit_limit NUMERIC(18, 2),

    -- Tax
    tax_id VARCHAR(50),
    tax_exempt BOOLEAN DEFAULT FALSE,

    -- Accounts
    receivables_account_id UUID REFERENCES financial_accounts(id),

    -- Balance tracking
    current_balance NUMERIC(18, 2) DEFAULT 0.00,
    overdue_balance NUMERIC(18, 2) DEFAULT 0.00,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Metadata
    notes TEXT,
    extra_data JSONB,

    -- Audit
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,

    -- Constraints
    CONSTRAINT uq_customer_number UNIQUE (tenant_id, company_id, customer_number)
);

CREATE INDEX idx_customers_tenant_company ON financial_customers(tenant_id, company_id);
CREATE INDEX idx_customers_name ON financial_customers(name);
CREATE INDEX idx_customers_email ON financial_customers(email);
```

---

### 5. **Invoices Table** (`financial_invoices`)

```sql
CREATE TABLE financial_invoices (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Multi-tenancy
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Invoice identification
    invoice_number VARCHAR(50) NOT NULL,    -- Auto-generated: INV-2024-0001
    reference_number VARCHAR(100),

    -- Customer
    customer_id UUID NOT NULL REFERENCES financial_customers(id),
    customer_name VARCHAR(255),             -- Denormalized for history

    -- Dates
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,

    -- Status
    status VARCHAR(20) DEFAULT 'draft',     -- draft, sent, partially_paid, paid, overdue, void

    -- Amounts
    subtotal NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    tax_amount NUMERIC(18, 2) DEFAULT 0.00,
    discount_amount NUMERIC(18, 2) DEFAULT 0.00,
    shipping_amount NUMERIC(18, 2) DEFAULT 0.00,
    total_amount NUMERIC(18, 2) NOT NULL,

    -- Payment tracking
    paid_amount NUMERIC(18, 2) DEFAULT 0.00,
    balance_due NUMERIC(18, 2) NOT NULL,

    -- Currency
    currency_code VARCHAR(3) DEFAULT 'USD',

    -- Terms
    payment_terms_days INTEGER DEFAULT 30,
    payment_terms_text TEXT,

    -- Notes
    notes TEXT,
    terms_and_conditions TEXT,

    -- Delivery
    sent_at TIMESTAMP,
    sent_by UUID REFERENCES users(id),

    -- Accounting
    journal_entry_id UUID REFERENCES financial_journal_entries(id),

    -- Metadata
    extra_data JSONB,

    -- Audit
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,

    -- Constraints
    CONSTRAINT uq_invoice_number UNIQUE (tenant_id, company_id, invoice_number),
    CONSTRAINT chk_invoice_status CHECK (status IN ('draft', 'sent', 'partially_paid', 'paid', 'overdue', 'void')),
    CONSTRAINT chk_invoice_amounts CHECK (
        total_amount = subtotal + tax_amount - discount_amount + shipping_amount
        AND balance_due = total_amount - paid_amount
    )
);

CREATE INDEX idx_invoices_tenant_company ON financial_invoices(tenant_id, company_id);
CREATE INDEX idx_invoices_customer ON financial_invoices(customer_id);
CREATE INDEX idx_invoices_status ON financial_invoices(status);
CREATE INDEX idx_invoices_date ON financial_invoices(invoice_date);
CREATE INDEX idx_invoices_due_date ON financial_invoices(due_date);
```

---

### 6. **Invoice Line Items Table** (`financial_invoice_line_items`)

```sql
CREATE TABLE financial_invoice_line_items (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign key
    invoice_id UUID NOT NULL REFERENCES financial_invoices(id) ON DELETE CASCADE,

    -- Line details
    line_number INTEGER NOT NULL,
    description TEXT NOT NULL,

    -- Product/Service (optional)
    product_id UUID,                        -- Reference to products table if exists
    product_code VARCHAR(50),

    -- Quantity and pricing
    quantity NUMERIC(10, 2) NOT NULL DEFAULT 1,
    unit_price NUMERIC(18, 2) NOT NULL,

    -- Amounts
    line_amount NUMERIC(18, 2) NOT NULL,    -- quantity * unit_price
    discount_percent NUMERIC(5, 2) DEFAULT 0,
    discount_amount NUMERIC(18, 2) DEFAULT 0,

    -- Tax
    tax_rate NUMERIC(5, 2) DEFAULT 0,
    tax_amount NUMERIC(18, 2) DEFAULT 0,

    -- Total
    total_amount NUMERIC(18, 2) NOT NULL,   -- line_amount - discount_amount + tax_amount

    -- Accounting
    revenue_account_id UUID REFERENCES financial_accounts(id),

    -- Metadata
    extra_data JSONB,

    -- Constraints
    CONSTRAINT chk_line_amounts CHECK (
        line_amount = quantity * unit_price
        AND total_amount = line_amount - discount_amount + tax_amount
    )
);

CREATE INDEX idx_invoice_lines_invoice ON financial_invoice_line_items(invoice_id);
CREATE INDEX idx_invoice_lines_product ON financial_invoice_line_items(product_id);
```

---

### 7. **Payments Table** (`financial_payments`)

```sql
CREATE TABLE financial_payments (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Multi-tenancy
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Payment identification
    payment_number VARCHAR(50) NOT NULL,    -- Auto-generated: PAY-2024-0001
    reference_number VARCHAR(100),

    -- Customer
    customer_id UUID NOT NULL REFERENCES financial_customers(id),

    -- Payment details
    payment_date DATE NOT NULL,
    payment_method VARCHAR(50),             -- cash, check, bank_transfer, credit_card, etc.

    -- Amount
    payment_amount NUMERIC(18, 2) NOT NULL,
    currency_code VARCHAR(3) DEFAULT 'USD',

    -- Bank details (if applicable)
    bank_account_id UUID,
    check_number VARCHAR(50),
    transaction_id VARCHAR(100),

    -- Status
    status VARCHAR(20) DEFAULT 'pending',   -- pending, completed, bounced, void

    -- Accounting
    deposit_to_account_id UUID NOT NULL REFERENCES financial_accounts(id),
    journal_entry_id UUID REFERENCES financial_journal_entries(id),

    -- Notes
    notes TEXT,

    -- Metadata
    extra_data JSONB,

    -- Audit
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,

    -- Constraints
    CONSTRAINT uq_payment_number UNIQUE (tenant_id, company_id, payment_number),
    CONSTRAINT chk_payment_status CHECK (status IN ('pending', 'completed', 'bounced', 'void')),
    CONSTRAINT chk_payment_method CHECK (payment_method IN ('cash', 'check', 'bank_transfer', 'credit_card', 'other'))
);

CREATE INDEX idx_payments_tenant_company ON financial_payments(tenant_id, company_id);
CREATE INDEX idx_payments_customer ON financial_payments(customer_id);
CREATE INDEX idx_payments_date ON financial_payments(payment_date);
CREATE INDEX idx_payments_status ON financial_payments(status);
```

---

### 8. **Payment Allocations Table** (`financial_payment_allocations`)

```sql
CREATE TABLE financial_payment_allocations (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    payment_id UUID NOT NULL REFERENCES financial_payments(id) ON DELETE CASCADE,
    invoice_id UUID NOT NULL REFERENCES financial_invoices(id) ON DELETE CASCADE,

    -- Allocation details
    allocated_amount NUMERIC(18, 2) NOT NULL,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_allocation_amount CHECK (allocated_amount > 0)
);

CREATE INDEX idx_payment_allocations_payment ON financial_payment_allocations(payment_id);
CREATE INDEX idx_payment_allocations_invoice ON financial_payment_allocations(invoice_id);
```

---

### 9. **Tax Rates Table** (`financial_tax_rates`)

```sql
CREATE TABLE financial_tax_rates (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Multi-tenancy
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Tax identification
    tax_code VARCHAR(50) NOT NULL,
    tax_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Rate
    tax_rate NUMERIC(5, 2) NOT NULL,        -- e.g., 10.00 for 10%

    -- Applicability
    is_active BOOLEAN DEFAULT TRUE,
    effective_from DATE,
    effective_to DATE,

    -- Accounting
    tax_payable_account_id UUID REFERENCES financial_accounts(id),

    -- Audit
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,

    -- Constraints
    CONSTRAINT uq_tax_code UNIQUE (tenant_id, company_id, tax_code)
);

CREATE INDEX idx_tax_rates_tenant_company ON financial_tax_rates(tenant_id, company_id);
CREATE INDEX idx_tax_rates_active ON financial_tax_rates(is_active) WHERE is_active = TRUE;
```

---

## API Endpoint Specifications

### **Accounts API** (`/api/v1/financial/accounts`)

#### **1. List Accounts**
```
GET /api/v1/financial/accounts

Query Parameters:
  - company_id: UUID (required)
  - type: string (optional) - Filter by account type
  - is_active: boolean (optional) - Filter active/inactive
  - search: string (optional) - Search by code or name
  - parent_id: UUID (optional) - Filter by parent account
  - page: integer (default: 1)
  - page_size: integer (default: 50)

Response: 200 OK
{
  "accounts": [
    {
      "id": "uuid",
      "code": "1000",
      "name": "Cash",
      "type": "asset",
      "category": "cash",
      "current_balance": 10000.00,
      "currency_code": "USD",
      "is_active": true,
      "is_header": false,
      "parent_account": {
        "id": "uuid",
        "code": "1000",
        "name": "Current Assets"
      }
    }
  ],
  "pagination": {
    "total": 100,
    "page": 1,
    "page_size": 50,
    "total_pages": 2
  }
}

Permissions: financial:accounts:read:company
```

#### **2. Get Account**
```
GET /api/v1/financial/accounts/{account_id}

Response: 200 OK
{
  "id": "uuid",
  "code": "1000",
  "name": "Cash",
  "description": "Main cash account",
  "type": "asset",
  "category": "cash",
  "sub_category": "bank_accounts",
  "current_balance": 10000.00,
  "debit_balance": 50000.00,
  "credit_balance": 40000.00,
  "currency_code": "USD",
  "is_active": true,
  "is_header": false,
  "parent_account_id": "uuid",
  "tax_category": "non_taxable",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}

Permissions: financial:accounts:read:company
```

#### **3. Create Account**
```
POST /api/v1/financial/accounts

Request Body:
{
  "company_id": "uuid",
  "code": "1001",
  "name": "Petty Cash",
  "description": "Petty cash for office expenses",
  "type": "asset",
  "category": "cash",
  "sub_category": "petty_cash",
  "parent_account_id": "uuid",
  "currency_code": "USD",
  "is_header": false,
  "tax_category": "non_taxable"
}

Response: 201 Created
{
  "id": "uuid",
  "code": "1001",
  "name": "Petty Cash",
  ...
}

Permissions: financial:accounts:create:company
Events: financial.account.created
```

#### **4. Update Account**
```
PUT /api/v1/financial/accounts/{account_id}

Request Body:
{
  "name": "Updated Account Name",
  "description": "Updated description",
  "is_active": false
}

Response: 200 OK
{
  "id": "uuid",
  ...
}

Permissions: financial:accounts:update:company
Events: financial.account.updated
```

#### **5. Delete Account**
```
DELETE /api/v1/financial/accounts/{account_id}

Response: 204 No Content

Permissions: financial:accounts:delete:company
Business Rules:
  - Cannot delete if account has transactions
  - Cannot delete if account has child accounts
Events: financial.account.deleted
```

#### **6. Get Account Balance**
```
GET /api/v1/financial/accounts/{account_id}/balance

Query Parameters:
  - as_of_date: date (optional) - Balance as of specific date

Response: 200 OK
{
  "account_id": "uuid",
  "current_balance": 10000.00,
  "debit_balance": 50000.00,
  "credit_balance": 40000.00,
  "as_of_date": "2024-01-31",
  "currency_code": "USD"
}

Permissions: financial:accounts:read:company
```

#### **7. Get Account Transactions**
```
GET /api/v1/financial/accounts/{account_id}/transactions

Query Parameters:
  - from_date: date (optional)
  - to_date: date (optional)
  - page: integer
  - page_size: integer

Response: 200 OK
{
  "account": {
    "id": "uuid",
    "code": "1000",
    "name": "Cash"
  },
  "opening_balance": 5000.00,
  "transactions": [
    {
      "date": "2024-01-15",
      "description": "Invoice payment",
      "debit": 1000.00,
      "credit": 0.00,
      "balance": 6000.00,
      "journal_entry_id": "uuid"
    }
  ],
  "closing_balance": 10000.00
}

Permissions: financial:accounts:read:company
```

---

### **Journal Entries API** (`/api/v1/financial/journal-entries`)

#### **1. List Journal Entries**
```
GET /api/v1/financial/journal-entries

Query Parameters:
  - company_id: UUID (required)
  - status: string (optional)
  - from_date: date (optional)
  - to_date: date (optional)
  - search: string (optional)
  - page: integer
  - page_size: integer

Response: 200 OK
{
  "entries": [
    {
      "id": "uuid",
      "entry_number": "JE-2024-0001",
      "entry_date": "2024-01-15",
      "description": "Month-end adjustments",
      "status": "posted",
      "total_debit": 5000.00,
      "total_credit": 5000.00,
      "created_by": {
        "id": "uuid",
        "name": "John Doe"
      },
      "posted_at": "2024-01-15T16:30:00Z"
    }
  ],
  "pagination": {...}
}

Permissions: financial:journal:read:company
```

#### **2. Create Journal Entry**
```
POST /api/v1/financial/journal-entries

Request Body:
{
  "company_id": "uuid",
  "entry_date": "2024-01-15",
  "description": "Office supplies purchase",
  "memo": "Invoice #12345",
  "lines": [
    {
      "account_id": "uuid",
      "description": "Office supplies",
      "debit_amount": 500.00,
      "credit_amount": 0.00,
      "department_id": "uuid"
    },
    {
      "account_id": "uuid",
      "description": "Cash payment",
      "debit_amount": 0.00,
      "credit_amount": 500.00
    }
  ]
}

Response: 201 Created
{
  "id": "uuid",
  "entry_number": "JE-2024-0001",
  "status": "draft",
  ...
}

Permissions: financial:journal:create:company
Business Rules:
  - Sum of debits must equal sum of credits
  - At least 2 lines required
  - All accounts must belong to the same company
Events: financial.journal_entry.created
```

#### **3. Post Journal Entry**
```
POST /api/v1/financial/journal-entries/{entry_id}/post

Response: 200 OK
{
  "id": "uuid",
  "status": "posted",
  "posted_at": "2024-01-15T16:30:00Z",
  "posted_by": {
    "id": "uuid",
    "name": "John Doe"
  }
}

Permissions: financial:journal:post:company
Business Rules:
  - Can only post entries in 'draft' status
  - Updates account balances
  - Cannot be edited after posting
Events: financial.journal_entry.posted
```

#### **4. Reverse Journal Entry**
```
POST /api/v1/financial/journal-entries/{entry_id}/reverse

Request Body:
{
  "reversal_date": "2024-01-31",
  "description": "Reversal of entry JE-2024-0001"
}

Response: 200 OK
{
  "original_entry_id": "uuid",
  "reversal_entry": {
    "id": "uuid",
    "entry_number": "JE-2024-0002",
    "status": "posted",
    "is_reversal": true,
    "reversed_entry_id": "uuid"
  }
}

Permissions: financial:journal:reverse:company
Business Rules:
  - Can only reverse posted entries
  - Creates new entry with opposite debits/credits
  - Both entries linked
Events: financial.journal_entry.reversed
```

---

### **Customers API** (`/api/v1/financial/customers`)

#### **1. List Customers**
```
GET /api/v1/financial/customers

Query Parameters:
  - company_id: UUID (required)
  - is_active: boolean
  - search: string
  - page: integer
  - page_size: integer

Response: 200 OK
{
  "customers": [
    {
      "id": "uuid",
      "customer_number": "CUST-0001",
      "name": "Acme Corporation",
      "email": "billing@acme.com",
      "phone": "+1-555-0100",
      "current_balance": 5000.00,
      "overdue_balance": 1000.00,
      "is_active": true
    }
  ],
  "pagination": {...}
}

Permissions: financial:customers:read:company
```

#### **2. Create Customer**
```
POST /api/v1/financial/customers

Request Body:
{
  "company_id": "uuid",
  "name": "Acme Corporation",
  "email": "billing@acme.com",
  "phone": "+1-555-0100",
  "billing_address_line1": "123 Main St",
  "billing_city": "New York",
  "billing_state": "NY",
  "billing_postal_code": "10001",
  "billing_country": "USA",
  "payment_terms_days": 30,
  "credit_limit": 50000.00,
  "currency_code": "USD"
}

Response: 201 Created
{
  "id": "uuid",
  "customer_number": "CUST-0001",
  ...
}

Permissions: financial:customers:create:company
Events: financial.customer.created
```

---

### **Invoices API** (`/api/v1/financial/invoices`)

#### **1. List Invoices**
```
GET /api/v1/financial/invoices

Query Parameters:
  - company_id: UUID (required)
  - customer_id: UUID (optional)
  - status: string (optional)
  - from_date: date (optional)
  - to_date: date (optional)
  - overdue_only: boolean (optional)
  - page: integer
  - page_size: integer

Response: 200 OK
{
  "invoices": [
    {
      "id": "uuid",
      "invoice_number": "INV-2024-0001",
      "customer": {
        "id": "uuid",
        "name": "Acme Corp"
      },
      "invoice_date": "2024-01-15",
      "due_date": "2024-02-14",
      "status": "sent",
      "total_amount": 5000.00,
      "paid_amount": 0.00,
      "balance_due": 5000.00,
      "currency_code": "USD"
    }
  ],
  "summary": {
    "total_invoices": 50,
    "total_amount": 250000.00,
    "total_paid": 200000.00,
    "total_outstanding": 50000.00
  },
  "pagination": {...}
}

Permissions: financial:invoices:read:company
```

#### **2. Create Invoice**
```
POST /api/v1/financial/invoices

Request Body:
{
  "company_id": "uuid",
  "customer_id": "uuid",
  "invoice_date": "2024-01-15",
  "due_date": "2024-02-14",
  "reference_number": "PO-12345",
  "payment_terms_days": 30,
  "notes": "Thank you for your business",
  "line_items": [
    {
      "description": "Consulting Services",
      "quantity": 10,
      "unit_price": 150.00,
      "tax_rate": 10.00,
      "revenue_account_id": "uuid"
    },
    {
      "description": "Software License",
      "quantity": 1,
      "unit_price": 500.00,
      "tax_rate": 10.00,
      "revenue_account_id": "uuid"
    }
  ],
  "discount_amount": 0.00,
  "shipping_amount": 0.00
}

Response: 201 Created
{
  "id": "uuid",
  "invoice_number": "INV-2024-0001",
  "status": "draft",
  "subtotal": 2000.00,
  "tax_amount": 200.00,
  "total_amount": 2200.00,
  "balance_due": 2200.00,
  ...
}

Permissions: financial:invoices:create:company
Business Rules:
  - Auto-generate invoice number
  - Calculate subtotal, tax, total
  - Set balance_due = total_amount
Events: financial.invoice.created
```

#### **3. Send Invoice**
```
POST /api/v1/financial/invoices/{invoice_id}/send

Request Body:
{
  "email_to": "customer@example.com",
  "email_subject": "Invoice INV-2024-0001",
  "email_body": "Please find attached your invoice",
  "send_copy_to_self": true
}

Response: 200 OK
{
  "id": "uuid",
  "status": "sent",
  "sent_at": "2024-01-15T14:30:00Z",
  "sent_by": {
    "id": "uuid",
    "name": "John Doe"
  }
}

Permissions: financial:invoices:send:company
Business Rules:
  - Can only send draft or sent invoices
  - Creates journal entry if first time sending
  - Sends email to customer
Events: financial.invoice.sent
```

#### **4. Record Payment**
```
POST /api/v1/financial/invoices/{invoice_id}/record-payment

Request Body:
{
  "payment_date": "2024-01-20",
  "payment_amount": 2200.00,
  "payment_method": "bank_transfer",
  "reference_number": "TXN-12345",
  "deposit_to_account_id": "uuid",
  "notes": "Payment received via bank transfer"
}

Response: 200 OK
{
  "invoice": {
    "id": "uuid",
    "status": "paid",
    "paid_amount": 2200.00,
    "balance_due": 0.00
  },
  "payment": {
    "id": "uuid",
    "payment_number": "PAY-2024-0001",
    "payment_amount": 2200.00
  }
}

Permissions: financial:payments:create:company
Business Rules:
  - Cannot exceed invoice balance
  - Updates invoice status (partially_paid/paid)
  - Creates journal entry
  - Updates customer balance
Events: financial.payment.recorded, financial.invoice.paid
```

#### **5. Generate Invoice PDF**
```
GET /api/v1/financial/invoices/{invoice_id}/pdf

Response: 200 OK (application/pdf)
Binary PDF content

Permissions: financial:invoices:read:company
```

#### **6. Void Invoice**
```
POST /api/v1/financial/invoices/{invoice_id}/void

Request Body:
{
  "reason": "Duplicate invoice created by mistake"
}

Response: 200 OK
{
  "id": "uuid",
  "status": "void",
  "voided_at": "2024-01-15T16:00:00Z"
}

Permissions: financial:invoices:delete:company
Business Rules:
  - Cannot void if payments exist
  - Reverses journal entry
Events: financial.invoice.voided
```

---

### **Payments API** (`/api/v1/financial/payments`)

#### **1. List Payments**
```
GET /api/v1/financial/payments

Query Parameters:
  - company_id: UUID (required)
  - customer_id: UUID (optional)
  - from_date: date (optional)
  - to_date: date (optional)
  - status: string (optional)
  - page: integer
  - page_size: integer

Response: 200 OK
{
  "payments": [
    {
      "id": "uuid",
      "payment_number": "PAY-2024-0001",
      "customer": {
        "id": "uuid",
        "name": "Acme Corp"
      },
      "payment_date": "2024-01-20",
      "payment_amount": 2200.00,
      "payment_method": "bank_transfer",
      "status": "completed",
      "allocated_invoices": [
        {
          "invoice_id": "uuid",
          "invoice_number": "INV-2024-0001",
          "allocated_amount": 2200.00
        }
      ]
    }
  ],
  "pagination": {...}
}

Permissions: financial:payments:read:company
```

---

### **Reports API** (`/api/v1/financial/reports`)

#### **1. Trial Balance**
```
GET /api/v1/financial/reports/trial-balance

Query Parameters:
  - company_id: UUID (required)
  - as_of_date: date (required)

Response: 200 OK
{
  "company_id": "uuid",
  "as_of_date": "2024-01-31",
  "accounts": [
    {
      "code": "1000",
      "name": "Cash",
      "debit_balance": 50000.00,
      "credit_balance": 0.00
    },
    {
      "code": "2000",
      "name": "Accounts Payable",
      "debit_balance": 0.00,
      "credit_balance": 30000.00
    }
  ],
  "totals": {
    "total_debits": 150000.00,
    "total_credits": 150000.00,
    "difference": 0.00
  }
}

Permissions: financial:reports:read:company
```

#### **2. Balance Sheet**
```
GET /api/v1/financial/reports/balance-sheet

Query Parameters:
  - company_id: UUID (required)
  - as_of_date: date (required)

Response: 200 OK
{
  "company_id": "uuid",
  "as_of_date": "2024-01-31",
  "assets": {
    "current_assets": {
      "cash": 50000.00,
      "accounts_receivable": 30000.00,
      "total": 80000.00
    },
    "total_assets": 150000.00
  },
  "liabilities": {
    "current_liabilities": {
      "accounts_payable": 30000.00,
      "total": 30000.00
    },
    "total_liabilities": 30000.00
  },
  "equity": {
    "retained_earnings": 120000.00,
    "total_equity": 120000.00
  },
  "total_liabilities_and_equity": 150000.00
}

Permissions: financial:reports:read:company
```

#### **3. Profit & Loss Statement**
```
GET /api/v1/financial/reports/profit-loss

Query Parameters:
  - company_id: UUID (required)
  - from_date: date (required)
  - to_date: date (required)

Response: 200 OK
{
  "company_id": "uuid",
  "from_date": "2024-01-01",
  "to_date": "2024-01-31",
  "revenue": {
    "sales": 100000.00,
    "total_revenue": 100000.00
  },
  "expenses": {
    "cost_of_goods_sold": 40000.00,
    "operating_expenses": 30000.00,
    "total_expenses": 70000.00
  },
  "net_income": 30000.00
}

Permissions: financial:reports:read:company
```

#### **4. Aged Receivables**
```
GET /api/v1/financial/reports/aged-receivables

Query Parameters:
  - company_id: UUID (required)
  - as_of_date: date (required)

Response: 200 OK
{
  "company_id": "uuid",
  "as_of_date": "2024-01-31",
  "customers": [
    {
      "customer_id": "uuid",
      "customer_name": "Acme Corp",
      "current": 5000.00,
      "30_days": 2000.00,
      "60_days": 1000.00,
      "90_days": 500.00,
      "over_90_days": 0.00,
      "total": 8500.00
    }
  ],
  "totals": {
    "current": 20000.00,
    "30_days": 8000.00,
    "60_days": 4000.00,
    "90_days": 2000.00,
    "over_90_days": 1000.00,
    "total": 35000.00
  }
}

Permissions: financial:reports:read:company
```

---

## Service Layer Design

### **1. Account Service** (`services/account_service.py`)

```python
class AccountService:
    """Business logic for account management"""

    async def create_account(
        self,
        db: AsyncSession,
        account_data: AccountCreate,
        current_user: User
    ) -> Account:
        """
        Create a new account

        Business Rules:
        - Validate account code uniqueness
        - Validate account type
        - Validate parent account (must be header account)
        - Auto-generate code if not provided
        - Set initial balance to 0
        """

    async def update_balance(
        self,
        db: AsyncSession,
        account_id: UUID,
        debit_amount: Decimal,
        credit_amount: Decimal
    ) -> Account:
        """
        Update account balance

        Business Rules:
        - For asset/expense accounts: balance = debit - credit
        - For liability/equity/revenue accounts: balance = credit - debit
        - Lock account row during update
        """

    async def get_account_balance(
        self,
        db: AsyncSession,
        account_id: UUID,
        as_of_date: Optional[date] = None
    ) -> Decimal:
        """
        Calculate account balance as of a specific date

        - If as_of_date is None, return current balance
        - Otherwise, sum all transactions up to that date
        """

    async def create_default_chart_of_accounts(
        self,
        db: AsyncSession,
        company_id: UUID,
        template: str = "standard"
    ) -> List[Account]:
        """
        Create default chart of accounts for new company

        Templates:
        - standard: Basic accounting structure
        - retail: Retail-specific accounts
        - service: Service business accounts
        - manufacturing: Manufacturing accounts
        """

    async def validate_account_deletion(
        self,
        db: AsyncSession,
        account_id: UUID
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if account can be deleted

        Returns:
        - (True, None) if can be deleted
        - (False, "reason") if cannot be deleted

        Checks:
        - Has no transactions
        - Has no child accounts
        - Not used in any invoices/payments
        """
```

---

### **2. Journal Entry Service** (`services/journal_entry_service.py`)

```python
class JournalEntryService:
    """Business logic for journal entries"""

    async def create_journal_entry(
        self,
        db: AsyncSession,
        entry_data: JournalEntryCreate,
        current_user: User
    ) -> JournalEntry:
        """
        Create a journal entry

        Business Rules:
        - Validate debits = credits
        - Generate entry number
        - At least 2 lines required
        - All accounts must exist
        - Entry date cannot be in a closed period
        """

    async def post_journal_entry(
        self,
        db: AsyncSession,
        entry_id: UUID,
        current_user: User
    ) -> JournalEntry:
        """
        Post a journal entry

        Actions:
        - Validate entry is in draft status
        - Update account balances for each line
        - Set status to 'posted'
        - Record posting timestamp and user
        - Publish event
        """

    async def reverse_journal_entry(
        self,
        db: AsyncSession,
        entry_id: UUID,
        reversal_date: date,
        current_user: User
    ) -> JournalEntry:
        """
        Reverse a journal entry

        Actions:
        - Create new entry with opposite debits/credits
        - Link original and reversal entries
        - Post reversal entry automatically
        - Mark original as reversed
        """

    async def auto_generate_entry_number(
        self,
        db: AsyncSession,
        company_id: UUID,
        entry_date: date
    ) -> str:
        """
        Generate journal entry number

        Format: JE-{YEAR}-{SEQUENCE}
        Example: JE-2024-0001
        """
```

---

### **3. Invoice Service** (`services/invoice_service.py`)

```python
class InvoiceService:
    """Business logic for invoices"""

    async def create_invoice(
        self,
        db: AsyncSession,
        invoice_data: InvoiceCreate,
        current_user: User
    ) -> Invoice:
        """
        Create an invoice

        Actions:
        - Generate invoice number
        - Calculate line totals
        - Calculate tax amounts
        - Calculate invoice total
        - Set balance_due = total_amount
        - Set status = 'draft'
        """

    async def calculate_invoice_totals(
        self,
        line_items: List[InvoiceLineItemCreate],
        discount_amount: Decimal = Decimal('0'),
        shipping_amount: Decimal = Decimal('0')
    ) -> Dict:
        """
        Calculate invoice totals

        Returns:
        {
          "subtotal": Decimal,
          "tax_amount": Decimal,
          "discount_amount": Decimal,
          "shipping_amount": Decimal,
          "total_amount": Decimal
        }
        """

    async def send_invoice(
        self,
        db: AsyncSession,
        invoice_id: UUID,
        email_params: Dict,
        current_user: User
    ) -> Invoice:
        """
        Send invoice to customer

        Actions:
        - Generate PDF
        - Send email
        - Update status to 'sent'
        - Create journal entry (if first time)
        - Publish event

        Journal Entry:
        Dr. Accounts Receivable
            Cr. Revenue (per line item)
            Cr. Tax Payable
        """

    async def create_invoice_journal_entry(
        self,
        db: AsyncSession,
        invoice: Invoice
    ) -> JournalEntry:
        """
        Create journal entry for invoice

        Dr. Accounts Receivable {total_amount}
            Cr. Revenue Account 1 {line_1_amount}
            Cr. Revenue Account 2 {line_2_amount}
            Cr. Tax Payable {tax_amount}
        """

    async def void_invoice(
        self,
        db: AsyncSession,
        invoice_id: UUID,
        reason: str,
        current_user: User
    ) -> Invoice:
        """
        Void an invoice

        Actions:
        - Validate no payments exist
        - Reverse journal entry
        - Set status to 'void'
        - Update customer balance
        """

    async def auto_generate_invoice_number(
        self,
        db: AsyncSession,
        company_id: UUID,
        invoice_date: date
    ) -> str:
        """
        Generate invoice number

        Format: {PREFIX}-{YEAR}-{SEQUENCE}
        Example: INV-2024-0001

        Prefix from company configuration
        """

    async def update_invoice_status(
        self,
        db: AsyncSession,
        invoice: Invoice
    ):
        """
        Update invoice status based on payments

        Status logic:
        - draft: No journal entry created
        - sent: Journal entry created, not paid
        - partially_paid: 0 < paid_amount < total_amount
        - paid: paid_amount == total_amount
        - overdue: sent + due_date < today
        """
```

---

### **4. Payment Service** (`services/payment_service.py`)

```python
class PaymentService:
    """Business logic for payments"""

    async def record_payment(
        self,
        db: AsyncSession,
        payment_data: PaymentCreate,
        current_user: User
    ) -> Payment:
        """
        Record a payment

        Actions:
        - Generate payment number
        - Create payment record
        - Create payment allocations to invoices
        - Create journal entry
        - Update invoice balances
        - Update customer balance
        - Update invoice statuses
        """

    async def allocate_payment_to_invoices(
        self,
        db: AsyncSession,
        payment: Payment,
        allocations: List[Dict]
    ):
        """
        Allocate payment to invoices

        Business Rules:
        - Cannot allocate more than payment amount
        - Cannot allocate more than invoice balance
        - Update invoice paid_amount and balance_due
        """

    async def create_payment_journal_entry(
        self,
        db: AsyncSession,
        payment: Payment,
        allocations: List[PaymentAllocation]
    ) -> JournalEntry:
        """
        Create journal entry for payment

        Dr. Bank/Cash Account {payment_amount}
            Cr. Accounts Receivable {payment_amount}
        """

    async def auto_generate_payment_number(
        self,
        db: AsyncSession,
        company_id: UUID,
        payment_date: date
    ) -> str:
        """
        Generate payment number

        Format: PAY-{YEAR}-{SEQUENCE}
        Example: PAY-2024-0001
        """

    async def auto_allocate_payment(
        self,
        db: AsyncSession,
        customer_id: UUID,
        payment_amount: Decimal
    ) -> List[Dict]:
        """
        Auto-allocate payment to oldest invoices first

        Strategy:
        - Get unpaid invoices ordered by due_date
        - Allocate to oldest first
        - Continue until payment exhausted
        """
```

---

### **5. Report Service** (`services/report_service.py`)

```python
class ReportService:
    """Business logic for financial reports"""

    async def generate_trial_balance(
        self,
        db: AsyncSession,
        company_id: UUID,
        as_of_date: date
    ) -> Dict:
        """
        Generate trial balance report

        Logic:
        - Get all active accounts
        - Calculate balance for each account as of date
        - Group by account type
        - Verify total debits = total credits
        """

    async def generate_balance_sheet(
        self,
        db: AsyncSession,
        company_id: UUID,
        as_of_date: date
    ) -> Dict:
        """
        Generate balance sheet

        Sections:
        - Assets (asset accounts)
        - Liabilities (liability accounts)
        - Equity (equity + net income)
        """

    async def generate_profit_loss(
        self,
        db: AsyncSession,
        company_id: UUID,
        from_date: date,
        to_date: date
    ) -> Dict:
        """
        Generate profit & loss statement

        Sections:
        - Revenue (revenue accounts)
        - Cost of Goods Sold (expense accounts - COGS category)
        - Operating Expenses (expense accounts - operations)
        - Net Income (revenue - expenses)
        """

    async def generate_aged_receivables(
        self,
        db: AsyncSession,
        company_id: UUID,
        as_of_date: date
    ) -> Dict:
        """
        Generate aged receivables report

        Aging buckets:
        - Current (0-30 days)
        - 30 days (31-60)
        - 60 days (61-90)
        - 90 days (91-120)
        - Over 90 days (121+)
        """
```

---

## Pydantic Schemas

### **Account Schemas** (`schemas/account.py`)

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal
from uuid import UUID
from datetime import datetime

class AccountBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    type: str = Field(..., regex="^(asset|liability|equity|revenue|expense)$")
    category: Optional[str] = Field(None, max_length=100)
    sub_category: Optional[str] = Field(None, max_length=100)
    parent_account_id: Optional[UUID] = None
    currency_code: str = Field(default="USD", max_length=3)
    is_header: bool = False
    tax_category: Optional[str] = None

class AccountCreate(AccountBase):
    company_id: UUID

class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    parent_account_id: Optional[UUID] = None

class AccountResponse(AccountBase):
    id: UUID
    tenant_id: UUID
    company_id: UUID
    current_balance: Decimal
    debit_balance: Decimal
    credit_balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
```

---

### **Invoice Schemas** (`schemas/invoice.py`)

```python
class InvoiceLineItemBase(BaseModel):
    description: str
    quantity: Decimal = Field(default=Decimal('1'), ge=0)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal('0'), ge=0, le=100)
    discount_percent: Decimal = Field(default=Decimal('0'), ge=0, le=100)
    revenue_account_id: UUID

class InvoiceLineItemCreate(InvoiceLineItemBase):
    pass

class InvoiceLineItemResponse(InvoiceLineItemBase):
    id: UUID
    invoice_id: UUID
    line_number: int
    line_amount: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal

    class Config:
        from_attributes = True

class InvoiceBase(BaseModel):
    customer_id: UUID
    invoice_date: date
    due_date: date
    reference_number: Optional[str] = None
    payment_terms_days: int = Field(default=30, ge=0)
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    discount_amount: Decimal = Field(default=Decimal('0'), ge=0)
    shipping_amount: Decimal = Field(default=Decimal('0'), ge=0)

class InvoiceCreate(InvoiceBase):
    company_id: UUID
    line_items: List[InvoiceLineItemCreate] = Field(..., min_items=1)

    @validator('due_date')
    def due_date_after_invoice_date(cls, v, values):
        if 'invoice_date' in values and v < values['invoice_date']:
            raise ValueError('due_date must be after invoice_date')
        return v

class InvoiceResponse(InvoiceBase):
    id: UUID
    tenant_id: UUID
    company_id: UUID
    invoice_number: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    balance_due: Decimal
    currency_code: str
    sent_at: Optional[datetime]
    line_items: List[InvoiceLineItemResponse]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
```

---

## Business Rules & Validation

### **Account Rules**

1. **Code Uniqueness**: Account code must be unique within company
2. **Type Validation**: Type must be one of: asset, liability, equity, revenue, expense
3. **Parent Account**: If parent specified, must be a header account
4. **Balance Rules**:
   - Assets & Expenses: Balance = Debit - Credit (normal debit balance)
   - Liabilities, Equity, Revenue: Balance = Credit - Debit (normal credit balance)
5. **Deletion**: Cannot delete if:
   - Has transactions
   - Has child accounts
   - Referenced in invoices/payments

### **Journal Entry Rules**

1. **Balance**: Total debits must equal total credits
2. **Minimum Lines**: At least 2 lines required
3. **Posting**: Can only post entries in 'draft' status
4. **Editing**: Posted entries cannot be edited (must reverse)
5. **Date Validation**: Entry date cannot be in a closed period

### **Invoice Rules**

1. **Number Generation**: Auto-generate in format {PREFIX}-{YEAR}-{SEQUENCE}
2. **Calculation**:
   ```
   line_amount = quantity * unit_price
   line_discount = line_amount * (discount_percent / 100)
   line_tax = (line_amount - line_discount) * (tax_rate / 100)
   line_total = line_amount - line_discount + line_tax

   invoice_subtotal = sum(line_amounts)
   invoice_tax = sum(line_tax_amounts)
   invoice_total = subtotal + tax - discount + shipping
   balance_due = total - paid_amount
   ```
3. **Status Transitions**:
   - draft → sent (when sent to customer)
   - sent → partially_paid (when 0 < paid < total)
   - partially_paid → paid (when paid == total)
   - sent → overdue (when due_date < today and not paid)
4. **Voiding**: Can only void if no payments recorded

### **Payment Rules**

1. **Allocation**: Total allocated cannot exceed payment amount
2. **Invoice Balance**: Cannot allocate more than invoice balance
3. **Auto-allocation**: Allocate to oldest invoices first (FIFO)
4. **Status Update**: Update invoice status after payment recorded

---

## Event System Design

### **Events Published**

```python
# Account Events
financial.account.created
financial.account.updated
financial.account.deleted

# Journal Entry Events
financial.journal_entry.created
financial.journal_entry.posted
financial.journal_entry.reversed

# Customer Events
financial.customer.created
financial.customer.updated

# Invoice Events
financial.invoice.created
financial.invoice.updated
financial.invoice.sent
financial.invoice.paid
financial.invoice.partially_paid
financial.invoice.overdue
financial.invoice.voided

# Payment Events
financial.payment.recorded
financial.payment.allocated
financial.payment.bounced
```

### **Events Subscribed**

```python
# From Core Platform
core.company.created       → Create default chart of accounts
core.company.deleted       → Archive/delete financial data
core.user.role_changed     → Update cached permissions
core.fiscal_period.closed  → Prevent posting to closed periods
```

### **Event Payloads**

```python
# financial.invoice.created
{
  "invoice_id": "uuid",
  "invoice_number": "INV-2024-0001",
  "customer_id": "uuid",
  "customer_name": "Acme Corp",
  "total_amount": 2200.00,
  "currency_code": "USD",
  "invoice_date": "2024-01-15",
  "due_date": "2024-02-14",
  "status": "draft"
}

# financial.payment.recorded
{
  "payment_id": "uuid",
  "payment_number": "PAY-2024-0001",
  "customer_id": "uuid",
  "payment_amount": 2200.00,
  "payment_date": "2024-01-20",
  "invoices_paid": [
    {
      "invoice_id": "uuid",
      "invoice_number": "INV-2024-0001",
      "allocated_amount": 2200.00
    }
  ]
}
```

---

## Frontend Component Design

### **Page Components**

#### **1. Dashboard Page** (`pages/dashboard-page.js`)

**Features:**
- Financial summary cards (revenue, expenses, profit, receivables)
- Chart: Revenue vs Expenses (last 12 months)
- Recent invoices list
- Overdue invoices alert
- Quick actions (create invoice, record payment)

**API Calls:**
- GET `/api/v1/financial/reports/dashboard-summary`
- GET `/api/v1/financial/invoices?status=overdue&limit=5`

---

#### **2. Accounts Page** (`pages/accounts-page.js`)

**Features:**
- Hierarchical account tree view
- Filter by type (asset, liability, etc.)
- Search by code/name
- Current balance display
- Create/Edit/Delete account actions
- Account details modal

**Components:**
- AccountList
- AccountTree
- AccountForm
- AccountDetailsModal

---

#### **3. Invoices Page** (`pages/invoices-page.js`)

**Features:**
- Invoice list with filters (status, date range, customer)
- Summary cards (total invoiced, paid, outstanding, overdue)
- Create invoice button
- Invoice actions (send, record payment, void, PDF)
- Invoice detail view
- Payment recording modal

**Components:**
- InvoiceList
- InvoiceForm
- InvoiceDetailModal
- RecordPaymentModal
- InvoicePDFViewer

---

#### **4. Journal Entries Page** (`pages/journal-entries-page.js`)

**Features:**
- List of journal entries with filters
- Create manual journal entry
- Post/Reverse actions
- Entry detail view showing all lines
- Trial balance validation

**Components:**
- JournalEntryList
- JournalEntryForm
- JournalEntryLinesTable

---

### **Reusable Components**

```javascript
// components/account-selector.js
class AccountSelector {
  // Dropdown to select accounts with search
}

// components/customer-selector.js
class CustomerSelector {
  // Dropdown to select customers with search
}

// components/amount-input.js
class AmountInput {
  // Formatted currency input
}

// components/date-picker.js
class DatePicker {
  // Date selection widget
}

// components/financial-summary-card.js
class FinancialSummaryCard {
  // Card showing financial metric with trend
}
```

---

## Security & Permissions

### **Permission Matrix**

| Action | Permission | Scope |
|--------|-----------|-------|
| List accounts | financial:accounts:read | company |
| Create account | financial:accounts:create | company |
| Update account | financial:accounts:update | company |
| Delete account | financial:accounts:delete | company |
| View journal entries | financial:journal:read | company |
| Create journal entry | financial:journal:create | company |
| Post journal entry | financial:journal:post | company |
| Reverse entry | financial:journal:reverse | company |
| View invoices | financial:invoices:read | company |
| Create invoice | financial:invoices:create | company |
| Send invoice | financial:invoices:send | company |
| Void invoice | financial:invoices:delete | company |
| Record payment | financial:payments:create | company |
| View reports | financial:reports:read | company |
| Export reports | financial:reports:export | company |

### **Data Isolation**

1. **Tenant Level**: All queries filtered by tenant_id
2. **Company Level**: All queries filtered by company_id
3. **Row-Level**: Use PostgreSQL RLS policies for additional security

```sql
-- Example RLS policy
CREATE POLICY financial_accounts_tenant_isolation
ON financial_accounts
USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

---

## Implementation Checklist

### **Phase 1: Core Functionality** (Week 1)

- [ ] Create database models
  - [ ] Account model
  - [ ] JournalEntry & JournalEntryLine models
  - [ ] Customer model
- [ ] Create Alembic migrations
- [ ] Implement Account API endpoints
- [ ] Implement Account service layer
- [ ] Create default chart of accounts template
- [ ] Write unit tests for account operations

### **Phase 2: Transactions** (Week 2)

- [ ] Implement Journal Entry API endpoints
- [ ] Implement Journal Entry service layer
- [ ] Add balance update logic
- [ ] Add posting/reversing functionality
- [ ] Test double-entry bookkeeping
- [ ] Write integration tests

### **Phase 3: Invoicing** (Week 3)

- [ ] Create Invoice & InvoiceLineItem models
- [ ] Implement Invoice API endpoints
- [ ] Implement Invoice service layer
- [ ] Add invoice number generation
- [ ] Add calculation logic
- [ ] Implement send invoice functionality
- [ ] Add PDF generation

### **Phase 4: Payments** (Week 4)

- [ ] Create Payment & PaymentAllocation models
- [ ] Implement Payment API endpoints
- [ ] Implement Payment service layer
- [ ] Add payment allocation logic
- [ ] Add auto-allocation functionality
- [ ] Update invoice statuses

### **Phase 5: Reports** (Week 5)

- [ ] Implement Trial Balance report
- [ ] Implement Balance Sheet report
- [ ] Implement P&L Statement report
- [ ] Implement Aged Receivables report
- [ ] Add PDF export for reports

### **Phase 6: Frontend** (Week 6-7)

- [ ] Build Dashboard page
- [ ] Build Accounts page with tree view
- [ ] Build Invoice page with list/create/edit
- [ ] Build Payment recording interface
- [ ] Build Reports page
- [ ] Add loading states and error handling

### **Phase 7: Polish** (Week 8)

- [ ] Add comprehensive error messages
- [ ] Implement field validation
- [ ] Add confirmation dialogs
- [ ] Optimize database queries
- [ ] Add caching where appropriate
- [ ] Write end-to-end tests
- [ ] Performance testing
- [ ] Security audit

---

**Total Estimated Time: 8 weeks for full implementation**

This design provides a complete blueprint for implementing a production-ready Financial Module with all standard accounting features! 🚀
