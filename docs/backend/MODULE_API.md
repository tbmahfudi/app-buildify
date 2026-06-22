# Module API — Canonical Lifecycle Paths

## Decision

The existing router (`backend/app/routers/modules.py`) is registered at prefix
`/api/v1/module-registry` and uses request-body parameters for `enable` and `disable`
actions. Epic-23 (Module Lifecycle & Activation) requires RESTful path-based endpoints
and a richer activation-preview contract.

**Resolution**: a second router (`modules_lifecycle.py`) is added at prefix
`/api/v1/modules`. The old `/api/v1/module-registry` router is kept intact for backward
compatibility with existing integrations. New features (activation-preview, structured
errors, dependency checking, menu/RBAC integration) are implemented only on the new
router. Old code paths will be deprecated once all callers migrate.

---

## Canonical State Machine

```
installed (install_status=ready)
    │
    ├─ POST /modules/{name}/enable  →  active  (ModuleActivation.is_enabled=True)
    │                                     │
    │                               POST /modules/{name}/disable
    │                                     │
    └──────────────────────────────  inactive  (ModuleActivation.is_enabled=False)

POST /admin/modules/{name}/deactivate-all  →  deactivation_pending
DELETE /admin/modules/{name}               →  uninstalled (row deleted)
```

---

## New Endpoints (prefix `/api/v1/modules`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/modules` | tenant | List installed modules with per-tenant activation_status |
| GET | `/modules/{name}/activation-preview` | tenant | Preview permissions/menu/deps before activation |
| POST | `/modules/{name}/enable` | tenant admin | Activate module for current tenant |
| POST | `/modules/{name}/disable` | tenant admin | Deactivate module for current tenant |
| POST | `/admin/modules/{name}/deactivate-all` | superadmin | Deactivate across all tenants |
| DELETE | `/admin/modules/{name}` | superadmin | Hard uninstall (requires `X-Confirm-Uninstall: true`) |

## Legacy Endpoints (prefix `/api/v1/module-registry` — keep, do not remove)

| Method | Path | Status |
|--------|------|--------|
| GET | `/module-registry/available` | Kept |
| GET | `/module-registry/enabled` | Kept |
| POST | `/module-registry/enable` | Kept (body param) |
| POST | `/module-registry/disable` | Kept (body param) |
| POST | `/module-registry/install` | Kept |
| POST | `/module-registry/uninstall` | Kept |
| POST | `/module-registry/register` | Kept |

---

## Structured Error Shape (new endpoints only)

```json
{
  "code": "MODULE_NOT_FOUND",
  "message": "Module 'crm' is not installed.",
  "detail": null
}
```

Common codes: `MODULE_NOT_FOUND`, `DEPS_UNMET`, `DEPENDENTS_ACTIVE`,
`ALREADY_ENABLED`, `ALREADY_DISABLED`, `SYSTEM_MODULE_PROTECTED`,
`INSTALL_NOT_READY`.
