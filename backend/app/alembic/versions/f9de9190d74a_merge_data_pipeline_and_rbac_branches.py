"""Merge data pipeline and rbac branches

Revision ID: f9de9190d74a
Revises: data_pipeline_metadata, initialize_rbac_data
Create Date: 2025-08-15 15:55:07.189182

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'f9de9190d74a'
down_revision = ('data_pipeline_metadata', 'initialize_rbac_data')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
