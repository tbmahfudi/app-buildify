"""Tenant-isolation RLS policies for hcs_002_rls_policies.py

Revision ID: hcs002
Revises: hcs001
"""
from __future__ import annotations
from alembic import op

revision = "hcs002"
down_revision = "hcs001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE hcs_appointments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcs_appointments FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcs_appointments_tenant_isolation ON hcs_appointments USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcs_waitlist ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcs_waitlist FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcs_waitlist_tenant_isolation ON hcs_waitlist USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcs_appointment_slots ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcs_appointment_slots FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcs_appointment_slots_tenant_isolation ON hcs_appointment_slots USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcs_provider_schedules ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcs_provider_schedules FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcs_provider_schedules_tenant_isolation ON hcs_provider_schedules USING (tenant_id = current_setting('app.current_tenant_id', true))")
    op.execute("ALTER TABLE hcs_notification_log ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hcs_notification_log FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY hcs_notification_log_tenant_isolation ON hcs_notification_log USING (tenant_id = current_setting('app.current_tenant_id', true))")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS hcs_appointments_tenant_isolation ON hcs_appointments;")
    op.execute("ALTER TABLE hcs_appointments DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcs_waitlist_tenant_isolation ON hcs_waitlist;")
    op.execute("ALTER TABLE hcs_waitlist DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcs_appointment_slots_tenant_isolation ON hcs_appointment_slots;")
    op.execute("ALTER TABLE hcs_appointment_slots DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcs_provider_schedules_tenant_isolation ON hcs_provider_schedules;")
    op.execute("ALTER TABLE hcs_provider_schedules DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcs_notification_log_tenant_isolation ON hcs_notification_log;")
    op.execute("ALTER TABLE hcs_notification_log DISABLE ROW LEVEL SECURITY;")
