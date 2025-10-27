"""Create RBAC tables (PostgreSQL) - Permissions, Roles, Groups, and Junctions"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "pg_f0g1h2i3j4k5"
down_revision = "pg_e9f0g1h2i3j4"
branch_labels = None
depends_on = None

def upgrade():
    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(length=100), unique=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resource', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('scope', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True)
    )
    op.create_index('ix_permissions_code', 'permissions', ['code'])
    op.create_index('ix_permissions_resource', 'permissions', ['resource'])
    op.create_index('ix_permissions_action', 'permissions', ['action'])
    op.create_index('ix_permissions_scope', 'permissions', ['scope'])
    op.create_index('ix_permissions_category', 'permissions', ['category'])
    op.create_index('ix_permissions_is_active', 'permissions', ['is_active'])
    op.create_index('ix_permission_resource_action_scope', 'permissions', ['resource', 'action', 'scope'])

    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('role_type', sa.String(length=50), nullable=False, server_default='custom'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    )
    op.create_index('ix_roles_tenant_id', 'roles', ['tenant_id'])
    op.create_index('ix_roles_code', 'roles', ['code'])
    op.create_index('ix_roles_role_type', 'roles', ['role_type'])
    op.create_index('ix_roles_is_active', 'roles', ['is_active'])
    op.create_index('ix_role_tenant_type', 'roles', ['tenant_id', 'role_type'])
    op.create_unique_constraint('uq_role_tenant_code', 'roles', ['tenant_id', 'code'])

    # Create groups table
    op.create_table(
        'groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('group_type', sa.String(length=50), nullable=False, server_default='team'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    )
    op.create_index('ix_groups_tenant_id', 'groups', ['tenant_id'])
    op.create_index('ix_groups_company_id', 'groups', ['company_id'])
    op.create_index('ix_groups_code', 'groups', ['code'])
    op.create_index('ix_groups_group_type', 'groups', ['group_type'])
    op.create_index('ix_groups_is_active', 'groups', ['is_active'])
    op.create_index('ix_group_tenant_company', 'groups', ['tenant_id', 'company_id'])
    op.create_unique_constraint('uq_group_tenant_company_code', 'groups', ['tenant_id', 'company_id', 'code'])

    # Create role_permissions junction table
    op.create_table(
        'role_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('granted_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    )
    op.create_index('ix_role_permissions_role_id', 'role_permissions', ['role_id'])
    op.create_index('ix_role_permissions_permission_id', 'role_permissions', ['permission_id'])
    op.create_unique_constraint('uq_role_permission', 'role_permissions', ['role_id', 'permission_id'])

    # Create user_roles junction table
    op.create_table(
        'user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('granted_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    )
    op.create_index('ix_user_roles_user_id', 'user_roles', ['user_id'])
    op.create_index('ix_user_roles_role_id', 'user_roles', ['role_id'])
    op.create_unique_constraint('uq_user_role', 'user_roles', ['user_id', 'role_id'])

    # Create user_groups junction table
    op.create_table(
        'user_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('added_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    )
    op.create_index('ix_user_groups_user_id', 'user_groups', ['user_id'])
    op.create_index('ix_user_groups_group_id', 'user_groups', ['group_id'])
    op.create_unique_constraint('uq_user_group', 'user_groups', ['user_id', 'group_id'])

    # Create group_roles junction table
    op.create_table(
        'group_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('granted_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    )
    op.create_index('ix_group_roles_group_id', 'group_roles', ['group_id'])
    op.create_index('ix_group_roles_role_id', 'group_roles', ['role_id'])
    op.create_unique_constraint('uq_group_role', 'group_roles', ['group_id', 'role_id'])

def downgrade():
    # Drop junction tables
    op.drop_table('group_roles')
    op.drop_table('user_groups')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')

    # Drop main tables
    op.drop_table('groups')
    op.drop_table('roles')
    op.drop_table('permissions')
