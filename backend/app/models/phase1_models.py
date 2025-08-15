# ABOUTME: Phase 1 enhanced models for widget architecture
# ABOUTME: Extends existing models with data contracts and advanced mapping capabilities

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import JSON, DateTime, String, Text, Boolean, Integer, BigInteger, Float
from pydantic import BaseModel

# Import existing enums and extend them
from .data_mapping import DataType, MappingType

# Additional enums for Phase 1
class DataGranularity(str, Enum):
    """Data granularity levels"""
    SUBJECT_LEVEL = "subject_level"
    VISIT_LEVEL = "visit_level"  
    EVENT_LEVEL = "event_level"
    RECORD_LEVEL = "record_level"
    TRANSACTION_LEVEL = "transaction_level"


class AggregationType(str, Enum):
    """Supported aggregation types"""
    COUNT = "count"
    COUNT_DISTINCT = "count_distinct"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    MODE = "mode"
    PERCENTILE = "percentile"
    STDDEV = "stddev"
    VARIANCE = "variance"


class JoinType(str, Enum):
    """SQL join types"""
    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"
    FULL = "full"


class CalculationType(str, Enum):
    """Calculation types for derived fields"""
    ARITHMETIC = "arithmetic"
    DATE_DIFF = "date_diff"
    DATE_ADD = "date_add"
    STRING_CONCAT = "string_concat"
    CONDITIONAL = "conditional"
    STATISTICAL = "statistical"
    CUSTOM_SQL = "custom_sql"


# Enhanced Widget Definition with Data Contract
class WidgetDataContract(BaseModel):
    """Data contract defining widget data requirements"""
    
    # Data requirements
    granularity: DataGranularity
    required_fields: List[Dict[str, Any]]
    # Example: [
    #   {"name": "subject_id", "type": "identifier", "description": "Unique subject identifier"},
    #   {"name": "value", "type": "numeric", "description": "Measurement value"}
    # ]
    
    optional_fields: List[Dict[str, Any]]
    
    # Aggregation capabilities
    supported_aggregations: List[AggregationType]
    supports_grouping: bool = False
    grouping_fields: Optional[List[str]] = None
    
    # Filter capabilities
    supports_filtering: bool = True
    filter_operators: Dict[str, List[str]] = {
        "string": ["equals", "not_equals", "contains", "not_contains", "is_null", "not_null"],
        "numeric": ["equals", "not_equals", "greater_than", "less_than", "between", "is_null", "not_null"],
        "date": ["equals", "before", "after", "between", "is_null", "not_null"]
    }
    
    # Join capabilities
    supports_joins: bool = False
    max_join_datasets: int = 1
    
    # Performance hints
    recommended_cache_ttl: int = 3600  # seconds
    max_result_rows: Optional[int] = None
    supports_pagination: bool = True


# Core Widget Type Definitions for Phase 1
class KPIMetricCardContract(WidgetDataContract):
    """Data contract for KPI Metric Card widget"""
    
    def __init__(self):
        super().__init__(
            granularity=DataGranularity.SUBJECT_LEVEL,
            required_fields=[
                {"name": "measure_field", "type": "any", "description": "Field to aggregate"}
            ],
            optional_fields=[
                {"name": "group_field", "type": "categorical", "description": "Field for segmentation"},
                {"name": "date_field", "type": "date", "description": "Date for trending"},
                {"name": "comparison_field", "type": "numeric", "description": "Field for comparison"}
            ],
            supported_aggregations=[
                AggregationType.COUNT,
                AggregationType.COUNT_DISTINCT,
                AggregationType.SUM,
                AggregationType.AVG,
                AggregationType.MIN,
                AggregationType.MAX,
                AggregationType.MEDIAN
            ],
            supports_grouping=True,
            supports_filtering=True,
            supports_joins=False,
            recommended_cache_ttl=1800
        )


class TimeSeriesChartContract(WidgetDataContract):
    """Data contract for Time Series Chart widget"""
    
    def __init__(self):
        super().__init__(
            granularity=DataGranularity.RECORD_LEVEL,
            required_fields=[
                {"name": "date_field", "type": "date", "description": "Date/time field"},
                {"name": "value_field", "type": "numeric", "description": "Value to plot"}
            ],
            optional_fields=[
                {"name": "series_field", "type": "categorical", "description": "Field for multiple series"},
                {"name": "error_field", "type": "numeric", "description": "Error bar values"}
            ],
            supported_aggregations=[
                AggregationType.SUM,
                AggregationType.AVG,
                AggregationType.COUNT,
                AggregationType.MIN,
                AggregationType.MAX
            ],
            supports_grouping=True,
            grouping_fields=["hour", "day", "week", "month", "quarter", "year"],
            supports_filtering=True,
            supports_joins=True,
            max_join_datasets=2,
            recommended_cache_ttl=3600
        )


class DistributionChartContract(WidgetDataContract):
    """Data contract for Distribution Chart widget"""
    
    def __init__(self):
        super().__init__(
            granularity=DataGranularity.RECORD_LEVEL,
            required_fields=[
                {"name": "category_field", "type": "categorical", "description": "Category field"},
                {"name": "value_field", "type": "numeric", "description": "Value to aggregate"}
            ],
            optional_fields=[
                {"name": "subcategory_field", "type": "categorical", "description": "Nested breakdown"},
                {"name": "tooltip_fields", "type": "array", "description": "Additional tooltip data"}
            ],
            supported_aggregations=[
                AggregationType.COUNT,
                AggregationType.SUM,
                AggregationType.AVG,
                AggregationType.PERCENTILE
            ],
            supports_grouping=True,
            supports_filtering=True,
            supports_joins=True,
            max_join_datasets=1,
            recommended_cache_ttl=3600
        )


class DataTableContract(WidgetDataContract):
    """Data contract for Data Table widget"""
    
    def __init__(self):
        super().__init__(
            granularity=DataGranularity.RECORD_LEVEL,
            required_fields=[
                {"name": "display_fields", "type": "array", "description": "Fields to display as columns"}
            ],
            optional_fields=[
                {"name": "sort_field", "type": "any", "description": "Default sort field"},
                {"name": "group_field", "type": "categorical", "description": "Grouping field"}
            ],
            supported_aggregations=[
                AggregationType.COUNT,
                AggregationType.SUM,
                AggregationType.AVG
            ],
            supports_grouping=True,
            supports_filtering=True,
            supports_joins=True,
            max_join_datasets=3,
            supports_pagination=True,
            max_result_rows=10000,
            recommended_cache_ttl=1800
        )


class SubjectTimelineContract(WidgetDataContract):
    """Data contract for Subject Timeline widget"""
    
    def __init__(self):
        super().__init__(
            granularity=DataGranularity.EVENT_LEVEL,
            required_fields=[
                {"name": "subject_id", "type": "identifier", "description": "Subject identifier"},
                {"name": "event_date", "type": "date", "description": "Event date/time"},
                {"name": "event_type", "type": "categorical", "description": "Type of event"}
            ],
            optional_fields=[
                {"name": "event_category", "type": "categorical", "description": "Event category"},
                {"name": "event_duration", "type": "numeric", "description": "Duration for range events"},
                {"name": "event_value", "type": "any", "description": "Event value/description"},
                {"name": "event_status", "type": "categorical", "description": "Event status"}
            ],
            supported_aggregations=[
                AggregationType.COUNT,
                AggregationType.MIN,
                AggregationType.MAX
            ],
            supports_grouping=True,
            grouping_fields=["subject_id", "event_category"],
            supports_filtering=True,
            supports_joins=True,
            max_join_datasets=2,
            recommended_cache_ttl=3600
        )


# Widget contract registry
WIDGET_CONTRACTS = {
    "kpi_metric_card": KPIMetricCardContract,
    "time_series_chart": TimeSeriesChartContract,
    "distribution_chart": DistributionChartContract,
    "data_table": DataTableContract,
    "subject_timeline": SubjectTimelineContract
}


# Request/Response Models for Phase 1 APIs
class DatasetAnalysisRequest(BaseModel):
    """Request to analyze uploaded dataset"""
    file_path: str
    study_id: uuid.UUID
    auto_detect_granularity: bool = True
    sample_rows: int = 1000


class DatasetAnalysisResponse(BaseModel):
    """Response from dataset analysis"""
    dataset_id: uuid.UUID
    filename: str
    row_count: int
    column_count: int
    columns: List[Dict[str, Any]]
    granularity: Optional[DataGranularity]
    data_quality_score: float
    potential_keys: List[str]
    potential_joins: List[str]
    suggested_widget_types: List[str]


class MappingGenerationRequest(BaseModel):
    """Request to generate mapping suggestions"""
    study_id: uuid.UUID
    widget_id: uuid.UUID
    dataset_id: uuid.UUID
    use_template: Optional[uuid.UUID] = None


class MappingGenerationResponse(BaseModel):
    """Response with mapping suggestions"""
    widget_type: str
    dataset_name: str
    suggested_mappings: Dict[str, Dict[str, Any]]
    confidence_scores: Dict[str, float]
    validation_results: Dict[str, Any]
    sample_preview: List[Dict[str, Any]]


class CalculationBuilderRequest(BaseModel):
    """Request to build a calculation"""
    name: str
    expression: str
    expression_type: CalculationType
    input_fields: List[str]
    test_data: Optional[Dict[str, Any]] = None


class CalculationBuilderResponse(BaseModel):
    """Response from calculation builder"""
    calculation_id: uuid.UUID
    is_valid: bool
    validation_errors: Optional[List[str]]
    output_type: str
    test_result: Optional[Any]
    optimized_expression: Optional[str]


class WidgetPreviewRequest(BaseModel):
    """Request to preview widget with mapped data"""
    widget_id: uuid.UUID
    mapping_id: uuid.UUID
    filters: Optional[Dict[str, Any]] = None
    limit: int = 100


class WidgetPreviewResponse(BaseModel):
    """Response with widget preview data"""
    widget_type: str
    data: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: int
    cache_hit: bool
    warnings: Optional[List[str]]