"""Add icon color columns to menu_items

Revision ID: add_menu_icon_colors
Revises: pg_nocode_module_system
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_menu_icon_colors'
down_revision = 'pg_nocode_module_system'
branch_labels = None
depends_on = None


def upgrade():
    """Add icon_color_primary and icon_color_secondary columns to menu_items table"""

    # Add icon color columns
    op.add_column('menu_items', sa.Column('icon_color_primary', sa.String(length=20), nullable=True))
    op.add_column('menu_items', sa.Column('icon_color_secondary', sa.String(length=20), nullable=True))


def downgrade():
    """Remove icon color columns from menu_items table"""

    # Remove icon color columns
    op.drop_column('menu_items', 'icon_color_secondary')
    op.drop_column('menu_items', 'icon_color_primary')
