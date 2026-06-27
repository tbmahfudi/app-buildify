# Runbook — Tenant Isolation

> Operational runbook for the Epic 22 shared-core tenant-scope layer and
> per-tenant module databases. Audience: on-call operators and backend engineers.
>
> Related: `plan/architecture/adr-tenant-isolation-22.md`,
> `docs/platform/TENANT_ISOLATION.md`,
> `docs/backend/TENANT_SCOPE_MIGRATION.md`.

---

## 1. Diagnose `TenantScopeMissingError` (HTTP 500)

### Symptom

A request returns **HTTP 500** with a sanitized body. Backend logs show:

```
ERROR app.core.tenant_listener tenant_scope.missing model=<Model> statement=Select
... TenantScopeNotSetError: Query on tenant-scoped model '<Model>' executed without tenant scope set.
```

or, for a write:

```
ERROR app.core.tenant_listener tenant_scope.flush.missing model=<Model>
```

### What it means

A query or write hit a `__tenant_scoped__ = True` model while the
`_current_tenant_id` ContextVar was **unset**. This is the fail-loud guarantee
doing its job — it is preventing a potential cross-tenant leak. It is a **bug in
the calling code**, not a data-corruption event.

### Most common root causes

1. **A route uses `Depends(get_db)` instead of `Depends(tenant_scoped_session)`.**
   Tenant-data routes must use `tenant_scoped_session`, which sets scope on entry
   and clears it in `finally`. Public routes (login, health) keep `get_db`.
2. **A background task built a bare `SessionLocal`** and never called
   `set_tenant_scope(session, tenant_id)`.
3. **A new model was marked `__tenant_scoped__ = True`** but some caller still
   queries it outside a scoped session.

### Steps to diagnose

```bash
# 1. Find the failing route/handler from the stack trace in logs.
docker logs app_buildify_backend --since 15m 2>&1 | grep -A20 "tenant_scope.missing"

# 2. Identify the model named in the error, then find unscoped DB access:
grep -rn "Depends(get_db)" backend/app/routers/        # candidate routes
grep -rn "SessionLocal()" backend/app/                 # candidate background tasks
```

### Fix

- Route: switch the dependency to `Depends(tenant_scoped_session)`.
- Background task: wrap work in `with with_tenant_scope(tenant_id):` **or** call
  `set_tenant_scope(session, tenant_id)` before querying.
- Legitimate cross-tenant admin read: use
  `with_admin_cross_tenant_scope(user, admin_reason, audit_log_fn)`.

### Cross-tenant write rejected

```
ERROR ... tenant_scope.flush.cross_tenant model=<Model> row_tenant=<A> scope=<B>
```

A write targeting tenant A executed under scope B. This is almost always a bug —
verify the object's `tenant_id` is set from the authenticated tenant, not from
client input.

---

## 2. Check violation counts (the `check-tenant-scope` gate)

The CI gate counts unguarded raw `.tenant_id ==` literals in `services/` and
`routers/` and fails when the count exceeds the frozen **baseline of 36**.

```bash
# Run the gate locally (same command CI runs):
bash manage.sh check-tenant-scope

# Override the baseline (e.g. to ratchet after migration):
TENANT_SCOPE_BASELINE=30 bash manage.sh check-tenant-scope
```

Expected healthy output:

```
==> check-tenant-scope: scanning services/ and routers/ ... (baseline=36)
check-tenant-scope: 8 unannotated literal(s) found (baseline 36).
check-tenant-scope: PASS — and below baseline; consider lowering BASELINE to 8 to ratchet.
```

### If the gate fails (count > baseline)

A new unguarded literal was introduced. Either:

- Replace it with `apply_tenant_scope(query, Model, user)` /
  `apply_tenant_scope_by_id(query, Model, tenant_id)`, or
- If the literal is genuinely intentional (e.g. `OR tenant_id IS NULL` for shared
  rows, or an admin cross-tenant join), annotate the line `# tenant-scope-ok`.

The offending file:line list is printed by the gate. See
`docs/backend/TENANT_SCOPE_MIGRATION.md` for the full convention. The baseline
ratchets **down only** — never raise it to admit a new violation.

---

## 3. Module databases: inspect, dry-run cleanup, deactivate

Per-tenant module databases are tracked in the `tenant_module_databases` table
(columns include `tenant_id`, `module_id`, `db_name`, `status`,
`connection_secret_ref`, `error_message`). `status` ∈
`provisioning | ready | failed | archived`.

### Inspect provisioning state

```bash
docker exec app_buildify_postgresql psql -U appuser -d appdb -c \
  "SELECT tenant_id, module_id, db_name, status, error_message
     FROM tenant_module_databases
    ORDER BY updated_at DESC;"
```

A row stuck at `provisioning` or sitting at `failed` (with `error_message`) means
provisioning did not complete — re-enabling the module retries it, or check the
backend logs for the provisioner stack trace.

### Dry-run cleanup (ALWAYS do this first)

`cleanup_tenant_module_dbs.py` supports `--dry-run`, which writes **nothing** to
the database — it only reports what would happen.

```bash
# Inside the backend container:
docker exec app_buildify_backend \
  python3 /app/scripts/cleanup_tenant_module_dbs.py <tenant_id> --dry-run
```

Confirm the listed databases and the action (archive vs drop) match expectations
before running for real. The action is governed by `TENANT_DELETION_POLICY`:

- `archive` (default) — renames each DB and sets rows to `status=archived` (reversible).
- `drop` — `DROP DATABASE` and deletes rows (**irreversible**; requires superuser auth on the API path).

An `audit_log` entry `tenant.module_dbs.cleanup` is written per `(tenant, module)`
**before** any destructive operation.

### Deactivate a tenant (real cleanup)

```bash
# Preferred wrapper — runs the cleanup service for the tenant:
bash manage.sh tenant deactivate <tenant_id>

# Equivalent direct invocation (omit --dry-run to apply):
docker exec app_buildify_backend \
  python3 /app/scripts/cleanup_tenant_module_dbs.py <tenant_id>
```

After an `archive` run, verify rows moved to `archived`:

```bash
docker exec app_buildify_postgresql psql -U appuser -d appdb -c \
  "SELECT db_name, status FROM tenant_module_databases WHERE tenant_id = '<tenant_id>';"
```

### Safety checklist before a `drop`-policy cleanup

- [ ] `--dry-run` reviewed; the DB list is exactly the intended tenant's.
- [ ] `TENANT_DELETION_POLICY` is intentionally `drop` (not an accidental override).
- [ ] Invoked by/through a superuser-authenticated path.
- [ ] `tenant.module_dbs.cleanup` audit entries present after the run.

---

## 4. Escalation

- Repeated `TenantScopeMissingError` from one route after a deploy → roll back the
  offending change; the route likely lost its `tenant_scoped_session` dependency.
- Provisioning rows stuck `failed` across many tenants → check
  `MODULE_DB_POOL_MAX`, database connectivity, and the provisioner logs; this is a
  backend (C2) escalation, not an isolation breach.
- Suspected actual cross-tenant data exposure (not a 500) → treat as a security
  incident: capture logs, notify the Security Engineer, and review recent
  `# tenant-scope-ok` annotations and any `text()`/`bulk_insert_mappings` bypass
  surfaces.
