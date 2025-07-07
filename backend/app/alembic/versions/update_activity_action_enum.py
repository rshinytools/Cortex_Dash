"""Update ActivityAction enum with new values

Revision ID: update_activity_action_enum
Revises: 824511abee60
Create Date: 2025-07-07 12:26:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'update_activity_action_enum'
down_revision = '824511abee60'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new enum values to ActivityAction
    op.execute("ALTER TYPE activityaction ADD VALUE IF NOT EXISTS 'archive_study'")
    op.execute("ALTER TYPE activityaction ADD VALUE IF NOT EXISTS 'hard_delete_study'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values
    # This would require recreating the enum type
    pass