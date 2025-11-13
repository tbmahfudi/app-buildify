"""Create menu_items table for backend-driven RBAC menu system

Revision ID: pg_create_menu_items
Revises: pg_add_department_fields
Create Date: 2025-11-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'pg_create_menu_items'
down_revision = 'pg_add_department_fields'
branch_labels = None
depends_on = None


def upgrade():
    """Create menu_items table with RBAC support."""

    # Create menu_items table
    op.create_table(
        'menu_items',

        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Unique identifier
        sa.Column('code', sa.String(100), nullable=False, unique=True, index=True),

        # Multi-tenancy
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),

        # Hierarchical structure
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('order', sa.Integer(), nullable=False, default=0, index=True),

        # Display properties
        sa.Column('title', sa.String(100), nullable=False),
        sa.Column('icon', sa.String(100), nullable=True),
        sa.Column('route', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),

        # RBAC Control
        sa.Column('permission', sa.String(200), nullable=True, index=True),
        sa.Column('required_roles', postgresql.JSONB(), nullable=True),

        # Behavior
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, index=True),
        sa.Column('is_visible', sa.Boolean(), nullable=False, default=True, index=True),
        sa.Column('target', sa.String(50), nullable=False, default='_self'),

        # Module Integration
        sa.Column('module_code', sa.String(100), nullable=True, index=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, default=True),

        # Extensible metadata (extra_data to avoid DB keyword conflicts)
        sa.Column('extra_data', postgresql.JSONB(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.text('now()')),
    )

    # Create foreign key constraints
    op.create_foreign_key(
        'fk_menu_items_tenant_id',
        'menu_items', 'tenants',
        ['tenant_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_menu_items_parent_id',
        'menu_items', 'menu_items',
        ['parent_id'], ['id'],
        ondelete='CASCADE'
    )

    # Create composite indexes for performance
    op.create_index(
        'ix_menu_tenant_active',
        'menu_items',
        ['tenant_id', 'is_active', 'is_visible']
    )

    op.create_index(
        'ix_menu_parent_order',
        'menu_items',
        ['parent_id', 'order']
    )

    op.create_index(
        'ix_menu_module',
        'menu_items',
        ['module_code']
    )


def downgrade():
    """Drop menu_items table."""
    op.drop_index('ix_menu_module', table_name='menu_items')
    op.drop_index('ix_menu_parent_order', table_name='menu_items')
    op.drop_index('ix_menu_tenant_active', table_name='menu_items')
    op.drop_constraint('fk_menu_items_parent_id', 'menu_items', type_='foreignkey')
    op.drop_constraint('fk_menu_items_tenant_id', 'menu_items', type_='foreignkey')
    op.drop_table('menu_items')
