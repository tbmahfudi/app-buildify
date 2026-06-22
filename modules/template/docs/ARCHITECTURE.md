# TEMPLATE Module — Architecture

## Overview

Brief description of what this module does and its role in the platform.

## Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Backend routes | `modules/TEMPLATE/routes.py` | FastAPI router |
| Data models | `modules/TEMPLATE/models.py` | SQLAlchemy models |
| Module lifecycle | `modules/TEMPLATE/module.py` | BaseModule hooks |
| Frontend | `modules/TEMPLATE/frontend/` | UI shell |
| Migrations | `modules/TEMPLATE/migrations/` | Schema migrations |

## Data model

```
TEMPLATERecord
  id            UUID       PK
  tenant_id     VARCHAR    NOT NULL, INDEX  (tenant-scoped)
  name          VARCHAR(255)
  created_at    TIMESTAMP
  updated_at    TIMESTAMP
```

## Tenant isolation

All models set `__tenant_scoped__ = True`. The platform's `TenantScopeListener`
automatically appends `WHERE tenant_id = <current_tenant>` on SELECT, UPDATE, DELETE.

## Platform dependencies

| Capability | Used via |
|------------|---------|
| Audit logging | `PlatformBridge.audit_log()` |
| Notifications | `PlatformBridge.send_notification()` |
| Feature flags | `PlatformBridge.is_feature_enabled()` |

## Cross-module communication

All cross-module communication goes through the platform event bus (`PlatformBridge.emit_event()`).
No direct imports from other modules.

## SDK constraint

Only `from modules.sdk import ...` — never `from backend.app import ...`.
