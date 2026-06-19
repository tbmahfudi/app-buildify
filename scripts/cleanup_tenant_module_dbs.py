#!/usr/bin/env python3
"""
cleanup_tenant_module_dbs.py <tenant_id>

Marks all tenant_module_databases rows for a tenant as 'archived'.
Called by manage.sh tenant deactivate <tenant_id>.  Story 22.4.5.
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)


def cleanup_tenant_module_dbs(tenant_id: str) -> int:
    """Archive all module DB records for the tenant. Returns count of rows updated."""
    import sqlalchemy as sa
    db_url = os.environ.get('DATABASE_URL', 'postgresql://appuser:apppassword@localhost:5432/appdb')
    engine = sa.create_engine(db_url)
    with engine.begin() as conn:
        result = conn.execute(
            sa.text(
                "UPDATE tenant_module_databases "
                "SET status = 'archived', updated_at = NOW() "
                "WHERE tenant_id = :tid AND status != 'archived'"
            ),
            {"tid": tenant_id},
        )
        count = result.rowcount
    logger.info(f"Archived {count} module DB record(s) for tenant {tenant_id}")
    return count


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: cleanup_tenant_module_dbs.py <tenant_id>")
        sys.exit(1)
    tenant_id = sys.argv[1]
    cleanup_tenant_module_dbs(tenant_id)
