"""create pipeline tables

Revision ID: create_pipeline_tables
Revises: 
Create Date: 2025-01-10

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_pipeline_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create pipeline_configs table
    op.create_table('pipeline_configs',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('study_id', postgresql.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('schedule_cron', sa.String(), nullable=True),
        sa.Column('retry_on_failure', sa.Boolean(), nullable=False, default=True),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=3),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, default=3600),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('is_current_version', sa.Boolean(), nullable=False, default=True),
        sa.Column('parent_version_id', postgresql.UUID(), nullable=True),
        sa.Column('source_config', sa.JSON(), nullable=False, default={}),
        sa.Column('transformation_steps', sa.JSON(), nullable=False, default=[]),
        sa.Column('output_config', sa.JSON(), nullable=False, default={}),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', postgresql.UUID(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', postgresql.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['parent_version_id'], ['pipeline_configs.id'], ),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pipeline_configs_name'), 'pipeline_configs', ['name'], unique=False)
    op.create_index(op.f('ix_pipeline_configs_study_id'), 'pipeline_configs', ['study_id'], unique=False)
    op.create_index(op.f('ix_pipeline_configs_version'), 'pipeline_configs', ['version'], unique=False)

    # Create pipeline_executions table
    op.create_table('pipeline_executions',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('pipeline_config_id', postgresql.UUID(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='pending'),
        sa.Column('triggered_by', sa.String(), nullable=False, default='manual'),
        sa.Column('task_id', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('input_records', sa.Integer(), nullable=True),
        sa.Column('output_records', sa.Integer(), nullable=True),
        sa.Column('records_failed', sa.Integer(), nullable=True),
        sa.Column('data_version_id', postgresql.UUID(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('execution_log', sa.JSON(), nullable=False, default=[]),
        sa.Column('output_path', sa.String(), nullable=True),
        sa.Column('output_version', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', postgresql.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['data_version_id'], ['data_source_uploads.id'], ),
        sa.ForeignKeyConstraint(['pipeline_config_id'], ['pipeline_configs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pipeline_executions_pipeline_config_id'), 'pipeline_executions', ['pipeline_config_id'], unique=False)
    op.create_index(op.f('ix_pipeline_executions_status'), 'pipeline_executions', ['status'], unique=False)
    op.create_index(op.f('ix_pipeline_executions_task_id'), 'pipeline_executions', ['task_id'], unique=False)

    # Create pipeline_execution_steps table
    op.create_table('pipeline_execution_steps',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('execution_id', postgresql.UUID(), nullable=False),
        sa.Column('step_index', sa.Integer(), nullable=False),
        sa.Column('step_name', sa.String(), nullable=False),
        sa.Column('step_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='pending'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('input_records', sa.Integer(), nullable=True),
        sa.Column('output_records', sa.Integer(), nullable=True),
        sa.Column('step_config', sa.JSON(), nullable=False, default={}),
        sa.Column('result_summary', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['execution_id'], ['pipeline_executions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pipeline_execution_steps_execution_id'), 'pipeline_execution_steps', ['execution_id'], unique=False)

    # Create transformation_scripts table
    op.create_table('transformation_scripts',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('pipeline_config_id', postgresql.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('script_type', sa.String(), nullable=False),
        sa.Column('script_content', sa.Text(), nullable=False),
        sa.Column('script_hash', sa.String(), nullable=False),
        sa.Column('is_validated', sa.Boolean(), nullable=False, default=False),
        sa.Column('validation_errors', sa.JSON(), nullable=True),
        sa.Column('allowed_imports', sa.JSON(), nullable=False, default=[]),
        sa.Column('resource_limits', sa.JSON(), nullable=False, default={}),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('is_current_version', sa.Boolean(), nullable=False, default=True),
        sa.Column('parent_version_id', postgresql.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', postgresql.UUID(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', postgresql.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['parent_version_id'], ['transformation_scripts.id'], ),
        sa.ForeignKeyConstraint(['pipeline_config_id'], ['pipeline_configs.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transformation_scripts_pipeline_config_id'), 'transformation_scripts', ['pipeline_config_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_transformation_scripts_pipeline_config_id'), table_name='transformation_scripts')
    op.drop_table('transformation_scripts')
    op.drop_index(op.f('ix_pipeline_execution_steps_execution_id'), table_name='pipeline_execution_steps')
    op.drop_table('pipeline_execution_steps')
    op.drop_index(op.f('ix_pipeline_executions_task_id'), table_name='pipeline_executions')
    op.drop_index(op.f('ix_pipeline_executions_status'), table_name='pipeline_executions')
    op.drop_index(op.f('ix_pipeline_executions_pipeline_config_id'), table_name='pipeline_executions')
    op.drop_table('pipeline_executions')
    op.drop_index(op.f('ix_pipeline_configs_version'), table_name='pipeline_configs')
    op.drop_index(op.f('ix_pipeline_configs_study_id'), table_name='pipeline_configs')
    op.drop_index(op.f('ix_pipeline_configs_name'), table_name='pipeline_configs')
    op.drop_table('pipeline_configs')