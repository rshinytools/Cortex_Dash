# ABOUTME: Migration to fix template_drafts column names to match models
# ABOUTME: Renames content to draft_content and adds missing changes_summary column

"""Fix template drafts column names

Revision ID: 005_fix_template_drafts_columns
Revises: 004_create_initial_versions
Create Date: 2025-07-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '005_fix_template_drafts_columns'
down_revision = '004_create_initial_versions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename content column to draft_content
    op.alter_column('template_drafts', 'content',
                    new_column_name='draft_content',
                    existing_type=postgresql.JSON(),
                    existing_nullable=False)
    
    # Add changes_summary column if it doesn't exist
    op.add_column('template_drafts', 
                  sa.Column('changes_summary', postgresql.JSON(), 
                           nullable=False, server_default='[]'))
    
    # Check if content_hash column exists before dropping
    # PostgreSQL-specific check
    result = op.get_bind().execute(
        text("SELECT column_name FROM information_schema.columns "
             "WHERE table_name='template_drafts' AND column_name='content_hash'")
    )
    if result.fetchone():
        # Drop the index first if it exists
        try:
            op.drop_index('ix_template_drafts_content_hash', table_name='template_drafts')
        except:
            pass  # Index might not exist
        
        # Remove content_hash column
        op.drop_column('template_drafts', 'content_hash')
    
    # Add conflict_status column if it doesn't exist
    op.add_column('template_drafts',
                  sa.Column('conflict_status', sa.String(length=50), nullable=True))


def downgrade() -> None:
    # Add back content_hash column and index
    op.add_column('template_drafts',
                  sa.Column('content_hash', sa.String(length=64), nullable=False,
                           server_default=''))
    op.create_index('ix_template_drafts_content_hash', 'template_drafts', 
                    ['content_hash'], unique=False)
    
    # Remove conflict_status column
    op.drop_column('template_drafts', 'conflict_status')
    
    # Remove changes_summary column
    op.drop_column('template_drafts', 'changes_summary')
    
    # Rename draft_content back to content
    op.alter_column('template_drafts', 'draft_content',
                    new_column_name='content',
                    existing_type=postgresql.JSON(),
                    existing_nullable=False)