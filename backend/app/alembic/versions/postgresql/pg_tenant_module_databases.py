"""tenant_module_databases table — Epic 22.4.1

Revision ID: pg_tenant_module_databases
Revises: pg_merge_lifecycle_main
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa

revision = 'pg_tenant_module_databases'
down_revision = 'pg_merge_lifecycle_main'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS tenant_module_databases (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            module_id UUID NOT NULL,
            db_name VARCHAR(255) NOT NULL,
            -- Store a secrets-manager reference, NOT the raw DSN
            -- Format: "vault:<path>" or "env:<VAR_NAME>" or "arn:aws:secretsmanager:..."
            connection_secret_ref TEXT,
            status VARCHAR(30) NOT NULL DEFAULT 'provisioning',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(tenant_id, module_id)
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_tenant_module_databases_tenant_id
            ON tenant_module_databases (tenant_id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_tenant_module_databases_module_id
            ON tenant_module_databases (module_id);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tenant_module_databases;")
