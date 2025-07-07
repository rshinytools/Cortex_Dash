"""Drop metadata column from study table

Revision ID: drop_metadata_column
Revises: add_study_compliance_fields
Create Date: 2025-01-05 06:40:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'drop_metadata_column'
down_revision = 'add_study_compliance_fields'
branch_labels = None
depends_on = None

def upgrade():
    # Drop the metadata column that's not in the current model
    op.drop_column('study', 'metadata')

def downgrade():
    # Re-add the metadata column
    op.add_column('study', sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'))