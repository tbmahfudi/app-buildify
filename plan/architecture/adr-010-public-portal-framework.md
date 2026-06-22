# ADR-010 — Public Portal Framework

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-06-23 |
| **Deciders** | A3 (Product Owner), B1 (Software Architect) |
| **Supersedes** | — |

---

## Context

Modules need to serve public-facing pages — clinic discovery, patient registration forms,
booking widgets — without requiring the visitor to be logged in. Without a platform
framework for this, each module that needs a public page must:

- Invent its own URL structure (no guarantee of consistency)
- Add its own nginx `location` block (duplication, review overhead)
- Implement its own auth-bypass pattern (risk of accidentally protecting a public page
  or accidentally leaving a staff page unprotected)

The result is inconsistency across modules and growing maintenance overhead as each
module manages its own public surface independently.

---

## Decision

**The platform owns the `/portal/{module_slug}/` URL namespace.**

nginx serves each module's `frontend/public/` assets at that path with SPA fallback.
Modules opt in by declaring `public_portal` in their `manifest.json`. The platform
provides a `get_current_user_optional` dependency for backend routes that personalise
content when a user is logged in but work correctly for anonymous visitors.

---

## nginx Pattern

The following `location` block is added once to `infra/nginx/app.conf` and covers all
registered module portals:

```nginx
location ~ ^/portal/([a-z][a-z0-9-]*)/(.*)$ {
    alias /usr/share/nginx/html/modules/$1/public/$2;
    try_files $uri $uri/ /portal/$1/index.html;
}
```

- `$1` — the module slug (e.g. `healthcare`)
- `$2` — the remainder of the path
- `try_files` provides SPA fallback so client-side routing works correctly

---

## Manifest Declaration

Modules that want a public portal add the `public_portal` field to `manifest.json`:

```json
"public_portal": {
  "enabled": true,
  "entry_point": "frontend/public/index.html",
  "title": "Find a Clinic"
}
```

The `title` field is used by the platform shell for browser tab titles and any
cross-module portal directory pages. Modules without this field have no public portal;
the nginx pattern simply returns 404 for their slug.

---

## `get_current_user_optional` Dependency

Lives in `backend/app/core/dependencies.py`. It wraps the standard `get_current_user`
dependency, catches all authentication errors (missing token, invalid token, expired
token), and returns `None` instead of raising `401 Unauthorized`.

Usage in a module route:

```python
from backend.app.core.dependencies import get_current_user_optional

@router.get("/api/v1/modules/healthcare/clinics")
async def list_clinics(
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),   # User | None
):
    results = query_clinics(db)
    if user:
        results = personalise_for_user(results, user)
    return results
```

Routes that use this dependency never return `401` to anonymous callers.

---

## Module Public Frontend Convention

| Item | Value |
|------|-------|
| Asset directory | `modules/{name}/frontend/public/` |
| Entry point | `index.html` (SPA shell) |
| Client-side routing | Hash fragments — `#search`, `#clinic/medcare`, `#register` |
| URL at runtime | `/portal/{module_slug}/` |

Hash-fragment routing is required so that the nginx `try_files` fallback always
serves `index.html` regardless of the client-side route.

---

## Separation Rule

| Path | Audience | Auth |
|------|----------|------|
| `/portal/{slug}/` | Public / patients | Anonymous; optional auth via `get_current_user_optional` |
| `#/{slug}/...` (existing staff portal) | Staff / tenants | Required — `get_current_user` |

The existing staff SPA routes (e.g. `#/healthcare/dashboard`) are unchanged. Public
and staff surfaces are separated at the URL level and at the dependency level.

---

## Consequences

### Positive

- Uniform URL structure: all public portals live at `/portal/{slug}/`, making them
  discoverable and easy to link.
- Module authors only write page content — no nginx config, no auth-bypass plumbing.
- Any future module gets a public surface for free by declaring `public_portal` in its
  manifest and placing an `index.html` in the right directory.

### Constraints

- Sub-modules cannot have their own `/portal/{sub_module_slug}/` path. They must surface
  public-facing pages through their parent module's portal (`/portal/{parent_slug}/`).
  This maintains a single public URL per clinic service and prevents URL proliferation
  (see ADR-008 and its public portal inheritance note).
- All public portal assets are served by nginx directly; they are not processed by the
  FastAPI application server.

---

## Implementation Checklist

- [ ] `infra/nginx/app.conf` — add the `location ~ ^/portal/...` block described above
- [ ] `backend/app/core/manifest.schema.json` — add `public_portal` object to the
      manifest JSON schema (properties: `enabled`, `entry_point`, `title`)
- [ ] `backend/app/core/dependencies.py` — implement `get_current_user_optional`
- [ ] Install pipeline — copy `frontend/public/` assets to
      `/usr/share/nginx/html/modules/{slug}/public/` during module install step 6
- [ ] Docs — `docs/modules/CREATING_A_MODULE.md` — add Public Portal section
