---
artifact_id: adr-hc-008
type: adr
module: healthcare_reporting
status: proposed
producer: B1 Backend Architect
upstream: [BACKLOG.md (v3), adr-hc-001, adr-hc-002, adr-hc-005, adr-hc-006, adr-hc-007, schema-hc-01, epic-12-reporting-dashboard]
created: 2026-07-02
---

# ADR-HC-008 — Reporting & Dashboard Integration

## Status

proposed

## Context

BACKLOG v3 makes Healthcare Reporting & Executive Dashboard an MVP deliverable (module
`healthcare_reporting`, epic-12) that **reuses the platform Reports engine**
(`backend/app/routers/reports.py`, `services/report_service.py`) and **Dashboard engine**
(`backend/app/routers/dashboards.py`, `services/dashboard_service.py`) — the Reuse Register forbids
rebuilding a report/dashboard designer inside healthcare. Healthcare supplies **datasets/widgets**, not
a new engine.

The hard constraint: healthcare data is branch-scoped and much of it is PHI (ADR-HC-001, ADR-HC-002).
The platform report/dashboard engines are generic and tenant-scoped; they must be able to read
healthcare aggregates **without** (a) leaking PHI or (b) crossing branch isolation.

The platform Reports engine binds to no-code **`EntityDefinition`** data sources (its
join-suggestion logic walks `EntityDefinition`/`FieldDefinition`/`RelationshipDefinition`), and the
Dashboard engine renders **widgets** over data sources. So the integration question is: *what* does
healthcare expose as a bindable data source, and *how* is it scoped.

Design questions:
1. What is the read-safe interface healthcare exposes to the platform engines?
2. How is tenant/branch scoping enforced inside that interface?
3. How do platform report/dashboard definitions bind to it?

## Decision

### D1 — Expose read-only, PHI-free **database views** as the reporting interface

Healthcare exposes a fixed set of read-only Postgres **views** (canonical names per BACKLOG) as the
*only* surface the platform Reports/Dashboards engines read:

| View | Grain | Purpose | Source tables |
|---|---|---|---|
| `v_hc_daily_patients` | branch × day | Patient/visit volume | `hcr_visits` (ADR-HC-006) |
| `v_hc_doctor_productivity` | branch × provider × day | Encounters/visits per doctor | `hc_encounters`, `hc_providers`, `hcr_visits` |
| `v_hc_queue` | branch × dept × day | Wait/service times, throughput | `hcr_queue_tickets`, `hcr_visits`, `hc_departments` |
| `v_hc_appointments` | branch × day (× status) | Booking/attendance/no-show | `hcs_appointments` |
| `v_hc_revenue` | branch × day (× payer) | Invoiced/paid amounts | `hcb_invoices`, `hcb_payments` |
| `v_hc_disease_stats` | branch × icd10_code × period | Diagnosis frequency | `hc_diagnoses`, `hc_icd10_codes` (ADR-HC-007) |
| `v_hc_drug_usage` | branch × drug × period | Dispense volume | `hcp_dispensing_log`, `hcp_dispensing_items`, `hcp_medication_catalog` |
| `v_hc_lab_utilization` | branch × test × period | Test order/result volume, TAT | `hcl_test_orders`, `hcl_test_order_items`, `hcl_test_catalog` |

**No raw PHI columns.** Every view is defined to select **aggregates and non-PHI dimensions only** —
counts, sums, durations, codes, dates, `tenant_id`, `branch_id`, `department_id`, `provider_id`. No
view selects `hc_patients` PHI, `hc_encounters` SOAP fields, `hc_clinical_notes.body`, or any
`EncryptedPHIType` column. `v_hc_disease_stats` exposes ICD **codes and counts only** (never notes or
patient identifiers, per ADR-HC-007 D3). `provider_id` is an internal id (a staff dimension, not
patient PHI); patient identity never appears. This makes the interface **PHI-safe by construction** —
the engines physically cannot select PHI because the views do not expose it.

**Why views (not direct table access, not an API):**
- The platform engines already read tabular data sources; a view is the least-friction bindable
  object and lets us pin the exact, PHI-free column set as a hard contract.
- The view is the PHI firewall: it is authored once by healthcare and reviewed; the report designer
  cannot widen it.

### D2 — Tenant/branch scoping enforced **inside** the views via session GUCs

Each view carries `tenant_id` and (where applicable) `branch_id` as columns **and** filters on the
ADR-HC-001 session settings so scoping cannot be bypassed by the caller:

```sql
CREATE VIEW v_hc_daily_patients AS
SELECT tenant_id, branch_id, service_day, COUNT(*) AS patient_count, ...
FROM hcr_visits
WHERE tenant_id = current_setting('app.tenant_id', true)
  AND (branch_id = current_setting('app.branch_id', true)
       OR current_setting('app.branch_id', true) = 'ALL')
GROUP BY tenant_id, branch_id, service_day;
```

- The views are defined over branch-scoped base tables that **already** carry RLS (ADR-HC-001 `§D4`);
  the in-view `current_setting` predicates make scoping explicit and independent of whether the
  querying role inherits RLS, giving defence-in-depth. Views are created with
  `security_invoker = true` (Postgres 15+) so the base-table RLS of the querying role also applies.
- **Branch scoping.** A Branch Manager / Doctor session (`healthcare_branch_session`, `app.branch_id`
  = their branch) sees only their branch's rows. A **Clinic Owner** aggregate-reporting session sets
  `app.branch_id = 'ALL'` (ADR-HC-001 `§D2`/`§D3`) and sees all branches within their tenant — this
  is exactly the "aggregated, non-PHI metrics" carve-out ADR-HC-001 already grants the owner
  reporting path. `tenant_id` is **always** filtered, so no cross-tenant leakage is ever possible.
- The `report_service` / `dashboard_service` must run healthcare-view queries on a connection where
  `app.tenant_id` (and `app.branch_id`, defaulting to `'ALL'` for owner-level dashboards) are set —
  the healthcare reporting adapter (epic-12) sets these on the reporting session, mirroring
  `healthcare_branch_session`.

### D3 — Binding: register each view as a read-only platform data source

The platform Reports engine binds to `EntityDefinition` data sources; healthcare registers each view
as a **read-only, system-managed `EntityDefinition`** (one per view) whose fields map to the view's
columns, seeded by the epic-12 reporting adapter:

- The registration is **metadata-only** (an `EntityDefinition` marked read-only / `is_view = true`
  pointing at the view name); it does not create a table. Report authors select these entities in the
  query builder and dashboards bind widgets to them exactly like any other data source — no engine
  code change.
- `RelationshipDefinition` rows join the views on their shared dimensions (`branch_id`,
  `provider_id`, `department_id`, `service_day`) so the engine's join-suggestion logic
  (`reports.py /entities/join-suggestions`) can offer cross-view reports (e.g. revenue × doctor
  productivity) — still PHI-free, since every joinable column is a non-PHI dimension.
- **Permissions.** Access to the healthcare reporting entities is gated by existing RBAC
  (`reports:*`, `dashboards:*` permissions) plus the healthcare role seeds (`hc_permissions.py`); a
  branch-scoped role's session GUCs (D2) further constrain rows. Report/dashboard *definitions* are
  stored by the platform engines unchanged; only their bound data source is a healthcare view.

### D4 — Isolation & PHI conformance summary

- **Branch isolation:** enforced twice — base-table RLS (ADR-HC-001 `§D4`) + in-view
  `current_setting` predicates; `tenant_id` always filtered.
- **PHI:** no view exposes a PHI/encrypted column; the aggregate grain removes patient identifiers.
  No SDK reader/audit entry is needed because **no PHI is read** — the ADR-HC-002 audit obligation
  applies to PHI reads, and reporting reads none. (Row-level PHI drill-downs are explicitly *not*
  offered through this surface; they remain in the clinical modules behind SDK readers + audit.)
- The views are **additive and read-only**; they change no base-table behavior and touch no platform
  table definitions.

## Consequences

### Positive
- **Reuse honored:** the platform Reports/Dashboards engines are used unchanged; healthcare adds only
  views + data-source metadata (epic-12), matching the Reuse Register.
- **PHI-safe by construction:** the engines cannot select PHI because the view column set excludes it;
  no per-report review of PHI leakage is required.
- **Branch isolation preserved:** in-view tenant/branch predicates + base RLS mean a branch role sees
  only its branch; owner sees tenant-wide aggregates via the sanctioned `'ALL'` path.
- **Owner exec dashboards** work through the existing `clinic_owner` aggregate carve-out — no new
  isolation exception invented.

### Negative
- **View maintenance:** each new metric may need a view or column change, coordinated with base-table
  schema. Mitigation: views are the stable contract; base-table internals can change as long as the
  view column set is preserved (same discipline as ADR-HC-002 DTOs).
- **Aggregate-only:** no PHI/row-level drill-down through reporting. Mitigation: intentional — PHI
  drill-down stays in clinical modules behind SDK readers + audit.
- **GUC-set reporting session required:** the reporting adapter must set `app.tenant_id`/
  `app.branch_id` on the engine's DB session. Mitigation: epic-12 adapter centralizes this; covered by
  an isolation integration test (owner vs branch-scoped role sees different row sets).

## Alternatives Considered

| Alternative | Rejected because |
|---|---|
| Let the report engine query healthcare base tables directly | Exposes PHI/encrypted columns and full branch data to the generic query builder; no PHI firewall. Views pin a safe column set. |
| Expose reporting via a healthcare REST/SDK API the engine calls | Duplicates the engine's query/aggregation capability; breaks reuse; harder to bind in the no-code designer. Views bind natively. |
| Materialized views / a separate reporting DB | Premature at MVP scale; adds refresh/staleness and a second isolation surface. Plain views suffice; revisit materialization at R3 exec-dashboard/BI scale (epic-19). |
| Rely only on base-table RLS (no in-view predicates) | Depends on the reporting connection's role inheriting RLS correctly; the in-view predicates make scoping explicit and independent, giving defence-in-depth. |

## Reference Map

| File | Relevance |
|------|-----------|
| `backend/app/routers/reports.py`, `services/report_service.py` | Platform Reports engine; binds to `EntityDefinition` data sources |
| `backend/app/routers/dashboards.py`, `services/dashboard_service.py` | Platform Dashboard engine; widgets bind to data sources |
| `backend/app/routers/data_model.py` | `EntityDefinition`/`FieldDefinition`/`RelationshipDefinition` used to register views as read-only data sources |
| `plan-mod-healthcare/architecture/adr-hc-001-branch-isolation-strategy.md` | RLS `§D4`, `clinic_owner` `'ALL'` aggregate carve-out |
| `plan-mod-healthcare/architecture/adr-hc-002-cross-module-phi-data-sharing.md` | PHI-read audit obligation (N/A here — no PHI read) |
| `plan-mod-healthcare/architecture/adr-hc-005-org-linkage-departments.md` | `department_id` dimension for dept-scoped reports |
| `plan-mod-healthcare/architecture/adr-hc-006-visit-queue.md` / `adr-hc-007-clinical-coding.md` | Sources for `v_hc_daily_patients`, `v_hc_queue`, `v_hc_disease_stats` |
| `plan-mod-healthcare/architecture/schema-hc-02.md` | DDL for all eight reporting views |
| `plan-mod-healthcare/BACKLOG.md` | v3 Canonical view names, Reuse Register (Reports/Dashboard engines) |
