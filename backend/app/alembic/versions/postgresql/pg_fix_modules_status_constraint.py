"""Add CHECK constraint to modules.status to enforce valid values

Revision ID: bb22cc33dd44
Revises: aa11bb22cc33
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa

revision = 'bb22cc33dd44'
down_revision = 'aa11bb22cc33'
branch_labels = None
depends_on = None


def upgrade():
    # Normalise any remaining non-standard values first
    op.execute("UPDATE modules SET status='available' WHERE status NOT IN ('draft','active','deprecated','archived','available','stable','beta')")
    op.create_check_constraint(
        'ck_modules_status',
        'modules',
        "status IN ('draft','active','deprecated','archived','available','stable','beta')"
    )


def downgrade():
    op.drop_constraint('ck_modules_status', 'modules', type_='check')
