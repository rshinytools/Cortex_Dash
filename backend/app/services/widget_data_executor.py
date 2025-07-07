# ABOUTME: Widget data execution engine for fetching and processing widget data
# ABOUTME: Handles metric, chart, and table widget data with caching support

import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
from enum import Enum
import pandas as pd

from sqlmodel import Session, select
from pydantic import BaseModel, Field

from app.models.widget import WidgetDefinition, WidgetCategory
from app.models.dashboard import DashboardTemplate, StudyDashboard
from app.models.study import Study
from app.core.config import settings
from app.services.data_source_manager import get_data_source_manager, DataSourceType
from app.services.query_builder import QueryBuilder

logger = logging.getLogger(__name__)


class AggregationType(str, Enum):
    """Aggregation types for metric widgets"""
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    DISTINCT = "distinct"


class ChartType(str, Enum):
    """Chart types for chart widgets"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    STACKED_BAR = "stacked_bar"


class WidgetDataRequest(BaseModel):
    """Request model for widget data"""
    widget_id: str
    widget_config: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    pagination: Optional[Dict[str, int]] = None  # for table widgets
    refresh: bool = False


class WidgetDataResponse(BaseModel):
    """Response model for widget data"""
    widget_id: str
    data: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    cached: bool = False
    cache_expires_at: Optional[datetime] = None
    execution_time_ms: int = 0


class BaseWidgetDataExecutor(ABC):
    """Base class for widget data executors"""
    
    def __init__(self, db: Session, study: Study, widget_definition: WidgetDefinition):
        self.db = db
        self.study = study
        self.widget_definition = widget_definition
        self.field_mappings = study.field_mappings or {}
        self.data_source_manager = get_data_source_manager()
        self.query_builder = QueryBuilder()
        
    @abstractmethod
    async def execute(self, request: WidgetDataRequest) -> WidgetDataResponse:
        """Execute the widget data request"""
        pass
    
    def apply_field_mappings(self, template_field: str) -> str:
        """Apply field mappings from template to study-specific fields"""
        return self.field_mappings.get(template_field, template_field)
    
    def get_cache_key(self, request: WidgetDataRequest) -> str:
        """Generate cache key for the widget data request"""
        # Create a deterministic key based on study, widget, config, and filters
        key_parts = [
            f"widget_data",
            str(self.study.id),
            request.widget_id,
            json.dumps(request.widget_config, sort_keys=True),
            json.dumps(request.filters, sort_keys=True) if request.filters else "no_filters"
        ]
        if request.pagination:
            key_parts.append(f"page_{request.pagination.get('page', 1)}_size_{request.pagination.get('page_size', 20)}")
        return ":".join(key_parts)
    
    def get_cache_ttl(self) -> int:
        """Get cache TTL in seconds based on widget and study configuration"""
        # Default to dashboard cache TTL from settings
        default_ttl = settings.DASHBOARD_CACHE_TTL
        
        # Check if widget has specific cache configuration
        widget_cache_config = self.widget_definition.config_schema.get("cache", {})
        if "ttl" in widget_cache_config:
            return widget_cache_config["ttl"]
        
        # Check study refresh frequency
        refresh_freq = self.study.refresh_frequency
        if refresh_freq == "real_time":
            return 60  # 1 minute for real-time data
        elif refresh_freq == "hourly":
            return 3600  # 1 hour
        elif refresh_freq == "daily":
            return 86400  # 24 hours
        elif refresh_freq == "weekly":
            return 604800  # 7 days
        
        return default_ttl


class MetricWidgetDataExecutor(BaseWidgetDataExecutor):
    """Executor for metric widgets (single value displays)"""
    
    async def execute(self, request: WidgetDataRequest) -> WidgetDataResponse:
        """Execute metric widget data request"""
        start_time = datetime.utcnow()
        
        # Extract configuration
        config = request.widget_config
        aggregation = AggregationType(config.get("aggregation", "count"))
        field = config.get("field")
        dataset = config.get("dataset", "ADSL")
        data_source = config.get("data_source", "primary")
        
        # Apply field mappings
        if field:
            field = self.apply_field_mappings(field)
        
        try:
            # Check if data source is registered
            sources = await self.data_source_manager.list_sources()
            if data_source not in sources:
                # Auto-discover and register sources for this study
                discovered = await self.data_source_manager.auto_discover_sources(str(self.study.id))
                if discovered:
                    # Register the first discovered source as primary
                    first_path = list(discovered.keys())[0]
                    first_type = discovered[first_path]
                    await self.data_source_manager.register_data_source(
                        "primary",
                        first_type,
                        base_path=first_path
                    )
                else:
                    # Fall back to mock data if no sources found
                    mock_data = self._generate_mock_metric(aggregation, field, dataset)
                    execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    return WidgetDataResponse(
                        widget_id=request.widget_id,
                        data={
                            "value": mock_data["value"],
                            "label": config.get("label", field or aggregation.value),
                            "unit": config.get("unit"),
                            "change": mock_data.get("change"),
                            "trend": mock_data.get("trend")
                        },
                        metadata={
                            "aggregation": aggregation.value,
                            "field": field,
                            "dataset": dataset,
                            "data_source": "mock",
                            "filters_applied": len(request.filters) if request.filters else 0
                        },
                        cached=False,
                        execution_time_ms=execution_time_ms
                    )
            
            # Build query for the metric
            query = self.query_builder.build_metric_query(
                dataset=dataset,
                field=field,
                aggregation=aggregation.value,
                filters=request.filters
            )
            
            # Execute query
            df = await self.data_source_manager.query(data_source, query)
            
            # Extract the metric value
            if df.empty:
                value = 0
            else:
                # The query should return a single value
                value = df.iloc[0, 0] if len(df.columns) > 0 else 0
            
            # TODO: Calculate change and trend from historical data
            change = None
            trend = None
            
            # Calculate execution time
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return WidgetDataResponse(
                widget_id=request.widget_id,
                data={
                    "value": value,
                    "label": config.get("label", field or aggregation.value),
                    "unit": config.get("unit"),
                    "change": change,
                    "trend": trend
                },
                metadata={
                    "aggregation": aggregation.value,
                    "field": field,
                    "dataset": dataset,
                    "data_source": data_source,
                    "filters_applied": len(request.filters) if request.filters else 0
                },
                cached=False,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            logger.error(f"Error executing metric widget: {str(e)}")
            # Fall back to mock data on error
            mock_data = self._generate_mock_metric(aggregation, field, dataset)
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return WidgetDataResponse(
                widget_id=request.widget_id,
                data={
                    "value": mock_data["value"],
                    "label": config.get("label", field or aggregation.value),
                    "unit": config.get("unit"),
                    "change": mock_data.get("change"),
                    "trend": mock_data.get("trend")
                },
                metadata={
                    "aggregation": aggregation.value,
                    "field": field,
                    "dataset": dataset,
                    "data_source": "mock",
                    "error": str(e),
                    "filters_applied": len(request.filters) if request.filters else 0
                },
                cached=False,
                execution_time_ms=execution_time_ms
            )
    
    def _generate_mock_metric(self, aggregation: AggregationType, field: str, dataset: str) -> Dict[str, Any]:
        """Generate realistic mock data for metrics"""
        import random
        
        # Base values for different metrics
        if dataset == "ADSL":  # Subject listing
            if aggregation == AggregationType.COUNT:
                base_value = random.randint(800, 1200)
                change = random.uniform(-5, 15)
            elif aggregation == AggregationType.DISTINCT and field in ["SITEID", "COUNTRY"]:
                base_value = random.randint(20, 50)
                change = random.uniform(-2, 5)
            else:
                base_value = random.uniform(50, 80)
                change = random.uniform(-10, 10)
        elif dataset == "ADAE":  # Adverse events
            if aggregation == AggregationType.COUNT:
                base_value = random.randint(200, 500)
                change = random.uniform(-20, 30)
            else:
                base_value = random.uniform(10, 30)
                change = random.uniform(-5, 10)
        else:
            base_value = random.uniform(100, 1000)
            change = random.uniform(-10, 20)
        
        # Round based on aggregation type
        if aggregation in [AggregationType.COUNT, AggregationType.DISTINCT]:
            value = int(base_value)
        else:
            value = round(base_value, 2)
        
        return {
            "value": value,
            "change": round(change, 1),
            "trend": "up" if change > 0 else "down" if change < 0 else "stable"
        }


class ChartWidgetDataExecutor(BaseWidgetDataExecutor):
    """Executor for chart widgets (line, bar, pie charts)"""
    
    async def execute(self, request: WidgetDataRequest) -> WidgetDataResponse:
        """Execute chart widget data request"""
        start_time = datetime.utcnow()
        
        # Extract configuration
        config = request.widget_config
        chart_type = ChartType(config.get("chart_type", "line"))
        x_axis_field = config.get("x_axis_field")
        y_axis_field = config.get("y_axis_field")
        group_by_field = config.get("group_by_field")
        dataset = config.get("dataset", "ADSL")
        data_source = config.get("data_source", "primary")
        aggregation = config.get("aggregation", "count")
        
        # Apply field mappings
        if x_axis_field:
            x_axis_field = self.apply_field_mappings(x_axis_field)
        if y_axis_field:
            y_axis_field = self.apply_field_mappings(y_axis_field)
        if group_by_field:
            group_by_field = self.apply_field_mappings(group_by_field)
        
        try:
            # Check if data source is registered
            sources = await self.data_source_manager.list_sources()
            if data_source not in sources:
                # Auto-discover and register sources
                discovered = await self.data_source_manager.auto_discover_sources(str(self.study.id))
                if discovered:
                    first_path = list(discovered.keys())[0]
                    first_type = discovered[first_path]
                    await self.data_source_manager.register_data_source(
                        "primary",
                        first_type,
                        base_path=first_path
                    )
                else:
                    # Fall back to mock data
                    mock_data = self._generate_mock_chart(chart_type, x_axis_field, y_axis_field, group_by_field)
                    execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    return WidgetDataResponse(
                        widget_id=request.widget_id,
                        data={
                            "chart_type": chart_type.value,
                            "series": mock_data["series"],
                            "categories": mock_data.get("categories"),
                            "x_axis_label": config.get("x_axis_label", x_axis_field),
                            "y_axis_label": config.get("y_axis_label", y_axis_field)
                        },
                        metadata={
                            "chart_type": chart_type.value,
                            "dataset": dataset,
                            "data_source": "mock",
                            "data_points": sum(len(series["data"]) for series in mock_data["series"])
                        },
                        cached=False,
                        execution_time_ms=execution_time_ms
                    )
            
            # Build query for the chart
            query = self.query_builder.build_chart_query(
                dataset=dataset,
                x_field=x_axis_field,
                y_field=y_axis_field,
                group_by=group_by_field,
                aggregation=aggregation,
                filters=request.filters
            )
            
            # Execute query
            df = await self.data_source_manager.query(data_source, query)
            
            # Transform data for chart format
            chart_data = self._transform_to_chart_format(df, chart_type, x_axis_field, y_axis_field, group_by_field)
            
            # Calculate execution time
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return WidgetDataResponse(
                widget_id=request.widget_id,
                data={
                    "chart_type": chart_type.value,
                    "series": chart_data["series"],
                    "categories": chart_data.get("categories"),
                    "x_axis_label": config.get("x_axis_label", x_axis_field),
                    "y_axis_label": config.get("y_axis_label", y_axis_field)
                },
                metadata={
                    "chart_type": chart_type.value,
                    "dataset": dataset,
                    "data_source": data_source,
                    "data_points": sum(len(series["data"]) for series in chart_data["series"])
                },
                cached=False,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            logger.error(f"Error executing chart widget: {str(e)}")
            # Fall back to mock data
            mock_data = self._generate_mock_chart(chart_type, x_axis_field, y_axis_field, group_by_field)
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return WidgetDataResponse(
                widget_id=request.widget_id,
                data={
                    "chart_type": chart_type.value,
                    "series": mock_data["series"],
                    "categories": mock_data.get("categories"),
                    "x_axis_label": config.get("x_axis_label", x_axis_field),
                    "y_axis_label": config.get("y_axis_label", y_axis_field)
                },
                metadata={
                    "chart_type": chart_type.value,
                    "dataset": dataset,
                    "data_source": "mock",
                    "error": str(e),
                    "data_points": sum(len(series["data"]) for series in mock_data["series"])
                },
                cached=False,
                execution_time_ms=execution_time_ms
            )
    
    def _generate_mock_chart(self, chart_type: ChartType, x_field: str, y_field: str, group_field: str) -> Dict[str, Any]:
        """Generate realistic mock data for charts"""
        import random
        from datetime import date, timedelta
        
        if chart_type in [ChartType.LINE, ChartType.AREA]:
            # Time series data
            categories = []
            start_date = date.today() - timedelta(days=30)
            for i in range(30):
                categories.append((start_date + timedelta(days=i)).strftime("%Y-%m-%d"))
            
            # Generate series data
            series = []
            groups = ["Treatment A", "Treatment B", "Placebo"] if group_field else ["All Subjects"]
            
            for group in groups:
                data = []
                base_value = random.uniform(50, 150)
                for _ in categories:
                    # Add some trend and randomness
                    base_value += random.uniform(-5, 5)
                    base_value = max(0, base_value)  # Keep positive
                    data.append(round(base_value, 1))
                
                series.append({
                    "name": group,
                    "data": data
                })
            
            return {"series": series, "categories": categories}
        
        elif chart_type in [ChartType.BAR, ChartType.STACKED_BAR]:
            # Categorical data
            categories = ["Site A", "Site B", "Site C", "Site D", "Site E"]
            
            if group_field:
                # Multiple series for grouped/stacked bars
                series = []
                groups = ["Enrolled", "Completed", "Discontinued"]
                for group in groups:
                    data = [random.randint(20, 100) for _ in categories]
                    series.append({
                        "name": group,
                        "data": data
                    })
            else:
                # Single series
                data = [random.randint(50, 200) for _ in categories]
                series = [{
                    "name": y_field or "Count",
                    "data": data
                }]
            
            return {"series": series, "categories": categories}
        
        elif chart_type == ChartType.PIE:
            # Pie chart data
            categories = ["Mild", "Moderate", "Severe", "Life-threatening"]
            data = [random.randint(100, 500) for _ in categories]
            
            series = [{
                "name": y_field or "Count",
                "data": [{"name": cat, "value": val} for cat, val in zip(categories, data)]
            }]
            
            return {"series": series}
        
        elif chart_type == ChartType.SCATTER:
            # Scatter plot data
            series = []
            groups = ["Male", "Female"] if group_field else ["All"]
            
            for group in groups:
                data = []
                for _ in range(50):
                    x = random.uniform(18, 80)  # Age
                    y = random.uniform(50, 100)  # Some measurement
                    data.append({"x": round(x, 1), "y": round(y, 1)})
                
                series.append({
                    "name": group,
                    "data": data
                })
            
            return {"series": series}
        
        return {"series": [], "categories": []}
    
    def _transform_to_chart_format(self, df: pd.DataFrame, chart_type: ChartType, 
                                  x_field: str, y_field: str, group_field: Optional[str]) -> Dict[str, Any]:
        """Transform DataFrame to chart format"""
        if df.empty:
            return {"series": [], "categories": []}
        
        try:
            if chart_type in [ChartType.LINE, ChartType.AREA, ChartType.BAR, ChartType.STACKED_BAR]:
                if group_field and group_field in df.columns:
                    # Multiple series based on groups
                    series = []
                    groups = df[group_field].unique()
                    
                    # Get unique x-axis values as categories
                    categories = sorted(df[x_field].unique()) if x_field in df.columns else []
                    
                    for group in groups:
                        group_df = df[df[group_field] == group]
                        if x_field in group_df.columns and y_field in group_df.columns:
                            # Sort by x-axis field
                            group_df = group_df.sort_values(x_field)
                            series.append({
                                "name": str(group),
                                "data": group_df[y_field].tolist()
                            })
                    
                    return {"series": series, "categories": [str(cat) for cat in categories]}
                else:
                    # Single series
                    if x_field in df.columns and y_field in df.columns:
                        df = df.sort_values(x_field)
                        return {
                            "series": [{
                                "name": y_field,
                                "data": df[y_field].tolist()
                            }],
                            "categories": df[x_field].astype(str).tolist()
                        }
            
            elif chart_type == ChartType.PIE:
                # Pie chart format
                if x_field in df.columns and y_field in df.columns:
                    data = [
                        {"name": str(row[x_field]), "value": row[y_field]}
                        for _, row in df.iterrows()
                    ]
                    return {
                        "series": [{
                            "name": y_field,
                            "data": data
                        }]
                    }
            
            elif chart_type == ChartType.SCATTER:
                # Scatter plot format
                if group_field and group_field in df.columns:
                    # Multiple series
                    series = []
                    groups = df[group_field].unique()
                    
                    for group in groups:
                        group_df = df[df[group_field] == group]
                        if x_field in group_df.columns and y_field in group_df.columns:
                            data = [
                                {"x": row[x_field], "y": row[y_field]}
                                for _, row in group_df.iterrows()
                            ]
                            series.append({
                                "name": str(group),
                                "data": data
                            })
                    
                    return {"series": series}
                else:
                    # Single series
                    if x_field in df.columns and y_field in df.columns:
                        data = [
                            {"x": row[x_field], "y": row[y_field]}
                            for _, row in df.iterrows()
                        ]
                        return {
                            "series": [{
                                "name": f"{y_field} vs {x_field}",
                                "data": data
                            }]
                        }
        
        except Exception as e:
            logger.error(f"Error transforming data to chart format: {str(e)}")
        
        return {"series": [], "categories": []}


class TableWidgetDataExecutor(BaseWidgetDataExecutor):
    """Executor for table widgets with pagination support"""
    
    async def execute(self, request: WidgetDataRequest) -> WidgetDataResponse:
        """Execute table widget data request"""
        start_time = datetime.utcnow()
        
        # Extract configuration
        config = request.widget_config
        columns = config.get("columns", [])
        dataset = config.get("dataset", "ADSL")
        data_source = config.get("data_source", "primary")
        sort_by = config.get("sort_by")
        sort_order = config.get("sort_order", "asc")
        
        # Pagination
        page = 1
        page_size = 20
        if request.pagination:
            page = request.pagination.get("page", 1)
            page_size = request.pagination.get("page_size", 20)
        
        # Apply field mappings to columns
        mapped_columns = []
        for col in columns:
            mapped_col = col.copy()
            if "field" in mapped_col:
                mapped_col["field"] = self.apply_field_mappings(mapped_col["field"])
            mapped_columns.append(mapped_col)
        
        try:
            # Check if data source is registered
            sources = await self.data_source_manager.list_sources()
            if data_source not in sources:
                # Auto-discover and register sources
                discovered = await self.data_source_manager.auto_discover_sources(str(self.study.id))
                if discovered:
                    first_path = list(discovered.keys())[0]
                    first_type = discovered[first_path]
                    await self.data_source_manager.register_data_source(
                        "primary",
                        first_type,
                        base_path=first_path
                    )
                else:
                    # Fall back to mock data
                    mock_data = self._generate_mock_table(mapped_columns, dataset, page, page_size, sort_by, sort_order)
                    execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    return WidgetDataResponse(
                        widget_id=request.widget_id,
                        data={
                            "rows": mock_data["rows"],
                            "columns": mapped_columns,
                            "total_rows": mock_data["total_rows"],
                            "page": page,
                            "page_size": page_size,
                            "total_pages": (mock_data["total_rows"] + page_size - 1) // page_size
                        },
                        metadata={
                            "dataset": dataset,
                            "data_source": "mock",
                            "sorted_by": sort_by,
                            "sort_order": sort_order
                        },
                        cached=False,
                        execution_time_ms=execution_time_ms
                    )
            
            # Extract column fields
            column_fields = [col["field"] for col in mapped_columns if "field" in col]
            
            # Build query for the table
            query = self.query_builder.build_table_query(
                dataset=dataset,
                columns=column_fields,
                filters=request.filters,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=page_size,
                offset=(page - 1) * page_size
            )
            
            # Execute query
            df = await self.data_source_manager.query(data_source, query)
            
            # Get total count (without limit)
            count_query = self.query_builder.build_count_query(
                dataset=dataset,
                filters=request.filters
            )
            count_df = await self.data_source_manager.query(data_source, count_query)
            total_rows = count_df.iloc[0, 0] if not count_df.empty else 0
            
            # Convert DataFrame to list of dicts
            rows = df.to_dict('records') if not df.empty else []
            
            # Calculate execution time
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return WidgetDataResponse(
                widget_id=request.widget_id,
                data={
                    "rows": rows,
                    "columns": mapped_columns,
                    "total_rows": total_rows,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total_rows + page_size - 1) // page_size if total_rows > 0 else 0
                },
                metadata={
                    "dataset": dataset,
                    "data_source": data_source,
                    "sorted_by": sort_by,
                    "sort_order": sort_order
                },
                cached=False,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            logger.error(f"Error executing table widget: {str(e)}")
            # Fall back to mock data
            mock_data = self._generate_mock_table(mapped_columns, dataset, page, page_size, sort_by, sort_order)
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return WidgetDataResponse(
                widget_id=request.widget_id,
                data={
                    "rows": mock_data["rows"],
                    "columns": mapped_columns,
                    "total_rows": mock_data["total_rows"],
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (mock_data["total_rows"] + page_size - 1) // page_size
                },
                metadata={
                    "dataset": dataset,
                    "data_source": "mock",
                    "error": str(e),
                    "sorted_by": sort_by,
                    "sort_order": sort_order
                },
                cached=False,
                execution_time_ms=execution_time_ms
            )
    
    def _generate_mock_table(self, columns: List[Dict], dataset: str, page: int, page_size: int, 
                            sort_by: str, sort_order: str) -> Dict[str, Any]:
        """Generate realistic mock data for tables"""
        import random
        from datetime import date, timedelta
        
        # Generate total number of rows
        if dataset == "ADSL":
            total_rows = random.randint(800, 1200)
        elif dataset == "ADAE":
            total_rows = random.randint(2000, 5000)
        else:
            total_rows = random.randint(500, 1500)
        
        # Calculate pagination
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_rows)
        
        # Generate rows for current page
        rows = []
        for i in range(start_idx, end_idx):
            row = {}
            for col in columns:
                field = col.get("field", "")
                field_type = col.get("type", "string")
                
                # Generate data based on field name and type
                if field == "USUBJID":
                    row[field] = f"SUBJ-{1000 + i:04d}"
                elif field == "SITEID":
                    row[field] = f"SITE-{random.randint(1, 20):03d}"
                elif field == "AGE":
                    row[field] = random.randint(18, 85)
                elif field == "SEX":
                    row[field] = random.choice(["M", "F"])
                elif field == "RACE":
                    row[field] = random.choice(["White", "Black", "Asian", "Hispanic", "Other"])
                elif field == "COUNTRY":
                    row[field] = random.choice(["USA", "Canada", "UK", "Germany", "France", "Japan"])
                elif field == "VISITDT" or "DATE" in field:
                    days_ago = random.randint(0, 365)
                    visit_date = date.today() - timedelta(days=days_ago)
                    row[field] = visit_date.strftime("%Y-%m-%d")
                elif field == "AETERM":
                    row[field] = random.choice(["Headache", "Nausea", "Fatigue", "Dizziness", "Rash", "Fever"])
                elif field == "AESEV":
                    row[field] = random.choice(["Mild", "Moderate", "Severe"])
                elif field_type == "number":
                    row[field] = round(random.uniform(0, 100), 2)
                elif field_type == "boolean":
                    row[field] = random.choice([True, False])
                else:
                    row[field] = f"{field}_{i}"
            
            rows.append(row)
        
        return {
            "rows": rows,
            "total_rows": total_rows
        }


class WidgetDataExecutorFactory:
    """Factory for creating widget data executors"""
    
    @staticmethod
    def create_executor(db: Session, study: Study, widget_definition: WidgetDefinition) -> BaseWidgetDataExecutor:
        """Create appropriate executor based on widget category"""
        category = widget_definition.category
        
        if category == WidgetCategory.METRICS:
            return MetricWidgetDataExecutor(db, study, widget_definition)
        elif category == WidgetCategory.CHARTS:
            return ChartWidgetDataExecutor(db, study, widget_definition)
        elif category == WidgetCategory.TABLES:
            return TableWidgetDataExecutor(db, study, widget_definition)
        else:
            raise ValueError(f"Unsupported widget category: {category}")