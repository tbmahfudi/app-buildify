"""Add title, data_source, and columns columns to report_definitions for designer format

Revision ID: my_r5_report_designer_columns
Revises: mysql_security_policy_system
Create Date: 2026-03-08 00:00:00.000000

Adds columns to support the visual report designer frontend format.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'my_r5_report_designer_columns'
down_revision = 'mysql_security_policy_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add designer columns to report_definitions table."""
    op.add_column('report_definitions',
        sa.Column('title', sa.String(255), nullable=True)
    )
    op.add_column('report_definitions',
        sa.Column('data_source', sa.JSON, nullable=True)
    )
    op.add_column('report_definitions',
        sa.Column('columns', sa.JSON, nullable=True)
    )
    op.add_column('report_definitions',
        sa.Column('chart_config', sa.JSON, nullable=True)
    )
    op.alter_column('report_definitions', 'base_entity',
        existing_type=sa.String(100),
        nullable=True
    )


def downgrade() -> None:
    """Remove designer columns from report_definitions table."""
    op.drop_column('report_definitions', 'chart_config')
    op.drop_column('report_definitions', 'columns')
    op.drop_column('report_definitions', 'data_source')
    op.drop_column('report_definitions', 'title')
    op.alter_column('report_definitions', 'base_entity',
        existing_type=sa.String(100),
        nullable=False
    )
