# ABOUTME: API endpoints for widget execution and data retrieval
# ABOUTME: Handles widget engine instantiation, query execution, and result caching

from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlmodel import Session, select
from pydantic import BaseModel

from app.api import deps
from app.models import User, WidgetDefinition, Study, WidgetDataMapping
from app.core.config import settings
from app.services.widget_engines.kpi_metric_card import KPIMetricCardEngine
from app.services.widget_engines.time_series_chart import TimeSeriesChartEngine
from app.services.widget_engines.distribution_chart import DistributionChartEngine
from app.services.widget_engines.data_table import DataTableEngine
from app.services.widget_engines.subject_timeline import SubjectTimelineEngine

router = APIRouter()


class WidgetExecutionRequest(BaseModel):
    """Request model for widget execution"""
    widget_id: UUID
    study_id: UUID
    filters: Optional[Dict[str, Any]] = {}
    parameters: Optional[Dict[str, Any]] = {}
    force_refresh: bool = False


class WidgetDataResponse(BaseModel):
    """Response model for widget data"""
    widget_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    execution_time_ms: int
    cached: bool
    cache_expires_at: Optional[datetime] = None


class WidgetValidationRequest(BaseModel):
    """Request model for widget mapping validation"""
    widget_type: str
    mapping_config: Dict[str, Any]


class WidgetValidationResponse(BaseModel):
    """Response model for widget validation"""
    valid: bool
    errors: List[str]
    data_contract: Dict[str, Any]


def get_widget_engine(widget_type: str, widget_id: UUID, study_id: UUID, mapping_config: Dict):
    """Factory function to get appropriate widget engine"""
    engines = {
        "kpi_metric_card": KPIMetricCardEngine,
        "time_series_chart": TimeSeriesChartEngine,
        "distribution_chart": DistributionChartEngine,
        "data_table": DataTableEngine,
        "subject_timeline": SubjectTimelineEngine
    }
    
    engine_class = engines.get(widget_type)
    if not engine_class:
        raise ValueError(f"Unknown widget type: {widget_type}")
    
    return engine_class(
        widget_id=widget_id,
        study_id=study_id,
        mapping_config=mapping_config
    )


@router.post("/execute", response_model=WidgetDataResponse)
def execute_widget(
    *,
    db: Session = Depends(deps.get_db),
    request: WidgetExecutionRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Execute a widget and return its data.
    
    This endpoint:
    1. Validates user access to the widget and study
    2. Retrieves the widget configuration and data mapping
    3. Instantiates the appropriate widget engine
    4. Executes the query (with caching if not force_refresh)
    5. Returns the formatted widget data
    """
    
    # Get widget
    widget = db.exec(
        select(WidgetDefinition).where(WidgetDefinition.id == request.widget_id)
    ).first()
    
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    # Get study and verify access
    study = db.exec(
        select(Study).where(Study.id == request.study_id)
    ).first()
    
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Check user has access to the study
    if not current_user.is_superuser:
        if study.org_id != current_user.org_id:
            raise HTTPException(status_code=403, detail="Access denied to this study")
    
    # Get data mapping for this widget and study
    data_mapping = db.exec(
        select(WidgetDataMapping).where(
            WidgetDataMapping.widget_definition_id == request.widget_id,
            WidgetDataMapping.study_id == request.study_id
        )
    ).first()
    
    if not data_mapping:
        raise HTTPException(
            status_code=404, 
            detail="No data mapping found for this widget and study combination"
        )
    
    # Merge mapping config with request parameters
    mapping_config = data_mapping.field_mappings.copy()
    if request.parameters:
        mapping_config.update(request.parameters)
    
    # Get appropriate widget engine
    try:
        engine = get_widget_engine(
            widget_type=widget.type,
            widget_id=widget.id,
            study_id=study.id,
            mapping_config=mapping_config
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Add filters from request
    if request.filters:
        for field, conditions in request.filters.items():
            if isinstance(conditions, dict):
                for operator, value in conditions.items():
                    engine.add_filter(field, operator, value)
            else:
                # Simple equality filter
                engine.add_filter(field, "equals", conditions)
    
    # Check cache unless force refresh
    cached_data = None
    cache_expires_at = None
    
    # TODO: Implement caching with QueryCache model
    # if not request.force_refresh:
    #     cached_data = engine.check_cache(db)
    #     if cached_data:
    #         # Get cache expiry
    #         cache_key = engine.get_cache_key()
    #         cache_entry = db.exec(
    #             select(QueryCache).where(QueryCache.cache_key == cache_key)
    #         ).first()
    #         if cache_entry:
    #             cache_expires_at = cache_entry.expires_at
    
    if cached_data:
        # Return cached data
        return WidgetDataResponse(
            widget_type=widget.type,
            data=cached_data,
            metadata={
                "widget_id": str(widget.id),
                "study_id": str(study.id),
                "from_cache": True
            },
            execution_time_ms=0,
            cached=True,
            cache_expires_at=cache_expires_at
        )
    
    # Execute query
    try:
        start_time = datetime.utcnow()
        
        # For real implementation, this would execute against actual database
        # For now, return mock data based on widget type
        mock_data = generate_mock_data(widget.widget_type, mapping_config)
        transformed_data = engine.transform_results(mock_data)
        
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # TODO: Save to cache
        # engine.save_to_cache(db, transformed_data, execution_time_ms)
        
        # TODO: Get cache expiry
        # cache_key = engine.get_cache_key()
        # cache_entry = db.exec(
        #     select(QueryCache).where(QueryCache.cache_key == cache_key)
        # ).first()
        # if cache_entry:
        #     cache_expires_at = cache_entry.expires_at
        
        return WidgetDataResponse(
            widget_type=widget.type,
            data=transformed_data,
            metadata={
                "widget_id": str(widget.id),
                "study_id": str(study.id),
                "from_cache": False,
                "query_executed": True
            },
            execution_time_ms=execution_time_ms,
            cached=False,
            cache_expires_at=cache_expires_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Widget execution failed: {str(e)}")


@router.post("/validate", response_model=WidgetValidationResponse)
def validate_widget_mapping(
    *,
    db: Session = Depends(deps.get_db),
    request: WidgetValidationRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Validate a widget mapping configuration.
    
    This endpoint:
    1. Creates a temporary widget engine instance
    2. Validates the mapping against the data contract
    3. Returns validation results and the data contract
    """
    
    # Create temporary engine for validation
    try:
        engine = get_widget_engine(
            widget_type=request.widget_type,
            widget_id=UUID("00000000-0000-0000-0000-000000000000"),  # Dummy ID
            study_id=UUID("00000000-0000-0000-0000-000000000000"),  # Dummy ID
            mapping_config=request.mapping_config
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Get data contract
    data_contract = engine.get_data_contract()
    
    # Validate mapping
    is_valid, errors = engine.validate_mapping()
    
    return WidgetValidationResponse(
        valid=is_valid,
        errors=errors,
        data_contract=data_contract
    )


@router.get("/data-contract/{widget_type}")
def get_widget_data_contract(
    widget_type: str,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get the data contract for a specific widget type.
    
    This returns the requirements and capabilities of the widget type.
    """
    
    # Create temporary engine to get data contract
    try:
        engine = get_widget_engine(
            widget_type=widget_type,
            widget_id=UUID("00000000-0000-0000-0000-000000000000"),
            study_id=UUID("00000000-0000-0000-0000-000000000000"),
            mapping_config={}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return engine.get_data_contract()


@router.get("/cache/status")
def get_cache_status(
    study_id: UUID = Query(..., description="Study ID"),
    widget_id: Optional[UUID] = Query(None, description="Widget ID (optional)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get cache status for widgets in a study.
    
    Returns information about cached queries, hit rates, and expiration times.
    """
    
    # TODO: Implement cache status with QueryCache model
    # Build query
    # query = select(QueryCache).where(QueryCache.study_id == study_id)
    # 
    # if widget_id:
    #     query = query.where(QueryCache.widget_id == widget_id)
    # 
    # cache_entries = db.exec(query).all()
    cache_entries = []
    
    # Calculate statistics
    total_entries = len(cache_entries)
    active_entries = sum(1 for e in cache_entries if e.expires_at > datetime.utcnow())
    total_hits = sum(e.hit_count for e in cache_entries)
    
    # Get per-widget statistics
    widget_stats = {}
    for entry in cache_entries:
        widget_id_str = str(entry.widget_id)
        if widget_id_str not in widget_stats:
            widget_stats[widget_id_str] = {
                "cache_entries": 0,
                "active_entries": 0,
                "total_hits": 0,
                "avg_execution_time_ms": 0
            }
        
        widget_stats[widget_id_str]["cache_entries"] += 1
        if entry.expires_at > datetime.utcnow():
            widget_stats[widget_id_str]["active_entries"] += 1
        widget_stats[widget_id_str]["total_hits"] += entry.hit_count
    
    # Calculate average execution times
    for widget_id_str in widget_stats:
        widget_entries = [e for e in cache_entries if str(e.widget_id) == widget_id_str]
        if widget_entries:
            avg_time = sum(e.execution_time_ms for e in widget_entries) / len(widget_entries)
            widget_stats[widget_id_str]["avg_execution_time_ms"] = round(avg_time)
    
    return {
        "study_id": str(study_id),
        "total_cache_entries": total_entries,
        "active_cache_entries": active_entries,
        "total_cache_hits": total_hits,
        "cache_hit_rate": round(total_hits / total_entries * 100, 1) if total_entries > 0 else 0,
        "widget_statistics": widget_stats
    }


@router.delete("/cache/clear")
def clear_widget_cache(
    study_id: UUID = Query(..., description="Study ID"),
    widget_id: Optional[UUID] = Query(None, description="Widget ID (optional)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Clear cache for widgets in a study.
    
    Requires superuser privileges.
    """
    
    # TODO: Implement cache status with QueryCache model
    # Build query
    # query = select(QueryCache).where(QueryCache.study_id == study_id)
    # 
    # if widget_id:
    #     query = query.where(QueryCache.widget_id == widget_id)
    # 
    # cache_entries = db.exec(query).all()
    cache_entries = []
    
    # Delete entries
    deleted_count = 0
    for entry in cache_entries:
        db.delete(entry)
        deleted_count += 1
    
    db.commit()
    
    return {
        "message": f"Cleared {deleted_count} cache entries",
        "study_id": str(study_id),
        "widget_id": str(widget_id) if widget_id else None
    }


def generate_mock_data(widget_type: str, mapping_config: Dict) -> List[Dict]:
    """Generate mock data for testing widgets"""
    
    if widget_type == "kpi_metric_card":
        return [{"value": 156, "group_name": "Active"}]
    
    elif widget_type == "time_series_chart":
        return [
            {"period": "2024-01", "value": 45, "series": "Treatment"},
            {"period": "2024-02", "value": 52, "series": "Treatment"},
            {"period": "2024-03", "value": 58, "series": "Treatment"},
            {"period": "2024-01", "value": 38, "series": "Control"},
            {"period": "2024-02", "value": 41, "series": "Control"},
            {"period": "2024-03", "value": 43, "series": "Control"}
        ]
    
    elif widget_type == "distribution_chart":
        return [
            {"category": "Site A", "value": 45},
            {"category": "Site B", "value": 38},
            {"category": "Site C", "value": 52},
            {"category": "Site D", "value": 31}
        ]
    
    elif widget_type == "data_table":
        return [
            {"row_id": "S001", "subject_id": "S001", "visit_date": "2024-01-15", "status": "Active"},
            {"row_id": "S002", "subject_id": "S002", "visit_date": "2024-01-18", "status": "Active"},
            {"row_id": "S003", "subject_id": "S003", "visit_date": "2024-01-22", "status": "Completed"}
        ]
    
    elif widget_type == "subject_timeline":
        return [
            {"subject_id": "S001", "event_date": "2024-01-01", "event_type": "Screening", "event_category": "Visit"},
            {"subject_id": "S001", "event_date": "2024-01-15", "event_type": "Baseline", "event_category": "Visit"},
            {"subject_id": "S001", "event_date": "2024-02-15", "event_type": "Follow-up", "event_category": "Visit"}
        ]
    
    return []