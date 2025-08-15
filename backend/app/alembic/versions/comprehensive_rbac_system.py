# ABOUTME: Comprehensive RBAC system migration with proper structure
# ABOUTME: Creates all RBAC tables with correct relationships and constraints

"""Comprehensive RBAC System

Revision ID: comprehensive_rbac_system
Revises: widget_init_data_002
Create Date: 2025-01-14 20:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from uuid import uuid4

# revision identifiers
revision = 'comprehensive_rbac_system'
down_revision = 'widget_init_data_002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create comprehensive RBAC system"""
    
    # Drop existing RBAC tables if they exist (clean slate)
    op.execute("DROP TABLE IF EXISTS permission_audit_logs CASCADE")
    op.execute("DROP TABLE IF EXISTS permission_presets CASCADE")
    op.execute("DROP TABLE IF EXISTS user_roles CASCADE")
    op.execute("DROP TABLE IF EXISTS role_permissions CASCADE")
    op.execute("DROP TABLE IF EXISTS roles CASCADE")
    op.execute("DROP TABLE IF EXISTS permissions CASCADE")
    
    # Create permissions table
    op.create_table('permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column('name', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('resource', sa.String(50), nullable=False, index=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    
    # Create roles table
    op.create_table('roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column('name', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), default=100, nullable=False),  # Lower number = higher priority
        sa.Column('is_system', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create role_permissions table (many-to-many)
    op.create_table('role_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('granted_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('conditions', sa.JSON(), nullable=True),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission')
    )
    
    # Create user_roles table
    op.create_table('user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=True),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('study.id', ondelete='CASCADE'), nullable=True),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.UniqueConstraint('user_id', 'role_id', 'organization_id', 'study_id', name='uq_user_role_scope')
    )
    
    # Create permission_audit_logs table
    op.create_table('permission_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )
    
    # Create indexes for performance
    op.create_index('idx_role_permissions_role', 'role_permissions', ['role_id'])
    op.create_index('idx_role_permissions_permission', 'role_permissions', ['permission_id'])
    op.create_index('idx_user_roles_user', 'user_roles', ['user_id'])
    op.create_index('idx_user_roles_role', 'user_roles', ['role_id'])
    op.create_index('idx_user_roles_org', 'user_roles', ['organization_id'])
    op.create_index('idx_user_roles_study', 'user_roles', ['study_id'])
    op.create_index('idx_audit_user', 'permission_audit_logs', ['user_id'])
    op.create_index('idx_audit_resource', 'permission_audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_created', 'permission_audit_logs', ['created_at'])


def downgrade() -> None:
    """Drop RBAC system"""
    # Drop indexes
    op.drop_index('idx_audit_created', 'permission_audit_logs')
    op.drop_index('idx_audit_resource', 'permission_audit_logs')
    op.drop_index('idx_audit_user', 'permission_audit_logs')
    op.drop_index('idx_user_roles_study', 'user_roles')
    op.drop_index('idx_user_roles_org', 'user_roles')
    op.drop_index('idx_user_roles_role', 'user_roles')
    op.drop_index('idx_user_roles_user', 'user_roles')
    op.drop_index('idx_role_permissions_permission', 'role_permissions')
    op.drop_index('idx_role_permissions_role', 'role_permissions')
    
    # Drop tables
    op.drop_table('permission_audit_logs')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('roles')
    op.drop_table('permissions')