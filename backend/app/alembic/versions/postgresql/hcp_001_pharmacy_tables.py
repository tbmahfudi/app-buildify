"""
hcp_001_pharmacy_tables

Revision ID: hcp001
Revises: hcb002
Create Date: 2026-06-21

Sprint 7: Pharmacy tables — medications catalog, drug interactions,
prescriptions, prescription lines, dispensing records.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "hcp001"
down_revision = "hcb002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. hcp_medications — branch-level medication catalog + stock
    # ------------------------------------------------------------------
    op.create_table(
        "hcp_medications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("generic_name", sa.String(255), nullable=True),
        sa.Column("brand_name", sa.String(255), nullable=True),
        sa.Column(
            "category",
            sa.String(50),
            nullable=False,
            server_default="other",
        ),  # antibiotic/analgesic/antihypertensive/vitamin/other
        sa.Column(
            "form",
            sa.String(50),
            nullable=False,
            server_default="tablet",
        ),  # tablet/capsule/syrup/injection/topical/other
        sa.Column("strength", sa.String(50), nullable=True),     # e.g. "500mg"
        sa.Column("unit", sa.String(20), nullable=False, server_default="tablet"),
        sa.Column("stock_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("minimum_stock", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("unit_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IDR"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["hc_branches.id"],
            name="fk_hcp_medications_branch_id",
        ),
    )
    op.create_index("idx_hcp_medications_tenant", "hcp_medications", ["tenant_id"])
    op.create_index(
        "idx_hcp_medications_branch",
        "hcp_medications",
        ["tenant_id", "branch_id"],
    )
    op.create_index(
        "idx_hcp_medications_category",
        "hcp_medications",
        ["tenant_id", "branch_id", "category"],
    )
    op.execute(
        "CREATE INDEX idx_hcp_medications_active ON hcp_medications "
        "(tenant_id, branch_id, is_active) WHERE is_active = true"
    )
    op.execute(
        "CREATE INDEX idx_hcp_medications_low_stock ON hcp_medications "
        "(tenant_id, branch_id, stock_quantity, minimum_stock) "
        "WHERE stock_quantity <= minimum_stock"
    )

    # ------------------------------------------------------------------
    # 2. hcp_drug_interactions — known interaction pairs (tenant-wide)
    # ------------------------------------------------------------------
    op.create_table(
        "hcp_drug_interactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("medication_a_id", sa.String(36), nullable=False),
        sa.Column("medication_b_id", sa.String(36), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),  # mild/moderate/severe
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["medication_a_id"],
            ["hcp_medications.id"],
            name="fk_hcp_drug_interactions_med_a",
        ),
        sa.ForeignKeyConstraint(
            ["medication_b_id"],
            ["hcp_medications.id"],
            name="fk_hcp_drug_interactions_med_b",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "medication_a_id",
            "medication_b_id",
            name="uq_hcp_drug_interactions_pair",
        ),
    )
    op.create_index(
        "idx_hcp_drug_interactions_tenant",
        "hcp_drug_interactions",
        ["tenant_id"],
    )
    op.create_index(
        "idx_hcp_drug_interactions_med_a",
        "hcp_drug_interactions",
        ["tenant_id", "medication_a_id"],
    )
    op.create_index(
        "idx_hcp_drug_interactions_med_b",
        "hcp_drug_interactions",
        ["tenant_id", "medication_b_id"],
    )

    # ------------------------------------------------------------------
    # 3. hcp_prescriptions — prescription header
    # ------------------------------------------------------------------
    op.create_table(
        "hcp_prescriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), nullable=False),
        sa.Column("encounter_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(36), nullable=False),
        sa.Column("provider_id", sa.String(36), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),  # pending/dispensed/partially_dispensed/cancelled
        sa.Column("notes", sa.Text(), nullable=True),  # internal only — not patient-visible
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["encounter_id"],
            ["hc_encounters.id"],
            name="fk_hcp_prescriptions_encounter_id",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["hc_patients.id"],
            name="fk_hcp_prescriptions_patient_id",
        ),
        sa.ForeignKeyConstraint(
            ["provider_id"],
            ["hc_providers.id"],
            name="fk_hcp_prescriptions_provider_id",
        ),
    )
    op.create_index(
        "idx_hcp_prescriptions_tenant",
        "hcp_prescriptions",
        ["tenant_id"],
    )
    op.create_index(
        "idx_hcp_prescriptions_branch",
        "hcp_prescriptions",
        ["tenant_id", "branch_id"],
    )
    op.create_index(
        "idx_hcp_prescriptions_patient",
        "hcp_prescriptions",
        ["tenant_id", "patient_id"],
    )
    op.create_index(
        "idx_hcp_prescriptions_encounter",
        "hcp_prescriptions",
        ["tenant_id", "encounter_id"],
    )
    op.create_index(
        "idx_hcp_prescriptions_status",
        "hcp_prescriptions",
        ["tenant_id", "branch_id", "status"],
    )

    # ------------------------------------------------------------------
    # 4. hcp_prescription_lines — individual medication lines
    # ------------------------------------------------------------------
    op.create_table(
        "hcp_prescription_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("prescription_id", sa.String(36), nullable=False),
        sa.Column("medication_id", sa.String(36), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("dosage_instructions", sa.String(255), nullable=True),
        sa.Column("days_supply", sa.Integer(), nullable=True),
        sa.Column("dispensed_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),  # pending/dispensed/cancelled
        sa.ForeignKeyConstraint(
            ["prescription_id"],
            ["hcp_prescriptions.id"],
            name="fk_hcp_prescription_lines_prescription_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["medication_id"],
            ["hcp_medications.id"],
            name="fk_hcp_prescription_lines_medication_id",
        ),
    )
    op.create_index(
        "idx_hcp_prescription_lines_prescription",
        "hcp_prescription_lines",
        ["prescription_id"],
    )
    op.create_index(
        "idx_hcp_prescription_lines_tenant",
        "hcp_prescription_lines",
        ["tenant_id"],
    )

    # ------------------------------------------------------------------
    # 5. hcp_dispensing_records — immutable dispense audit trail
    # ------------------------------------------------------------------
    op.create_table(
        "hcp_dispensing_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), nullable=False),
        sa.Column("prescription_id", sa.String(36), nullable=False),
        sa.Column("prescription_line_id", sa.String(36), nullable=False),
        sa.Column("medication_id", sa.String(36), nullable=False),
        sa.Column("quantity_dispensed", sa.Integer(), nullable=False),
        sa.Column("dispensed_by", sa.String(36), nullable=False),  # staff user_id
        sa.Column("dispensed_at", sa.DateTime(), nullable=False),
        sa.Column("batch_number", sa.String(50), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["prescription_id"],
            ["hcp_prescriptions.id"],
            name="fk_hcp_dispensing_records_prescription_id",
        ),
        sa.ForeignKeyConstraint(
            ["prescription_line_id"],
            ["hcp_prescription_lines.id"],
            name="fk_hcp_dispensing_records_line_id",
        ),
        sa.ForeignKeyConstraint(
            ["medication_id"],
            ["hcp_medications.id"],
            name="fk_hcp_dispensing_records_medication_id",
        ),
    )
    op.create_index(
        "idx_hcp_dispensing_records_prescription",
        "hcp_dispensing_records",
        ["tenant_id", "prescription_id"],
    )
    op.create_index(
        "idx_hcp_dispensing_records_branch",
        "hcp_dispensing_records",
        ["tenant_id", "branch_id"],
    )

    # ------------------------------------------------------------------
    # Grants
    # ------------------------------------------------------------------
    # Ensure application roles exist on a fresh DB before granting (GH#678).
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
                CREATE ROLE app_user NOLOGIN;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_readonly_role') THEN
                CREATE ROLE app_readonly_role NOLOGIN;
            END IF;
        END
        $$;
        """
    )
    for table in (
        "hcp_medications",
        "hcp_drug_interactions",
        "hcp_prescriptions",
        "hcp_prescription_lines",
        "hcp_dispensing_records",
    ):
        op.execute(f"GRANT SELECT ON {table} TO app_readonly_role;")
        op.execute(f"GRANT INSERT, UPDATE ON {table} TO app_user;")


def downgrade() -> None:
    op.drop_table("hcp_dispensing_records")
    op.drop_table("hcp_prescription_lines")
    op.drop_table("hcp_prescriptions")
    op.drop_table("hcp_drug_interactions")
    op.drop_table("hcp_medications")
