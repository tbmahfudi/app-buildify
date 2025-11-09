"""Create org tables (MySQL)"""
from alembic import op
import sqlalchemy as sa

revision = "mysql_8c4ee763aa"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'companies',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('code', sa.String(length=32), nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        mysql_engine='InnoDB', mysql_charset='utf8mb4'
    )
    op.create_table(
        'branches',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('company_id', sa.String(length=36), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        mysql_engine='InnoDB', mysql_charset='utf8mb4'
    )
    op.create_index('ix_branches_company_id', 'branches', ['company_id'])
    op.create_table(
        'departments',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('company_id', sa.String(length=36), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('branch_id', sa.String(length=36), sa.ForeignKey('branches.id', ondelete='CASCADE'), nullable=True),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        mysql_engine='InnoDB', mysql_charset='utf8mb4'
    )
    op.create_index('ix_departments_company_id', 'departments', ['company_id'])
    op.create_index('ix_departments_branch_id', 'departments', ['branch_id'])
    op.create_unique_constraint('uq_branch_code_per_company', 'branches', ['company_id', 'code'])
    op.create_unique_constraint('uq_dept_code_per_company', 'departments', ['company_id', 'code'])

def downgrade():
    op.drop_constraint('uq_dept_code_per_company', 'departments', type_='unique')
    op.drop_constraint('uq_branch_code_per_company', 'branches', type_='unique')
    op.drop_index('ix_departments_branch_id', table_name='departments')
    op.drop_index('ix_departments_company_id', table_name='departments')
    op.drop_table('departments')
    op.drop_index('ix_branches_company_id', table_name='branches')
    op.drop_table('branches')
    op.drop_table('companies')
