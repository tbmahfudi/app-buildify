"""E2 Search & Discovery: full-text search vector over document metadata.

Adds a `search_vector tsvector` to dms_documents, maintained by a trigger over
filename + tags + custom metadata (document *content* extraction/OCR is deferred),
and a GIN index for ranked full-text queries.

Revision ID: dms_007
Revises: dms_006
Create Date: 2026-07-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "dms_007"
down_revision = "dms_006"
branch_labels = None
depends_on = None

# Filenames tokenize poorly ("quarterly-report-zephyr.pdf" is one compound token),
# so split on non-alphanumerics before indexing → "zephyr" becomes searchable.
_VECTOR_EXPR = (
    "to_tsvector('english', "
    "coalesce(regexp_replace({p}filename, '[^a-zA-Z0-9]+', ' ', 'g'),'') || ' ' || "
    "coalesce(array_to_string({p}tags, ' '), '') || ' ' || "
    "coalesce({p}doc_metadata::text, ''))"
)


def upgrade() -> None:
    op.add_column("dms_documents", sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True))
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION dms_documents_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := {_VECTOR_EXPR.format(p='NEW.')};
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER dms_documents_search_vector_trg
        BEFORE INSERT OR UPDATE ON dms_documents
        FOR EACH ROW EXECUTE FUNCTION dms_documents_search_vector_update();
        """
    )
    op.create_index(
        "ix_dms_documents_search", "dms_documents", ["search_vector"], postgresql_using="gin"
    )
    # Backfill existing rows.
    op.execute(f"UPDATE dms_documents SET search_vector = {_VECTOR_EXPR.format(p='')}")


def downgrade() -> None:
    op.drop_index("ix_dms_documents_search", table_name="dms_documents")
    op.execute("DROP TRIGGER IF EXISTS dms_documents_search_vector_trg ON dms_documents")
    op.execute("DROP FUNCTION IF EXISTS dms_documents_search_vector_update()")
    op.drop_column("dms_documents", "search_vector")
