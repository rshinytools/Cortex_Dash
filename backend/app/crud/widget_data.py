# ABOUTME: CRUD operations for loading and transforming widget data from study datasets
# ABOUTME: Handles dynamic data loading based on widget configurations and data bindings

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlmodel import Session, select, func
from sqlalchemy import and_, or_, text
import uuid
import pandas as pd
import numpy as np
from pathlib import Path
import json

from app.models import (
    Study,
    DashboardWidget,
    WidgetDefinition
)
from app.core.config import settings


class WidgetDataLoader:
    """Handles loading and transforming data for widgets"""
    
    def __init__(self, db: Session, study_id: uuid.UUID):
        self.db = db
        self.study_id = study_id
        self.study = db.get(Study, study_id)
        if not self.study:
            raise ValueError(f"Study {study_id} not found")
        
        # Build path to study data
        self.data_path = Path(settings.DATA_DIR) / "studies" / str(study_id) / "processed"
    
    def get_available_datasets(self) -> List[str]:
        """Get list of available datasets for the study"""
        if not self.data_path.exists():
            return []
        
        # Look for parquet files in the processed directory
        datasets = []
        for file in self.data_path.glob("*.parquet"):
            datasets.append(file.stem.upper())
        
        return sorted(datasets)
    
    def load_dataset(self, dataset_name: str) -> pd.DataFrame:
        """Load a dataset from parquet file"""
        file_path = self.data_path / f"{dataset_name.lower()}.parquet"
        
        if not file_path.exists():
            # Try uppercase
            file_path = self.data_path / f"{dataset_name.upper()}.parquet"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset {dataset_name} not found for study")
        
        return pd.read_parquet(file_path)
    
    def apply_filters(
        self, 
        df: pd.DataFrame, 
        filters: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """Apply filters to a dataframe"""
        for filter_spec in filters:
            field = filter_spec.get("field")
            operator = filter_spec.get("operator", "=")
            value = filter_spec.get("value")
            
            if field not in df.columns:
                continue
            
            if operator == "=":
                df = df[df[field] == value]
            elif operator == "!=":
                df = df[df[field] != value]
            elif operator == ">":
                df = df[df[field] > value]
            elif operator == "<":
                df = df[df[field] < value]
            elif operator == ">=":
                df = df[df[field] >= value]
            elif operator == "<=":
                df = df[df[field] <= value]
            elif operator == "in":
                df = df[df[field].isin(value)]
            elif operator == "not_in":
                df = df[~df[field].isin(value)]
            elif operator == "contains":
                df = df[df[field].str.contains(value, na=False)]
        
        return df
    
    def apply_time_range(
        self, 
        df: pd.DataFrame, 
        time_field: str, 
        time_range: str
    ) -> pd.DataFrame:
        """Apply time range filter to a dataframe"""
        if time_field not in df.columns:
            return df
        
        # Convert to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(df[time_field]):
            df[time_field] = pd.to_datetime(df[time_field], errors='coerce')
        
        # Calculate date range
        end_date = datetime.utcnow()
        
        if time_range == "1w":
            start_date = end_date - timedelta(weeks=1)
        elif time_range == "1m":
            start_date = end_date - timedelta(days=30)
        elif time_range == "3m":
            start_date = end_date - timedelta(days=90)
        elif time_range == "6m":
            start_date = end_date - timedelta(days=180)
        elif time_range == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            return df  # No filter for "all" or unknown ranges
        
        return df[(df[time_field] >= start_date) & (df[time_field] <= end_date)]


def get_widget_data(
    db: Session,
    study_id: uuid.UUID,
    widget_id: uuid.UUID,
    time_range: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Load data for a single widget"""
    # Get widget configuration
    widget = db.get(DashboardWidget, widget_id)
    if not widget:
        raise ValueError(f"Widget {widget_id} not found")
    
    widget_def = widget.widget_definition
    instance_config = widget.instance_config
    data_binding = widget.data_binding or {}
    
    # Initialize data loader
    loader = WidgetDataLoader(db, study_id)
    
    # Load dataset
    dataset_name = instance_config.get("dataset") or data_binding.get("dataset")
    if not dataset_name:
        return {"error": "No dataset specified for widget"}
    
    try:
        df = loader.load_dataset(dataset_name)
    except FileNotFoundError:
        return {"error": f"Dataset {dataset_name} not found"}
    
    # Apply data binding filters
    if data_binding.get("filters"):
        df = loader.apply_filters(df, data_binding["filters"])
    
    # Apply runtime filters
    if filters:
        runtime_filters = []
        for field, value in filters.items():
            runtime_filters.append({
                "field": field,
                "operator": "=",
                "value": value
            })
        df = loader.apply_filters(df, runtime_filters)
    
    # Apply time range if specified
    if time_range and data_binding.get("time_field"):
        df = loader.apply_time_range(df, data_binding["time_field"], time_range)
    
    # Transform data based on widget type
    result = transform_data_for_widget(
        df=df,
        widget_def=widget_def,
        instance_config=instance_config,
        data_binding=data_binding
    )
    
    return result


def get_batch_widget_data(
    db: Session,
    study_id: uuid.UUID,
    widget_ids: List[uuid.UUID],
    time_range: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Load data for multiple widgets in batch"""
    results = []
    
    for widget_id in widget_ids:
        try:
            data = get_widget_data(
                db=db,
                study_id=study_id,
                widget_id=widget_id,
                time_range=time_range,
                filters=filters
            )
            results.append({
                "widget_id": widget_id,
                "data": data,
                "success": True
            })
        except Exception as e:
            results.append({
                "widget_id": widget_id,
                "data": {},
                "success": False,
                "error": str(e)
            })
    
    return results


def transform_data_for_widget(
    df: pd.DataFrame,
    widget_def: WidgetDefinition,
    instance_config: Dict[str, Any],
    data_binding: Dict[str, Any]
) -> Dict[str, Any]:
    """Transform raw data for widget consumption based on widget type"""
    
    if widget_def.category == "metrics":
        return transform_metric_data(df, instance_config, data_binding)
    elif widget_def.category == "charts":
        return transform_chart_data(df, instance_config, data_binding)
    elif widget_def.category == "tables":
        return transform_table_data(df, instance_config, data_binding)
    elif widget_def.category == "maps":
        return transform_map_data(df, instance_config, data_binding)
    else:
        return {"error": f"Unknown widget category: {widget_def.category}"}


def transform_metric_data(
    df: pd.DataFrame,
    config: Dict[str, Any],
    binding: Dict[str, Any]
) -> Dict[str, Any]:
    """Transform data for metric widgets"""
    field = config.get("field", binding.get("field"))
    calculation = config.get("calculation", "count")
    
    if not field and calculation != "count":
        return {"error": "Field not specified for calculation"}
    
    # Perform calculation
    if calculation == "count":
        if field and field in df.columns:
            value = df[field].notna().sum()
        else:
            value = len(df)
    elif calculation == "sum":
        value = df[field].sum() if field in df.columns else 0
    elif calculation == "avg" or calculation == "mean":
        value = df[field].mean() if field in df.columns else 0
    elif calculation == "min":
        value = df[field].min() if field in df.columns else 0
    elif calculation == "max":
        value = df[field].max() if field in df.columns else 0
    elif calculation == "distinct":
        value = df[field].nunique() if field in df.columns else 0
    else:
        value = 0
    
    # Calculate trend if requested
    result = {
        "value": float(value) if not pd.isna(value) else 0,
        "calculation": calculation,
        "field": field,
        "dataset": config.get("dataset", binding.get("dataset"))
    }
    
    # Add trend calculation if configured
    if config.get("showTrend", True) and binding.get("trend_field"):
        # This would require historical data comparison
        # For now, return mock trend
        result["trend"] = "up"
        result["change"] = 10
        result["change_percent"] = 3.5
    
    return result


def transform_chart_data(
    df: pd.DataFrame,
    config: Dict[str, Any],
    binding: Dict[str, Any]
) -> Dict[str, Any]:
    """Transform data for chart widgets"""
    chart_type = config.get("chartType", "line")
    x_field = config.get("xAxis", binding.get("x_field"))
    y_field = config.get("yAxis", binding.get("y_field"))
    group_by = config.get("groupBy", binding.get("group_field"))
    
    if not x_field:
        return {"error": "X-axis field not specified"}
    
    if x_field not in df.columns:
        return {"error": f"Field {x_field} not found in dataset"}
    
    # Handle different chart types
    if chart_type in ["line", "bar", "area"]:
        if group_by and group_by in df.columns:
            # Group data
            datasets = []
            for group_value in df[group_by].unique():
                group_df = df[df[group_by] == group_value]
                
                if y_field and y_field in df.columns:
                    # Aggregate by x-axis
                    aggregated = group_df.groupby(x_field)[y_field].sum().reset_index()
                else:
                    # Count by x-axis
                    aggregated = group_df.groupby(x_field).size().reset_index(name='count')
                    y_field = 'count'
                
                datasets.append({
                    "label": str(group_value),
                    "data": aggregated[y_field].tolist()
                })
            
            labels = aggregated[x_field].tolist()
        else:
            # Single dataset
            if y_field and y_field in df.columns:
                aggregated = df.groupby(x_field)[y_field].sum().reset_index()
            else:
                aggregated = df.groupby(x_field).size().reset_index(name='count')
                y_field = 'count'
            
            labels = aggregated[x_field].tolist()
            datasets = [{
                "label": config.get("title", "Data"),
                "data": aggregated[y_field].tolist()
            }]
        
        return {
            "labels": [str(label) for label in labels],
            "datasets": datasets,
            "chartType": chart_type
        }
    
    elif chart_type == "pie" or chart_type == "doughnut":
        # For pie charts, use x_field as category
        if x_field in df.columns:
            value_counts = df[x_field].value_counts()
            return {
                "labels": value_counts.index.tolist(),
                "datasets": [{
                    "data": value_counts.values.tolist()
                }],
                "chartType": chart_type
            }
    
    return {"error": f"Unsupported chart type: {chart_type}"}


def transform_table_data(
    df: pd.DataFrame,
    config: Dict[str, Any],
    binding: Dict[str, Any]
) -> Dict[str, Any]:
    """Transform data for table widgets"""
    columns = config.get("columns", binding.get("columns"))
    page_size = config.get("pageSize", 20)
    
    # Select columns if specified
    if columns and isinstance(columns, list):
        available_columns = [col for col in columns if col in df.columns]
        if available_columns:
            df = df[available_columns]
    
    # Convert to list of records
    total_count = len(df)
    
    # Limit to first page for now
    df_page = df.head(page_size)
    
    # Convert to records
    rows = []
    for _, row in df_page.iterrows():
        row_data = []
        for col in df.columns:
            value = row[col]
            # Convert numpy/pandas types to Python types
            if pd.isna(value):
                value = None
            elif isinstance(value, (np.integer, np.int64)):
                value = int(value)
            elif isinstance(value, (np.floating, np.float64)):
                value = float(value)
            elif isinstance(value, pd.Timestamp):
                value = value.strftime("%Y-%m-%d")
            else:
                value = str(value)
            row_data.append(value)
        rows.append(row_data)
    
    return {
        "headers": df.columns.tolist(),
        "rows": rows,
        "total_count": total_count,
        "page": 1,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size
    }


def transform_map_data(
    df: pd.DataFrame,
    config: Dict[str, Any],
    binding: Dict[str, Any]
) -> Dict[str, Any]:
    """Transform data for map widgets"""
    # This would require geographic data processing
    # For now, return a placeholder
    return {
        "type": "FeatureCollection",
        "features": [],
        "error": "Map data transformation not yet implemented"
    }


def get_widget_preview_data(
    db: Session,
    widget_def_id: uuid.UUID,
    sample_config: Dict[str, Any],
    sample_size: int = 10
) -> Dict[str, Any]:
    """Generate preview data for a widget definition"""
    widget_def = db.get(WidgetDefinition, widget_def_id)
    if not widget_def:
        return {"error": "Widget definition not found"}
    
    # Generate sample data based on widget type
    if widget_def.category == "metrics":
        return {
            "value": 142,
            "previous_value": 125,
            "change": 17,
            "change_percent": 13.6,
            "trend": "up"
        }
    elif widget_def.category == "charts":
        return {
            "labels": [f"Point {i+1}" for i in range(5)],
            "datasets": [{
                "label": "Sample Data",
                "data": [10, 25, 15, 30, 20]
            }]
        }
    elif widget_def.category == "tables":
        return {
            "headers": ["Column 1", "Column 2", "Column 3"],
            "rows": [
                [f"Row {i+1}", f"Value {i+1}", f"Status {i+1}"]
                for i in range(sample_size)
            ],
            "total_count": sample_size
        }
    
    return {"error": f"No preview available for category: {widget_def.category}"}