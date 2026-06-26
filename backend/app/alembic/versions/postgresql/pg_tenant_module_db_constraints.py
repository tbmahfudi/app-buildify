"""tenant_module_databases FK + CHECK constraints (TD-1 + TD-2) -- Epic 22.4.1

TD-1: add FK constraints tenant_id -> tenants.id and module_id -> modules.id
TD-2: add CHECK constraint on status column

Revision ID: pg_tenant_module_db_constraints
Revises: pg_tenant_module_databases
Create Date: 2026-06-26
"""
from alembic import op

revision = 'pg_tenant_module_db_constraints'
down_revision = 'pg_tenant_module_databases'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # TD-1: FK tenant_id -> tenants.id (CASCADE on tenant delete)
    op.execute("""
        ALTER TABLE tenant_module_databases
            ADD CONSTRAINT fk_tmd_tenant
            FOREIGN KEY (tenant_id)
            REFERENCES tenants(id)
            ON DELETE CASCADE;
    """)

    # TD-1: FK module_id -> modules.id (CASCADE on module delete)
    op.execute("""
        ALTER TABLE tenant_module_databases
            ADD CONSTRAINT fk_tmd_module
            FOREIGN KEY (module_id)
            REFERENCES modules(id)
            ON DELETE CASCADE;
    """)

    # TD-2: CHECK constraint on status -- must match lifecycle values in schema-22 §3.3
    op.execute("""
        ALTER TABLE tenant_module_databases
            ADD CONSTRAINT ck_tmd_status
            CHECK (status IN ('provisioning', 'ready', 'failed', 'archived'));
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE tenant_module_databases
            DROP CONSTRAINT IF EXISTS ck_tmd_status;
    """)
    op.execute("""
        ALTER TABLE tenant_module_databases
            DROP CONSTRAINT IF EXISTS fk_tmd_module;
    """)
    op.execute("""
        ALTER TABLE tenant_module_databases
            DROP CONSTRAINT IF EXISTS fk_tmd_tenant;
    """)
