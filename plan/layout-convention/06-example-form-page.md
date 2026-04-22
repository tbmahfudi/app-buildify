# Example 2 — Form Page (Invoice Creation)

This example shows a full-width form page with a live summary sidebar, editable line-items table, and a post confirmation modal.

---

```markdown
#### Frontend
*As a billing administrator, I want to fill in customer details, add line items, and post
the invoice on a single full-width page with a live total panel.*

- Route: `#/financial/invoices/new` → `invoice-form.html` + `invoice-form-page.js`
- Layout: FlexSidebar(side=right, sidebar-width=300px) > form-body, summary-panel
  - form-body: FlexStack(direction=vertical, gap=lg) — page-header | header-fields | line-items | notes
    - page-header: FlexToolbar — FlexBreadcrumb | status chip | "Save Draft" | "Post Invoice" (primary)
    - header-fields: FlexGrid(columns=2, gap=md) — Customer (FlexSelect, searchable) | Invoice # (FlexInput, auto-filled) | Invoice Date (FlexDatepicker) | Due Date (FlexDatepicker)
    - line-items: FlexSection — editable table + "Add Line" FlexButton(ghost)
  - summary-panel: FlexStack(gap=sm, sticky) — Subtotal | Tax breakdown | Total (bold) | payment terms

- FlexTable(editable-rows) — line items, client-side state
  - columns: Description (FlexInput inline) | Account (FlexSelect inline) | Qty (FlexInput, number) | Unit Price (FlexInput, number) | Tax Rate (FlexSelect) | Amount (calculated, disabled)
  - on row-change: summary panel totals recalculate instantly

- FlexModal(size=sm) — "Post Invoice" confirm, triggered by Post button
  - footer: Cancel | Post Invoice (FlexButton, variant=danger-outline)
  - on confirm: POST /financial/invoices/{id}/post → redirect to invoice detail

- Interactions:
  - change any header field: summary panel recalculates totals instantly (client-side)
  - change line item Qty or Unit Price: Amount cell updates in real time; summary panel totals update
  - click "Add Line": appends a blank row; focus moves to Description cell of new row
  - click trash icon on line row: removes row immediately (no confirm for unsaved rows)
  - click "Save Draft": PATCH /financial/invoices/{id} → success toast "Draft saved" | error FlexAlert(type=error)
  - click "Post Invoice": opens confirm FlexModal → on confirm POST /invoices/{id}/post → redirects to invoice detail
  - keyboard Tab within line item: moves focus across cells left-to-right; Tab on last cell of last row adds a new row
  - keyboard Escape: if FlexSelect is open closes it; if FlexModal is open closes it

- States:
  - saving: "Save Draft" button shows spinner; all inputs disabled
  - posting: full-page overlay "Posting invoice…"
  - post-error: FlexAlert(type=error) above line items; inputs re-enabled
  - posted: redirect to detail view; FlexBadge(color=success) "Posted"; fields become read-only

- Responsive:
  - lg−: summary-panel collapses to sticky bottom bar showing Total only; "View Summary" toggle expands it
  - md−: header-fields drops to single column; line items table scrolls horizontally
```

---

## Notation types used

| # | Type | Used? | Notes |
|---|------|-------|-------|
| 1 | Page Layout Block | Yes | `FlexSidebar` root with form-body and summary-panel |
| 2 | Zone Notation | Yes | Two-level nesting inside form-body |
| 3 | Component Spec | Yes | `FlexTable` and `FlexModal` specified |
| 4 | Responsive Notation | Yes | Two breakpoints, including summary-panel collapse |
| 5 | State Notation | Yes | saving, posting, post-error, posted |
| 6 | Interaction Notation | Yes | 8 interactions including keyboard Tab flow |
