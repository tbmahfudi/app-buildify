"""Add title, data_source, and columns columns to report_definitions for designer format

Revision ID: pg_r5_report_designer_columns
Revises: pg_week3_field_enhancements
Create Date: 2026-03-08 00:00:00.000000

Adds columns to support the visual report designer frontend format:
- title: display title (distinct from internal name)
- data_source: full data source config (entities, joins) from designer
- columns: selected columns list from the drag-drop column designer
Allows base_entity to be nullable (derived from data_source on save).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'pg_r5_report_designer_columns'
down_revision = 'pg_week3_field_enhancements'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add designer columns to report_definitions table."""
    # Add title column (display title, separate from name)
    op.add_column('report_definitions',
        sa.Column('title', sa.String(255), nullable=True)
    )

    # Add data_source column (full data source config from designer)
    op.add_column('report_definitions',
        sa.Column('data_source', JSONB, nullable=True)
    )

    # Add columns column (selected columns from drag-drop designer)
    op.add_column('report_definitions',
        sa.Column('columns', JSONB, nullable=True)
    )

    # Add chart_config column (chart configuration from visual designer)
    op.add_column('report_definitions',
        sa.Column('chart_config', JSONB, nullable=True)
    )

    # Make base_entity nullable (can be derived from data_source)
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
