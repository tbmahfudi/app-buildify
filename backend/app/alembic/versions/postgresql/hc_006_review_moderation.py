"""
hc_006_review_moderation

Revision ID: hc006
Revises: hc005
Create Date: 2026-06-21

Adds moderation columns to hc_clinic_reviews:
  - status                 (already exists in model; added here for DB parity if not present)
  - response_text
  - response_at
  - moderation_released_at

Note: hc_clinic_reviews.status was created in hcs_001 with server_default
'pending_moderation'. This migration is a no-op for status but adds the
three new timestamp/text columns for the moderation workflow.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "hc006"
down_revision = "hc005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # status was added in the base table creation; guard with IF NOT EXISTS via raw SQL
    op.execute(
        "ALTER TABLE hc_clinic_reviews "
        "ADD COLUMN IF NOT EXISTS status VARCHAR(30) NOT NULL DEFAULT 'pending_moderation'"
    )
    op.execute(
        "ALTER TABLE hc_clinic_reviews "
        "ADD COLUMN IF NOT EXISTS response_text TEXT"
    )
    op.execute(
        "ALTER TABLE hc_clinic_reviews "
        "ADD COLUMN IF NOT EXISTS response_at TIMESTAMP"
    )
    op.execute(
        "ALTER TABLE hc_clinic_reviews "
        "ADD COLUMN IF NOT EXISTS moderation_released_at TIMESTAMP"
    )


def downgrade() -> None:
    op.drop_column("hc_clinic_reviews", "moderation_released_at")
    op.drop_column("hc_clinic_reviews", "response_at")
    op.drop_column("hc_clinic_reviews", "response_text")
    # Do not drop status — it was part of the original table definition
