"""E4: document expiry + reminder tracking.

Adds `expires_at` (when a document expires) and `expiry_reminder_window` (the
smallest reminder window already fired for it: 30/7/1/0 days, NULL = none) so the
daily scan reminds at most once per window.

Revision ID: dms_009
Revises: dms_008
Create Date: 2026-07-25
"""
from alembic import op
import sqlalchemy as sa

revision = "dms_009"
down_revision = "dms_008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("dms_documents", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("dms_documents", sa.Column("expiry_reminder_window", sa.Integer(), nullable=True))
    # Partial index: the scan only cares about documents that actually expire.
    op.execute(
        "CREATE INDEX ix_dms_documents_expiry ON dms_documents (expires_at) "
        "WHERE expires_at IS NOT NULL AND is_active"
    )


def downgrade() -> None:
    op.drop_index("ix_dms_documents_expiry", table_name="dms_documents")
    op.drop_column("dms_documents", "expiry_reminder_window")
    op.drop_column("dms_documents", "expires_at")
