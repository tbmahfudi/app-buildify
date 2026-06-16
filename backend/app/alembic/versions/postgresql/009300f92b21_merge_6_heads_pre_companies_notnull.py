"""merge 6 heads (pre-companies-notnull)

Revision ID: 009300f92b21
Revises: pg_add_commit_msg, add_module_id_to_entities, pg_add_module_id_webhooks, pg_add_precision_refs, pg_consolidate_entity_metadata, pg_r5_report_designer_columns
Create Date: 2026-06-15 18:44:04.626633

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009300f92b21'
down_revision = ('pg_add_commit_msg', 'add_module_id_to_entities', 'pg_add_module_id_webhooks', 'pg_add_precision_refs', 'pg_consolidate_entity_metadata', 'pg_r5_report_designer_columns')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass