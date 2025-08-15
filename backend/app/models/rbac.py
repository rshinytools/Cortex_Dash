# ABOUTME: RBAC (Role-Based Access Control) models for dynamic permission management
# ABOUTME: Allows System Admin to grant/revoke permissions to roles at runtime

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
import json


class Permission(SQLModel, table=True):
    """Individual permission that can be granted to roles"""
    __tablename__ = "permissions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(unique=True, index=True)  # e.g., "study.create"
    resource: str = Field(index=True)  # e.g., "study"
    action: str  # e.g., "create"
    description: Optional[str] = None
    is_system: bool = Field(default=False)  # System permissions cannot be deleted
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    role_permissions: List["RolePermission"] = Relationship(back_populates="permission")


class Role(SQLModel, table=True):
    """Role that groups permissions"""
    __tablename__ = "roles"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(unique=True, index=True)  # e.g., "system_admin"
    display_name: str  # e.g., "System Administrator"
    description: Optional[str] = None
    is_system: bool = Field(default=False)  # System roles cannot be deleted
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    role_permissions: List["RolePermission"] = Relationship(back_populates="role")
    user_roles: List["UserRole"] = Relationship(back_populates="role")


class RolePermission(SQLModel, table=True):
    """Many-to-many relationship between roles and permissions"""
    __tablename__ = "role_permissions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    role_id: UUID = Field(foreign_key="roles.id", index=True)
    permission_id: UUID = Field(foreign_key="permissions.id", index=True)
    granted_by: Optional[UUID] = Field(foreign_key="user.id", default=None)
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    conditions: Optional[str] = None  # JSON string for conditional permissions
    
    # Relationships
    role: Role = Relationship(back_populates="role_permissions")
    permission: Permission = Relationship(back_populates="role_permissions")


class UserRole(SQLModel, table=True):
    """User role assignments with optional scope"""
    __tablename__ = "user_roles"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    role_id: UUID = Field(foreign_key="roles.id", index=True)
    organization_id: Optional[UUID] = Field(foreign_key="organization.id", default=None)
    study_id: Optional[UUID] = Field(foreign_key="study.id", default=None)
    assigned_by: UUID = Field(foreign_key="user.id")
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = Field(default=True)
    
    # Relationships
    role: Role = Relationship(back_populates="user_roles")


class PermissionPreset(SQLModel, table=True):
    """Predefined permission sets for quick role setup"""
    __tablename__ = "permission_presets"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(unique=True)
    role_name: str
    permissions: str  # JSON array of permission names
    description: Optional[str] = None
    is_default: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_permissions_list(self) -> List[str]:
        """Get permissions as a list"""
        return json.loads(self.permissions) if self.permissions else []
    
    def set_permissions_list(self, permissions: List[str]):
        """Set permissions from a list"""
        self.permissions = json.dumps(permissions)


class PermissionAuditLog(SQLModel, table=True):
    """Audit log for permission changes"""
    __tablename__ = "permission_audit_logs"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    action: str  # grant, revoke, create, delete
    resource_type: str  # permission, role, user_role
    resource_id: UUID
    user_id: UUID = Field(foreign_key="user.id")
    details: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # JSON field
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Default permissions list
DEFAULT_PERMISSIONS = [
    # Study Management
    {"name": "study.create", "resource": "study", "action": "create", "description": "Create new studies"},
    {"name": "study.edit", "resource": "study", "action": "edit", "description": "Edit study settings"},
    {"name": "study.delete", "resource": "study", "action": "delete", "description": "Delete studies"},
    {"name": "study.view", "resource": "study", "action": "view", "description": "View studies"},
    
    # Data Management
    {"name": "data.upload", "resource": "data", "action": "upload", "description": "Upload data files"},
    {"name": "data.delete", "resource": "data", "action": "delete", "description": "Delete data files"},
    {"name": "data.export", "resource": "data", "action": "export", "description": "Export data"},
    {"name": "data.view", "resource": "data", "action": "view", "description": "View data"},
    
    # Widget Management
    {"name": "widget.create", "resource": "widget", "action": "create", "description": "Create widgets"},
    {"name": "widget.edit", "resource": "widget", "action": "edit", "description": "Edit widgets"},
    {"name": "widget.delete", "resource": "widget", "action": "delete", "description": "Delete widgets"},
    {"name": "widget.map", "resource": "widget", "action": "map", "description": "Map data to widgets"},
    
    # Dashboard Management
    {"name": "dashboard.create", "resource": "dashboard", "action": "create", "description": "Create dashboards"},
    {"name": "dashboard.edit", "resource": "dashboard", "action": "edit", "description": "Edit dashboards"},
    {"name": "dashboard.delete", "resource": "dashboard", "action": "delete", "description": "Delete dashboards"},
    {"name": "dashboard.view", "resource": "dashboard", "action": "view", "description": "View dashboards"},
    
    # Template Management
    {"name": "template.create", "resource": "template", "action": "create", "description": "Create dashboard templates"},
    {"name": "template.edit", "resource": "template", "action": "edit", "description": "Edit templates"},
    {"name": "template.delete", "resource": "template", "action": "delete", "description": "Delete templates"},
    
    # User Management
    {"name": "user.manage_system", "resource": "user", "action": "manage_system", "description": "Manage all system users"},
    {"name": "user.manage_org", "resource": "user", "action": "manage_org", "description": "Manage organization users"},
    {"name": "user.view", "resource": "user", "action": "view", "description": "View users"},
    
    # Team Management
    {"name": "team.manage", "resource": "team", "action": "manage", "description": "Manage study teams"},
    {"name": "team.view", "resource": "team", "action": "view", "description": "View team members"},
    
    # Report Management
    {"name": "report.create", "resource": "report", "action": "create", "description": "Create reports"},
    {"name": "report.edit", "resource": "report", "action": "edit", "description": "Edit reports"},
    {"name": "report.delete", "resource": "report", "action": "delete", "description": "Delete reports"},
    {"name": "report.view", "resource": "report", "action": "view", "description": "View reports"},
    
    # System Settings
    {"name": "settings.manage", "resource": "settings", "action": "manage", "description": "Manage system settings"},
    {"name": "settings.view", "resource": "settings", "action": "view", "description": "View settings"},
    
    # Data Refresh
    {"name": "refresh.schedule", "resource": "refresh", "action": "schedule", "description": "Schedule data refresh"},
    {"name": "refresh.manual", "resource": "refresh", "action": "manual", "description": "Trigger manual refresh"},
    
    # Filters
    {"name": "filter.apply", "resource": "filter", "action": "apply", "description": "Apply dashboard filters"},
    
    # RBAC Management
    {"name": "permission.manage", "resource": "permission", "action": "manage", "description": "Manage RBAC permissions"},
    {"name": "permission.view", "resource": "permission", "action": "view", "description": "View permissions"},
    
    # Audit
    {"name": "audit.view", "resource": "audit", "action": "view", "description": "View audit logs"},
]

# Default role permission mappings
DEFAULT_ROLE_PERMISSIONS = {
    "system_admin": ["*"],  # All permissions
    "org_admin": [
        "user.manage_org", "user.view",
        "study.view", 
        "dashboard.view", "filter.apply",
        "report.view", "report.create", "report.edit",
        "data.export", "data.view",
        "team.view",
        "audit.view"
    ],
    "study_manager": [
        "team.manage", "team.view",
        "study.view",
        "dashboard.view", "filter.apply",
        "report.view", "report.create",
        "data.view", "data.export",
        "refresh.schedule", "refresh.manual"
    ],
    "data_analyst": [
        "dashboard.view", "filter.apply",
        "report.create", "report.edit", "report.view",
        "data.export", "data.view"
    ],
    "viewer": [
        "dashboard.view", "filter.apply",
        "report.view"
    ]
}