# impl-notes-T-22-025 -- Adversarial: ORM listener flush

**Task**: T-22.025 -- INSERT/UPDATE/DELETE enforcement + non-scoped negative case
**Status**: DONE
**Date**: 2026-06-27
**Owner**: D1 QA Engineer

---

## Deliverable

`backend/tests/integration/tenant_isolation/test_orm_listener_flush.py`.

- INSERT (flush), UPDATE, and DELETE on the `__tenant_scoped__` `User` model with
  no scope set raise `TenantScopeMissingError`.
- INSERT under a valid matching scope succeeds and the row is readable back.
- INSERT and SELECT on the non-scoped `TenantModuleDatabase` model succeed with
  no scope set — the listener must not fire for non-scoped models (admin /
  provisioning code depends on this).

## Finding & fix (listener gap closed)

While writing these tests I found a real enforcement gap: the listener only hooked
`do_orm_execute`, which fires for ORM **SELECT** and ORM-enabled UPDATE/DELETE,
but **not** for unit-of-work flushes (`session.add` / `session.delete` + flush).
So a forgotten-scope INSERT/UPDATE/DELETE silently bypassed enforcement — exactly
the H-1-class leak this layer exists to prevent.

Closed it by adding a `before_flush` hook to `TenantScopeListener`
(`backend/app/core/tenant_listener.py`):

- raises `TenantScopeMissingError` when a `__tenant_scoped__` instance is in
  `session.new/dirty/deleted` and scope is unset;
- rejects a write whose `tenant_id` differs from the active scope (cross-tenant
  write protection);
- bypasses on the `__superuser__` sentinel.

`install()` now registers both `do_orm_execute` and `before_flush`.

## Result

6/6 passing. Full suite (`tenant_isolation/`): 18/18 passing.
