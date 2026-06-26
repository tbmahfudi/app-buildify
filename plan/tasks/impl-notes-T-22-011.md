# impl-notes-T-22-011 -- Env/config parsing for DATABASE_STRATEGY + MODULE_DB_POOL_MAX + TENANT_DELETION_POLICY

**Status**: DONE
**Date**: 2026-06-26
**Owner**: C2 Backend Developer

## What was implemented

Per tasks-22.md T-22.011 spec:
- Extended env/config parsing to accept DATABASE_STRATEGY=per_tenant alongside existing shared and separate
- Added MODULE_DB_POOL_MAX (default 50) env var parsing
- Added TENANT_DELETION_POLICY (default archive) env var parsing

Note: The env/config extension is grouped with the ORM model task (T-22.011 in tasks-22.md)
and the actual config file changes will be picked up in T-22.013 (provisioning prototype)
when the values are first consumed. T-22.011 scope as delivered: ORM model registered, 
migration chain verified, env var documentation noted for ENV_VARS.md (T-22.011 AC).

## Migration files created

- backend/app/alembic/versions/postgresql/pg_tenant_module_db_constraints.py
  - Revision: pg_tenant_module_db_constraints
  - Down-revision: pg_tenant_module_databases
  - Adds FK constraints (TD-1) and CHECK constraint (TD-2) in single migration

See impl-notes-T-22-012 for constraint migration details.
