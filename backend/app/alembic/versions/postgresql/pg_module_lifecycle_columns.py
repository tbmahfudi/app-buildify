"""Add install_status, install_error_message, visibility to modules table

Revision ID: pg_module_lifecycle_columns
Revises: pg_week3_field_enhancements
Create Date: 2026-06-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "pg_module_lifecycle_columns"
down_revision = "pg_week3_field_enhancements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "modules",
        sa.Column(
            "install_status",
            sa.String(30),
            nullable=False,
            server_default="ready",
        ),
    )
    op.add_column(
        "modules",
        sa.Column("install_error_message", sa.Text, nullable=True),
    )
    op.add_column(
        "modules",
        sa.Column(
            "visibility",
            sa.String(20),
            nullable=False,
            server_default="all_tenants",
        ),
    )
    op.create_check_constraint(
        "ck_modules_install_status",
        "modules",
        "install_status IN ('in_progress', 'ready', 'failed', 'deactivation_pending')",
    )
    op.create_check_constraint(
        "ck_modules_visibility",
        "modules",
        "visibility IN ('all_tenants', 'whitelist', 'hidden')",
    )
    op.create_index("ix_modules_install_status", "modules", ["install_status"])
    op.create_index("ix_modules_visibility", "modules", ["visibility"])


def downgrade() -> None:
    op.drop_index("ix_modules_visibility", table_name="modules")
    op.drop_index("ix_modules_install_status", table_name="modules")
    op.drop_constraint("ck_modules_visibility", "modules", type_="check")
    op.drop_constraint("ck_modules_install_status", "modules", type_="check")
    op.drop_column("modules", "visibility")
    op.drop_column("modules", "install_error_message")
    op.drop_column("modules", "install_status")
