"""
hcb_001_billing_tables

Revision ID: hcb001
Revises: hcs002
Create Date: 2026-06-21

Wave 3: Healthcare billing tables.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "hcb001"
down_revision = "hcs002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. hcb_service_items
    # ------------------------------------------------------------------
    op.create_table(
        "hcb_service_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("unit_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IDR"),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["branch_id"], ["hc_branches.id"], name="fk_hcb_service_items_branch_id"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_hcb_service_items_tenant_code"),
    )
    op.create_index("idx_hcb_service_items_tenant_id", "hcb_service_items", ["tenant_id"])
    op.create_index("idx_hcb_service_items_branch_id", "hcb_service_items", ["tenant_id", "branch_id"])
    op.create_index("idx_hcb_service_items_category", "hcb_service_items", ["tenant_id", "category"])
    op.execute(
        "CREATE INDEX idx_hcb_service_items_active ON hcb_service_items (tenant_id, branch_id, is_active) "
        "WHERE is_active = true"
    )

    # ------------------------------------------------------------------
    # 2. hcb_insurance_profiles
    # ------------------------------------------------------------------
    op.create_table(
        "hcb_insurance_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(36), nullable=False),
        sa.Column("insurance_type", sa.String(50), nullable=False),
        sa.Column("insurance_number", sa.Text(), nullable=True),  # Fernet-encrypted
        sa.Column("provider_name", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["patient_id"], ["hc_patients.id"], name="fk_hcb_insurance_profiles_patient_id"),
        sa.CheckConstraint(
            "insurance_type IN ('bpjs','private','none')",
            name="ck_hcb_insurance_profiles_type",
        ),
    )
    op.create_index("idx_hcb_insurance_profiles_tenant_id", "hcb_insurance_profiles", ["tenant_id"])
    op.create_index("idx_hcb_insurance_profiles_patient_id", "hcb_insurance_profiles", ["patient_id"])

    # ------------------------------------------------------------------
    # 3. hcb_invoices
    # ------------------------------------------------------------------
    op.create_table(
        "hcb_invoices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(36), nullable=False),
        sa.Column("encounter_id", sa.String(36), nullable=True),
        sa.Column("invoice_number", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IDR"),
        sa.Column("insurance_profile_id", sa.String(36), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("finalized_at", sa.DateTime(), nullable=True),
        sa.Column("voided_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["patient_id"], ["hc_patients.id"], name="fk_hcb_invoices_patient_id"),
        sa.ForeignKeyConstraint(["encounter_id"], ["hc_encounters.id"], name="fk_hcb_invoices_encounter_id"),
        sa.ForeignKeyConstraint(
            ["insurance_profile_id"],
            ["hcb_insurance_profiles.id"],
            name="fk_hcb_invoices_insurance_profile_id",
        ),
        sa.UniqueConstraint("invoice_number", name="uq_hcb_invoices_invoice_number"),
        sa.CheckConstraint(
            "status IN ('draft','finalized','void')",
            name="ck_hcb_invoices_status",
        ),
    )
    op.create_index("idx_hcb_invoices_tenant_id", "hcb_invoices", ["tenant_id"])
    op.create_index("idx_hcb_invoices_branch_id", "hcb_invoices", ["tenant_id", "branch_id"])
    op.create_index("idx_hcb_invoices_patient_id", "hcb_invoices", ["tenant_id", "patient_id"])
    op.create_index("idx_hcb_invoices_status", "hcb_invoices", ["tenant_id", "branch_id", "status"])
    op.create_index("idx_hcb_invoices_created_at", "hcb_invoices", ["created_at"])

    # ------------------------------------------------------------------
    # 4. hcb_invoice_lines
    # ------------------------------------------------------------------
    op.create_table(
        "hcb_invoice_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("invoice_id", sa.String(36), nullable=False),
        sa.Column("service_item_id", sa.String(36), nullable=True),
        sa.Column("item_name", sa.String(255), nullable=False),
        sa.Column("item_code", sa.String(50), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(15, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["hcb_invoices.id"],
            ondelete="CASCADE",
            name="fk_hcb_invoice_lines_invoice_id",
        ),
        sa.ForeignKeyConstraint(
            ["service_item_id"],
            ["hcb_service_items.id"],
            name="fk_hcb_invoice_lines_service_item_id",
        ),
    )
    op.create_index("idx_hcb_invoice_lines_invoice_id", "hcb_invoice_lines", ["invoice_id"])
    op.create_index("idx_hcb_invoice_lines_service_item_id", "hcb_invoice_lines", ["service_item_id"])

    # ------------------------------------------------------------------
    # 5. hcb_payments
    # ------------------------------------------------------------------
    op.create_table(
        "hcb_payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("invoice_id", sa.String(36), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IDR"),
        sa.Column("payment_method", sa.String(50), nullable=False),
        sa.Column("payment_date", sa.DateTime(), nullable=False),
        sa.Column("reference_number", sa.String(100), nullable=True),
        sa.Column("recorded_by", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["hcb_invoices.id"],
            name="fk_hcb_payments_invoice_id",
        ),
        sa.CheckConstraint(
            "payment_method IN ('cash','transfer','bpjs','insurance','other')",
            name="ck_hcb_payments_method",
        ),
    )
    op.create_index("idx_hcb_payments_tenant_id", "hcb_payments", ["tenant_id"])
    op.create_index("idx_hcb_payments_invoice_id", "hcb_payments", ["invoice_id"])
    op.create_index("idx_hcb_payments_payment_date", "hcb_payments", ["payment_date"])

    # ------------------------------------------------------------------
    # 6. hcb_bpjs_exports
    # ------------------------------------------------------------------
    op.create_table(
        "hcb_bpjs_exports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), nullable=False),
        sa.Column("export_period", sa.String(7), nullable=False),  # YYYY-MM
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("file_reference", sa.String(500), nullable=True),  # base64 content
        sa.Column("record_count", sa.Integer(), nullable=True),
        sa.Column("total_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "status IN ('pending','generated','submitted')",
            name="ck_hcb_bpjs_exports_status",
        ),
    )
    op.create_index("idx_hcb_bpjs_exports_tenant_id", "hcb_bpjs_exports", ["tenant_id"])
    op.create_index("idx_hcb_bpjs_exports_branch_id", "hcb_bpjs_exports", ["tenant_id", "branch_id"])
    op.create_index("idx_hcb_bpjs_exports_period", "hcb_bpjs_exports", ["tenant_id", "branch_id", "export_period"])


def downgrade() -> None:
    op.drop_table("hcb_bpjs_exports")
    op.drop_table("hcb_payments")
    op.drop_table("hcb_invoice_lines")
    op.drop_table("hcb_invoices")
    op.drop_table("hcb_insurance_profiles")
    op.drop_table("hcb_service_items")
