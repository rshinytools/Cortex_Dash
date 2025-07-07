# ABOUTME: Alembic migration to add dashboard template fields to study table
# ABOUTME: Adds dashboard_template_id, field_mappings, and template_overrides columns

"""Add study template fields

Revision ID: add_study_template_fields
Revises: drop_metadata_column
Create Date: 2025-01-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'add_study_template_fields'
down_revision = 'add_widget_dashboard_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add dashboard_template_id column
    op.add_column('study',
        sa.Column('dashboard_template_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Add field_mappings column (JSON)
    op.add_column('study',
        sa.Column('field_mappings', sa.JSON(), nullable=False, server_default='{}')
    )
    
    # Add template_overrides column (JSON)
    op.add_column('study',
        sa.Column('template_overrides', sa.JSON(), nullable=False, server_default='{}')
    )
    
    # Create foreign key constraint to dashboard_templates table
    op.create_foreign_key(
        'fk_study_dashboard_template',
        'study',
        'dashboard_templates',
        ['dashboard_template_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Create index on dashboard_template_id for better query performance
    op.create_index(
        'ix_study_dashboard_template_id',
        'study',
        ['dashboard_template_id']
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_study_dashboard_template_id', 'study')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_study_dashboard_template', 'study', type_='foreignkey')
    
    # Drop columns
    op.drop_column('study', 'template_overrides')
    op.drop_column('study', 'field_mappings')
    op.drop_column('study', 'dashboard_template_id')