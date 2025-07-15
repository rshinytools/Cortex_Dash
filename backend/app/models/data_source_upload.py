# ABOUTME: Data source upload model for tracking file uploads and conversion to parquet
# ABOUTME: Tracks individual file uploads, conversion status, and data lineage

import uuid
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import JSON, DateTime, String, Text, Float, Integer

if TYPE_CHECKING:
    from .study import Study
    from .user import User


class UploadStatus(str, Enum):
    """Upload and processing status"""
    PENDING = "pending"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileFormat(str, Enum):
    """Supported file formats for upload"""
    CSV = "csv"
    SAS7BDAT = "sas7bdat"
    XPT = "xpt"
    XLSX = "xlsx"
    PARQUET = "parquet"
    ZIP = "zip"


class DataSourceUploadBase(SQLModel):
    """Base properties for data source uploads"""
    study_id: uuid.UUID = Field(foreign_key="study.id", index=True)
    upload_name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Upload details
    status: UploadStatus = Field(default=UploadStatus.PENDING, index=True)
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # File information
    original_filename: str = Field(max_length=500)
    file_format: FileFormat
    file_size_mb: float = Field(default=0.0)
    
    # Storage paths
    raw_path: str = Field(max_length=1000)  # Path to original uploaded file
    processed_path: Optional[str] = Field(default=None, max_length=1000)  # Path to parquet files
    
    # Processing details
    processing_started_at: Optional[datetime] = Field(default=None)
    processing_completed_at: Optional[datetime] = Field(default=None)
    processing_duration_seconds: Optional[float] = Field(default=None)
    
    # Data summary
    files_extracted: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    # Example: [
    #   {"name": "DM.sas7bdat", "format": "sas7bdat", "size_mb": 2.5, "rows": 1000, "columns": 25},
    #   {"name": "AE.csv", "format": "csv", "size_mb": 5.2, "rows": 5000, "columns": 15}
    # ]
    
    total_rows: Optional[int] = Field(default=None)
    total_columns: Optional[int] = Field(default=None)
    
    # Error tracking
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    warnings: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    
    # Metadata
    upload_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    # Can include: client IP, user agent, custom tags, etc.


class DataSourceUploadCreate(DataSourceUploadBase):
    """Properties to receive on upload creation"""
    pass


class DataSourceUploadUpdate(SQLModel):
    """Properties to receive on upload update"""
    status: Optional[UploadStatus] = None
    description: Optional[str] = None
    processed_path: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    processing_duration_seconds: Optional[float] = None
    files_extracted: Optional[List[Dict[str, Any]]] = None
    total_rows: Optional[int] = None
    total_columns: Optional[int] = None
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None


class DataSourceUpload(DataSourceUploadBase, table=True):
    """Database model for data source uploads"""
    __tablename__ = "data_source_uploads"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Version tracking (for data lineage)
    version_number: int = Field(default=1)
    is_active_version: bool = Field(default=True)
    superseded_by: Optional[uuid.UUID] = Field(default=None, foreign_key="data_source_uploads.id")
    
    # Audit fields
    created_by: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    )
    
    # Relationships
    # Temporarily commented out until table is created
    # study: "Study" = Relationship(back_populates="data_uploads")
    creator: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[DataSourceUpload.created_by]"}
    )


class DataSourceUploadPublic(DataSourceUploadBase):
    """Properties to return to client"""
    id: uuid.UUID
    version_number: int
    is_active_version: bool
    created_at: datetime
    updated_at: datetime


class DataSourceUploadsPublic(SQLModel):
    """Response model for multiple uploads"""
    data: List[DataSourceUploadPublic]
    count: int


class ParquetFileInfo(SQLModel):
    """Information about a converted parquet file"""
    dataset_name: str
    file_path: str
    row_count: int
    column_count: int
    columns: List[Dict[str, str]]  # [{"name": "USUBJID", "type": "string"}, ...]
    file_size_mb: float
    compression: str = "snappy"
    created_at: datetime