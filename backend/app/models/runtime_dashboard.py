# ABOUTME: Runtime dashboard model representing actual dashboard instances
# ABOUTME: Used for dashboard exports and runtime operations

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4, UUID
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .scheduled_export import ScheduledExport
    from .widget import Widget


class Dashboard(SQLModel, table=True):
    """Runtime dashboard instance"""
    __tablename__ = "dashboard"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    study_id: UUID = Field(foreign_key="study.id", index=True)
    template_id: Optional[UUID] = Field(foreign_key="dashboard_templates.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    scheduled_exports: List["ScheduledExport"] = Relationship(back_populates="dashboard")
    widgets: List["Widget"] = Relationship(back_populates="dashboard")