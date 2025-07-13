"""Add template versioning system tables and fields

Revision ID: 003_template_versioning
Revises: 002_dashboard_permissions
Create Date: 2025-01-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = '003_template_versioning'
down_revision = '002_dashboard_permissions'
branch_labels = None
depends_on = None


def upgrade():
    # Create template_drafts table
    op.create_table(
        'template_drafts',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('template_id', sa.UUID(), nullable=False),
        sa.Column('base_version_id', sa.UUID(), nullable=True),
        sa.Column('draft_content', sa.JSON(), nullable=False),
        sa.Column('changes_summary', sa.JSON(), nullable=True, default=[]),
        sa.Column('auto_save_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('conflict_status', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['template_id'], ['dashboard_templates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['base_version_id'], ['template_versions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for template_drafts
    op.create_index('idx_template_drafts_template_id', 'template_drafts', ['template_id'])
    op.create_index('idx_template_drafts_created_by', 'template_drafts', ['created_by'])
    op.create_index('idx_template_drafts_active', 'template_drafts', ['is_active', 'template_id'])
    
    # Create template_change_logs table
    op.create_table(
        'template_change_logs',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('template_id', sa.UUID(), nullable=False),
        sa.Column('draft_id', sa.UUID(), nullable=True),
        sa.Column('change_type', sa.String(50), nullable=False),
        sa.Column('change_category', sa.String(100), nullable=False),
        sa.Column('change_description', sa.Text(), nullable=True),
        sa.Column('change_data', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['template_id'], ['dashboard_templates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['draft_id'], ['template_drafts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("change_type IN ('major', 'minor', 'patch')", name='check_change_type')
    )
    
    # Create indexes for template_change_logs
    op.create_index('idx_template_change_logs_template_id', 'template_change_logs', ['template_id'])
    op.create_index('idx_template_change_logs_created_at', 'template_change_logs', ['created_at'])
    op.create_index('idx_template_change_logs_draft_id', 'template_change_logs', ['draft_id'])
    
    # Add new columns to template_versions table
    op.add_column('template_versions', 
        sa.Column('version_type', sa.String(10), nullable=True))
    op.add_column('template_versions', 
        sa.Column('auto_created', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('template_versions', 
        sa.Column('change_summary', sa.JSON(), nullable=True, server_default='[]'))
    op.add_column('template_versions', 
        sa.Column('created_by_name', sa.String(255), nullable=True))
    op.add_column('template_versions', 
        sa.Column('comparison_hash', sa.String(64), nullable=True))
    
    # Add constraint for version_type
    op.create_check_constraint(
        'check_version_type',
        'template_versions',
        "version_type IN ('major', 'minor', 'patch')"
    )
    
    # Create index for comparison_hash for faster lookups
    op.create_index('idx_template_versions_hash', 'template_versions', ['comparison_hash'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_template_versions_hash', 'template_versions')
    op.drop_index('idx_template_change_logs_draft_id', 'template_change_logs')
    op.drop_index('idx_template_change_logs_created_at', 'template_change_logs')
    op.drop_index('idx_template_change_logs_template_id', 'template_change_logs')
    op.drop_index('idx_template_drafts_active', 'template_drafts')
    op.drop_index('idx_template_drafts_created_by', 'template_drafts')
    op.drop_index('idx_template_drafts_template_id', 'template_drafts')
    
    # Drop constraint
    op.drop_constraint('check_version_type', 'template_versions', type_='check')
    
    # Drop columns from template_versions
    op.drop_column('template_versions', 'comparison_hash')
    op.drop_column('template_versions', 'created_by_name')
    op.drop_column('template_versions', 'change_summary')
    op.drop_column('template_versions', 'auto_created')
    op.drop_column('template_versions', 'version_type')
    
    # Drop tables
    op.drop_table('template_change_logs')
    op.drop_table('template_drafts')