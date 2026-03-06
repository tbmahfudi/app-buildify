"""consolidate entity_metadata into entity_definitions (MySQL)

Revision ID: my_consolidate_entity_metadata
Revises: my_add_module_id_components
Create Date: 2026-03-05 00:00:00.000000

Moves table_config, form_config, and permissions from the separate
entity_metadata table directly onto entity_definitions, then drops
entity_metadata.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'my_consolidate_entity_metadata'
down_revision = 'my_add_module_id_components'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add JSON columns to entity_definitions
    op.add_column('entity_definitions',
        sa.Column('table_config', sa.JSON, nullable=True)
    )
    op.add_column('entity_definitions',
        sa.Column('form_config', sa.JSON, nullable=True)
    )
    op.add_column('entity_definitions',
        sa.Column('permissions', sa.JSON, nullable=True)
    )

    # 2. Migrate data from entity_metadata into entity_definitions
    op.execute("""
        UPDATE entity_definitions ed
        INNER JOIN entity_metadata em ON ed.name = em.entity_name
        SET
            ed.table_config  = CAST(em.table_config AS JSON),
            ed.form_config   = CAST(em.form_config AS JSON),
            ed.permissions   = CAST(em.permissions AS JSON)
        WHERE em.is_active = 1
          AND em.table_config IS NOT NULL
    """)

    # 3. Drop entity_metadata table
    op.drop_table('entity_metadata')


def downgrade():
    op.create_table(
        'entity_metadata',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('entity_name', sa.String(100), unique=True, nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('table_config', sa.Text, nullable=True),
        sa.Column('form_config', sa.Text, nullable=True),
        sa.Column('permissions', sa.Text, nullable=True),
        sa.Column('version', sa.Integer, default=1, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_system', sa.Boolean, default=False, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('updated_by', sa.String(36), nullable=True),
    )

    op.execute("""
        INSERT INTO entity_metadata (
            id, entity_name, display_name, description, icon,
            table_config, form_config, permissions,
            version, is_active, is_system,
            created_at, updated_at, created_by, updated_by
        )
        SELECT
            UUID(),
            ed.name,
            ed.label,
            ed.description,
            ed.icon,
            CAST(ed.table_config AS CHAR),
            CAST(ed.form_config AS CHAR),
            CAST(ed.permissions AS CHAR),
            ed.version,
            ed.is_active,
            (ed.entity_type = 'system'),
            ed.created_at,
            ed.updated_at,
            ed.created_by,
            ed.updated_by
        FROM entity_definitions ed
        WHERE ed.table_config IS NOT NULL
          AND ed.is_deleted = 0
    """)

    op.drop_column('entity_definitions', 'permissions')
    op.drop_column('entity_definitions', 'form_config')
    op.drop_column('entity_definitions', 'table_config')
