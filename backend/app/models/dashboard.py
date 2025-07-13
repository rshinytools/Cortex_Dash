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


class TemplateStatus(str, Enum):
    """Template status for lifecycle management"""
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class InheritanceType(str, Enum):
    """Types of template inheritance"""
    NONE = "none"
    EXTENDS = "extends"  # Inherits from parent and can override
    INCLUDES = "includes"  # Includes components from parent


class MenuItemType(str, Enum):
    """Menu item types for navigation structure"""
    DASHBOARD_PAGE = "dashboard_page"  # Has its own canvas in the dashboard
    GROUP = "group"                    # Placeholder for submenus
    DIVIDER = "divider"                # Visual separator
    EXTERNAL = "external"              # External link


class DashboardTemplateBase(SQLModel):
    """Base properties for unified dashboard templates"""
    code: str = Field(unique=True, index=True, max_length=50)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    category: DashboardCategory = Field(default=DashboardCategory.OVERVIEW)
    
    # Versioning and lifecycle
    major_version: int = Field(default=1)
    minor_version: int = Field(default=0)
    patch_version: int = Field(default=0)
    status: TemplateStatus = Field(default=TemplateStatus.DRAFT)
    
    # Template inheritance
    parent_template_id: Optional[uuid.UUID] = Field(default=None, foreign_key="dashboard_templates.id")
    inheritance_type: InheritanceType = Field(default=InheritanceType.NONE)
    
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
    
    # Metadata for marketplace
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    screenshot_urls: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    documentation_url: Optional[str] = Field(default=None, max_length=500)
    
    # Ratings and reviews
    average_rating: Optional[float] = Field(default=None)
    total_ratings: int = Field(default=0)
    download_count: int = Field(default=0)
    
    is_active: bool = Field(default=True)
    is_public: bool = Field(default=False)  # Available in marketplace


class DashboardTemplateCreate(DashboardTemplateBase):
    """Properties to receive on dashboard template creation"""
    pass


class DashboardTemplateUpdate(SQLModel):
    """Properties to receive on dashboard template update"""
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    category: Optional[DashboardCategory] = None
    template_structure: Optional[Dict[str, Any]] = None
    status: Optional[TemplateStatus] = None
    tags: Optional[List[str]] = None
    screenshot_urls: Optional[List[str]] = None
    documentation_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


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
    
    # Template versioning relationships
    parent_template: Optional["DashboardTemplate"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[DashboardTemplate.parent_template_id]",
            "remote_side": "[DashboardTemplate.id]"
        }
    )
    child_templates: List["DashboardTemplate"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[DashboardTemplate.parent_template_id]"
        }
    )
    
    # Version history
    template_versions: List["TemplateVersion"] = Relationship(back_populates="template")
    
    # Drafts
    drafts: List["TemplateDraft"] = Relationship(back_populates="template")
    
    # Ratings and reviews
    template_reviews: List["TemplateReview"] = Relationship(back_populates="template")
    
    @property
    def version_string(self) -> str:
        """Return semantic version string"""
        return f"{self.major_version}.{self.minor_version}.{self.patch_version}"
    
    @property
    def full_code(self) -> str:
        """Return code with version for uniqueness"""
        return f"{self.code}@{self.version_string}"


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
    version: str  # Changed to string for semantic versioning (e.g., "1.0.0")
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


class TemplateVersionBase(SQLModel):
    """Base properties for template versions"""
    template_id: uuid.UUID = Field(foreign_key="dashboard_templates.id")
    major_version: int
    minor_version: int
    patch_version: int
    change_description: str = Field(max_length=500)
    template_structure: Dict[str, Any] = Field(sa_column=Column(JSON))
    is_published: bool = Field(default=False)
    
    # Migration metadata
    migration_notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    breaking_changes: bool = Field(default=False)
    required_migrations: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))


class TemplateVersionCreate(TemplateVersionBase):
    """Properties to receive on template version creation"""
    pass


class TemplateVersion(TemplateVersionBase, table=True):
    """Database model for template version history"""
    __tablename__ = "template_versions"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # New versioning fields
    version_type: Optional[str] = Field(default=None, max_length=10)  # major, minor, patch
    auto_created: bool = Field(default=False)
    change_summary: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    created_by_name: Optional[str] = Field(default=None, max_length=255)
    comparison_hash: Optional[str] = Field(default=None, max_length=64)
    
    # Audit fields
    created_by: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )
    
    # Relationships
    template: DashboardTemplate = Relationship(back_populates="template_versions")
    creator: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[TemplateVersion.created_by]"}
    )
    
    @property
    def version_string(self) -> str:
        """Return semantic version string"""
        return f"{self.major_version}.{self.minor_version}.{self.patch_version}"


# Template Drafts for version control
class TemplateDraftBase(SQLModel):
    """Base properties for template drafts"""
    template_id: uuid.UUID = Field(foreign_key="dashboard_templates.id")
    base_version_id: Optional[uuid.UUID] = Field(default=None, foreign_key="template_versions.id")
    draft_content: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    changes_summary: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    conflict_status: Optional[str] = Field(default=None, max_length=50)
    is_active: bool = Field(default=True)


class TemplateDraftCreate(TemplateDraftBase):
    """Properties to receive on draft creation"""
    pass


class TemplateDraftUpdate(SQLModel):
    """Properties to receive on draft update"""
    draft_content: Optional[Dict[str, Any]] = None
    changes_summary: Optional[List[Dict[str, Any]]] = None
    conflict_status: Optional[str] = None
    is_active: Optional[bool] = None


class TemplateDraft(TemplateDraftBase, table=True):
    """Template draft database model"""
    __tablename__ = "template_drafts"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_by: uuid.UUID = Field(foreign_key="user.id")
    auto_save_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    
    # Relationships
    template: "DashboardTemplate" = Relationship(back_populates="drafts")
    base_version: Optional["TemplateVersion"] = Relationship()
    # creator: "User" = Relationship()  # Commented out due to foreign key issues
    change_logs: List["TemplateChangeLog"] = Relationship(back_populates="draft")


# Template Change Logs for tracking changes
class TemplateChangeLogBase(SQLModel):
    """Base properties for template change logs"""
    template_id: uuid.UUID = Field(foreign_key="dashboard_templates.id")
    draft_id: Optional[uuid.UUID] = Field(default=None, foreign_key="template_drafts.id")
    change_type: str = Field(max_length=50)  # major, minor, patch
    change_category: str = Field(max_length=100)
    change_description: Optional[str] = Field(default=None, sa_column=Column(Text))
    change_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))


class TemplateChangeLogCreate(TemplateChangeLogBase):
    """Properties to receive on change log creation"""
    pass


class TemplateChangeLog(TemplateChangeLogBase, table=True):
    """Template change log database model"""
    __tablename__ = "template_change_logs"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_by: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    template: "DashboardTemplate" = Relationship()
    draft: Optional["TemplateDraft"] = Relationship(back_populates="change_logs")
    # creator: "User" = Relationship()  # Commented out due to foreign key issues


class TemplateReviewBase(SQLModel):
    """Base properties for template reviews"""
    template_id: uuid.UUID = Field(foreign_key="dashboard_templates.id")
    rating: int = Field(ge=1, le=5)  # 1-5 star rating
    review_text: Optional[str] = Field(default=None, sa_column=Column(Text))
    is_verified_user: bool = Field(default=False)  # Premium/verified organization


class TemplateReviewCreate(TemplateReviewBase):
    """Properties to receive on template review creation"""
    pass


class TemplateReview(TemplateReviewBase, table=True):
    """Database model for template reviews and ratings"""
    __tablename__ = "template_reviews"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Audit fields
    reviewed_by: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    )
    
    # Relationships
    template: DashboardTemplate = Relationship(back_populates="template_reviews")
    reviewer: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[TemplateReview.reviewed_by]"}
    )


class TemplateExportData(SQLModel):
    """Model for template export/import"""
    template: DashboardTemplateBase
    versions: List[TemplateVersionBase]
    reviews: Optional[List[TemplateReviewBase]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    export_timestamp: datetime = Field(default_factory=datetime.utcnow)