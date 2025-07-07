# ABOUTME: Runtime widget model representing actual widget instances in dashboards
# ABOUTME: Used for widget data retrieval and dashboard rendering

from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4, UUID
from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy import JSON

if TYPE_CHECKING:
    from .runtime_dashboard import Dashboard


class Widget(SQLModel, table=True):
    """Runtime widget instance"""
    __tablename__ = "widget"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    dashboard_id: UUID = Field(foreign_key="dashboard.id", index=True)
    widget_definition_id: UUID = Field(foreign_key="widget_definitions.id", index=True)
    title: str
    description: Optional[str] = None
    type: str  # metric, line, bar, pie, scatter, table, etc.
    position: Dict[str, Any] = Field(sa_column=Column(JSON))  # x, y, w, h
    config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    data_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    dashboard: "Dashboard" = Relationship(back_populates="widgets")