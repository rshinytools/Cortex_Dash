# ABOUTME: Migration for data pipeline metadata storage tables
# ABOUTME: Stores dataset metadata, field mappings, and query cache for efficient data access

"""Data pipeline metadata tables

Revision ID: data_pipeline_metadata
Revises: widget_init_data_002
Create Date: 2025-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = 'data_pipeline_metadata'
down_revision = 'widget_init_data_002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get database connection to check if tables exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()
    
    # Create dataset_metadata table for storing information about uploaded datasets
    if 'dataset_metadata' not in existing_tables:
        op.create_table(
            'dataset_metadata',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('study_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('dataset_name', sa.String(255), nullable=False),
            sa.Column('dataset_type', sa.String(50), nullable=True),  # SDTM, ADaM, Custom
            sa.Column('file_path', sa.String(500), nullable=False),
            sa.Column('parquet_path', sa.String(500), nullable=True),
            sa.Column('row_count', sa.Integer(), nullable=True),
            sa.Column('column_count', sa.Integer(), nullable=True),
            sa.Column('columns_info', postgresql.JSONB, nullable=True),  # Detailed column metadata
            sa.Column('detected_patterns', postgresql.JSONB, nullable=True),  # Auto-detected CDISC patterns
            sa.Column('file_size', sa.BigInteger(), nullable=True),
            sa.Column('checksum', sa.String(64), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.Column('version', sa.Integer(), default=1),
            sa.ForeignKeyConstraint(['study_id'], ['study.id'], ondelete='CASCADE'),
        )
        
        # Create indexes for dataset_metadata
        op.create_index('ix_dataset_metadata_org_study', 'dataset_metadata', ['org_id', 'study_id'])
        op.create_index('ix_dataset_metadata_study_name', 'dataset_metadata', ['study_id', 'dataset_name'])
    
    # Create study_datasets table for storing actual data (PostgreSQL approach)
    if 'study_datasets' not in existing_tables:
        op.create_table(
            'study_datasets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_name', sa.String(100), nullable=False),
        sa.Column('row_data', postgresql.JSONB, nullable=False),  # Actual data rows
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer(), default=1),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ondelete='CASCADE'),
            sa.UniqueConstraint('study_id', 'dataset_name', 'version', name='uq_study_dataset_version')
        )
    
        # Create GIN index for fast JSONB queries
        op.create_index('idx_study_datasets_data', 'study_datasets', ['row_data'], postgresql_using='gin')
        op.create_index('idx_study_datasets_org_study', 'study_datasets', ['org_id', 'study_id'])
    
    # Create field_mapping_templates table for reusable mappings
    if 'field_mapping_templates' not in existing_tables:
        op.create_table(
            'field_mapping_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_name', sa.String(255), nullable=False),
        sa.Column('edc_system', sa.String(50), nullable=True),  # Rave, Veeva, etc.
        sa.Column('mapping_rules', postgresql.JSONB, nullable=False),
        sa.Column('confidence_threshold', sa.Float(), default=0.7),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        )
    
        # Create index for field_mapping_templates
        op.create_index('ix_field_mapping_templates_org', 'field_mapping_templates', ['org_id'])
    
    # Create query_cache table for caching expensive queries
    if 'query_cache' not in existing_tables:
        op.create_table(
            'query_cache',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('widget_id', sa.String(255), nullable=False),
        sa.Column('query_hash', sa.String(64), nullable=False),  # Hash of the query parameters
        sa.Column('result_data', postgresql.JSONB, nullable=False),
        sa.Column('metadata', postgresql.JSONB, nullable=True),  # Query metadata (execution time, etc.)
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ondelete='CASCADE'),
            sa.UniqueConstraint('study_id', 'widget_id', 'query_hash', name='uq_query_cache')
        )
    
        # Create index for query_cache
        op.create_index('ix_query_cache_study_widget', 'query_cache', ['study_id', 'widget_id'])
        op.create_index('ix_query_cache_expires', 'query_cache', ['expires_at'])
    
    # Add columns to study table if they don't exist
    with op.batch_alter_table('study') as batch_op:
        # Check if columns exist before adding
        batch_op.add_column(sa.Column('data_storage_type', sa.String(20), server_default='postgresql'))
        batch_op.add_column(sa.Column('use_parquet', sa.Boolean(), server_default='false'))
        batch_op.add_column(sa.Column('last_data_refresh', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('query_cache')
    op.drop_table('field_mapping_templates')
    op.drop_table('study_datasets')
    op.drop_table('dataset_metadata')
    
    # Remove columns from study table
    with op.batch_alter_table('study') as batch_op:
        batch_op.drop_column('data_storage_type')
        batch_op.drop_column('use_parquet')
        batch_op.drop_column('last_data_refresh')