"""add transformation fields to study

Revision ID: 008
Revises: 007_create_field_mapping_table
Create Date: 2025-07-15 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_add_transformation_fields'
down_revision = '007_create_field_mapping_table'
branch_labels = None
depends_on = None


def upgrade():
    """Add transformation tracking fields to study table"""
    # Add transformation tracking columns
    op.add_column('study', 
        sa.Column('last_transformation_at', sa.DateTime(), nullable=True)
    )
    op.add_column('study', 
        sa.Column('transformation_status', sa.String(), nullable=True)
    )
    op.add_column('study', 
        sa.Column('transformation_count', sa.Integer(), nullable=False, server_default='0')
    )
    op.add_column('study', 
        sa.Column('derived_datasets', postgresql.JSON(astext_type=sa.Text()), nullable=True)
    )
    op.add_column('study', 
        sa.Column('transformation_errors', postgresql.JSON(astext_type=sa.Text()), nullable=True)
    )


def downgrade():
    """Remove transformation tracking fields from study table"""
    op.drop_column('study', 'transformation_errors')
    op.drop_column('study', 'derived_datasets')
    op.drop_column('study', 'transformation_count')
    op.drop_column('study', 'transformation_status')
    op.drop_column('study', 'last_transformation_at')