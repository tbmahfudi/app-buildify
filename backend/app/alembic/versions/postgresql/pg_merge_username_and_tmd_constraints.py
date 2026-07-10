"""merge username-login and tenant_module_db-constraint heads

Resolves the two divergent postgres heads so `alembic upgrade head` (run on
startup) converges on a single head again:
  - pg_add_user_username_login          (username/password login fields)
  - pg_tenant_module_db_constraints     (Epic 22.4.1 FK/CHECK constraints)

No schema changes — merge only.

Revision ID: pg_merge_username_and_tmd_constraints
Revises: pg_add_user_username_login, pg_tenant_module_db_constraints
Create Date: 2026-07-10
"""
from alembic import op


revision = 'pg_merge_username_and_tmd_constraints'
down_revision = ('pg_add_user_username_login', 'pg_tenant_module_db_constraints')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
