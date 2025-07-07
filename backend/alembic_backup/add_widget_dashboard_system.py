"""Add widget-based dashboard system tables

Revision ID: add_widget_dashboard_system
Revises: drop_metadata_column
Create Date: 2025-01-06 10:45:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_widget_dashboard_system'
down_revision = 'drop_metadata_column'
branch_labels = None
depends_on = None


def upgrade():
    # Create widget_definitions table - System-wide widget library
    op.create_table(
        'widget_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('config_schema', sa.JSON(), nullable=False),
        sa.Column('default_config', sa.JSON(), nullable=True),
        sa.Column('size_constraints', sa.JSON(), nullable=True),
        sa.Column('data_requirements', sa.JSON(), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_widget_definitions_category'), 'widget_definitions', ['category'], unique=False)
    op.create_index(op.f('ix_widget_definitions_is_active'), 'widget_definitions', ['is_active'], unique=False)

    # Create dashboard_templates table - Pre-built dashboard configurations
    op.create_table(
        'dashboard_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('layout_config', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_dashboard_templates_category'), 'dashboard_templates', ['category'], unique=False)
    op.create_index(op.f('ix_dashboard_templates_is_active'), 'dashboard_templates', ['is_active'], unique=False)

    # Create dashboard_widgets table - Widget instances on dashboards
    op.create_table(
        'dashboard_widgets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dashboard_template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('widget_definition_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instance_config', sa.JSON(), nullable=False),
        sa.Column('position', sa.JSON(), nullable=False),
        sa.Column('data_binding', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['dashboard_template_id'], ['dashboard_templates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['widget_definition_id'], ['widget_definitions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_widgets_dashboard_template_id'), 'dashboard_widgets', ['dashboard_template_id'], unique=False)

    # Create menu_templates table - Menu structure templates
    op.create_table(
        'menu_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('menu_structure', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_menu_templates_is_active'), 'menu_templates', ['is_active'], unique=False)

    # Create study_dashboards table - Study-specific dashboard assignments
    op.create_table(
        'study_dashboards',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dashboard_template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('menu_template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('customizations', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['dashboard_template_id'], ['dashboard_templates.id'], ),
        sa.ForeignKeyConstraint(['menu_template_id'], ['menu_templates.id'], ),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('study_id', 'dashboard_template_id')
    )
    op.create_index(op.f('ix_study_dashboards_study_id'), 'study_dashboards', ['study_id'], unique=False)
    op.create_index(op.f('ix_study_dashboards_is_active'), 'study_dashboards', ['is_active'], unique=False)

    # Create org_admin_permissions table - Permission delegation for org admins
    op.create_table(
        'org_admin_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permission_set', sa.JSON(), nullable=False),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['granted_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id', 'user_id')
    )
    op.create_index(op.f('ix_org_admin_permissions_org_id'), 'org_admin_permissions', ['org_id'], unique=False)
    op.create_index(op.f('ix_org_admin_permissions_user_id'), 'org_admin_permissions', ['user_id'], unique=False)
    op.create_index(op.f('ix_org_admin_permissions_is_active'), 'org_admin_permissions', ['is_active'], unique=False)

    # Create dashboard_config_audit table - Audit log for configuration changes
    op.create_table(
        'dashboard_config_audit',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('changes', sa.JSON(), nullable=True),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('performed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['performed_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dashboard_config_audit_entity_type'), 'dashboard_config_audit', ['entity_type'], unique=False)
    op.create_index(op.f('ix_dashboard_config_audit_entity_id'), 'dashboard_config_audit', ['entity_id'], unique=False)
    op.create_index(op.f('ix_dashboard_config_audit_performed_at'), 'dashboard_config_audit', ['performed_at'], unique=False)
    op.create_index(op.f('ix_dashboard_config_audit_performed_by'), 'dashboard_config_audit', ['performed_by'], unique=False)

    # Add indexes for performance
    op.create_index('idx_widget_definitions_code_active', 'widget_definitions', ['code', 'is_active'], unique=False)
    op.create_index('idx_dashboard_templates_code_active', 'dashboard_templates', ['code', 'is_active'], unique=False)
    op.create_index('idx_study_dashboards_study_active', 'study_dashboards', ['study_id', 'is_active'], unique=False)
    op.create_index('idx_org_admin_permissions_org_user_active', 'org_admin_permissions', ['org_id', 'user_id', 'is_active'], unique=False)
    op.create_index('idx_dashboard_config_audit_entity', 'dashboard_config_audit', ['entity_type', 'entity_id'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('idx_dashboard_config_audit_entity', table_name='dashboard_config_audit')
    op.drop_index('idx_org_admin_permissions_org_user_active', table_name='org_admin_permissions')
    op.drop_index('idx_study_dashboards_study_active', table_name='study_dashboards')
    op.drop_index('idx_dashboard_templates_code_active', table_name='dashboard_templates')
    op.drop_index('idx_widget_definitions_code_active', table_name='widget_definitions')

    # Drop tables in reverse order to respect foreign key constraints
    op.drop_index(op.f('ix_dashboard_config_audit_performed_by'), table_name='dashboard_config_audit')
    op.drop_index(op.f('ix_dashboard_config_audit_performed_at'), table_name='dashboard_config_audit')
    op.drop_index(op.f('ix_dashboard_config_audit_entity_id'), table_name='dashboard_config_audit')
    op.drop_index(op.f('ix_dashboard_config_audit_entity_type'), table_name='dashboard_config_audit')
    op.drop_table('dashboard_config_audit')

    op.drop_index(op.f('ix_org_admin_permissions_is_active'), table_name='org_admin_permissions')
    op.drop_index(op.f('ix_org_admin_permissions_user_id'), table_name='org_admin_permissions')
    op.drop_index(op.f('ix_org_admin_permissions_org_id'), table_name='org_admin_permissions')
    op.drop_table('org_admin_permissions')

    op.drop_index(op.f('ix_study_dashboards_is_active'), table_name='study_dashboards')
    op.drop_index(op.f('ix_study_dashboards_study_id'), table_name='study_dashboards')
    op.drop_table('study_dashboards')

    op.drop_index(op.f('ix_menu_templates_is_active'), table_name='menu_templates')
    op.drop_table('menu_templates')

    op.drop_index(op.f('ix_dashboard_widgets_dashboard_template_id'), table_name='dashboard_widgets')
    op.drop_table('dashboard_widgets')

    op.drop_index(op.f('ix_dashboard_templates_is_active'), table_name='dashboard_templates')
    op.drop_index(op.f('ix_dashboard_templates_category'), table_name='dashboard_templates')
    op.drop_table('dashboard_templates')

    op.drop_index(op.f('ix_widget_definitions_is_active'), table_name='widget_definitions')
    op.drop_index(op.f('ix_widget_definitions_category'), table_name='widget_definitions')
    op.drop_table('widget_definitions')