"""Create user_trusted_devices (ADR-HC-009 D4 — remembered-device store)

Revision ID: pg_user_trusted_devices
Revises: pg_user_mfa_factors
Create Date: 2026-07-15

Lets a browser that already cleared an MFA challenge skip the second factor for a
bounded window (30 days). Only the HMAC of the device secret is stored — the raw
secret lives solely in a signed HttpOnly cookie — so this table alone is not
replayable. Not PHI; keyed on the platform user, not a tenant.

MySQL parity is deferred to GH#669 (the MySQL tree has multiple unmerged heads and
two missing revision files; adding one there now would deepen the break), matching
the precedent set by pg_user_mfa_factors.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "pg_user_trusted_devices"
down_revision = "pg_user_mfa_factors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_trusted_devices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("device_hash", sa.String(255), nullable=False),  # HMAC-SHA256, never the secret
        sa.Column("label", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_trusted_devices_user_id", ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "device_hash", name="uq_user_trusted_devices_hash"),
    )
    op.create_index("idx_user_trusted_devices_user", "user_trusted_devices", ["user_id"])
    # Login-time lookup: a live, non-revoked trust for this user.
    op.create_index(
        "idx_user_trusted_devices_active",
        "user_trusted_devices",
        ["user_id", "expires_at"],
        postgresql_where=sa.text("revoked_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_user_trusted_devices_active", table_name="user_trusted_devices")
    op.drop_index("idx_user_trusted_devices_user", table_name="user_trusted_devices")
    op.drop_table("user_trusted_devices")
