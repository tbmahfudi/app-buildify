# ADR-008 — Sub-module Deployment Topology

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-06-22 |
| **Deciders** | A3 (Product Owner), B1 (Software Architect) |
| **Supersedes** | — |

---

## Context

As the module ecosystem grows, some product domains (e.g. Healthcare) decompose into many
closely-related sub-features (lab, billing, pharmacy, scheduling). If each sub-feature is
packaged as a fully independent top-level module, the deployment surface explodes:

- Every new sub-feature demands its own container, process supervisor, port, and health check.
- Sub-features within the same domain share a DB namespace and auth context — running them in
  separate containers forces cross-service DB calls for what is logically intra-service logic.
- Tenant activation becomes operationally expensive: enabling "healthcare-lab" for a tenant
  would spin a new container per tenant, which is not viable at scale.

The platform therefore needs a first-class concept of a **sub-module**: a module that runs
*inside* an already-deployed parent service rather than as its own deployment unit.

---

## Decision

**Sub-modules deploy inside their parent service. Top-level modules get their own deployment unit.**

The `parent_module` field in `manifest.json` is the routing key for the install pipeline:

- If `parent_module` is set → the install pipeline **injects** the sub-module into the named
  parent service directory and signals the parent to hot-reload its routes.
- If `parent_module` is null/absent → standard install path (embedded or standalone service).

Sub-modules declare `"deployment": { "mode": "inherit" }`, meaning they inherit the
deployment mode (and therefore the process, container, and DB connection) of their parent.

### Install pipeline branch (authoritative pseudocode for C2)

```
if manifest.parent_module:
    -> inject sub-module files into parent service directory
    -> signal parent service to reload routes
else:
    -> standard install (embedded or standalone)
```

### manifest.json for a sub-module

```json
{
  "name": "healthcare-lab",
  "parent_module": "healthcare",
  "deployment": { "mode": "inherit" },
  "...": "..."
}
```

---

## Consequences

### For C4 / C5 module developers

- Sub-module authors must declare `parent_module` in their manifest. The install pipeline
  enforces that the named parent module is already installed before accepting the sub-module.
- Sub-modules share the parent's DB connection and tenant context — they **must not** assume
  a separate connection pool or separate Alembic revision chain. DB table names should follow
  the parent's namespace convention (e.g. `hc_*` for healthcare).
- Sub-module routes are registered under the parent service's FastAPI router, so the prefix
  `/api/v1/modules/<parent>/` is effectively shared.

### Shared DB namespace (B1 note)

B1 called out that sub-modules must respect the parent module's DB table namespace to avoid
migration conflicts. Healthcare sub-modules therefore prefix all tables with `hc_` regardless
of which sub-module owns the table. The parent (`healthcare/core`) owns the namespace; sub-
modules lease from it.

### Graduation path

A sub-module can be promoted to a top-level module by:

1. Removing `parent_module` from the manifest.
2. Declaring the former parent as a `dependencies.required` entry.
3. Providing its own `deployment.mode` (`"embedded"` or `"standalone"`).
4. Migrating any shared DB tables it owns into its own namespace (new Alembic migration).

This is an **explicit architectural migration**, not a runtime toggle. It requires a new
module version and coordinator approval.

### What does not change

- Tenant activation API is unchanged — sub-modules are activated per-tenant via the same
  `POST /api/v1/admin/modules/<name>/activate` endpoint.
- The module SDK surface (`modules.sdk`) is unchanged for sub-module code.
- Frontend asset delivery is unchanged.

---

## Implementation checklist

- [ ] **Schema** (`backend/app/core/module_system/manifest.schema.json`): add `parent_module`
      (string | null) and `deployment.mode` enum including `"inherit"`.
- [ ] **Install pipeline** (`backend/app/core/module_system/installer.py` or equivalent):
      branch on `parent_module` as described above.
- [ ] **Healthcare restructure**: update manifests for `healthcare-lab`, `healthcare-billing`,
      `healthcare-pharmacy`, `healthcare-scheduling` to set `parent_module: "healthcare"` and
      `deployment.mode: "inherit"`.
- [ ] **Docs**: `docs/modules/CREATING_A_MODULE.md` — add Sub-modules section.
- [ ] **Template**: `modules/template/manifest.json` — add `deployment` block; document
      `parent_module` in `modules/template/README.md`.
