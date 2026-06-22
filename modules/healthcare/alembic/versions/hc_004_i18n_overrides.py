"""
hc_004_i18n_overrides

Revision ID: hc004
Revises: hc003
Create Date: 2026-06-21

Creates hc_i18n_overrides table for per-tenant translation key overrides.
No PHI; no RLS needed (tenant_id enforced by platform TenantScopeListener).
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "hc004"
down_revision = "hc003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hc_i18n_overrides",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("translation_key", sa.String(255), nullable=False),
        sa.Column("translation_value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("locale IN ('id-ID','en-US')", name="ck_hc_i18n_overrides_locale"),
        sa.UniqueConstraint("tenant_id", "locale", "translation_key", name="uq_hc_i18n_overrides"),
    )
    op.create_index("idx_hc_i18n_overrides_tenant_locale", "hc_i18n_overrides", ["tenant_id", "locale"])
    op.create_index("idx_hc_i18n_overrides_created_at", "hc_i18n_overrides", ["created_at"])


def downgrade() -> None:
    op.drop_table("hc_i18n_overrides")
