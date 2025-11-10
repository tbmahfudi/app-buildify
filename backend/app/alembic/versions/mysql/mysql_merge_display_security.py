"""Merge display_name and security_policy migrations

Revision ID: mysql_merge_display_security
Revises: mysql_add_display_name, mysql_security_policy_system
Create Date: 2025-11-10 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'mysql_merge_display_security'
down_revision = ('mysql_add_display_name', 'mysql_security_policy_system')
branch_labels = None
depends_on = None


def upgrade():
    """
    This is a merge migration that combines the display_name and security_policy branches.
    No actual schema changes are needed - this just resolves the multiple heads issue.
    """
    pass


def downgrade():
    """
    No downgrade needed for merge migration.
    """
    pass
