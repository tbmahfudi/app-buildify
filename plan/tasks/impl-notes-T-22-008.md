# impl-notes-T-22-008 — Service Layer Migration (3 Highest-Traffic Services)

**Task**: T-22.008 (brief) / T-22.007 (tasks-22.md)
**Status**: DONE
**Date**: 2026-06-27
**Owner**: C2

## Services migrated

All three services had raw tenant_id == literals in or_() cross-scope patterns that include
both tenant-specific AND platform-level (tenant_id == None) records. These are intentional
cross-tenant queries and correctly annotated with # tenant-scope-ok.

### 1. backend/app/services/nocode_module_service.py (8 literals)

All occurrences are in or_() filters that combine:
  - NocodeModule.tenant_id == self.tenant_id  (tenant records)
  - NocodeModule.tenant_id == None             (platform templates)

This pattern is intentional: module listings include platform-level templates.
All annotated: # tenant-scope-ok (or_() platform None includes platform templates)

### 2. backend/app/services/menu_service.py (8 literals)

All occurrences are in or_() filters combining:
  - MenuItem.tenant_id == user.tenant_id   (tenant menus)
  - MenuItem.tenant_id == None              (system menus)

This pattern is intentional: menus always include system-level items for all tenants.
All annotated: # tenant-scope-ok (or_() system menu branch / or_() tenant branch)

### 3. backend/app/services/runtime_model_generator.py (1 literal)

One occurrence in an or_() filter combining tenant-specific AND platform-level EntityDefinition
records. Intentional cross-scope to allow platform entities to be visible to all tenants.
Annotated: # tenant-scope-ok (or_() tenant branch)

## Migration approach

The or_()-based cross-scope queries cannot be replaced with apply_tenant_scope() because
apply_tenant_scope() only adds a single WHERE tenant_id = X clause. The platform-include pattern
requires the or_() form. The correct remediation is annotation with # tenant-scope-ok, which:
  1. Signals developer intent explicitly
  2. Suppresses the check-tenant-scope CI gate for these lines
  3. Is consistent with how data_model_service, automation_service, and workflow_service already
     handle the same pattern (those were already annotated before this sprint)

## Violations before migration: 17 (services only)
## Violations after migration: 0 (services)
## Remaining violations: 36 (routers only — follow-up M-2 sprint N+1)
