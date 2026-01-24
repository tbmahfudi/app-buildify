"""Add Week 3-4 field enhancements: conditional visibility, dependencies, and i18n

Revision ID: pg_week3_field_enhancements
Revises: pg_lookup_enhancements
Create Date: 2026-01-24 00:00:00.000000

Adds columns to support:
- Conditional field visibility based on other field values
- Field dependencies for cascading dropdowns
- Multi-language support for labels, help text, and placeholders
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'pg_week3_field_enhancements'
down_revision = 'pg_lookup_enhancements'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add conditional visibility, field dependencies, and i18n columns to field_definitions table.
    """

    # Conditional Visibility
    # Stores rules for showing/hiding fields dynamically
    # Example: {"operator": "AND", "conditions": [{"field": "status", "operator": "equals", "value": "active"}]}
    op.add_column('field_definitions',
                  sa.Column('visibility_rules', JSONB, nullable=True))

    # Field Dependencies (Cascading Dropdowns)
    # Parent field that this field depends on
    op.add_column('field_definitions',
                  sa.Column('depends_on_field', sa.String(100), nullable=True))

    # Filter expression to apply when loading options
    # Example: "country_code = '{country}'"
    op.add_column('field_definitions',
                  sa.Column('filter_expression', sa.Text, nullable=True))

    # Multi-language Support (i18n)
    # Store translations for labels in JSONB format
    # Example: {"en": "Customer Name", "es": "Nombre del Cliente", "fr": "Nom du Client"}
    op.add_column('field_definitions',
                  sa.Column('label_i18n', JSONB, nullable=True))

    # Store translations for help text
    op.add_column('field_definitions',
                  sa.Column('help_text_i18n', JSONB, nullable=True))

    # Store translations for placeholders
    op.add_column('field_definitions',
                  sa.Column('placeholder_i18n', JSONB, nullable=True))


def downgrade() -> None:
    """
    Remove conditional visibility, field dependencies, and i18n columns from field_definitions table.
    """
    # Remove i18n columns
    op.drop_column('field_definitions', 'placeholder_i18n')
    op.drop_column('field_definitions', 'help_text_i18n')
    op.drop_column('field_definitions', 'label_i18n')

    # Remove dependency columns
    op.drop_column('field_definitions', 'filter_expression')
    op.drop_column('field_definitions', 'depends_on_field')

    # Remove visibility rules column
    op.drop_column('field_definitions', 'visibility_rules')
