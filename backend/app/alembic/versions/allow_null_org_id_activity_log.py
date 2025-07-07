"""Allow null org_id in activity log

Revision ID: allow_null_org_id_activity_log
Revises: fix_activity_log_columns
Create Date: 2025-01-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'allow_null_org_id_activity_log'
down_revision = 'fix_activity_log_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make org_id nullable in activity_log table for system-level operations
    op.alter_column('activity_log', 'org_id',
               existing_type=postgresql.UUID(as_uuid=True),
               nullable=True)


def downgrade() -> None:
    # Make org_id not nullable again
    op.alter_column('activity_log', 'org_id',
               existing_type=postgresql.UUID(as_uuid=True),
               nullable=False)