"""Update tables for multi-tenant architecture (PostgreSQL)"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "pg_e9f0g1h2i3j4"
down_revision = "pg_d8e9f0g1h2i3"
branch_labels = None
depends_on = None

def upgrade():
    # Add tenant_id to companies table
    op.add_column('companies', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_companies_tenant', 'companies', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_companies_tenant_id', 'companies', ['tenant_id'])

    # Add new fields to companies
    op.add_column('companies', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('companies', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('companies', sa.Column('phone', sa.String(length=50), nullable=True))
    op.add_column('companies', sa.Column('website', sa.String(length=255), nullable=True))
    op.add_column('companies', sa.Column('address_line1', sa.String(length=255), nullable=True))
    op.add_column('companies', sa.Column('address_line2', sa.String(length=255), nullable=True))
    op.add_column('companies', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('companies', sa.Column('state', sa.String(length=100), nullable=True))
    op.add_column('companies', sa.Column('postal_code', sa.String(length=20), nullable=True))
    op.add_column('companies', sa.Column('country', sa.String(length=100), nullable=True))
    op.add_column('companies', sa.Column('tax_id', sa.String(length=50), nullable=True))
    op.add_column('companies', sa.Column('registration_number', sa.String(length=50), nullable=True))
    op.add_column('companies', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('companies', sa.Column('extra_data', sa.Text(), nullable=True))
    op.add_column('companies', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    # Drop old unique constraint on code, add new one with tenant_id
    op.drop_constraint('companies_code_key', 'companies', type_='unique')
    op.create_unique_constraint('uq_company_tenant_code', 'companies', ['tenant_id', 'code'])
    op.create_index('ix_companies_is_active', 'companies', ['is_active'])

    # Add tenant_id to branches table
    op.add_column('branches', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_branches_tenant', 'branches', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_branches_tenant_id', 'branches', ['tenant_id'])

    # Add new fields to branches
    op.add_column('branches', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('branches', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('branches', sa.Column('extra_data', sa.Text(), nullable=True))
    op.add_column('branches', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_index('ix_branches_is_active', 'branches', ['is_active'])

    # Add tenant_id to departments table
    op.add_column('departments', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_departments_tenant', 'departments', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_departments_tenant_id', 'departments', ['tenant_id'])

    # Add new fields to departments
    op.add_column('departments', sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_departments_parent', 'departments', 'departments', ['parent_id'], ['id'], ondelete='SET NULL')
    op.add_column('departments', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('departments', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('departments', sa.Column('extra_data', sa.Text(), nullable=True))
    op.add_column('departments', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_index('ix_departments_parent_id', 'departments', ['parent_id'])
    op.create_index('ix_departments_is_active', 'departments', ['is_active'])

    # Update users table for multi-tenant
    # First, drop the old tenant_id column (it was String, we need FK to tenants)
    op.drop_column('users', 'tenant_id')

    # Add new tenant_id with foreign key
    op.add_column('users', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_users_tenant', 'users', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')

    # Add new fields to users
    op.add_column('users', sa.Column('default_company_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_users_default_company', 'users', 'companies', ['default_company_id'], ['id'], ondelete='SET NULL')
    op.add_column('users', sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_users_branch', 'users', 'branches', ['branch_id'], ['id'], ondelete='SET NULL')
    op.add_column('users', sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_users_department', 'users', 'departments', ['department_id'], ['id'], ondelete='SET NULL')

    op.add_column('users', sa.Column('phone', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('avatar_url', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('extra_data', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    # Create indexes
    op.create_index('ix_users_default_company_id', 'users', ['default_company_id'])
    op.create_index('ix_users_branch_id', 'users', ['branch_id'])
    op.create_index('ix_users_department_id', 'users', ['department_id'])
    op.create_index('ix_users_is_verified', 'users', ['is_verified'])

def downgrade():
    # Revert users table
    op.drop_index('ix_users_is_verified', table_name='users')
    op.drop_index('ix_users_department_id', table_name='users')
    op.drop_index('ix_users_branch_id', table_name='users')
    op.drop_index('ix_users_default_company_id', table_name='users')

    op.drop_constraint('fk_users_department', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_branch', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_default_company', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_tenant', 'users', type_='foreignkey')

    op.drop_column('users', 'deleted_at')
    op.drop_column('users', 'extra_data')
    op.drop_column('users', 'is_verified')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'department_id')
    op.drop_column('users', 'branch_id')
    op.drop_column('users', 'default_company_id')
    op.drop_column('users', 'tenant_id')

    # Add back old tenant_id as String
    op.add_column('users', sa.Column('tenant_id', sa.String(length=36), nullable=True))

    # Revert departments
    op.drop_index('ix_departments_is_active', table_name='departments')
    op.drop_index('ix_departments_parent_id', table_name='departments')
    op.drop_constraint('fk_departments_parent', 'departments', type_='foreignkey')
    op.drop_constraint('fk_departments_tenant', 'departments', type_='foreignkey')
    op.drop_column('departments', 'deleted_at')
    op.drop_column('departments', 'extra_data')
    op.drop_column('departments', 'is_active')
    op.drop_column('departments', 'description')
    op.drop_column('departments', 'parent_id')
    op.drop_index('ix_departments_tenant_id', table_name='departments')
    op.drop_column('departments', 'tenant_id')

    # Revert branches
    op.drop_index('ix_branches_is_active', table_name='branches')
    op.drop_constraint('fk_branches_tenant', 'branches', type_='foreignkey')
    op.drop_column('branches', 'deleted_at')
    op.drop_column('branches', 'extra_data')
    op.drop_column('branches', 'is_active')
    op.drop_column('branches', 'description')
    op.drop_index('ix_branches_tenant_id', table_name='branches')
    op.drop_column('branches', 'tenant_id')

    # Revert companies
    op.drop_index('ix_companies_is_active', table_name='companies')
    op.drop_constraint('uq_company_tenant_code', 'companies', type_='unique')
    op.create_unique_constraint('companies_code_key', 'companies', ['code'])

    op.drop_constraint('fk_companies_tenant', 'companies', type_='foreignkey')
    op.drop_column('companies', 'deleted_at')
    op.drop_column('companies', 'extra_data')
    op.drop_column('companies', 'is_active')
    op.drop_column('companies', 'registration_number')
    op.drop_column('companies', 'tax_id')
    op.drop_column('companies', 'country')
    op.drop_column('companies', 'postal_code')
    op.drop_column('companies', 'state')
    op.drop_column('companies', 'city')
    op.drop_column('companies', 'address_line2')
    op.drop_column('companies', 'address_line1')
    op.drop_column('companies', 'website')
    op.drop_column('companies', 'phone')
    op.drop_column('companies', 'email')
    op.drop_column('companies', 'description')
    op.drop_index('ix_companies_tenant_id', table_name='companies')
    op.drop_column('companies', 'tenant_id')
