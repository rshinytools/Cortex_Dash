# ABOUTME: Refresh schedule models for managing automatic data refresh schedules
# ABOUTME: Includes schedule definitions, execution history, and notification settings

import uuid
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import JSON, DateTime, String, Text, Integer

if TYPE_CHECKING:
    from .study import Study
    from .organization import Organization


class RefreshType(str, Enum):
    """Type of data refresh"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DELTA = "delta"


class ScheduleStatus(str, Enum):
    """Schedule status"""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"


class ExecutionStatus(str, Enum):
    """Execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationChannel(str, Enum):
    """Notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class RefreshScheduleBase(SQLModel):
    """Base model for refresh schedules"""
    schedule_name: str = Field(max_length=255, index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Schedule configuration
    cron_expression: str = Field(max_length=100)  # Standard cron expression
    timezone: str = Field(default="UTC", max_length=50)
    
    # Refresh settings
    refresh_type: RefreshType = Field(default=RefreshType.INCREMENTAL)
    data_sources: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    refresh_options: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Status and control
    status: ScheduleStatus = Field(default=ScheduleStatus.ACTIVE)
    enabled: bool = Field(default=True)
    max_retries: int = Field(default=3)
    retry_delay_minutes: int = Field(default=30)
    
    # Timing
    next_run_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    last_run_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    
    # Statistics
    total_runs: int = Field(default=0)
    successful_runs: int = Field(default=0)
    failed_runs: int = Field(default=0)
    
    # Notification settings
    notification_settings: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    notify_on_success: bool = Field(default=False)
    notify_on_failure: bool = Field(default=True)
    
    # Relationships
    study_id: uuid.UUID = Field(foreign_key="study.id", index=True)
    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    
    # Metadata
    created_by: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))


class RefreshScheduleCreate(RefreshScheduleBase):
    """Model for creating refresh schedules"""
    pass


class RefreshScheduleUpdate(SQLModel):
    """Model for updating refresh schedules"""
    schedule_name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    cron_expression: Optional[str] = Field(default=None, max_length=100)
    timezone: Optional[str] = Field(default=None, max_length=50)
    refresh_type: Optional[RefreshType] = None
    data_sources: Optional[List[str]] = None
    refresh_options: Optional[Dict[str, Any]] = None
    status: Optional[ScheduleStatus] = None
    enabled: Optional[bool] = None
    max_retries: Optional[int] = None
    retry_delay_minutes: Optional[int] = None
    notification_settings: Optional[Dict[str, Any]] = None
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None


class RefreshSchedule(RefreshScheduleBase, table=True):
    """Refresh schedule table model"""
    __tablename__ = "refresh_schedules"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Relationships
    study: Optional["Study"] = Relationship(back_populates="refresh_schedules")
    organization: Optional["Organization"] = Relationship()
    executions: List["RefreshExecution"] = Relationship(back_populates="schedule")


class RefreshExecutionBase(SQLModel):
    """Base model for refresh executions"""
    execution_name: Optional[str] = Field(default=None, max_length=255)
    
    # Execution details
    refresh_type: RefreshType
    data_sources: List[str] = Field(sa_column=Column(JSON))
    refresh_options: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Timing
    started_at: datetime = Field(sa_column=Column(DateTime))
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    duration_seconds: Optional[int] = Field(default=None)
    
    # Status and results
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    error_details: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Processing statistics
    records_processed: int = Field(default=0)
    records_added: int = Field(default=0)
    records_updated: int = Field(default=0)
    records_deleted: int = Field(default=0)
    records_failed: int = Field(default=0)
    
    # Data quality metrics
    data_quality_score: Optional[float] = Field(default=None)
    quality_issues_found: int = Field(default=0)
    validation_errors: int = Field(default=0)
    
    # Execution metadata
    execution_details: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    pipeline_version: Optional[str] = Field(default=None, max_length=50)
    triggered_by: str = Field(default="scheduled", max_length=50)  # scheduled, manual, api
    
    # Relationships
    schedule_id: uuid.UUID = Field(foreign_key="refresh_schedules.id", index=True)
    study_id: uuid.UUID = Field(foreign_key="study.id", index=True)
    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    
    # User who triggered (for manual executions)
    triggered_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")


class RefreshExecutionCreate(RefreshExecutionBase):
    """Model for creating refresh executions"""
    pass


class RefreshExecutionUpdate(SQLModel):
    """Model for updating refresh executions"""
    execution_name: Optional[str] = Field(default=None, max_length=255)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    status: Optional[ExecutionStatus] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    records_processed: Optional[int] = None
    records_added: Optional[int] = None
    records_updated: Optional[int] = None
    records_deleted: Optional[int] = None
    records_failed: Optional[int] = None
    data_quality_score: Optional[float] = None
    quality_issues_found: Optional[int] = None
    validation_errors: Optional[int] = None
    execution_details: Optional[Dict[str, Any]] = None


class RefreshExecution(RefreshExecutionBase, table=True):
    """Refresh execution table model"""
    __tablename__ = "refresh_executions"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Relationships
    schedule: Optional[RefreshSchedule] = Relationship(back_populates="executions")
    study: Optional["Study"] = Relationship()
    organization: Optional["Organization"] = Relationship()


class RefreshNotificationBase(SQLModel):
    """Base model for refresh notifications"""
    notification_type: str = Field(max_length=50)  # success, failure, warning, info
    channel: NotificationChannel
    recipient: str = Field(max_length=255)  # email address, slack channel, webhook URL, etc.
    
    # Message content
    subject: str = Field(max_length=255)
    message: str = Field(sa_column=Column(Text))
    template_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Delivery status
    sent_at: datetime = Field(sa_column=Column(DateTime))
    delivered_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    delivery_status: str = Field(default="pending", max_length=50)  # pending, sent, delivered, failed
    delivery_error: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Relationships
    execution_id: uuid.UUID = Field(foreign_key="refresh_executions.id", index=True)
    schedule_id: uuid.UUID = Field(foreign_key="refresh_schedules.id", index=True)
    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)


class RefreshNotificationCreate(RefreshNotificationBase):
    """Model for creating refresh notifications"""
    pass


class RefreshNotification(RefreshNotificationBase, table=True):
    """Refresh notification table model"""
    __tablename__ = "refresh_notifications"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Relationships
    execution: Optional[RefreshExecution] = Relationship()
    schedule: Optional[RefreshSchedule] = Relationship()
    organization: Optional["Organization"] = Relationship()


class DataSourceRefreshBase(SQLModel):
    """Base model for data source refresh configuration"""
    data_source_name: str = Field(max_length=255, index=True)
    refresh_method: str = Field(max_length=50)  # api, sftp, file_sync, database
    
    # Source-specific configuration
    source_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    transformation_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    validation_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Processing options
    batch_size: int = Field(default=1000)
    parallel_processing: bool = Field(default=False)
    max_workers: int = Field(default=1)
    
    # Quality checks
    enable_quality_checks: bool = Field(default=True)
    quality_threshold: float = Field(default=0.95)  # Minimum acceptable quality score
    fail_on_quality_issues: bool = Field(default=False)
    
    # Relationships
    schedule_id: uuid.UUID = Field(foreign_key="refresh_schedules.id", index=True)
    study_id: uuid.UUID = Field(foreign_key="study.id", index=True)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))


class DataSourceRefreshCreate(DataSourceRefreshBase):
    """Model for creating data source refresh configuration"""
    pass


class DataSourceRefresh(DataSourceRefreshBase, table=True):
    """Data source refresh configuration table model"""
    __tablename__ = "data_source_refreshes"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Relationships
    schedule: Optional[RefreshSchedule] = Relationship()
    study: Optional["Study"] = Relationship()


# Response models
class RefreshScheduleResponse(RefreshScheduleBase):
    """Response model for refresh schedules"""
    id: uuid.UUID
    success_rate: Optional[float] = None
    average_duration: Optional[float] = None
    last_execution_status: Optional[str] = None
    health_score: Optional[float] = None


class RefreshExecutionResponse(RefreshExecutionBase):
    """Response model for refresh executions"""
    id: uuid.UUID
    schedule_name: Optional[str] = None


class RefreshExecutionSummary(SQLModel):
    """Summary model for refresh execution statistics"""
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    average_duration: float
    total_records_processed: int
    last_execution_date: Optional[datetime] = None
    next_execution_date: Optional[datetime] = None