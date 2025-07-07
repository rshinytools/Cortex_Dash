# ABOUTME: Alembic migration for adding clinical models
# ABOUTME: Adds Organization, Study, ActivityLog, and DataSource tables

"""Add clinical models - Organization, Study, ActivityLog, DataSource

Revision ID: clinical_models_001
Revises: d98dd8ec85a3
Create Date: 2025-01-04

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'clinical_models_001'
down_revision = 'd98dd8ec85a3'
branch_labels = None
depends_on = None


def upgrade():
    # Create organization table
    op.create_table('organization',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('license_type', sa.String(length=50), nullable=False, default='trial'),
        sa.Column('max_users', sa.Integer(), nullable=False, default=10),
        sa.Column('max_studies', sa.Integer(), nullable=False, default=5),
        sa.Column('active', sa.Boolean(), nullable=False, default=True),
        sa.Column('features', postgresql.JSON(), nullable=False, default={}),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('compliance_settings', postgresql.JSON(), nullable=False, default={}),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_organization_slug'), 'organization', ['slug'], unique=True)
    
    # Update user table to add organization relationship
    op.add_column('user', sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('user', sa.Column('role', sa.String(length=50), nullable=False, default='viewer'))
    op.add_column('user', sa.Column('department', sa.String(length=100), nullable=True))
    op.add_column('user', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('user', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('user', sa.Column('last_login', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, default=0))
    op.add_column('user', sa.Column('locked_until', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('password_changed_at', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('force_password_change', sa.Boolean(), nullable=False, default=False))
    op.add_column('user', sa.Column('preferences', postgresql.JSON(), nullable=False, default={}))
    op.create_foreign_key('fk_user_org_id', 'user', 'organization', ['org_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_user_created_by', 'user', 'user', ['created_by'], ['id'])
    op.create_foreign_key('fk_user_updated_by', 'user', 'user', ['updated_by'], ['id'])
    
    # Create study table
    op.create_table('study',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('protocol_number', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='setup'),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('folder_path', sa.String(length=500), nullable=True),
        sa.Column('pipeline_config', postgresql.JSON(), nullable=False, default={}),
        sa.Column('dashboard_config', postgresql.JSON(), nullable=False, default={}),
        sa.Column('metadata', postgresql.JSON(), nullable=False, default={}),
        sa.ForeignKeyConstraint(['created_by'], ['user.id']),
        sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('protocol_number')
    )
    op.create_index(op.f('ix_study_org_id'), 'study', ['org_id'], unique=False)
    op.create_index(op.f('ix_study_protocol_number'), 'study', ['protocol_number'], unique=True)
    op.create_index(op.f('ix_study_status'), 'study', ['status'], unique=False)
    
    # Create activity_log table
    op.create_table('activity_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('details', postgresql.JSON(), nullable=False, default={}),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, default=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_log_action'), 'activity_log', ['action'], unique=False)
    op.create_index(op.f('ix_activity_log_created_at'), 'activity_log', ['created_at'], unique=False)
    op.create_index(op.f('ix_activity_log_org_id'), 'activity_log', ['org_id'], unique=False)
    op.create_index(op.f('ix_activity_log_resource_type'), 'activity_log', ['resource_type'], unique=False)
    op.create_index(op.f('ix_activity_log_user_id'), 'activity_log', ['user_id'], unique=False)
    
    # Create data_source table
    op.create_table('data_source',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('config', postgresql.JSON(), nullable=False, default={}),
        sa.Column('active', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_sync', sa.DateTime(), nullable=True),
        sa.Column('sync_status', sa.String(length=50), nullable=True),
        sa.Column('sync_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['user.id']),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_source_active'), 'data_source', ['active'], unique=False)
    op.create_index(op.f('ix_data_source_study_id'), 'data_source', ['study_id'], unique=False)
    op.create_index(op.f('ix_data_source_type'), 'data_source', ['type'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_data_source_type'), table_name='data_source')
    op.drop_index(op.f('ix_data_source_study_id'), table_name='data_source')
    op.drop_index(op.f('ix_data_source_active'), table_name='data_source')
    op.drop_table('data_source')
    
    op.drop_index(op.f('ix_activity_log_user_id'), table_name='activity_log')
    op.drop_index(op.f('ix_activity_log_resource_type'), table_name='activity_log')
    op.drop_index(op.f('ix_activity_log_org_id'), table_name='activity_log')
    op.drop_index(op.f('ix_activity_log_created_at'), table_name='activity_log')
    op.drop_index(op.f('ix_activity_log_action'), table_name='activity_log')
    op.drop_table('activity_log')
    
    op.drop_index(op.f('ix_study_status'), table_name='study')
    op.drop_index(op.f('ix_study_protocol_number'), table_name='study')
    op.drop_index(op.f('ix_study_org_id'), table_name='study')
    op.drop_table('study')
    
    # Drop user columns
    op.drop_constraint('fk_user_updated_by', 'user', type_='foreignkey')
    op.drop_constraint('fk_user_created_by', 'user', type_='foreignkey')
    op.drop_constraint('fk_user_org_id', 'user', type_='foreignkey')
    op.drop_column('user', 'preferences')
    op.drop_column('user', 'force_password_change')
    op.drop_column('user', 'password_changed_at')
    op.drop_column('user', 'locked_until')
    op.drop_column('user', 'failed_login_attempts')
    op.drop_column('user', 'last_login')
    op.drop_column('user', 'updated_by')
    op.drop_column('user', 'updated_at')
    op.drop_column('user', 'created_by')
    op.drop_column('user', 'created_at')
    op.drop_column('user', 'department')
    op.drop_column('user', 'role')
    op.drop_column('user', 'org_id')
    
    op.drop_index(op.f('ix_organization_slug'), table_name='organization')
    op.drop_table('organization')