"""Create token_blacklist table (MySQL MEMORY)"""
from alembic import op
import sqlalchemy as sa

revision = "mysql_d7e8f9g0h1i2"
down_revision = "mysql_f6e5d4c3b2a1"
branch_labels = None
depends_on = None

def upgrade():
    # Create MEMORY table for better performance
    # MEMORY tables are stored in RAM and provide fast access
    # Data is lost on restart (acceptable for token blacklist as tokens expire anyway)
    op.execute("""
        CREATE TABLE token_blacklist (
            jti VARCHAR(255) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            token_type VARCHAR(20) NOT NULL,
            expires_at DATETIME NOT NULL,
            blacklisted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX ix_token_blacklist_jti (jti),
            INDEX ix_token_blacklist_user_id (user_id),
            INDEX ix_token_blacklist_expires_at (expires_at)
        ) ENGINE=MEMORY
    """)

def downgrade():
    op.drop_table('token_blacklist')
