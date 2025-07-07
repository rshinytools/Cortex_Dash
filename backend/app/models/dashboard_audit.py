# ABOUTME: Dashboard configuration audit and permission delegation models
# ABOUTME: Tracks all configuration changes and manages org admin permission delegation

import uuid
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from ipaddress import IPv4Address, IPv6Address

from sqlmodel import Field, Relationship, SQLModel, Column, UniqueConstraint
from sqlalchemy import JSON, DateTime, String, Text, Boolean
from sqlalchemy.dialects.postgresql import INET

if TYPE_CHECKING:
    from .user import User
    from .organization import Organization


class EntityType(str, Enum):
    """Types of entities that can be audited"""
    WIDGET = "widget"
    DASHBOARD = "dashboard"
    MENU = "menu"
    STUDY_DASHBOARD = "study_dashboard"
    PERMISSION = "permission"


class AuditAction(str, Enum):
    """Types of audit actions"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ASSIGN = "assign"
    UNASSIGN = "unassign"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"


class DashboardConfigAudit(SQLModel, table=True):
    """Database model for dashboard configuration audit log"""
    __tablename__ = "dashboard_config_audit"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # What was changed
    entity_type: EntityType = Field(index=True)
    entity_id: uuid.UUID = Field(index=True)
    action: AuditAction = Field(index=True)
    
    # Details of the change
    changes: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    # Example: {"before": {"name": "Old Name"}, "after": {"name": "New Name"}}
    
    # Who made the change
    performed_by: uuid.UUID = Field(foreign_key="user.id", index=True)
    performed_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    )
    
    # Additional context
    ip_address: Optional[str] = Field(default=None, sa_column=Column(INET))
    user_agent: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Relationships
    performer: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[DashboardConfigAudit.performed_by]"}
    )


class OrgAdminPermissionBase(SQLModel):
    """Base properties for organization admin permissions"""
    org_id: uuid.UUID = Field(foreign_key="organization.id")
    user_id: uuid.UUID = Field(foreign_key="user.id")
    
    # Specific permissions granted
    permission_set: Dict[str, Any] = Field(sa_column=Column(JSON))
    # Example:
    # {
    #   "dashboard_management": {
    #     "can_view_templates": true,
    #     "can_assign_dashboards": true,
    #     "can_customize_layouts": false,
    #     "can_create_dashboards": false
    #   },
    #   "menu_management": {
    #     "can_view_menus": true,
    #     "can_enable_items": true,
    #     "can_reorder_items": true,
    #     "can_create_items": false
    #   },
    #   "widget_management": {
    #     "can_configure_widgets": true,
    #     "can_update_data_bindings": true,
    #     "can_create_widgets": false
    #   }
    # }
    
    expires_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    is_active: bool = Field(default=True)


class OrgAdminPermission(OrgAdminPermissionBase, table=True):
    """Database model for organization admin permission delegation"""
    __tablename__ = "org_admin_permissions"
    __table_args__ = (
        UniqueConstraint("org_id", "user_id", name="unique_org_user_permission"),
    )
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Who granted the permission
    granted_by: uuid.UUID = Field(foreign_key="user.id")
    granted_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )
    
    # Relationships
    organization: "Organization" = Relationship()
    user: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[OrgAdminPermission.user_id]"}
    )
    granter: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[OrgAdminPermission.granted_by]"}
    )