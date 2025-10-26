"""Create token_blacklist table (PostgreSQL UNLOGGED)"""
from alembic import op
import sqlalchemy as sa

revision = "pg_c5d6e7f8g9h0"
down_revision = "pg_a1b2c3d4e5f6"
branch_labels = None
depends_on = None

def upgrade():
    # Create UNLOGGED table for better performance
    # UNLOGGED tables are faster but data is lost on crash (acceptable for token blacklist)
    op.execute("""
        CREATE UNLOGGED TABLE token_blacklist (
            jti VARCHAR(255) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            token_type VARCHAR(20) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            blacklisted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes for faster lookups
    op.create_index('ix_token_blacklist_jti', 'token_blacklist', ['jti'])
    op.create_index('ix_token_blacklist_user_id', 'token_blacklist', ['user_id'])
    op.create_index('ix_token_blacklist_expires_at', 'token_blacklist', ['expires_at'])

def downgrade():
    op.drop_index('ix_token_blacklist_expires_at', table_name='token_blacklist')
    op.drop_index('ix_token_blacklist_user_id', table_name='token_blacklist')
    op.drop_index('ix_token_blacklist_jti', table_name='token_blacklist')
    op.drop_table('token_blacklist')
