# ABOUTME: Service layer for fetching widget data based on widget requirements
# ABOUTME: Handles data aggregation, filtering, and transformation for different widget types

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging

from app.models import WidgetDefinition, Study
from fastapi import HTTPException
import json

logger = logging.getLogger(__name__)


class WidgetDataService:
    """Service for fetching and processing widget data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def fetch_widget_data(
        self,
        widget_instance: Dict[str, Any],
        widget_definition: WidgetDefinition,
        global_filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Any:
        """
        Fetch data for a widget based on its requirements and configuration
        """
        if not widget_definition.data_requirements:
            raise HTTPException(status_code=400, detail="Widget has no data requirements defined")
        
        data_type = widget_definition.data_requirements.get("dataType")
        
        if data_type == "metric":
            return await self._fetch_metric_data(
                widget_instance, widget_definition, global_filters
            )
        elif data_type == "timeseries":
            return await self._fetch_timeseries_data(
                widget_instance, widget_definition, global_filters
            )
        elif data_type == "table":
            return await self._fetch_table_data(
                widget_instance, widget_definition, global_filters, page, page_size
            )
        elif data_type == "geographic":
            return await self._fetch_geographic_data(
                widget_instance, widget_definition, global_filters
            )
        elif data_type == "flow":
            return await self._fetch_flow_data(
                widget_instance, widget_definition, global_filters
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown data type: {data_type}")
    
    async def _fetch_metric_data(
        self,
        instance: Dict[str, Any],
        definition: WidgetDefinition,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fetch aggregated metric data"""
        config = instance.get("config", {})
        data_contract = definition.data_contract or {}
        
        # Mock implementation - replace with actual data fetching
        # In production, this would:
        # 1. Get the dataset and column from widget instance mapping
        # 2. Apply the specified aggregation method
        # 3. Apply filters
        # 4. Compare with previous extract if enabled
        
        # Simulate different aggregation types
        aggregation_type = config.get("aggregationType", "COUNT")
        
        if aggregation_type == "COUNT":
            mock_value = np.random.randint(100, 5000)
        elif aggregation_type == "COUNT_DISTINCT":
            mock_value = np.random.randint(50, 500)
        elif aggregation_type == "SUM":
            mock_value = round(np.random.uniform(10000, 100000), 2)
        elif aggregation_type == "AVG":
            mock_value = round(np.random.uniform(40, 80), 1)
        elif aggregation_type in ["MIN", "MAX"]:
            mock_value = np.random.randint(1, 100)
        elif aggregation_type == "MEDIAN":
            mock_value = round(np.random.uniform(45, 65), 1)
        else:
            mock_value = 0
        
        # Build response
        response = {
            "value": mock_value,
            "aggregationType": aggregation_type,
            "lastUpdated": datetime.utcnow().isoformat()
        }
        
        # Add display configuration if specified
        if config.get("format"):
            response["displayConfig"] = {
                "format": config.get("format", "number"),
                "decimalPlaces": config.get("decimalPlaces", 0),
                "prefix": config.get("prefix", ""),
                "suffix": config.get("suffix", "")
            }
        
        # Add comparison if enabled
        show_comparison = config.get("showComparison", True)
        comparison_type = config.get("comparisonType", "previous_extract")
        
        if show_comparison and comparison_type:
            mock_previous = mock_value - np.random.randint(-50, 50)
            change = mock_value - mock_previous
            change_percent = (change / mock_previous * 100) if mock_previous != 0 else 0
            
            response["comparison"] = {
                "value": mock_previous,
                "change": round(change_percent, 2),
                "type": comparison_type
            }
            
            if comparison_type == "previous_extract":
                response["comparison"]["period"] = "last extract"
            elif comparison_type == "target_value":
                response["comparison"]["period"] = "target"
                response["comparison"]["target"] = config.get("targetValue", 1000)
            elif comparison_type == "previous_period":
                response["comparison"]["period"] = config.get("comparisonPeriod", "last month")
        
        return response
    
    async def _fetch_timeseries_data(
        self,
        instance: Dict[str, Any],
        definition: WidgetDefinition,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fetch time series data"""
        requirements = definition.data_requirements
        timeseries_config = requirements.get("timeSeries", {})
        
        # Mock implementation - generate sample time series
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        dates = pd.date_range(start=start_date, end=end_date, freq='W')
        
        # Generate mock data
        enrolled = np.random.randint(5, 15, size=len(dates))
        screen_failures = np.random.randint(1, 5, size=len(dates))
        
        if timeseries_config.get("cumulative", False):
            enrolled = np.cumsum(enrolled)
            screen_failures = np.cumsum(screen_failures)
        
        data_points = []
        for i, date in enumerate(dates):
            data_points.append({
                "date": date.strftime('%Y-%m-%d'),
                "enrolled": int(enrolled[i]),
                "screenFailures": int(screen_failures[i])
            })
        
        return {
            "series": [
                {
                    "name": "Enrolled",
                    "data": [{"x": p["date"], "y": p["enrolled"]} for p in data_points]
                },
                {
                    "name": "Screen Failures",
                    "data": [{"x": p["date"], "y": p["screenFailures"]} for p in data_points]
                }
            ],
            "interval": timeseries_config.get("interval", "week")
        }
    
    async def _fetch_table_data(
        self,
        instance: Dict[str, Any],
        definition: WidgetDefinition,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """Fetch paginated table data"""
        requirements = definition.data_requirements
        dataset = requirements["datasets"]["primary"]
        required_fields = requirements["requiredFields"].get(dataset, [])
        optional_fields = requirements.get("optionalFields", {}).get(dataset, [])
        
        # Mock implementation - generate sample table data
        total_records = 250
        
        # Generate mock rows
        rows = []
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_records)
        
        for i in range(start_idx, end_idx):
            row = {
                "USUBJID": f"SUBJ{i+1:04d}",
                "SITEID": f"SITE{(i % 10) + 1:02d}",
                "AGE": np.random.randint(18, 75),
                "SEX": np.random.choice(["M", "F"]),
                "RACE": np.random.choice(["WHITE", "BLACK", "ASIAN", "OTHER"]),
                "ARM": np.random.choice(["TREATMENT", "PLACEBO", "CONTROL"])
            }
            rows.append(row)
        
        # Apply field mappings
        field_mappings = instance.get("fieldMappings", {})
        if field_mappings:
            mapped_rows = []
            for row in rows:
                mapped_row = {}
                for widget_field, data_field in field_mappings.items():
                    if data_field in row:
                        mapped_row[widget_field] = row[data_field]
                mapped_rows.append(mapped_row)
            rows = mapped_rows
        
        return {
            "data": rows,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "totalRecords": total_records,
                "totalPages": (total_records + page_size - 1) // page_size
            },
            "columns": list(rows[0].keys()) if rows else []
        }
    
    async def _fetch_geographic_data(
        self,
        instance: Dict[str, Any],
        definition: WidgetDefinition,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fetch geographic data for map widgets"""
        # Mock implementation
        sites = [
            {"name": "Boston Medical Center", "lat": 42.3601, "lng": -71.0589, "enrolled": 45},
            {"name": "UCLA Medical Center", "lat": 34.0522, "lng": -118.2437, "enrolled": 38},
            {"name": "Mayo Clinic", "lat": 44.0121, "lng": -92.4802, "enrolled": 52},
            {"name": "Johns Hopkins", "lat": 39.2904, "lng": -76.6122, "enrolled": 41},
            {"name": "Cleveland Clinic", "lat": 41.4993, "lng": -81.6944, "enrolled": 36}
        ]
        
        return {
            "locations": sites,
            "bounds": {
                "north": max(s["lat"] for s in sites),
                "south": min(s["lat"] for s in sites),
                "east": max(s["lng"] for s in sites),
                "west": min(s["lng"] for s in sites)
            }
        }
    
    async def _fetch_flow_data(
        self,
        instance: Dict[str, Any],
        definition: WidgetDefinition,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fetch flow data for Sankey diagrams"""
        # Mock implementation - patient flow through study phases
        nodes = [
            {"id": "screened", "label": "Screened", "value": 500},
            {"id": "randomized", "label": "Randomized", "value": 420},
            {"id": "treatment", "label": "On Treatment", "value": 400},
            {"id": "completed", "label": "Completed", "value": 350},
            {"id": "discontinued", "label": "Discontinued", "value": 50},
            {"id": "screen_failure", "label": "Screen Failure", "value": 80}
        ]
        
        links = [
            {"source": "screened", "target": "randomized", "value": 420},
            {"source": "screened", "target": "screen_failure", "value": 80},
            {"source": "randomized", "target": "treatment", "value": 400},
            {"source": "randomized", "target": "discontinued", "value": 20},
            {"source": "treatment", "target": "completed", "value": 350},
            {"source": "treatment", "target": "discontinued", "value": 30}
        ]
        
        return {
            "nodes": nodes,
            "links": links,
            "totalSubjects": 500
        }
    
    def _apply_filters(
        self,
        data: Any,
        filters: Optional[Dict[str, Any]] = None,
        field_mappings: Optional[Dict[str, str]] = None
    ) -> Any:
        """Apply filters to data with field mappings"""
        if not filters:
            return data
        
        # This is a simplified implementation
        # In production, this would properly parse and apply complex filter expressions
        return data
    
    def _merge_filters(
        self,
        global_filters: Optional[Dict[str, Any]] = None,
        widget_filters: Optional[Dict[str, Any]] = None,
        required_filters: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """Merge multiple filter sources"""
        filters = []
        
        if global_filters:
            filters.append(global_filters)
        
        if widget_filters:
            filters.append(widget_filters)
        
        if required_filters:
            for rf in required_filters:
                filters.append(rf)
        
        if not filters:
            return None
        
        if len(filters) == 1:
            return filters[0]
        
        # Combine filters with AND operator
        return {
            "operator": "AND",
            "filters": filters
        }