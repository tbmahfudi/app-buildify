"""Add unique constraint for module_versions.is_current

Revision ID: ee55ff66aa77
Revises: dd44ee55ff66
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa

revision = 'ee55ff66aa77'
down_revision = 'dd44ee55ff66'
branch_labels = None
depends_on = None

def upgrade():
    # First ensure no duplicates exist
    op.execute("""
        UPDATE module_versions mv
        SET is_current = false
        WHERE is_current = true
          AND id NOT IN (
            SELECT DISTINCT ON (module_id) id
            FROM module_versions
            WHERE is_current = true
            ORDER BY module_id, version_number DESC NULLS LAST
          )
    """)
    op.create_index(
        'uq_module_versions_one_current',
        'module_versions',
        ['module_id'],
        unique=True,
        postgresql_where=sa.text('is_current = true')
    )

def downgrade():
    op.drop_index('uq_module_versions_one_current', table_name='module_versions')
