"""Add module_id to workflow, automation, lookup, report, and dashboard tables

Revision ID: my_add_module_id_components
Revises: add_module_id_to_entities
Create Date: 2026-02-18

"""
from alembic import op
import sqlalchemy as sa
from app.models.base import GUID


# revision identifiers, used by Alembic.
revision = 'my_add_module_id_components'
down_revision = 'add_module_id_to_entities'
branch_labels = None
depends_on = None

# Tables that need module_id added
TABLES = [
    'workflow_definitions',
    'automation_rules',
    'lookup_configurations',
    'report_definitions',
    'dashboards',
]


def upgrade():
    """Add module_id column to component tables"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    for table_name in TABLES:
        columns = [col['name'] for col in inspector.get_columns(table_name)]

        if 'module_id' not in columns:
            op.add_column(table_name, sa.Column('module_id', GUID(), nullable=True))

            op.create_foreign_key(
                f'fk_{table_name}_module_id',
                table_name,
                'modules',
                ['module_id'],
                ['id']
            )

            op.create_index(
                f'ix_{table_name}_module_id',
                table_name,
                ['module_id'],
                unique=False
            )


def downgrade():
    """Remove module_id column from component tables"""
    for table_name in reversed(TABLES):
        op.drop_index(f'ix_{table_name}_module_id', table_name=table_name)
        op.drop_constraint(f'fk_{table_name}_module_id', table_name, type_='foreignkey')
        op.drop_column(table_name, 'module_id')
