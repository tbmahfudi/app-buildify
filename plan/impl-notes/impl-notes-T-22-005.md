# impl-notes-T-22-005 -- TenantScopeListener install in app startup

**Task**: T-22.005  
**File**: backend/app/main.py  
**Status**: DONE

## What was implemented

Wired TenantScopeListener.install(engine) into the FastAPI lifespan startup
handler in backend/app/main.py per tasks-22.md T-22.005 spec.

### Location in startup sequence

The install call was placed at the VERY END of the lifespan startup block,
just before the yield, to respect the rollout order mandated in arch-22
section 3.2 and tasks-22 Item 22.2 note:

  Rollout order (must be respected to avoid HTTP 500 storms):
  1. T-22.001 through T-22.003 -- scope.py helper live
  2. T-22.007 -- all services migrated to apply_tenant_scope
  3. T-22.009 -- tenant_scoped_session dependency on all tenant routes (DONE)
  4. T-22.006 -- __tenant_scoped__ = True on all 18 models (DONE)
  5. T-22.005 -- listener installed at FastAPI lifespan startup (THIS TASK)

By placing the install last, existing requests that have already been migrated
to tenant_scoped_session will have scope set, and requests that do not go
through the dependency (health checks, login) will not hit scoped models.

### Changes in main.py

1. Added import at module level:
   from app.core.tenant_listener import TenantScopeListener

2. Added at end of lifespan startup (before yield):
   from app.core.db import engine as _db_engine
   TenantScopeListener.install(_db_engine)

The install method registers event.listen(Session, do_orm_execute, ...) on
the SQLAlchemy Session class, which fires for every session bound to this engine.

## Files changed

- backend/app/main.py -- added import + TenantScopeListener.install(engine) call
