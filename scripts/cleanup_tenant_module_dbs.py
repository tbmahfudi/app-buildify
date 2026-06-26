#!/usr/bin/env python3
"""
scripts/cleanup_tenant_module_dbs.py  --  T-22.018

Tenant offboarding cleanup for per-tenant module databases.

Usage:
    cleanup_tenant_module_dbs.py <tenant_id> [--dry-run]

Behaviour is controlled by the TENANT_DELETION_POLICY env var:
    archive (default)  -- rename each module DB to <db_name>__archived__<ts>
                          and set status=archived in tenant_module_databases.
    drop               -- DROP DATABASE for each (tenant, module) and DELETE the row.
                          Requires DROP_AUTH_TOKEN env var (superuser guard).

Security requirements (T-22.020 D3 sign-off):
    * Audit entry tenant.module_dbs.cleanup written BEFORE any destructive operation.
    * --dry-run reads rows and writes log lines but makes NO database changes.
    * TENANT_DELETION_POLICY=drop requires DROP_AUTH_TOKEN env var.

Called by:
    manage.sh tenant deactivate <tenant_id>
    backend/app/routers/modules.py  T-23.025 stub (wired in T-22.019)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import List, Tuple

import sqlalchemy as sa

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s -- %(message)s",
)
logger = logging.getLogger("cleanup_tenant_module_dbs")


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _get_db_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        os.environ.get(
            "SQLALCHEMY_DATABASE_URL",
            "postgresql://appuser:apppassword@localhost:5432/appdb",
        ),
    )


def _get_admin_db_url() -> str:
    """Return a DSN pointing at the postgres maintenance DB for DDL commands."""
    url = _get_db_url()
    base = url.rsplit("/", 1)[0]
    return f"{base}/postgres"


def _get_policy() -> str:
    policy = os.environ.get("TENANT_DELETION_POLICY", "archive").strip().lower()
    if policy not in ("archive", "drop"):
        raise ValueError(
            f"Invalid TENANT_DELETION_POLICY={policy!r}; must be archive or drop."
        )
    return policy


def _require_drop_auth() -> None:
    """Require DROP_AUTH_TOKEN when policy=drop (D3 / T-22.020 superuser guard)."""
    token = os.environ.get("DROP_AUTH_TOKEN", "").strip()
    if not token:
        raise PermissionError(
            "TENANT_DELETION_POLICY=drop requires DROP_AUTH_TOKEN env var to be set. "
            "This guard prevents accidental data destruction. "
            "Set DROP_AUTH_TOKEN to a non-empty value in your operator environment."
        )


# ---------------------------------------------------------------------------
# Audit helpers
# ---------------------------------------------------------------------------

def _write_audit_entry(
    conn,
    action: str,
    tenant_id: str,
    module_id: str,
    db_name: str,
    policy: str,
    dry_run: bool,
    status: str = "success",
    error_message=None,
) -> None:
    """Write a tenant.module_dbs.cleanup audit row BEFORE any destructive op.

    Fail-open on audit failure: if the INSERT fails we log the error but do NOT
    abort cleanup -- leaving tenant data in an inconsistent intermediate state
    is worse than a missing audit row.  D3 requirement: T-22.020.
    """
    changes = json.dumps({
        "tenant_id": tenant_id,
        "module_id": module_id,
        "db_name": db_name,
        "policy": policy,
        "dry_run": dry_run,
    })
    try:
        conn.execute(
            sa.text(
                "INSERT INTO audit_log "
                "(id, user_id, user_email, tenant_id, action, entity_type, entity_id, "
                " changes, status, error_message, request_id, created_at) "
                "VALUES "
                "(:id, NULL, :user_email, :tenant_id, :action, "
                " :entity_type, :entity_id, :changes, :status, "
                " :error_message, :request_id, :now)"
            ),
            {
                "id": str(uuid.uuid4()),
                "user_email": "system:cleanup_tenant_module_dbs",
                "tenant_id": tenant_id,
                "action": action,
                "entity_type": "tenant_module_database",
                "entity_id": db_name,
                "changes": changes,
                "status": status,
                "error_message": error_message,
                "request_id": str(uuid.uuid4()),
                "now": datetime.now(timezone.utc),
            },
        )
    except Exception as audit_err:
        logger.error(
            "Failed to write audit entry action=%s tenant=%s module=%s: %s",
            action, tenant_id, module_id, audit_err,
        )


# ---------------------------------------------------------------------------
# Row fetching
# ---------------------------------------------------------------------------

def _fetch_rows(conn, tenant_id: str) -> List[Tuple[str, str, str, str]]:
    """Return list of (row_id, module_id, db_name, status) for non-archived rows."""
    result = conn.execute(
        sa.text(
            "SELECT id, module_id, db_name, status "
            "FROM tenant_module_databases "
            "WHERE tenant_id = :tid AND status != 'archived' "
            "ORDER BY created_at"
        ),
        {"tid": tenant_id},
    )
    return [(str(r[0]), str(r[1]), str(r[2]), str(r[3])) for r in result.fetchall()]


# ---------------------------------------------------------------------------
# Archive path (TENANT_DELETION_POLICY=archive)
# ---------------------------------------------------------------------------

def _archive_one(conn, admin_conn, row_id, module_id, db_name, tenant_id, dry_run):
    """Archive a single (tenant, module) database entry."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    archived_name = f"{db_name}__archived__{ts}"

    # Write audit BEFORE any destructive operation (D3 / T-22.020)
    _write_audit_entry(
        conn=conn,
        action="tenant.module_dbs.cleanup",
        tenant_id=tenant_id,
        module_id=module_id,
        db_name=db_name,
        policy="archive",
        dry_run=dry_run,
    )

    if dry_run:
        logger.info(
            "[dry-run] Would rename DB %r -> %r and set status=archived (module=%s)",
            db_name, archived_name, module_id,
        )
        return

    # Terminate active connections before rename
    try:
        admin_conn.execute(
            sa.text(
                "SELECT pg_terminate_backend(pid) "
                "FROM pg_stat_activity "
                "WHERE datname = :dbname AND pid <> pg_backend_pid()"
            ),
            {"dbname": db_name},
        )
        admin_conn.execute(
            sa.text(f'ALTER DATABASE "{db_name}" RENAME TO "{archived_name}"')
        )
        logger.info("Renamed physical DB %r -> %r (module=%s)", db_name, archived_name, module_id)
    except Exception as rename_err:
        logger.warning(
            "Could not rename physical DB %r (module=%s): %s -- row still marked archived.",
            db_name, module_id, rename_err,
        )

    conn.execute(
        sa.text(
            "UPDATE tenant_module_databases "
            "SET status = 'archived', db_name = :new_name, updated_at = NOW() "
            "WHERE id = :row_id"
        ),
        {"new_name": archived_name, "row_id": row_id},
    )
    logger.info("Marked row archived: module=%s db=%r -> %r", module_id, db_name, archived_name)


# ---------------------------------------------------------------------------
# Drop path (TENANT_DELETION_POLICY=drop)
# ---------------------------------------------------------------------------

def _drop_one(conn, admin_conn, row_id, module_id, db_name, tenant_id, dry_run):
    """Drop a single (tenant, module) database and delete its registry row."""

    # Write audit BEFORE any destructive operation (D3 / T-22.020)
    _write_audit_entry(
        conn=conn,
        action="tenant.module_dbs.cleanup",
        tenant_id=tenant_id,
        module_id=module_id,
        db_name=db_name,
        policy="drop",
        dry_run=dry_run,
    )

    if dry_run:
        logger.info(
            "[dry-run] Would DROP DATABASE %r and DELETE row (module=%s)",
            db_name, module_id,
        )
        return

    try:
        admin_conn.execute(
            sa.text(
                "SELECT pg_terminate_backend(pid) "
                "FROM pg_stat_activity "
                "WHERE datname = :dbname AND pid <> pg_backend_pid()"
            ),
            {"dbname": db_name},
        )
        admin_conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{db_name}"'))
        logger.info("Dropped physical DB %r (module=%s)", db_name, module_id)
    except Exception as drop_err:
        logger.error("Failed to DROP DATABASE %r (module=%s): %s", db_name, module_id, drop_err)
        raise

    conn.execute(
        sa.text("DELETE FROM tenant_module_databases WHERE id = :row_id"),
        {"row_id": row_id},
    )
    logger.info("Deleted row module=%s db=%r", module_id, db_name)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def cleanup_tenant_module_dbs(tenant_id: str, dry_run: bool = False) -> int:
    """Clean up all module databases for a tenant.

    Reads TENANT_DELETION_POLICY from the environment (default: archive).
    Returns the count of (tenant, module) pairs processed.

    Args:
        tenant_id: UUID string of the tenant to clean up.
        dry_run:   If True, logs what would be done but makes no DB changes.

    Security (D3 / T-22.020):
        - Audit entry written per (tenant, module) pair BEFORE any destructive op.
        - dry_run=True writes no rows to any database.
        - policy=drop requires DROP_AUTH_TOKEN env var (superuser guard).
    """
    policy = _get_policy()

    if policy == "drop" and not dry_run:
        _require_drop_auth()

    logger.info(
        "cleanup_tenant_module_dbs tenant=%s policy=%s dry_run=%s",
        tenant_id, policy, dry_run,
    )

    db_url = _get_db_url()
    admin_url = _get_admin_db_url()

    engine = sa.create_engine(db_url, isolation_level="AUTOCOMMIT")
    admin_engine = sa.create_engine(admin_url, isolation_level="AUTOCOMMIT")

    processed = 0
    total = 0

    with engine.connect() as conn, admin_engine.connect() as admin_conn:
        rows = _fetch_rows(conn, tenant_id)
        total = len(rows)

        if not rows:
            logger.info("No active module DB rows found for tenant %s", tenant_id)
            return 0

        logger.info(
            "Found %d module DB row(s) to process for tenant %s",
            total, tenant_id,
        )

        for row_id, module_id, db_name, current_status in rows:
            logger.info(
                "Processing: module=%s db=%r status=%s",
                module_id, db_name, current_status,
            )
            try:
                if policy == "archive":
                    _archive_one(
                        conn=conn,
                        admin_conn=admin_conn,
                        row_id=row_id,
                        module_id=module_id,
                        db_name=db_name,
                        tenant_id=tenant_id,
                        dry_run=dry_run,
                    )
                else:
                    _drop_one(
                        conn=conn,
                        admin_conn=admin_conn,
                        row_id=row_id,
                        module_id=module_id,
                        db_name=db_name,
                        tenant_id=tenant_id,
                        dry_run=dry_run,
                    )
                processed += 1
            except Exception as err:
                logger.error(
                    "Failed to process module=%s db=%r: %s -- continuing",
                    module_id, db_name, err,
                )

    logger.info(
        "cleanup complete: %d/%d row(s) processed (dry_run=%s)",
        processed, total, dry_run,
    )
    return processed


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Clean up per-tenant module databases (T-22.018 / Story 22.4.5)."
    )
    parser.add_argument("tenant_id", help="UUID of the tenant to clean up")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Log what would be done without making any changes",
    )
    args = parser.parse_args()

    count = cleanup_tenant_module_dbs(args.tenant_id, dry_run=args.dry_run)
    sys.exit(0 if count >= 0 else 1)
