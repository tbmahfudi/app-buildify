"""Normalize tenant codes to uppercase and add functional index

Revision ID: normalize_tenant_codes
Revises: hc006, hcl002, ee55ff66aa77
"""
from __future__ import annotations
import sqlalchemy as sa
from alembic import op

revision = "normalize_tenant_codes"
down_revision = ("hc006", "hcl002", "ee55ff66aa77")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE tenants SET code = UPPER(code)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_tenants_code_lower "
        "ON tenants (lower(code))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tenants_code_lower")
