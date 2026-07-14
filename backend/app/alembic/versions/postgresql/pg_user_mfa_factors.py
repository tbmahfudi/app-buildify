"""Create user_mfa_factors (ADR-011 S3 — optional OTP MFA)

Revision ID: pg_user_mfa_factors
Revises: pg_merge_username_tmd
Create Date: 2026-07-14

Optional second-factor enrollment for platform users (phone/email OTP; TOTP
reserved via the open factor_type string). No credential/secret is stored here —
only the factor type, delivery target, and verification state. MySQL parity is
deferred to GH#669 (the MySQL tree has multiple unmerged heads; adding one there
now would create another).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "pg_user_mfa_factors"
down_revision = "pg_merge_username_tmd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_mfa_factors",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("factor_type", sa.String(20), nullable=False),  # phone_otp | email_otp (TOTP later)
        sa.Column("target", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_user_mfa_factors_user_id", ondelete="CASCADE"
        ),
        sa.UniqueConstraint("user_id", "factor_type", "target", name="uq_user_mfa_factor"),
    )
    op.create_index("idx_user_mfa_factors_user", "user_mfa_factors", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_user_mfa_factors_user", table_name="user_mfa_factors")
    op.drop_table("user_mfa_factors")
