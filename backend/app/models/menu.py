# ABOUTME: DEPRECATED - Menu templates are now embedded in unified dashboard templates
# ABOUTME: This file is kept for backward compatibility during migration

import uuid
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import JSON, DateTime, String, Text, Boolean, Integer

if TYPE_CHECKING:
    from .user import User
    from .dashboard import StudyDashboard


class MenuTemplateBase(SQLModel):
    """Base properties for menu templates"""
    code: str = Field(unique=True, index=True, max_length=50)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Hierarchical menu structure
    menu_structure: Dict[str, Any] = Field(sa_column=Column(JSON))
    # Example structure:
    # {
    #   "items": [
    #     {
    #       "id": "overview",
    #       "label": "Overview",
    #       "icon": "LayoutDashboard",
    #       "type": "dashboard",
    #       "dashboard_code": "clinical_overview",
    #       "permissions": ["view_dashboard"],
    #       "order": 1
    #     },
    #     {
    #       "id": "safety",
    #       "label": "Safety",
    #       "icon": "Shield",
    #       "type": "group",
    #       "order": 2,
    #       "children": [...]
    #     }
    #   ]
    # }
    
    version: int = Field(default=1)
    is_active: bool = Field(default=True)


class MenuTemplateCreate(MenuTemplateBase):
    """Properties to receive on menu template creation"""
    pass


class MenuTemplateUpdate(SQLModel):
    """Properties to receive on menu template update"""
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    menu_structure: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class MenuTemplate(MenuTemplateBase, table=True):
    """Database model for menu templates"""
    __tablename__ = "menu_templates"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Audit fields
    created_by: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    )
    
    # Relationships
    creator: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[MenuTemplate.created_by]"}
    )
    study_dashboards: List["StudyDashboard"] = Relationship(back_populates="menu_template")


class MenuTemplatePublic(MenuTemplateBase):
    """Properties to return to client"""
    id: uuid.UUID
    version: int
    created_at: datetime
    updated_at: datetime


class MenuTemplatesPublic(SQLModel):
    """Response model for multiple menu templates"""
    data: List[MenuTemplatePublic]
    count: int