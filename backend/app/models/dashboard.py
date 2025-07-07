# ABOUTME: Unified dashboard template models combining menu structure and dashboard configurations
# ABOUTME: Manages complete dashboard templates with embedded menus, widgets, and data requirements

import uuid
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel, Column, UniqueConstraint
from sqlalchemy import JSON, DateTime, String, Text, Boolean, Integer, ForeignKey

if TYPE_CHECKING:
    from .user import User
    from .study import Study
    from .widget import WidgetDefinition


class DashboardCategory(str, Enum):
    """Dashboard categories for organization"""
    OVERVIEW = "overview"
    SAFETY = "safety"
    EFFICACY = "efficacy"
    OPERATIONAL = "operational"
    QUALITY = "quality"
    CUSTOM = "custom"


class MenuItemType(str, Enum):
    """Menu item types for navigation structure"""
    DASHBOARD = "dashboard"
    STATIC_PAGE = "static_page"
    EXTERNAL_LINK = "external"
    GROUP = "group"
    DIVIDER = "divider"


class DashboardTemplateBase(SQLModel):
    """Base properties for unified dashboard templates"""
    code: str = Field(unique=True, index=True, max_length=50)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    category: DashboardCategory = Field(default=DashboardCategory.OVERVIEW)
    
    # Complete template structure including menu and dashboards
    template_structure: Dict[str, Any] = Field(sa_column=Column(JSON))
    # Example structure:
    # {
    #   "menu": {
    #     "items": [
    #       {
    #         "id": "overview",
    #         "type": "dashboard",
    #         "label": "Overview",
    #         "icon": "LayoutDashboard",
    #         "dashboard": {
    #           "layout": {"type": "grid", "columns": 12, "rows": 10},
    #           "widgets": [
    #             {
    #               "widget_code": "metric_card",
    #               "instance_config": {"title": "Total Enrolled"},
    #               "position": {"x": 0, "y": 0, "w": 3, "h": 2},
    #               "data_requirements": {
    #                 "dataset": "ADSL",
    #                 "fields": ["USUBJID"],
    #                 "calculation": "count"
    #               }
    #             }
    #           ]
    #         }
    #       }
    #     ]
    #   },
    #   "data_mappings": {
    #     "required_datasets": ["ADSL", "ADAE"],
    #     "field_mappings": {
    #       "ADSL": ["USUBJID", "AGE", "SEX", "RACE"],
    #       "ADAE": ["USUBJID", "AETERM", "AESEV"]
    #     }
    #   }
    # }
    
    version: int = Field(default=1)
    is_active: bool = Field(default=True)


class DashboardTemplateCreate(DashboardTemplateBase):
    """Properties to receive on dashboard template creation"""
    pass


class DashboardTemplateUpdate(SQLModel):
    """Properties to receive on dashboard template update"""
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    category: Optional[DashboardCategory] = None
    layout_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class DashboardTemplate(DashboardTemplateBase, table=True):
    """Database model for dashboard templates"""
    __tablename__ = "dashboard_templates"
    
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
        sa_relationship_kwargs={"foreign_keys": "[DashboardTemplate.created_by]"}
    )
    study_dashboards: List["StudyDashboard"] = Relationship(back_populates="dashboard_template")


# Note: DashboardWidget table is deprecated - widgets are now embedded in template_structure


class StudyDashboardBase(SQLModel):
    """Base properties for study dashboard assignments"""
    study_id: uuid.UUID = Field(foreign_key="study.id")
    dashboard_template_id: uuid.UUID = Field(foreign_key="dashboard_templates.id")
    
    # Study-specific customizations
    customizations: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    # Example: {"widget_overrides": {"widget_1": {"title": "Study-specific Title"}}}
    
    # Data source mappings for this study
    data_mappings: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    # Example: {"dataset_paths": {"ADSL": "/data/study_123/adsl.sas7bdat"}}
    
    is_active: bool = Field(default=True)


class StudyDashboardCreate(StudyDashboardBase):
    """Properties to receive on study dashboard creation"""
    pass


class StudyDashboard(StudyDashboardBase, table=True):
    """Database model for study dashboard configurations"""
    __tablename__ = "study_dashboards"
    __table_args__ = (
        UniqueConstraint("study_id", "dashboard_template_id", name="unique_study_dashboard"),
    )
    
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
    study: "Study" = Relationship()
    dashboard_template: DashboardTemplate = Relationship(back_populates="study_dashboards")
    creator: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[StudyDashboard.created_by]"}
    )


class DashboardTemplatePublic(DashboardTemplateBase):
    """Properties to return to client"""
    id: uuid.UUID
    version: int
    created_at: datetime
    updated_at: datetime
    dashboard_count: Optional[int] = None
    widget_count: Optional[int] = None


class DashboardTemplatesPublic(SQLModel):
    """Response model for multiple dashboard templates"""
    data: List[DashboardTemplatePublic]
    count: int


class DashboardTemplateDataRequirements(SQLModel):
    """Data requirements extracted from a dashboard template"""
    template_id: uuid.UUID
    template_code: str
    required_datasets: List[str]
    field_mappings: Dict[str, List[str]]
    widget_requirements: List[Dict[str, Any]]