# ABOUTME: Database migration to add template versioning, inheritance, marketplace features
# ABOUTME: Adds versioning fields, template reviews, version history, and inheritance support

"""Add template versioning and marketplace features

Revision ID: add_template_versioning
Revises: unify_dashboard_templates
Create Date: 2025-07-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'add_template_versioning'
down_revision = 'unify_dashboard_templates'
branch_labels = None
depends_on = None


def upgrade():
    # Create ENUM types first
    templatestatus = sa.Enum('DRAFT', 'PUBLISHED', 'DEPRECATED', 'ARCHIVED', name='templatestatus')
    inheritancetype = sa.Enum('NONE', 'EXTENDS', 'INCLUDES', name='inheritancetype')
    
    # Create the enums in the database
    templatestatus.create(op.get_bind(), checkfirst=True)
    inheritancetype.create(op.get_bind(), checkfirst=True)
    
    # Add new columns to dashboard_templates table
    op.add_column('dashboard_templates', sa.Column('major_version', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('dashboard_templates', sa.Column('minor_version', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('dashboard_templates', sa.Column('patch_version', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('dashboard_templates', sa.Column('status', templatestatus, nullable=False, server_default='DRAFT'))
    op.add_column('dashboard_templates', sa.Column('parent_template_id', sa.UUID(), nullable=True))
    op.add_column('dashboard_templates', sa.Column('inheritance_type', inheritancetype, nullable=False, server_default='NONE'))
    op.add_column('dashboard_templates', sa.Column('tags', sa.JSON(), nullable=True))
    op.add_column('dashboard_templates', sa.Column('screenshot_urls', sa.JSON(), nullable=True))
    op.add_column('dashboard_templates', sa.Column('documentation_url', sa.String(length=500), nullable=True))
    op.add_column('dashboard_templates', sa.Column('average_rating', sa.Float(), nullable=True))
    op.add_column('dashboard_templates', sa.Column('total_ratings', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('dashboard_templates', sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('dashboard_templates', sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'))
    
    # Remove old version column and replace with semantic versioning
    op.drop_column('dashboard_templates', 'version')
    
    # Add foreign key constraint for parent template
    op.create_foreign_key(
        'fk_dashboard_templates_parent_template_id',
        'dashboard_templates', 'dashboard_templates',
        ['parent_template_id'], ['id']
    )
    
    # Create template_versions table
    op.create_table(
        'template_versions',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('template_id', sa.UUID(), nullable=False),
        sa.Column('major_version', sa.Integer(), nullable=False),
        sa.Column('minor_version', sa.Integer(), nullable=False),
        sa.Column('patch_version', sa.Integer(), nullable=False),
        sa.Column('change_description', sa.String(length=500), nullable=False),
        sa.Column('template_structure', sa.JSON(), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('migration_notes', sa.Text(), nullable=True),
        sa.Column('breaking_changes', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('required_migrations', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['template_id'], ['dashboard_templates.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    )
    
    # Create template_reviews table
    op.create_table(
        'template_reviews',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('template_id', sa.UUID(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('review_text', sa.Text(), nullable=True),
        sa.Column('is_verified_user', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reviewed_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['template_id'], ['dashboard_templates.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['user.id'], ),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )
    
    # Create indexes for performance
    op.create_index('idx_dashboard_templates_status', 'dashboard_templates', ['status'])
    op.create_index('idx_dashboard_templates_parent_id', 'dashboard_templates', ['parent_template_id'])
    op.create_index('idx_dashboard_templates_public', 'dashboard_templates', ['is_public'])
    op.create_index('idx_dashboard_templates_category_public', 'dashboard_templates', ['category', 'is_public'])
    op.create_index('idx_template_versions_template_id', 'template_versions', ['template_id'])
    op.create_index('idx_template_versions_version', 'template_versions', ['major_version', 'minor_version', 'patch_version'])
    op.create_index('idx_template_reviews_template_id', 'template_reviews', ['template_id'])
    op.create_index('idx_template_reviews_rating', 'template_reviews', ['rating'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_template_reviews_rating', table_name='template_reviews')
    op.drop_index('idx_template_reviews_template_id', table_name='template_reviews')
    op.drop_index('idx_template_versions_version', table_name='template_versions')
    op.drop_index('idx_template_versions_template_id', table_name='template_versions')
    op.drop_index('idx_dashboard_templates_category_public', table_name='dashboard_templates')
    op.drop_index('idx_dashboard_templates_public', table_name='dashboard_templates')
    op.drop_index('idx_dashboard_templates_parent_id', table_name='dashboard_templates')
    op.drop_index('idx_dashboard_templates_status', table_name='dashboard_templates')
    
    # Drop tables
    op.drop_table('template_reviews')
    op.drop_table('template_versions')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_dashboard_templates_parent_template_id', 'dashboard_templates', type_='foreignkey')
    
    # Remove new columns from dashboard_templates
    op.drop_column('dashboard_templates', 'is_public')
    op.drop_column('dashboard_templates', 'download_count')
    op.drop_column('dashboard_templates', 'total_ratings')
    op.drop_column('dashboard_templates', 'average_rating')
    op.drop_column('dashboard_templates', 'documentation_url')
    op.drop_column('dashboard_templates', 'screenshot_urls')
    op.drop_column('dashboard_templates', 'tags')
    op.drop_column('dashboard_templates', 'inheritance_type')
    op.drop_column('dashboard_templates', 'parent_template_id')
    op.drop_column('dashboard_templates', 'status')
    op.drop_column('dashboard_templates', 'patch_version')
    op.drop_column('dashboard_templates', 'minor_version')
    op.drop_column('dashboard_templates', 'major_version')
    
    # Re-add old version column
    op.add_column('dashboard_templates', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS inheritancetype')
    op.execute('DROP TYPE IF EXISTS templatestatus')