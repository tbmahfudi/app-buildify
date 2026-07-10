---
artifact_id: epic-19-analytics-bi
status: active
version: 1
module: cross-module
launch_phase: R5
producer: A3 Product Owner
upstream: BACKLOG v3
created: 2026-07-02
---

# Epic 19 — Multi-clinic Analytics / BI / Data Warehouse

**Module:** cross-module (requires `healthcare` base + reporting datasets from epic-12)
**Launch Phase:** R5
**Depth:** Outline (epic header + one-line story list; detailed AC/UILDC deferred to build time).
**Summary:** Cross-clinic analytics, BI dashboards, workflow automation, and a data-warehouse layer that
aggregates the `v_hc_*` reporting views (epic-12) across branches/tenants. Reuses the platform Reports and
Dashboards engines (Reuse Register #15/#16) and Scheduler; adds a warehouse/aggregation layer and automation
rules on top — no new reporting or dashboard engine.

---

## Feature 19.1 — Multi-clinic Analytics
- Story 19.1.1 — Aggregate the `v_hc_*` views across branches/tenants into a warehouse layer for cross-clinic analysis.
- Story 19.1.2 — Cross-clinic comparison analytics (volume, revenue, utilization) by branch/region/period.

## Feature 19.2 — BI Dashboards
- Story 19.2.1 — Executive multi-clinic BI dashboards on the platform Dashboards engine over the warehouse layer.
- Story 19.2.2 — Trend/forecast and drill-down BI widgets (period-over-period, cohort) bound to warehouse datasets.

## Feature 19.3 — Workflow Automation
- Story 19.3.1 — Rule-based automation (threshold alerts, scheduled actions) on analytics signals via the platform Scheduler/notification transport.
- Story 19.3.2 — Data-warehouse ETL scheduling, refresh monitoring, and lineage/quality checks.

## Story Count: Feature 19.1 (2) + 19.2 (2) + 19.3 (2) = **6 stories**
