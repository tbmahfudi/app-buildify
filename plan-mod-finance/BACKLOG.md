# Financial Module — Backlog

> Production-ready double-entry bookkeeping module for App-Buildify. Built on top of the platform's Module System (see `/plan/epics/epic-11-module-system.md`).

## Status Legend

| Tag | Meaning |
|-----|---------|
| `[DONE]` | Fully implemented in the codebase |
| `[IN-PROGRESS]` | Partially implemented or has known bugs |
| `[OPEN]` | Documented gap — design exists, code does not |
| `[PLANNED]` | Roadmap item — no code or design yet |

---

## Summary Table

| # | Epic | Status |
|---|------|--------|
| 12 | Financial Module | DONE; AP/Budget PLANNED |

---

## EPIC 12 — Financial Module

> Production-ready double-entry bookkeeping: Chart of Accounts, customers, invoicing with workflow, payments, journal entries, tax management, and six standard financial reports.

---

### Feature 12.1 — Chart of Accounts `[DONE]`

#### Story 12.1.1 — Hierarchical Account Structure `[DONE]`
*As a finance manager, I want to set up a hierarchical Chart of Accounts, so that my organization's finances are organized according to accounting principles.*
- `POST /financial/accounts` creates an account with `code`, `name`, `account_type` (`asset`/`liability`/`equity`/`revenue`/`expense`), `parent_account_id`
- Account tree is unlimited in depth; each node inherits the type from its root
- `POST /financial/accounts/setup/default` seeds a 50-account standard chart template
- `GET /financial/accounts/hierarchy` returns the full tree structure

#### Story 12.1.2 — Account Balance Tracking `[DONE]`
*As an accountant, I want to see the current balance of any account at any point in time, so that I can verify financial positions without running a full report.*
- `GET /financial/accounts/{id}/balance?as_of=2025-12-31` returns debit/credit balance as of the given date
- Balance computed from posted journal entries only (draft and voided entries excluded)
- Normal balance direction respected per account type (debit normal vs. credit normal)

---

### Feature 12.2 — Invoicing with Workflow `[DONE]`

#### Story 12.2.1 — Invoice Creation and Posting `[DONE]`
*As a billing administrator, I want to create invoices, add line items, and post them to the general ledger, so that revenue is recognized in accounting.*
- `POST /financial/invoices` creates an invoice in `DRAFT` status with `customer_id`, `invoice_date`, `due_date`, `line_items`, `tax_rate_id`
- `POST /financial/invoices/{id}/post` transitions to `POSTED` and auto-generates double-entry journal entries
- Invoice number auto-generated with configurable prefix and sequence per company
- Line items include `description`, `quantity`, `unit_price`, `account_id`, `tax_amount`

#### Story 12.2.2 — Invoice Workflow States `[DONE]`
*As a finance manager, I want invoices to move through defined states, so that the status of all receivables is always clear.*
- Lifecycle: `DRAFT → POSTED → PARTIALLY_PAID → PAID → VOID`
- `POST /financial/invoices/{id}/void` voids an invoice and creates reversal journal entries
- Status transitions enforced: a draft invoice cannot be directly voided
- Voided invoices retained for audit with `voided_at` timestamp and `void_reason`

#### Story 12.2.3 — Payment Recording and Allocation `[DONE]`
*As an accountant, I want to record customer payments and allocate them against invoices, so that outstanding balances are accurately tracked.*
- `POST /financial/payments` records a payment with `customer_id`, `amount`, `payment_date`, `payment_method`, `reference`
- `POST /financial/payments/{id}/allocate` allocates payment amounts against invoices
- Partial allocation → invoice status `PARTIALLY_PAID`; full allocation → `PAID`
- `GET /financial/payments/unallocated` returns payments with unallocated balance > 0

---

### Feature 12.3 — Double-Entry Journal Entries `[DONE]`

#### Story 12.3.1 — Manual Journal Entry Posting `[DONE]`
*As an accountant, I want to post manual journal entries with balanced debits and credits, so that adjusting entries and corrections can be made.*
- `POST /financial/journal-entries` creates a journal with `date`, `description`, `reference`, `line_items`
- `POST /financial/journal-entries/{id}/post` validates balance (total debits = total credits) before posting
- Unbalanced entries return 400 with `UNBALANCED_JOURNAL_ENTRY`
- `POST /financial/journal-entries/{id}/reverse` creates a reversal entry with negated amounts

---

### Feature 12.4 — Financial Reports `[DONE]`

#### Story 12.4.1 — Standard Financial Report Suite `[DONE]`
*As a CFO, I want to generate standard financial reports on demand, so that the organization's financial health can be assessed quickly.*
- `GET /financial/reports/trial-balance?as_of=2025-12-31` — all accounts with debit/credit totals
- `GET /financial/reports/balance-sheet?as_of=2025-12-31` — assets, liabilities, equity
- `GET /financial/reports/income-statement?from=2025-01-01&to=2025-12-31` — revenues and expenses
- `GET /financial/reports/aged-receivables?as_of=2025-12-31` — outstanding invoices by aging bucket (0-30, 31-60, 61-90, 90+ days)
- `GET /financial/reports/cash-flow?from=...&to=...` — operating/investing/financing activities
- `GET /financial/reports/account-ledger/{id}?from=...&to=...` — all transactions for a specific account

#### Story 12.4.2 — Tax Rate Management `[DONE]`
*As a finance administrator, I want to configure multiple tax rates for different jurisdictions, so that invoices apply correct tax calculations automatically.*
- `POST /financial/tax-rates` creates a tax rate with `name`, `rate` (percentage), `account_id`, `is_compound`
- `POST /financial/tax-rates/calculate` returns the tax amount for a given `subtotal` and `tax_rate_id`
- Multiple tax rates can be applied to a single invoice line item
- Archived tax rates cannot be applied to new invoices but remain visible on historical invoices

---

### Feature 12.5 — Financial Module Planned Enhancements `[PLANNED]`

#### Story 12.5.1 — Vendor Management and Accounts Payable `[PLANNED]`
*As an accountant, I want to manage vendor records and track bills, so that the platform covers the full payables cycle.*
- Vendor model with `name`, `code`, `tax_id`, `payment_terms`, `default_expense_account_id`
- `POST /financial/bills` creates an AP bill with workflow mirroring the invoice module
- `GET /financial/reports/aged-payables` — outstanding bills grouped by aging bucket
- AP journal entries use the accounts payable liability account automatically

#### Story 12.5.2 — Bank Reconciliation `[PLANNED]`
*As an accountant, I want to reconcile bank statement transactions against GL entries, so that accounting records match actual bank activity.*
- `POST /financial/bank-accounts` registers a bank account mapped to a GL cash account
- Bank statement CSV import maps transactions to the reconciliation workspace
- Matched transactions flagged; unmatched items require manual assignment to GL entries
- Reconciliation report shows matched, unmatched, and outstanding items

#### Story 12.5.3 — Budget Management `[PLANNED]`
*As a department manager, I want to define budgets by account and period, so that actual vs. budget variance reports are available.*
- `POST /financial/budgets` creates a budget per `fiscal_year`, `company_id`, with line items per `account_id` and `period`
- `GET /financial/reports/budget-variance?year=2025` compares actuals to budget by period and account
- Budget approval workflow: draft → submitted → approved
- Budget figures editable only before the period start date (or by finance admin override)
