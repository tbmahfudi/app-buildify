# impl-notes — T-23.016

**Task**: Run Alembic migration `pg_module_lifecycle_columns`  
**Agent**: C2 Backend Developer  
**Date**: 2026-06-25  
**Status**: DONE

---

## Summary

Migration `pg_module_lifecycle_columns` adds three columns to the `modules` table:

| Column | Type | Nullable | Default |
|---|---|---|---|
| `install_status` | VARCHAR(30) | NOT NULL | `ready` |
| `install_error_message` | TEXT | YES | NULL |
| `visibility` | VARCHAR(20) | NOT NULL | `all_tenants` |

Also creates:
- `ix_modules_install_status` index
- `ix_modules_visibility` index
- `ck_modules_install_status` CHECK constraint (values: `in_progress`, `ready`, `failed`, `deactivation_pending`)
- `ck_modules_visibility` CHECK constraint (values: `all_tenants`, `whitelist`, `hidden`)

---

## Findings

Both the migration file and the SQLAlchemy model were already in place when this task was executed:

- **Migration file**: `backend/app/alembic/versions/postgresql/pg_module_lifecycle_columns.py` — existed and is correct
- **Model**: `backend/app/models/nocode_module.py` (Module class) — already has the three columns and both CheckConstraint entries in `__table_args__`
- **`module_registry.py`**: backward-compat shim that re-exports `Module as ModuleRegistry` — no changes needed

The migration is part of the chain:  
pg_week3_field_enhancements -> pg_module_lifecycle_columns -> pg_merge_lifecycle_main -> pg_tenant_module_databases -> ... -> ee55ff66aa77 -> normalize_tenant_codes (current head)

---

## Migration Verification

**Forward migration**: Confirmed via DB inspection — all three columns, both indexes, and both CHECK constraints exist in the `modules` table.

```
column_name            | data_type         | is_nullable | column_default
install_error_message  | text              | YES         |
install_status         | character varying | NO          | 'ready'
visibility             | character varying | NO          | 'all_tenants'

ix_modules_install_status  (index)
ix_modules_visibility      (index)

ck_modules_install_status  (check constraint)
ck_modules_visibility      (check constraint)
```

**Backward migration**: Verified via `alembic downgrade pg_week3_field_enhancements`. The `pg_module_lifecycle_columns` downgrade step ran cleanly (drops indexes, constraints, columns in correct order). The full downgrade chain was rolled back at an unrelated migration (`pg_r5_report_designer_columns` fails due to NOT NULL violation in existing `report_definitions` rows — pre-existing data issue, unrelated to this task). Alembic's transactional DDL restored the DB to `normalize_tenant_codes` (head).

---

## Notes for T-23.017

T-23.017 (update the SQLAlchemy model) is also effectively already complete — the `Module` model in `nocode_module.py` already has all three columns and both CheckConstraints. The assignee should verify and mark DONE.

---

## Files

- `backend/app/alembic/versions/postgresql/pg_module_lifecycle_columns.py` — migration (pre-existing, verified correct)
- `backend/app/models/nocode_module.py` — Module model with all three columns (pre-existing, verified correct)
- `backend/app/models/module_registry.py` — shim re-export, no change needed
