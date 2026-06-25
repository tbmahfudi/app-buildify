# Implementation Notes — T-23.007

**Task**: Add jsonschema.validate() call in loader.py; wire into POST /modules/register (422 on violation) and add POST /modules/validate dry-run endpoint.

**Date**: 2026-06-25
**Author**: C2 Backend Developer

---

## What was done

### 1. backend/app/core/module_system/loader.py — validate_manifest()

Updated the existing validate_manifest(manifest: dict) -> tuple[bool, str | None] method:
- Loads manifest.schema.json from the same directory (Path(__file__).parent)
- Calls jsonschema.validate(instance=manifest, schema=schema)
- Returns (True, None) on success
- Returns (False, "<path>: <message>") on jsonschema.ValidationError — includes the JSON pointer path when available for better DX
- Handles ImportError gracefully (logs warning, returns (True, None)) so the server starts even if jsonschema is not installed

jsonschema>=4.17 was already present in backend/requirements.txt.

### 2. POST /api/v1/module-registry/register — error shape fix

The validation call was already wired (partial T-23.007 work) but used a wrong detail shape. Fixed to the canonical structured error:

  {"code": "manifest_invalid", "message": "Manifest validation failed", "detail": {"errors": ["<error string>"]}}

HTTP status: 422 Unprocessable Entity.

### 3. POST /api/v1/modules/validate — new dry-run endpoint

Added to _modules_v1_router (prefix /api/v1/modules) in backend/app/routers/modules.py.

- Auth: get_current_user (no superuser requirement)
- Body: {"manifest": {...}}
- Returns {"valid": true} on success (HTTP 200)
- Returns HTTP 422 with {code, message, detail: {errors: [...]}} on failure
- No DB writes

---

## Key decisions

- Reused the existing ModuleLoader.validate_manifest() method rather than duplicating schema-loading logic in the router.
- ModuleLoader("/tmp") is instantiated for schema validation only — the path is unused by validate_manifest.
- Error detail is always a list (errors: [...]) to leave room for future multi-error reporting.

---

## Files changed

- backend/app/core/module_system/loader.py — updated validate_manifest()
- backend/app/routers/modules.py — fixed register error shape; added /validate endpoint

---

## Follow-up

- T-23.009 (manage.sh module pack calls POST /modules/validate) can now proceed.
- T-23.010 (manage.sh module install calls /modules/validate) can now proceed.
