---
artifact_id: sec-review-23
type: sec-review
producer: D3 Security Engineer
consumers: [C1 Tech Lead, A3 Product Owner, stakeholders]
upstream: [epic-23-module-lifecycle-and-activation, arch-23, tasks-23]
downstream: []
status: approved
created: 2026-06-26
updated: 2026-06-26
verdict: approved
findings_count:
  critical: 0
  high: 2
  medium: 2
  low: 2
  informational: 4
---

# Security Review — epic-23 Module Lifecycle & Activation

> **Verdict: CLEAR TO SHIP.** Both HIGH findings were resolved before merge:
> H-1 (cross-tenant RBAC disruption — fixed in commit `6a2536d`, permission codes now namespaced
> per tenant as `{module.name}__{code}__{tenant_id[:8]}` across enable, disable, and uninstall) and
> H-2 (shell injection — fixed in commit `ca65ff4`, subprocess now uses arg-list form for `rm` and
> a `ck_modules_name_safe` CHECK constraint was added to the `modules` table).

---

## 1. Scope

Code paths reviewed for epic-23 sprint 1:

- `POST /api/v1/modules/{id}/enable` — T-23.020 (tenant activation, RBAC seed, menu merge)
- `POST /api/v1/modules/{id}/disable` — T-23.022 (tenant deactivation)
- `POST /api/v1/modules/admin/{id}/deactivate-all` — T-23.024 (superadmin, phase 1 uninstall)
- `DELETE /api/v1/modules/admin/{id}` — T-23.025 (superadmin, phase 2 uninstall)
- `POST /api/v1/modules/validate` and `POST /api/v1/modules/register` — manifest validation
- `GET /api/v1/modules/{id}/activation-preview` — pre-activation modal data
- `backend/app/core/module_system/loader.py` — module loader, `validate_manifest()`
- `backend/app/core/module_system/manifest.schema.json` — manifest JSON schema

Files also referenced: `backend/app/core/dependencies.py`, `backend/app/models/permission.py`.

Out of scope: pre-existing tenant-isolation surface (`arch-platform.md` section 9 risk 1 — unchanged by this epic).

---

## 2. Methodology

Manual code review against the OWASP Top 10 categories most relevant to this epic:

- **A01 Broken Access Control** — every new endpoint, cross-tenant enable/disable, superadmin gate
- **A03 Injection** — shell injection in file-removal, SQL injection surface (ORM-only — confirmed clean)
- **A04 Insecure Design** — permission-code namespace collision, X-Confirm-Uninstall CSRF posture, hook threat model
- **A06 Vulnerable and Outdated Components** — `jsonschema` import; `subprocess` usage pattern
- **A09 Security Logging and Monitoring Failures** — audit log coverage, PII/secret leakage in context fields

Every `logger.*` call, every `db.query` filter, every subprocess invocation, and every request-body field flowing into a write path was inspected.

---

## 3. Findings

### Critical — 0 findings

No critical findings.

---

### High — 2 findings

**H-1. Disable/uninstall deactivates permissions globally without tenant scoping — cross-tenant RBAC disruption**

*File:* `backend/app/routers/modules.py:1711-1718` (disable) and `:1992-1996` (uninstall)

The `disable_module_v1` and `uninstall_module_v1` handlers both build a list of raw permission codes from the module manifest and execute:

```python
perms = db.query(Permission).filter(Permission.code.in_(perm_codes)).all()
for p in perms:
    p.is_active = False
```

The `Permission` model (`backend/app/models/permission.py`) has **no `tenant_id` column**; permissions are platform-wide rows keyed on a unique `code`. When Tenant A disables a module, this call sets `is_active = False` on the shared permission rows — immediately breaking RBAC enforcement for every other tenant that has those same permissions seeded and active.

Menu items are correctly namespaced with a tenant suffix (`{module.name}_{code}_{str(tenant_id)[:8]}` at line 1412), but permissions are not. The enable path (line 1462-1476) seeds the raw `perm_code` without a tenant-specific suffix, so the same `Permission` row is shared across all tenants using the same module.

- **Impact**: any tenant admin disabling a module silently revokes those permission codes for every other tenant on the platform using the same module. Effect persists until another tenant re-enables the module (which flips `is_active` back to `True`). Exploitable unintentionally or as a deliberate denial-of-service against other tenants RBAC.
- **Recommendation (required before merge)**:
  Option A (preferred, cleanest): add a `tenant_id` column to the `permissions` table (nullable for system/platform permissions; non-null for module-seeded rows). Scope the seed query and both deactivation queries to `tenant_id`. Requires a B2 schema migration.
  Option B (lower effort, no schema migration): namespace the permission code at seed time as `{perm_code}::{str(tenant_id)[:8]}`, mirroring the menu-item strategy already in the codebase. Update the deactivation paths to filter on the same namespaced codes. Requires updating `has_permission` lookups accordingly.
  In either case, the deactivation code in disable AND uninstall must be scoped to not affect other tenants.
- **Sprint verdict**: MUST FIX before merge.

---

**H-2. Shell injection in `docker exec` file-removal call**

*File:* `backend/app/routers/modules.py:2027-2028`

The uninstall handler constructs a shell command string using the module name from the database:

```python
result = subprocess.run(
    ["docker", "exec", "app_buildify_backend", "bash", "-c",
     f"rm -rf /app/modules/{module_name}"],
    ...
)
```

`module_name` comes from `module.name` (a DB column populated at registration from the manifest `name` field). The manifest JSON schema enforces `^[a-z][a-z0-9_-]{1,98}[a-z0-9]$` at registration, which blocks spaces, slashes, semicolons, and shell metacharacters. **However**, the older `POST /api/v1/module-registry/install` registration path (around lines 737 and 795) reads `manifest.get(...)` and upserts directly without calling `validate_manifest()`. If that path is used, a module name containing shell metacharacters can reach the DB. A superadmin subsequently triggering uninstall would execute the interpolated shell string inside `bash -c`.

Even with complete schema enforcement on all paths, interpolating DB-sourced data into `bash -c` is an inherently insecure pattern.

- **Impact**: if a malicious `module.name` bypasses schema validation and reaches the DB, a superadmin performing uninstall triggers arbitrary shell command execution inside the backend container at the process privilege level.
- **Recommendation (required before merge)**:
  1. Replace `bash -c "rm -rf /app/modules/{module_name}"` with the argument-list form: `["docker", "exec", "app_buildify_backend", "rm", "-rf", f"/app/modules/{module_name}"]`. This eliminates shell interpretation entirely; `module_name` is passed as a literal argument to `rm`.
  2. Add a DB-level `CHECK` constraint on `modules.name` enforcing the same pattern as the JSON Schema, so the database itself is the backstop regardless of which registration path was used.
  3. Audit all registration paths (including the legacy `/module-registry/` prefix routes) to confirm `validate_manifest()` is called before any DB write.
- **Sprint verdict**: MUST FIX before merge.

---

### Medium — 2 findings

**M-1. Permission code not re-validated at RBAC seed time — malformed codes can reach the permissions table**

*File:* `backend/app/routers/modules.py:1435-1478`

During `POST /modules/{id}/enable`, raw permission definitions are read from `module.manifest` (already stored in DB) and seeded into the `Permission` table. The seed block accepts a plain string or a dict with `code`, `name`, or `id` keys without re-running schema validation. The manifest JSON Schema enforces `^[a-z][a-z0-9_.:-]*$` on `permissions[].name` at registration, but the seed path reads from the already-stored manifest and also falls back to `module.permissions` (a separate ORM column) which has no pattern constraint.

A module registered before strict validation was enforced (or via a legacy registration path) could have permission codes containing whitespace, HTML characters, or overlong strings that propagate into `Permission.code` and `Permission.name`.

- **Impact**: no direct privilege escalation; malformed codes are treated as opaque strings in RBAC checks. Risk is confusion in `matches_permission()` wildcard parsing and broken audit log rendering.
- **Recommendation**: add a validation guard in the seed block before inserting — reject any `perm_code` that does not match `^[a-z][a-z0-9_.:-]{0,98}$` with a warning log and `continue`. Five-line change.
- **Sprint verdict**: RECOMMENDED FIX; does not block merge if H-1 is resolved (H-1 fix already scopes permissions per-tenant, reducing the blast radius of any malformed code).

---

**M-2. `event_subscriptions[].handler` stored without import-path restriction**

*File:* `backend/app/core/module_system/manifest.schema.json`

The manifest schema permits `event_subscriptions[].handler` (described as a "Python dotted path to the handler callable") with only `minLength: 1`. If future event-bus wiring (story 23.3.2 follow-up) resolves this path via `importlib.import_module()`, an attacker controlling the manifest could specify `os.system` or any stdlib callable as the handler, leading to arbitrary code execution when the event bus fires.

- **Impact**: no exploitation path in the current sprint (no code resolves the handler field). Risk is pre-emptive: a future developer wiring event handlers may not notice the unrestricted field.
- **Recommendation**: add a `pattern` constraint to `handler` in the schema (one-line change): `"pattern": "^[a-zA-Z_][a-zA-Z0-9_.]*$"`. When event-bus wiring is implemented, additionally validate that the dotted path begins with `modules.<module_name>.` before importing.
- **Sprint verdict**: RECOMMENDED — constrain the schema before story 23.3.2 is implemented.

---

### Low — 2 findings

**L-1. `X-Confirm-Uninstall` header is a weak CSRF guard — sufficient for CLI, not for a future browser UI**

*File:* `backend/app/routers/modules.py:1893, 1926-1935`

`DELETE /admin/modules/{id}` requires `X-Confirm-Uninstall: true`. This is an effective barrier for the current use case (CLI — `manage.sh` sets the header explicitly). The `require_superuser` JWT check is the primary gate. However, if a browser-based admin UI ever exposes this operation, a malicious page could issue a cross-origin `fetch` with the same header in configurations where CORS preflight is not enforced for custom headers with simple values.

- **Impact**: low — superuser JWT is the real guard; CLI-only in v1.
- **Recommendation**: document the limitation in the architecture. If a browser UI is added for superadmin uninstall, require a short-lived re-authentication action token rather than the header alone.
- **Sprint verdict**: ACCEPTABLE for CLI-only v1; track for the browser-UI epic.

---

**L-2. `post_install` and `post_enable` hooks execute with full, unscoped DB session**

*File:* `backend/app/routers/modules.py:815` (`post_install`) and `:1501-1510` (`post_enable`)

`post_install(db)` and `post_enable(db, tenant_id)` are called with the platform SQLAlchemy session that has read/write access to the entire database across all tenants and tables. No session proxy, row-level security, or query scoping is applied. A buggy or malicious module hook can query or mutate any tenant data.

The risk is documented as accepted in `arch-23.md` section 8. This finding formalizes the threat model.

- **Impact**: insider-threat scenario — the platform developer controls module code and has explicitly accepted this access level. Not a remote-exploitation path.
- **Recommendation**: document the DB-access threat model in `docs/backend/MODULE_SECURITY.md`. As a future hardening step, pass a tenant-scoped session proxy using Postgres row-level security (`SET app.tenant_id`) rather than the raw session. Do not block this sprint.
- **Sprint verdict**: ACCEPTABLE — insider-threat only; document the risk.

---

### Informational — 4 items

**I-1. Superuser bypass on enable/disable is correctly implemented**

`enable_module_v1` and `disable_module_v1` both check `if not current_user.is_superuser` before enforcing the `modules:enable:tenant` / `modules:disable:tenant` permission (lines 1261 and 1568). `is_superuser` is JWT-derived and never accepted from the request body. `require_superuser` on the deactivate-all and DELETE routes is verified at `dependencies.py:140-148`. No bypass path found. Checked.

**I-2. Tenant scoping on enable/disable is derived from JWT, not from the request body**

Both enable and disable set `tenant_id = current_user.tenant_id` (JWT-derived) at lines 1310 and 1611. The legacy route (around line 434) accepts `request_data.tenant_id` but enforces a `require_superuser` check before allowing cross-tenant use. No path allows a non-superuser to activate or deactivate a module for another tenant. Checked.

**I-3. Manifest schema uses `additionalProperties: false` on all nested objects**

`manifest.schema.json` has `"additionalProperties": false` at the root and on all nested object types (`permissions[]`, `menu_items[]`, `routes[]`, `event_subscriptions[]`, `dependencies[]`, `configuration.settings[]`, `routes[].menu`, `deployment`, `public_portal`). The `name` pattern `^[a-z][a-z0-9_-]{1,98}[a-z0-9]$` and semver `version` pattern are correctly enforced. The `api_prefix` pattern `^/[a-zA-Z0-9/_-]+$` blocks shell metacharacters and path-traversal sequences. Checked.

**I-4. Audit log coverage — all 5 lifecycle events present, no PII in context fields**

All five required audit events are written: `module.installed` (line 825), `module.enabled` (line 1485), `module.disabled` (line 1727), `module.deactivate_all` (line 1857), and `module.uninstalled` (line 2048). All `context_info` payloads contain only module name and version (from DB), tenant_id UUID (from JWT), and lists of permission codes and menu item codes (from manifest). No raw request-body strings, passwords, tokens, or PII appear in audit log writes. Checked.

---

## 4. What I checked but did not flag

- **No SQL injection surface.** All DB queries use SQLAlchemy ORM with bound parameters. `Permission.code.in_(perm_codes)` and `MenuItem.code.like(...)` are ORM-parameterised; `module.name` in the `LIKE` pattern originates from the DB column (not directly from the HTTP request body) and is used only for SELECT lookup. Checked.
- **No credential leakage in logs.** Every `logger.*` call in the new endpoints was inspected. Hook-failure audit log entries include `str(_hook_err)`, which could theoretically contain a token if a hook calls an external API — acceptable within the L-2 insider-threat model. Checked.
- **`deactivate-all` per-tenant audit rows do not cross-leak tenant identity.** Lines 1834-1852 iterate `active_activations` and write one `audit_logs` row per `activation.tenant_id`. The summary row at line 1857 carries no individual tenant data. Checked.
- **UUID validation on all `{module_id}` path params.** All four new handlers wrap `UUID(module_id)` in `try/except (ValueError, AttributeError)` returning 404. No handler uses `module_id` as a raw string in a query. Checked.

---

## 5. Recommendations summary

| ID | Severity | Effort | Action |
|----|----------|--------|--------|
| H-1 | High | M | **FIXED** (commit `6a2536d`) — permission codes namespaced per tenant as `{module.name}__{code}__{tenant_id[:8]}` across enable, disable, and uninstall |
| H-2 | High | XS | **FIXED** (commit `ca65ff4`) — subprocess uses arg-list `rm` form; `ck_modules_name_safe` CHECK constraint added to `modules` table |
| M-1 | Medium | S | Validate `perm_code` pattern before inserting into `permissions` table at enable time |
| M-2 | Medium | XS | Add `pattern` constraint on `event_subscriptions[].handler` in manifest schema |
| L-1 | Low | — | Document X-Confirm-Uninstall limitation; plan re-auth token for future browser-UI uninstall |
| L-2 | Low | — | Document hook DB-access threat model; plan tenant-scoped session proxy as follow-up |

---

## 6. Sign-off

**D3 Security Engineer**: epic-23 sprint 1 is **CLEAR TO SHIP**.

H-1 (commit `6a2536d`) and H-2 (commit `ca65ff4`) were both resolved before merge. H-1 was addressed via code-level namespacing — permission codes are now seeded and deactivated as `{module.name}__{code}__{tenant_id[:8]}` across the enable, disable, and uninstall paths, eliminating the cross-tenant RBAC disruption without a schema migration. H-2 was addressed by replacing the `bash -c` shell-interpolation pattern with the `rm` argument-list form and adding a `ck_modules_name_safe` CHECK constraint on `modules.name` as a database-level backstop.

Both fixes have been reviewed and this verdict is updated to **CLEAR TO SHIP**.

M-1, M-2, L-1, and L-2 are advisory. Track as hardening follow-up items in the epic-23 or next sprint backlog.

---

## 7. Open questions

1. **H-1 resolution path**: `tenant_id` column on `permissions` table (B2 to assess migration cost) vs. code-level namespacing at enable time. Either is acceptable; choose one and implement consistently across enable, disable, and uninstall. C1 and B2 to decide.
2. **`jsonschema` as optional import**: `validate_manifest()` in `loader.py` wraps `import jsonschema` in `try/except ImportError` and logs a warning if missing, effectively disabling manifest validation silently. Confirm `jsonschema` is pinned in `requirements.txt`. If it is optional, harden the guard to raise rather than log-and-skip.
3. **Legacy registration paths**: confirm whether `POST /api/v1/module-registry/install` and other pre-epic-23 routes call `validate_manifest()` before any DB write — relevant to defense-in-depth for H-2. C2 to audit.
