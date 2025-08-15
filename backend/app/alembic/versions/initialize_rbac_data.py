# ABOUTME: Initialize RBAC with comprehensive permissions and role assignments
# ABOUTME: Sets up complete permission matrix for all system roles

"""Initialize RBAC Data

Revision ID: initialize_rbac_data
Revises: comprehensive_rbac_system
Create Date: 2025-01-14 20:05:00

"""
from alembic import op
import sqlalchemy as sa
from uuid import uuid4
from datetime import datetime

# revision identifiers
revision = 'initialize_rbac_data'
down_revision = 'comprehensive_rbac_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Initialize RBAC data"""
    
    # Define all system permissions
    permissions = [
        # Dashboard Management
        ('dashboard.view', 'dashboard', 'view', 'View dashboards'),
        ('dashboard.create', 'dashboard', 'create', 'Create new dashboards'),
        ('dashboard.edit', 'dashboard', 'edit', 'Edit existing dashboards'),
        ('dashboard.delete', 'dashboard', 'delete', 'Delete dashboards'),
        ('dashboard.share', 'dashboard', 'share', 'Share dashboards with others'),
        
        # Study Management
        ('study.view', 'study', 'view', 'View studies'),
        ('study.create', 'study', 'create', 'Create new studies'),
        ('study.edit', 'study', 'edit', 'Edit study configuration'),
        ('study.delete', 'study', 'delete', 'Delete studies'),
        ('study.initialize', 'study', 'initialize', 'Initialize study data'),
        
        # Data Management
        ('data.view', 'data', 'view', 'View data'),
        ('data.upload', 'data', 'upload', 'Upload data files'),
        ('data.export', 'data', 'export', 'Export data'),
        ('data.delete', 'data', 'delete', 'Delete data'),
        ('data.transform', 'data', 'transform', 'Run data transformations'),
        
        # Widget Management
        ('widget.view', 'widget', 'view', 'View widgets'),
        ('widget.create', 'widget', 'create', 'Create widgets'),
        ('widget.edit', 'widget', 'edit', 'Edit widget configuration'),
        ('widget.delete', 'widget', 'delete', 'Delete widgets'),
        ('widget.execute', 'widget', 'execute', 'Execute widget queries'),
        
        # User Management
        ('user.view', 'user', 'view', 'View users'),
        ('user.create', 'user', 'create', 'Create new users'),
        ('user.edit', 'user', 'edit', 'Edit user profiles'),
        ('user.delete', 'user', 'delete', 'Delete users'),
        ('user.manage_roles', 'user', 'manage_roles', 'Manage user roles'),
        
        # Organization Management
        ('org.view', 'org', 'view', 'View organization details'),
        ('org.edit', 'org', 'edit', 'Edit organization settings'),
        ('org.manage_users', 'org', 'manage_users', 'Manage organization users'),
        ('org.manage_studies', 'org', 'manage_studies', 'Manage organization studies'),
        
        # Template Management
        ('template.view', 'template', 'view', 'View templates'),
        ('template.create', 'template', 'create', 'Create templates'),
        ('template.edit', 'template', 'edit', 'Edit templates'),
        ('template.delete', 'template', 'delete', 'Delete templates'),
        ('template.publish', 'template', 'publish', 'Publish templates'),
        
        # Pipeline Management
        ('pipeline.view', 'pipeline', 'view', 'View pipelines'),
        ('pipeline.create', 'pipeline', 'create', 'Create pipelines'),
        ('pipeline.edit', 'pipeline', 'edit', 'Edit pipelines'),
        ('pipeline.execute', 'pipeline', 'execute', 'Execute pipelines'),
        ('pipeline.delete', 'pipeline', 'delete', 'Delete pipelines'),
        
        # RBAC Management
        ('rbac.view', 'rbac', 'view', 'View roles and permissions'),
        ('rbac.manage', 'rbac', 'manage', 'Manage roles and permissions'),
        ('rbac.assign', 'rbac', 'assign', 'Assign roles to users'),
        
        # Audit Management
        ('audit.view', 'audit', 'view', 'View audit logs'),
        ('audit.export', 'audit', 'export', 'Export audit logs'),
        
        # System Management
        ('system.view', 'system', 'view', 'View system settings'),
        ('system.configure', 'system', 'configure', 'Configure system settings'),
        ('system.backup', 'system', 'backup', 'Create system backups'),
        ('system.restore', 'system', 'restore', 'Restore from backups'),
    ]
    
    # Insert permissions
    for name, resource, action, description in permissions:
        perm_id = str(uuid4())
        op.execute(
            f"""INSERT INTO permissions (id, name, resource, action, description, is_system, created_at)
                VALUES ('{perm_id}'::UUID, '{name}', '{resource}', '{action}', '{description}', true, NOW())"""
        )
    
    # Define roles with priority
    roles = [
        ('system_admin', 'System Administrator', 'Full system access with all permissions', 1),
        ('org_admin', 'Organization Administrator', 'Manage organization, users, and studies', 10),
        ('study_manager', 'Study Manager', 'Manage specific studies and their data', 20),
        ('data_analyst', 'Data Analyst', 'Analyze data and create visualizations', 30),
        ('viewer', 'Viewer', 'Read-only access to dashboards and reports', 40),
    ]
    
    # Insert roles and store their IDs
    role_ids = {}
    for name, display_name, description, priority in roles:
        role_id = str(uuid4())
        role_ids[name] = role_id
        op.execute(
            f"""INSERT INTO roles (id, name, display_name, description, priority, is_system, is_active, created_at)
                VALUES ('{role_id}'::UUID, '{name}', '{display_name}', '{description}', {priority}, true, true, NOW())"""
        )
    
    # Define role-permission mappings
    role_permissions = {
        'system_admin': [
            # System admin gets ALL permissions
            'dashboard.view', 'dashboard.create', 'dashboard.edit', 'dashboard.delete', 'dashboard.share',
            'study.view', 'study.create', 'study.edit', 'study.delete', 'study.initialize',
            'data.view', 'data.upload', 'data.export', 'data.delete', 'data.transform',
            'widget.view', 'widget.create', 'widget.edit', 'widget.delete', 'widget.execute',
            'user.view', 'user.create', 'user.edit', 'user.delete', 'user.manage_roles',
            'org.view', 'org.edit', 'org.manage_users', 'org.manage_studies',
            'template.view', 'template.create', 'template.edit', 'template.delete', 'template.publish',
            'pipeline.view', 'pipeline.create', 'pipeline.edit', 'pipeline.execute', 'pipeline.delete',
            'rbac.view', 'rbac.manage', 'rbac.assign',
            'audit.view', 'audit.export',
            'system.view', 'system.configure', 'system.backup', 'system.restore',
        ],
        'org_admin': [
            'dashboard.view', 'dashboard.create', 'dashboard.edit', 'dashboard.share',
            'study.view', 'study.create', 'study.edit', 'study.initialize',
            'data.view', 'data.upload', 'data.export',
            'widget.view', 'widget.create', 'widget.edit', 'widget.execute',
            'user.view', 'user.create', 'user.edit', 'user.manage_roles',
            'org.view', 'org.edit', 'org.manage_users', 'org.manage_studies',
            'template.view', 'template.create', 'template.edit',
            'pipeline.view', 'pipeline.create', 'pipeline.edit', 'pipeline.execute',
            'rbac.view',
            'audit.view',
        ],
        'study_manager': [
            'dashboard.view', 'dashboard.create', 'dashboard.edit',
            'study.view', 'study.edit', 'study.initialize',
            'data.view', 'data.upload', 'data.export', 'data.transform',
            'widget.view', 'widget.create', 'widget.edit', 'widget.execute',
            'user.view',
            'template.view',
            'pipeline.view', 'pipeline.execute',
            'audit.view',
        ],
        'data_analyst': [
            'dashboard.view', 'dashboard.create', 'dashboard.edit',
            'study.view',
            'data.view', 'data.export',
            'widget.view', 'widget.execute',
            'template.view',
            'pipeline.view',
        ],
        'viewer': [
            'dashboard.view',
            'study.view',
            'data.view',
            'widget.view',
        ],
    }
    
    # Get permission IDs
    perm_ids = {}
    for name, _, _, _ in permissions:
        result = op.get_bind().execute(
            sa.text(f"SELECT id FROM permissions WHERE name = '{name}'")
        ).fetchone()
        if result:
            perm_ids[name] = str(result[0])
    
    # Assign permissions to roles
    for role_name, permission_names in role_permissions.items():
        role_id = role_ids[role_name]
        for perm_name in permission_names:
            if perm_name in perm_ids:
                rp_id = str(uuid4())
                op.execute(
                    f"""INSERT INTO role_permissions (id, role_id, permission_id, granted_at, is_active)
                        VALUES ('{rp_id}'::UUID, '{role_id}'::UUID, '{perm_ids[perm_name]}'::UUID, NOW(), true)"""
                )
    
    # Assign system_admin role to the default admin user
    admin_result = op.get_bind().execute(
        sa.text("SELECT id FROM \"user\" WHERE email = 'admin@sagarmatha.ai'")
    ).fetchone()
    
    if admin_result:
        admin_id = str(admin_result[0])
        ur_id = str(uuid4())
        op.execute(
            f"""INSERT INTO user_roles (id, user_id, role_id, assigned_at, is_active)
                VALUES ('{ur_id}'::UUID, '{admin_id}'::UUID, '{role_ids['system_admin']}'::UUID, NOW(), true)"""
        )


def downgrade() -> None:
    """Remove RBAC data"""
    op.execute("DELETE FROM user_roles")
    op.execute("DELETE FROM role_permissions")
    op.execute("DELETE FROM roles")
    op.execute("DELETE FROM permissions")