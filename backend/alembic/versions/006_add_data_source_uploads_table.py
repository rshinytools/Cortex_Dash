# ABOUTME: Migration to add data_source_uploads table for study data file uploads
# ABOUTME: Fixes foreign key constraint error when deleting draft studies

"""Add data_source_uploads table

Revision ID: 006_add_data_source_uploads
Revises: 005_fix_template_drafts_columns
Create Date: 2025-07-15

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_data_source_uploads'
down_revision = '005_fix_template_drafts_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create data_source_uploads table
    op.create_table('data_source_uploads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('upload_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('upload_timestamp', sa.DateTime(), nullable=False),
        sa.Column('original_filename', sa.String(length=500), nullable=False),
        sa.Column('file_format', sa.String(length=50), nullable=False),
        sa.Column('file_size_mb', sa.Float(), nullable=True),
        sa.Column('raw_path', sa.String(length=1000), nullable=True),
        sa.Column('processed_path', sa.String(length=1000), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_duration_seconds', sa.Float(), nullable=True),
        sa.Column('files_extracted', sa.Integer(), nullable=True),
        sa.Column('total_rows', sa.Integer(), nullable=True),
        sa.Column('total_columns', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('warnings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('upload_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active_version', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('superseded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['superseded_by'], ['data_source_uploads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_source_uploads_study_id'), 'data_source_uploads', ['study_id'], unique=False)
    op.create_index(op.f('ix_data_source_uploads_upload_name'), 'data_source_uploads', ['upload_name'], unique=False)
    op.create_index(op.f('ix_data_source_uploads_status'), 'data_source_uploads', ['status'], unique=False)


def downgrade() -> None:
    # Drop data_source_uploads table
    op.drop_index(op.f('ix_data_source_uploads_status'), table_name='data_source_uploads')
    op.drop_index(op.f('ix_data_source_uploads_upload_name'), table_name='data_source_uploads')
    op.drop_index(op.f('ix_data_source_uploads_study_id'), table_name='data_source_uploads')
    op.drop_table('data_source_uploads')