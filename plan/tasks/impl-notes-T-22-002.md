# impl-notes-T-22-002 -- Add __tenant_scoped__ = True to 18 models

**Status**: DONE
**Date**: 2026-06-26
**Owner**: C2 Backend Developer

## What was implemented

Added __tenant_scoped__ = True class attribute immediately after __tablename__ on
all 18 models listed in schema-22.md section 5.1.

## Models updated

| File | Class |
|------|-------|
| backend/app/models/user.py | User |
| backend/app/models/company.py | Company |
| backend/app/models/branch.py | Branch |
| backend/app/models/department.py | Department |
| backend/app/models/group.py | Group |
| backend/app/models/report.py | ReportDefinition |
| backend/app/models/report.py | ReportExecution |
| backend/app/models/report.py | ReportSchedule |
| backend/app/models/report.py | ReportCache |
| backend/app/models/dashboard.py | Dashboard |
| backend/app/models/dashboard.py | DashboardPage |
| backend/app/models/dashboard.py | DashboardWidget |
| backend/app/models/dashboard.py | DashboardShare |
| backend/app/models/dashboard.py | DashboardSnapshot |
| backend/app/models/dashboard.py | WidgetDataCache |
| backend/app/models/builder_page.py | BuilderPage |
| backend/app/models/module_service.py | ModuleServiceAccessLog |
| backend/app/models/nocode_module.py | ModuleActivation |

## Models explicitly NOT marked (per schema-22 section 5.2)

Module, Role, AuditLog, SecurityPolicy, NotificationConfig, NotificationQueue,
MenuItem, SchedulerConfig, SchedulerJob, WorkflowDefinition, WorkflowState,
WorkflowTransition, WorkflowInstance, WorkflowHistory, EntityDefinition,
FieldDefinition, FieldGroup, RelationshipDefinition, IndexDefinition,
EntityMigration, LookupConfiguration, LookupCache, CascadingLookupRule,
AutomationRule, AutomationExecution, ActionTemplate, WebhookConfig.
All are dual-mode (NULL = system/platform) or platform-wide.

## Rollout note

Per schema-22 section 10.2 and tasks-22.md dependency graph, TenantScopeListener
MUST NOT be installed (T-22.005) until after service migration (T-22.007) and
tenant_scoped_session deployment (T-22.009). Adding the class attribute now is
safe -- the listener is not yet active.
