# ABOUTME: Data source model for managing various clinical data sources (Medidata, ZIP uploads, etc.)
# ABOUTME: Supports multiple data source types with encrypted credential storage

import uuid
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import JSON, DateTime, String, Text
from pydantic import BaseModel

if TYPE_CHECKING:
    from .study import Study


class DataSourceType(str, Enum):
    """Supported data source types"""
    MEDIDATA_API = "medidata_api"
    ZIP_UPLOAD = "zip_upload"
    SFTP = "sftp"
    FOLDER_SYNC = "folder_sync"
    EDC_API = "edc_api"
    AWS_S3 = "aws_s3"
    AZURE_BLOB = "azure_blob"


class DataSourceStatus(str, Enum):
    """Data source connection status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"


class DataSourceConfig(BaseModel):
    """Configuration schema for data sources"""
    # Connection details (varies by type)
    connection_details: Dict[str, Any] = {}
    
    # Authentication (encrypted in database)
    credentials: Dict[str, Any] = {}
    
    # Data selection
    datasets: Optional[list[str]] = None
    file_patterns: Optional[list[str]] = None
    
    # Sync settings
    refresh_schedule: Optional[str] = None  # Cron expression
    retention_days: Optional[int] = None
    
    # Validation
    validation_rules: Dict[str, Any] = {}


class DataSourceBase(SQLModel):
    name: str = Field(index=True, max_length=255)
    type: DataSourceType = Field(index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Configuration (encrypted credentials)
    config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Connection info
    status: DataSourceStatus = Field(default=DataSourceStatus.INACTIVE)
    last_connected: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    last_sync: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    next_sync: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    
    # Error tracking
    last_error: Optional[str] = Field(default=None, sa_column=Column(Text))
    error_count: int = Field(default=0)
    
    # Study relationship
    study_id: uuid.UUID = Field(foreign_key="study.id", index=True)
    
    # Status
    is_active: bool = Field(default=True)
    is_primary: bool = Field(default=False)  # Primary data source for study


class DataSourceCreate(DataSourceBase):
    pass


class DataSourceUpdate(SQLModel):
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[DataSourceStatus] = None
    is_active: Optional[bool] = None
    is_primary: Optional[bool] = None


class DataSource(DataSourceBase, table=True):
    __tablename__ = "data_source"
    
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
    
    # Statistics
    sync_count: int = Field(default=0)
    records_synced: int = Field(default=0)
    data_volume_mb: float = Field(default=0.0)
    
    # Medidata specific fields (when type = MEDIDATA_API)
    medidata_study_oid: Optional[str] = Field(default=None, max_length=100)
    medidata_environment: Optional[str] = Field(default=None, max_length=50)  # prod, uat, dev
    
    # File upload specific (when type = ZIP_UPLOAD)
    upload_path: Optional[str] = Field(default=None, max_length=500)
    allowed_file_types: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    
    # Relationships
    study: "Study" = Relationship(back_populates="data_sources")


class DataSourcePublic(DataSourceBase):
    id: uuid.UUID
    created_at: datetime
    status: DataSourceStatus
    last_sync: Optional[datetime] = None
    sync_count: int
    records_synced: int


class DataSourcesPublic(SQLModel):
    data: list[DataSourcePublic]
    count: int