"""Add remaining study fields

Revision ID: add_remaining_study_fields
Revises: add_study_code_field
Create Date: 2025-01-05 06:25:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_remaining_study_fields'
down_revision = 'add_study_code_field'
branch_labels = None
depends_on = None

def upgrade():
    # Add missing columns to study table
    op.add_column('study', sa.Column('phase', sa.String(length=50), nullable=True))
    op.add_column('study', sa.Column('therapeutic_area', sa.String(length=100), nullable=True))
    op.add_column('study', sa.Column('indication', sa.String(length=255), nullable=True))
    op.add_column('study', sa.Column('planned_start_date', sa.DateTime(), nullable=True))
    op.add_column('study', sa.Column('planned_end_date', sa.DateTime(), nullable=True))
    op.add_column('study', sa.Column('actual_start_date', sa.DateTime(), nullable=True))
    op.add_column('study', sa.Column('actual_end_date', sa.DateTime(), nullable=True))
    op.add_column('study', sa.Column('config', sa.JSON(), nullable=True))
    op.add_column('study', sa.Column('data_retention_days', sa.Integer(), nullable=True))
    op.add_column('study', sa.Column('refresh_frequency', sa.String(length=50), nullable=True))
    op.add_column('study', sa.Column('is_active', sa.Boolean(), nullable=True))
    
    # Update existing records to have default values
    op.execute("UPDATE study SET is_active = TRUE WHERE is_active IS NULL")
    op.execute("UPDATE study SET data_retention_days = 2555 WHERE data_retention_days IS NULL")
    op.execute("UPDATE study SET refresh_frequency = 'daily' WHERE refresh_frequency IS NULL")
    op.execute("UPDATE study SET config = '{}' WHERE config IS NULL")

def downgrade():
    # Drop columns
    op.drop_column('study', 'is_active')
    op.drop_column('study', 'refresh_frequency')
    op.drop_column('study', 'data_retention_days')
    op.drop_column('study', 'config')
    op.drop_column('study', 'actual_end_date')
    op.drop_column('study', 'actual_start_date')
    op.drop_column('study', 'planned_end_date')
    op.drop_column('study', 'planned_start_date')
    op.drop_column('study', 'indication')
    op.drop_column('study', 'therapeutic_area')
    op.drop_column('study', 'phase')