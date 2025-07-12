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
    from .data_mapping import WidgetDataMapping


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
    # Example: {"dataType": "metric", "supportsFiltering": true, "supportsComparison": true}
    
    # Data contract - defines widget capabilities for data mapping
    data_contract: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    # Example for MetricCard: {
    #   "aggregation_options": {
    #     "methods": ["COUNT", "COUNT_DISTINCT", "SUM", "AVG", "MIN", "MAX", "MEDIAN"],
    #     "supports_grouping": true,
    #     "supports_unique_by": true
    #   },
    #   "filter_options": {
    #     "supports_complex_logic": true,
    #     "operators": {
    #       "string": ["equals", "not_equals", "contains", "not_contains", "is_null", "not_null"],
    #       "numeric": ["equals", "not_equals", "greater_than", "less_than", "between", "is_null", "not_null"],
    #       "date": ["equals", "before", "after", "between", "is_null", "not_null"]
    #     }
    #   },
    #   "comparison_options": {
    #     "types": ["previous_extract", "target_value", "previous_period"],
    #     "default": "previous_extract"
    #   },
    #   "display_options": {
    #     "formats": ["number", "percentage", "currency"],
    #     "decimal_places": [0, 1, 2],
    #     "show_trend": true
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
    data_mappings: List["WidgetDataMapping"] = Relationship(
        back_populates="widget",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


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