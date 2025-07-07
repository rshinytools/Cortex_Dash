# ABOUTME: Consolidated initial schema migration combining all models
# ABOUTME: Created to resolve migration conflicts and establish clean baseline

"""Consolidated initial schema with all models

Revision ID: consolidated_initial_schema
Revises: 
Create Date: 2025-01-07

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'consolidated_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create ENUM types
    op.execute("CREATE TYPE widgetcategory AS ENUM ('metrics', 'charts', 'tables', 'clinical', 'monitoring', 'analytics', 'custom')")
    op.execute("CREATE TYPE dashboardcategory AS ENUM ('clinical', 'safety', 'efficacy', 'operations', 'quality', 'custom')")
    op.execute("CREATE TYPE menuitemtype AS ENUM ('dashboard', 'external_link', 'divider')")
    op.execute("CREATE TYPE datasourcetype AS ENUM ('medidata_api', 'zip_upload', 'sftp', 'folder_sync', 'edc_api', 'aws_s3', 'azure_blob')")
    op.execute("CREATE TYPE datasourcestatus AS ENUM ('active', 'inactive', 'error', 'testing')")
    op.execute("CREATE TYPE refreshtype AS ENUM ('manual', 'scheduled', 'triggered')")
    op.execute("CREATE TYPE schedulestatus AS ENUM ('active', 'paused', 'disabled')")
    op.execute("CREATE TYPE executionstatus AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled')")
    op.execute("CREATE TYPE notificationchannel AS ENUM ('email', 'sms', 'webhook', 'in_app')")
    op.execute("CREATE TYPE entitytype AS ENUM ('study', 'organization', 'global')")
    op.execute("CREATE TYPE auditaction AS ENUM ('create', 'update', 'delete', 'approve', 'reject')")
    op.execute("CREATE TYPE templatestatus AS ENUM ('DRAFT', 'PUBLISHED', 'DEPRECATED', 'ARCHIVED')")
    op.execute("CREATE TYPE inheritancetype AS ENUM ('NONE', 'EXTENDS', 'INCLUDES')")

    # Organization table
    op.create_table(
        'organization',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_organization_name', 'organization', ['name'], unique=True)

    # User table
    op.create_table(
        'user',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('org_id', sa.UUID(), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.Column('preferences', sa.JSON(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_email', 'user', ['email'], unique=True)
    op.create_index('ix_user_org_id', 'user', ['org_id'])

    # Study table
    op.create_table(
        'study',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('protocol_number', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('org_id', sa.UUID(), nullable=False),
        sa.Column('therapeutic_area', sa.String(length=100), nullable=True),
        sa.Column('phase', sa.String(length=20), nullable=True),
        sa.Column('sponsor', sa.String(length=255), nullable=True),
        sa.Column('indication', sa.String(length=255), nullable=True),
        sa.Column('study_type', sa.String(length=50), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('expected_enrollment', sa.Integer(), nullable=True),
        sa.Column('actual_enrollment', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('primary_endpoint', sa.Text(), nullable=True),
        sa.Column('secondary_endpoints', sa.JSON(), nullable=True),
        sa.Column('inclusion_criteria', sa.JSON(), nullable=True),
        sa.Column('exclusion_criteria', sa.JSON(), nullable=True),
        sa.Column('study_design', sa.Text(), nullable=True),
        sa.Column('randomization_method', sa.String(length=100), nullable=True),
        sa.Column('blinding_type', sa.String(length=50), nullable=True),
        sa.Column('number_of_sites', sa.Integer(), nullable=True),
        sa.Column('countries', sa.JSON(), nullable=True),
        sa.Column('regulatory_status', sa.JSON(), nullable=True),
        sa.Column('data_collection_status', sa.String(length=50), nullable=True),
        sa.Column('compliance_frameworks', sa.JSON(), nullable=True),
        sa.Column('gcp_compliance', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('cfr_part11_compliance', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('hipaa_compliance', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('gdpr_compliance', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('ich_compliance', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('iso_compliance', sa.String(length=100), nullable=True),
        sa.Column('last_audit_date', sa.Date(), nullable=True),
        sa.Column('next_audit_date', sa.Date(), nullable=True),
        sa.Column('audit_findings', sa.JSON(), nullable=True),
        sa.Column('corrective_actions', sa.JSON(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('field_mappings', sa.JSON(), nullable=True),
        sa.Column('pipeline_config', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_study_name', 'study', ['name'])
    op.create_index('ix_study_org_id', 'study', ['org_id'])
    op.create_index('ix_study_code', 'study', ['code'])

    # Activity Log table
    op.create_table(
        'activity_log',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('org_id', sa.UUID(), nullable=True),
        sa.Column('study_id', sa.UUID(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_activity_log_user_id', 'activity_log', ['user_id'])
    op.create_index('ix_activity_log_org_id', 'activity_log', ['org_id'])
    op.create_index('ix_activity_log_timestamp', 'activity_log', ['timestamp'])
    op.create_index('idx_activity_log_user_timestamp', 'activity_log', ['user_id', 'timestamp'])
    op.create_index('idx_activity_log_org_timestamp', 'activity_log', ['org_id', 'timestamp'])

    # Data Source table
    op.create_table(
        'data_source',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', postgresql.ENUM('medidata_api', 'zip_upload', 'sftp', 'folder_sync', 'edc_api', 'aws_s3', 'azure_blob', name='datasourcetype'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('status', postgresql.ENUM('active', 'inactive', 'error', 'testing', name='datasourcestatus'), nullable=False),
        sa.Column('last_connected', sa.DateTime(), nullable=True),
        sa.Column('last_sync', sa.DateTime(), nullable=True),
        sa.Column('next_sync', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('study_id', sa.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('sync_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_synced', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('data_volume_mb', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('medidata_study_oid', sa.String(length=100), nullable=True),
        sa.Column('medidata_environment', sa.String(length=50), nullable=True),
        sa.Column('upload_path', sa.String(length=500), nullable=True),
        sa.Column('allowed_file_types', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_data_source_name', 'data_source', ['name'])
    op.create_index('ix_data_source_study_id', 'data_source', ['study_id'])
    op.create_index('ix_data_source_type', 'data_source', ['type'])
    op.create_index('idx_data_source_study_type', 'data_source', ['study_id', 'type'])

    # Item table (from template)
    op.create_table(
        'item',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_item_title', 'item', ['title'])
    op.create_index('ix_item_owner_id', 'item', ['owner_id'])

    # Widget Definitions table
    op.create_table(
        'widget_definitions',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', postgresql.ENUM('metrics', 'charts', 'tables', 'clinical', 'monitoring', 'analytics', 'custom', name='widgetcategory'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('config_schema', sa.JSON(), nullable=False),
        sa.Column('default_config', sa.JSON(), nullable=True),
        sa.Column('size_constraints', sa.JSON(), nullable=True),
        sa.Column('data_requirements', sa.JSON(), nullable=True),
        sa.Column('preview_image', sa.String(length=500), nullable=True),
        sa.Column('documentation_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('idx_widget_definitions_category', 'widget_definitions', ['category'])
    op.create_index('idx_widget_definitions_category_active', 'widget_definitions', ['category', 'is_active'])

    # Dashboard Templates table
    op.create_table(
        'dashboard_templates',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', postgresql.ENUM('clinical', 'safety', 'efficacy', 'operations', 'quality', 'custom', name='dashboardcategory'), nullable=False),
        sa.Column('template_structure', sa.JSON(), nullable=False),
        sa.Column('required_fields', sa.JSON(), nullable=True),
        sa.Column('default_config', sa.JSON(), nullable=True),
        sa.Column('preview_image', sa.String(length=500), nullable=True),
        sa.Column('major_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('minor_version', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('patch_version', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', postgresql.ENUM('DRAFT', 'PUBLISHED', 'DEPRECATED', 'ARCHIVED', name='templatestatus'), nullable=False, server_default='DRAFT'),
        sa.Column('parent_template_id', sa.UUID(), nullable=True),
        sa.Column('inheritance_type', postgresql.ENUM('NONE', 'EXTENDS', 'INCLUDES', name='inheritancetype'), nullable=False, server_default='NONE'),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('screenshot_urls', sa.JSON(), nullable=True),
        sa.Column('documentation_url', sa.String(length=500), nullable=True),
        sa.Column('average_rating', sa.Float(), nullable=True),
        sa.Column('total_ratings', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['parent_template_id'], ['dashboard_templates.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('idx_dashboard_templates_category', 'dashboard_templates', ['category'])
    op.create_index('idx_dashboard_templates_category_active', 'dashboard_templates', ['category', 'is_active'])
    op.create_index('idx_dashboard_templates_status', 'dashboard_templates', ['status'])
    op.create_index('idx_dashboard_templates_parent_id', 'dashboard_templates', ['parent_template_id'])
    op.create_index('idx_dashboard_templates_public', 'dashboard_templates', ['is_public'])
    op.create_index('idx_dashboard_templates_category_public', 'dashboard_templates', ['category', 'is_public'])

    # Study Dashboards table
    op.create_table(
        'study_dashboards',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('study_id', sa.UUID(), nullable=False),
        sa.Column('dashboard_template_id', sa.UUID(), nullable=False),
        sa.Column('customizations', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['dashboard_template_id'], ['dashboard_templates.id'], ),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_study_dashboards_study_id', 'study_dashboards', ['study_id'])
    op.create_index('idx_study_dashboards_template_id', 'study_dashboards', ['dashboard_template_id'])
    op.create_index('idx_study_dashboards_study_template', 'study_dashboards', ['study_id', 'dashboard_template_id'])

    # Dashboard Config Audit table
    op.create_table(
        'dashboard_config_audit',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('entity_type', postgresql.ENUM('study', 'organization', 'global', name='entitytype'), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=True),
        sa.Column('dashboard_id', sa.UUID(), nullable=True),
        sa.Column('action', postgresql.ENUM('create', 'update', 'delete', 'approve', 'reject', name='auditaction'), nullable=False),
        sa.Column('changes', sa.JSON(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('performed_by', sa.UUID(), nullable=False),
        sa.Column('approved_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['approved_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['performed_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_dashboard_config_audit_entity', 'dashboard_config_audit', ['entity_type', 'entity_id'])
    op.create_index('idx_dashboard_config_audit_dashboard', 'dashboard_config_audit', ['dashboard_id'])
    op.create_index('idx_dashboard_config_audit_timestamp', 'dashboard_config_audit', ['created_at'])

    # Org Admin Permission table
    op.create_table(
        'org_admin_permission',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('org_id', sa.UUID(), nullable=False),
        sa.Column('can_manage_users', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_manage_studies', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_manage_dashboards', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_manage_settings', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_view_audit_logs', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('granted_by', sa.UUID(), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['granted_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'org_id')
    )

    # Template versions table
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
        sa.ForeignKeyConstraint(['template_id'], ['dashboard_templates.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_template_versions_template_id', 'template_versions', ['template_id'])
    op.create_index('idx_template_versions_version', 'template_versions', ['major_version', 'minor_version', 'patch_version'])

    # Template reviews table
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
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        sa.ForeignKeyConstraint(['template_id'], ['dashboard_templates.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_template_reviews_template_id', 'template_reviews', ['template_id'])
    op.create_index('idx_template_reviews_rating', 'template_reviews', ['rating'])

    # Refresh Schedule tables (commented out as they were causing issues)
    # Will be added in a separate migration if needed
    
    # Add check constraints
    op.create_check_constraint(
        'check_study_dates',
        'study',
        'end_date IS NULL OR end_date >= start_date'
    )
    
    op.create_check_constraint(
        'check_study_enrollment',
        'study',
        'actual_enrollment IS NULL OR expected_enrollment IS NULL OR actual_enrollment <= expected_enrollment * 1.2'
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table('template_reviews')
    op.drop_table('template_versions')
    op.drop_table('org_admin_permission')
    op.drop_table('dashboard_config_audit')
    op.drop_table('study_dashboards')
    op.drop_table('dashboard_templates')
    op.drop_table('widget_definitions')
    op.drop_table('item')
    op.drop_table('data_source')
    op.drop_table('activity_log')
    op.drop_table('study')
    op.drop_table('user')
    op.drop_table('organization')
    
    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS inheritancetype')
    op.execute('DROP TYPE IF EXISTS templatestatus')
    op.execute('DROP TYPE IF EXISTS auditaction')
    op.execute('DROP TYPE IF EXISTS entitytype')
    op.execute('DROP TYPE IF EXISTS notificationchannel')
    op.execute('DROP TYPE IF EXISTS executionstatus')
    op.execute('DROP TYPE IF EXISTS schedulestatus')
    op.execute('DROP TYPE IF EXISTS refreshtype')
    op.execute('DROP TYPE IF EXISTS datasourcestatus')
    op.execute('DROP TYPE IF EXISTS datasourcetype')
    op.execute('DROP TYPE IF EXISTS menuitemtype')
    op.execute('DROP TYPE IF EXISTS dashboardcategory')
    op.execute('DROP TYPE IF EXISTS widgetcategory')