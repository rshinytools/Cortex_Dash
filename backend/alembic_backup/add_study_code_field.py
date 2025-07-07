"""Add study code field

Revision ID: add_study_code_field
Revises: 80b1396a9695
Create Date: 2025-01-05 06:20:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_study_code_field'
down_revision = 'clinical_models_001'
branch_labels = None
depends_on = None

def upgrade():
    # Add code column to study table
    op.add_column('study', sa.Column('code', sa.String(length=50), nullable=True))
    
    # Create index on code
    op.create_index('ix_study_code', 'study', ['code'])

def downgrade():
    # Drop index
    op.drop_index('ix_study_code', 'study')
    
    # Drop column
    op.drop_column('study', 'code')