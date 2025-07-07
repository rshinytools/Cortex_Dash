# ABOUTME: Central import for all models in the Clinical Dashboard Platform
# ABOUTME: Provides a single import point for database models with proper organization

from sqlmodel import SQLModel
from .user import User, UserBase, UserCreate, UserUpdate, UserRegister, UserPublic, UsersPublic, UserUpdateMe, UpdatePassword
from .organization import Organization, OrganizationCreate, OrganizationUpdate, OrganizationPublic
from .study import Study, StudyCreate, StudyUpdate, StudyPublic
from .activity_log import ActivityLog, ActivityLogCreate, ActivityLogPublic
from .data_source import DataSource, DataSourceCreate, DataSourceUpdate, DataSourceConfig, DataSourceType
from .item import Item, ItemBase, ItemCreate, ItemUpdate, ItemPublic, ItemsPublic, Message
from .token import Token, TokenPayload, NewPassword
from .widget import WidgetDefinition, WidgetDefinitionCreate, WidgetDefinitionUpdate, WidgetDefinitionPublic, WidgetDefinitionsPublic, WidgetCategory
from .dashboard import (
    DashboardTemplate, DashboardTemplateCreate, DashboardTemplateUpdate, DashboardTemplatePublic, DashboardTemplatesPublic,
    StudyDashboard, StudyDashboardCreate, StudyDashboardBase,
    DashboardCategory, MenuItemType, DashboardTemplateDataRequirements
)
from .dashboard_audit import DashboardConfigAudit, OrgAdminPermission, OrgAdminPermissionBase, EntityType, AuditAction

__all__ = [
    # SQLModel base
    "SQLModel",
    # User models
    "User", "UserBase", "UserCreate", "UserUpdate", "UserRegister", "UserPublic", "UsersPublic", "UserUpdateMe", "UpdatePassword",
    # Organization models
    "Organization", "OrganizationCreate", "OrganizationUpdate", "OrganizationPublic",
    # Study models
    "Study", "StudyCreate", "StudyUpdate", "StudyPublic",
    # Activity logging
    "ActivityLog", "ActivityLogCreate", "ActivityLogPublic",
    # Data sources
    "DataSource", "DataSourceCreate", "DataSourceUpdate", "DataSourceConfig", "DataSourceType",
    # Items (from template)
    "Item", "ItemBase", "ItemCreate", "ItemUpdate", "ItemPublic", "ItemsPublic", "Message",
    # Auth tokens
    "Token", "TokenPayload", "NewPassword",
    # Widget models
    "WidgetDefinition", "WidgetDefinitionCreate", "WidgetDefinitionUpdate", "WidgetDefinitionPublic", "WidgetDefinitionsPublic", "WidgetCategory",
    # Dashboard models (unified with menu)
    "DashboardTemplate", "DashboardTemplateCreate", "DashboardTemplateUpdate", "DashboardTemplatePublic", "DashboardTemplatesPublic",
    "StudyDashboard", "StudyDashboardCreate", "StudyDashboardBase",
    "DashboardCategory", "MenuItemType", "DashboardTemplateDataRequirements",
    # Dashboard audit models
    "DashboardConfigAudit", "OrgAdminPermission", "OrgAdminPermissionBase", "EntityType", "AuditAction"
]