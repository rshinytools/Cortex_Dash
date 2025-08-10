"""Create field mapping table

Revision ID: 007_field_mapping_table
Revises: 006_study_init_fields
Create Date: 2025-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_create_field_mapping_table'
down_revision = '006_add_data_source_uploads'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create field_mapping table
    op.create_table('field_mapping',
        sa.Column('id', postgresql.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('study_id', postgresql.UUID(), nullable=False),
        sa.Column('widget_id', sa.String(length=255), nullable=False),
        sa.Column('widget_title', sa.String(length=255), nullable=True),
        sa.Column('dataset', sa.String(length=100), nullable=True),
        sa.Column('target_field', sa.String(length=255), nullable=False),
        sa.Column('source_field', sa.String(length=255), nullable=True),
        sa.Column('is_mapped', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('confidence_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('mapping_type', sa.String(length=50), nullable=True, server_default='manual'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', postgresql.UUID(), nullable=True),
        sa.Column('updated_by', postgresql.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['user.id'], )
    )
    
    # Create indexes for better performance
    op.create_index('ix_field_mapping_study_id', 'field_mapping', ['study_id'])
    op.create_index('ix_field_mapping_widget_id', 'field_mapping', ['widget_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_field_mapping_widget_id', table_name='field_mapping')
    op.drop_index('ix_field_mapping_study_id', table_name='field_mapping')
    
    # Drop field_mapping table
    op.drop_table('field_mapping')