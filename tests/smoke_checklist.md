---
artifact_id: smoke_checklist
type: qa-checklist
producer: D1 QA Engineer
status: active
created: 2026-06-26
updated: 2026-06-26
---

# D1 QA Smoke Checklist

Manual smoke checks to run after any deploy or significant migration.

---

## Epic 23 -- Module Lifecycle Audit Events

Endpoint: POST /api/v1/audit/list
Filter body: {"entity_type": "module", "page": 1, "page_size": 200}
Auth required: audit:read:tenant permission or superuser

Note: the task spec references GET /api/v1/audit-logs?entity_type=module.
The actual implementation is POST /api/v1/audit/list with the filter in the
request body (backend/app/routers/audit.py). Use the POST form for all checks.

### Checklist

- [ ] **module.installed** -- POST /api/v1/audit/list with action=module.installed
  - Expected: total >= 1; each entry has entity_type=module, action=module.installed
  - Triggered by: POST /api/v1/module-registry/register (new module or first_install=True)

- [ ] **module.enabled** -- POST /api/v1/audit/list with action=module.enabled
  - Expected: total >= 1; each entry has entity_type=module, action=module.enabled
  - Triggered by: POST /api/v1/module-registry/enable

- [ ] **module.disabled** -- POST /api/v1/audit/list with action=module.disabled
  - Expected: total >= 1; each entry has entity_type=module, action=module.disabled
  - Triggered by: POST /api/v1/module-registry/disable OR inside /deactivate-all per-tenant loop

- [ ] **module.deactivate_all** -- POST /api/v1/audit/list with action=module.deactivate_all
  - Expected: total >= 1; each entry has entity_type=module, action=module.deactivate_all
  - Triggered by: POST /api/v1/module-registry/deactivate-all (written after the per-tenant loop)

- [ ] **module.uninstalled** -- POST /api/v1/audit/list with action=module.uninstalled
  - Expected: total >= 1; each entry has entity_type=module, action=module.uninstalled
  - Triggered by: POST /api/v1/module-registry/uninstall

### Automated coverage

backend/tests/e2e/test_audit_logs_module.py (added T-23.028):

Structural tests (auth guard, response shape, field presence, action-filter scoping)
run unconditionally and must pass. Per-event-type tests are xfail(strict=False)
because the dev stack has no loadable module class (DEF-032). They auto-promote
to PASSED once a loadable module is wired up.

Run:
    docker exec app_buildify_backend python -m pytest tests/e2e/test_audit_logs_module.py
      --confcutdir=tests/e2e -v

### Blocker note (DEF-032)

The financial module exists in the DB seed but has no loadable class
(backend/modules/financial/ lacks module.py + permissions.py). All
install/enable/disable/uninstall calls return 400. The 5 lifecycle audit
events cannot be generated via the HTTP API until this is resolved.

---

## Future sections

Add new epic sections here as QA coverage expands.
