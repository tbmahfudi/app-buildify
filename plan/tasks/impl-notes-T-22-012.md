# impl-notes-T-22-012 -- Alembic migration pg_tenant_module_db_constraints (TD-1 + TD-2)

**Status**: DONE
**Date**: 2026-06-26
**Owner**: C2 Backend Developer

## What was implemented

Created `backend/app/alembic/versions/postgresql/pg_tenant_module_db_constraints.py`.

Single migration file combining TD-1 (FK constraints) and TD-2 (CHECK constraint) as
specified in tasks-22.md T-22.012. Down-revision chains from pg_tenant_module_databases.

### upgrade() operations

1. TD-1 FK: tenant_id -> tenants(id) ON DELETE CASCADE
   Constraint name: fk_tmd_tenant

2. TD-1 FK: module_id -> modules(id) ON DELETE CASCADE
   Constraint name: fk_tmd_module

3. TD-2 CHECK: status IN ('provisioning', 'ready', 'failed', 'archived')
   Constraint name: ck_tmd_status
   Values match schema-22 section 3.3 lifecycle table.

### downgrade() operations

Drops ck_tmd_status, fk_tmd_module, fk_tmd_tenant (in that order) using IF EXISTS.

## Key design decisions

- Combined TD-1 and TD-2 into one migration file (pg_tenant_module_db_constraints.py)
  as tasks-22.md T-22.012 specifies a single follow-up file.
- Used raw op.execute() SQL (same pattern as pg_tenant_module_databases.py base migration)
  for consistency with existing migration style in this project.
- ON DELETE CASCADE on both FKs: tenant deletion removes all module DB registry rows
  (cleanup service handles actual DB drop/archive before tenant row is deleted).
- IF EXISTS in downgrade prevents errors when running downgrade on a DB where constraints
  were never applied (e.g. the original raw-DDL environment).
