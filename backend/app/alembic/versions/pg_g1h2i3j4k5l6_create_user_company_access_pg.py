"""Create user_company_access table (PostgreSQL)"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "pg_g1h2i3j4k5l6"
down_revision = "pg_f0g1h2i3j4k5"
branch_labels = None
depends_on = None

def upgrade():
    # Create user_company_access table
    op.create_table(
        'user_company_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('access_level', sa.String(length=50), nullable=False, server_default='full'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('granted_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('granted_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True)
    )

    # Create indexes
    op.create_index('ix_user_company_access_user_id', 'user_company_access', ['user_id'])
    op.create_index('ix_user_company_access_company_id', 'user_company_access', ['company_id'])
    op.create_index('ix_user_company_access_is_active', 'user_company_access', ['is_active'])
    op.create_index('ix_user_company_access_branch_id', 'user_company_access', ['branch_id'])
    op.create_index('ix_user_company_access_department_id', 'user_company_access', ['department_id'])

    # Create unique constraint
    op.create_unique_constraint('uq_user_company_access', 'user_company_access', ['user_id', 'company_id'])

def downgrade():
    op.drop_table('user_company_access')
