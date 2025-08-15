# ABOUTME: Phase 1 database migration for enhanced widget architecture
# ABOUTME: Adds data contracts, mapping tables, and metadata storage

"""Phase 1: Widget Architecture Enhancement

Revision ID: phase1_widget_arch
Revises: ff71440d9654
Create Date: 2025-08-13

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision: str = 'phase1_widget_arch'
down_revision: Union[str, None] = 'ff71440d9654'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Phase 1 widget architecture tables and columns"""
    
    # 1. Add data_contract and cache_ttl to widget_definitions (if not exists)
    from sqlalchemy import inspect
    from sqlalchemy import create_engine
    
    # Get current columns
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = [col['name'] for col in inspector.get_columns('widget_definitions')]
    
    if 'data_contract' not in existing_columns:
        op.add_column('widget_definitions', 
            sa.Column('data_contract', postgresql.JSON(astext_type=sa.Text()), nullable=True,
                comment='Defines widget data requirements and capabilities'))
    
    if 'cache_ttl' not in existing_columns:
        op.add_column('widget_definitions', 
            sa.Column('cache_ttl', sa.Integer(), nullable=True, default=3600,
                comment='Cache time-to-live in seconds'))
    
    if 'query_template' not in existing_columns:
        op.add_column('widget_definitions', 
            sa.Column('query_template', sa.Text(), nullable=True,
                comment='SQL query template for widget data'))
    
    # 2. Create dataset_metadata table (if not exists)
    existing_tables = inspector.get_table_names()
    
    if 'dataset_metadata' not in existing_tables:
        op.create_table('dataset_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('column_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True,
            comment='Column names, types, statistics'),
        sa.Column('granularity', sa.String(50), nullable=True,
            comment='Data level: subject/visit/event'),
        sa.Column('data_quality_score', sa.Float(), nullable=True),
        sa.Column('upload_date', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.Column('last_updated', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='SET NULL')
    )
        op.create_index('idx_dataset_metadata_study', 'dataset_metadata', ['study_id'])
    
    # 3. Create study_data_mappings table (if not exists)
    if 'study_data_mappings' not in existing_tables:
        op.create_table('study_data_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('widget_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('mapping_name', sa.String(255), nullable=True),
        sa.Column('field_mappings', postgresql.JSON(astext_type=sa.Text()), nullable=False,
            comment='Maps widget requirements to dataset fields'),
        sa.Column('transformations', postgresql.JSON(astext_type=sa.Text()), nullable=True,
            comment='Field transformations and calculations'),
        sa.Column('join_config', postgresql.JSON(astext_type=sa.Text()), nullable=True,
            comment='Configuration for multi-dataset JOINs'),
        sa.Column('filters', postgresql.JSON(astext_type=sa.Text()), nullable=True,
            comment='Default filters to apply'),
        sa.Column('cache_override', sa.Integer(), nullable=True,
            comment='Override widget cache TTL'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('validation_status', sa.String(50), nullable=True),
        sa.Column('validation_errors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['widget_id'], ['widget_definitions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_id'], ['dataset_metadata.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='SET NULL')
    )
        op.create_index('idx_study_mappings_study', 'study_data_mappings', ['study_id'])
        op.create_index('idx_study_mappings_widget', 'study_data_mappings', ['widget_id'])
    
    # 4. Create widget_mapping_templates table (if not exists)
    if 'widget_mapping_templates' not in existing_tables:
        op.create_table('widget_mapping_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('widget_type', sa.String(100), nullable=False),
        sa.Column('edc_system', sa.String(50), nullable=True,
            comment='EDC system this template is for (Rave, Veeva, etc)'),
        sa.Column('field_patterns', postgresql.JSON(astext_type=sa.Text()), nullable=True,
            comment='Common field naming patterns'),
        sa.Column('default_mappings', postgresql.JSON(astext_type=sa.Text()), nullable=False,
            comment='Default field mappings'),
        sa.Column('transformation_rules', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_public', sa.Boolean(), default=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='SET NULL')
    )
        op.create_index('idx_mapping_templates_org', 'widget_mapping_templates', ['organization_id'])
        op.create_index('idx_mapping_templates_type', 'widget_mapping_templates', ['widget_type'])
    
    # 5. Create widget_calculations table for derived fields (if not exists)
    if 'widget_calculations' not in existing_tables:
        op.create_table('widget_calculations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('expression', sa.Text(), nullable=False,
            comment='SQL expression or formula'),
        sa.Column('expression_type', sa.String(50), nullable=False, default='sql',
            comment='sql, javascript, python'),
        sa.Column('input_fields', postgresql.JSON(astext_type=sa.Text()), nullable=True,
            comment='List of required input fields'),
        sa.Column('output_type', sa.String(50), nullable=True,
            comment='Data type of result'),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_validated', sa.Boolean(), default=False),
        sa.Column('validation_errors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='SET NULL')
    )
        op.create_index('idx_calculations_study', 'widget_calculations', ['study_id'])
    
    # 6. Create query_cache table (if not exists)
    if 'query_cache' not in existing_tables:
        op.create_table('query_cache',
        sa.Column('cache_key', sa.String(255), primary_key=True),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('widget_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('query_hash', sa.String(64), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=True),
        sa.Column('result_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('result_count', sa.Integer(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('hit_count', sa.Integer(), default=0),
        sa.Column('last_accessed', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['widget_id'], ['widget_definitions.id'], ondelete='CASCADE')
    )
        op.create_index('idx_cache_study', 'query_cache', ['study_id'])
        op.create_index('idx_cache_expires', 'query_cache', ['expires_at'])
    
    # 7. Add columns to study table for data mapping status (if not exists)
    study_columns = [col['name'] for col in inspector.get_columns('study')]
    
    if 'mapping_status' not in study_columns:
        op.add_column('study',
        sa.Column('mapping_status', sa.String(50), nullable=True, default='pending',
            comment='Status of data mapping: pending, in_progress, completed, error'))
    
    if 'mapping_completed_at' not in study_columns:
        op.add_column('study',
            sa.Column('mapping_completed_at', sa.TIMESTAMP(timezone=True), nullable=True))
    
    if 'total_datasets' not in study_columns:
        op.add_column('study',
            sa.Column('total_datasets', sa.Integer(), nullable=True, default=0))
    
    if 'mapped_widgets' not in study_columns:
        op.add_column('study',
            sa.Column('mapped_widgets', sa.Integer(), nullable=True, default=0))
    
    # 8. Create calculation_templates table for reusable calculations (if not exists)
    if 'calculation_templates' not in existing_tables:
        op.create_table('calculation_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('expression', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('input_parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('output_type', sa.String(50), nullable=True),
        sa.Column('example_usage', sa.Text(), nullable=True),
        sa.Column('is_clinical_standard', sa.Boolean(), default=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'))
    )
    
    print("✅ Phase 1 database schema created successfully")


def downgrade() -> None:
    """Remove Phase 1 widget architecture tables and columns"""
    
    # Drop tables in reverse order due to foreign key constraints
    op.drop_table('calculation_templates')
    op.drop_table('query_cache')
    op.drop_table('widget_calculations')
    op.drop_table('study_data_mappings')
    op.drop_table('widget_mapping_templates')
    op.drop_table('dataset_metadata')
    
    # Remove columns from study table
    op.drop_column('study', 'mapped_widgets')
    op.drop_column('study', 'total_datasets')
    op.drop_column('study', 'mapping_completed_at')
    op.drop_column('study', 'mapping_status')
    
    # Remove columns from widget_definitions
    op.drop_column('widget_definitions', 'query_template')
    op.drop_column('widget_definitions', 'cache_ttl')
    op.drop_column('widget_definitions', 'data_contract')
    
    print("✅ Phase 1 database schema rolled back successfully")