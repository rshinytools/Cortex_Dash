# ABOUTME: API endpoints for dashboard widget management
# ABOUTME: Handles widget types, configurations, and data retrieval

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlmodel import Session, select
from datetime import datetime, timedelta
import uuid
import random
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models import User, Study, Message, WidgetDefinition, WidgetCategory
from app.core.permissions import Permission, require_permission
from app.services.widget_data_service import WidgetDataService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class WidgetDataRequest(BaseModel):
    """Request model for fetching widget data"""
    widget_instance_id: str
    widget_id: int
    field_mappings: Dict[str, str] = {}
    filters: Optional[Dict[str, Any]] = None
    global_filters: Optional[Dict[str, Any]] = None
    config: Dict[str, Any] = {}
    page: Optional[int] = 1
    page_size: Optional[int] = 100


@router.get("/widget-types", response_model=List[Dict[str, Any]])
async def list_widget_types(
    category: Optional[str] = Query(None, description="Filter by widget category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get available widget types and their configurations.
    """
    widget_types = [
        {
            "id": "metric",
            "name": "Metric Card",
            "description": "Display a single metric with trend",
            "category": "basic",
            "icon": "chart-bar",
            "default_size": {"w": 3, "h": 2},
            "min_size": {"w": 2, "h": 2},
            "max_size": {"w": 6, "h": 4},
            "configurable_properties": [
                {
                    "name": "metric",
                    "type": "select",
                    "label": "Metric",
                    "required": True,
                    "options": ["count", "sum", "average", "percentage"]
                },
                {
                    "name": "dataset",
                    "type": "select",
                    "label": "Dataset",
                    "required": True
                },
                {
                    "name": "field",
                    "type": "select",
                    "label": "Field",
                    "required": False
                },
                {
                    "name": "show_trend",
                    "type": "boolean",
                    "label": "Show Trend",
                    "default": True
                }
            ]
        },
        {
            "id": "chart",
            "name": "Chart",
            "description": "Various chart types for data visualization",
            "category": "visualization",
            "icon": "chart-line",
            "default_size": {"w": 6, "h": 4},
            "min_size": {"w": 4, "h": 3},
            "max_size": {"w": 12, "h": 8},
            "configurable_properties": [
                {
                    "name": "chart_type",
                    "type": "select",
                    "label": "Chart Type",
                    "required": True,
                    "options": ["line", "bar", "scatter", "pie", "area", "heatmap"]
                },
                {
                    "name": "dataset",
                    "type": "select",
                    "label": "Dataset",
                    "required": True
                },
                {
                    "name": "x_axis",
                    "type": "select",
                    "label": "X Axis",
                    "required": True
                },
                {
                    "name": "y_axis",
                    "type": "select",
                    "label": "Y Axis",
                    "required": True
                },
                {
                    "name": "group_by",
                    "type": "select",
                    "label": "Group By",
                    "required": False
                }
            ]
        },
        {
            "id": "table",
            "name": "Data Table",
            "description": "Tabular data display with sorting and filtering",
            "category": "data",
            "icon": "table",
            "default_size": {"w": 8, "h": 4},
            "min_size": {"w": 4, "h": 3},
            "max_size": {"w": 12, "h": 8},
            "configurable_properties": [
                {
                    "name": "dataset",
                    "type": "select",
                    "label": "Dataset",
                    "required": True
                },
                {
                    "name": "columns",
                    "type": "multiselect",
                    "label": "Columns",
                    "required": True
                },
                {
                    "name": "page_size",
                    "type": "number",
                    "label": "Rows per Page",
                    "default": 10,
                    "min": 5,
                    "max": 100
                },
                {
                    "name": "enable_export",
                    "type": "boolean",
                    "label": "Enable Export",
                    "default": True
                }
            ]
        },
        {
            "id": "kpi_grid",
            "name": "KPI Grid",
            "description": "Grid of multiple KPI metrics",
            "category": "composite",
            "icon": "grid",
            "default_size": {"w": 6, "h": 3},
            "min_size": {"w": 4, "h": 2},
            "max_size": {"w": 12, "h": 6},
            "configurable_properties": [
                {
                    "name": "metrics",
                    "type": "array",
                    "label": "Metrics",
                    "required": True,
                    "item_schema": {
                        "dataset": "select",
                        "field": "select",
                        "calculation": "select",
                        "label": "text"
                    }
                },
                {
                    "name": "columns",
                    "type": "number",
                    "label": "Grid Columns",
                    "default": 3,
                    "min": 2,
                    "max": 4
                }
            ]
        },
        {
            "id": "timeline",
            "name": "Timeline",
            "description": "Event timeline visualization",
            "category": "specialized",
            "icon": "calendar",
            "default_size": {"w": 8, "h": 3},
            "min_size": {"w": 6, "h": 2},
            "max_size": {"w": 12, "h": 6},
            "configurable_properties": [
                {
                    "name": "dataset",
                    "type": "select",
                    "label": "Dataset",
                    "required": True
                },
                {
                    "name": "date_field",
                    "type": "select",
                    "label": "Date Field",
                    "required": True
                },
                {
                    "name": "event_field",
                    "type": "select",
                    "label": "Event Field",
                    "required": True
                },
                {
                    "name": "group_field",
                    "type": "select",
                    "label": "Group By",
                    "required": False
                }
            ]
        },
        {
            "id": "map",
            "name": "Geographic Map",
            "description": "Geographic distribution visualization",
            "category": "specialized",
            "icon": "map",
            "default_size": {"w": 6, "h": 4},
            "min_size": {"w": 4, "h": 3},
            "max_size": {"w": 12, "h": 8},
            "configurable_properties": [
                {
                    "name": "dataset",
                    "type": "select",
                    "label": "Dataset",
                    "required": True
                },
                {
                    "name": "location_field",
                    "type": "select",
                    "label": "Location Field",
                    "required": True
                },
                {
                    "name": "value_field",
                    "type": "select",
                    "label": "Value Field",
                    "required": True
                },
                {
                    "name": "map_type",
                    "type": "select",
                    "label": "Map Type",
                    "options": ["world", "usa", "europe"],
                    "default": "world"
                }
            ]
        }
    ]
    
    # Apply category filter
    if category:
        widget_types = [w for w in widget_types if w["category"] == category]
    
    return widget_types


@router.post("/widgets/validate-config", response_model=Dict[str, Any])
async def validate_widget_config(
    widget_config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Validate widget configuration before saving.
    """
    widget_type = widget_config.get("type")
    config = widget_config.get("config", {})
    
    # TODO: Implement actual validation logic
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "suggestions": []
    }
    
    # Example validation checks
    if not widget_type:
        validation_result["is_valid"] = False
        validation_result["errors"].append({
            "field": "type",
            "message": "Widget type is required"
        })
    
    if widget_type == "chart" and not config.get("chart_type"):
        validation_result["is_valid"] = False
        validation_result["errors"].append({
            "field": "config.chart_type",
            "message": "Chart type is required for chart widgets"
        })
    
    # Add warnings
    if widget_type == "table" and config.get("page_size", 10) > 50:
        validation_result["warnings"].append({
            "field": "config.page_size",
            "message": "Large page sizes may impact performance"
        })
    
    # Add suggestions
    if widget_type == "metric" and not config.get("show_trend"):
        validation_result["suggestions"].append({
            "field": "config.show_trend",
            "message": "Consider enabling trend display for better context"
        })
    
    return validation_result


@router.get("/widgets/{widget_id}/data", response_model=Dict[str, Any])
async def get_widget_data(
    widget_id: uuid.UUID,
    dashboard_id: uuid.UUID = Query(..., description="Dashboard ID"),
    refresh: bool = Query(False, description="Force refresh data"),
    filters: Optional[str] = Query(None, description="JSON encoded filters"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get data for a specific widget.
    """
    # TODO: Implement actual data retrieval logic
    # For now, return mock data based on widget type
    
    # Generate mock data
    mock_data = {
        "widget_id": str(widget_id),
        "dashboard_id": str(dashboard_id),
        "timestamp": datetime.utcnow().isoformat(),
        "cache_status": "hit" if not refresh else "miss",
        "data_version": "v5.0"
    }
    
    # Add type-specific mock data
    # Simulating different widget types
    widget_types = ["metric", "chart", "table", "timeline"]
    widget_type = random.choice(widget_types)
    
    if widget_type == "metric":
        mock_data["data"] = {
            "value": 1234,
            "previous_value": 1189,
            "change": 45,
            "change_percent": 3.78,
            "trend": "up",
            "unit": "subjects",
            "last_updated": datetime.utcnow().isoformat()
        }
    
    elif widget_type == "chart":
        # Generate time series data
        dates = [(datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30, 0, -1)]
        mock_data["data"] = {
            "labels": dates,
            "datasets": [
                {
                    "label": "Enrolled",
                    "data": [random.randint(100, 150) for _ in dates],
                    "color": "#3b82f6"
                },
                {
                    "label": "Screened",
                    "data": [random.randint(150, 200) for _ in dates],
                    "color": "#10b981"
                }
            ]
        }
    
    elif widget_type == "table":
        mock_data["data"] = {
            "columns": ["Subject ID", "Site", "Visit", "Date", "Status"],
            "rows": [
                [f"SUBJ-{i:04d}", f"SITE-{i % 10 + 1:02d}", f"V{i % 5 + 1}", 
                 (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d"),
                 random.choice(["Completed", "In Progress", "Scheduled"])]
                for i in range(1, 11)
            ],
            "total_count": 245,
            "page": 1,
            "page_size": 10
        }
    
    elif widget_type == "timeline":
        mock_data["data"] = {
            "events": [
                {
                    "id": str(uuid.uuid4()),
                    "date": (datetime.utcnow() - timedelta(days=i*5)).isoformat(),
                    "event": f"Event {i}",
                    "type": random.choice(["milestone", "visit", "assessment"]),
                    "description": f"Description for event {i}"
                }
                for i in range(10)
            ]
        }
    
    mock_data["metadata"] = {
        "execution_time_ms": random.randint(50, 200),
        "row_count": random.randint(100, 1000),
        "filters_applied": bool(filters)
    }
    
    return mock_data


@router.post("/widgets/batch-data", response_model=Dict[str, Any])
async def get_batch_widget_data(
    widget_ids: List[str] = Body(..., description="List of widget IDs"),
    dashboard_id: str = Body(..., description="Dashboard ID"),
    filters: Optional[Dict[str, Any]] = Body(None, description="Global filters"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get data for multiple widgets in a single request.
    """
    # TODO: Implement actual batch data retrieval
    # This is more efficient than multiple individual requests
    
    results = {}
    errors = {}
    
    for widget_id in widget_ids:
        try:
            # Mock data for each widget
            results[widget_id] = {
                "data": {
                    "value": random.randint(100, 1000),
                    "trend": random.choice(["up", "down", "stable"])
                },
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
        except Exception as e:
            errors[widget_id] = {
                "error": "Failed to load data",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    return {
        "dashboard_id": dashboard_id,
        "requested_widgets": len(widget_ids),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
        "execution_time_ms": random.randint(100, 500)
    }


@router.post("/widgets/{widget_id}/refresh", response_model=Dict[str, Any])
async def refresh_widget_data(
    widget_id: uuid.UUID,
    dashboard_id: uuid.UUID = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Force refresh data for a specific widget.
    """
    # TODO: Implement actual refresh logic
    # This would clear cache and fetch fresh data
    
    return {
        "widget_id": str(widget_id),
        "dashboard_id": str(dashboard_id),
        "status": "refreshing",
        "job_id": str(uuid.uuid4()),
        "estimated_completion": (datetime.utcnow() + timedelta(seconds=5)).isoformat(),
        "cache_cleared": True
    }


@router.get("/widgets/data-sources", response_model=List[Dict[str, Any]])
async def get_widget_data_sources(
    study_id: uuid.UUID = Query(..., description="Study ID"),
    widget_type: Optional[str] = Query(None, description="Filter by widget type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get available data sources for widgets in a study.
    """
    # TODO: Implement actual data source retrieval
    # This would return datasets and fields available for the study
    
    data_sources = [
        {
            "dataset": "ADSL",
            "name": "Subject Level Analysis Dataset",
            "type": "ADaM",
            "fields": [
                {
                    "name": "USUBJID",
                    "label": "Unique Subject ID",
                    "type": "string",
                    "is_identifier": True
                },
                {
                    "name": "AGE",
                    "label": "Age",
                    "type": "numeric",
                    "is_continuous": True
                },
                {
                    "name": "SEX",
                    "label": "Sex",
                    "type": "categorical",
                    "categories": ["M", "F"]
                },
                {
                    "name": "TRT01P",
                    "label": "Planned Treatment",
                    "type": "categorical",
                    "categories": ["Placebo", "Drug A 10mg", "Drug A 20mg"]
                }
            ],
            "compatible_widgets": ["metric", "chart", "table", "kpi_grid"]
        },
        {
            "dataset": "ADAE",
            "name": "Adverse Events Analysis Dataset",
            "type": "ADaM",
            "fields": [
                {
                    "name": "USUBJID",
                    "label": "Unique Subject ID",
                    "type": "string",
                    "is_identifier": True
                },
                {
                    "name": "AEDECOD",
                    "label": "AE Preferred Term",
                    "type": "categorical"
                },
                {
                    "name": "AESOC",
                    "label": "System Organ Class",
                    "type": "categorical"
                },
                {
                    "name": "AESER",
                    "label": "Serious AE",
                    "type": "categorical",
                    "categories": ["Y", "N"]
                },
                {
                    "name": "ASTDT",
                    "label": "AE Start Date",
                    "type": "date"
                }
            ],
            "compatible_widgets": ["metric", "chart", "table", "timeline"]
        },
        {
            "dataset": "LB",
            "name": "Laboratory Test Results",
            "type": "SDTM",
            "fields": [
                {
                    "name": "USUBJID",
                    "label": "Unique Subject ID",
                    "type": "string",
                    "is_identifier": True
                },
                {
                    "name": "LBTEST",
                    "label": "Lab Test Name",
                    "type": "categorical"
                },
                {
                    "name": "LBSTRESN",
                    "label": "Numeric Result",
                    "type": "numeric",
                    "is_continuous": True
                },
                {
                    "name": "LBDTC",
                    "label": "Date/Time of Collection",
                    "type": "datetime"
                }
            ],
            "compatible_widgets": ["chart", "table", "timeline"]
        }
    ]
    
    # Filter by widget type compatibility if specified
    if widget_type:
        data_sources = [
            ds for ds in data_sources 
            if widget_type in ds["compatible_widgets"]
        ]
    
    return data_sources


@router.post("/widgets/preview", response_model=Dict[str, Any])
async def preview_widget(
    widget_config: Dict[str, Any] = Body(...),
    sample_size: int = Query(10, description="Number of sample records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Preview widget with sample data before saving.
    """
    widget_type = widget_config.get("type")
    config = widget_config.get("config", {})
    
    # Generate preview based on widget type
    preview_data = {
        "widget_type": widget_type,
        "config": config,
        "preview_generated_at": datetime.utcnow().isoformat()
    }
    
    if widget_type == "metric":
        preview_data["sample_data"] = {
            "value": 156,
            "previous_value": 142,
            "change": 14,
            "change_percent": 9.86,
            "trend": "up"
        }
    elif widget_type == "chart":
        preview_data["sample_data"] = {
            "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
            "datasets": [{
                "label": "Sample Data",
                "data": [65, 72, 78, 85]
            }]
        }
    elif widget_type == "table":
        preview_data["sample_data"] = {
            "columns": config.get("columns", ["Col1", "Col2", "Col3"]),
            "rows": [
                [f"Row{i}-Col1", f"Row{i}-Col2", f"Row{i}-Col3"]
                for i in range(1, min(sample_size + 1, 6))
            ]
        }
    
    preview_data["render_info"] = {
        "estimated_render_time_ms": 150,
        "recommended_size": {"w": 6, "h": 4},
        "responsive": True
    }
    
    return preview_data


@router.get("/library", response_model=List[Dict[str, Any]])
async def get_widget_library(
    category: Optional[str] = Query(None, description="Filter by category name"),
    search: Optional[str] = Query(None, description="Search widgets by name or description"),
    is_active: bool = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get available widgets from the widget library.
    """
    # Query widgets from database
    query = db.query(WidgetDefinition)
    
    if category:
        # Convert category string to enum
        try:
            category_enum = WidgetCategory(category)
            query = query.filter(WidgetDefinition.category == category_enum)
        except ValueError:
            # Invalid category, return empty list
            return []
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (WidgetDefinition.name.ilike(search_pattern)) |
            (WidgetDefinition.description.ilike(search_pattern))
        )
    
    if is_active is not None:
        query = query.filter(WidgetDefinition.is_active == is_active)
    
    widgets = query.all()
    
    # Transform to response format
    result = []
    for widget in widgets:
        result.append({
            "id": str(widget.id),
            "code": widget.code,
            "name": widget.name,
            "description": widget.description,
            "category": widget.category.value,
            "version": widget.version,
            "size_constraints": widget.size_constraints,
            "config_schema": widget.config_schema,
            "default_config": widget.default_config,
            "data_requirements": widget.data_requirements,
            "data_contract": widget.data_contract,
            "is_active": widget.is_active,
            "created_at": widget.created_at.isoformat() if widget.created_at else None,
            "updated_at": widget.updated_at.isoformat() if widget.updated_at else None
        })
    
    return result


@router.get("/library/{widget_id}", response_model=Dict[str, Any])
async def get_widget_definition(
    widget_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific widget definition by ID.
    """
    widget = db.query(WidgetDefinition).filter(WidgetDefinition.id == widget_id).first()
    
    if not widget:
        raise HTTPException(status_code=404, detail="Widget definition not found")
    
    return {
        "id": str(widget.id),
        "code": widget.code,
        "name": widget.name,
        "description": widget.description,
        "category": widget.category.value,
        "version": widget.version,
        "size_constraints": widget.size_constraints,
        "config_schema": widget.config_schema,
        "default_config": widget.default_config,
        "data_requirements": widget.data_requirements,
        "data_contract": widget.data_contract,
        "is_active": widget.is_active,
        "created_at": widget.created_at.isoformat() if widget.created_at else None,
        "updated_at": widget.updated_at.isoformat() if widget.updated_at else None
    }


@router.get("/categories", response_model=List[Dict[str, Any]])
async def get_widget_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all widget categories.
    """
    # Define widget category metadata
    category_metadata = {
        WidgetCategory.METRICS: {
            "display_name": "Metrics",
            "description": "Key performance indicators and single-value displays",
            "icon": "chart-bar",
            "order": 1
        },
        WidgetCategory.CHARTS: {
            "display_name": "Charts",
            "description": "Data visualizations including line, bar, and pie charts",
            "icon": "chart-line",
            "order": 2
        },
        WidgetCategory.TABLES: {
            "display_name": "Tables",
            "description": "Tabular data displays with sorting and filtering",
            "icon": "table",
            "order": 3
        },
        WidgetCategory.MAPS: {
            "display_name": "Maps",
            "description": "Geographic data visualizations",
            "icon": "map",
            "order": 4
        },
        WidgetCategory.SPECIALIZED: {
            "display_name": "Specialized",
            "description": "Domain-specific and custom widgets",
            "icon": "puzzle",
            "order": 5
        }
    }
    
    result = []
    for category_enum in WidgetCategory:
        meta = category_metadata.get(category_enum, {})
        
        # Count widgets in this category
        widget_count = db.query(WidgetDefinition).filter(
            WidgetDefinition.category == category_enum,
            WidgetDefinition.is_active == True
        ).count()
        
        result.append({
            "id": category_enum.value,
            "name": category_enum.value,
            "display_name": meta.get("display_name", category_enum.value.title()),
            "description": meta.get("description", ""),
            "icon": meta.get("icon", "box"),
            "order": meta.get("order", 99),
            "widget_count": widget_count
        })
    
    # Sort by order
    result.sort(key=lambda x: x["order"])
    
    return result


@router.post("/data/fetch", response_model=Dict[str, Any])
async def fetch_widget_data(
    request: WidgetDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Fetch data for a specific widget instance based on its configuration.
    """
    try:
        # Get widget definition
        widget = db.query(WidgetDefinition).filter(WidgetDefinition.id == request.widget_id).first()
        if not widget:
            raise HTTPException(status_code=404, detail="Widget definition not found")
        
        # Create widget instance structure
        widget_instance = {
            "id": request.widget_instance_id,
            "widget_id": request.widget_id,
            "fieldMappings": request.field_mappings,
            "filters": request.filters,
            "config": request.config,
            "display": {
                "size": request.config.get("size", widget.default_size)
            }
        }
        
        # Initialize data service
        data_service = WidgetDataService(db)
        
        # Fetch data
        data = await data_service.fetch_widget_data(
            widget_instance=widget_instance,
            widget_definition=widget,
            global_filters=request.global_filters,
            page=request.page,
            page_size=request.page_size
        )
        
        return {
            "success": True,
            "data": data,
            "metadata": {
                "widget_type": widget.widget_type,
                "widget_name": widget.name,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching widget data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch widget data: {str(e)}"
        )