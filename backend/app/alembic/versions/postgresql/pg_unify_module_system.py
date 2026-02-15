"""Unify module system: merge module_registry, nocode_modules, tenant_modules

Revision ID: pg_unify_module_system
Revises: pg_module_extensions
Create Date: 2026-02-12 10:00:00.000000

Merges the dual module system into a single unified model:
- module_registry + nocode_modules -> modules
- tenant_modules -> module_activations
- Updates FKs in module_dependencies, module_versions, module_services, module_extensions
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision = 'pg_unify_module_system'
down_revision = 'pg_module_extensions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Merge module_registry and nocode_modules into unified 'modules' table,
    and tenant_modules into 'module_activations' table.
    """

    # ========================================================
    # Step 1: Create new unified 'modules' table
    # ========================================================
    op.create_table(
        'modules',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),

        # Module type
        sa.Column('module_type', sa.String(20), nullable=False, server_default='nocode', index=True),

        # Versioning
        sa.Column('version', sa.String(50), nullable=False, server_default='1.0.0'),
        sa.Column('major_version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('minor_version', sa.Integer, nullable=False, server_default='0'),
        sa.Column('patch_version', sa.Integer, nullable=False, server_default='0'),

        # Nocode table prefix
        sa.Column('table_prefix', sa.String(10), unique=True, nullable=True, index=True),

        # Metadata
        sa.Column('category', sa.String(50), index=True),
        sa.Column('tags', JSON),
        sa.Column('icon', sa.String(50)),
        sa.Column('color', sa.String(7)),
        sa.Column('author', sa.String(255)),
        sa.Column('license', sa.String(100)),

        # Status
        sa.Column('status', sa.String(50), nullable=False, server_default='draft', index=True),
        sa.Column('is_installed', sa.Boolean, nullable=False, server_default='false', index=True),
        sa.Column('is_core', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_template', sa.Boolean, server_default='false'),

        # Organization
        sa.Column('tenant_id', UUID(as_uuid=False), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True, index=True),

        # Installation tracking
        sa.Column('installed_at', sa.DateTime),
        sa.Column('installed_by_user_id', UUID(as_uuid=False), sa.ForeignKey('users.id', ondelete='SET NULL')),

        # Configuration & Manifest
        sa.Column('manifest', JSON),
        sa.Column('configuration', JSON),
        sa.Column('permissions', JSON),

        # Dependencies JSON
        sa.Column('dependencies_json', JSON),

        # Subscription / Marketplace
        sa.Column('subscription_tier', sa.String(50)),
        sa.Column('pricing_model', sa.String(50)),

        # API info
        sa.Column('api_prefix', sa.String(100)),

        # Database info
        sa.Column('has_migrations', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('database_tables', JSON),

        # Support
        sa.Column('homepage', sa.String(500)),
        sa.Column('repository', sa.String(500)),
        sa.Column('support_email', sa.String(255)),

        # Audit
        sa.Column('created_by', UUID(as_uuid=False), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_by', UUID(as_uuid=False), sa.ForeignKey('users.id')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('published_at', sa.DateTime(timezone=True)),
        sa.Column('published_by', UUID(as_uuid=False), sa.ForeignKey('users.id')),

        # Constraints
        sa.CheckConstraint("module_type IN ('code', 'nocode', 'hybrid')", name='valid_module_type'),
    )

    # ========================================================
    # Step 2: Migrate data from module_registry -> modules (as type='code')
    # ========================================================
    op.execute("""
        INSERT INTO modules (
            id, name, display_name, description,
            module_type, version, major_version, minor_version, patch_version,
            category, tags, author, license,
            status, is_installed, is_core,
            installed_at, installed_by_user_id,
            manifest, configuration, dependencies_json,
            subscription_tier, pricing_model, api_prefix,
            has_migrations, database_tables,
            homepage, repository, support_email,
            created_at, updated_at
        )
        SELECT
            id, name, display_name, description,
            'code', version, 1, 0, 0,
            category, tags, author, license,
            COALESCE(status, 'available'), is_installed, is_core,
            installed_at, installed_by_user_id,
            manifest, configuration, dependencies,
            subscription_tier, pricing_model, api_prefix,
            has_migrations, database_tables,
            homepage, repository, support_email,
            created_at, COALESCE(updated_at, created_at)
        FROM module_registry
    """)

    # ========================================================
    # Step 3: Migrate data from nocode_modules -> modules (as type='nocode')
    # Only migrate modules that don't conflict with already-migrated module_registry names
    # ========================================================
    op.execute("""
        INSERT INTO modules (
            id, name, display_name, description,
            module_type, version, major_version, minor_version, patch_version,
            table_prefix, category, tags, icon, color,
            status, is_core, is_template,
            tenant_id, configuration, permissions,
            created_by, created_at, updated_by, updated_at,
            published_at, published_by
        )
        SELECT
            nm.id, nm.name, nm.display_name, nm.description,
            'nocode', nm.version, nm.major_version, nm.minor_version, nm.patch_version,
            nm.table_prefix, nm.category, nm.tags, nm.icon, nm.color,
            nm.status, nm.is_core, nm.is_template,
            nm.tenant_id, nm.config, nm.permissions,
            nm.created_by, nm.created_at, nm.updated_by, nm.updated_at,
            nm.published_at, nm.published_by
        FROM nocode_modules nm
        WHERE nm.name NOT IN (SELECT name FROM module_registry)
    """)

    # ========================================================
    # Step 4: Create unified 'module_activations' table
    # ========================================================
    op.create_table(
        'module_activations',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('module_id', UUID(as_uuid=False), sa.ForeignKey('modules.id', ondelete='CASCADE'), nullable=False, index=True),

        # Organizational scope
        sa.Column('tenant_id', UUID(as_uuid=False), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('company_id', UUID(as_uuid=False), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('branch_id', UUID(as_uuid=False), sa.ForeignKey('branches.id', ondelete='CASCADE'), nullable=True),
        sa.Column('department_id', UUID(as_uuid=False), sa.ForeignKey('departments.id', ondelete='CASCADE'), nullable=True),

        # Status
        sa.Column('is_enabled', sa.Boolean, nullable=False, server_default='false', index=True),
        sa.Column('is_configured', sa.Boolean, nullable=False, server_default='false'),

        # Configuration
        sa.Column('configuration', JSON),
        sa.Column('enabled_features', JSON),
        sa.Column('disabled_features', JSON),

        # Tracking
        sa.Column('enabled_at', sa.DateTime),
        sa.Column('enabled_by_user_id', UUID(as_uuid=False), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('disabled_at', sa.DateTime),
        sa.Column('disabled_by_user_id', UUID(as_uuid=False), sa.ForeignKey('users.id', ondelete='SET NULL')),

        # Usage
        sa.Column('usage_count', JSON),
        sa.Column('last_used_at', sa.DateTime),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True)),

        # Constraints
        sa.UniqueConstraint('module_id', 'tenant_id', 'company_id', 'branch_id', 'department_id',
                          name='unique_module_activation_scope'),
    )
    op.create_index('idx_module_activations_tenant', 'module_activations', ['tenant_id'])
    op.create_index('idx_module_activations_module', 'module_activations', ['module_id'])
    op.create_index('idx_module_activations_company', 'module_activations', ['company_id'])

    # ========================================================
    # Step 5: Migrate data from tenant_modules -> module_activations
    # ========================================================
    op.execute("""
        INSERT INTO module_activations (
            id, module_id, tenant_id,
            is_enabled, is_configured, configuration,
            enabled_at, enabled_by_user_id,
            disabled_at, disabled_by_user_id,
            usage_count, last_used_at,
            created_at, updated_at
        )
        SELECT
            tm.id, tm.module_id, tm.tenant_id,
            tm.is_enabled, tm.is_configured, tm.configuration,
            tm.enabled_at, tm.enabled_by_user_id,
            tm.disabled_at, tm.disabled_by_user_id,
            tm.usage_count, tm.last_used_at,
            tm.created_at, tm.updated_at
        FROM tenant_modules tm
        WHERE tm.module_id IN (SELECT id FROM modules)
    """)

    # ========================================================
    # Step 6: Update FK references in dependent tables
    # ========================================================

    # module_dependencies: point FKs from nocode_modules -> modules
    op.drop_constraint('module_dependencies_module_id_fkey', 'module_dependencies', type_='foreignkey')
    op.drop_constraint('module_dependencies_depends_on_module_id_fkey', 'module_dependencies', type_='foreignkey')
    op.create_foreign_key(
        'module_dependencies_module_id_fkey', 'module_dependencies', 'modules',
        ['module_id'], ['id'], ondelete='CASCADE'
    )
    op.create_foreign_key(
        'module_dependencies_depends_on_module_id_fkey', 'module_dependencies', 'modules',
        ['depends_on_module_id'], ['id'], ondelete='RESTRICT'
    )

    # module_versions: point FK from nocode_modules -> modules
    op.drop_constraint('module_versions_module_id_fkey', 'module_versions', type_='foreignkey')
    op.create_foreign_key(
        'module_versions_module_id_fkey', 'module_versions', 'modules',
        ['module_id'], ['id'], ondelete='CASCADE'
    )

    # module_services: point FK from nocode_modules -> modules
    op.drop_constraint('module_services_module_id_fkey', 'module_services', type_='foreignkey')
    op.create_foreign_key(
        'module_services_module_id_fkey', 'module_services', 'modules',
        ['module_id'], ['id'], ondelete='CASCADE'
    )

    # module_service_access_log: point FK from nocode_modules -> modules
    op.drop_constraint('module_service_access_log_calling_module_id_fkey', 'module_service_access_log', type_='foreignkey')
    op.create_foreign_key(
        'module_service_access_log_calling_module_id_fkey', 'module_service_access_log', 'modules',
        ['calling_module_id'], ['id'], ondelete='SET NULL'
    )

    # module_entity_extensions
    op.drop_constraint('module_entity_extensions_extending_module_id_fkey', 'module_entity_extensions', type_='foreignkey')
    op.drop_constraint('module_entity_extensions_target_module_id_fkey', 'module_entity_extensions', type_='foreignkey')
    op.create_foreign_key(
        'module_entity_extensions_extending_module_id_fkey', 'module_entity_extensions', 'modules',
        ['extending_module_id'], ['id'], ondelete='CASCADE'
    )
    op.create_foreign_key(
        'module_entity_extensions_target_module_id_fkey', 'module_entity_extensions', 'modules',
        ['target_module_id'], ['id'], ondelete='CASCADE'
    )

    # module_screen_extensions
    op.drop_constraint('module_screen_extensions_extending_module_id_fkey', 'module_screen_extensions', type_='foreignkey')
    op.drop_constraint('module_screen_extensions_target_module_id_fkey', 'module_screen_extensions', type_='foreignkey')
    op.create_foreign_key(
        'module_screen_extensions_extending_module_id_fkey', 'module_screen_extensions', 'modules',
        ['extending_module_id'], ['id'], ondelete='CASCADE'
    )
    op.create_foreign_key(
        'module_screen_extensions_target_module_id_fkey', 'module_screen_extensions', 'modules',
        ['target_module_id'], ['id'], ondelete='CASCADE'
    )

    # module_menu_extensions
    op.drop_constraint('module_menu_extensions_extending_module_id_fkey', 'module_menu_extensions', type_='foreignkey')
    op.drop_constraint('module_menu_extensions_target_module_id_fkey', 'module_menu_extensions', type_='foreignkey')
    op.create_foreign_key(
        'module_menu_extensions_extending_module_id_fkey', 'module_menu_extensions', 'modules',
        ['extending_module_id'], ['id'], ondelete='CASCADE'
    )
    op.create_foreign_key(
        'module_menu_extensions_target_module_id_fkey', 'module_menu_extensions', 'modules',
        ['target_module_id'], ['id'], ondelete='CASCADE'
    )

    # entity_definitions: point FK from nocode_modules -> modules
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    fks = inspector.get_foreign_keys('entity_definitions')
    for fk in fks:
        if 'module_id' in fk['constrained_columns']:
            op.drop_constraint(fk['name'], 'entity_definitions', type_='foreignkey')
            break
    op.create_foreign_key(
        'fk_entity_definitions_module_id', 'entity_definitions', 'modules',
        ['module_id'], ['id'], ondelete='SET NULL'
    )

    # Also update module_id FKs on component tables that were added by pg_nocode_module_system
    component_tables = [
        'workflow_definitions', 'automation_rules', 'lookup_configurations',
        'report_definitions', 'dashboard_definitions'
    ]
    for table_name in component_tables:
        try:
            fks = inspector.get_foreign_keys(table_name)
            for fk in fks:
                if 'module_id' in fk['constrained_columns'] and fk.get('referred_table') == 'nocode_modules':
                    op.drop_constraint(fk['name'], table_name, type_='foreignkey')
                    op.create_foreign_key(
                        f'{table_name}_module_id_fkey', table_name, 'modules',
                        ['module_id'], ['id'], ondelete='SET NULL'
                    )
                    break
        except Exception:
            pass  # Table may not exist

    # ========================================================
    # Step 7: Drop old tables
    # ========================================================
    op.drop_table('tenant_modules')
    op.drop_table('nocode_modules')
    op.drop_table('module_registry')


def downgrade() -> None:
    """
    Reverse the unification: recreate the original tables and migrate data back.
    """
    # Recreate module_registry
    op.create_table(
        'module_registry',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('category', sa.String(50)),
        sa.Column('tags', JSON),
        sa.Column('author', sa.String(255)),
        sa.Column('license', sa.String(100)),
        sa.Column('is_installed', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_enabled', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_core', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('installed_at', sa.DateTime),
        sa.Column('installed_by_user_id', UUID(as_uuid=False)),
        sa.Column('manifest', JSON),
        sa.Column('configuration', JSON),
        sa.Column('dependencies', JSON),
        sa.Column('subscription_tier', sa.String(50)),
        sa.Column('pricing_model', sa.String(50)),
        sa.Column('api_prefix', sa.String(100)),
        sa.Column('has_migrations', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('database_tables', JSON),
        sa.Column('status', sa.String(50)),
        sa.Column('homepage', sa.String(500)),
        sa.Column('repository', sa.String(500)),
        sa.Column('support_email', sa.String(255)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime),
    )

    # Recreate nocode_modules
    op.create_table(
        'nocode_modules',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('version', sa.String(20), nullable=False, server_default='1.0.0'),
        sa.Column('major_version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('minor_version', sa.Integer, nullable=False, server_default='0'),
        sa.Column('patch_version', sa.Integer, nullable=False, server_default='0'),
        sa.Column('table_prefix', sa.String(10), nullable=False, unique=True),
        sa.Column('category', sa.String(50)),
        sa.Column('tags', JSON),
        sa.Column('icon', sa.String(50)),
        sa.Column('color', sa.String(7)),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('is_core', sa.Boolean, server_default='false'),
        sa.Column('is_template', sa.Boolean, server_default='false'),
        sa.Column('tenant_id', UUID(as_uuid=False), sa.ForeignKey('tenants.id', ondelete='CASCADE')),
        sa.Column('permissions', JSON),
        sa.Column('config', JSON),
        sa.Column('created_by', UUID(as_uuid=False), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_by', UUID(as_uuid=False), sa.ForeignKey('users.id')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('published_at', sa.DateTime(timezone=True)),
        sa.Column('published_by', UUID(as_uuid=False), sa.ForeignKey('users.id')),
    )

    # Recreate tenant_modules
    op.create_table(
        'tenant_modules',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=False), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('module_id', UUID(as_uuid=False), sa.ForeignKey('module_registry.id'), nullable=False),
        sa.Column('is_enabled', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_configured', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('configuration', JSON),
        sa.Column('enabled_at', sa.DateTime),
        sa.Column('enabled_by_user_id', UUID(as_uuid=False), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('disabled_at', sa.DateTime),
        sa.Column('disabled_by_user_id', UUID(as_uuid=False), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('usage_count', JSON),
        sa.Column('last_used_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    # Migrate data back from modules -> module_registry (code modules)
    op.execute("""
        INSERT INTO module_registry (
            id, name, display_name, version, description, category, tags, author, license,
            is_installed, is_core, installed_at, installed_by_user_id,
            manifest, configuration, dependencies,
            subscription_tier, pricing_model, api_prefix,
            has_migrations, database_tables, status,
            homepage, repository, support_email,
            created_at, updated_at
        )
        SELECT
            id, name, display_name, version, description, category, tags, author, license,
            is_installed, is_core, installed_at, installed_by_user_id,
            manifest, configuration, dependencies_json,
            subscription_tier, pricing_model, api_prefix,
            has_migrations, database_tables, status,
            homepage, repository, support_email,
            created_at, updated_at
        FROM modules
        WHERE module_type = 'code'
    """)

    # Migrate data back from modules -> nocode_modules
    op.execute("""
        INSERT INTO nocode_modules (
            id, name, display_name, description,
            version, major_version, minor_version, patch_version,
            table_prefix, category, tags, icon, color,
            status, is_core, is_template, tenant_id, permissions, config,
            created_by, created_at, updated_by, updated_at,
            published_at, published_by
        )
        SELECT
            id, name, display_name, description,
            version, major_version, minor_version, patch_version,
            table_prefix, category, tags, icon, color,
            status, is_core, is_template, tenant_id, permissions, configuration,
            created_by, created_at, updated_by, updated_at,
            published_at, published_by
        FROM modules
        WHERE module_type = 'nocode'
    """)

    # Migrate data back from module_activations -> tenant_modules
    op.execute("""
        INSERT INTO tenant_modules (
            id, tenant_id, module_id,
            is_enabled, is_configured, configuration,
            enabled_at, enabled_by_user_id,
            disabled_at, disabled_by_user_id,
            usage_count, last_used_at,
            created_at, updated_at
        )
        SELECT
            id, tenant_id, module_id,
            is_enabled, is_configured, configuration,
            enabled_at, enabled_by_user_id,
            disabled_at, disabled_by_user_id,
            usage_count, last_used_at,
            created_at, updated_at
        FROM module_activations
        WHERE company_id IS NULL AND branch_id IS NULL AND department_id IS NULL
    """)

    # Restore FK references
    op.drop_constraint('module_dependencies_module_id_fkey', 'module_dependencies', type_='foreignkey')
    op.drop_constraint('module_dependencies_depends_on_module_id_fkey', 'module_dependencies', type_='foreignkey')
    op.create_foreign_key(
        'module_dependencies_module_id_fkey', 'module_dependencies', 'nocode_modules',
        ['module_id'], ['id'], ondelete='CASCADE'
    )
    op.create_foreign_key(
        'module_dependencies_depends_on_module_id_fkey', 'module_dependencies', 'nocode_modules',
        ['depends_on_module_id'], ['id'], ondelete='RESTRICT'
    )

    op.drop_constraint('module_versions_module_id_fkey', 'module_versions', type_='foreignkey')
    op.create_foreign_key(
        'module_versions_module_id_fkey', 'module_versions', 'nocode_modules',
        ['module_id'], ['id'], ondelete='CASCADE'
    )

    op.drop_constraint('module_services_module_id_fkey', 'module_services', type_='foreignkey')
    op.create_foreign_key(
        'module_services_module_id_fkey', 'module_services', 'nocode_modules',
        ['module_id'], ['id'], ondelete='CASCADE'
    )

    op.drop_constraint('module_service_access_log_calling_module_id_fkey', 'module_service_access_log', type_='foreignkey')
    op.create_foreign_key(
        'module_service_access_log_calling_module_id_fkey', 'module_service_access_log', 'nocode_modules',
        ['calling_module_id'], ['id'], ondelete='SET NULL'
    )

    op.drop_constraint('module_entity_extensions_extending_module_id_fkey', 'module_entity_extensions', type_='foreignkey')
    op.drop_constraint('module_entity_extensions_target_module_id_fkey', 'module_entity_extensions', type_='foreignkey')
    op.create_foreign_key(
        'module_entity_extensions_extending_module_id_fkey', 'module_entity_extensions', 'nocode_modules',
        ['extending_module_id'], ['id'], ondelete='CASCADE'
    )
    op.create_foreign_key(
        'module_entity_extensions_target_module_id_fkey', 'module_entity_extensions', 'nocode_modules',
        ['target_module_id'], ['id'], ondelete='CASCADE'
    )

    op.drop_constraint('module_screen_extensions_extending_module_id_fkey', 'module_screen_extensions', type_='foreignkey')
    op.drop_constraint('module_screen_extensions_target_module_id_fkey', 'module_screen_extensions', type_='foreignkey')
    op.create_foreign_key(
        'module_screen_extensions_extending_module_id_fkey', 'module_screen_extensions', 'nocode_modules',
        ['extending_module_id'], ['id'], ondelete='CASCADE'
    )
    op.create_foreign_key(
        'module_screen_extensions_target_module_id_fkey', 'module_screen_extensions', 'nocode_modules',
        ['target_module_id'], ['id'], ondelete='CASCADE'
    )

    op.drop_constraint('module_menu_extensions_extending_module_id_fkey', 'module_menu_extensions', type_='foreignkey')
    op.drop_constraint('module_menu_extensions_target_module_id_fkey', 'module_menu_extensions', type_='foreignkey')
    op.create_foreign_key(
        'module_menu_extensions_extending_module_id_fkey', 'module_menu_extensions', 'nocode_modules',
        ['extending_module_id'], ['id'], ondelete='CASCADE'
    )
    op.create_foreign_key(
        'module_menu_extensions_target_module_id_fkey', 'module_menu_extensions', 'nocode_modules',
        ['target_module_id'], ['id'], ondelete='CASCADE'
    )

    # Drop unified tables
    op.drop_table('module_activations')
    op.drop_table('modules')
