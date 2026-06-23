"""
hcl_001_lab_tables

Revision ID: hcl001
Revises: hcp002
Create Date: 2026-06-21

Sprint 8: Laboratory tables — test panels catalog, lab orders, order lines,
specimens, and results.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "hcl001"
down_revision = "hcp002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. hcl_test_panels — branch-level test catalog
    # ------------------------------------------------------------------
    op.create_table(
        "hcl_test_panels",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "category",
            sa.String(50),
            nullable=False,
            server_default="other",
        ),  # hematology/chemistry/immunology/microbiology/urinalysis/other
        sa.Column("turnaround_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("unit_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="IDR"),
        sa.Column(
            "sample_type",
            sa.String(50),
            nullable=False,
            server_default="blood",
        ),  # blood/urine/stool/swab/tissue/other
        sa.Column("requires_fasting", sa.Boolean(), nullable=False, server_default="false"),
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
        # UNIQUE code per tenant
        sa.UniqueConstraint("tenant_id", "code", name="uq_hcl_test_panels_tenant_code"),
    )

    # ------------------------------------------------------------------
    # 2. hcl_lab_orders
    # ------------------------------------------------------------------
    op.create_table(
        "hcl_lab_orders",
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
            server_default="ordered",
        ),  # ordered/specimen_collected/processing/resulted/cancelled
        sa.Column(
            "priority",
            sa.String(10),
            nullable=False,
            server_default="routine",
        ),  # routine/urgent/stat
        sa.Column("clinical_notes", sa.Text(), nullable=True),
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
            ["encounter_id"], ["hc_encounters.id"], name="fk_hcl_orders_encounter"
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"], ["hc_patients.id"], name="fk_hcl_orders_patient"
        ),
        sa.ForeignKeyConstraint(
            ["provider_id"], ["hc_providers.id"], name="fk_hcl_orders_provider"
        ),
    )

    # ------------------------------------------------------------------
    # 3. hcl_order_lines
    # ------------------------------------------------------------------
    op.create_table(
        "hcl_order_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("order_id", sa.String(36), nullable=False),
        sa.Column("test_panel_id", sa.String(36), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),  # pending/collected/processing/resulted/cancelled
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["hcl_lab_orders.id"],
            name="fk_hcl_order_lines_order",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["test_panel_id"],
            ["hcl_test_panels.id"],
            name="fk_hcl_order_lines_panel",
        ),
    )

    # ------------------------------------------------------------------
    # 4. hcl_specimens
    # ------------------------------------------------------------------
    op.create_table(
        "hcl_specimens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("branch_id", sa.String(36), nullable=False),
        sa.Column("order_id", sa.String(36), nullable=False),
        sa.Column("sample_type", sa.String(50), nullable=False),
        sa.Column("collection_datetime", sa.DateTime(), nullable=True),
        sa.Column("collected_by", sa.String(36), nullable=True),
        sa.Column("barcode", sa.String(100), nullable=True, unique=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["order_id"], ["hcl_lab_orders.id"], name="fk_hcl_specimens_order"
        ),
    )

    # ------------------------------------------------------------------
    # 5. hcl_results
    # ------------------------------------------------------------------
    op.create_table(
        "hcl_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("order_id", sa.String(36), nullable=False),
        sa.Column("order_line_id", sa.String(36), nullable=False),
        sa.Column("test_panel_id", sa.String(36), nullable=False),
        sa.Column("result_value", sa.String(255), nullable=True),
        sa.Column("result_unit", sa.String(50), nullable=True),
        sa.Column("reference_range", sa.String(100), nullable=True),
        sa.Column("is_abnormal", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_critical", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resulted_by", sa.String(36), nullable=True),
        sa.Column("resulted_at", sa.DateTime(), nullable=True),
        sa.Column("shared_with_patient", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("released_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["order_id"], ["hcl_lab_orders.id"], name="fk_hcl_results_order"
        ),
        sa.ForeignKeyConstraint(
            ["order_line_id"], ["hcl_order_lines.id"], name="fk_hcl_results_order_line"
        ),
        sa.ForeignKeyConstraint(
            ["test_panel_id"], ["hcl_test_panels.id"], name="fk_hcl_results_panel"
        ),
    )


def downgrade() -> None:
    op.drop_table("hcl_results")
    op.drop_table("hcl_specimens")
    op.drop_table("hcl_order_lines")
    op.drop_table("hcl_lab_orders")
    op.drop_table("hcl_test_panels")
