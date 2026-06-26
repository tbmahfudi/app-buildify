# impl-notes-T-22-009 — Baseline Measurement (check-tenant-scope)

**Task**: T-22.009 (brief) / T-22.008 (tasks-22.md partial — router inventory)
**Status**: DONE
**Date**: 2026-06-27
**Owner**: C2

## Baseline run

Command: bash manage.sh check-tenant-scope

## Results after service migration (T-22.008)

**Services violations**: 0 (all 17 pre-existing literals annotated in T-22.008)
**Router violations**: 36 (follow-up sprint N+1 per M-2)

## Router violations by file

- backend/app/routers/audit.py: 2 violations
- backend/app/routers/scheduler.py: 1 violation
- backend/app/routers/org.py: 7 violations
- backend/app/routers/rbac.py: 12 violations
- backend/app/routers/modules.py: 12 violations
- backend/app/routers/settings.py: 2 violations

Total router violations: 36

## Pre-migration baseline (services only)

Before T-22.008 service migration, services had 17 raw literals:
- nocode_module_service.py: 8
- menu_service.py: 8
- runtime_model_generator.py: 1

All were or_() intentional cross-scope patterns, not filterable by apply_tenant_scope().
Correctly annotated with # tenant-scope-ok.

## Next steps

Router violations are documented for sprint N+1 M-2 migration. The CI gate (T-22.022)
will enforce no NEW violations from this point; the 36 legacy router violations will be
remediated incrementally.
