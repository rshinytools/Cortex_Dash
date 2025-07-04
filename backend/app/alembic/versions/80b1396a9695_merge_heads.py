"""Merge heads

Revision ID: 80b1396a9695
Revises: 1a31ce608336, clinical_models_001
Create Date: 2025-07-03 23:13:05.042356

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '80b1396a9695'
down_revision = ('1a31ce608336', 'clinical_models_001')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
