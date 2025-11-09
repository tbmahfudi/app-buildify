"""Add display_name to users table

Revision ID: pg_add_display_name
Revises: pg_merge_module_fk_dashboard
Create Date: 2025-11-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'pg_add_display_name'
down_revision = 'pg_merge_module_fk_dashboard'
branch_labels = None
depends_on = None


def upgrade():
    # Add display_name column to users table
    op.add_column('users', sa.Column('display_name', sa.String(length=50), nullable=True))


def downgrade():
    # Remove display_name column from users table
    op.drop_column('users', 'display_name')
