# TEMPLATE Module

> Quick-start guide for module developers.
> Replace every occurrence of `TEMPLATE` with your module name.

## Getting started

```bash
# 1. Scaffold a new module from this template:
manage.sh module new my_module

# 2. Fill in modules/my_module/manifest.json
# 3. Implement modules/my_module/module.py
# 4. Write routes in modules/my_module/routes.py
# 5. Write models in modules/my_module/models.py
# 6. Add Alembic migrations in modules/my_module/migrations/
# 7. Build and install:
manage.sh module pack my_module
manage.sh module install my_module_v1.0.0.tar.gz
```

## SDK import rule

Only import from `modules.sdk`:

```python
from modules.sdk import BaseModule, PlatformBridge
```

Never `from backend.app import ...`.

## Tenant isolation

Every SQLAlchemy model must:
- Set `__tenant_scoped__ = True`
- Include a `tenant_id = Column(String(36), nullable=False, index=True)` column

## Platform capabilities

Use `PlatformBridge` (injected into your module) for:
- `bridge.audit_log(...)` — write audit log entries
- `bridge.send_notification(...)` — in-app notifications
- `bridge.send_email(...)` — templated emails
- `bridge.get_tenant_config(...)` — tenant settings
- `bridge.emit_event(...)` — platform event bus
- `bridge.is_feature_enabled(...)` — feature flags

Need something not listed? File a request in `platform-requests/open/`.

## File structure

```
modules/my_module/
├── manifest.json       # Module metadata, routes, permissions
├── module.py           # BaseModule subclass + lifecycle hooks
├── routes.py           # FastAPI router
├── models.py           # SQLAlchemy models (tenant-scoped)
├── migrations/         # Alembic migration scripts
├── frontend/
│   ├── index.html      # Module HTML shell
│   └── module.js       # Frontend entry point
└── tests/
    └── test_module.py  # pytest test suite
```
