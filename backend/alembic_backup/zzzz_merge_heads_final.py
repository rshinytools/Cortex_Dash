"""Merge all migration heads

Revision ID: merge_heads_final
Revises: add_data_constraints_and_triggers, add_template_versioning, drop_created_at_activity_log
Create Date: 2025-01-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_heads_final'
down_revision = ('add_data_constraints_and_triggers', 'add_template_versioning', 'drop_created_at_activity_log', 'add_study_code_field')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a merge migration, no operations needed
    pass


def downgrade() -> None:
    # This is a merge migration, no operations needed
    pass