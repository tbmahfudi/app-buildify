"""Merge migration heads

Revision ID: pg_merge_heads
Revises: pg_add_branch_fields, pg_c5d6e7f8g9h0
Create Date: 2025-11-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'pg_merge_heads'
down_revision = ('pg_add_branch_fields', 'pg_c5d6e7f8g9h0')
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge migration - no changes needed
    pass


def downgrade():
    # This is a merge migration - no changes needed
    pass
