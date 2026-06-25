# T-23.015 Implementation Notes

## What was implemented

`backend/tests/integration/modules_lifecycle/test_module_hook.py`

Two tests in `TestPostInstallHookSentinel`:

### test_post_install_writes_sentinel_to_audit_log (primary)

Verifies that the `post_install` hook is called by `/register` (T-23.014) and
writes a sentinel DB row.

**Approach**:
1. A real Python module stub is written into `tmp_path` using `textwrap.dedent`.
   Class name: `TestHookSentinelModule` (PascalCase of `test_hook_sentinel` + Module).
2. The stub's `post_install(db)` inserts an `AuditLog` row with
   `action="test_sentinel_post_install"` and commits.
3. `ModuleLoader` (imported inline by the /register handler from
   `app.core.module_system.loader`) is patched at the class level using
   `patch("app.core.module_system.loader.ModuleLoader", return_value=real_loader_instance)`.
   This works because Python resolves the class from `sys.modules` at import time;
   patching the attribute on the source module intercepts all inline imports.
4. `POST /api/v1/module-registry/register` is called with a valid manifest
   (required fields: `name`, `display_name`, `version`, `module_type`, `category`,
   `api_prefix` per `manifest.schema.json`; `dependencies` must be `[]` not `{}`).
5. Assert `audit_logs` row with `action="test_sentinel_post_install"` exists.

### test_register_endpoint_writes_module_installed_audit (baseline)

Verifies that `/register` always writes `action="module.installed"` via the
T-23.027 path, even for a module with no on-disk class (hook silently skipped).

## Key discoveries

- `ModuleRegistrationRequest` requires `manifest` (nested object) and
  `backend_service_url` at the top level ? not a flat manifest.
- `manifest.schema.json` requires: `name`, `display_name`, `version`,
  `module_type`, `category`, `api_prefix`.
- `dependencies` in manifest must be an array `[]`, not an object `{}`.
- `ModuleLoader` is imported inline (not at module level) in the /register
  handler, so `patch("app.routers.modules.ModuleLoader")` fails.
  The correct patch target is `app.core.module_system.loader.ModuleLoader`.

## Test result

```
2 passed in 28.25s
```

## Files

- `/home/mahfudi/app-buildify/backend/tests/integration/modules_lifecycle/test_module_hook.py`
