"""Create token_blacklist table (SQLite)"""
from alembic import op
import sqlalchemy as sa

revision = "sqlite_e8f9g0h1i2j3"
down_revision = "001_sqlite_complete"
branch_labels = None
depends_on = None

def upgrade():
    # SQLite doesn't support UNLOGGED or MEMORY tables
    # Using regular table with indexes for performance
    op.create_table(
        'token_blacklist',
        sa.Column('jti', sa.String(length=255), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('token_type', sa.String(length=20), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('blacklisted_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False)
    )

    # Create indexes for faster lookups
    op.create_index('ix_token_blacklist_jti', 'token_blacklist', ['jti'])
    op.create_index('ix_token_blacklist_user_id', 'token_blacklist', ['user_id'])
    op.create_index('ix_token_blacklist_expires_at', 'token_blacklist', ['expires_at'])

def downgrade():
    op.drop_index('ix_token_blacklist_expires_at', table_name='token_blacklist')
    op.drop_index('ix_token_blacklist_user_id', table_name='token_blacklist')
    op.drop_index('ix_token_blacklist_jti', table_name='token_blacklist')
    op.drop_table('token_blacklist')
