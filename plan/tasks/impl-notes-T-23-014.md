# Implementation Notes — T-23.014

**Task**: Wire `post_install` and `post_enable` lifecycle hooks
**Owner**: C2
**Status**: DONE

---

## post_install hook

**Location**: `backend/app/routers/modules.py` — `POST /api/v1/module-registry/register`
**Finding**: Already implemented in a prior commit (lines ~764–805). The hook is called after the new `Module` row is committed to the database. It instantiates a `ModuleLoader` pointing at the modules root, calls `loader.load_module(module_name)`, and invokes `_instance.post_install(db)`. Failure is caught, logged at WARNING, and audited as a `module_hook_failure` — the registration transaction is NOT rolled back per spec.

No changes were needed here.

---

## post_enable hook

**Location**: `backend/app/routers/modules.py` — `POST /api/v1/module-registry/enable`
**Change**: Added a try/except block immediately after the success audit log and before the `return ModuleOperationResponse(...)`.

### What was added (lines ~500–523)

```python
# T-23.014: call post_enable hook after ModuleActivation is created
module_name = request_data.module_name
try:
    _loader = registry.loader
    _instance = _loader.get_module(module_name) or _loader.load_module(module_name)
    if _instance is not None:
        _instance.post_enable(db, target_tenant_id)
        logger.info(f"post_enable hook completed for '{module_name}' tenant={target_tenant_id}")
except Exception as _hook_err:
    logger.warning(
        f"post_enable hook failed for '{module_name}': {_hook_err}",
        exc_info=True,
    )
    create_audit_log(
        db=db,
        action="module_hook_failure",
        user=current_user,
        entity_type="module",
        entity_id=request_data.module_name,
        context_info={"hook": "post_enable", "error": str(_hook_err)},
        request=http_request,
        status="failure",
    )
    # do NOT raise — hook failure is non-fatal per T-23.014
```

### Design decisions

- `registry.loader` is the `ModuleLoader` instance held by `ModuleRegistryService` (set in `__init__`). This avoids constructing a new loader and uses the already-warmed module cache.
- `get_module()` is tried first (cache hit); falls back to `load_module()` for cold paths.
- Hook failure does NOT roll back the enable — `ModuleActivation` row stays, the module is considered enabled. This matches the spec's "log+audit on failure, do NOT roll back" requirement.
- Audit action is `module_hook_failure` with `entity_type=module` for consistency with the post_install failure pattern already in the register endpoint.

---

## Files changed

- `backend/app/routers/modules.py` — post_enable block added in `/enable` endpoint
- `plan/tasks/tasks-23.md` — T-23.014 status set to DONE
