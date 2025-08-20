# ABOUTME: API endpoints for widget filtering system
# ABOUTME: Handles filter validation, application, and management

from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.models import Study, User
from app.services.filter_validator import FilterValidator
from app.services.filter_executor import FilterExecutor
from app.services.filter_parser import FilterParser
from sqlalchemy.orm.attributes import flag_modified

router = APIRouter()


class FilterValidateRequest(BaseModel):
    """Request model for filter validation"""
    widget_id: str
    expression: str
    dataset_name: str


class FilterValidateResponse(BaseModel):
    """Response model for filter validation"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    validated_columns: List[Dict[str, Any]] = []
    complexity: Optional[int] = None


class FilterApplyRequest(BaseModel):
    """Request model for applying filter to widget"""
    expression: str
    enabled: bool = True


class FilterTestRequest(BaseModel):
    """Request model for testing filter execution"""
    widget_id: str
    expression: str
    dataset_name: str
    limit: int = 100  # Limit rows for testing


class FilterTestResponse(BaseModel):
    """Response model for filter test"""
    success: bool
    row_count: int
    original_count: int
    execution_time_ms: int
    sample_data: Optional[List[Dict]] = None
    error: Optional[str] = None


class WidgetFilterConfig(BaseModel):
    """Widget filter configuration"""
    widget_id: str
    expression: Optional[str] = None
    enabled: bool = True
    last_validated: Optional[str] = None
    validation_status: Optional[str] = None


@router.post("/studies/{study_id}/widgets/{widget_id}/filter/validate", response_model=FilterValidateResponse)
async def validate_widget_filter(
    *,
    db: Session = Depends(deps.get_db),
    study_id: UUID,
    widget_id: str,
    request: FilterValidateRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Validate a filter expression for a widget
    """
    # Get study
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check user has access to study
    if study.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this study"
        )
    
    # Validate the filter
    validator = FilterValidator(db)
    result = validator.validate_filter(
        study_id=str(study_id),
        widget_id=widget_id,
        filter_expression=request.expression,
        dataset_name=request.dataset_name,
        user=current_user
    )
    
    return FilterValidateResponse(
        is_valid=result["is_valid"],
        errors=result.get("errors", []),
        warnings=result.get("warnings", []),
        validated_columns=result.get("validated_columns", []),
        complexity=result.get("complexity")
    )


@router.post("/studies/{study_id}/widgets/{widget_id}/filter/test", response_model=FilterTestResponse)
async def test_widget_filter(
    *,
    db: Session = Depends(deps.get_db),
    study_id: UUID,
    widget_id: str,
    request: FilterTestRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Test filter execution on actual data
    """
    # Get study
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check user has access
    if study.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this study"
        )
    
    # Build dataset path
    from pathlib import Path
    org_id = study.org_id
    
    # Try multiple possible data locations
    possible_paths = [
        Path(f"/data/{org_id}/studies/{study_id}/source_data"),  # Primary structure
        Path(f"/data/studies/{org_id}/{study_id}/source_data"),  # Alternative structure
    ]
    
    base_path = None
    for path in possible_paths:
        if path.exists():
            base_path = path
            break
    
    if not base_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data directory found for this study"
        )
    
    # Find latest data version
    data_versions = sorted([d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("2")])
    if not data_versions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data found for this study"
        )
    
    latest_version = data_versions[-1]
    dataset_path = latest_version / f"{request.dataset_name}.parquet"
    
    if not dataset_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {request.dataset_name} not found"
        )
    
    # Execute the filter
    executor = FilterExecutor(db)
    result = executor.execute_filter(
        study_id=str(study_id),
        widget_id=widget_id,
        filter_expression=request.expression,
        dataset_path=dataset_path,
        track_metrics=False  # Don't track metrics for test
    )
    
    # Prepare sample data
    sample_data = None
    if "data" in result and result["data"] is not None and not result["data"].empty:
        # Convert first N rows to dict for response
        sample_df = result["data"].head(request.limit)
        sample_data = sample_df.to_dict(orient="records")
    
    return FilterTestResponse(
        success="error" not in result,
        row_count=result.get("row_count", 0),
        original_count=result.get("original_count", 0),
        execution_time_ms=result.get("execution_time_ms", 0),
        sample_data=sample_data,
        error=result.get("error")
    )


@router.put("/studies/{study_id}/widgets/{widget_id}/filter")
async def apply_widget_filter(
    *,
    db: Session = Depends(deps.get_db),
    study_id: UUID,
    widget_id: str,
    request: FilterApplyRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Apply or update filter for a widget
    """
    # Get study
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check user has access
    if study.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this study"
        )
    
    # Get or initialize filter configuration
    filters = study.field_mapping_filters or {}
    
    # Update filter for widget
    if request.enabled and request.expression:
        filters[widget_id] = {
            "expression": request.expression,
            "enabled": True,
            "updated_by": str(current_user.id),
            "updated_at": datetime.now().isoformat()
        }
    elif widget_id in filters:
        # Disable or remove filter
        if request.enabled:
            filters[widget_id]["enabled"] = False
        else:
            del filters[widget_id]
    
    # Update study
    study.field_mapping_filters = filters
    flag_modified(study, "field_mapping_filters")
    db.add(study)
    db.commit()
    
    # Log audit
    from sqlalchemy import text
    audit_query = text("""
        INSERT INTO filter_audit_log 
        (id, study_id, widget_id, action, new_expression, user_id, created_at, details)
        VALUES 
        (gen_random_uuid(), :study_id, :widget_id, :action, :expression, 
         :user_id, NOW(), :details)
    """)
    
    db.execute(audit_query, {
        "study_id": str(study_id),
        "widget_id": widget_id,
        "action": "UPDATE" if widget_id in filters else "DELETE",
        "expression": request.expression if request.enabled else None,
        "user_id": str(current_user.id),
        "details": json.dumps({"enabled": request.enabled})
    })
    db.commit()
    
    return {"message": "Filter updated successfully"}


@router.get("/studies/{study_id}/widgets/{widget_id}/filter", response_model=WidgetFilterConfig)
async def get_widget_filter(
    *,
    db: Session = Depends(deps.get_db),
    study_id: UUID,
    widget_id: str,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get filter configuration for a widget
    """
    # Get study
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check user has access
    if study.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this study"
        )
    
    # Get filter configuration
    filters = study.field_mapping_filters or {}
    filter_config = filters.get(widget_id, {})
    
    # Get cached validation status
    validator = FilterValidator(db)
    cached = validator.get_cached_validation(str(study_id), widget_id)
    
    return WidgetFilterConfig(
        widget_id=widget_id,
        expression=filter_config.get("expression"),
        enabled=filter_config.get("enabled", False),
        last_validated=cached["last_validated"].isoformat() if cached else None,
        validation_status="valid" if cached and cached["is_valid"] else "invalid" if cached else None
    )


@router.get("/studies/{study_id}/filters", response_model=List[WidgetFilterConfig])
async def get_all_study_filters(
    *,
    db: Session = Depends(deps.get_db),
    study_id: UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get all filter configurations for a study
    """
    # Get study
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check user has access
    if study.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this study"
        )
    
    # Get all filters
    filters = study.field_mapping_filters or {}
    validator = FilterValidator(db)
    
    result = []
    for widget_id, config in filters.items():
        cached = validator.get_cached_validation(str(study_id), widget_id)
        
        result.append(WidgetFilterConfig(
            widget_id=widget_id,
            expression=config.get("expression"),
            enabled=config.get("enabled", False),
            last_validated=cached["last_validated"].isoformat() if cached else None,
            validation_status="valid" if cached and cached["is_valid"] else "invalid" if cached else None
        ))
    
    return result


@router.delete("/studies/{study_id}/widgets/{widget_id}/filter")
async def delete_widget_filter(
    *,
    db: Session = Depends(deps.get_db),
    study_id: UUID,
    widget_id: str,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Delete filter for a widget
    """
    # Get study
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check user has access
    if study.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this study"
        )
    
    # Remove filter
    filters = study.field_mapping_filters or {}
    if widget_id in filters:
        old_expression = filters[widget_id].get("expression")
        del filters[widget_id]
        
        study.field_mapping_filters = filters
        flag_modified(study, "field_mapping_filters")
        db.add(study)
        db.commit()
        
        # Log audit
        from sqlalchemy import text
        audit_query = text("""
            INSERT INTO filter_audit_log 
            (id, study_id, widget_id, action, old_expression, user_id, created_at)
            VALUES 
            (gen_random_uuid(), :study_id, :widget_id, 'DELETE', :old_expression, 
             :user_id, NOW())
        """)
        
        db.execute(audit_query, {
            "study_id": str(study_id),
            "widget_id": widget_id,
            "old_expression": old_expression,
            "user_id": str(current_user.id)
        })
        db.commit()
        
        return {"message": "Filter deleted successfully"}
    
    return {"message": "No filter to delete"}


@router.get("/studies/{study_id}/filters/metrics")
async def get_filter_metrics(
    *,
    db: Session = Depends(deps.get_db),
    study_id: UUID,
    widget_id: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get execution metrics for filters
    """
    # Get study
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check user has access
    if study.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this study"
        )
    
    # Get metrics
    executor = FilterExecutor(db)
    metrics = executor.get_execution_metrics(
        study_id=str(study_id),
        widget_id=widget_id,
        limit=limit
    )
    
    return {"metrics": metrics}