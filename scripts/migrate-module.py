#!/usr/bin/env python3
"""
migrate-module.py {module_id}

Alembic fan-out migration: runs alembic upgrade heads on every per-tenant DB
registered for the given module_id in tenant_module_databases.

Story 22.4.4

TODO (production hardening):
  - Replace subprocess alembic call with programmatic alembic API to capture
    per-tenant logs cleanly.
  - Add --dry-run flag that prints the list of target DBs without migrating.
  - Add --tenant-id flag to migrate a single tenant in isolation.
  - Emit progress events to an audit log / observability sink.
  - Handle connection failures per tenant without aborting the whole fan-out
    (collect errors and surface a summary at the end).
"""
import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)


def get_tenant_dbs(module_id: str) -> list[dict]:
    """Fetch all active tenant_module_databases rows for this module."""
    try:
        import sqlalchemy as sa
        db_url = os.environ.get('DATABASE_URL', 'postgresql://appuser:apppassword@localhost:5432/appdb')
        engine = sa.create_engine(db_url)
        with engine.connect() as conn:
            rows = conn.execute(
                sa.text(
                    "SELECT tenant_id, db_name, connection_url, status "
                    "FROM tenant_module_databases "
                    "WHERE module_id = :mid AND status NOT IN ('archived', 'failed')"
                ),
                {"mid": module_id},
            ).fetchall()
        return [{"tenant_id": str(r[0]), "db_name": r[1], "connection_url": r[2], "status": r[3]}
                for r in rows]
    except Exception as exc:
        logger.error(f"Could not query tenant_module_databases: {exc}")
        return []


def run_migration_for_tenant(db: dict) -> bool:
    """Run alembic upgrade heads against one tenant DB. Returns True on success."""
    db_url = db.get("connection_url") or os.environ.get("DATABASE_URL", "")
    if not db_url:
        logger.warning(f"No connection_url for tenant {db['tenant_id']} — skipping")
        return False

    env = {**os.environ, "DATABASE_URL": db_url}
    result = subprocess.run(
        ["alembic", "upgrade", "heads"],
        env=env,
        capture_output=True,
        text=True,
        cwd=os.path.join(os.path.dirname(__file__), '..', 'backend'),
    )
    if result.returncode == 0:
        logger.info(f"[OK] tenant={db['tenant_id']} db={db['db_name']}")
        return True
    else:
        logger.error(f"[FAIL] tenant={db['tenant_id']}: {result.stderr[:500]}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: migrate-module.py <module_id>")
        sys.exit(1)

    module_id = sys.argv[1]
    logger.info(f"Fan-out migration for module: {module_id}")

    tenant_dbs = get_tenant_dbs(module_id)
    if not tenant_dbs:
        logger.info("No tenant DBs found — nothing to migrate.")
        return

    logger.info(f"Found {len(tenant_dbs)} tenant DB(s)")
    ok, fail = 0, 0
    for db in tenant_dbs:
        if run_migration_for_tenant(db):
            ok += 1
        else:
            fail += 1

    logger.info(f"Migration complete: {ok} OK, {fail} failed")
    if fail:
        sys.exit(1)


if __name__ == '__main__':
    main()
