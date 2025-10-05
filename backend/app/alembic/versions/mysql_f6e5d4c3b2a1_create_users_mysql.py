"""Create users table (MySQL)"""
from alembic import op
import sqlalchemy as sa

revision = "mysql_f6e5d4c3b2a1"
down_revision = "mysql_8c4ee763aa"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('tenant_id', sa.String(length=36), nullable=True),
        sa.Column('roles', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        mysql_engine='InnoDB', mysql_charset='utf8mb4'
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])

def downgrade():
    op.drop_index('ix_users_tenant_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')