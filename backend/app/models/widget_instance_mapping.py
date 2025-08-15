# ABOUTME: Widget instance mapping models for study-specific widget configurations
# ABOUTME: Stores simplified dropdown-based mappings between uploaded data and widgets

import uuid
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import JSON, DateTime, String, UniqueConstraint

if TYPE_CHECKING:
    from .user import User
    from .study import Study
    from .widget import Widget
    from .data_source_upload import DataSourceUpload


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
    """Base properties for widget instance mapping - simplified dropdown approach"""
    widget_id: str = Field(foreign_key="widgets.id")
    data_upload_id: str = Field(foreign_key="data_source_uploads.id")
    
    # Simple dataset and field mapping
    dataset_name: str = Field(max_length=100)  # Selected dataset from upload
    field_mappings: Dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))
    # Example: {
    #   "value": "AVAL",  # Widget field -> Data column
    #   "label": "PARAM",
    #   "date": "VISITDAT",
    #   "category": "ARM"
    # }
    
    # Optional transformations (simple expressions)
    transformations: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSON))
    # Example: {
    #   "value": "value * 100",  # Simple transformation
    #   "date": "to_date(date, 'YYYY-MM-DD')"
    # }
    
    # Optional filters
    filters: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    # Example: [
    #   {"column": "AESER", "operator": "equals", "value": "Y"},
    #   {"column": "AESEV", "operator": "in_list", "value": ["MODERATE", "SEVERE"]}
    # ]
    
    # Metadata
    is_active: bool = Field(default=True)
    validation_status: Optional[str] = Field(default=None)  # valid, invalid, pending
    validation_errors: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    last_validated_at: Optional[datetime] = Field(default=None)


class WidgetInstanceMappingCreate(WidgetInstanceMappingBase):
    """Properties to receive on widget instance mapping creation"""
    pass


class WidgetInstanceMappingUpdate(SQLModel):
    """Properties to receive on widget instance mapping update"""
    data_upload_id: Optional[str] = None
    dataset_name: Optional[str] = None
    field_mappings: Optional[Dict[str, str]] = None
    transformations: Optional[Dict[str, str]] = None
    filters: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


class WidgetInstanceMapping(WidgetInstanceMappingBase, table=True):
    """Database model for widget instance mappings"""
    __tablename__ = "widget_instance_mappings"
    __table_args__ = (
        UniqueConstraint("widget_id", name="unique_widget_mapping"),
    )
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    # Audit fields
    created_by: str = Field(foreign_key="user.id")
    updated_by: Optional[str] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, onupdate=datetime.utcnow, nullable=True)
    )
    
    # Relationships
    widget: "Widget" = Relationship(back_populates="data_mappings")
    data_upload: "DataSourceUpload" = Relationship()
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