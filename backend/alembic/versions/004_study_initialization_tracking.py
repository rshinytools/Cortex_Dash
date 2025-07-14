"""Add study initialization tracking fields

Revision ID: 20250114_001
Revises: previous_revision
Create Date: 2025-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_study_initialization'
down_revision = '003_template_versioning'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add initialization tracking fields to study table
    op.add_column('study', sa.Column('initialization_status', sa.String(length=50), nullable=True, server_default='not_started'))
    op.add_column('study', sa.Column('initialization_progress', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('study', sa.Column('initialization_steps', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'))
    op.add_column('study', sa.Column('template_applied_at', sa.DateTime(), nullable=True))
    op.add_column('study', sa.Column('data_uploaded_at', sa.DateTime(), nullable=True))
    op.add_column('study', sa.Column('mappings_configured_at', sa.DateTime(), nullable=True))
    op.add_column('study', sa.Column('activated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove initialization tracking fields from study table
    op.drop_column('study', 'activated_at')
    op.drop_column('study', 'mappings_configured_at')
    op.drop_column('study', 'data_uploaded_at')
    op.drop_column('study', 'template_applied_at')
    op.drop_column('study', 'initialization_steps')
    op.drop_column('study', 'initialization_progress')
    op.drop_column('study', 'initialization_status')