# ABOUTME: Migration to add template versioning system tables
# ABOUTME: Adds template_drafts and template_change_logs tables for version tracking

"""Add template versioning system

Revision ID: 003
Revises: 002
Create Date: 2025-07-12

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_template_versioning'
down_revision = 'update_activity_action_enum'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create template_drafts table
    op.create_table('template_drafts',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('template_id', postgresql.UUID(), nullable=False),
        sa.Column('base_version_id', postgresql.UUID(), nullable=True),
        sa.Column('content', postgresql.JSON(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', postgresql.UUID(), nullable=False),
        sa.Column('auto_save_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['base_version_id'], ['template_versions.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['dashboard_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_template_drafts_content_hash'), 'template_drafts', ['content_hash'], unique=False)
    op.create_index(op.f('ix_template_drafts_template_id'), 'template_drafts', ['template_id'], unique=False)

    # Create template_change_logs table
    op.create_table('template_change_logs',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('template_id', postgresql.UUID(), nullable=False),
        sa.Column('draft_id', postgresql.UUID(), nullable=True),
        sa.Column('change_type', sa.String(length=50), nullable=False),
        sa.Column('change_category', sa.String(length=100), nullable=False),
        sa.Column('change_description', sa.Text(), nullable=True),
        sa.Column('change_data', postgresql.JSON(), nullable=True),
        sa.Column('created_by', postgresql.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['draft_id'], ['template_drafts.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['dashboard_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_template_change_logs_template_id'), 'template_change_logs', ['template_id'], unique=False)

    # Add new columns to template_versions table if they don't exist
    with op.batch_alter_table('template_versions') as batch_op:
        batch_op.add_column(sa.Column('version_type', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('auto_created', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('change_summary', postgresql.JSON(), nullable=False, server_default='[]'))
        batch_op.add_column(sa.Column('created_by_name', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('comparison_hash', sa.String(length=64), nullable=True))


def downgrade() -> None:
    # Drop new columns from template_versions
    with op.batch_alter_table('template_versions') as batch_op:
        batch_op.drop_column('comparison_hash')
        batch_op.drop_column('created_by_name')
        batch_op.drop_column('change_summary')
        batch_op.drop_column('auto_created')
        batch_op.drop_column('version_type')

    # Drop tables
    op.drop_index(op.f('ix_template_change_logs_template_id'), table_name='template_change_logs')
    op.drop_table('template_change_logs')
    op.drop_index(op.f('ix_template_drafts_template_id'), table_name='template_drafts')
    op.drop_index(op.f('ix_template_drafts_content_hash'), table_name='template_drafts')
    op.drop_table('template_drafts')