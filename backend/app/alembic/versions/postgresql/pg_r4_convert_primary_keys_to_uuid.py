"""Convert report, dashboard, and scheduler primary keys to UUID

Revision ID: pg_r4
Revises: pg_s1
Create Date: 2025-11-12 13:00:00.000000

This migration converts Integer primary keys to UUID for consistency:
- All report tables (ReportDefinition, ReportExecution, ReportSchedule, ReportTemplate, ReportCache)
- All dashboard tables (Dashboard, DashboardPage, DashboardWidget, DashboardShare, DashboardSnapshot, WidgetDataCache)
- All scheduler tables (SchedulerConfig, SchedulerJob, SchedulerJobExecution, SchedulerJobLog)

⚠️ IMPORTANT: This is a breaking change. Backup your database before running.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'pg_r4'
down_revision = 'pg_s1'
branch_labels = None
depends_on = None


def upgrade():
    """
    Convert primary keys from Integer to UUID.

    Strategy:
    1. Add new UUID columns alongside existing Integer PKs
    2. Generate UUIDs for existing records
    3. Update foreign key references
    4. Drop old constraints and columns
    5. Rename new columns to replace old ones
    """

    # Enable uuid-ossp extension if not already enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # =================================================================
    # REPORT TABLES
    # =================================================================

    # --- ReportDefinition ---
    print("Converting report_definitions.id to UUID...")

    # Add temporary UUID column
    op.add_column('report_definitions', sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True))

    # Generate UUIDs for existing records
    op.execute(text("""
        UPDATE report_definitions
        SET id_uuid = uuid_generate_v4()
        WHERE id_uuid IS NULL
    """))

    # Make it non-nullable
    op.alter_column('report_definitions', 'id_uuid', nullable=False)

    # --- ReportExecution ---
    print("Converting report_executions...")

    # Add temporary UUID columns for PK and FK
    op.add_column('report_executions', sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('report_executions', sa.Column('report_definition_id_uuid', postgresql.UUID(as_uuid=True), nullable=True))

    # Generate UUIDs for existing records
    op.execute(text("""
        UPDATE report_executions
        SET id_uuid = uuid_generate_v4()
        WHERE id_uuid IS NULL
    """))

    # Update FK references using join
    op.execute(text("""
        UPDATE report_executions re
        SET report_definition_id_uuid = rd.id_uuid
        FROM report_definitions rd
        WHERE re.report_definition_id = rd.id
    """))

    # Make columns non-nullable
    op.alter_column('report_executions', 'id_uuid', nullable=False)
    op.alter_column('report_executions', 'report_definition_id_uuid', nullable=False)

    # --- ReportSchedule ---
    print("Converting report_schedules...")

    op.add_column('report_schedules', sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('report_schedules', sa.Column('report_definition_id_uuid', postgresql.UUID(as_uuid=True), nullable=True))

    op.execute(text("""
        UPDATE report_schedules
        SET id_uuid = uuid_generate_v4()
        WHERE id_uuid IS NULL
    """))

    op.execute(text("""
        UPDATE report_schedules rs
        SET report_definition_id_uuid = rd.id_uuid
        FROM report_definitions rd
        WHERE rs.report_definition_id = rd.id
    """))

    op.alter_column('report_schedules', 'id_uuid', nullable=False)
    op.alter_column('report_schedules', 'report_definition_id_uuid', nullable=False)

    # --- ReportTemplate ---
    print("Converting report_templates...")

    op.add_column('report_templates', sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True))

    op.execute(text("""
        UPDATE report_templates
        SET id_uuid = uuid_generate_v4()
        WHERE id_uuid IS NULL
    """))

    op.alter_column('report_templates', 'id_uuid', nullable=False)

    # --- ReportCache ---
    print("Converting report_cache...")

    op.add_column('report_cache', sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('report_cache', sa.Column('report_definition_id_uuid', postgresql.UUID(as_uuid=True), nullable=True))

    op.execute(text("""
        UPDATE report_cache
        SET id_uuid = uuid_generate_v4()
        WHERE id_uuid IS NULL
    """))

    op.execute(text("""
        UPDATE report_cache rc
        SET report_definition_id_uuid = rd.id_uuid
        FROM report_definitions rd
        WHERE rc.report_definition_id = rd.id
    """))

    op.alter_column('report_cache', 'id_uuid', nullable=False)
    op.alter_column('report_cache', 'report_definition_id_uuid', nullable=False)

    # Drop old constraints and swap columns for report tables
    print("Swapping report table columns...")

    # ReportExecution
    op.drop_constraint('report_executions_report_definition_id_fkey', 'report_executions', type_='foreignkey')
    op.drop_constraint('report_executions_pkey', 'report_executions', type_='primary')
    op.drop_column('report_executions', 'id')
    op.drop_column('report_executions', 'report_definition_id')
    op.alter_column('report_executions', 'id_uuid', new_column_name='id')
    op.alter_column('report_executions', 'report_definition_id_uuid', new_column_name='report_definition_id')
    op.create_primary_key('report_executions_pkey', 'report_executions', ['id'])

    # ReportSchedule
    op.drop_constraint('report_schedules_report_definition_id_fkey', 'report_schedules', type_='foreignkey')
    op.drop_constraint('report_schedules_pkey', 'report_schedules', type_='primary')
    op.drop_column('report_schedules', 'id')
    op.drop_column('report_schedules', 'report_definition_id')
    op.alter_column('report_schedules', 'id_uuid', new_column_name='id')
    op.alter_column('report_schedules', 'report_definition_id_uuid', new_column_name='report_definition_id')
    op.create_primary_key('report_schedules_pkey', 'report_schedules', ['id'])

    # ReportCache
    op.drop_constraint('report_cache_report_definition_id_fkey', 'report_cache', type_='foreignkey')
    op.drop_constraint('report_cache_pkey', 'report_cache', type_='primary')
    op.drop_column('report_cache', 'id')
    op.drop_column('report_cache', 'report_definition_id')
    op.alter_column('report_cache', 'id_uuid', new_column_name='id')
    op.alter_column('report_cache', 'report_definition_id_uuid', new_column_name='report_definition_id')
    op.create_primary_key('report_cache_pkey', 'report_cache', ['id'])

    # ReportDefinition (no FK dependencies now)
    op.drop_constraint('report_definitions_pkey', 'report_definitions', type_='primary')
    op.drop_column('report_definitions', 'id')
    op.alter_column('report_definitions', 'id_uuid', new_column_name='id')
    op.create_primary_key('report_definitions_pkey', 'report_definitions', ['id'])

    # ReportTemplate
    op.drop_constraint('report_templates_pkey', 'report_templates', type_='primary')
    op.drop_column('report_templates', 'id')
    op.alter_column('report_templates', 'id_uuid', new_column_name='id')
    op.create_primary_key('report_templates_pkey', 'report_templates', ['id'])

    # Recreate foreign keys
    op.create_foreign_key('report_executions_report_definition_id_fkey',
                         'report_executions', 'report_definitions',
                         ['report_definition_id'], ['id'])
    op.create_foreign_key('report_schedules_report_definition_id_fkey',
                         'report_schedules', 'report_definitions',
                         ['report_definition_id'], ['id'])
    op.create_foreign_key('report_cache_report_definition_id_fkey',
                         'report_cache', 'report_definitions',
                         ['report_definition_id'], ['id'])

    # =================================================================
    # DASHBOARD TABLES
    # =================================================================

    print("Converting dashboard tables...")

    # --- Dashboard ---
    op.add_column('dashboards', sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(text("UPDATE dashboards SET id_uuid = uuid_generate_v4() WHERE id_uuid IS NULL"))
    op.alter_column('dashboards', 'id_uuid', nullable=False)

    # --- DashboardPage ---
    op.add_column('dashboard_pages', sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('dashboard_pages', sa.Column('dashboard_id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(text("UPDATE dashboard_pages SET id_uuid = uuid_generate_v4() WHERE id_uuid IS NULL"))
    op.execute(text("""
        UPDATE dashboard_pages dp
        SET dashboard_id_uuid = d.id_uuid
        FROM dashboards d
        WHERE dp.dashboard_id = d.id
    """))
    op.alter_column('dashboard_pages', 'id_uuid', nullable=False)
    op.alter_column('dashboard_pages', 'dashboard_id_uuid', nullable=False)

    # --- DashboardWidget ---
    op.add_column('dashboard_widgets', sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('dashboard_widgets', sa.Column('page_id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('dashboard_widgets', sa.Column('report_definition_id_uuid', postgresql.UUID(as_uuid=True), nullable=True))

    op.execute(text("UPDATE dashboard_widgets SET id_uuid = uuid_generate_v4() WHERE id_uuid IS NULL"))
    op.execute(text("""
        UPDATE dashboard_widgets dw
        SET page_id_uuid = dp.id_uuid
        FROM dashboard_pages dp
        WHERE dw.page_id = dp.id
    """))
    # Link widgets to report definitions if they exist
    op.execute(text("""
        UPDATE dashboard_widgets dw
        SET report_definition_id_uuid = rd.id
        FROM report_definitions rd
        WHERE dw.report_definition_id = rd.id::text::integer
        AND dw.report_definition_id IS NOT NULL
    """))

    op.alter_column('dashboard_widgets', 'id_uuid', nullable=False)
    op.alter_column('dashboard_widgets', 'page_id_uuid', nullable=False)

    # --- DashboardShare ---
    op.add_column('dashboard_shares', sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('dashboard_shares', sa.Column('dashboard_id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(text("UPDATE dashboard_shares SET id_uuid = uuid_generate_v4() WHERE id_uuid IS NULL"))
    op.execute(text("""
        UPDATE dashboard_shares ds
        SET dashboard_id_uuid = d.id_uuid
        FROM dashboards d
        WHERE ds.dashboard_id = d.id
    """))
    op.alter_column('dashboard_shares', 'id_uuid', nullable=False)
    op.alter_column('dashboard_shares', 'dashboard_id_uuid', nullable=False)

    # --- DashboardSnapshot ---
    op.add_column('dashboard_snapshots', sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('dashboard_snapshots', sa.Column('dashboard_id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(text("UPDATE dashboard_snapshots SET id_uuid = uuid_generate_v4() WHERE id_uuid IS NULL"))
    op.execute(text("""
        UPDATE dashboard_snapshots ds
        SET dashboard_id_uuid = d.id_uuid
        FROM dashboards d
        WHERE ds.dashboard_id = d.id
    """))
    op.alter_column('dashboard_snapshots', 'id_uuid', nullable=False)
    op.alter_column('dashboard_snapshots', 'dashboard_id_uuid', nullable=False)

    # --- WidgetDataCache ---
    op.add_column('widget_data_cache', sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('widget_data_cache', sa.Column('widget_id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(text("UPDATE widget_data_cache SET id_uuid = uuid_generate_v4() WHERE id_uuid IS NULL"))
    op.execute(text("""
        UPDATE widget_data_cache wdc
        SET widget_id_uuid = dw.id_uuid
        FROM dashboard_widgets dw
        WHERE wdc.widget_id = dw.id
    """))
    op.alter_column('widget_data_cache', 'id_uuid', nullable=False)
    op.alter_column('widget_data_cache', 'widget_id_uuid', nullable=False)

    # Drop and swap dashboard columns
    print("Swapping dashboard table columns...")

    # WidgetDataCache
    op.drop_constraint('widget_data_cache_widget_id_fkey', 'widget_data_cache', type_='foreignkey')
    op.drop_constraint('widget_data_cache_pkey', 'widget_data_cache', type_='primary')
    op.drop_column('widget_data_cache', 'id')
    op.drop_column('widget_data_cache', 'widget_id')
    op.alter_column('widget_data_cache', 'id_uuid', new_column_name='id')
    op.alter_column('widget_data_cache', 'widget_id_uuid', new_column_name='widget_id')
    op.create_primary_key('widget_data_cache_pkey', 'widget_data_cache', ['id'])

    # DashboardWidget
    op.drop_constraint('dashboard_widgets_page_id_fkey', 'dashboard_widgets', type_='foreignkey')
    op.drop_constraint('dashboard_widgets_pkey', 'dashboard_widgets', type_='primary')
    op.drop_column('dashboard_widgets', 'id')
    op.drop_column('dashboard_widgets', 'page_id')
    op.drop_column('dashboard_widgets', 'report_definition_id')
    op.alter_column('dashboard_widgets', 'id_uuid', new_column_name='id')
    op.alter_column('dashboard_widgets', 'page_id_uuid', new_column_name='page_id')
    op.alter_column('dashboard_widgets', 'report_definition_id_uuid', new_column_name='report_definition_id')
    op.create_primary_key('dashboard_widgets_pkey', 'dashboard_widgets', ['id'])

    # DashboardPage
    op.drop_constraint('dashboard_pages_dashboard_id_fkey', 'dashboard_pages', type_='foreignkey')
    op.drop_constraint('dashboard_pages_pkey', 'dashboard_pages', type_='primary')
    op.drop_column('dashboard_pages', 'id')
    op.drop_column('dashboard_pages', 'dashboard_id')
    op.alter_column('dashboard_pages', 'id_uuid', new_column_name='id')
    op.alter_column('dashboard_pages', 'dashboard_id_uuid', new_column_name='dashboard_id')
    op.create_primary_key('dashboard_pages_pkey', 'dashboard_pages', ['id'])

    # DashboardShare
    op.drop_constraint('dashboard_shares_dashboard_id_fkey', 'dashboard_shares', type_='foreignkey')
    op.drop_constraint('dashboard_shares_pkey', 'dashboard_shares', type_='primary')
    op.drop_column('dashboard_shares', 'id')
    op.drop_column('dashboard_shares', 'dashboard_id')
    op.alter_column('dashboard_shares', 'id_uuid', new_column_name='id')
    op.alter_column('dashboard_shares', 'dashboard_id_uuid', new_column_name='dashboard_id')
    op.create_primary_key('dashboard_shares_pkey', 'dashboard_shares', ['id'])

    # DashboardSnapshot
    op.drop_constraint('dashboard_snapshots_dashboard_id_fkey', 'dashboard_snapshots', type_='foreignkey')
    op.drop_constraint('dashboard_snapshots_pkey', 'dashboard_snapshots', type_='primary')
    op.drop_column('dashboard_snapshots', 'id')
    op.drop_column('dashboard_snapshots', 'dashboard_id')
    op.alter_column('dashboard_snapshots', 'id_uuid', new_column_name='id')
    op.alter_column('dashboard_snapshots', 'dashboard_id_uuid', new_column_name='dashboard_id')
    op.create_primary_key('dashboard_snapshots_pkey', 'dashboard_snapshots', ['id'])

    # Dashboard
    op.drop_constraint('dashboards_pkey', 'dashboards', type_='primary')
    op.drop_column('dashboards', 'id')
    op.alter_column('dashboards', 'id_uuid', new_column_name='id')
    op.create_primary_key('dashboards_pkey', 'dashboards', ['id'])

    # Recreate foreign keys
    op.create_foreign_key('dashboard_pages_dashboard_id_fkey',
                         'dashboard_pages', 'dashboards',
                         ['dashboard_id'], ['id'])
    op.create_foreign_key('dashboard_widgets_page_id_fkey',
                         'dashboard_widgets', 'dashboard_pages',
                         ['page_id'], ['id'])
    op.create_foreign_key('dashboard_shares_dashboard_id_fkey',
                         'dashboard_shares', 'dashboards',
                         ['dashboard_id'], ['id'])
    op.create_foreign_key('dashboard_snapshots_dashboard_id_fkey',
                         'dashboard_snapshots', 'dashboards',
                         ['dashboard_id'], ['id'])
    op.create_foreign_key('widget_data_cache_widget_id_fkey',
                         'widget_data_cache', 'dashboard_widgets',
                         ['widget_id'], ['id'])

    # =================================================================
    # SCHEDULER TABLES
    # =================================================================

    print("Converting scheduler tables...")

    # --- SchedulerConfig ---
    op.add_column('scheduler_configs', sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(text("UPDATE scheduler_configs SET id_uuid = uuid_generate_v4() WHERE id_uuid IS NULL"))
    op.alter_column('scheduler_configs', 'id_uuid', nullable=False)

    # --- SchedulerJob ---
    op.add_column('scheduler_jobs', sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('scheduler_jobs', sa.Column('config_id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(text("UPDATE scheduler_jobs SET id_uuid = uuid_generate_v4() WHERE id_uuid IS NULL"))
    op.execute(text("""
        UPDATE scheduler_jobs sj
        SET config_id_uuid = sc.id_uuid
        FROM scheduler_configs sc
        WHERE sj.config_id = sc.id
    """))
    op.alter_column('scheduler_jobs', 'id_uuid', nullable=False)
    op.alter_column('scheduler_jobs', 'config_id_uuid', nullable=False)

    # --- SchedulerJobExecution ---
    op.add_column('scheduler_job_executions', sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('scheduler_job_executions', sa.Column('job_id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(text("UPDATE scheduler_job_executions SET id_uuid = uuid_generate_v4() WHERE id_uuid IS NULL"))
    op.execute(text("""
        UPDATE scheduler_job_executions sje
        SET job_id_uuid = sj.id_uuid
        FROM scheduler_jobs sj
        WHERE sje.job_id = sj.id
    """))
    op.alter_column('scheduler_job_executions', 'id_uuid', nullable=False)
    op.alter_column('scheduler_job_executions', 'job_id_uuid', nullable=False)

    # --- SchedulerJobLog ---
    op.add_column('scheduler_job_logs', sa.Column('id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('scheduler_job_logs', sa.Column('execution_id_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(text("UPDATE scheduler_job_logs SET id_uuid = uuid_generate_v4() WHERE id_uuid IS NULL"))
    op.execute(text("""
        UPDATE scheduler_job_logs sjl
        SET execution_id_uuid = sje.id_uuid
        FROM scheduler_job_executions sje
        WHERE sjl.execution_id = sje.id
    """))
    op.alter_column('scheduler_job_logs', 'id_uuid', nullable=False)
    op.alter_column('scheduler_job_logs', 'execution_id_uuid', nullable=False)

    # Drop and swap scheduler columns
    print("Swapping scheduler table columns...")

    # SchedulerJobLog
    op.drop_constraint('scheduler_job_logs_execution_id_fkey', 'scheduler_job_logs', type_='foreignkey')
    op.drop_constraint('scheduler_job_logs_pkey', 'scheduler_job_logs', type_='primary')
    op.drop_column('scheduler_job_logs', 'id')
    op.drop_column('scheduler_job_logs', 'execution_id')
    op.alter_column('scheduler_job_logs', 'id_uuid', new_column_name='id')
    op.alter_column('scheduler_job_logs', 'execution_id_uuid', new_column_name='execution_id')
    op.create_primary_key('scheduler_job_logs_pkey', 'scheduler_job_logs', ['id'])

    # SchedulerJobExecution
    op.drop_constraint('scheduler_job_executions_job_id_fkey', 'scheduler_job_executions', type_='foreignkey')
    op.drop_constraint('scheduler_job_executions_pkey', 'scheduler_job_executions', type_='primary')
    op.drop_column('scheduler_job_executions', 'id')
    op.drop_column('scheduler_job_executions', 'job_id')
    op.alter_column('scheduler_job_executions', 'id_uuid', new_column_name='id')
    op.alter_column('scheduler_job_executions', 'job_id_uuid', new_column_name='job_id')
    op.create_primary_key('scheduler_job_executions_pkey', 'scheduler_job_executions', ['id'])

    # SchedulerJob
    op.drop_constraint('scheduler_jobs_config_id_fkey', 'scheduler_jobs', type_='foreignkey')
    op.drop_constraint('scheduler_jobs_pkey', 'scheduler_jobs', type_='primary')
    op.drop_column('scheduler_jobs', 'id')
    op.drop_column('scheduler_jobs', 'config_id')
    op.alter_column('scheduler_jobs', 'id_uuid', new_column_name='id')
    op.alter_column('scheduler_jobs', 'config_id_uuid', new_column_name='config_id')
    op.create_primary_key('scheduler_jobs_pkey', 'scheduler_jobs', ['id'])

    # SchedulerConfig
    op.drop_constraint('scheduler_configs_pkey', 'scheduler_configs', type_='primary')
    op.drop_column('scheduler_configs', 'id')
    op.alter_column('scheduler_configs', 'id_uuid', new_column_name='id')
    op.create_primary_key('scheduler_configs_pkey', 'scheduler_configs', ['id'])

    # Recreate foreign keys
    op.create_foreign_key('scheduler_jobs_config_id_fkey',
                         'scheduler_jobs', 'scheduler_configs',
                         ['config_id'], ['id'])
    op.create_foreign_key('scheduler_job_executions_job_id_fkey',
                         'scheduler_job_executions', 'scheduler_jobs',
                         ['job_id'], ['id'])
    op.create_foreign_key('scheduler_job_logs_execution_id_fkey',
                         'scheduler_job_logs', 'scheduler_job_executions',
                         ['execution_id'], ['id'])

    print("✓ Migration completed successfully!")


def downgrade():
    """
    Downgrade is intentionally not implemented.

    Reversing UUID to Integer conversion would require:
    1. Mapping UUIDs back to sequential integers
    2. Risk of data loss if UUIDs can't map to integers
    3. Breaking existing API contracts

    If downgrade is absolutely necessary, restore from database backup.
    """
    raise NotImplementedError(
        "Downgrade not supported for UUID conversion. "
        "Restore from database backup if you need to revert this change."
    )
