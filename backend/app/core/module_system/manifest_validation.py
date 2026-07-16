"""
Module manifest validation — shared load-time guardrails.

Historically the two manifest readers (the client module loader and the backend
menu/sync) parsed manifests with different field expectations and NO validation, so a
malformed manifest failed silently (see adr-module-frontend-integration.md §1.3). This
module gives the backend a single ``validate_manifest`` used by ``sync_manifests_from_disk``.

Enforcement is layered:
  * pure-Python **load-critical checks** always run (no external files/deps needed at
    runtime — the JSON Schema is not mounted into the container);
  * when the canonical JSON Schema (docs/modules/module-manifest.schema.json) and the
    ``jsonschema`` package are both available (dev / CI), its full errors are added too.

Returns a list of human-readable error strings (empty == valid). Callers log these; a
bad manifest is surfaced loudly rather than crashing module loading.
"""

from __future__ import annotations

import json
import os
from typing import Any, List, Optional

from .tenancy import validate_tenancy_block

# Candidate locations for the canonical schema (first hit wins). Env override first.
_SCHEMA_CANDIDATES = [
    os.environ.get("MODULE_MANIFEST_SCHEMA"),
    "/app/docs/modules/module-manifest.schema.json",
    os.path.join(os.path.dirname(__file__), "module-manifest.schema.json"),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../docs/modules/module-manifest.schema.json")),
]


def _load_schema() -> Optional[dict]:
    for path in _SCHEMA_CANDIDATES:
        if path and os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:  # noqa: BLE001
                return None
    return None


def _minimal_checks(manifest: Any) -> List[str]:
    """Load-critical invariants that break the SPA loader / menu if violated."""
    errors: List[str] = []
    if not isinstance(manifest, dict):
        return ["manifest must be a JSON object"]

    name = manifest.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("'name' is required and must be a non-empty string")

    routes = manifest.get("routes")
    if routes is None:
        errors.append("'routes' is required (use [] if the module has no routes)")
    elif not isinstance(routes, list):
        errors.append("'routes' must be an array")
    else:
        for i, r in enumerate(routes):
            if not isinstance(r, dict):
                errors.append(f"routes[{i}] must be an object")
                continue
            path = r.get("path")
            if not isinstance(path, str) or not path.startswith("#/"):
                errors.append(f"routes[{i}].path must be a hash route starting with '#/'")
            comp = r.get("component")
            # nginx serves /modules/<name>/<path> from the module frontend/ dir, so a
            # component MUST be relative to frontend/ — a leading 'frontend/' double-nests.
            if isinstance(comp, str) and (comp.startswith("frontend/") or comp.startswith("/frontend/")):
                errors.append(
                    f"routes[{i}].component '{comp}' must not start with 'frontend/' (paths are relative to the module frontend/ dir)"
                )

    nav = manifest.get("navigation")
    if nav is not None and not isinstance(nav, dict):
        errors.append("'navigation' must be an object when present")

    # ADR-012 D1. The canonical schema this module validates against
    # (docs/modules/module-manifest.schema.json) is lenient by design
    # (additionalProperties: true), so a malformed tenancy block would sail through it —
    # and the namespace rule is a cross-field check no JSON Schema can express anyway.
    # Both manifest-admitting paths must agree on it, so it runs here too (the strict
    # register path calls the same function from loader.validate_manifest).
    errors.extend(validate_tenancy_block(manifest))

    return errors


def validate_manifest(manifest: Any) -> List[str]:
    """Return a list of validation errors for a module manifest (empty == valid)."""
    errors = _minimal_checks(manifest)

    schema = _load_schema()
    if schema is not None:
        try:
            import jsonschema  # type: ignore

            validator = jsonschema.Draft7Validator(schema)
            for err in sorted(validator.iter_errors(manifest), key=lambda e: list(e.path)):
                loc = "/".join(str(p) for p in err.path) or "<root>"
                msg = f"{loc}: {err.message}"
                if msg not in errors:
                    errors.append(msg)
        except ImportError:
            pass  # jsonschema not available at runtime — minimal checks already ran
        except Exception:  # noqa: BLE001 — never let validation itself break loading
            pass

    return errors
