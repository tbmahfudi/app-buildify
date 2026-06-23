from __future__ import annotations
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "hcs001"
down_revision = "hc004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. hcs_provider_schedules -- Provider weekly schedule templates
    op.create_table(
        "hcs_provider_schedules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), sa.ForeignKey("hc_branches.id"), nullable=False),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("hc_providers.id"), nullable=False),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("slot_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("appointment_types", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("day_of_week BETWEEN 0 AND 6", name="ck_hcs_schedules_day"),
        sa.CheckConstraint("start_time < end_time", name="ck_hcs_schedules_time_order"),
        sa.CheckConstraint("slot_duration_minutes > 0", name="ck_hcs_schedules_duration"),
    )
    op.create_index("idx_hcs_psch_tenant", "hcs_provider_schedules", ["tenant_id"])
    op.create_index("idx_hcs_psch_branch", "hcs_provider_schedules", ["branch_id"])
    op.create_index("idx_hcs_psch_prov_day", "hcs_provider_schedules", ["provider_id", "day_of_week"])

    # 2. hcs_appointment_slots -- Materialised time slots
    op.create_table(
        "hcs_appointment_slots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), sa.ForeignKey("hc_branches.id"), nullable=False),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("hc_providers.id"), nullable=False),
        sa.Column("schedule_id", sa.String(36), sa.ForeignKey("hcs_provider_schedules.id"), nullable=False),
        sa.Column("slot_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("appointment_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="available"),
        sa.Column("appointment_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "status IN ('available','booked','blocked','held')",
            name="ck_hcs_slots_status",
        ),
    )
    op.create_index("idx_hcs_slots_tenant", "hcs_appointment_slots", ["tenant_id"])
    op.create_index("idx_hcs_slots_branch", "hcs_appointment_slots", ["branch_id"])
    op.create_index("idx_hcs_slots_date", "hcs_appointment_slots", ["branch_id", "slot_date", "status"])
    op.create_index("idx_hcs_slots_prov_date", "hcs_appointment_slots", ["provider_id", "slot_date"])
    op.create_unique_constraint(
        "uq_hcs_slot_provider_datetime",
        "hcs_appointment_slots",
        ["tenant_id", "provider_id", "slot_date", "start_time"],
    )

    # 3. hcs_appointments -- Confirmed appointments
    op.create_table(
        "hcs_appointments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), sa.ForeignKey("hc_branches.id"), nullable=False),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("hc_providers.id"), nullable=False),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("hc_patients.id"), nullable=False),
        sa.Column("slot_id", sa.String(36), sa.ForeignKey("hcs_appointment_slots.id"), nullable=False),
        sa.Column("appointment_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="confirmed"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("rescheduled_from_id", sa.String(36), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "status IN ('confirmed','checked_in','in_progress','completed',"
            "'cancelled','no_show','flagged_for_review')",
            name="ck_hcs_appointments_status",
        ),
        sa.ForeignKeyConstraint(
            ["rescheduled_from_id"], ["hcs_appointments.id"],
            name="fk_hcs_appt_rescheduled",
        ),
    )
    op.create_index("idx_hcs_appt_tenant", "hcs_appointments", ["tenant_id"])
    op.create_index("idx_hcs_appt_branch", "hcs_appointments", ["branch_id"])
    op.create_index("idx_hcs_appt_patient", "hcs_appointments", ["patient_id"])
    op.create_index("idx_hcs_appt_provider", "hcs_appointments", ["provider_id"])
    op.create_index("idx_hcs_appt_sched_at", "hcs_appointments", ["branch_id", "scheduled_at"])

    # 4. hcs_waitlist -- Patient waitlist entries (FIFO)
    op.create_table(
        "hcs_waitlist",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), sa.ForeignKey("hc_branches.id"), nullable=False),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("hc_providers.id"), nullable=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("hc_patients.id"), nullable=False),
        sa.Column("appointment_type", sa.String(50), nullable=False),
        sa.Column("preferred_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="waiting"),
        sa.Column("offered_slot_id", sa.String(36), nullable=True),
        sa.Column("offer_expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "status IN ('waiting','offered','accepted','expired','removed')",
            name="ck_hcs_waitlist_status",
        ),
    )
    op.create_index("idx_hcs_wl_tenant", "hcs_waitlist", ["tenant_id"])
    op.create_index("idx_hcs_wl_branch", "hcs_waitlist", ["branch_id"])
    op.create_index("idx_hcs_wl_patient", "hcs_waitlist", ["patient_id"])
    op.create_index(
        "idx_hcs_wl_fifo",
        "hcs_waitlist",
        ["branch_id", "provider_id", "appointment_type", "preferred_date", "created_at"],
    )

    # 5. hcs_notification_log -- Outbound notification records (no raw PHI)
    op.create_table(
        "hcs_notification_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("appointment_id", sa.String(36), nullable=True),
        sa.Column("waitlist_id", sa.String(36), nullable=True),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("template_name", sa.String(100), nullable=False),
        sa.Column("recipient_phone_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("provider_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("channel IN ('whatsapp','sms')", name="ck_hcs_notif_channel"),
        sa.CheckConstraint("status IN ('sent','failed','delivered')", name="ck_hcs_notif_status"),
    )
    op.create_index("idx_hcs_notif_appt", "hcs_notification_log", ["appointment_id"])
    op.create_index("idx_hcs_notif_wl", "hcs_notification_log", ["waitlist_id"])


def downgrade() -> None:
    op.drop_table("hcs_notification_log")
    op.drop_table("hcs_waitlist")
    op.drop_table("hcs_appointments")
    op.drop_table("hcs_appointment_slots")
    op.drop_table("hcs_provider_schedules")
