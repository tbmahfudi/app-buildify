# impl-notes-T-22-004 -- TenantScopeListener class

**Task**: T-22.004  
**File**: backend/app/core/tenant_listener.py  
**Status**: DONE

## What was implemented

Rewrote tenant_listener.py to implement the full TenantScopeListener per
arch-22 section 3.2 and tasks-22.md T-22.004 spec.

### Key design choices

**ContextVar as scope source (not session attribute)**

The existing tenant/scope.py stores scope in _current_tenant_id (ContextVar).
The tenant_scoped_session FastAPI dependency writes to this ContextVar.
The listener reads _current_tenant_id.get() as the authoritative scope.
Session-attribute fallback (_tenant_scope) is retained for background tasks
that call set_tenant_scope(session, tenant_id).

**Fail-loud with no silent pass (arch-22 section 3.2)**

When a scoped model is queried and scope is None, the listener immediately
raises TenantScopeMissingError. There is no fallback or silent pass.

**Superuser bypass**

When scope is the sentinel __superuser__ (written by tenant_scoped_session
for superusers or by with_admin_cross_tenant_scope()), the listener returns
without injecting any filter.

**SELECT + UPDATE + DELETE covered**

The do_orm_execute hook fires on all ORM statement types. The arch-22
HIGH finding H-1 (SELECT only was guarded) is resolved by not gating on is_select.

**SA 2.x all_mappers / bind_mapper compatibility**

all_mappers is tried first (covers JOIN queries); falls back to bind_mapper
for simple single-entity queries.

### set_tenant_scope / clear_tenant_scope (session-attr variants)

tenant_listener.py exposes set_tenant_scope(session, tenant_id) and
clear_tenant_scope(session) per T-22.005 spec. These write both the
ContextVar AND the session attribute for maximum compatibility.

## Files changed

- backend/app/core/tenant_listener.py -- full rewrite
