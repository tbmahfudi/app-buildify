---
artifact_id: epic-16-inventory
status: active
version: 1
module: healthcare_inventory
launch_phase: R3
producer: A3 Product Owner
upstream: BACKLOG v3
created: 2026-07-02
---

# Epic 16 — Inventory: Purchasing & Warehouse

**Module:** `healthcare_inventory` (requires `healthcare` base; extends the existing pharmacy drug-stock model, epic-04)
**Launch Phase:** R3
**Depth:** Outline (epic header + one-line story list; detailed AC/UILDC deferred to build time).
**Summary:** Procurement (purchase order → goods receipt → supplier invoice) and warehouse operations
(stock transfer, stock adjustment, physical count) layered over the branch drug/consumables stock from epic-04.
Billing-only finance stance inherited (no GL/AR — supplier invoices are recorded, not posted to a ledger).

---

## Feature 16.1 — Procurement
- Story 16.1.1 — Staff creates a purchase order to a supplier with line items (drug/consumable, qty, price).
- Story 16.1.2 — Staff records goods receipt against a PO (full/partial), incrementing branch stock.
- Story 16.1.3 — Staff records the supplier invoice against the receipt (recorded only; GL/AR deferred).

## Feature 16.2 — Warehouse Operations
- Story 16.2.1 — Staff transfers stock between branches/departments with an auditable movement record.
- Story 16.2.2 — Staff performs a stock adjustment (damage/expiry/correction) with reason and audit.
- Story 16.2.3 — Staff runs a physical count (stock-take) and reconciles counted vs system quantities.

## Story Count: Feature 16.1 (3) + 16.2 (3) = **6 stories**
