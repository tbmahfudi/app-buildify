"""E1 Document Core: folders + version history.

Adds dms_folders (nested, tenant-scoped) and dms_document_versions (full history
per document), and links documents to a folder.

Revision ID: dms_002
Revises: dms_001
Create Date: 2026-07-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "dms_002"
down_revision = "dms_001"
branch_labels = None
depends_on = None


def _tenant_rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY {table}_tenant_isolation ON {table}
        USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """
    )


def upgrade() -> None:
    # --- folders --------------------------------------------------------------
    op.create_table(
        "dms_folders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dms_folders.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_dms_folders_tenant", "dms_folders", ["tenant_id"])
    op.create_index("ix_dms_folders_parent", "dms_folders", ["tenant_id", "parent_id"])
    # No two active sibling folders with the same name. parent_id is coalesced to
    # a sentinel because NULL values are distinct in a unique index, which would
    # otherwise let duplicate root-level folders through.
    op.execute(
        "CREATE UNIQUE INDEX uq_dms_folders_sibling_name ON dms_folders "
        "(tenant_id, COALESCE(parent_id, '00000000-0000-0000-0000-000000000000'::uuid), name) "
        "WHERE is_active"
    )
    _tenant_rls("dms_folders")

    # --- documents.folder_id --------------------------------------------------
    op.add_column(
        "dms_documents",
        sa.Column(
            "folder_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dms_folders.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_dms_documents_folder", "dms_documents", ["tenant_id", "folder_id"]
    )

    # --- version history ------------------------------------------------------
    op.create_table(
        "dms_document_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dms_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("change_comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_dms_versions_document",
        "dms_document_versions",
        ["tenant_id", "document_id", "version_no"],
    )
    op.create_index(
        "uq_dms_versions_doc_no",
        "dms_document_versions",
        ["document_id", "version_no"],
        unique=True,
    )
    _tenant_rls("dms_document_versions")

    # Backfill: every existing document gets a v1 history row from its current blob.
    op.execute(
        """
        INSERT INTO dms_document_versions
            (id, tenant_id, document_id, version_no, filename, content_type,
             size_bytes, storage_key, uploaded_by, change_comment, created_at)
        SELECT gen_random_uuid(), tenant_id, id, current_version, filename,
               content_type, size_bytes, storage_key, uploaded_by,
               'Initial version', created_at
        FROM dms_documents
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS dms_document_versions_tenant_isolation ON dms_document_versions")
    op.drop_table("dms_document_versions")
    op.drop_index("ix_dms_documents_folder", table_name="dms_documents")
    op.drop_column("dms_documents", "folder_id")
    op.execute("DROP POLICY IF EXISTS dms_folders_tenant_isolation ON dms_folders")
    op.drop_table("dms_folders")
