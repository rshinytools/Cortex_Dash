# ABOUTME: Real widget data executor that reads from Parquet files
# ABOUTME: Provides actual clinical data for dashboard widgets

import uuid
import time
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from sqlmodel import Session
from pydantic import BaseModel, Field

from app.models.widget import WidgetDefinition
from app.models.study import Study
from app.services.filter_executor import FilterExecutor
from app.services.filter_validator import FilterValidator

logger = logging.getLogger(__name__)


class WidgetDataRequest(BaseModel):
    """Request model for widget data"""
    widget_id: str
    widget_config: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None
    pagination: Optional[Dict[str, int]] = None
    refresh: bool = False


class WidgetDataResponse(BaseModel):
    """Response model for widget data"""
    widget_id: str
    status: str = "success"
    data: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    cached: bool = False
    cache_expires_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    error: Optional[str] = None


class RealWidgetExecutor:
    """Executor that reads real data from Parquet files"""
    
    def __init__(self, db: Session, study: Study, widget_def: WidgetDefinition):
        self.db = db
        self.study = study
        self.widget_def = widget_def
        self.filter_executor = FilterExecutor(db)
        self.filter_validator = FilterValidator(db)
        
        # Data is stored under org_id/studies/study_id/source_data/date/
        # First, try the most recent date
        base_path = Path(f"/data/{study.org_id}/studies/{study.id}/source_data")
        if base_path.exists():
            # Get the most recent date folder
            date_folders = sorted([d for d in base_path.iterdir() if d.is_dir()], reverse=True)
            if date_folders:
                self.data_path = date_folders[0]
            else:
                self.data_path = base_path
        else:
            # Fallback to old path structure
            self.data_path = Path(f"/data/studies/{study.id}/parquet")
    
    async def execute(self, request: WidgetDataRequest) -> WidgetDataResponse:
        """Execute widget data request - returns real data from Parquet files"""
        start_time = time.time()
        
        logger.info(f"Executing widget {request.widget_id} for study {self.study.id}")
        logger.info(f"Widget category: {self.widget_def.category}")
        
        try:
            # Determine widget type from category
            category = self.widget_def.category.lower() if self.widget_def.category else "metrics"
            
            # Get real data based on widget type
            if category in ["metrics", "kpi"]:
                data = await self._get_real_kpi_data(request.widget_config)
            else:
                # For other widget types, return empty data for now
                data = {"value": 0, "label": "No data"}
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return WidgetDataResponse(
                widget_id=request.widget_id,
                status="success",
                data=data,
                metadata={
                    "study_id": str(self.study.id),
                    "widget_type": category,
                    "is_real_data": True,
                    "data_source": "parquet"
                },
                execution_time_ms=execution_time,
                cached=False
            )
        except Exception as e:
            logger.error(f"Error executing widget: {str(e)}")
            return WidgetDataResponse(
                widget_id=request.widget_id,
                status="error",
                data=None,
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
    
    async def _get_real_kpi_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get real KPI data from Parquet files using field mappings from database"""
        try:
            logger.info(f"Widget config received: {config}")
            widget_id = config.get("id", "")
            widget_title = config.get("title", "Unknown")
            
            # Get field mappings from the study
            field_mappings = self.study.field_mappings or {}
            logger.info(f"Field mappings available: {list(field_mappings.keys())}")
            
            # Look for mapping for this widget
            # Try different mapping key formats
            mapping_keys = [
                widget_id,  # Direct widget ID
                f"{widget_id}_value",  # Widget ID with _value suffix
                f"{widget_id}_value_field",  # Widget ID with _value_field suffix
                widget_title.lower().replace(" ", "_"),  # Title-based key
            ]
            
            mapping_value = None
            for key in mapping_keys:
                if key in field_mappings:
                    mapping_value = field_mappings[key]
                    logger.info(f"Found mapping for key '{key}': {mapping_value}")
                    break
            
            if not mapping_value:
                logger.warning(f"No field mapping found for widget {widget_id} ({widget_title})")
                return {
                    "value": 0,
                    "label": widget_title,
                    "error": "No field mapping configured"
                }
            
            # Parse the mapping (format: dataset.column)
            if "." in mapping_value:
                dataset_name, column_name = mapping_value.split(".", 1)
            else:
                # If no dot, assume it's just a dataset name
                dataset_name = mapping_value
                column_name = None
            
            # Load the dataset
            dataset_path = self.data_path / f"{dataset_name}.parquet"
            if not dataset_path.exists():
                logger.error(f"Dataset file not found: {dataset_path}")
                return {
                    "value": 0,
                    "label": widget_title,
                    "error": f"Dataset {dataset_name} not found"
                }
            
            # Read the parquet file
            df = pd.read_parquet(dataset_path)
            logger.info(f"Loaded dataset {dataset_name} with {len(df)} rows")
            
            # Check for filter configuration
            filter_config = self._get_filter_config(widget_id)
            if filter_config and filter_config.get('expression'):
                logger.info(f"Applying filter for widget {widget_id}: {filter_config['expression']}")
                
                # Apply the filter
                filtered_result = await self._apply_widget_filter(
                    df=df,
                    expression=filter_config['expression'],
                    dataset_name=dataset_name,
                    widget_id=widget_id
                )
                
                if filtered_result['success']:
                    df = filtered_result['data']
                    logger.info(f"Filter applied successfully. Rows after filtering: {len(df)}")
                else:
                    logger.warning(f"Filter failed, continuing without filter: {filtered_result.get('error')}")
                    # Continue without filter rather than fail the widget
            
            # Calculate the value based on aggregation type
            aggregation = field_mappings.get(f"{widget_id}_aggregation", "count_distinct")
            
            if column_name and column_name in df.columns:
                if aggregation == "count_distinct":
                    value = df[column_name].nunique()
                elif aggregation == "count":
                    value = len(df)
                elif aggregation == "sum":
                    value = df[column_name].sum()
                elif aggregation == "mean":
                    value = df[column_name].mean()
                elif aggregation == "max":
                    value = df[column_name].max()
                elif aggregation == "min":
                    value = df[column_name].min()
                else:
                    value = len(df)  # Default to count
            else:
                # No specific column, just count rows
                value = len(df)
            
            logger.info(f"Calculated value: {value} using aggregation: {aggregation}")
            
            return {
                "value": value,
                "label": widget_title,
                "dataset": dataset_name,
                "column": column_name,
                "aggregation": aggregation,
                "trend": "0%",  # Trend calculation would need historical data
                "comparison": "current period"
            }
            
        except Exception as e:
            logger.error(f"Error reading Parquet data: {str(e)}")
            return {
                "value": 0,
                "label": "Error",
                "error": str(e)
            }
    
    def _get_filter_config(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """Get filter configuration for a widget from study settings"""
        try:
            # Check if study has filter configurations
            filters = self.study.field_mapping_filters or {}
            return filters.get(widget_id)
        except Exception as e:
            logger.error(f"Error getting filter config: {str(e)}")
            return None
    
    async def _apply_widget_filter(
        self,
        df: pd.DataFrame,
        expression: str,
        dataset_name: str,
        widget_id: str
    ) -> Dict[str, Any]:
        """Apply filter to dataframe with error handling"""
        try:
            # Execute the filter
            result = self.filter_executor.execute_filter(
                study_id=str(self.study.id),
                widget_id=widget_id,
                filter_expression=expression,
                dataset_path=self.data_path / f"{dataset_name}.parquet",
                track_metrics=True
            )
            
            if "error" in result:
                return {
                    "success": False,
                    "error": result["error"],
                    "data": df  # Return original data on error
                }
            
            return {
                "success": True,
                "data": result["data"],
                "metrics": {
                    "original_count": result["original_count"],
                    "filtered_count": result["row_count"],
                    "reduction_percentage": result["reduction_percentage"],
                    "execution_time_ms": result["execution_time_ms"]
                }
            }
            
        except Exception as e:
            logger.error(f"Filter execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": df  # Return original data on error
            }


class WidgetDataExecutorFactory:
    """Factory for creating widget data executors"""
    
    @staticmethod
    def create_executor(db: Session, study: Study, widget_def: WidgetDefinition):
        """Create executor - returns RealWidgetExecutor"""
        return RealWidgetExecutor(db, study, widget_def)