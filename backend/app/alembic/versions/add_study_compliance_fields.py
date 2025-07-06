"""Add study compliance and stats fields

Revision ID: add_study_compliance_fields
Revises: add_remaining_study_fields
Create Date: 2025-01-05 06:35:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_study_compliance_fields'
down_revision = 'add_remaining_study_fields'
branch_labels = None
depends_on = None

def upgrade():
    # Add compliance and statistics columns to study table
    op.add_column('study', sa.Column('protocol_version', sa.String(length=20), nullable=True))
    op.add_column('study', sa.Column('protocol_approved_date', sa.DateTime(), nullable=True))
    op.add_column('study', sa.Column('protocol_approved_by', sa.UUID(), nullable=True))
    op.add_column('study', sa.Column('subject_count', sa.Integer(), nullable=True))
    op.add_column('study', sa.Column('site_count', sa.Integer(), nullable=True))
    op.add_column('study', sa.Column('data_points_count', sa.Integer(), nullable=True))
    op.add_column('study', sa.Column('last_data_update', sa.DateTime(), nullable=True))
    
    # Add foreign key for protocol_approved_by
    op.create_foreign_key('study_protocol_approved_by_fkey', 'study', 'user', ['protocol_approved_by'], ['id'])
    
    # Update existing records to have default values
    op.execute("UPDATE study SET protocol_version = '1.0' WHERE protocol_version IS NULL")
    op.execute("UPDATE study SET subject_count = 0 WHERE subject_count IS NULL")
    op.execute("UPDATE study SET site_count = 0 WHERE site_count IS NULL")
    op.execute("UPDATE study SET data_points_count = 0 WHERE data_points_count IS NULL")

def downgrade():
    # Drop foreign key
    op.drop_constraint('study_protocol_approved_by_fkey', 'study', type_='foreignkey')
    
    # Drop columns
    op.drop_column('study', 'last_data_update')
    op.drop_column('study', 'data_points_count')
    op.drop_column('study', 'site_count')
    op.drop_column('study', 'subject_count')
    op.drop_column('study', 'protocol_approved_by')
    op.drop_column('study', 'protocol_approved_date')
    op.drop_column('study', 'protocol_version')