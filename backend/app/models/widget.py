# ABOUTME: Widget definition models for dynamic dashboard widgets library
# ABOUTME: Contains widget definitions with configuration schemas and constraints

import uuid
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import JSON, DateTime, String, Text, Boolean, Integer

if TYPE_CHECKING:
    from .user import User


class WidgetCategory(str, Enum):
    """Widget categories for organization and filtering"""
    METRICS = "metrics"
    CHARTS = "charts"
    TABLES = "tables"
    MAPS = "maps"
    SPECIALIZED = "specialized"


class WidgetDefinitionBase(SQLModel):
    """Base properties for widget definitions"""
    code: str = Field(unique=True, index=True, max_length=50)  # e.g., 'metric_card', 'enrollment_map'
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    category: WidgetCategory = Field(default=WidgetCategory.METRICS)
    version: int = Field(default=1)
    
    # Widget configuration
    config_schema: Dict[str, Any] = Field(sa_column=Column(JSON))  # JSON Schema for configuration validation
    default_config: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Layout constraints
    size_constraints: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    # Example: {"minWidth": 2, "minHeight": 2, "maxWidth": 4, "maxHeight": 4, "defaultWidth": 2, "defaultHeight": 2}
    
    # Data requirements
    data_requirements: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    # Example: {"datasets": ["ADSL", "ADAE"], "minimum_fields": ["USUBJID"]}
    
    # Data contract - defines what data fields the widget needs and how they map
    data_contract: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    # Example: {
    #   "required_fields": [
    #     {"name": "subject_id", "type": "string", "description": "Unique subject identifier", "sdtm_mapping": "USUBJID"},
    #     {"name": "visit_date", "type": "date", "description": "Visit date", "sdtm_mapping": "VISITDT"}
    #   ],
    #   "optional_fields": [
    #     {"name": "site_id", "type": "string", "description": "Site identifier", "sdtm_mapping": "SITEID"}
    #   ],
    #   "calculated_fields": [
    #     {"name": "days_from_baseline", "type": "number", "calculation": "visit_date - baseline_date"}
    #   ],
    #   "data_sources": {
    #     "primary": {"dataset_type": "ADSL", "refresh_rate": 3600},
    #     "secondary": [{"dataset_type": "ADAE", "join_on": "subject_id"}]
    #   }
    # }
    
    # Access control
    permissions: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    # Example: {"required_permissions": ["view_safety_data"], "restricted_orgs": []}
    
    # Status
    is_active: bool = Field(default=True)


class WidgetDefinitionCreate(WidgetDefinitionBase):
    """Properties to receive on widget definition creation"""
    pass


class WidgetDefinitionUpdate(SQLModel):
    """Properties to receive on widget definition update"""
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    category: Optional[WidgetCategory] = None
    config_schema: Optional[Dict[str, Any]] = None
    default_config: Optional[Dict[str, Any]] = None
    size_constraints: Optional[Dict[str, Any]] = None
    data_requirements: Optional[Dict[str, Any]] = None
    data_contract: Optional[Dict[str, Any]] = None
    permissions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class WidgetDefinition(WidgetDefinitionBase, table=True):
    """Database model for widget definitions"""
    __tablename__ = "widget_definitions"
    
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
        sa_relationship_kwargs={"foreign_keys": "[WidgetDefinition.created_by]"}
    )
    # Widget instances are now embedded in dashboard templates, not separate entities


class WidgetDefinitionPublic(WidgetDefinitionBase):
    """Properties to return to client"""
    id: uuid.UUID
    version: int
    created_at: datetime
    updated_at: datetime


class WidgetDefinitionsPublic(SQLModel):
    """Response model for multiple widget definitions"""
    data: List[WidgetDefinitionPublic]
    count: int