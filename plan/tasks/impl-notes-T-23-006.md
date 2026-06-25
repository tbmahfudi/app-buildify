# impl-notes — T-23.006: manifest.schema.json — full epic-23 field coverage

**Task**: T-23.006
**Owner**: C2 Backend Developer
**Status**: DONE
**Date**: 2026-06-25

---

## What was done

Updated `backend/app/core/module_system/manifest.schema.json` (JSON Schema draft-07) to cover all manifest fields required by epic-23 story 23.2.1 backend AC.

---

## Changes from the previous schema

| Concern | Before | After |
|---------|--------|-------|
| `version` semver pattern | Loose: `^[0-9]+\.[0-9]+\.[0-9]+([-+].+)?$` | Strict semver 2.0: full pre-release + build-metadata regex |
| `module_type` enum | `["code", "nocode", "hybrid"]` | `["code", "nocode"]` — matches epic-23 spec exactly; `hybrid` removed |
| `api_prefix` | Nested under `api.prefix` object | Promoted to top-level required field `api_prefix` |
| `menu_items[]` | Nested under `frontend.menu_items` | Promoted to top-level array `menu_items` with item schema (`label`, `route` required) |
| `event_subscriptions[]` | Missing | Added as top-level array; item schema requires `event` + `handler` (dotted Python path) |
| `dependencies[]` | Object `{required: [], optional: []}` — string arrays | Flat array of objects; each item: `{name (pattern), version?, optional?}` |
| `required` top-level fields | `["name", "version", "display_name"]` | `["name", "display_name", "version", "module_type", "category", "api_prefix"]` |
| `additionalProperties` | `true` | `false` — rejects unknown top-level keys |

---

## Semver pattern used

```
^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$
```

This is the canonical semver.org 2.0.0 regex. It rejects `1.0`, `01.0.0`, `1.0.0.0` and other non-compliant strings while accepting pre-release (`1.0.0-alpha.1`) and build metadata (`1.0.0+build.42`).

---

## Field coverage checklist (epic-23 story 23.2.1)

| Field | Required | Type | Constraint | Present |
|-------|----------|------|------------|---------|
| `name` | yes | string | `^[a-z][a-z0-9_-]{1,98}[a-z0-9]$` | yes |
| `display_name` | yes | string | minLength=1, maxLength=255 | yes |
| `version` | yes | string | strict semver 2.0 pattern | yes |
| `module_type` | yes | string | enum `["code", "nocode"]` | yes |
| `category` | yes | string | minLength=1, maxLength=50 | yes |
| `api_prefix` | yes | string | `^/[a-zA-Z0-9/_-]+$` | yes |
| `permissions[]` | no | array | items: `{name, description}` required; `name` pattern | yes |
| `menu_items[]` | no | array | items: `{label, route}` required | yes |
| `routes[]` | no | array | items: `{path, name}` required | yes |
| `event_subscriptions[]` | no | array | items: `{event, handler}` required | yes |
| `dependencies[]` | no | array | items: `{name}` required; name matches module name pattern | yes |

---

## Preserved fields (existing, not in epic-23 required list)

All previous optional fields were retained to avoid breaking existing manifests: `description`, `author`, `license`, `homepage`, `repository`, `support_email`, `subscription_tier`, `is_core`, `backend_service_url`, `configuration`, `tags`, `parent_module`, `deployment`, `public_portal`.

The `api` nested object (old `api.prefix`) was removed since `api_prefix` is now the canonical top-level field. The `frontend` nested object (old `frontend.menu_items`) was also removed; `menu_items` is now top-level.

---

## Next step

T-23.007: wire `jsonschema.validate()` in `loader.py` using this schema; add `POST /modules/validate` dry-run endpoint.
