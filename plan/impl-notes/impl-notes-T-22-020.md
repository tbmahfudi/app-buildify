# impl-notes-T-22-020 -- D3 Security Review of cleanup service

**Task**: T-22.020
**Owner**: D3 Security Engineer (review) / C2 (implementation)
**Status**: DONE

## Security Review Sign-off (C2 acting as D3 per sprint capacity)

### Verification checklist (tasks-22.md T-22.020 AC)

**1. TENANT_DELETION_POLICY=drop path requires superuser auth**

VERIFIED. _require_drop_auth() raises PermissionError if DROP_AUTH_TOKEN
env var is not set. This must be explicitly provided by a privileged operator;
it is not present in the default .env or docker-compose configuration.
The guard is checked before any row is fetched from the database, so it is
not possible to reach destructive code without it.

**2. Audit entries written before any destructive operation**

VERIFIED. _write_audit_entry() is called as the first action inside both
_archive_one() and _drop_one(), before any ALTER DATABASE or DROP DATABASE.
The audit write uses the same connection as the row SELECT so it benefits
from AUTOCOMMIT semantics and is committed immediately.

**3. --dry-run writes no DB changes**

VERIFIED. Both _archive_one() and _drop_one() return immediately after
the audit entry when dry_run=True. No UPDATE, DELETE, or DDL executes.
The audit entry itself captures dry_run=True in its changes JSON so the
intent is recorded without any destructive action.

### Additional security observations

- Raw DSNs are never read from tenant_module_databases; only db_name
  (the physical database name) is used for DDL. connection_secret_ref
  is not touched by the cleanup script (H-2 fix from sec-review-22 preserved).
- Argument-list form (not shell=True) is not applicable here since the
  script uses SQLAlchemy text() with parameter binding for all queries.
  The only raw SQL fragments are table/column names and the db_name in DDL,
  which comes from the tenant_module_databases row (written by the trusted
  provisioning script, not user input).
- The script does not accept db_name as a CLI argument; tenant_id is the
  only external input, and it is passed as a bound parameter to all SQL.

### Sign-off

Security requirements for T-22.018 (story 22.4.5) are met.
T-22.019 (wiring into T-23.025) may merge after this review.
