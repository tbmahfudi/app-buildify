from __future__ import annotations
from alembic import op
from modules.healthcare.sdk.rls_policies import apply_branch_rls, apply_tenant_rls

revision = "hcs002"
down_revision = "hcs001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Branch-scoped RLS on scheduling tables
    apply_branch_rls(op, "hcs_appointments")
    apply_branch_rls(op, "hcs_waitlist")

    # hcs_appointment_slots -- branch-scoped RLS
    apply_branch_rls(op, "hcs_appointment_slots")

    # hcs_provider_schedules -- branch-scoped RLS
    apply_branch_rls(op, "hcs_provider_schedules")

    # hcs_notification_log -- tenant-only RLS (not branch-scoped)
    apply_tenant_rls(op, "hcs_notification_log")

    # Deferred FK: hcs_appointment_slots.appointment_id -> hcs_appointments.id
    op.execute(
        "ALTER TABLE hcs_appointment_slots "
        "ADD CONSTRAINT fk_hcs_slots_appointment_id "
        "FOREIGN KEY (appointment_id) REFERENCES hcs_appointments(id) "
        "DEFERRABLE INITIALLY DEFERRED"
    )

    # Add nullable appointment_id to hc_encounters (deferred FK)
    op.execute(
        "ALTER TABLE hc_encounters "
        "ADD COLUMN IF NOT EXISTS appointment_id VARCHAR(36) NULL"
    )
    op.execute(
        "ALTER TABLE hc_encounters "
        "ADD CONSTRAINT fk_hc_encounters_appointment_id "
        "FOREIGN KEY (appointment_id) REFERENCES hcs_appointments(id) "
        "DEFERRABLE INITIALLY DEFERRED"
    )

    for tbl in (
        "hcs_appointments",
        "hcs_waitlist",
        "hcs_appointment_slots",
        "hcs_provider_schedules",
        "hcs_notification_log",
    ):
        op.execute(f"GRANT SELECT ON {tbl} TO app_readonly_role;")
        op.execute(f"GRANT INSERT, UPDATE ON {tbl} TO app_user;")


def downgrade() -> None:
    op.execute("ALTER TABLE hc_encounters DROP CONSTRAINT IF EXISTS fk_hc_encounters_appointment_id")
    op.execute("ALTER TABLE hcs_appointment_slots DROP CONSTRAINT IF EXISTS fk_hcs_slots_appointment_id")
    op.execute("DROP POLICY IF EXISTS hcs_waitlist_branch_isolation ON hcs_waitlist;")
    op.execute("ALTER TABLE hcs_waitlist DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS hcs_appointments_branch_isolation ON hcs_appointments;")
    op.execute("ALTER TABLE hcs_appointments DISABLE ROW LEVEL SECURITY;")
