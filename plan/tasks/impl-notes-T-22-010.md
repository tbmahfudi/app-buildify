# impl-notes-T-22-010 -- TenantModuleDatabase SQLAlchemy ORM model (TD-3)

**Status**: DONE
**Date**: 2026-06-26
**Owner**: C2 Backend Developer

## What was implemented

Created `backend/app/models/tenant_module_database.py` with the `TenantModuleDatabase`
ORM class resolving tech debt TD-3 (table existed from migration; ORM model was missing).

### Columns

| Column | Type | Notes |
|--------|------|-------|
| id | GUID PK | default=generate_uuid |
| tenant_id | GUID NOT NULL | FK enforced by pg_tenant_module_db_constraints migration (TD-1) |
| module_id | GUID NOT NULL | FK enforced by pg_tenant_module_db_constraints migration (TD-1) |
| db_name | String(255) NOT NULL | Physical DB name e.g. {tenant_id}_{module_id} |
| connection_secret_ref | Text nullable | Secrets-manager ref -- never raw DSN |
| status | String(30) NOT NULL | server_default="provisioning"; CHECK via TD-2 migration |
| error_message | Text nullable | Set on status=failed; cleared on retry |
| created_at | DateTime | server_default=CURRENT_TIMESTAMP |
| updated_at | DateTime | server_default + onupdate=CURRENT_TIMESTAMP |

### Table args

- UniqueConstraint("tenant_id", "module_id", name="uq_tenant_module_databases_tenant_module")
- Index("ix_tenant_module_databases_tenant_id", "tenant_id")
- Index("ix_tenant_module_databases_module_id", "module_id")

Note: SQLAlchemy Index() in __table_args__ mirrors indexes already created by the raw-DDL
migration. Alembic autogenerate will detect them as existing -- no migration delta produced.

## Key design decisions

- NOT marked __tenant_scoped__ per schema-22 section 9 -- provisioning and cleanup scripts
  require cross-tenant visibility via with_admin_cross_tenant_scope().
- FK constraints intentionally omitted from column definitions (no ForeignKey() call)
  because DB-level FKs are added by the follow-up migration (TD-1). This avoids
  SQLAlchemy relationship loading issues before TD-1 migration runs in older envs.
- Registered in backend/app/models/__init__.py import and __all__.
