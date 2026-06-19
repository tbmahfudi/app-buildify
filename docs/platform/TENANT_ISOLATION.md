---
artifact_id: tenant-isolation
type: architecture-doc
producer: Platform Engineering
covers_epics: [epic-22]
created: 2026-06-20
updated: 2026-06-20
---

# Tenant Isolation — Platform Architecture

> **Two-layer defence**: every read path is filtered twice — first by the ORM-level `TenantScopeListener` (automatic, hard to bypass), then by the service-level `apply_tenant_scope()` helper (explicit, auditable). A raw query that skips both layers fails the `manage.sh check-tenant-scope` gate.

## 1. Overview

App-Buildify is a multi-tenant SaaS platform. All tenant data must be strictly isolated: one tenant must never read or write another tenant's records, even if they share the same underlying Postgres instance.

Epic 22 delivers this via two complementary strategies:

| Strategy | Scope | Story |
|---|---|---|
| **Shared-DB row-level filtering** | Platform core DB (`appdb`) | 22.2, 22.3 |
| **Database-per-tenant** | Module-specific DBs (opt-in) | 22.1, 22.4 |

---

## 2. Layer 1 — Shared-core-DB hardening

### 2.1 `scope.py` helper (`backend/app/core/scope.py`)

Three public symbols:

| Symbol | Purpose |
|---|---|
| `apply_tenant_scope(query, model, user)` | Adds `WHERE tenant_id = <user.tenant_id>` to a SQLAlchemy `Query`. No-op for superusers and models without a `tenant_id` column. |
| `tenant_scope_dependency(user)` | FastAPI dependency that raises `TenantScopeMissingError` when the user has no tenant context. |
| `with_admin_cross_tenant_scope(user, reason, audit_log_fn)` | Context manager for legitimate superuser cross-tenant reads. Requires `is_superuser=True` and a non-empty `admin_reason` string. Always audit-logged. |

**Adding a new tenant-scoped service method:**

```python
from app.core.scope import apply_tenant_scope

def list_invoices(db, user):
    q = db.query(Invoice)
    q = apply_tenant_scope(q, Invoice, user)
    return q.all()
```

### 2.2 SQLAlchemy session listener (`backend/app/core/tenant_listener.py`)

`TenantScopeListener.install(engine)` attaches an `orm_execute` event. For any model decorated with `__tenant_scoped__ = True`, every ORM SELECT automatically receives a `WHERE tenant_id = <scope>` clause. If the session has no scope set, `TenantScopeMissingError` is raised before the query hits Postgres.

**Marking a model as tenant-scoped:**

```python
class Invoice(Base):
    __tablename__ = 'invoices'
    __tenant_scoped__ = True   # ← add this

    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey('tenants.id'), nullable=False)
    ...
```

### 2.3 Per-request scope binding (`backend/app/core/dependencies.py`)

The `tenant_scoped_session` FastAPI dependency:
1. Resolves the current user via `get_current_user`.
2. Calls `set_tenant_scope(db, user.tenant_id)`.
3. Yields the session.
4. Calls `clear_tenant_scope(db)` in the finally block.

Superusers receive the special marker `__superuser__` which tells the listener to skip filtering.

**Using in a router:**

```python
from app.core.dependencies import tenant_scoped_session

@router.get("/invoices")
def list_invoices(db: Session = Depends(tenant_scoped_session)):
    return db.query(Invoice).all()  # tenant filter applied automatically
```

### 2.4 `manage.sh check-tenant-scope` gate

Run before every deploy:

```bash
./manage.sh check-tenant-scope
```

Exits non-zero if any file in `backend/app/services/` contains a raw `.tenant_id ==` comparison that bypasses the helper. CI should block merges when this gate fails.

---

## 3. Layer 2 — Database-per-tenant for module DBs

### 3.1 When to use per-tenant DBs

Use `DATABASE_STRATEGY=per_tenant` when:
- A module stores large volumes of tenant-specific data (e.g. financial ledgers).
- Regulatory requirements demand physical data separation.
- You need per-tenant backup/restore or per-tenant schema evolution.

### 3.2 `tenant_module_databases` table

Tracks provisioning state for each (tenant, module) pair.

| Column | Type | Purpose |
|---|---|---|
| `id` | UUID | PK |
| `tenant_id` | UUID | Owning tenant |
| `module_id` | UUID | Module being provisioned |
| `db_name` | VARCHAR | `{tenant_id}_{module_id}` (sanitised) |
| `connection_url` | TEXT | Full DSN for the per-tenant DB |
| `status` | VARCHAR(30) | `provisioning` → `ready` → `archived` |
| `error_message` | TEXT | Set on failure |

### 3.3 Provisioning flow

1. Module enabled for tenant → `status = 'provisioning'` row inserted.
2. `scripts/provision-tenant-module-db.py <tenant_id> <module_id>` is invoked (≤60 s gate).
3. Status polled via `GET /api/v1/modules/{module_id}/provisioning-status`.
4. Frontend badge shows `provisioning` / `ready` / `failed`.

### 3.4 `ModuleScopeMiddleware`

When `DATABASE_STRATEGY=per_tenant`:
- Intercepts `POST/GET/PATCH /api/v1/modules/{module_id}/...`.
- Sets `request.state.module_scope = module_id`.
- Downstream dependencies resolve the per-tenant DB from `tenant_module_databases`.

### 3.5 Fan-out migrations

To migrate all tenant DBs for a module:

```bash
python3 scripts/migrate-module.py <module_id>
```

### 3.6 Tenant deactivation

```bash
./manage.sh tenant deactivate <tenant_id>
```

Marks all `tenant_module_databases` rows as `status='archived'`. Does **not** drop the physical databases — that requires a separate DBA step with a 30-day retention window.

---

## 4. Caveats for direct DB access

- **Never** query tenant data via `psql` or raw SQL outside the ORM without first setting `SET app.current_tenant_id = '<uuid>';` and adding `WHERE tenant_id = current_setting('app.current_tenant_id')::uuid` to your query.
- The `TenantScopeListener` only protects ORM queries. Raw `engine.execute()` or `connection.execute()` calls bypass it entirely.
- Celery workers must call `set_tenant_scope(session, tenant_id)` before processing any tenant-scoped task.

---

## 5. Adding a new tenant-scoped table

1. Add `tenant_id UUID NOT NULL REFERENCES tenants(id)` to the CREATE TABLE DDL.
2. Set `__tenant_scoped__ = True` on the SQLAlchemy model class.
3. Return the table name from `get_tenant_scoped_tables()` in your `BaseModule` subclass.
4. Add an index: `CREATE INDEX ON my_table (tenant_id);`.
5. Run `./manage.sh check-tenant-scope` to verify no service method bypasses the helper.
