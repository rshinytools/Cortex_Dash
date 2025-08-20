# ABOUTME: Study model representing clinical trials with compliance and configuration support
# ABOUTME: Core entity for clinical data management with folder structure and pipeline configuration

import uuid
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import JSON, DateTime, String, Text, Enum as SQLEnum

if TYPE_CHECKING:
    from .organization import Organization
    from .data_source import DataSource
    from .data_source_upload import DataSourceUpload
    from .activity_log import ActivityLog
    from .dashboard import DashboardTemplate
    from .data_mapping import WidgetDataMapping


class StudyStatus(str, Enum):
    """Study lifecycle status"""
    DRAFT = "DRAFT"  # Study created but initialization not completed
    PLANNING = "PLANNING"
    SETUP = "SETUP"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class StudyPhase(str, Enum):
    """Clinical trial phases"""
    PHASE_1 = "phase_1"
    PHASE_2 = "phase_2"
    PHASE_3 = "phase_3"
    PHASE_4 = "phase_4"
    OBSERVATIONAL = "observational"
    EXPANDED_ACCESS = "expanded_access"


class StudyBase(SQLModel):
    name: str = Field(index=True, max_length=255)
    code: str = Field(index=True, max_length=50)  # Study code like "COV-VAC-P3"
    protocol_number: str = Field(unique=True, index=True, max_length=100)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Study metadata
    phase: Optional[StudyPhase] = Field(default=None)
    therapeutic_area: Optional[str] = Field(default=None, max_length=100)
    indication: Optional[str] = Field(default=None, max_length=255)
    
    # Timeline
    planned_start_date: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    planned_end_date: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    actual_start_date: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    actual_end_date: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    
    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    pipeline_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    dashboard_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Template-based configuration
    dashboard_template_id: Optional[uuid.UUID] = Field(default=None, foreign_key="dashboard_templates.id")
    field_mappings: Dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))  # template_field -> study_field
    field_mapping_filters: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))  # Widget filters
    template_overrides: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))  # Customizations to template
    
    # Data management
    data_retention_days: int = Field(default=2555)  # 7 years default for regulatory
    refresh_frequency: Optional[str] = Field(default="daily", max_length=50)  # daily, weekly, monthly, manual
    
    # Multi-tenant relationship
    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    
    # Status
    status: StudyStatus = Field(
        default=StudyStatus.SETUP,
        sa_column=Column(SQLEnum(StudyStatus, values_callable=lambda x: [e.value for e in x]))
    )
    is_active: bool = Field(default=True)
    
    # Initialization tracking
    initialization_status: Optional[str] = Field(default="not_started", max_length=50)  # not_started, in_progress, completed, failed
    initialization_progress: Optional[int] = Field(default=0)  # 0-100
    initialization_steps: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))  # Track each step status
    template_applied_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    data_uploaded_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    mappings_configured_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    activated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    
    # Transformation tracking
    last_transformation_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    transformation_status: Optional[str] = Field(default=None, max_length=50)  # running, completed, failed
    transformation_count: int = Field(default=0)  # Total number of transformations run
    derived_datasets: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))  # Dataset schemas from transformations
    transformation_errors: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))  # Recent transformation errors


class StudyCreate(StudyBase):
    pass


class StudyUpdate(SQLModel):
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    phase: Optional[StudyPhase] = None
    therapeutic_area: Optional[str] = Field(default=None, max_length=100)
    indication: Optional[str] = Field(default=None, max_length=255)
    
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    
    config: Optional[Dict[str, Any]] = None
    pipeline_config: Optional[Dict[str, Any]] = None
    dashboard_config: Optional[Dict[str, Any]] = None
    
    data_retention_days: Optional[int] = None
    refresh_frequency: Optional[str] = Field(default=None, max_length=50)
    
    status: Optional[StudyStatus] = None
    is_active: Optional[bool] = None
    
    # Initialization tracking updates
    initialization_status: Optional[str] = Field(default=None, max_length=50)
    initialization_progress: Optional[int] = None
    initialization_steps: Optional[Dict[str, Any]] = None
    
    # Transformation tracking updates
    last_transformation_at: Optional[datetime] = None
    transformation_status: Optional[str] = Field(default=None, max_length=50)
    transformation_count: Optional[int] = None
    derived_datasets: Optional[Dict[str, Any]] = None
    transformation_errors: Optional[Dict[str, Any]] = None


class Study(StudyBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Audit fields
    created_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    )
    created_by: uuid.UUID = Field(foreign_key="user.id")
    updated_by: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    
    # Study-specific settings
    folder_path: Optional[str] = Field(default=None, max_length=500)  # /data/studies/{org_id}/{study_id}
    
    # Compliance fields
    protocol_version: str = Field(default="1.0", max_length=20)
    protocol_approved_date: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    protocol_approved_by: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    
    # Statistics (updated by background jobs)
    subject_count: int = Field(default=0)
    site_count: int = Field(default=0)
    data_points_count: int = Field(default=0)
    last_data_update: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    
    # Relationships
    organization: "Organization" = Relationship(back_populates="studies")
    data_sources: List["DataSource"] = Relationship(
        back_populates="study",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    # Temporarily commented out until table is created
    # data_uploads: List["DataSourceUpload"] = Relationship(
    #     back_populates="study",
    #     sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    # )
    activity_logs: List["ActivityLog"] = Relationship(back_populates="study")
    dashboard_template: Optional["DashboardTemplate"] = Relationship()
    widget_mappings: List["WidgetDataMapping"] = Relationship(
        back_populates="study",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class StudyPublic(StudyBase):
    id: uuid.UUID
    created_at: datetime
    status: StudyStatus
    subject_count: int
    site_count: int
    last_data_update: Optional[datetime] = None
    folder_path: Optional[str] = None
    # Initialization tracking
    initialization_status: Optional[str] = None
    initialization_progress: Optional[int] = None
    template_applied_at: Optional[datetime] = None
    data_uploaded_at: Optional[datetime] = None
    mappings_configured_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    
    # Transformation tracking
    last_transformation_at: Optional[datetime] = None
    transformation_status: Optional[str] = None
    transformation_count: int
    derived_datasets: Dict[str, Any]


class StudiesPublic(SQLModel):
    data: List[StudyPublic]
    count: int