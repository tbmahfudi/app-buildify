"""consolidate entity_metadata into entity_definitions

Revision ID: pg_consolidate_entity_metadata
Revises: pg_add_data_scope
Create Date: 2026-03-05 00:00:00.000000

Moves table_config, form_config, and permissions from the separate
entity_metadata table directly onto entity_definitions, then drops
entity_metadata. The other columns (display_name, description, icon,
is_active, version) already exist on entity_definitions (as label,
description, icon, is_active, version respectively).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'pg_consolidate_entity_metadata'
down_revision = 'pg_add_data_scope'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add new JSONB columns to entity_definitions
    op.add_column('entity_definitions',
        sa.Column('table_config', JSONB, nullable=True)
    )
    op.add_column('entity_definitions',
        sa.Column('form_config', JSONB, nullable=True)
    )
    op.add_column('entity_definitions',
        sa.Column('permissions', JSONB, nullable=True)
    )

    # 2. Migrate data from entity_metadata into entity_definitions
    #    Match on entity_definitions.name = entity_metadata.entity_name
    #    Only migrate from active metadata rows
    op.execute("""
        UPDATE entity_definitions ed
        SET
            table_config  = em.table_config::jsonb,
            form_config   = em.form_config::jsonb,
            permissions   = em.permissions::jsonb
        FROM entity_metadata em
        WHERE ed.name = em.entity_name
          AND em.is_active = true
          AND em.table_config IS NOT NULL
    """)

    # 3. Drop entity_metadata table
    op.drop_table('entity_metadata')


def downgrade():
    # Re-create entity_metadata table
    op.create_table(
        'entity_metadata',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('entity_name', sa.String(100), unique=True, nullable=False, index=True),
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

    # Restore data from entity_definitions back to entity_metadata
    op.execute("""
        INSERT INTO entity_metadata (
            id, entity_name, display_name, description, icon,
            table_config, form_config, permissions,
            version, is_active, is_system,
            created_at, updated_at, created_by, updated_by
        )
        SELECT
            gen_random_uuid()::text,
            ed.name,
            ed.label,
            ed.description,
            ed.icon,
            ed.table_config::text,
            ed.form_config::text,
            ed.permissions::text,
            ed.version,
            ed.is_active,
            (ed.entity_type = 'system'),
            ed.created_at,
            ed.updated_at,
            ed.created_by::text,
            ed.updated_by::text
        FROM entity_definitions ed
        WHERE ed.table_config IS NOT NULL
          AND ed.is_deleted = false
    """)

    # Remove the columns from entity_definitions
    op.drop_column('entity_definitions', 'permissions')
    op.drop_column('entity_definitions', 'form_config')
    op.drop_column('entity_definitions', 'table_config')
