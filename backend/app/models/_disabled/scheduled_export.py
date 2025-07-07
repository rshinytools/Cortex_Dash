# ABOUTME: SQLModel for scheduled dashboard exports with recurring schedules and email delivery
# ABOUTME: Supports cron-based scheduling and tracks export history

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from uuid import uuid4, UUID
from sqlalchemy import Column, JSON


class ScheduledExportBase(SQLModel):
    name: str = Field(index=True)
    dashboard_id: UUID = Field(foreign_key="dashboard.id", index=True)
    format: str = Field(default="pdf")  # pdf, pptx, xlsx
    schedule: str = Field(default="0 9 * * 1")  # Cron expression (default: Monday 9am)
    is_active: bool = Field(default=True)
    email_recipients: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None  # success, failed, skipped
    last_run_error: Optional[str] = None
    created_by: UUID = Field(foreign_key="user.id", index=True)


class ScheduledExport(ScheduledExportBase, table=True):
    __tablename__ = "scheduled_export"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    dashboard: Optional["Dashboard"] = Relationship(back_populates="scheduled_exports")
    creator: Optional["User"] = Relationship(back_populates="scheduled_exports")
    history: List["ScheduledExportHistory"] = Relationship(back_populates="scheduled_export")


class ScheduledExportHistoryBase(SQLModel):
    scheduled_export_id: UUID = Field(foreign_key="scheduled_export.id", index=True)
    export_id: Optional[str] = None  # ID of the generated export
    status: str  # success, failed, skipped
    format: str
    file_size: Optional[int] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    email_sent: bool = Field(default=False)
    email_error: Optional[str] = None


class ScheduledExportHistory(ScheduledExportHistoryBase, table=True):
    __tablename__ = "scheduled_export_history"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    executed_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Relationships
    scheduled_export: Optional["ScheduledExport"] = Relationship(back_populates="history")


class ScheduledExportCreate(ScheduledExportBase):
    pass


class ScheduledExportUpdate(SQLModel):
    name: Optional[str] = None
    schedule: Optional[str] = None
    is_active: Optional[bool] = None
    format: Optional[str] = None
    email_recipients: Optional[List[str]] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class ScheduledExportRead(ScheduledExportBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    dashboard_name: Optional[str] = None
    creator_name: Optional[str] = None


class ScheduledExportHistoryRead(ScheduledExportHistoryBase):
    id: UUID
    executed_at: datetime