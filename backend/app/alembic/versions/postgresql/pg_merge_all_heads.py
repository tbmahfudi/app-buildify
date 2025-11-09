"""merge all migration heads

Revision ID: pg_merge_all_heads
Revises: pg_fix_dept_constraint, pg_add_audit_org_fields, pg_merge_heads
Create Date: 2025-11-06 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'pg_merge_all_heads'
down_revision = ('pg_fix_dept_constraint', 'pg_add_audit_org_fields', 'pg_merge_heads')
branch_labels = None
depends_on = None


def upgrade():
    """
    This is a merge migration that combines multiple migration branches.
    No actual schema changes are needed - this just resolves the multiple heads issue.
    """
    pass


def downgrade():
    """
    No downgrade needed for merge migration.
    """
    pass
