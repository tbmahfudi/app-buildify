"""Remove icon_color_secondary from menu_items

Revision ID: remove_menu_icon_secondary
Revises: add_menu_icon_colors
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_menu_icon_secondary'
down_revision = 'add_menu_icon_colors'
branch_labels = None
depends_on = None


def upgrade():
    """Remove icon_color_secondary column from menu_items table"""

    # Remove icon_color_secondary column
    op.drop_column('menu_items', 'icon_color_secondary')


def downgrade():
    """Re-add icon_color_secondary column to menu_items table"""

    # Add icon_color_secondary column back
    op.add_column('menu_items', sa.Column('icon_color_secondary', sa.String(length=20), nullable=True))
