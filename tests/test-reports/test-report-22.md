---
artifact_id: test-report-22
type: test-report
producer: D1 QA Engineer
upstream: [test-plan-22]
status: pending
created: 2026-06-20
updated: 2026-06-20
---

# Test Report — Epic 22: Tenant Isolation Hardening

> All scenarios are PENDING — awaiting execution against the deployed stack.

## Part A — Shared-core-DB hardening

| ID | Scenario | Status | Notes |
|---|---|---|---|
| A-01 | `apply_tenant_scope` filters for normal user | PENDING | |
| A-02 | `apply_tenant_scope` no-op for superuser | PENDING | |
| A-03 | `apply_tenant_scope` no-op for model without tenant_id | PENDING | |
| A-04 | `apply_tenant_scope` raises when user has no tenant_id | PENDING | |
| A-05 | `tenant_scope_dependency` passes with tenant_id | PENDING | |
| A-06 | `tenant_scope_dependency` raises without tenant_id | PENDING | |
| A-07 | `tenant_scope_dependency` passes for superuser | PENDING | |
| A-08 | `with_admin_cross_tenant_scope` allows superuser + audit | PENDING | |
| A-09 | `with_admin_cross_tenant_scope` blocks non-superuser | PENDING | |
| A-10 | `with_admin_cross_tenant_scope` requires non-empty reason | PENDING | |
| A-11 | `with_admin_cross_tenant_scope` audit-logs on exception | PENDING | |
| A-12 | `TenantScopeListener` auto-filters `__tenant_scoped__` model | PENDING | |
| A-13 | `TenantScopeListener` raises when scope unset | PENDING | |
| A-14 | `TenantScopeListener` skips non-scoped models | PENDING | |
| A-15 | `TenantScopeListener` skips on `__superuser__` marker | PENDING | |
| A-16 | `set_tenant_scope` / `clear_tenant_scope` state management | PENDING | |
| A-17 | `tenant_scoped_session` binds scope for normal user | PENDING | |
| A-18 | `tenant_scoped_session` binds `__superuser__` | PENDING | |
| A-19 | `tenant_scoped_session` raises for user without tenant_id | PENDING | |
| A-20 | Cross-tenant ID guessing blocked | PENDING | |
| A-21 | URL path manipulation cannot escape scope | PENDING | |
| A-22 | `check-tenant-scope` PASS on clean repo | PENDING | |
| A-23 | `check-tenant-scope` FAIL on raw filter | PENDING | |
| A-24 | Unauthenticated request blocked | PENDING | |
| A-25 | JWT tenant mismatch rejected | PENDING | |
| A-26 | Revoked token rejected | PENDING | |
| A-27 | `apply_tenant_scope` idempotent | PENDING | |
| A-28 | Service layer enforces scope | PENDING | |
| A-29 | Audit log on every cross-tenant scope entry | PENDING | |
| A-30 | Concurrent requests don't bleed scope | PENDING | |

## Part B — Per-tenant module DB

| ID | Scenario | Status | Notes |
|---|---|---|---|
| B-01 | Provision script creates DB within 60 s | PENDING | |
| B-02 | `tenant_module_databases` row inserted | PENDING | |
| B-03 | Provisioning status returns `not_provisioned` initially | PENDING | |
| B-04 | Provisioning status returns `ready` after provision | PENDING | |
| B-05 | `ModuleScopeMiddleware` no-op in shared strategy | PENDING | |
| B-06 | `ModuleScopeMiddleware` sets `module_scope` in per_tenant | PENDING | |
| B-07 | `migrate-module.py` fan-out success | PENDING | |
| B-08 | `migrate-module.py` exits 1 on partial failure | PENDING | |
| B-09 | `tenant deactivate` archives rows | PENDING | |
| B-10 | T-B cannot see T-A's provisioning status | PENDING | |

## Summary

| | Count |
|---|---|
| PASS | 0 |
| FAIL | 0 |
| PENDING | 40 |
| TOTAL | 40 |
