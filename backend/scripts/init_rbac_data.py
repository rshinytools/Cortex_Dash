# ABOUTME: Initialize RBAC roles and permissions in the database
# ABOUTME: Creates all system roles and assigns appropriate permissions

"""
Initialize RBAC Data Script
Creates all system roles, permissions, and assignments
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uuid import uuid4
from datetime import datetime
from sqlmodel import Session
from app.core.db import engine
from app.models.rbac import Role, Permission, RolePermission

def init_rbac_data():
    """Initialize RBAC roles and permissions"""
    db = Session(engine)
    
    try:
        # Check if data already exists
        existing_roles = db.query(Role).count()
        if existing_roles > 0:
            print(f"RBAC data already exists ({existing_roles} roles found)")
            return
        
        print("Initializing RBAC data...")
        
        # Create all permissions
        permissions_data = [
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
        
        # Create permissions
        permissions = {}
        for name, resource, action, description in permissions_data:
            permission = Permission(
                id=uuid4(),
                name=name,
                resource=resource,
                action=action,
                description=description,
                is_system=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(permission)
            permissions[name] = permission
        
        print(f"Created {len(permissions)} permissions")
        
        # Create roles
        roles_data = [
            ('system_admin', 'System Admin', 'Full system access with all permissions', True, [
                'dashboard.*', 'study.*', 'data.*', 'widget.*', 'user.*', 
                'org.*', 'template.*', 'pipeline.*', 'rbac.*', 'audit.*', 'system.*'
            ]),
            ('org_admin', 'Organization Admin', 'Manage organization resources and users', True, [
                'dashboard.*', 'study.*', 'data.*', 'widget.*', 'user.view', 
                'user.create', 'user.edit', 'org.*', 'template.*', 'pipeline.*', 'audit.view'
            ]),
            ('study_manager', 'Study Manager', 'Manage specific studies and their data', True, [
                'dashboard.view', 'dashboard.create', 'dashboard.edit', 'study.*', 
                'data.*', 'widget.*', 'template.view', 'pipeline.*', 'audit.view'
            ]),
            ('data_analyst', 'Data Analyst', 'View and analyze study data', True, [
                'dashboard.view', 'study.view', 'data.view', 'data.export', 
                'widget.view', 'widget.execute', 'template.view', 'audit.view'
            ]),
            ('viewer', 'Viewer', 'Read-only access to authorized resources', True, [
                'dashboard.view', 'study.view', 'data.view', 'widget.view', 'template.view'
            ]),
        ]
        
        # Create roles and assign permissions
        for role_name, display_name, description, is_system, permission_patterns in roles_data:
            role = Role(
                id=uuid4(),
                name=role_name,
                display_name=display_name,
                description=description,
                is_system=is_system,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(role)
            
            # Assign permissions to role
            for pattern in permission_patterns:
                if pattern.endswith('.*'):
                    # Wildcard pattern - match all permissions for resource
                    resource = pattern[:-2]
                    matching_perms = [p for name, p in permissions.items() if name.startswith(resource + '.')]
                else:
                    # Exact permission name
                    matching_perms = [permissions.get(pattern)] if pattern in permissions else []
                
                for perm in matching_perms:
                    if perm:
                        role_perm = RolePermission(
                            id=uuid4(),
                            role_id=role.id,
                            permission_id=perm.id,
                            is_active=True,
                            created_at=datetime.utcnow()
                        )
                        db.add(role_perm)
        
        print(f"Created {len(roles_data)} roles with permissions")
        
        # Commit all changes
        db.commit()
        print("RBAC data initialized successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error initializing RBAC data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_rbac_data()