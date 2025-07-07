"""Drop created_at from activity_log

Revision ID: drop_created_at_activity_log
Revises: allow_null_org_id_activity_log
Create Date: 2025-01-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'drop_created_at_activity_log'
down_revision = 'allow_null_org_id_activity_log'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the created_at column and its index since we use timestamp instead
    op.drop_index('ix_activity_log_created_at', table_name='activity_log')
    op.drop_column('activity_log', 'created_at')
    
    # Also drop session_id and success columns that aren't in the model
    op.drop_column('activity_log', 'session_id')
    op.drop_column('activity_log', 'success')
    op.drop_column('activity_log', 'error_message')


def downgrade() -> None:
    # Re-add the columns
    op.add_column('activity_log', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('activity_log', sa.Column('session_id', sa.String(length=255), nullable=True))
    op.add_column('activity_log', sa.Column('success', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('activity_log', sa.Column('error_message', sa.Text(), nullable=True))
    
    # Re-create index
    op.create_index('ix_activity_log_created_at', 'activity_log', ['created_at'])