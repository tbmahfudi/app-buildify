"""Create module system tables (MySQL)"""
from alembic import op
import sqlalchemy as sa

revision = "mysql_m1n2o3p4q5r6"
down_revision = "mysql_d7e8f9g0h1i2"  # Update this to the latest MySQL migration
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
        sa.Column('tags', sa.JSON, nullable=True),
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
        sa.Column('manifest', sa.JSON, nullable=False),
        sa.Column('configuration', sa.JSON, nullable=True),

        # Dependencies
        sa.Column('dependencies', sa.JSON, nullable=True),

        # Subscription requirements
        sa.Column('subscription_tier', sa.String(length=50), nullable=True),
        sa.Column('pricing_model', sa.String(length=50), nullable=True),

        # API information
        sa.Column('api_prefix', sa.String(length=100), nullable=True),

        # Database information
        sa.Column('has_migrations', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('database_tables', sa.JSON, nullable=True),

        # Status tracking
        sa.Column('status', sa.String(length=50), nullable=False, server_default='available'),

        # Support
        sa.Column('homepage', sa.String(length=500), nullable=True),
        sa.Column('repository', sa.String(length=500), nullable=True),
        sa.Column('support_email', sa.String(length=255), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now()),
    )

    # Create indexes for module_registry
    op.create_index('ix_module_registry_name', 'module_registry', ['name'])
    op.create_index('ix_module_registry_category', 'module_registry', ['category'])
    op.create_index('ix_module_registry_is_installed', 'module_registry', ['is_installed'])

    # Create foreign key for installed_by_user_id
    op.create_foreign_key(
        'fk_module_registry_installed_by_user',
        'module_registry', 'users',
        ['installed_by_user_id'], ['id']
    )

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
        sa.Column('configuration', sa.JSON, nullable=True),

        # Activation tracking
        sa.Column('enabled_at', sa.DateTime(), nullable=True),
        sa.Column('enabled_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('disabled_at', sa.DateTime(), nullable=True),
        sa.Column('disabled_by_user_id', sa.String(length=36), nullable=True),

        # Usage tracking
        sa.Column('usage_count', sa.JSON, nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now()),
    )

    # Create indexes for tenant_modules
    op.create_index('ix_tenant_modules_tenant_id', 'tenant_modules', ['tenant_id'])
    op.create_index('ix_tenant_modules_module_id', 'tenant_modules', ['module_id'])
    op.create_index('ix_tenant_modules_is_enabled', 'tenant_modules', ['is_enabled'])

    # Create foreign keys for tenant_modules
    op.create_foreign_key(
        'fk_tenant_modules_tenant',
        'tenant_modules', 'tenants',
        ['tenant_id'], ['id']
    )

    op.create_foreign_key(
        'fk_tenant_modules_module',
        'tenant_modules', 'module_registry',
        ['module_id'], ['id']
    )

    op.create_foreign_key(
        'fk_tenant_modules_enabled_by_user',
        'tenant_modules', 'users',
        ['enabled_by_user_id'], ['id']
    )

    op.create_foreign_key(
        'fk_tenant_modules_disabled_by_user',
        'tenant_modules', 'users',
        ['disabled_by_user_id'], ['id']
    )


def downgrade():
    # Drop tenant_modules table
    op.drop_table('tenant_modules')

    # Drop module_registry table
    op.drop_table('module_registry')
