"""
hc_003_audit_log_permissions

Revision ID: hc003
Revises: hc002
Create Date: 2026-06-21

Sets INSERT-only DB grants on hc_audit_log. Creates pg rules to block
UPDATE and DELETE as an additional enforcement layer (belt-and-suspenders).
"""
from __future__ import annotations

from alembic import op

revision = "hc003"
down_revision = "hc002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Revoke UPDATE and DELETE from application roles
    op.execute("REVOKE UPDATE, DELETE ON hc_audit_log FROM app_user;")
    op.execute("REVOKE UPDATE, DELETE ON hc_audit_log FROM app_readonly_role;")

    # Grant INSERT only to app_user; SELECT to app_readonly_role
    op.execute("GRANT INSERT ON hc_audit_log TO app_user;")
    op.execute("GRANT SELECT ON hc_audit_log TO app_readonly_role;")

    # Belt-and-suspenders: pg rules that silently discard UPDATE/DELETE attempts
    op.execute(
        "CREATE OR REPLACE RULE no_update_audit_log AS "
        "ON UPDATE TO hc_audit_log DO INSTEAD NOTHING;"
    )
    op.execute(
        "CREATE OR REPLACE RULE no_delete_audit_log AS "
        "ON DELETE TO hc_audit_log DO INSTEAD NOTHING;"
    )


def downgrade() -> None:
    op.execute("DROP RULE IF EXISTS no_delete_audit_log ON hc_audit_log;")
    op.execute("DROP RULE IF EXISTS no_update_audit_log ON hc_audit_log;")

    # Restore original grants (platform defaults)
    op.execute("GRANT UPDATE, DELETE ON hc_audit_log TO app_user;")
    op.execute("GRANT UPDATE, DELETE ON hc_audit_log TO app_readonly_role;")
