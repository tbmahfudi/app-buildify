# impl-notes-T-22-018 -- cleanup_tenant_module_dbs.py

**Task**: T-22.018
**File**: scripts/cleanup_tenant_module_dbs.py
**Status**: DONE

## What was implemented

Replaced the bare-bones stub (archive-only, no audit, no dry-run) with a
full implementation per tasks-22.md T-22.018 spec and arch-22 section 3.6.

### Key design choices

**TENANT_DELETION_POLICY=archive (default)**

Renames the physical PostgreSQL database to db_name__archived__ts,
updates the tenant_module_databases row status to archived and db_name to
the renamed value. Physical rename uses the admin postgres connection
(pointed at the postgres maintenance DB) so we are never connected to the
target DB during the rename. Active connections are terminated first via
pg_terminate_backend before the ALTER DATABASE RENAME.

**TENANT_DELETION_POLICY=drop**

Terminates connections, runs DROP DATABASE IF EXISTS, then DELETEs the
tenant_module_databases row. Requires DROP_AUTH_TOKEN env var to be set
(non-empty) as a superuser guard -- prevents accidental destruction in
shared/staging environments where the env var would not be present.

**Audit BEFORE destructive operation (D3 / T-22.020)**

_write_audit_entry() is called before any ALTER DATABASE or DROP DATABASE.
On audit INSERT failure the function logs at ERROR but does not abort --
failing the cleanup because of an audit table issue would leave tenant data
in a worse inconsistent state.

**--dry-run**

When dry_run=True, _write_audit_entry IS still called (the audit row is
written to log the intent), but no ALTER/DROP/UPDATE/DELETE is executed.
D3 requirement: dry-run writes NO physical database changes.

**Two-engine pattern**

engine points at the application DB (AUTOCOMMIT) for row SELECT/UPDATE/DELETE.
admin_engine points at the postgres maintenance DB (AUTOCOMMIT) for DDL
(ALTER DATABASE, DROP DATABASE). AUTOCOMMIT is required because DDL
cannot run inside a transaction in PostgreSQL.

**Standalone script -- no FastAPI import**

The script imports only sqlalchemy; it does not import the app stack. This
allows it to be run directly from manage.sh without starting the full server
and also makes it importable from within the FastAPI app (T-22.019 wiring)
without circular dependency risk.

## Security verification (D3 requirements met)

- policy=drop path raises PermissionError if DROP_AUTH_TOKEN is not set.
- Audit entries written BEFORE any destructive operation.
- --dry-run flag makes zero database changes (no UPDATE, no DROP, no DELETE).
- Physical DB rename/drop uses admin engine, never a raw DSN from rows.

## Files changed

- scripts/cleanup_tenant_module_dbs.py -- full rewrite
