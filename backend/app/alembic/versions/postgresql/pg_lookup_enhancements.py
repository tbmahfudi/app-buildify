"""Add lookup enhancement columns to field_definitions

Revision ID: pg_lookup_enhancements
Revises: pg_add_fk_constraint
Create Date: 2026-01-23 12:00:00.000000

Adds columns to support enhanced lookup/reference field functionality:
- Display templates for custom formatting
- Search field configuration
- Filter field for cascading lookups
- Quick-create capability
- Recent selections tracking
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'pg_lookup_enhancements'
down_revision = 'pg_add_fk_constraint'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add lookup enhancement columns to field_definitions table.
    """
    # Display template for formatting lookup dropdown items
    # Example: "{name} ({email})" or "{code} - {description}"
    op.add_column('field_definitions',
                  sa.Column('lookup_display_template', sa.Text, nullable=True))

    # Field to filter lookup results based on another field's value
    # Example: filter "State" by "Country"
    op.add_column('field_definitions',
                  sa.Column('lookup_filter_field', sa.String(100), nullable=True))

    # Array of field names to search in autocomplete
    # Example: ["name", "email", "code"]
    op.add_column('field_definitions',
                  sa.Column('lookup_search_fields', JSONB, nullable=True))

    # Allow quick-create of new records from lookup dropdown
    op.add_column('field_definitions',
                  sa.Column('lookup_allow_create', sa.Boolean, server_default='false'))

    # Number of recent selections to show
    op.add_column('field_definitions',
                  sa.Column('lookup_recent_count', sa.Integer, server_default='5'))


def downgrade() -> None:
    """
    Remove lookup enhancement columns from field_definitions table.
    """
    op.drop_column('field_definitions', 'lookup_recent_count')
    op.drop_column('field_definitions', 'lookup_allow_create')
    op.drop_column('field_definitions', 'lookup_search_fields')
    op.drop_column('field_definitions', 'lookup_filter_field')
    op.drop_column('field_definitions', 'lookup_display_template')
