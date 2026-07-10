"""Add users.username + must_set_password login fields (ADR-HC-009 D1/D7)

Adds the columns and partial unique index that back username-or-email login
and the legacy-patient password-migration flag. These were applied ad-hoc to
the shared dev appdb; this revision captures them so fresh environments match.

Idempotent (IF NOT EXISTS) so it no-ops on databases where the columns already
exist.

Revision ID: pg_add_user_username_login
Revises: normalize_tenant_codes
Create Date: 2026-07-10
"""
from alembic import op


revision = 'pg_add_user_username_login'
down_revision = 'normalize_tenant_codes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Optional case-insensitive login identifier (ADR-HC-009 D1).
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(50)"
    )
    # Migration flag (ADR-HC-009 D7): legacy patients must set a password.
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS must_set_password "
        "BOOLEAN NOT NULL DEFAULT false"
    )
    # Case-insensitive uniqueness on username, ignoring NULLs.
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_username_lower "
        "ON users (lower(username)) WHERE username IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_users_username_lower")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS must_set_password")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS username")
