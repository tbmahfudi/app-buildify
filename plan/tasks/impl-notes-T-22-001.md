# impl-notes-T-22-001 -- Create backend/app/core/tenant/scope.py

**Status**: DONE
**Date**: 2026-06-26
**Owner**: C2 Backend Developer

## What was implemented

Created backend/app/core/tenant/ package:

- backend/app/core/tenant/scope.py -- canonical tenant scope helper
- backend/app/core/tenant/__init__.py -- public API re-export

### Public API

- ContextVar _current_tenant_id: per-request/async tenant binding
- set_tenant_scope(tenant_id) -- binds UUID to current context
- get_tenant_scope() -- returns UUID; raises TenantScopeNotSetError if not set
- clear_tenant_scope() -- removes binding
- with_tenant_scope(tenant_id) -- contextmanager: set/yield/reset
- with_admin_cross_tenant_scope(user, reason, audit_log_fn) -- superuser-only audit-logged bypass; sets __superuser__ sentinel
- apply_tenant_scope(query, model, user) -- adds WHERE clause; no-op for superuser or non-scoped models
- apply_tenant_scope_by_id(query, model, tenant_id) -- bare UUID variant for static methods
- tenant_scope_dependency(user) -- FastAPI dependency validator
- TenantScopeNotSetError -- raised on missing scope
- TenantScopeMissingError -- legacy alias

### Backward compatibility

backend/app/core/scope.py converted to a shim re-exporting from the new package.
All existing imports continue to work unchanged.

### Exception wiring

TenantScopeNotSetError imported into backend/app/core/exceptions.py.
Dedicated tenant_scope_not_set_handler added, registered before generic handler.
Returns HTTP 500 sanitized body (satisfies sec-review-22 I-1).

## Key design decisions

- ContextVar (not session attribute) so scope is async-safe.
- with_admin_cross_tenant_scope uses inspect.stack() to capture caller frame for audit entry.
- __superuser__ sentinel set via ContextVar for integration with tenant_listener.py.
