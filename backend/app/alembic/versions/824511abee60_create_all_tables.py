"""create_all_tables

Revision ID: 824511abee60
Revises: simple_initial_schema
Create Date: 2025-07-07 16:32:25.298668

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '824511abee60'
down_revision = 'simple_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('organization',
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('slug', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('features', sa.JSON(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('license_type', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('max_users', sa.Integer(), nullable=False),
    sa.Column('max_studies', sa.Integer(), nullable=False),
    sa.Column('compliance_settings', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_name'), 'organization', ['name'], unique=False)
    op.create_index(op.f('ix_organization_slug'), 'organization', ['slug'], unique=True)
    op.create_table('user',
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_superuser', sa.Boolean(), nullable=False),
    sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
    sa.Column('org_id', sa.Uuid(), nullable=True),
    sa.Column('role', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('department', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.Column('password_changed_at', sa.DateTime(), nullable=True),
    sa.Column('failed_login_attempts', sa.Integer(), nullable=False),
    sa.Column('locked_until', sa.DateTime(), nullable=True),
    sa.Column('force_password_change', sa.Boolean(), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=True),
    sa.Column('updated_by', sa.Uuid(), nullable=True),
    sa.Column('preferences', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_table('dashboard_config_audit',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('entity_type', sa.Enum('WIDGET', 'DASHBOARD', 'MENU', 'STUDY_DASHBOARD', 'PERMISSION', name='entitytype'), nullable=False),
    sa.Column('entity_id', sa.Uuid(), nullable=False),
    sa.Column('action', sa.Enum('CREATE', 'UPDATE', 'DELETE', 'ASSIGN', 'UNASSIGN', 'ACTIVATE', 'DEACTIVATE', name='auditaction'), nullable=False),
    sa.Column('changes', sa.JSON(), nullable=True),
    sa.Column('performed_by', sa.Uuid(), nullable=False),
    sa.Column('performed_at', sa.DateTime(), nullable=False),
    sa.Column('ip_address', postgresql.INET(), nullable=True),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['performed_by'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_config_audit_action'), 'dashboard_config_audit', ['action'], unique=False)
    op.create_index(op.f('ix_dashboard_config_audit_entity_id'), 'dashboard_config_audit', ['entity_id'], unique=False)
    op.create_index(op.f('ix_dashboard_config_audit_entity_type'), 'dashboard_config_audit', ['entity_type'], unique=False)
    op.create_index(op.f('ix_dashboard_config_audit_performed_at'), 'dashboard_config_audit', ['performed_at'], unique=False)
    op.create_index(op.f('ix_dashboard_config_audit_performed_by'), 'dashboard_config_audit', ['performed_by'], unique=False)
    op.create_table('dashboard_templates',
    sa.Column('code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('category', sa.Enum('OVERVIEW', 'SAFETY', 'EFFICACY', 'OPERATIONAL', 'QUALITY', 'CUSTOM', name='dashboardcategory'), nullable=False),
    sa.Column('major_version', sa.Integer(), nullable=False),
    sa.Column('minor_version', sa.Integer(), nullable=False),
    sa.Column('patch_version', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('DRAFT', 'PUBLISHED', 'DEPRECATED', 'ARCHIVED', name='templatestatus'), nullable=False),
    sa.Column('parent_template_id', sa.Uuid(), nullable=True),
    sa.Column('inheritance_type', sa.Enum('NONE', 'EXTENDS', 'INCLUDES', name='inheritancetype'), nullable=False),
    sa.Column('template_structure', sa.JSON(), nullable=True),
    sa.Column('tags', sa.JSON(), nullable=True),
    sa.Column('screenshot_urls', sa.JSON(), nullable=True),
    sa.Column('documentation_url', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
    sa.Column('average_rating', sa.Float(), nullable=True),
    sa.Column('total_ratings', sa.Integer(), nullable=False),
    sa.Column('download_count', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_public', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['parent_template_id'], ['dashboard_templates.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_templates_code'), 'dashboard_templates', ['code'], unique=True)
    op.create_table('item',
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('org_admin_permissions',
    sa.Column('org_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('permission_set', sa.JSON(), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('granted_by', sa.Uuid(), nullable=False),
    sa.Column('granted_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['granted_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('org_id', 'user_id', name='unique_org_user_permission')
    )
    op.create_table('widget_definitions',
    sa.Column('code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('category', sa.Enum('METRICS', 'CHARTS', 'TABLES', 'MAPS', 'SPECIALIZED', name='widgetcategory'), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('config_schema', sa.JSON(), nullable=True),
    sa.Column('default_config', sa.JSON(), nullable=True),
    sa.Column('size_constraints', sa.JSON(), nullable=True),
    sa.Column('data_requirements', sa.JSON(), nullable=True),
    sa.Column('data_contract', sa.JSON(), nullable=True),
    sa.Column('permissions', sa.JSON(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_widget_definitions_code'), 'widget_definitions', ['code'], unique=True)
    op.create_table('study',
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('protocol_number', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('phase', sa.Enum('PHASE_1', 'PHASE_2', 'PHASE_3', 'PHASE_4', 'OBSERVATIONAL', 'EXPANDED_ACCESS', name='studyphase'), nullable=True),
    sa.Column('therapeutic_area', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
    sa.Column('indication', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
    sa.Column('planned_start_date', sa.DateTime(), nullable=True),
    sa.Column('planned_end_date', sa.DateTime(), nullable=True),
    sa.Column('actual_start_date', sa.DateTime(), nullable=True),
    sa.Column('actual_end_date', sa.DateTime(), nullable=True),
    sa.Column('config', sa.JSON(), nullable=True),
    sa.Column('pipeline_config', sa.JSON(), nullable=True),
    sa.Column('dashboard_config', sa.JSON(), nullable=True),
    sa.Column('dashboard_template_id', sa.Uuid(), nullable=True),
    sa.Column('field_mappings', sa.JSON(), nullable=True),
    sa.Column('template_overrides', sa.JSON(), nullable=True),
    sa.Column('data_retention_days', sa.Integer(), nullable=False),
    sa.Column('refresh_frequency', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
    sa.Column('org_id', sa.Uuid(), nullable=False),
    sa.Column('status', sa.Enum('PLANNING', 'SETUP', 'ACTIVE', 'PAUSED', 'COMPLETED', 'ARCHIVED', name='studystatus'), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('updated_by', sa.Uuid(), nullable=True),
    sa.Column('folder_path', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
    sa.Column('protocol_version', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
    sa.Column('protocol_approved_date', sa.DateTime(), nullable=True),
    sa.Column('protocol_approved_by', sa.Uuid(), nullable=True),
    sa.Column('subject_count', sa.Integer(), nullable=False),
    sa.Column('site_count', sa.Integer(), nullable=False),
    sa.Column('data_points_count', sa.Integer(), nullable=False),
    sa.Column('last_data_update', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['dashboard_template_id'], ['dashboard_templates.id'], ),
    sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['protocol_approved_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_study_code'), 'study', ['code'], unique=False)
    op.create_index(op.f('ix_study_name'), 'study', ['name'], unique=False)
    op.create_index(op.f('ix_study_org_id'), 'study', ['org_id'], unique=False)
    op.create_index(op.f('ix_study_protocol_number'), 'study', ['protocol_number'], unique=True)
    op.create_table('template_reviews',
    sa.Column('template_id', sa.Uuid(), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=False),
    sa.Column('review_text', sa.Text(), nullable=True),
    sa.Column('is_verified_user', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('reviewed_by', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['reviewed_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['template_id'], ['dashboard_templates.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('template_versions',
    sa.Column('template_id', sa.Uuid(), nullable=False),
    sa.Column('major_version', sa.Integer(), nullable=False),
    sa.Column('minor_version', sa.Integer(), nullable=False),
    sa.Column('patch_version', sa.Integer(), nullable=False),
    sa.Column('change_description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
    sa.Column('template_structure', sa.JSON(), nullable=True),
    sa.Column('is_published', sa.Boolean(), nullable=False),
    sa.Column('migration_notes', sa.Text(), nullable=True),
    sa.Column('breaking_changes', sa.Boolean(), nullable=False),
    sa.Column('required_migrations', sa.JSON(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['template_id'], ['dashboard_templates.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('activity_log',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('action', sa.Enum('LOGIN', 'LOGOUT', 'LOGIN_FAILED', 'PASSWORD_CHANGED', 'CREATE', 'READ', 'UPDATE', 'DELETE', 'STUDY_CREATED', 'STUDY_UPDATED', 'STUDY_ARCHIVED', 'DASHBOARD_TEMPLATE_APPLIED', 'DASHBOARD_CREATED', 'DASHBOARD_UPDATED', 'DASHBOARD_DELETED', 'PIPELINE_STARTED', 'PIPELINE_COMPLETED', 'PIPELINE_FAILED', 'DATA_VIEWED', 'DATA_EXPORTED', 'DATA_UPLOADED', 'SIGNATURE_CREATED', 'PROTOCOL_APPROVED', 'AUDIT_VIEWED', 'PHI_ACCESSED', 'PHI_EXPORTED', name='activityaction'), nullable=False),
    sa.Column('resource_type', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('resource_id', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('ip_address', sqlmodel.sql.sqltypes.AutoString(length=45), nullable=True),
    sa.Column('user_agent', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
    sa.Column('details', sa.JSON(), nullable=True),
    sa.Column('study_id', sa.Uuid(), nullable=True),
    sa.Column('org_id', sa.Uuid(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('system_timestamp', sa.DateTime(), nullable=False),
    sa.Column('sequence_number', sa.BigInteger(), nullable=False),
    sa.Column('checksum', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True),
    sa.Column('old_value', sa.JSON(), nullable=True),
    sa.Column('new_value', sa.JSON(), nullable=True),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['study_id'], ['study.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_activity_org_study', 'activity_log', ['org_id', 'study_id'], unique=False)
    op.create_index('idx_activity_resource', 'activity_log', ['resource_type', 'resource_id'], unique=False)
    op.create_index('idx_activity_timestamp_user', 'activity_log', ['timestamp', 'user_id'], unique=False)
    op.create_index(op.f('ix_activity_log_action'), 'activity_log', ['action'], unique=False)
    op.create_index(op.f('ix_activity_log_org_id'), 'activity_log', ['org_id'], unique=False)
    op.create_index(op.f('ix_activity_log_resource_id'), 'activity_log', ['resource_id'], unique=False)
    op.create_index(op.f('ix_activity_log_resource_type'), 'activity_log', ['resource_type'], unique=False)
    op.create_index(op.f('ix_activity_log_sequence_number'), 'activity_log', ['sequence_number'], unique=False)
    op.create_index(op.f('ix_activity_log_study_id'), 'activity_log', ['study_id'], unique=False)
    op.create_index(op.f('ix_activity_log_timestamp'), 'activity_log', ['timestamp'], unique=False)
    op.create_index(op.f('ix_activity_log_user_id'), 'activity_log', ['user_id'], unique=False)
    op.create_table('data_source',
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('type', sa.Enum('MEDIDATA_API', 'ZIP_UPLOAD', 'SFTP', 'FOLDER_SYNC', 'EDC_API', 'AWS_S3', 'AZURE_BLOB', name='datasourcetype'), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('config', sa.JSON(), nullable=True),
    sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'ERROR', 'TESTING', name='datasourcestatus'), nullable=False),
    sa.Column('last_connected', sa.DateTime(), nullable=True),
    sa.Column('last_sync', sa.DateTime(), nullable=True),
    sa.Column('next_sync', sa.DateTime(), nullable=True),
    sa.Column('last_error', sa.Text(), nullable=True),
    sa.Column('error_count', sa.Integer(), nullable=False),
    sa.Column('study_id', sa.Uuid(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_primary', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('updated_by', sa.Uuid(), nullable=True),
    sa.Column('sync_count', sa.Integer(), nullable=False),
    sa.Column('records_synced', sa.Integer(), nullable=False),
    sa.Column('data_volume_mb', sa.Float(), nullable=False),
    sa.Column('medidata_study_oid', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
    sa.Column('medidata_environment', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
    sa.Column('upload_path', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
    sa.Column('allowed_file_types', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['study_id'], ['study.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_source_name'), 'data_source', ['name'], unique=False)
    op.create_index(op.f('ix_data_source_study_id'), 'data_source', ['study_id'], unique=False)
    op.create_index(op.f('ix_data_source_type'), 'data_source', ['type'], unique=False)
    op.create_table('study_dashboards',
    sa.Column('study_id', sa.Uuid(), nullable=False),
    sa.Column('dashboard_template_id', sa.Uuid(), nullable=False),
    sa.Column('customizations', sa.JSON(), nullable=True),
    sa.Column('data_mappings', sa.JSON(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_by', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['dashboard_template_id'], ['dashboard_templates.id'], ),
    sa.ForeignKeyConstraint(['study_id'], ['study.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('study_id', 'dashboard_template_id', name='unique_study_dashboard')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('study_dashboards')
    op.drop_index(op.f('ix_data_source_type'), table_name='data_source')
    op.drop_index(op.f('ix_data_source_study_id'), table_name='data_source')
    op.drop_index(op.f('ix_data_source_name'), table_name='data_source')
    op.drop_table('data_source')
    op.drop_index(op.f('ix_activity_log_user_id'), table_name='activity_log')
    op.drop_index(op.f('ix_activity_log_timestamp'), table_name='activity_log')
    op.drop_index(op.f('ix_activity_log_study_id'), table_name='activity_log')
    op.drop_index(op.f('ix_activity_log_sequence_number'), table_name='activity_log')
    op.drop_index(op.f('ix_activity_log_resource_type'), table_name='activity_log')
    op.drop_index(op.f('ix_activity_log_resource_id'), table_name='activity_log')
    op.drop_index(op.f('ix_activity_log_org_id'), table_name='activity_log')
    op.drop_index(op.f('ix_activity_log_action'), table_name='activity_log')
    op.drop_index('idx_activity_timestamp_user', table_name='activity_log')
    op.drop_index('idx_activity_resource', table_name='activity_log')
    op.drop_index('idx_activity_org_study', table_name='activity_log')
    op.drop_table('activity_log')
    op.drop_table('template_versions')
    op.drop_table('template_reviews')
    op.drop_index(op.f('ix_study_protocol_number'), table_name='study')
    op.drop_index(op.f('ix_study_org_id'), table_name='study')
    op.drop_index(op.f('ix_study_name'), table_name='study')
    op.drop_index(op.f('ix_study_code'), table_name='study')
    op.drop_table('study')
    op.drop_index(op.f('ix_widget_definitions_code'), table_name='widget_definitions')
    op.drop_table('widget_definitions')
    op.drop_table('org_admin_permissions')
    op.drop_table('item')
    op.drop_index(op.f('ix_dashboard_templates_code'), table_name='dashboard_templates')
    op.drop_table('dashboard_templates')
    op.drop_index(op.f('ix_dashboard_config_audit_performed_by'), table_name='dashboard_config_audit')
    op.drop_index(op.f('ix_dashboard_config_audit_performed_at'), table_name='dashboard_config_audit')
    op.drop_index(op.f('ix_dashboard_config_audit_entity_type'), table_name='dashboard_config_audit')
    op.drop_index(op.f('ix_dashboard_config_audit_entity_id'), table_name='dashboard_config_audit')
    op.drop_index(op.f('ix_dashboard_config_audit_action'), table_name='dashboard_config_audit')
    op.drop_table('dashboard_config_audit')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_organization_slug'), table_name='organization')
    op.drop_index(op.f('ix_organization_name'), table_name='organization')
    op.drop_table('organization')
    # ### end Alembic commands ###
