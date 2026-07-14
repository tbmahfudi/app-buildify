"""merge username-login and tenant_module_db-constraint heads

Resolves the two divergent postgres heads so `alembic upgrade head` (run on
startup) converges on a single head again:
  - pg_add_user_username_login          (username/password login fields)
  - pg_tenant_module_db_constraints     (Epic 22.4.1 FK/CHECK constraints)

No schema changes — merge only.

Revision ID: pg_merge_username_tmd
Revises: pg_add_user_username_login, pg_tenant_module_db_constraints
Create Date: 2026-07-10

Note: revision id kept <= 32 chars so it fits alembic_version.version_num
(default varchar(32)); the original 37-char id broke fresh-DB upgrades (GH#678).
"""

revision = 'pg_merge_username_tmd'
down_revision = ('pg_add_user_username_login', 'pg_tenant_module_db_constraints')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
