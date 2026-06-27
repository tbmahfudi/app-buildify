# impl-notes-T-22-023 -- Adversarial: cross-tenant SELECT

**Task**: T-22.023 -- cross-tenant SELECT adversarial tests
**Status**: DONE
**Date**: 2026-06-27
**Owner**: D1 QA Engineer

---

## Deliverable

`backend/tests/integration/tenant_isolation/test_cross_tenant_select.py` (+ a
local `conftest.py` and `__init__.py` for the suite).

Tests, all against the `__tenant_scoped__` `User` model with the
`TenantScopeListener` installed:

- `test_select_under_own_scope_sees_own_rows` — scope = tenant A returns only A's rows.
- `test_select_with_other_tenant_scope_returns_empty` — querying A's data under tenant B's scope returns `[]`.
- `test_select_cannot_be_widened_by_explicit_filter` — an explicit `filter(tenant_id == A)` under scope B still returns `[]` (listener ANDs in scope).
- `test_select_without_scope_raises` — unset ContextVar raises `TenantScopeMissingError`.
- `test_superuser_bypass_sees_all_tenants` — `__superuser__` sentinel sees all tenants.

## Harness design

The local `conftest.py` builds a per-test in-memory SQLite engine, installs the
listener on the `Session` class, creates the tables SQLite can build (skipping
PG-only DDL), and resets the `_current_tenant_id` ContextVar around every test.
The suite deliberately avoids importing `app.main` so it runs without the full
FastAPI dependency stack. `seed_user()` inserts under the `__superuser__` bypass.

## Result

5/5 passing.
