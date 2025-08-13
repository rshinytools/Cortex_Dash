"""add_data_source_uploads_table

Revision ID: 1319a427c2cc
Revises: 005_fix_template_drafts_columns
Create Date: 2025-08-10 18:56:56.705382

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '1319a427c2cc'
down_revision = '005_fix_template_drafts_columns'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
