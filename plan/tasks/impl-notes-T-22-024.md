# impl-notes-T-22-024 -- Adversarial: scope leak

**Task**: T-22.024 -- ContextVar / cross-tenant-scope leak tests
**Status**: DONE
**Date**: 2026-06-27
**Owner**: D1 QA Engineer

---

## Deliverable

`backend/tests/integration/tenant_isolation/test_scope_leak.py`.

Verifies the `_current_tenant_id` ContextVar and the `__superuser__` sentinel
never leak past the context manager that set them:

- `with_tenant_scope` restores the prior value on normal exit **and** on exception.
- Nested `with_tenant_scope` restores the outer tenant (not `None`) on inner exit.
- `with_admin_cross_tenant_scope` clears the `__superuser__` sentinel on exit and
  on exception, and writes `tenant.cross_scope.enter` / `.exit` audit entries on
  both paths (a leaked sentinel would silently disable all tenant filtering).
- `set_tenant_scope` + `clear_tenant_scope` leaves the ContextVar at `None`;
  `get_tenant_scope` then raises `TenantScopeNotSetError`.
- A simulated request (`set_tenant_scope` … `finally: clear_tenant_scope`) leaves
  scope cleared even when the handler raises.

## Result

7/7 passing.
