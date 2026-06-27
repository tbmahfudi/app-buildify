# Tenant Scope Migration & the `check-tenant-scope` CI Gate

> Epic 22 — Tenant Isolation Hardening. Owner: E1 DevOps. Related: T-22.008, T-22.021, T-22.022.

## Why this exists

Soft multi-tenancy means every query against a tenant-scoped table must carry a
`WHERE tenant_id = :current_tenant` filter. A *forgotten* filter is a silent
cross-tenant data leak (see `arch-22` §1.1, risk #1). Epic 22 closes this with
two runtime layers (the `apply_tenant_scope()` helper and the
`TenantScopeListener` ORM listener) **and** a static CI gate that stops new raw
`tenant_id ==` literals from creeping back in.

## The rule

Do **not** write a raw `Model.tenant_id == <value>` filter in
`backend/app/services/` or `backend/app/routers/`. Use the centralized helper
instead:

```python
from app.core.tenant import apply_tenant_scope, apply_tenant_scope_by_id

# With a current_user (has .tenant_id and .is_superuser):
query = apply_tenant_scope(query, MyModel, current_user)

# In a static/class method with only a tenant_id UUID:
query = apply_tenant_scope_by_id(query, MyModel, tenant_id)
```

The helper is a no-op for superusers and for non-`__tenant_scoped__` models, and
raises `TenantScopeNotSetError` when a scoped model is queried with no tenant.

## The annotation convention

Some raw literals are legitimate and cannot use the helper (e.g. an explicit
`OR tenant_id IS NULL` for shared/global rows, or admin cross-tenant joins).
Annotate each such line with a trailing comment so the gate accepts it:

```python
.filter(or_(Role.tenant_id == current_user.tenant_id, Role.tenant_id.is_(None)))  # tenant-scope-ok
```

Accepted annotations (either form is treated as reviewed-and-allowed):

| Annotation        | Meaning                                                        |
|-------------------|----------------------------------------------------------------|
| `# tenant-scope-ok` | Canonical marker. Use for all new intentional exceptions.    |
| `# tenant_scope`    | Legacy marker from the T-22.007/008 migration. Still honored. |

Any raw `.tenant_id ==` literal **without** one of these annotations counts as a
violation.

## The CI gate

`manage.sh check-tenant-scope` scans `services/` and `routers/`, counts
unannotated literals, and compares against a frozen **baseline of 36**
(the router-layer literals tracked as M-2 for sprint N+1).

- **count > baseline** → exit non-zero, build fails. This is what catches a
  *new* unguarded literal.
- **count == baseline** → pass (no new violations).
- **count < baseline** → pass, with a hint to ratchet the baseline down.

Override the baseline for a ratcheting run with `TENANT_SCOPE_BASELINE=<n>`.

### CI wiring

The gate runs in `.github/workflows/ci.yml` as the `tenant-scope-gate` job,
which runs **after `lint`** and **before `test`**:

```
lint → tenant-scope-gate → test
```

A failing gate blocks the `test` job and therefore the merge.

### Running locally

```bash
bash manage.sh check-tenant-scope
```

## Ratcheting down (M-2 follow-up)

As router-layer literals are migrated to `apply_tenant_scope()` or annotated,
lower the `BASELINE` constant in the `check-tenant-scope` arm of `manage.sh`
(and the comment in `ci.yml`) to the new lower count. The ratchet must only
ever go **down** — never raise the baseline to accommodate a new violation.
