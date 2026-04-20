# Epic 12 — Financial Module

> Production-ready double-entry bookkeeping: Chart of Accounts, customers, invoicing with workflow, payments, journal entries, tax management, and six standard financial reports.

---

## Feature 12.1 — Chart of Accounts `[DONE]`

### Story 12.1.1 — Hierarchical Account Structure `[DONE]`

#### Backend
*As an API, I want to manage a hierarchical Chart of Accounts with standard account types, so that accounting data is organized correctly.*
- `POST /api/v1/financial/accounts` with `{code, name, account_type, parent_account_id?, is_active}`
- Account types: `asset`, `liability`, `equity`, `revenue`, `expense`
- `POST /api/v1/financial/accounts/setup/default` seeds a 50-account standard chart
- `GET /api/v1/financial/accounts/hierarchy` returns a tree structure

#### Frontend
*As a finance manager on the Chart of Accounts page, I want to see a collapsible tree of all accounts organized by type, add new accounts by clicking a parent to add a child, and deactivate obsolete accounts, so that I can maintain the chart without SQL knowledge.*
- Route: `#/financial/accounts` renders a tree view grouped by account type (Assets, Liabilities, Equity, Revenue, Expenses)
- Each group is a collapsible section header with a total balance chip
- Account rows: account code | account name | type badge | balance | action icons (Add Child, Edit, Deactivate)
- "Add Account" button in the page header opens a `FlexModal`: Code, Name, Account Type, Parent Account (tree select), Currency
- "Setup Default Chart" button (only shown if chart is empty) seeds the 50-account template with a single click + confirmation
- Deactivated accounts shown with strikethrough text; hidden by default with a "Show Inactive" toggle

---

### Story 12.1.2 — Account Balance Tracking `[DONE]`

#### Backend
*As an API, I want to calculate account balances from posted journal entries as of a given date, so that real-time balances are accurate.*
- `GET /api/v1/financial/accounts/{id}/balance?as_of=2025-12-31` computes `SUM(debit) - SUM(credit)` or vice versa per account type from posted entries
- Normal balance direction: Asset/Expense = debit normal; Liability/Equity/Revenue = credit normal

#### Frontend
*As an accountant on the Chart of Accounts page, I want to click any account and see a balance panel with the current balance and a mini ledger showing the last 10 transactions, so that I can quickly verify an account position.*
- Clicking an account row opens a right-side `FlexDrawer`
- Drawer header: account code + name + type badge
- Balance section: current balance prominently displayed in the account's normal direction (DR $12,450 or CR $8,200)
- "As of date" date picker (defaults to today); changing the date recalculates the balance
- Mini-ledger table below: Date | Description | Debit | Credit | Running Balance — last 10 entries
- "View Full Ledger" button navigates to the account ledger report page pre-filtered to this account

---

## Feature 12.2 — Invoicing with Workflow `[DONE]`

### Story 12.2.1 — Invoice Creation and Posting `[DONE]`

#### Backend
*As an API, I want to create invoices with line items and post them to the general ledger via double-entry journal entries, so that revenue is correctly recognized.*
- `POST /api/v1/financial/invoices` creates an invoice in `DRAFT` status
- Line items: `{description, quantity, unit_price, account_id, tax_rate_id?}`
- `POST /api/v1/financial/invoices/{id}/post` validates, transitions to `POSTED`, auto-generates journal entries (DR Accounts Receivable, CR Revenue + Tax Payable)
- Invoice number auto-generated: configurable prefix + zero-padded sequence per company

#### Frontend
*As a billing administrator on the invoice creation page, I want a form with a customer selector, invoice details, and an interactive line items table where I can add rows, set quantities and prices, and see the subtotal, tax, and total update in real time, so that creating an invoice is fast and error-free.*
- Route: `#/financial/invoices/new` renders an invoice form page (not a modal — full page due to complexity)
- Header section: Customer (searchable select from `GET /financial/customers`), Invoice Date (datepicker), Due Date (datepicker), Invoice # (auto-filled, editable), Notes textarea
- Line items table: each row has Description | Account (select) | Quantity | Unit Price | Tax Rate (select) | Amount (calculated, read-only)
- "Add Line" button appends a new blank row; delete icon on each row
- Summary panel (right side, sticky): Subtotal, Tax (breakdown by rate), **Total** in large bold text
- "Save as Draft" and "Post Invoice" buttons in the sticky footer
- "Post Invoice" confirmation modal: "Posting will create journal entries and cannot be easily reversed. Continue?"
- After posting: page transitions to the invoice detail view with a green "Posted" status badge

---

### Story 12.2.2 — Invoice Workflow States `[DONE]`

#### Backend
*As an API, I want invoices to transition through defined states with enforced rules, so that the financial lifecycle is controlled.*
- Lifecycle: `DRAFT → POSTED → PARTIALLY_PAID → PAID → VOID`
- `POST /api/v1/financial/invoices/{id}/void` creates reversal journal entries; sets `voided_at` and `void_reason`
- Invalid transitions return 400 with `INVALID_INVOICE_TRANSITION`

#### Frontend
*As a finance manager on the invoice list page, I want to see the status of each invoice at a glance with color-coded badges, and be able to filter by status, so that I can quickly identify outstanding and overdue invoices.*
- Route: `#/financial/invoices` renders a table with columns: Invoice # | Customer | Issue Date | Due Date | Amount | Status | Actions
- Status badge colors: Draft=grey, Posted=blue, Partially Paid=amber, Paid=green, Void=red strikethrough
- "Overdue" secondary badge (red) shown when `due_date < today` and status is Posted or Partially Paid
- Filter bar: Status chips (All / Draft / Posted / Unpaid / Paid / Void), Customer search, Date range
- Invoice detail page shows the workflow state chip prominently and displays available actions (Post / Void / Record Payment) based on current state
- "Void Invoice" opens a modal with a required "Reason" textarea

---

### Story 12.2.3 — Payment Recording and Allocation `[DONE]`

#### Backend
*As an API, I want to record payments and allocate them against invoices, so that outstanding balances and invoice statuses are accurate.*
- `POST /api/v1/financial/payments` records a payment: `{customer_id, amount, payment_date, payment_method, reference}`
- `POST /api/v1/financial/payments/{id}/allocate` accepts `{allocations: [{invoice_id, amount}]}`
- Partial allocation → invoice `PARTIALLY_PAID`; full → `PAID`; creates DR Cash / CR Accounts Receivable journal entries

#### Frontend
*As an accountant recording a customer payment, I want to enter the payment amount and then see a list of the customer's outstanding invoices where I can allocate amounts against each one, so that payment application is clear and accurate.*
- Route: `#/financial/payments/new` opens a payment form page
- Step 1 — Payment details: Customer (select), Amount, Payment Date, Method (Cash/Bank Transfer/Card/Cheque), Reference
- Step 2 — Allocation: table of the customer's POSTED/PARTIALLY_PAID invoices: Invoice # | Due Date | Original Amount | Outstanding | Allocate (input)
- "Auto-allocate" button fills allocations oldest-first up to the payment amount
- Running total below the table: "Allocated: $X | Unallocated: $Y" — unallocated amount shown in amber as a warning
- "Save Payment" button; if unallocated amount > 0, shows a warning: "You have $Y unallocated. This will be held as unapplied credit."
- Invoice detail page shows payment history in a "Payments" tab: date, reference, allocated amount

---

## Feature 12.3 — Double-Entry Journal Entries `[DONE]`

### Story 12.3.1 — Manual Journal Entry Posting `[DONE]`

#### Backend
*As an API, I want to create and post manual journal entries, enforcing debit/credit balance, so that accountants can make adjusting entries.*
- `POST /api/v1/financial/journal-entries` creates a journal in `DRAFT` status
- `POST /api/v1/financial/journal-entries/{id}/post` validates `SUM(debit) == SUM(credit)` (within 0.01 rounding tolerance)
- `POST /api/v1/financial/journal-entries/{id}/reverse` creates a new entry with all debits/credits negated, linked to the original

#### Frontend
*As an accountant creating a journal entry, I want a form with a dynamic debit/credit line table where the running totals update as I type, and the Post button is disabled until the entry is balanced, so that I can't post an unbalanced entry.*
- Route: `#/financial/journal-entries/new`
- Header: Date (datepicker), Description, Reference, Period selector
- Line items table: Account (select, searchable) | Description | Debit | Credit
- "Add Line" button appends a row; minimum 2 rows enforced
- Balance status bar at the bottom: "Debits: $X | Credits: $Y | Difference: $Z" — green when balanced ($Z = 0), red when unbalanced
- "Post Entry" button disabled (greyed) when the entry is unbalanced; tooltip "Entry must balance before posting"
- After posting: a `FlexAlert` info banner: "This entry has been posted and cannot be modified. To correct it, use Reverse Entry."
- "Reverse Entry" button creates the reversal and navigates to the new draft entry with the lines pre-filled

---

## Feature 12.4 — Financial Reports `[DONE]`

### Story 12.4.1 — Standard Financial Report Suite `[DONE]`

#### Backend
*As an API, I want to generate standard financial statements from posted journal entries, so that finance managers can review the organization's financial position.*
- `GET /api/v1/financial/reports/trial-balance?as_of=DATE`
- `GET /api/v1/financial/reports/balance-sheet?as_of=DATE`
- `GET /api/v1/financial/reports/income-statement?from=DATE&to=DATE`
- `GET /api/v1/financial/reports/aged-receivables?as_of=DATE` (buckets: 0-30, 31-60, 61-90, 90+ days)
- `GET /api/v1/financial/reports/cash-flow?from=DATE&to=DATE`
- `GET /api/v1/financial/reports/account-ledger/{id}?from=DATE&to=DATE`

#### Frontend
*As a CFO on the financial reports page, I want a sidebar with links to each standard report, and each report renders in a printable table format with a date picker at the top and an export button, so that financial reporting is one click away.*
- Route: `#/financial/reports` with left sidebar listing all 6 reports
- Each report page has a date/period picker at the top (As Of date for balance sheet/trial balance; From/To range for income statement/cash flow)
- "Run Report" button fetches and renders the report in a structured table
- Balance Sheet: two-column layout (Assets on left, Liabilities+Equity on right) with section subtotals and a grand total row
- Income Statement: revenue section, expense section, net income/loss row highlighted in green/red
- Aged Receivables: customer rows × aging bucket columns; "Total Outstanding" column; customers with 90+ days shown in red
- Export button (top right): dropdown with PDF / Excel / CSV options
- "Print" button triggers `window.print()` with print-optimized CSS (hides navigation, maximizes table width)

---

### Story 12.4.2 — Tax Rate Management `[DONE]`

#### Backend
*As an API, I want to manage tax rates that can be applied to invoice line items, so that tax calculations are consistent.*
- `POST /api/v1/financial/tax-rates` with `{name, rate, account_id, is_compound, is_active}`
- `POST /api/v1/financial/tax-rates/calculate` accepts `{subtotal, tax_rate_id}` and returns `{tax_amount, total}`

#### Frontend
*As a finance administrator on the tax rates page, I want to add, edit, and deactivate tax rates in a simple table, and see a live calculation preview when entering a rate, so that tax setup is straightforward.*
- Route: `#/financial/tax-rates` renders a table: Name | Rate % | GL Account | Type | Status | Actions
- "Add Tax Rate" button opens a `FlexModal`: Name, Rate % (number input), GL Account (select from Chart of Accounts), Compound toggle, Active toggle
- Rate preview: entering a rate shows a live example: "On a $100 subtotal: Tax = $X, Total = $Y"
- Deactivating a tax rate: confirmation modal warns if the rate is referenced by draft invoices
- Archived rates shown with a "(Archived)" suffix in invoice line item selects — visible on historical invoices but not selectable for new ones

---

## Feature 12.5 — Financial Module Planned Enhancements `[PLANNED]`

### Story 12.5.1 — Vendor Management and Accounts Payable `[PLANNED]`

#### Backend
*As an API, I want vendor and bill management endpoints mirroring the customer/invoice structure, so that the full payables cycle is covered.*
- `POST /api/v1/financial/vendors`, `/bills`, `/bills/{id}/post`, `/bills/{id}/pay`
- `GET /api/v1/financial/reports/aged-payables?as_of=DATE`

#### Frontend
*As an accountant on the bills page, I want the same workflow as invoices — create, post, and pay — but for vendor bills, so that payables are managed consistently with receivables.*
- Route: `#/financial/bills` mirrors the invoices page with "Vendor" instead of "Customer"
- Aged Payables report accessible from the financial reports sidebar alongside Aged Receivables
- Vendor master page at `#/financial/vendors` with the same CRUD UX as customers

---

### Story 12.5.2 — Bank Reconciliation `[PLANNED]`

#### Backend
*As an API, I want bank account and statement import endpoints, so that accountants can match bank transactions to GL entries.*
- `POST /api/v1/financial/bank-accounts`, `POST /api/v1/financial/bank-accounts/{id}/import-statement` (CSV)
- Matching logic: auto-match by amount + date proximity

#### Frontend
*As an accountant doing a bank reconciliation, I want to see unmatched bank transactions on the left and unmatched GL entries on the right, and drag a bank transaction to a GL entry to match them, so that reconciliation is visual and efficient.*
- Route: `#/financial/bank-reconciliation/{account_id}`
- Split-pane layout: left = imported bank statement lines; right = unmatched GL entries for the same cash account
- Drag a bank line to a GL entry to match; matched pairs move to a "Matched" section below
- "Auto-Match" button matches lines by amount and date automatically
- Running totals: Unmatched Bank Items total | Unmatched GL Items total | Difference (must reach zero to complete reconciliation)
- "Complete Reconciliation" button enabled only when difference = $0
