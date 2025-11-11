"""Convert report and dashboard tenant_id and user IDs to UUID

Revision ID: pg_r3
Revises: pg_merge_module_fk_dashboard
Create Date: 2025-11-11 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'pg_r3'
down_revision = 'pg_merge_module_fk_dashboard'
branch_labels = None
depends_on = None


def upgrade():
    # Report tables
    # ReportDefinition
    op.alter_column('report_definitions', 'tenant_id',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::uuid')

    op.alter_column('report_definitions', 'created_by',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=False,
                    postgresql_using='created_by::text::uuid')

    # ReportExecution
    op.alter_column('report_executions', 'tenant_id',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::uuid')

    op.alter_column('report_executions', 'executed_by',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=False,
                    postgresql_using='executed_by::text::uuid')

    # ReportSchedule
    op.alter_column('report_schedules', 'tenant_id',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::uuid')

    op.alter_column('report_schedules', 'created_by',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=False,
                    postgresql_using='created_by::text::uuid')

    # ReportCache
    op.alter_column('report_cache', 'tenant_id',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::uuid')

    # Dashboard tables
    # Dashboard
    op.alter_column('dashboards', 'tenant_id',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::uuid')

    op.alter_column('dashboards', 'created_by',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=False,
                    postgresql_using='created_by::text::uuid')

    # DashboardPage
    op.alter_column('dashboard_pages', 'tenant_id',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::uuid')

    # DashboardWidget
    op.alter_column('dashboard_widgets', 'tenant_id',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::uuid')

    # DashboardShare
    op.alter_column('dashboard_shares', 'tenant_id',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::uuid')

    op.alter_column('dashboard_shares', 'created_by',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=False,
                    postgresql_using='created_by::text::uuid')

    op.alter_column('dashboard_shares', 'shared_with_user_id',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=True,
                    postgresql_using='shared_with_user_id::text::uuid')

    # DashboardSnapshot
    op.alter_column('dashboard_snapshots', 'tenant_id',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::uuid')

    op.alter_column('dashboard_snapshots', 'created_by',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=False,
                    postgresql_using='created_by::text::uuid')

    # WidgetDataCache
    op.alter_column('widget_data_cache', 'tenant_id',
                    existing_type=sa.Integer(),
                    type_=postgresql.UUID(as_uuid=True),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::uuid')


def downgrade():
    # Reverse all changes
    # Report tables
    op.alter_column('report_definitions', 'tenant_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::integer')

    op.alter_column('report_definitions', 'created_by',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='created_by::text::integer')

    op.alter_column('report_executions', 'tenant_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::integer')

    op.alter_column('report_executions', 'executed_by',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='executed_by::text::integer')

    op.alter_column('report_schedules', 'tenant_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::integer')

    op.alter_column('report_schedules', 'created_by',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='created_by::text::integer')

    op.alter_column('report_cache', 'tenant_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::integer')

    # Dashboard tables
    op.alter_column('dashboards', 'tenant_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::integer')

    op.alter_column('dashboards', 'created_by',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='created_by::text::integer')

    op.alter_column('dashboard_pages', 'tenant_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::integer')

    op.alter_column('dashboard_widgets', 'tenant_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::integer')

    op.alter_column('dashboard_shares', 'tenant_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::integer')

    op.alter_column('dashboard_shares', 'created_by',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='created_by::text::integer')

    op.alter_column('dashboard_shares', 'shared_with_user_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=True,
                    postgresql_using='shared_with_user_id::text::integer')

    op.alter_column('dashboard_snapshots', 'tenant_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::integer')

    op.alter_column('dashboard_snapshots', 'created_by',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='created_by::text::integer')

    op.alter_column('widget_data_cache', 'tenant_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='tenant_id::text::integer')
