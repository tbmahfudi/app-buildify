# impl-notes-T-22-007 — tenant_scoped_session FastAPI Dependency

**Task**: T-22.007 (brief) / T-22.009 (tasks-22.md)
**Status**: DONE
**Date**: 2026-06-27
**Owner**: C2

## What was built

Created backend/app/core/tenant/dependencies.py with a tenant_scoped_session FastAPI
dependency that:

- Calls set_tenant_scope(current_user.tenant_id) at request start via ContextVar
- Yields the db session inside a try/finally block
- Calls clear_tenant_scope() unconditionally in finally clause
- Uses ContextVar path from scope.py (not session-attribute approach in tenant_listener.py)
- Routes superuser requests via the __superuser__ sentinel
- Raises TenantScopeNotSetError for non-superuser users without a tenant_id

Also exported tenant_scoped_session from backend/app/core/tenant/__init__.py.

## Note on pre-existing implementation

backend/app/core/dependencies.py already contained a tenant_scoped_session using the
session-attribute approach (tenant_listener.set_tenant_scope). The new canonical version
in tenant/dependencies.py uses the ContextVar path from scope.py and does not depend on
listener installation order.

Router authors should prefer: from app.core.tenant.dependencies import tenant_scoped_session

## Files created/modified

- backend/app/core/tenant/dependencies.py -- NEW
- backend/app/core/tenant/__init__.py -- updated to export tenant_scoped_session
