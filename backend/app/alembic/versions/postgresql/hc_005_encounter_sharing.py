"""
hc_005_encounter_sharing

Revision ID: hc005
Revises: hcs001
Create Date: 2026-06-21

Adds shared_with_patient flag to hc_encounters.
Revision chain: ... → hc004 → hcs001 → hc005
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "hc005"
down_revision = "hcs001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "hc_encounters",
        sa.Column(
            "shared_with_patient",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("hc_encounters", "shared_with_patient")
