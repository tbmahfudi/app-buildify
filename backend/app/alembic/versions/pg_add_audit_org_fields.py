"""add company_id, branch_id, department_id to audit_logs

Revision ID: pg_add_audit_org_fields
Revises: pg_m1n2o3p4q5r6
Create Date: 2025-11-06 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'pg_add_audit_org_fields'
down_revision = 'pg_m1n2o3p4q5r6'
branch_labels = None
depends_on = None


def upgrade():
    # Add missing columns to audit_logs table
    op.add_column('audit_logs', sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('audit_logs', sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('audit_logs', sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('audit_logs', sa.Column('request_method', sa.String(length=10), nullable=True))
    op.add_column('audit_logs', sa.Column('request_path', sa.String(length=500), nullable=True))
    op.add_column('audit_logs', sa.Column('error_code', sa.String(length=50), nullable=True))
    op.add_column('audit_logs', sa.Column('duration_ms', sa.String(length=20), nullable=True))

    # Create indexes for the new columns
    op.create_index('ix_audit_logs_company_id', 'audit_logs', ['company_id'])
    op.create_index('ix_audit_company_created', 'audit_logs', ['company_id', 'created_at'])
    op.create_index('ix_audit_tenant_company', 'audit_logs', ['tenant_id', 'company_id'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_audit_tenant_company', 'audit_logs')
    op.drop_index('ix_audit_company_created', 'audit_logs')
    op.drop_index('ix_audit_logs_company_id', 'audit_logs')

    # Drop columns
    op.drop_column('audit_logs', 'duration_ms')
    op.drop_column('audit_logs', 'error_code')
    op.drop_column('audit_logs', 'request_path')
    op.drop_column('audit_logs', 'request_method')
    op.drop_column('audit_logs', 'department_id')
    op.drop_column('audit_logs', 'branch_id')
    op.drop_column('audit_logs', 'company_id')
