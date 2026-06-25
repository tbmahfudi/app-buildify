# T-23.028 -- QA: Module Audit-Log Event Coverage + Smoke Checklist

**Date:** 2026-06-26
**Author:** D1 (QA Engineer)

---

## Summary

Implemented automated test coverage for the 5 module lifecycle audit events
(module.installed, module.enabled, module.disabled, module.deactivate_all,
module.uninstalled) and added them to the D1 QA smoke checklist.

---

## Findings

### API endpoint clarification

The task spec references GET /api/v1/audit-logs?entity_type=module. The
actual implementation in backend/app/routers/audit.py (router prefix
/api/v1/audit) is:

    POST /api/v1/audit/list
    Body: {"entity_type": "module", "page": 1, "page_size": 200}

There is no GET endpoint with query params. The POST /list endpoint supports
entity_type, action, user_id, entity_id, status, start_date, end_date filters.

### DB state (docker container not running)

The PostgreSQL container (app_buildify_postgresql) was not running at QA time.
DB state inference is based on impl-notes-T-23-027 which confirmed all 5
event writes are in the code (module.installed was the only missing one,
added in T-23.027).

### Dev stack blocker (DEF-032)

The financial module exists in the DB seed but has no loadable class
(backend/modules/financial/ lacks module.py + permissions.py):

  - POST /module-registry/install    -> 400
  - POST /module-registry/enable     -> 400
  - POST /module-registry/disable    -> 400
  - POST /module-registry/deactivate-all -> 400 (no enabled modules)
  - POST /module-registry/uninstall  -> 400

None of the 5 events can be triggered via pure HTTP API in this environment.
All event-specific test assertions are marked xfail(strict=False).

---

## Deliverables

### 1. Integration test file

backend/tests/e2e/test_audit_logs_module.py

Structural tests (run unconditionally, must pass):
  - test_audit_list_requires_auth -- anon request rejected (401/403)
  - test_audit_list_module_filter_returns_200 -- superuser gets 200
  - test_audit_list_module_response_shape -- response has logs list + total int
  - test_audit_list_all_entries_have_correct_entity_type -- no filter leakage
  - test_audit_list_action_filter_scopes_results -- action filter works
  - test_audit_list_entries_have_required_fields -- id/action/entity_type/created_at
  - test_audit_list_low_privilege_user_result -- 200 or 403 for tenant user

Event coverage tests (xfail, DEF-032, auto-promote when stack wired):
  - test_module_installed_event_present
  - test_module_enabled_event_present
  - test_module_disabled_event_present
  - test_module_deactivate_all_event_present
  - test_module_uninstalled_event_present
  - test_all_five_module_event_types_present -- acceptance criterion rollup

Run:
    docker exec app_buildify_backend python -m pytest tests/e2e/test_audit_logs_module.py
      --confcutdir=tests/e2e -v

### 2. QA Smoke Checklist

tests/smoke_checklist.md

Added Epic 23 -- Module Lifecycle Audit Events section with:
  - Per-event manual check items
  - Reference to automated test file
  - DEF-032 blocker note

---

## Notes for follow-up

- DEF-032: wiring a loadable module class will auto-promote all 6 xfail event tests.
- The test-plan-e2e-api.md coverage matrix shows audit as not started.
  T-23.028 provides partial coverage (audit/list filtered to module entity_type).
  Full audit router deep coverage remains open.
