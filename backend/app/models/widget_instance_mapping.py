# ABOUTME: Widget instance mapping models for study-specific widget configurations
# ABOUTME: Stores how widgets are mapped to datasets, filters, and aggregations for each study

import uuid
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import JSON, DateTime, String, UniqueConstraint

if TYPE_CHECKING:
    from .user import User
    from .study import Study
    from .widget import WidgetDefinition


class AggregationMethod(str, Enum):
    """Available aggregation methods for widgets"""
    COUNT = "COUNT"
    COUNT_DISTINCT = "COUNT_DISTINCT"
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    MEDIAN = "MEDIAN"


class FilterOperator(str, Enum):
    """Filter operators for data filtering"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    BETWEEN = "between"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_NULL = "is_null"
    NOT_NULL = "not_null"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"


class ComparisonType(str, Enum):
    """Types of comparisons for widget data"""
    PREVIOUS_EXTRACT = "previous_extract"
    TARGET_VALUE = "target_value"
    PREVIOUS_PERIOD = "previous_period"


class WidgetInstanceMappingBase(SQLModel):
    """Base properties for widget instance mapping"""
    study_id: uuid.UUID = Field(foreign_key="study.id")
    widget_instance_id: str = Field(max_length=100)  # Unique ID within dashboard template
    widget_definition_id: uuid.UUID = Field(foreign_key="widget_definitions.id")
    
    # Dataset configuration
    dataset_name: str = Field(max_length=100)  # e.g., "AE", "DM", "ADSL"
    dataset_source: str = Field(default="source_data")  # "source_data" or "transformed_data"
    
    # Aggregation configuration
    aggregation_method: AggregationMethod
    aggregation_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    # Example: {
    #   "value_column": "AVAL",  # For SUM, AVG, etc.
    #   "unique_columns": ["USUBJID"],  # For COUNT_DISTINCT
    #   "group_by": ["SITEID", "ARM"]  # Optional grouping
    # }
    
    # Filter configuration
    filter_config: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    # Example: {
    #   "logic": "AND",
    #   "conditions": [
    #     {"column": "AETERM", "operator": "not_null"},
    #     {"column": "AESEV", "operator": "equals", "value": "SEVERE"}
    #   ],
    #   "groups": [
    #     {
    #       "logic": "OR",
    #       "conditions": [
    #         {"column": "AESER", "operator": "equals", "value": "Y"}
    #       ]
    #     }
    #   ]
    # }
    
    # Comparison configuration
    comparison_config: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    # Example: {
    #   "enabled": true,
    #   "type": "previous_extract",
    #   "label": "vs last month",
    #   "target_value": 100  # Only for target_value type
    # }
    
    # Display configuration
    display_config: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    # Example: {
    #   "format": "number",
    #   "decimal_places": 0,
    #   "prefix": "",
    #   "suffix": " subjects"
    # }
    
    # Metadata
    is_active: bool = Field(default=True)
    last_executed_at: Optional[datetime] = Field(default=None)
    last_execution_error: Optional[str] = Field(default=None, sa_column=Column(String(500)))


class WidgetInstanceMappingCreate(WidgetInstanceMappingBase):
    """Properties to receive on widget instance mapping creation"""
    pass


class WidgetInstanceMappingUpdate(SQLModel):
    """Properties to receive on widget instance mapping update"""
    dataset_name: Optional[str] = None
    dataset_source: Optional[str] = None
    aggregation_method: Optional[AggregationMethod] = None
    aggregation_config: Optional[Dict[str, Any]] = None
    filter_config: Optional[Dict[str, Any]] = None
    comparison_config: Optional[Dict[str, Any]] = None
    display_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class WidgetInstanceMapping(WidgetInstanceMappingBase, table=True):
    """Database model for widget instance mappings"""
    __tablename__ = "widget_instance_mappings"
    __table_args__ = (
        UniqueConstraint("study_id", "widget_instance_id", name="unique_study_widget_instance"),
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
    widget_definition: "WidgetDefinition" = Relationship()
    creator: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[WidgetInstanceMapping.created_by]"}
    )


class WidgetInstanceMappingPublic(WidgetInstanceMappingBase):
    """Properties to return to client"""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class WidgetInstanceMappingsPublic(SQLModel):
    """Response model for multiple widget instance mappings"""
    data: List[WidgetInstanceMappingPublic]
    count: int