"""Create no-code module system tables (Phase 4 Priority 1)

Revision ID: pg_nocode_module_system
Revises: pg_template_management
Create Date: 2026-01-19 15:30:00.000000

Creates tables for the Module System Foundation:
- nocode_modules: Module registry with semantic versioning
- module_dependencies: Cross-module dependencies with version constraints
- module_versions: Version history and snapshots
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision = 'pg_nocode_module_system'
down_revision = 'pg_template_management'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create no-code module system tables.
    """

    # Create nocode_modules table
    op.create_table(
        'nocode_modules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),

        # Versioning (Semantic Versioning)
        sa.Column('version', sa.String(20), nullable=False, server_default='1.0.0'),
        sa.Column('major_version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('minor_version', sa.Integer, nullable=False, server_default='0'),
        sa.Column('patch_version', sa.Integer, nullable=False, server_default='0'),

        # Table naming (max 10 chars, lowercase alphanumeric, no underscore)
        sa.Column('table_prefix', sa.String(10), nullable=False, unique=True),

        # Metadata
        sa.Column('category', sa.String(50)),
        sa.Column('tags', JSON, server_default='[]'),
        sa.Column('icon', sa.String(50)),
        sa.Column('color', sa.String(7)),

        # Status
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('is_core', sa.Boolean, server_default='false'),
        sa.Column('is_template', sa.Boolean, server_default='false'),

        # Organization (NULL = platform-level template)
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE')),

        # Permissions
        sa.Column('permissions', JSON, server_default='[]'),

        # Configuration
        sa.Column('config', JSON, server_default='{}'),

        # Audit
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_by', UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('published_at', sa.DateTime(timezone=True)),
        sa.Column('published_by', UUID(as_uuid=True), sa.ForeignKey('users.id')),

        # Constraints
        sa.CheckConstraint("version ~ '^[0-9]+\\.[0-9]+\\.[0-9]+$'", name='valid_version'),
        sa.CheckConstraint("table_prefix ~ '^[a-z0-9]{1,10}$'", name='valid_prefix'),
        sa.CheckConstraint("status IN ('draft', 'active', 'deprecated', 'archived')", name='valid_status'),
    )

    # Create indexes for nocode_modules
    op.create_index('idx_nocode_modules_name', 'nocode_modules', ['name'])
    op.create_index('idx_nocode_modules_tenant', 'nocode_modules', ['tenant_id'])
    op.create_index('idx_nocode_modules_status', 'nocode_modules', ['status'])
    op.create_index('idx_nocode_modules_prefix', 'nocode_modules', ['table_prefix'])
    op.create_index('idx_nocode_modules_category', 'nocode_modules', ['category'])

    # Create module_dependencies table
    op.create_table(
        'module_dependencies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),

        # Relationship
        sa.Column('module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('depends_on_module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='RESTRICT'), nullable=False),

        # Dependency type
        sa.Column('dependency_type', sa.String(20), nullable=False, server_default='required'),

        # Version constraints
        sa.Column('min_version', sa.String(20)),
        sa.Column('max_version', sa.String(20)),
        sa.Column('version_constraint', sa.String(100)),

        # Metadata
        sa.Column('reason', sa.Text),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id')),

        # Constraints
        sa.CheckConstraint("dependency_type IN ('required', 'optional', 'conflicts')", name='valid_dependency_type'),
        sa.CheckConstraint("module_id != depends_on_module_id", name='no_self_dependency'),
        sa.UniqueConstraint('module_id', 'depends_on_module_id', name='unique_module_dependency'),
    )

    # Create indexes for module_dependencies
    op.create_index('idx_module_dependencies_module', 'module_dependencies', ['module_id'])
    op.create_index('idx_module_dependencies_depends_on', 'module_dependencies', ['depends_on_module_id'])

    # Create module_versions table
    op.create_table(
        'module_versions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),

        # Module reference
        sa.Column('module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='CASCADE'), nullable=False),

        # Version info
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('major_version', sa.Integer, nullable=False),
        sa.Column('minor_version', sa.Integer, nullable=False),
        sa.Column('patch_version', sa.Integer, nullable=False),

        # Change tracking
        sa.Column('change_type', sa.String(20), nullable=False),
        sa.Column('change_summary', sa.Text, nullable=False),
        sa.Column('changelog', sa.Text),
        sa.Column('breaking_changes', sa.Text),

        # Snapshot
        sa.Column('snapshot', JSON, nullable=False),

        # Status
        sa.Column('is_current', sa.Boolean, server_default='false'),

        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id')),

        # Constraints
        sa.CheckConstraint("change_type IN ('major', 'minor', 'patch', 'hotfix')", name='valid_change_type'),
        sa.UniqueConstraint('module_id', 'version', name='unique_module_version'),
    )

    # Create indexes for module_versions
    op.create_index('idx_module_versions_module', 'module_versions', ['module_id'])
    op.create_index('idx_module_versions_current', 'module_versions', ['module_id', 'is_current'], postgresql_where=sa.text('is_current = true'))
    op.create_index('idx_module_versions_number', 'module_versions', ['module_id', 'version_number'])

    # Add module_id to existing no-code component tables (only if they exist)
    # Using a connection to check table existence
    connection = op.get_bind()

    # Helper function to check if table exists
    def table_exists(table_name):
        result = connection.execute(sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"
        ), {"table_name": table_name})
        return result.scalar()

    # List of tables to add module_id to
    component_tables = [
        'entity_definitions',
        'workflow_definitions',
        'automation_rules',
        'lookup_configurations',
        'report_definitions',
        'dashboard_definitions'
    ]

    # Add module_id column and index to each table if it exists
    for table_name in component_tables:
        if table_exists(table_name):
            op.add_column(table_name, sa.Column('module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='SET NULL')))
            op.create_index(f'idx_{table_name}_module', table_name, ['module_id'])


def downgrade() -> None:
    """
    Drop no-code module system tables.
    """

    connection = op.get_bind()

    # Helper function to check if table exists
    def table_exists(table_name):
        result = connection.execute(sa.text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"
        ), {"table_name": table_name})
        return result.scalar()

    # List of component tables
    component_tables = [
        'entity_definitions',
        'workflow_definitions',
        'automation_rules',
        'lookup_configurations',
        'report_definitions',
        'dashboard_definitions'
    ]

    # Drop indexes and columns from component tables if they exist
    for table_name in component_tables:
        if table_exists(table_name):
            try:
                op.drop_index(f'idx_{table_name}_module', table_name)
            except Exception:
                pass  # Index might not exist

            try:
                op.drop_column(table_name, 'module_id')
            except Exception:
                pass  # Column might not exist


    # Drop module_versions table
    op.drop_index('idx_module_versions_number', 'module_versions')
    op.drop_index('idx_module_versions_current', 'module_versions')
    op.drop_index('idx_module_versions_module', 'module_versions')
    op.drop_table('module_versions')

    # Drop module_dependencies table
    op.drop_index('idx_module_dependencies_depends_on', 'module_dependencies')
    op.drop_index('idx_module_dependencies_module', 'module_dependencies')
    op.drop_table('module_dependencies')

    # Drop nocode_modules table
    op.drop_index('idx_nocode_modules_category', 'nocode_modules')
    op.drop_index('idx_nocode_modules_prefix', 'nocode_modules')
    op.drop_index('idx_nocode_modules_status', 'nocode_modules')
    op.drop_index('idx_nocode_modules_tenant', 'nocode_modules')
    op.drop_index('idx_nocode_modules_name', 'nocode_modules')
    op.drop_table('nocode_modules')
