"""Add contact and address fields to branches table

Revision ID: pg_add_branch_fields
Revises: pg_h2i3j4k5l6m7
Create Date: 2025-11-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'pg_add_branch_fields'
down_revision = 'pg_h2i3j4k5l6m7'
branch_labels = None
depends_on = None


def upgrade():
    # Add contact fields
    op.add_column('branches', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('branches', sa.Column('phone', sa.String(length=50), nullable=True))

    # Add address fields
    op.add_column('branches', sa.Column('address_line1', sa.String(length=255), nullable=True))
    op.add_column('branches', sa.Column('address_line2', sa.String(length=255), nullable=True))
    op.add_column('branches', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('branches', sa.Column('state', sa.String(length=100), nullable=True))
    op.add_column('branches', sa.Column('postal_code', sa.String(length=20), nullable=True))
    op.add_column('branches', sa.Column('country', sa.String(length=100), nullable=True))

    # Add geolocation fields
    op.add_column('branches', sa.Column('latitude', sa.String(length=50), nullable=True))
    op.add_column('branches', sa.Column('longitude', sa.String(length=50), nullable=True))

    # Add is_headquarters if it doesn't exist
    op.add_column('branches', sa.Column('is_headquarters', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('branches', 'is_headquarters')
    op.drop_column('branches', 'longitude')
    op.drop_column('branches', 'latitude')
    op.drop_column('branches', 'country')
    op.drop_column('branches', 'postal_code')
    op.drop_column('branches', 'state')
    op.drop_column('branches', 'city')
    op.drop_column('branches', 'address_line2')
    op.drop_column('branches', 'address_line1')
    op.drop_column('branches', 'phone')
    op.drop_column('branches', 'email')
