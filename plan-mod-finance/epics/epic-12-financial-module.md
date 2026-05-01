# Epic 12 — Financial Module

> Production-ready double-entry bookkeeping: Chart of Accounts, customers, invoicing with workflow, payments, journal entries, tax management, and six standard financial reports.

---

## Feature 12.1 — Chart of Accounts `[DONE]`

### Story 12.1.1 — Hierarchical Account Structure `[IN-PROGRESS]`

#### Backend
*As an API, I want to manage a hierarchical Chart of Accounts with standard account types, so that accounting data is organized correctly.*
- `POST /api/v1/financial/accounts` with `{code, name, account_type, parent_account_id?, is_active}`
- Account types: `asset`, `liability`, `equity`, `revenue`, `expense`
- `POST /api/v1/financial/accounts/setup/default` seeds a 50-account standard chart
- `GET /api/v1/financial/accounts/hierarchy` returns a tree structure

#### Frontend
*As a finance manager on the Chart of Accounts page, I want to see a collapsible tree of all accounts organized by type, add new accounts by clicking a parent to add a child, and deactivate obsolete accounts, so that I can maintain the chart without SQL knowledge.*
- Route: `#/financial/accounts` → `financial-accounts.html` + `financial-accounts-page.js`
- Layout: FlexStack(direction=vertical) > page-header, account-tree
  - page-header: FlexToolbar — "Chart of Accounts" title | "Show Inactive" FlexCheckbox toggle | "Add Account" FlexButton(primary)
  - account-tree: FlexStack(gap=xs) — one FlexAccordion per account type (Assets / Liabilities / Equity / Revenue / Expenses)

- Per account-type FlexAccordion:
  - header: type label + total balance FlexBadge(chip)
  - body: indented tree rows per account — account code | account name | type FlexBadge | balance | action icons (Add Child / Edit / Deactivate)
  - deactivated account rows: strikethrough text; hidden unless "Show Inactive" toggle is on

- `AddAccountModal` FlexModal(size=sm) triggered by "Add Account" or "Add Child":
  - fields: Code (FlexInput) | Name (FlexInput, required) | Account Type (FlexSelect) | Parent Account (tree-select FlexSelect) | Currency (FlexSelect)
  - footer: Cancel | "Add Account" FlexButton(primary)

- `SetupDefaultModal` FlexModal(size=sm) shown only when chart is empty:
  - body: "Seed 50-account standard chart?"
  - footer: Cancel | "Setup Default Chart" FlexButton(primary)

- Interactions:
  - click accordion header: expands/collapses that account type group
  - click "Add Child" on an account row: opens AddAccountModal with Parent Account pre-filled
  - click "Deactivate" on a row: FlexModal(size=sm) confirm → PATCH /financial/accounts/{id} {is_active: false} → row shows strikethrough
  - toggle "Show Inactive": re-renders tree including/excluding deactivated rows

- States:
  - loading: account-tree shows skeleton rows
  - empty (chart): "Setup Default Chart" FlexButton(primary) centered instead of account-tree

---

### Story 12.1.2 — Account Balance Tracking `[DONE]`

#### Backend
*As an API, I want to calculate account balances from posted journal entries as of a given date, so that real-time balances are accurate.*
- `GET /api/v1/financial/accounts/{id}/balance?as_of=2025-12-31` computes `SUM(debit) - SUM(credit)` or vice versa per account type from posted entries
- Normal balance direction: Asset/Expense = debit normal; Liability/Equity/Revenue = credit normal

#### Frontend
*As an accountant on the Chart of Accounts page, I want to click any account and see a balance panel with the current balance and a mini ledger showing the last 10 transactions, so that I can quickly verify an account position.*
- Route: `#/financial/accounts` → FlexDrawer triggered by clicking an account row (no separate route)
- Layout: FlexDrawer(position=right, size=sm, overlay=false) > balance-header, balance-section, mini-ledger
  - balance-header: FlexToolbar — account code + name + type FlexBadge | × close
  - balance-section: FlexStack — "As of" FlexDatepicker (defaults to today) | current balance label (DR $X or CR $X, large text)
  - mini-ledger: FlexDataGrid(static, max 10 rows) — Date | Description | Debit | Credit | Running Balance
  - footer: "View Full Ledger" FlexButton(ghost)

- Interactions:
  - click account row: FlexDrawer opens; GET /financial/accounts/{id}/balance?as_of=today → balance displays
  - change "As of" date: GET /financial/accounts/{id}/balance?as_of=DATE → balance updates; mini-ledger re-fetches
  - click "View Full Ledger": navigates to `#/financial/reports/account-ledger?account_id={id}`

- States:
  - loading: balance-section and mini-ledger show skeleton while fetch resolves
  - no-transactions: mini-ledger shows "No transactions in this period"

---

## Feature 12.2 — Invoicing with Workflow `[DONE]`

### Story 12.2.1 — Invoice Creation and Posting `[IN-PROGRESS]`

#### Backend
*As an API, I want to create invoices with line items and post them to the general ledger via double-entry journal entries, so that revenue is correctly recognized.*
- `POST /api/v1/financial/invoices` creates an invoice in `DRAFT` status
- Line items: `{description, quantity, unit_price, account_id, tax_rate_id?}`
- `POST /api/v1/financial/invoices/{id}/post` validates, transitions to `POSTED`, auto-generates journal entries (DR Accounts Receivable, CR Revenue + Tax Payable)
- Invoice number auto-generated: configurable prefix + zero-padded sequence per company

#### Frontend
*As a billing administrator on the invoice creation page, I want a form with a customer selector, invoice details, and an interactive line items table where I can add rows, set quantities and prices, and see the subtotal, tax, and total update in real time, so that creating an invoice is fast and error-free.*
- Route: `#/financial/invoices/new` → `financial-invoice-form.html` + `financial-invoice-form-page.js`
- Layout: FlexSplitPane(initial-split=70%) > form-panel, summary-panel
  - form-panel: FlexStack(direction=vertical) > header-fields, line-items-table, sticky-footer
    - header-fields: FlexGrid(columns=2) — Customer (FlexSelect, searchable) | Invoice # (FlexInput, auto-filled, editable) | Invoice Date (FlexDatepicker) | Due Date (FlexDatepicker) | Notes (FlexTextarea, full-width)
    - line-items-table: table rows — Description (FlexInput) | Account (FlexSelect) | Quantity (FlexInput, type=number) | Unit Price (FlexInput, type=number) | Tax Rate (FlexSelect) | Amount (read-only, calculated) | × delete icon
    - "Add Line" FlexButton(ghost) below table
    - sticky-footer: FlexToolbar — Cancel | "Save as Draft" FlexButton(ghost) | "Post Invoice" FlexButton(primary)
  - summary-panel: FlexCard(sticky) — Subtotal | Tax breakdown per rate | **Total** (large bold text)

- `PostConfirmModal` FlexModal(size=sm) triggered by "Post Invoice":
  - body: "Posting will create journal entries and cannot be easily reversed. Continue?"
  - footer: Cancel | "Post Invoice" FlexButton(primary)

- Interactions:
  - change Quantity or Unit Price in a line row: Amount recalculates; summary-panel totals update immediately
  - change Tax Rate in a line row: Tax breakdown in summary-panel updates
  - click "Add Line": new blank row appended to line-items-table
  - click × on line row: row removed; totals recalculate
  - click "Save as Draft": POST /financial/invoices {status: DRAFT} → redirect to `#/financial/invoices/{id}`
  - click "Post Invoice": opens PostConfirmModal → confirm: POST /financial/invoices/{id}/post → redirect to invoice detail with FlexBadge(color=success) "Posted"

- States:
  - saving: sticky-footer buttons show spinner; form disabled
  - posted: redirect to invoice detail view

---

### Story 12.2.2 — Invoice Workflow States `[DONE]`

#### Backend
*As an API, I want invoices to transition through defined states with enforced rules, so that the financial lifecycle is controlled.*
- Lifecycle: `DRAFT → POSTED → PARTIALLY_PAID → PAID → VOID`
- `POST /api/v1/financial/invoices/{id}/void` creates reversal journal entries; sets `voided_at` and `void_reason`
- Invalid transitions return 400 with `INVALID_INVOICE_TRANSITION`

#### Frontend
*As a finance manager on the invoice list page, I want to see the status of each invoice at a glance with color-coded badges, and be able to filter by status, so that I can quickly identify outstanding and overdue invoices.*
- Route (list): `#/financial/invoices` → `financial-invoices.html` + `financial-invoices-page.js`
- Route (detail): `#/financial/invoices/{id}` → invoice detail page
- Layout (list): FlexStack(direction=vertical) > page-header, filter-bar, invoices-grid
  - page-header: FlexToolbar — "Invoices" title | "New Invoice" FlexButton(primary)
  - filter-bar: FlexCluster — status chips (All / Draft / Posted / Unpaid / Paid / Void) | Customer FlexSelect(searchable) | Date range FlexDatepicker pair
  - invoices-grid: FlexDataGrid — Invoice # | Customer | Issue Date | Due Date | Amount | Status FlexBadge | Actions

- Status FlexBadge colors: Draft=neutral | Posted=info | Partially Paid=warning | Paid=success | Void=danger (strikethrough text)
- Overdue: secondary FlexBadge(color=danger) "Overdue" shown alongside Posted/Partially Paid when `due_date < today`

- Layout (detail): FlexStack(direction=vertical) > detail-header, invoice-body, detail-tabs
  - detail-header: FlexToolbar — FlexBreadcrumb | Invoice # | status FlexBadge | available action FlexButtons (Post / Void / Record Payment — shown per current state)
  - invoice-body: header fields (read-only) + line items table (read-only)
  - detail-tabs: FlexTabs — Details | Payments

- `VoidModal` FlexModal(size=sm) triggered by "Void Invoice":
  - fields: Reason (FlexTextarea, required)
  - footer: Cancel | "Void Invoice" FlexButton(variant=danger)

- Interactions:
  - click status chip in filter-bar: GET /financial/invoices?status=X → grid refreshes
  - click "Void Invoice" action: opens VoidModal → confirm: POST /financial/invoices/{id}/void {reason} → status FlexBadge updates to Void
  - click "Record Payment": navigates to `#/financial/payments/new?customer_id={X}&invoice_id={id}`

- States:
  - loading: invoices-grid shows skeleton rows
  - empty: "No invoices found" + "New Invoice" FlexButton(primary)
  - empty (filtered): "No invoices match the selected filters"

---

### Story 12.2.3 — Payment Recording and Allocation `[DONE]`

#### Backend
*As an API, I want to record payments and allocate them against invoices, so that outstanding balances and invoice statuses are accurate.*
- `POST /api/v1/financial/payments` records a payment: `{customer_id, amount, payment_date, payment_method, reference}`
- `POST /api/v1/financial/payments/{id}/allocate` accepts `{allocations: [{invoice_id, amount}]}`
- Partial allocation → invoice `PARTIALLY_PAID`; full → `PAID`; creates DR Cash / CR Accounts Receivable journal entries

#### Frontend
*As an accountant recording a customer payment, I want to enter the payment amount and then see a list of the customer's outstanding invoices where I can allocate amounts against each one, so that payment application is clear and accurate.*
- Route: `#/financial/payments/new` → `financial-payment-form.html` + `financial-payment-form-page.js`
- Layout: FlexStack(direction=vertical) > payment-details-section, allocation-section, sticky-footer
  - payment-details-section: FlexGrid(columns=2) — Customer (FlexSelect) | Amount (FlexInput, type=number) | Payment Date (FlexDatepicker) | Method (FlexSelect: Cash / Bank Transfer / Card / Cheque) | Reference (FlexInput)
  - allocation-section: FlexStack > "Auto-allocate" FlexButton(ghost) | allocation-table | running-total-bar
    - allocation-table: FlexDataGrid(static) — Invoice # | Due Date | Original Amount | Outstanding | Allocate (FlexInput, type=number) per row
    - running-total-bar: FlexCluster — "Allocated: $X" | "Unallocated: $Y" FlexBadge(color=warning, shown when > 0)
  - sticky-footer: FlexToolbar — Cancel | "Save Payment" FlexButton(primary)

- Interactions:
  - select Customer: allocation-table populates with customer's POSTED/PARTIALLY_PAID invoices
  - type in Allocate input: running-total-bar recalculates Allocated and Unallocated amounts immediately
  - click "Auto-allocate": fills Allocate inputs oldest-first up to payment Amount; running-total-bar updates
  - click "Save Payment" with unallocated > 0: FlexAlert(type=warning, inline) "You have $Y unallocated. This will be held as unapplied credit." — requires explicit second confirm
  - click "Save Payment" (balanced): POST /financial/payments → POST /financial/payments/{id}/allocate → redirect to customer or invoice detail

- States:
  - no-customer-selected: allocation-section hidden; "Select a customer to see outstanding invoices"
  - fully-allocated: Unallocated badge hidden; running-total-bar shows green confirmation
  - saving: sticky-footer buttons show spinner; form disabled

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
- Route: `#/financial/journal-entries/new` → `financial-journal-entry-form.html` + `financial-journal-entry-form-page.js`
- Layout: FlexStack(direction=vertical) > header-fields, lines-table, balance-bar, sticky-footer
  - header-fields: FlexGrid(columns=2) — Date (FlexDatepicker) | Reference (FlexInput) | Description (FlexInput) | Period (FlexSelect)
  - lines-table: table rows — Account (FlexSelect, searchable) | Description (FlexInput) | Debit (FlexInput, type=number) | Credit (FlexInput, type=number) | × delete; minimum 2 rows
  - "Add Line" FlexButton(ghost) below table
  - balance-bar: FlexCluster — "Debits: $X" | "Credits: $Y" | "Difference: $Z" FlexBadge (color=success when $Z=0, color=danger when $Z≠0)
  - sticky-footer: FlexToolbar — Cancel | "Save Draft" FlexButton(ghost) | "Post Entry" FlexButton(primary)

- Interactions:
  - type in Debit or Credit: balance-bar totals recalculate immediately
  - "Post Entry" button: disabled + FlexTooltip "Entry must balance before posting" when $Z ≠ 0; enabled when balanced
  - click "Post Entry" (balanced): POST /financial/journal-entries/{id}/post → FlexAlert(type=info) banner "This entry has been posted and cannot be modified. To correct it, use Reverse Entry." + "Reverse Entry" FlexButton(ghost) shown
  - click "Reverse Entry": POST /financial/journal-entries/{id}/reverse → navigate to new draft entry with lines pre-filled

- States:
  - unbalanced: balance-bar shows red $Z badge; "Post Entry" disabled
  - balanced: balance-bar shows green $Z=0 badge; "Post Entry" enabled
  - posted: form fields read-only; FlexAlert(type=info) banner shown; "Reverse Entry" button visible

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
- Route: `#/financial/reports` → `financial-reports.html` + `financial-reports-page.js`
- Layout: FlexSplitPane(initial-split=18%) > reports-sidebar, report-area
  - reports-sidebar: FlexStack(direction=vertical) — nav links: Trial Balance | Balance Sheet | Income Statement | Aged Receivables | Cash Flow | Account Ledger
  - report-area: FlexStack(direction=vertical) > report-controls, report-output

- report-controls (per report type):
  - balance-sheet / trial-balance: "As Of" FlexDatepicker + "Run Report" FlexButton(primary)
  - income-statement / cash-flow: From FlexDatepicker + To FlexDatepicker + "Run Report" FlexButton(primary)
  - aged-receivables: "As Of" FlexDatepicker + "Run Report" FlexButton(primary)
  - account-ledger: Account FlexSelect + From/To FlexDatepicker pair + "Run Report" FlexButton(primary)
  - shared toolbar: "Export" FlexButton(split, dropdown: PDF / Excel / CSV) | "Print" FlexButton(ghost)

- report-output layouts:
  - Balance Sheet: FlexGrid(columns=2) — Assets column (left) | Liabilities + Equity column (right); section subtotals; grand total row
  - Income Statement: Revenue section → Expenses section → Net Income/Loss row (green text if profit, red if loss)
  - Aged Receivables: table — customer rows × aging bucket columns (0-30 / 31-60 / 61-90 / 90+); "Total Outstanding" column; 90+ cells highlighted red
  - Other reports: single-column structured table with section headers and subtotals

- Interactions:
  - click sidebar nav link: report-area switches to selected report; controls update for that report type
  - click "Run Report": GET /financial/reports/{type}?params → report-output renders
  - click "Print": `window.print()` with print-optimized CSS
  - click "Export" option: POST /reports/{type}/export?format=X → file download

- States:
  - loading: report-output shows skeleton table while fetch resolves
  - empty: "No data for the selected period"
  - not-run: report-output shows "Select a period and click Run Report"

---

### Story 12.4.2 — Tax Rate Management `[IN-PROGRESS]`

#### Backend
*As an API, I want to manage tax rates that can be applied to invoice line items, so that tax calculations are consistent.*
- `POST /api/v1/financial/tax-rates` with `{name, rate, account_id, is_compound, is_active}`
- `POST /api/v1/financial/tax-rates/calculate` accepts `{subtotal, tax_rate_id}` and returns `{tax_amount, total}`

#### Frontend
*As a finance administrator on the tax rates page, I want to add, edit, and deactivate tax rates in a simple table, and see a live calculation preview when entering a rate, so that tax setup is straightforward.*
- Route: `#/financial/tax-rates` → `financial-tax-rates.html` + `financial-tax-rates-page.js`
- Layout: FlexStack(direction=vertical) > page-header, tax-rates-grid
  - page-header: FlexToolbar — "Tax Rates" title | "Add Tax Rate" FlexButton(primary)
  - tax-rates-grid: FlexDataGrid — Name | Rate % | GL Account | Type | Status FlexBadge | Actions (Edit / Deactivate)

- `TaxRateModal` FlexModal(size=sm) triggered by "Add Tax Rate" or Edit:
  - fields: Name (FlexInput, required) | Rate % (FlexInput, type=number) | GL Account (FlexSelect, from Chart of Accounts) | Compound (FlexCheckbox toggle) | Active (FlexCheckbox toggle)
  - live preview (below Rate % input): "On a $100 subtotal: Tax = $X, Total = $Y" — updates as Rate % changes
  - footer: Cancel | Save FlexButton(primary)

- `DeactivateModal` FlexModal(size=sm) triggered by "Deactivate":
  - body: warning if rate referenced by draft invoices: "This rate is used in X draft invoices."
  - footer: Cancel | "Deactivate" FlexButton(variant=danger)

- Interactions:
  - type in Rate % field: live preview recalculates immediately
  - click "Deactivate": opens DeactivateModal → confirm: PATCH /financial/tax-rates/{id} {is_active: false} → row Status FlexBadge updates
  - archived rates: appear with "(Archived)" suffix in invoice line item FlexSelect — selectable on existing invoices only

- States:
  - loading: tax-rates-grid shows skeleton rows
  - empty: "No tax rates configured" + "Add Tax Rate" FlexButton(primary)

---

## Feature 12.5 — Financial Module Planned Enhancements `[PLANNED]`

### Story 12.5.1 — Vendor Management and Accounts Payable `[PLANNED]`

#### Backend
*As an API, I want vendor and bill management endpoints mirroring the customer/invoice structure, so that the full payables cycle is covered.*
- `POST /api/v1/financial/vendors`, `/bills`, `/bills/{id}/post`, `/bills/{id}/pay`
- `GET /api/v1/financial/reports/aged-payables?as_of=DATE`

#### Frontend
*As an accountant on the bills page, I want the same workflow as invoices — create, post, and pay — but for vendor bills, so that payables are managed consistently with receivables.*
- Route (bills): `#/financial/bills` → mirrors `#/financial/invoices` layout with "Vendor" label in place of "Customer"
- Route (vendors): `#/financial/vendors` → mirrors customer master page layout with "Vendor" terminology
- Route (new bill): `#/financial/bills/new` → mirrors invoice creation form with Vendor FlexSelect replacing Customer

- Layout: identical to invoices page (Story 12.2.2) and invoice form (Story 12.2.1) with label substitution only
- reports-sidebar addition: "Aged Payables" link added to financial reports sidebar below "Aged Receivables"

- Interactions: identical to invoice and payment flows; all API paths use `/bills` and `/vendors` prefixes

---

### Story 12.5.2 — Bank Reconciliation `[PLANNED]`

#### Backend
*As an API, I want bank account and statement import endpoints, so that accountants can match bank transactions to GL entries.*
- `POST /api/v1/financial/bank-accounts`, `POST /api/v1/financial/bank-accounts/{id}/import-statement` (CSV)
- Matching logic: auto-match by amount + date proximity

#### Frontend
*As an accountant doing a bank reconciliation, I want to see unmatched bank transactions on the left and unmatched GL entries on the right, and drag a bank transaction to a GL entry to match them, so that reconciliation is visual and efficient.*
- Route: `#/financial/bank-reconciliation/{account_id}` → `financial-reconciliation.html` + `financial-reconciliation-page.js`
- Layout: FlexStack(direction=vertical) > recon-header, recon-panes, matched-section
  - recon-header: FlexToolbar — account name | "Auto-Match" FlexButton(ghost) | totals bar (Unmatched Bank: $X | Unmatched GL: $Y | Difference: $Z FlexBadge) | "Complete Reconciliation" FlexButton(primary)
  - recon-panes: FlexSplitPane(initial-split=50%) > bank-panel, gl-panel
    - bank-panel: FlexStack > "Bank Statement" label | FlexDataGrid — Date | Description | Amount; rows draggable
    - gl-panel: FlexStack > "GL Entries" label | FlexDataGrid — Date | Description | Debit | Credit; rows are drop targets
  - matched-section: FlexAccordion (collapsed) — matched pairs list

- Interactions:
  - drag bank statement row onto GL entry row: pair matched; both rows move to matched-section; totals bar recalculates
  - click "Auto-Match": POST /financial/bank-reconciliation/{id}/auto-match → matched pairs appear in matched-section; unmatched rows remain
  - Difference reaches $0: "Complete Reconciliation" button enables
  - click "Complete Reconciliation": POST /financial/bank-reconciliation/{id}/complete → redirect to account detail

- States:
  - loading: both panels show skeleton rows
  - balanced (difference=$0): Difference FlexBadge turns green; "Complete Reconciliation" button enabled
  - unbalanced: Difference FlexBadge shows red; "Complete Reconciliation" button disabled
