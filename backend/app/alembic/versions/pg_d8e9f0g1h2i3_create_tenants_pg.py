"""Create tenants table (PostgreSQL)"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "pg_d8e9f0g1h2i3"
down_revision = "pg_b2c3d4e5f6a7"
branch_labels = None
depends_on = None

def upgrade():
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Subscription info
        sa.Column('subscription_tier', sa.String(length=50), nullable=False, server_default='free'),
        sa.Column('subscription_status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('subscription_start', sa.DateTime(), nullable=True),
        sa.Column('subscription_end', sa.DateTime(), nullable=True),

        # Limits
        sa.Column('max_companies', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('max_users', sa.Integer(), nullable=False, server_default='500'),
        sa.Column('max_storage_gb', sa.Integer(), nullable=False, server_default='10'),

        # Usage
        sa.Column('current_companies', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_users', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_storage_gb', sa.Integer(), nullable=False, server_default='0'),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_trial', sa.Boolean(), nullable=False, server_default='false'),

        # Contact
        sa.Column('contact_name', sa.String(length=255), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),

        # Branding
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('primary_color', sa.String(length=7), nullable=True),

        # Metadata
        sa.Column('metadata', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True)
    )

    # Create indexes
    op.create_index('ix_tenants_name', 'tenants', ['name'])
    op.create_index('ix_tenants_code', 'tenants', ['code'])
    op.create_index('ix_tenants_is_active', 'tenants', ['is_active'])

def downgrade():
    op.drop_index('ix_tenants_is_active', table_name='tenants')
    op.drop_index('ix_tenants_code', table_name='tenants')
    op.drop_index('ix_tenants_name', table_name='tenants')
    op.drop_table('tenants')
