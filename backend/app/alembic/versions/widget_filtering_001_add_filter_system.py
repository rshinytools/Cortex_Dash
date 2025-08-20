# ABOUTME: Database migration for widget filtering system
# ABOUTME: Adds filter storage, validation cache, and metrics tables

"""Add widget filtering system

Revision ID: widget_filtering_001
Revises: f9de9190d74a
Create Date: 2025-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'widget_filtering_001'
down_revision = 'f9de9190d74a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add widget filtering system tables and columns"""
    
    # Add filter storage column to study table (not studies)
    op.add_column('study',
        sa.Column('field_mapping_filters', sa.JSON, nullable=True, server_default='{}')
    )
    
    # Create filter validation cache table
    op.create_table('filter_validation_cache',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('study.id', ondelete='CASCADE'), nullable=False),
        sa.Column('widget_id', sa.String(255), nullable=False),
        sa.Column('filter_expression', sa.Text, nullable=False),
        sa.Column('dataset_name', sa.String(255), nullable=False),
        sa.Column('is_valid', sa.Boolean, nullable=False, default=False),
        sa.Column('validation_errors', sa.JSON, nullable=True),
        sa.Column('validated_columns', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('last_validated', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for filter validation cache
    op.create_index(
        'idx_validation_cache_study_widget',
        'filter_validation_cache',
        ['study_id', 'widget_id']
    )
    
    # Create filter metrics table for performance tracking
    op.create_table('filter_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('widget_id', sa.String(255), nullable=False),
        sa.Column('filter_expression', sa.Text, nullable=False),
        sa.Column('execution_time_ms', sa.Integer, nullable=False),
        sa.Column('rows_before', sa.Integer, nullable=False),
        sa.Column('rows_after', sa.Integer, nullable=False),
        sa.Column('reduction_percentage', sa.Float, nullable=True),
        sa.Column('executed_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('execution_context', sa.JSON, nullable=True),  # Additional context like user, endpoint
    )
    
    # Create indexes for filter metrics
    op.create_index(
        'idx_metrics_study_execution',
        'filter_metrics',
        ['study_id', 'executed_at']
    )
    
    op.create_index(
        'idx_metrics_widget',
        'filter_metrics',
        ['widget_id', 'executed_at']
    )
    
    # Create filter audit log table for compliance
    op.create_table('filter_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('study.id', ondelete='CASCADE'), nullable=False),
        sa.Column('widget_id', sa.String(255), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),  # CREATE, UPDATE, DELETE, VALIDATE
        sa.Column('old_expression', sa.Text, nullable=True),
        sa.Column('new_expression', sa.Text, nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('details', sa.JSON, nullable=True),
    )
    
    # Create index for audit log
    op.create_index(
        'idx_filter_audit_study',
        'filter_audit_log',
        ['study_id', 'created_at']
    )


def downgrade() -> None:
    """Remove widget filtering system"""
    
    # Drop tables
    op.drop_table('filter_audit_log')
    op.drop_table('filter_metrics')
    op.drop_table('filter_validation_cache')
    
    # Remove column from study table
    op.drop_column('study', 'field_mapping_filters')