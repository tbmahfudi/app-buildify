# Utility & Operational Scripts

This document describes all utility and operational scripts in the repository.
These are **not** part of the core platform code — they are tools for setup,
development, debugging, and maintenance.

---

## Table of Contents

- [Root Level](#root-level)
- [backend/](#backend)
- [backend/scripts/](#backendscripts)
- [modules/financial/backend/](#modulesfinancialbackend)
- [scripts/](#scripts)

---

## Root Level

These scripts live at the repository root and cover end-to-end operational tasks.

### `GIT_COMMANDS.sh`
Reference script that **prints** (but does not execute) the git commands needed
to deploy the Option A MVP to GitHub. Run it to see a guided step-by-step
commit/push workflow.

```bash
./GIT_COMMANDS.sh
```

---

### `check_finance_module_access.py`
Diagnostic tool that queries the database directly to report:
- Whether the financial module is registered and installed
- Which tenants have it enabled
- Which users have access and what permissions they hold

```bash
python check_finance_module_access.py
```

---

### `enable_finance_module.sh`
Calls the REST API to enable the financial module for the authenticated user's
tenant. Requires an `AUTH_TOKEN` environment variable.

```bash
AUTH_TOKEN=<jwt> ./enable_finance_module.sh
# Override API base URL if needed:
API_BASE_URL=http://localhost:8000/api/v1 AUTH_TOKEN=<jwt> ./enable_finance_module.sh
```

---

### `fix-db.sh`
Fixes the `relation 'tenants' does not exist` error by running Alembic
migrations (`upgrade heads`) via Docker Compose. Prompts to create a `.env`
file if one is missing.

```bash
./fix-db.sh
```

---

### `manage.sh`
Docker Compose wrapper for managing the full dev environment.

```bash
./manage.sh [command] [database_type]

# Commands:  start | stop | restart | migrate | logs | clean
# Database:  postgres (default) | mysql

./manage.sh start postgres
./manage.sh migrate mysql
./manage.sh logs postgres
```

---

### `run_migration.sh`
Reference snippet (not fully executable as-is) showing the commands to run
Alembic migrations and seed data inside Docker containers.

```bash
# Contents are intended to be copy-pasted or sourced, e.g.:
docker-compose -f infra/docker-compose.dev.yml exec backend alembic upgrade heads
```

---

### `run_rbac_sql.sh`
Executes RBAC verification or cleanup SQL scripts against the PostgreSQL
container via Docker Compose.

```bash
./run_rbac_sql.sh verify
./run_rbac_sql.sh cleanup
./run_rbac_sql.sh cleanup-interactive
```

---

### `setup_financial_module.py`
Installs and enables the financial module **directly via the database**,
bypassing the REST API. Useful when the API is unavailable or during initial
bootstrap.

```bash
cd /home/user/app-buildify
python setup_financial_module.py
```

---

### `setup_financial_module.sh`
API-based alternative to `setup_financial_module.py`. Uses curl to call the
install and enable endpoints. Requires a valid `TOKEN` configured inside the
script.

```bash
./setup_financial_module.sh
```

---

### `start-frontend.sh`
Starts the frontend development server by navigating to the `frontend/`
directory and launching it. Validates that the directory and `index.html` exist
before starting.

```bash
./start-frontend.sh
```

---

### `verify_setup.py`
Checks that all required files and configuration entries for the module system
are present. Prints a pass/fail report for each expected item.

```bash
python verify_setup.py
```

---

## `backend/`

Scripts located directly in the `backend/` directory. Most interact with the
database or Alembic migration state.

### `run_be.sh`
Starts the Uvicorn development server with hot-reload.

```bash
cd backend
./run_be.sh
# Equivalent to: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### `run_migrations.py`
CLI helper that runs `alembic upgrade heads`. Accepts an optional database URL
as a positional argument, falling back to `SQLALCHEMY_DATABASE_URL` or
`DATABASE_URL` environment variables.

```bash
cd backend
python run_migrations.py
python run_migrations.py postgresql://user:pass@localhost:5432/dbname
python run_migrations.py sqlite:///./app.db
```

---

### `migrate.py`
Placeholder file — currently empty.

---

### `setup_sqllite.sh`
Sets up a local SQLite database for development: runs Alembic migrations and
seeds initial data. Prompts before overwriting an existing `app.db`.

```bash
cd backend
./setup_sqllite.sh
```

---

### `test_api.sh`
Smoke-tests the **Option A MVP** endpoints (health check, authentication, org
CRUD) using curl against `http://localhost:8000`.

```bash
cd backend
./test_api.sh
```

---

### `test_api_option_b.sh`
Smoke-tests **Option B** feature endpoints (metadata, generic CRUD, audit,
settings) using curl. Performs a login first to obtain a token.

```bash
cd backend
./test_api_option_b.sh
```

---

### `apply_tenant_nullable_migration.py`
Directly runs `ALTER COLUMN` SQL statements to make `tenant_id` nullable across
all no-code platform tables. Accepts an optional database URL argument.

```bash
cd backend
python apply_tenant_nullable_migration.py
python apply_tenant_nullable_migration.py postgresql://user:pass@localhost:5432/dbname
```

---

### `assign_menu_permissions.py`
One-time script that assigns `menu:manage:tenant` and `menu:read:tenant`
permissions to an existing admin role. Lists available roles when run without
arguments.

```bash
cd backend
python assign_menu_permissions.py                        # list roles
python assign_menu_permissions.py ADMIN FASHIONHUB
python assign_menu_permissions.py SYSTEM_ADMIN TECHSTART
```

---

### `debug_module_menus.py`
Dumps module registry and menu integration state for the FASHIONHUB tenant to
stdout. A quick one-off debug helper.

```bash
cd backend
python debug_module_menus.py
```

---

### `enable_financial_module.py`
Enables the financial module for one or more tenants specified by their tenant
code, directly via the database.

```bash
cd backend
python enable_financial_module.py TECHSTART
python enable_financial_module.py TECHSTART FASHIONHUB
```

---

### `install_financial.py`
Installs and enables the financial module using `ModuleRegistryService`. More
thorough than `enable_financial_module.py` — handles registration, installation,
and tenant enablement in one step.

```bash
cd backend
python install_financial.py
```

---

### `register_financial_module.py`
Reads `modules/financial/manifest.json` and registers the financial module
entry in the database. Typically run once before enabling it for a tenant.

```bash
cd backend
python register_financial_module.py
```

---

### `resync_module_manifest.py`
Updates a module's stored manifest in the database from its `manifest.json`
file. Use after editing a manifest to sync changes without a full reinstall.

```bash
cd backend
python resync_module_manifest.py financial
python resync_module_manifest.py --all
```

---

### `validate_module_manifest.py`
Validates a module's `manifest.json` for required fields and proper menu
integration configuration. Reports errors and warnings.

```bash
cd backend
python validate_module_manifest.py financial
python validate_module_manifest.py --all
```

---

### `diagnose_alembic.sh`
Queries the database and Alembic inside Docker containers to display the
current migration version, available heads, and recent history. Read-only
diagnostic — makes no changes.

```bash
cd backend
./diagnose_alembic.sh
```

---

### `fix_alembic_duplicate.sh`
Resolves the Alembic duplicate key error by clearing `alembic_version` and
re-stamping with `pg_merge_all_heads`.

```bash
cd backend
./fix_alembic_duplicate.sh
```

---

### `fix_alembic_heads.sh`
Restarts the backend Docker container (to pick up new migration files) then
re-stamps Alembic to resolve multiple-heads conflicts.

```bash
cd backend
./fix_alembic_heads.sh
```

---

### `fix_multi_db_heads.sh`
Handles the case where Alembic sees heads for multiple database types
(PostgreSQL, MySQL, SQLite simultaneously). Clears `alembic_version` and
upgrades only the PostgreSQL head.

```bash
cd backend
./fix_multi_db_heads.sh
```

---

## `backend/scripts/`

Standalone maintenance and data scripts intended to be run from the `backend/`
directory.

### `create_sample_data.py`
Creates sample report definitions and dashboard pages/widgets in the database
for a specified tenant and user. Used to populate test data.

```bash
cd backend
python scripts/create_sample_data.py
```

---

### `diagnose_entity_pk.py`
Detects primary-key mismatches between `entity_definitions` records and their
actual database tables — useful when the runtime model generator adds phantom
`id` columns. Accepts an optional entity name to narrow the check.

```bash
cd backend
python scripts/diagnose_entity_pk.py
python scripts/diagnose_entity_pk.py <entity_name>
```

---

### `fix_entity_table_names.py`
Updates `entity_definitions.table_name` values that are missing their module
`table_prefix`. Supports a `--dry-run` flag to preview changes before applying.

```bash
cd backend
python scripts/fix_entity_table_names.py --dry-run
python scripts/fix_entity_table_names.py
```

---

### `recalculate_tenant_usage.py`
Recalculates and corrects tenant usage counters (`current_companies`,
`current_users`, `current_storage_gb`) from actual database counts. Run after
migrations or when counters appear out of sync.

```bash
cd backend
python scripts/recalculate_tenant_usage.py
```

---

## `modules/financial/backend/`

Setup and seeding scripts specific to the Financial module.

### `setup_sample_data.py`
Seeds a complete financial dataset for a given tenant, including:
- Default chart of accounts
- Sample customers
- Sample invoices, payments, and journal entries

```bash
cd modules/financial/backend
python setup_sample_data.py TECHSTART
python setup_sample_data.py FASHIONHUB
```

---

### `setup_tenants.sh`
Convenience wrapper that runs `setup_sample_data.py` for both TECHSTART and
FASHIONHUB tenants in sequence.

```bash
cd modules/financial/backend
./setup_tenants.sh
```

---

## `scripts/`

Top-level developer tooling scripts.

### `create-module.sh`
Scaffolds a new pluggable module with a complete backend and frontend directory
structure. Takes the module name as an argument.

```bash
./scripts/create-module.sh <module-name>

# Example:
./scripts/create-module.sh warehousing
```

---

## Quick Reference

| Script | Category | When to use |
|--------|----------|-------------|
| `manage.sh` | Dev environment | Start/stop/restart Docker services |
| `start-frontend.sh` | Dev environment | Start frontend dev server |
| `backend/run_be.sh` | Dev environment | Start backend dev server (no Docker) |
| `backend/setup_sqllite.sh` | Dev environment | Bootstrap local SQLite DB |
| `backend/run_migrations.py` | Database | Run Alembic migrations |
| `fix-db.sh` | Database | Fix missing tenants relation error |
| `backend/diagnose_alembic.sh` | Database | Inspect Alembic migration state |
| `backend/fix_alembic_duplicate.sh` | Database | Fix duplicate key in alembic_version |
| `backend/fix_alembic_heads.sh` | Database | Fix multiple migration heads |
| `backend/fix_multi_db_heads.sh` | Database | Fix cross-DB-type head conflicts |
| `backend/apply_tenant_nullable_migration.py` | Database | Make tenant_id nullable in no-code tables |
| `backend/resync_module_manifest.py` | Modules | Sync manifest file → database |
| `backend/validate_module_manifest.py` | Modules | Validate manifest.json |
| `backend/register_financial_module.py` | Modules | Register financial module in DB |
| `backend/install_financial.py` | Modules | Full install of financial module |
| `backend/enable_financial_module.py` | Modules | Enable financial module per tenant |
| `setup_financial_module.py` | Modules | DB-direct financial module setup |
| `setup_financial_module.sh` | Modules | API-based financial module setup |
| `enable_finance_module.sh` | Modules | API-based enable via curl |
| `check_finance_module_access.py` | Modules | Diagnose finance module access |
| `modules/financial/backend/setup_sample_data.py` | Modules | Seed financial data for a tenant |
| `modules/financial/backend/setup_tenants.sh` | Modules | Seed financial data for all tenants |
| `backend/assign_menu_permissions.py` | RBAC | Assign menu permissions to admin roles |
| `run_rbac_sql.sh` | RBAC | Run RBAC SQL verification/cleanup |
| `backend/scripts/recalculate_tenant_usage.py` | Maintenance | Fix out-of-sync tenant usage counters |
| `backend/scripts/fix_entity_table_names.py` | Maintenance | Fix entity table_name prefixes |
| `backend/scripts/diagnose_entity_pk.py` | Maintenance | Detect entity primary-key mismatches |
| `backend/scripts/create_sample_data.py` | Testing | Seed sample reports and dashboards |
| `backend/test_api.sh` | Testing | Smoke-test Option A MVP endpoints |
| `backend/test_api_option_b.sh` | Testing | Smoke-test Option B endpoints |
| `verify_setup.py` | Testing | Verify module system file setup |
| `backend/debug_module_menus.py` | Debugging | Dump module menu state for FASHIONHUB |
| `scripts/create-module.sh` | Scaffolding | Scaffold a new pluggable module |
| `GIT_COMMANDS.sh` | Reference | Print deployment git commands |
