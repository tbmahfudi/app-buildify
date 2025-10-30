"""Create module system tables (SQLite)"""
from alembic import op
import sqlalchemy as sa

revision = "sqlite_m1n2o3p4q5r6"
down_revision = "sqlite_e8f9g0h1i2j3"  # Update this to the latest SQLite migration
branch_labels = None
depends_on = None

def upgrade():
    # Create module_registry table
    op.create_table(
        'module_registry',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=100), unique=True, nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Module metadata
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),  # JSON stored as TEXT in SQLite
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('license', sa.String(length=100), nullable=True),

        # Status
        sa.Column('is_installed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_core', sa.Boolean(), nullable=False, server_default='0'),

        # Installation tracking
        sa.Column('installed_at', sa.DateTime(), nullable=True),
        sa.Column('installed_by_user_id', sa.String(length=36), nullable=True),

        # Configuration
        sa.Column('manifest', sa.Text(), nullable=False),  # JSON stored as TEXT in SQLite
        sa.Column('configuration', sa.Text(), nullable=True),  # JSON stored as TEXT

        # Dependencies
        sa.Column('dependencies', sa.Text(), nullable=True),  # JSON stored as TEXT

        # Subscription requirements
        sa.Column('subscription_tier', sa.String(length=50), nullable=True),
        sa.Column('pricing_model', sa.String(length=50), nullable=True),

        # API information
        sa.Column('api_prefix', sa.String(length=100), nullable=True),

        # Database information
        sa.Column('has_migrations', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('database_tables', sa.Text(), nullable=True),  # JSON stored as TEXT

        # Status tracking
        sa.Column('status', sa.String(length=50), nullable=False, server_default='available'),

        # Support
        sa.Column('homepage', sa.String(length=500), nullable=True),
        sa.Column('repository', sa.String(length=500), nullable=True),
        sa.Column('support_email', sa.String(length=255), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime()),
    )

    # Create indexes for module_registry
    op.create_index('ix_module_registry_name', 'module_registry', ['name'])
    op.create_index('ix_module_registry_category', 'module_registry', ['category'])
    op.create_index('ix_module_registry_is_installed', 'module_registry', ['is_installed'])

    # Create tenant_modules table
    op.create_table(
        'tenant_modules',
        sa.Column('id', sa.String(length=36), primary_key=True),

        # Foreign keys
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('module_id', sa.String(length=36), nullable=False),

        # Status
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_configured', sa.Boolean(), nullable=False, server_default='0'),

        # Tenant-specific configuration
        sa.Column('configuration', sa.Text(), nullable=True),  # JSON stored as TEXT

        # Activation tracking
        sa.Column('enabled_at', sa.DateTime(), nullable=True),
        sa.Column('enabled_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('disabled_at', sa.DateTime(), nullable=True),
        sa.Column('disabled_by_user_id', sa.String(length=36), nullable=True),

        # Usage tracking
        sa.Column('usage_count', sa.Text(), nullable=True),  # JSON stored as TEXT
        sa.Column('last_used_at', sa.DateTime(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime()),

        # Foreign key constraints
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_tenant_modules_tenant'),
        sa.ForeignKeyConstraint(['module_id'], ['module_registry.id'], name='fk_tenant_modules_module'),
        sa.ForeignKeyConstraint(['enabled_by_user_id'], ['users.id'], name='fk_tenant_modules_enabled_by_user'),
        sa.ForeignKeyConstraint(['disabled_by_user_id'], ['users.id'], name='fk_tenant_modules_disabled_by_user'),
    )

    # Create indexes for tenant_modules
    op.create_index('ix_tenant_modules_tenant_id', 'tenant_modules', ['tenant_id'])
    op.create_index('ix_tenant_modules_module_id', 'tenant_modules', ['module_id'])
    op.create_index('ix_tenant_modules_is_enabled', 'tenant_modules', ['is_enabled'])


def downgrade():
    # Drop tenant_modules table
    op.drop_table('tenant_modules')

    # Drop module_registry table
    op.drop_table('module_registry')
