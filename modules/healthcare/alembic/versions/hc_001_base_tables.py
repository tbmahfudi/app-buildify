"""
hc_001_base_tables

Revision ID: hc001
Revises: pg_unify_module_system (platform head — confirm with platform team)
Create Date: 2026-06-21

Wave 1: Create all Healthcare base module tables.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "hc001"
down_revision = None  # Set to platform pg_unify_module_system revision ID before running
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. hc_branches — Branch registry per tenant (no branch_id on itself)
    # ------------------------------------------------------------------
    op.create_table(
        "hc_branches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("address_street", sa.String(500), nullable=False),
        sa.Column("address_city", sa.String(100), nullable=False),
        sa.Column("address_province", sa.String(100), nullable=False),
        sa.Column("address_postal_code", sa.String(10), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="Asia/Jakarta"),
        sa.Column("contact_phone", sa.String(30), nullable=False),
        sa.Column("operating_hours", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("online_booking", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("default_locale", sa.String(10), nullable=False, server_default="id-ID"),
        sa.Column("appointment_types", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('active','inactive','suspended')", name="ck_hc_branches_status"),
        sa.CheckConstraint("default_locale IN ('id-ID','en-US')", name="ck_hc_branches_locale"),
    )
    op.create_index("idx_hc_branches_tenant_id", "hc_branches", ["tenant_id"])
    op.create_index("idx_hc_branches_tenant_slug", "hc_branches", ["tenant_id", "slug"], unique=True)
    op.create_index("idx_hc_branches_status", "hc_branches", ["tenant_id", "status"])
    op.create_index("idx_hc_branches_created_at", "hc_branches", ["created_at"])

    # ------------------------------------------------------------------
    # 2. hc_providers — Doctors/nurses per branch (depends on hc_branches)
    # ------------------------------------------------------------------
    op.create_table(
        "hc_providers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("provider_type", sa.String(30), nullable=False),
        sa.Column("specialty", sa.String(100), nullable=True),
        sa.Column("license_number", sa.String(50), nullable=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["branch_id"], ["hc_branches.id"], name="fk_hc_providers_branch_id"),
        sa.CheckConstraint(
            "provider_type IN ('doctor','nurse','pharmacist','lab_tech','billing_staff')",
            name="ck_hc_providers_type",
        ),
        sa.UniqueConstraint("tenant_id", "branch_id", "user_id", name="uq_hc_providers_tenant_branch_user"),
    )
    op.create_index("idx_hc_providers_tenant_id", "hc_providers", ["tenant_id"])
    op.create_index("idx_hc_providers_branch_id", "hc_providers", ["tenant_id", "branch_id"])
    op.create_index("idx_hc_providers_user_id", "hc_providers", ["user_id"])
    op.create_index("idx_hc_providers_created_at", "hc_providers", ["created_at"])
    op.execute(
        "CREATE INDEX idx_hc_providers_specialty ON hc_providers (tenant_id, branch_id, specialty) "
        "WHERE specialty IS NOT NULL"
    )

    # ------------------------------------------------------------------
    # 3. hc_branch_staff — Staff ↔ branch assignments (depends on hc_branches)
    # ------------------------------------------------------------------
    op.create_table(
        "hc_branch_staff",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), nullable=True),  # NULL = clinic_owner cross-branch sentinel
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("invitation_token", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("invited_at", sa.DateTime(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["branch_id"], ["hc_branches.id"], name="fk_hc_branch_staff_branch_id"),
        sa.CheckConstraint(
            "role IN ('clinic_owner','branch_manager','doctor','nurse','pharmacist','lab_tech','billing_staff')",
            name="ck_hc_branch_staff_role",
        ),
        sa.CheckConstraint(
            "status IN ('pending','active','revoked')",
            name="ck_hc_branch_staff_status",
        ),
        sa.UniqueConstraint("tenant_id", "branch_id", "user_id", "role", name="uq_hc_branch_staff"),
    )
    op.create_index("idx_hc_branch_staff_tenant_id", "hc_branch_staff", ["tenant_id"])
    op.create_index("idx_hc_branch_staff_user_id", "hc_branch_staff", ["user_id", "tenant_id"])
    op.create_index("idx_hc_branch_staff_role", "hc_branch_staff", ["tenant_id", "branch_id", "role"])
    op.create_index("idx_hc_branch_staff_created_at", "hc_branch_staff", ["created_at"])
    op.execute(
        "CREATE INDEX idx_hc_branch_staff_branch_id ON hc_branch_staff (branch_id) "
        "WHERE branch_id IS NOT NULL"
    )

    # ------------------------------------------------------------------
    # 4. hc_patients — Tenant-wide patient profiles [PHI]
    # ------------------------------------------------------------------
    op.create_table(
        "hc_patients",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        # PHI columns stored as Text — EncryptedPHIType encrypts at ORM layer
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("date_of_birth", sa.Text(), nullable=False),
        sa.Column("phone", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("gender", sa.String(10), nullable=False),
        sa.Column("nik", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("locale", sa.String(10), nullable=False, server_default="id-ID"),
        sa.Column("consent_version", sa.String(20), nullable=False),
        sa.Column("consent_accepted_at", sa.DateTime(), nullable=False),
        sa.Column("consent_ip", sa.String(45), nullable=False),
        sa.Column("consent_user_agent", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("gender IN ('male','female','other')", name="ck_hc_patients_gender"),
        sa.CheckConstraint("status IN ('active','suspended','deleted')", name="ck_hc_patients_status"),
    )
    op.create_index("idx_hc_patients_tenant_id", "hc_patients", ["tenant_id"])
    op.create_index("idx_hc_patients_created_at", "hc_patients", ["created_at"])
    op.create_index("idx_hc_patients_status", "hc_patients", ["tenant_id", "status"])

    # ------------------------------------------------------------------
    # 5. hc_patient_consents — DPA/consent records (depends on hc_patients)
    # ------------------------------------------------------------------
    op.create_table(
        "hc_patient_consents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(36), nullable=False),
        sa.Column("consent_type", sa.String(50), nullable=False),
        sa.Column("consent_version", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("accepted_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("ip", sa.String(45), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=False),
        sa.Column("purpose_description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["patient_id"], ["hc_patients.id"], name="fk_hc_patient_consents_patient_id"),
        sa.CheckConstraint(
            "consent_type IN ('dpa_acceptance','data_processing','marketing')",
            name="ck_hc_patient_consents_type",
        ),
        sa.CheckConstraint(
            "status IN ('active','revoked')",
            name="ck_hc_patient_consents_status",
        ),
    )
    op.create_index("idx_hc_patient_consents_tenant_id", "hc_patient_consents", ["tenant_id"])
    op.create_index("idx_hc_patient_consents_patient_id", "hc_patient_consents", ["patient_id"])
    op.create_index("idx_hc_patient_consents_status", "hc_patient_consents", ["patient_id", "status"])
    op.create_index("idx_hc_patient_consents_created_at", "hc_patient_consents", ["created_at"])

    # ------------------------------------------------------------------
    # 6. hc_encounters — Clinical encounters [PHI] (depends on branches, patients, providers)
    # ------------------------------------------------------------------
    op.create_table(
        "hc_encounters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(36), nullable=False),
        sa.Column("provider_id", sa.String(36), nullable=False),
        sa.Column("appointment_id", sa.String(36), nullable=True),  # deferred FK added in hcs001
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        # PHI encrypted columns (stored as Text; EncryptedPHIType applied at ORM layer)
        sa.Column("soap_subjective", sa.Text(), nullable=True),
        sa.Column("soap_objective", sa.Text(), nullable=True),
        sa.Column("soap_assessment", sa.Text(), nullable=True),
        sa.Column("soap_plan", sa.Text(), nullable=True),
        sa.Column("soap_notes", sa.Text(), nullable=True),
        sa.Column("patient_summary", sa.Text(), nullable=True),
        sa.Column("summary_released", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("summary_released_at", sa.DateTime(), nullable=True),
        sa.Column("amendment_of_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["branch_id"], ["hc_branches.id"], name="fk_hc_encounters_branch_id"),
        sa.ForeignKeyConstraint(["patient_id"], ["hc_patients.id"], name="fk_hc_encounters_patient_id"),
        sa.ForeignKeyConstraint(["provider_id"], ["hc_providers.id"], name="fk_hc_encounters_provider_id"),
        sa.ForeignKeyConstraint(["amendment_of_id"], ["hc_encounters.id"], name="fk_hc_encounters_amendment_of"),
        sa.CheckConstraint(
            "status IN ('open','in_progress','completed','cancelled')",
            name="ck_hc_encounters_status",
        ),
    )
    op.create_index("idx_hc_encounters_tenant_branch", "hc_encounters", ["tenant_id", "branch_id"])
    op.create_index("idx_hc_encounters_patient_id", "hc_encounters", ["tenant_id", "patient_id"])
    op.create_index("idx_hc_encounters_provider_id", "hc_encounters", ["branch_id", "provider_id"])
    op.create_index("idx_hc_encounters_status", "hc_encounters", ["tenant_id", "branch_id", "status"])
    op.create_index("idx_hc_encounters_started_at", "hc_encounters", ["tenant_id", "branch_id", "started_at"])
    op.create_index("idx_hc_encounters_created_at", "hc_encounters", ["created_at"])

    # ------------------------------------------------------------------
    # 7. hc_audit_log — Append-only PHI access audit (no FKs; standalone)
    # ------------------------------------------------------------------
    op.create_table(
        "hc_audit_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("actor_type", sa.String(20), nullable=False),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), nullable=True),  # NULL for tenant-wide events
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=False),
        sa.Column("source_module", sa.String(50), nullable=False),
        sa.Column("phi_accessed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("actor_type IN ('staff','patient','system')", name="ck_hc_audit_log_actor_type"),
    )
    op.create_index("idx_hc_audit_log_tenant_id", "hc_audit_log", ["tenant_id", "created_at"])
    op.create_index("idx_hc_audit_log_actor_id", "hc_audit_log", ["actor_id", "created_at"])
    op.create_index("idx_hc_audit_log_resource", "hc_audit_log", ["resource_type", "resource_id"])
    op.create_index("idx_hc_audit_log_event_type", "hc_audit_log", ["tenant_id", "event_type", "created_at"])
    op.create_index("idx_hc_audit_log_created_at", "hc_audit_log", ["created_at"])

    # ------------------------------------------------------------------
    # 8. hc_clinic_reviews — Patient reviews per branch (depends on branches, patients, encounters)
    # ------------------------------------------------------------------
    op.create_table(
        "hc_clinic_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(36), nullable=False),
        sa.Column("encounter_id", sa.String(36), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending_moderation"),
        sa.Column("moderated_at", sa.DateTime(), nullable=True),
        sa.Column("moderated_by", sa.String(36), nullable=True),
        sa.Column("staff_response", sa.Text(), nullable=True),
        sa.Column("staff_response_at", sa.DateTime(), nullable=True),
        sa.Column("staff_response_by", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["branch_id"], ["hc_branches.id"], name="fk_hc_clinic_reviews_branch_id"),
        sa.ForeignKeyConstraint(["patient_id"], ["hc_patients.id"], name="fk_hc_clinic_reviews_patient_id"),
        sa.ForeignKeyConstraint(["encounter_id"], ["hc_encounters.id"], name="fk_hc_clinic_reviews_encounter_id"),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_hc_clinic_reviews_rating"),
        sa.CheckConstraint(
            "status IN ('pending_moderation','approved','removed')",
            name="ck_hc_clinic_reviews_status",
        ),
        sa.UniqueConstraint("encounter_id", name="uq_hc_clinic_reviews_encounter"),
    )
    op.create_index("idx_hc_clinic_reviews_tenant_id", "hc_clinic_reviews", ["tenant_id"])
    op.create_index("idx_hc_clinic_reviews_branch_status", "hc_clinic_reviews", ["branch_id", "status", "created_at"])
    op.create_index("idx_hc_clinic_reviews_patient_id", "hc_clinic_reviews", ["patient_id"])
    op.create_index("idx_hc_clinic_reviews_created_at", "hc_clinic_reviews", ["created_at"])


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("hc_clinic_reviews")

    op.drop_index("idx_hc_audit_log_created_at", table_name="hc_audit_log")
    op.drop_index("idx_hc_audit_log_event_type", table_name="hc_audit_log")
    op.drop_index("idx_hc_audit_log_resource", table_name="hc_audit_log")
    op.drop_index("idx_hc_audit_log_actor_id", table_name="hc_audit_log")
    op.drop_index("idx_hc_audit_log_tenant_id", table_name="hc_audit_log")
    op.drop_table("hc_audit_log")

    op.drop_table("hc_encounters")
    op.drop_table("hc_patient_consents")
    op.drop_table("hc_patients")
    op.drop_table("hc_branch_staff")
    op.drop_table("hc_providers")
    op.drop_table("hc_branches")
