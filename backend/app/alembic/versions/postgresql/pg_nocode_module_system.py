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

    # Add module_id to existing no-code component tables
    op.add_column('entity_definitions', sa.Column('module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='SET NULL')))
    op.add_column('workflow_definitions', sa.Column('module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='SET NULL')))
    op.add_column('automation_rules', sa.Column('module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='SET NULL')))
    op.add_column('lookup_configurations', sa.Column('module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='SET NULL')))
    op.add_column('report_definitions', sa.Column('module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='SET NULL')))
    op.add_column('dashboard_definitions', sa.Column('module_id', UUID(as_uuid=True), sa.ForeignKey('nocode_modules.id', ondelete='SET NULL')))

    # Create indexes on module_id foreign keys
    op.create_index('idx_entity_definitions_module', 'entity_definitions', ['module_id'])
    op.create_index('idx_workflow_definitions_module', 'workflow_definitions', ['module_id'])
    op.create_index('idx_automation_rules_module', 'automation_rules', ['module_id'])
    op.create_index('idx_lookup_configurations_module', 'lookup_configurations', ['module_id'])
    op.create_index('idx_report_definitions_module', 'report_definitions', ['module_id'])
    op.create_index('idx_dashboard_definitions_module', 'dashboard_definitions', ['module_id'])


def downgrade() -> None:
    """
    Drop no-code module system tables.
    """

    # Drop indexes from component tables
    op.drop_index('idx_entity_definitions_module', 'entity_definitions')
    op.drop_index('idx_workflow_definitions_module', 'workflow_definitions')
    op.drop_index('idx_automation_rules_module', 'automation_rules')
    op.drop_index('idx_lookup_configurations_module', 'lookup_configurations')
    op.drop_index('idx_report_definitions_module', 'report_definitions')
    op.drop_index('idx_dashboard_definitions_module', 'dashboard_definitions')

    # Drop module_id columns from component tables
    op.drop_column('entity_definitions', 'module_id')
    op.drop_column('workflow_definitions', 'module_id')
    op.drop_column('automation_rules', 'module_id')
    op.drop_column('lookup_configurations', 'module_id')
    op.drop_column('report_definitions', 'module_id')
    op.drop_column('dashboard_definitions', 'module_id')

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
