---
artifact_id: epic-12-reporting-dashboard
status: active
version: 1
module: healthcare_reporting
launch_phase: MVP
producer: A3 Product Owner
upstream: BACKLOG v3
created: 2026-07-02
---

# Epic 12 — Healthcare Reporting & Executive Dashboard

**Module:** `healthcare_reporting` (requires `healthcare` base + reporting sub-modules for data)
**Launch Phase:** MVP
**Summary:** Healthcare **reporting datasets/templates** and **dashboard widgets** that bind to the
**platform Reports engine** (Reuse Register #15 — `routers/reports.py`, `services/report_service.py`) and the
**platform Dashboards engine** (Reuse Register #16 — `routers/dashboards.py`, `services/dashboard_service.py`).

> **REUSE, do not rebuild.** This epic ships **no report engine, no dashboard engine, no query builder, no
> export/scheduler** — those already exist on the platform. It ships (a) healthcare **datasets** that register
> the read-only `v_hc_*` views from ADR-HC-008 as report data sources, (b) healthcare **report templates**
> that lay out those datasets, and (c) healthcare **dashboard widgets** that read those datasets. All PHI
> rules, branch/tenant scoping, CSV/Excel/PDF export, scheduled delivery, and sharing come from the platform
> engines. Datasets are bound to views with **no raw PHI columns**, branch/tenant scoped, per the Hand-off
> Notice invariants.

**Bound views (ADR-HC-008, no raw PHI):** `v_hc_daily_patients`, `v_hc_doctor_productivity`, `v_hc_queue`,
`v_hc_appointments`, `v_hc_revenue`, `v_hc_disease_stats`, `v_hc_drug_usage`, `v_hc_lab_utilization`.

---

## Feature 12.1 — Healthcare Report Datasets (bind to platform Reports engine)

### Story 12.1.1 [OPEN]
**As a** Clinic Owner or Branch Manager,
**I want to** register the healthcare `v_hc_*` views as report datasets on the platform Reports engine,
**so that** I can build, run, filter, schedule, and export healthcare reports using the existing report tooling.

**Backend AC:**
- Seed/register healthcare **datasets** into the platform report catalog (`services/report_service.py`), one per bound view: daily patients, doctor productivity, queue, appointment, revenue, disease stats, drug usage, lab utilization. Each dataset declares its columns, filterable dimensions (branch, department, date range, provider, specialty as applicable), and measures — **no engine code is added**.
- Each dataset is bound to its `v_hc_*` view (read-only, no raw PHI columns, branch/tenant scoped via the view's RLS); the platform engine applies existing export (CSV/Excel/PDF), scheduling, and permission checks.
- Dataset access respects platform RBAC (Reuse Register #3): datasets are visible only to roles with reporting permission at the caller's branch/tenant; branch-scoped roles see only their branch rows via the view.
- No new PHI path is introduced; if a report requires a patient-identifying breakdown, it is out of scope for these datasets (aggregate/coded only). Dataset registration is idempotent and versioned with the module.

**Frontend AC:**
- No new report-builder UI is built; healthcare datasets appear in the **platform Reports** dataset picker (`routers/reports.py` UI) under a "Healthcare" group.
- Users pick a healthcare dataset, apply the platform's standard filters, and use the platform's run/export/schedule controls.
- Dataset names/labels localized (ID / EN) via the platform's label mechanism.

---

#### Frontend (UILDC v1.0)

- **Route:** platform Reports UI (`#/reports/*`) — healthcare datasets surface inside the existing report builder; **no new healthcare route**.
- **Portal:** Clinic Portal (platform Reports module)
- **Layout:** Reuses the platform Reports layout; healthcare datasets appear as a grouped section ("Kesehatan" / Healthcare) in the dataset picker.
- **Components (all platform-provided — bound, not rebuilt):**
  - Platform dataset picker — healthcare datasets listed under a Healthcare group
  - Platform filter panel — branch, department, date range, provider, specialty (as each dataset declares)
  - Platform run / export (CSV/Excel/PDF) / schedule controls
  - `FlexBadge` — "Kesehatan" group label; per-dataset localized name
- **Key interactions:**
  - User opens the platform report builder → selects a healthcare dataset → the engine loads the bound `v_hc_*` view columns/filters.
  - Filtering, running, exporting, and scheduling all use existing platform controls; branch-scoped roles are auto-limited by the view.
  - No PHI columns are selectable (the datasets do not expose them).
- **Empty state:** Platform empty state; if no healthcare sub-module data yet: "Belum ada data untuk dataset ini." (No data yet for this dataset.)
- **Error state:** Platform error handling; permission denied uses the platform's standard message.
- **i18n:** Healthcare dataset names, group label, and column labels localized (ID / EN); everything else inherits platform i18n.
- **Mobile:** Inherits platform Reports responsiveness (secondary use case).

### Story 12.1.2 [OPEN]
**As a** Branch Manager,
**I want to** run daily patient-volume and appointment reports from the healthcare datasets,
**so that** I can monitor operational throughput per branch and department.

**Backend AC:**
- Bind report templates over `v_hc_daily_patients` (visits/day by branch, department, visit type, new vs returning) and `v_hc_appointments` (booked/attended/no-show/cancelled by provider, day, status) using the platform Reports engine — no new query engine.
- Filters (branch, department, date range, provider) map to view dimensions; aggregates only (counts, rates) — no patient rows.
- Export/schedule via platform engine; scheduled delivery uses the platform scheduler + notification transport (Reuse Register).

**Frontend AC:**
- Delivered as **platform report templates** selectable in the Reports UI; no bespoke page.
- Standard platform run/filter/export controls; healthcare-specific default filters (current branch, last 30 days) preset in the template.

---

#### Frontend (UILDC v1.0)

- **Route:** platform Reports UI — "Pasien Harian" (Daily Patients) and "Janji Temu" (Appointments) templates.
- **Portal:** Clinic Portal (platform Reports)
- **Layout:** Platform report-view layout; healthcare templates preselect sensible defaults.
- **Components (platform-provided):** platform report table/chart view, filter panel, export/schedule controls; `FlexBadge` template label.
- **Key interactions:** select the "Pasien Harian" or "Janji Temu" template → engine runs the bound dataset with preset filters → user adjusts filters/exports via platform controls.
- **Empty state / Error state / i18n / Mobile:** inherit the platform Reports engine; healthcare labels localized (ID / EN).

## Feature 12.2 — Healthcare Report Templates

### Story 12.2.1 [OPEN]
**As a** Clinic Owner,
**I want to** a doctor-productivity report bound to `v_hc_doctor_productivity`,
**so that** I can see encounters, patients seen, and average consult time per doctor.

**Backend AC:**
- Ship a platform **report template** over `v_hc_doctor_productivity` (encounters, unique patients, avg consult duration, no-show rate) grouped by provider, with branch/department/date filters — laid out on the platform Reports engine; no engine code.
- Values are aggregates keyed by `provider_id` label (no patient PHI); respects branch scoping.
- Exportable/scheduleable via the platform engine.

**Frontend AC:**
- Platform Reports template "Produktivitas Dokter" (Doctor Productivity); grouped table + platform chart; standard export.
- Provider filter from HR provider directory (epic-11); labels localized.

---

#### Frontend (UILDC v1.0)

- **Route:** platform Reports UI — "Produktivitas Dokter" template.
- **Portal:** Clinic Portal (platform Reports)
- **Layout:** Platform report layout; grouped-by-provider table with a summary chart.
- **Components (platform-provided):** report table, group-by control, platform bar chart, export/schedule; `FlexBadge` template label.
- **Key interactions:** run template → view per-doctor productivity → filter by branch/department/date → export.
- **Empty state / Error / i18n / Mobile:** inherit platform Reports; "Produktivitas Dokter" and column labels localized (ID / EN).

### Story 12.2.2 [OPEN]
**As a** Branch Manager,
**I want to** queue and revenue reports bound to `v_hc_queue` and `v_hc_revenue`,
**so that** I can monitor wait times and daily/period revenue per branch and department.

**Backend AC:**
- Templates over `v_hc_queue` (avg wait, avg service time, served/skipped/transferred counts by department/station/day) and `v_hc_revenue` (charged/paid/outstanding by branch, department, payment category, day) on the platform Reports engine.
- Revenue dataset is billing-only aggregates (no GL/AR — deferred per BACKLOG); no PHI.
- Export/schedule via platform engine.

**Frontend AC:**
- Platform Reports templates "Antrean" (Queue) and "Pendapatan" (Revenue); standard controls; localized labels.

---

#### Frontend (UILDC v1.0)

- **Route:** platform Reports UI — "Antrean" and "Pendapatan" templates.
- **Portal:** Clinic Portal (platform Reports)
- **Layout:** Platform report layout.
- **Components (platform-provided):** report table/chart, filters, export/schedule; `FlexBadge` labels.
- **Key interactions:** run either template → filter by branch/department/date/payment-category → export/schedule.
- **Empty state / Error / i18n / Mobile:** inherit platform Reports; labels + currency formatting localized (ID / EN).

### Story 12.2.3 [OPEN]
**As a** Clinic Owner or Pharmacist/Lab Manager,
**I want to** disease-statistics, drug-usage, and lab-utilization reports,
**so that** I have clinical-operations insight across diagnoses, dispensing, and lab throughput.

**Backend AC:**
- Templates over `v_hc_disease_stats` (top ICD-10 diagnoses counts by period/department — coded, no patient rows), `v_hc_drug_usage` (dispensed quantities by drug/period/branch), and `v_hc_lab_utilization` (tests ordered/resulted, turnaround, rejection rate by period/branch) on the platform Reports engine.
- Disease stats read coded diagnoses (epic-10) via the view — aggregate/coded only, no free-text notes or patient identifiers.
- Export/schedule via platform engine.

**Frontend AC:**
- Platform Reports templates "Statistik Penyakit" (Disease Statistics), "Penggunaan Obat" (Drug Usage), "Utilisasi Lab" (Lab Utilization); standard controls; localized labels (ICD labels via master-data).

---

#### Frontend (UILDC v1.0)

- **Route:** platform Reports UI — the three clinical-operations templates.
- **Portal:** Clinic Portal (platform Reports)
- **Layout:** Platform report layout; top-N tables + platform charts.
- **Components (platform-provided):** report table/chart, filters, export/schedule; `FlexBadge` labels.
- **Key interactions:** run a template → filter by period/branch/department/drug/test → export.
- **Empty state / Error / i18n / Mobile:** inherit platform Reports; ICD/drug/test labels localized via master-data (ID / EN).

## Feature 12.3 — Executive Dashboard Widgets (bind to platform Dashboards engine)

### Story 12.3.1 [OPEN]
**As a** Clinic Owner or Branch Manager,
**I want to** "Today's Patients" and "Waiting Patients" widgets on the platform Dashboards engine,
**so that** I see live operational load at a glance without building a dashboard framework.

**Backend AC:**
- Register two healthcare **dashboard widgets** on the platform Dashboards engine (`services/dashboard_service.py`): "Today's Patients" (bound to `v_hc_daily_patients`, filtered to today, current branch) and "Waiting Patients" (bound to `v_hc_queue`, status=waiting). No dashboard engine code is written.
- Widgets declare their bound dataset, refresh interval, and drill-through target (queue view epic-09); branch/tenant scoped via the view; no PHI (counts only).
- Widget definitions are seeded/versioned with the module and honor platform dashboard sharing/snapshot features.

**Frontend AC:**
- Widgets appear in the **platform Dashboards** widget gallery under "Healthcare"; users add them to any dashboard using the existing designer.
- "Today's Patients" shows a count + trend; "Waiting Patients" shows a live count with drill-through to the queue.
- Labels localized (ID / EN).

---

#### Frontend (UILDC v1.0)

- **Route:** platform Dashboards UI (`#/dashboards/*`) — widgets added via the existing designer; **no new healthcare route**.
- **Portal:** Clinic Portal (platform Dashboards)
- **Layout:** Widgets render inside the platform dashboard grid; healthcare widgets appear under a "Kesehatan" group in the widget gallery.
- **Components (platform-provided widget shells, bound to healthcare datasets):**
  - Platform KPI/stat widget — "Pasien Hari Ini" (Today's Patients): count + trend
  - Platform KPI widget — "Pasien Menunggu" (Waiting Patients): live count
  - `FlexBadge` — "Kesehatan" group label; live-refresh indicator
- **Key interactions:**
  - User adds a healthcare widget from the platform widget gallery to any dashboard.
  - "Pasien Menunggu" drill-through navigates to the queue view (epic-09).
  - Refresh interval and sharing/snapshots handled by the platform engine.
- **Empty state:** Platform widget empty state; "Tidak ada pasien menunggu." (No waiting patients.)
- **Error state:** Platform widget error handling.
- **i18n:** Widget titles + labels localized (ID / EN); rest inherits platform.
- **Mobile:** Inherits platform Dashboards responsiveness.

### Story 12.3.2 [OPEN]
**As a** Clinic Owner,
**I want to** "Revenue Today" and "Appointment Summary" widgets,
**so that** I can track financial and scheduling health on my executive dashboard.

**Backend AC:**
- Register widgets "Revenue Today" (bound to `v_hc_revenue`, today, current branch — billing aggregates only, no GL/AR) and "Appointment Summary" (bound to `v_hc_appointments`: booked / attended / no-show / cancelled for today) on the platform Dashboards engine; no engine code.
- Widgets declare bound dataset, refresh, and drill-through (revenue → revenue report; appointments → scheduling); branch/tenant scoped; no PHI.

**Frontend AC:**
- Widgets in the platform Dashboards "Healthcare" gallery; "Revenue Today" shows a currency KPI (locale-formatted); "Appointment Summary" shows a small status breakdown.
- Labels + currency localized (ID / EN).

---

#### Frontend (UILDC v1.0)

- **Route:** platform Dashboards UI — widgets added via the designer.
- **Portal:** Clinic Portal (platform Dashboards)
- **Layout:** Platform dashboard grid; healthcare gallery group.
- **Components (platform-provided, bound):** KPI widget "Pendapatan Hari Ini" (Revenue Today, currency); status-breakdown widget "Ringkasan Janji Temu" (Appointment Summary); `FlexBadge` group label.
- **Key interactions:** add widgets from gallery; drill-through to revenue report / scheduling; currency locale-formatted.
- **Empty state / Error / i18n / Mobile:** inherit platform Dashboards; titles + currency localized (ID / EN).

### Story 12.3.3 [OPEN]
**As a** Clinic Owner or Branch Manager,
**I want to** "Doctor Utilization" and "Pharmacy Stock Alerts" widgets,
**so that** I can monitor clinician load and act on stock risks from one dashboard.

**Backend AC:**
- Register widgets "Doctor Utilization" (bound to `v_hc_doctor_productivity` + practice-schedule availability from epic-11: booked vs available slots per doctor today) and "Pharmacy Stock Alerts" (bound to the pharmacy reorder-alert view from epic-04 addendum: count of items at/below reorder level) on the platform Dashboards engine; no engine code.
- Widgets declare bound dataset, refresh, drill-through (utilization → doctor-productivity report; stock alerts → pharmacy catalog reorder tab); branch/tenant scoped; no PHI.

**Frontend AC:**
- Widgets in the platform Dashboards "Healthcare" gallery; "Doctor Utilization" shows a per-doctor utilization bar; "Pharmacy Stock Alerts" shows a count badge with drill-through.
- Labels localized (ID / EN).

---

#### Frontend (UILDC v1.0)

- **Route:** platform Dashboards UI — widgets added via the designer.
- **Portal:** Clinic Portal (platform Dashboards)
- **Layout:** Platform dashboard grid; healthcare gallery group.
- **Components (platform-provided, bound):** utilization bar widget "Utilisasi Dokter" (Doctor Utilization); alert-count widget "Peringatan Stok Farmasi" (Pharmacy Stock Alerts); `FlexBadge` alert count.
- **Key interactions:** add widgets; "Utilisasi Dokter" drill-through to doctor-productivity report; "Peringatan Stok Farmasi" drill-through to the pharmacy reorder-alerts tab (epic-04).
- **Empty state:** "Tidak ada peringatan stok." (No stock alerts.)
- **Error / i18n / Mobile:** inherit platform Dashboards; titles/labels localized (ID / EN).

## Feature 12.4 — Executive Dashboard Assembly & Scheduled Delivery

### Story 12.4.1 [OPEN]
**As a** Clinic Owner,
**I want to** a seeded "Executive Overview" healthcare dashboard assembling the six widgets, with scheduled report delivery,
**so that** leadership has a ready-made operational view and periodic report emails without configuring anything.

**Backend AC:**
- Seed a **dashboard template** ("Clinic Executive Overview") on the platform Dashboards engine assembling the six healthcare widgets (today's patients, waiting patients, revenue today, appointment summary, doctor utilization, pharmacy stock alerts); it is a platform dashboard definition — no engine code.
- Register a **scheduled report bundle** (daily/weekly) via the platform Reports scheduler + notification transport (Reuse Register) delivering the daily-patients, revenue, and appointment templates to Clinic Owner/Branch Manager; delivery honors platform permissions and locale.
- Dashboard and schedule are seeded per tenant on module activation, branch-scoped, and fully editable by the owner through the platform designers (owner can add/remove widgets, change schedule).

**Frontend AC:**
- The seeded "Ikhtisar Eksekutif" (Executive Overview) dashboard is available in the platform Dashboards list; owner can clone/edit via the existing designer.
- Scheduled delivery managed through the platform Reports scheduler UI; healthcare bundle preset with sensible defaults.
- Labels localized (ID / EN).

---

#### Frontend (UILDC v1.0)

- **Route:** platform Dashboards UI (seeded "Ikhtisar Eksekutif" dashboard) + platform Reports scheduler UI.
- **Portal:** Clinic Portal (platform Dashboards + Reports)
- **Layout:** Reuses the platform dashboard view and scheduler UI; the healthcare dashboard is a preseeded entry.
- **Components (platform-provided):** platform dashboard grid rendering the six healthcare widgets; platform schedule editor; `FlexBadge` "Ikhtisar Eksekutif" label.
- **Key interactions:**
  - Owner opens the seeded "Ikhtisar Eksekutif" dashboard → all six widgets render → clone/edit via the platform designer.
  - Scheduled delivery reviewed/adjusted in the platform Reports scheduler; default recipients = Clinic Owner + Branch Manager; locale-aware.
- **Empty state:** Widgets show their own empty states before data exists.
- **Error state:** Platform dashboard/scheduler error handling.
- **i18n:** Dashboard name, widget titles, schedule labels localized (ID / EN); rest inherits platform.
- **Mobile:** Inherits platform Dashboards responsiveness (leadership may view on mobile).

## Story Count: Feature 12.1 (2) + 12.2 (3) + 12.3 (3) + 12.4 (1) = **9 stories**
