"""Add module_id to webhook_configs table

Revision ID: my_add_module_id_webhooks
Revises: my_add_module_id_components
Create Date: 2026-02-21

"""
from alembic import op
import sqlalchemy as sa
from app.models.base import GUID


# revision identifiers, used by Alembic.
revision = 'my_add_module_id_webhooks'
down_revision = 'my_add_module_id_components'
branch_labels = None
depends_on = None


def upgrade():
    """Add module_id column to webhook_configs table"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    columns = [col['name'] for col in inspector.get_columns('webhook_configs')]

    if 'module_id' not in columns:
        op.add_column('webhook_configs', sa.Column('module_id', GUID(), nullable=True))

        op.create_foreign_key(
            'fk_webhook_configs_module_id',
            'webhook_configs',
            'modules',
            ['module_id'],
            ['id']
        )

        op.create_index(
            'ix_webhook_configs_module_id',
            'webhook_configs',
            ['module_id'],
            unique=False
        )


def downgrade():
    """Remove module_id column from webhook_configs table"""
    op.drop_index('ix_webhook_configs_module_id', table_name='webhook_configs')
    op.drop_constraint('fk_webhook_configs_module_id', 'webhook_configs', type_='foreignkey')
    op.drop_column('webhook_configs', 'module_id')
