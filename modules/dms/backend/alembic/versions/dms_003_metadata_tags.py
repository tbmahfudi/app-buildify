"""E1 F1.4: tags + custom metadata on documents.

Adds `tags text[]` (GIN-indexed for findability / future full-text search) and
`doc_metadata jsonb` (arbitrary custom fields) to dms_documents.

Revision ID: dms_003
Revises: dms_002
Create Date: 2026-07-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "dms_003"
down_revision = "dms_002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "dms_documents",
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "dms_documents",
        sa.Column(
            "doc_metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.create_index(
        "ix_dms_documents_tags", "dms_documents", ["tags"], postgresql_using="gin"
    )


def downgrade() -> None:
    op.drop_index("ix_dms_documents_tags", table_name="dms_documents")
    op.drop_column("dms_documents", "doc_metadata")
    op.drop_column("dms_documents", "tags")
