# ABOUTME: API endpoints for data pipeline management
# ABOUTME: Handles pipeline execution, monitoring, and configuration

from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlmodel import Session
import uuid

from app.api.deps import get_db, get_current_user
from app.models import Study, User, Message
from app.crud import study as crud_study
from app.crud import activity_log as crud_activity
from app.core.permissions import Permission, PermissionChecker
from app.clinical_modules.pipeline.tasks import execute_pipeline, get_pipeline_status
from app.clinical_modules.data_sources.tasks import test_data_source, sync_data_source

router = APIRouter()


@router.post("/studies/{study_id}/pipeline/execute")
async def execute_study_pipeline(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    pipeline_config: Optional[dict] = None,
    current_user: User = Depends(PermissionChecker(Permission.EXECUTE_PIPELINE)),
    request: Request
) -> Any:
    """Execute data pipeline for a study"""
    # Get study
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Use provided config or study's default pipeline config
    if not pipeline_config:
        pipeline_config = study.pipeline_config or {}
    
    if not pipeline_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pipeline configuration provided"
        )
    
    # Start pipeline execution task
    task = execute_pipeline.delay(
        str(study_id),
        pipeline_config,
        str(current_user.id)
    )
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="execute_pipeline",
        resource_type="pipeline",
        resource_id=task.id,
        details={
            "study_id": str(study_id),
            "task_id": task.id,
            "config": pipeline_config
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return {
        "task_id": task.id,
        "status": "started",
        "message": "Pipeline execution started",
        "study_id": str(study_id)
    }


@router.get("/pipeline/status/{task_id}")
async def get_pipeline_execution_status(
    *,
    task_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get status of a pipeline execution task"""
    result = get_pipeline_status.delay(task_id)
    status_info = result.get()
    
    # TODO: Add permission check to ensure user can view this pipeline
    
    return status_info


@router.post("/studies/{study_id}/pipeline/configure")
async def configure_study_pipeline(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    pipeline_config: dict,
    current_user: User = Depends(PermissionChecker(Permission.CONFIGURE_PIPELINE)),
    request: Request
) -> Any:
    """Configure pipeline for a study"""
    # Get study
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update pipeline configuration
    study.pipeline_config = pipeline_config
    study.updated_at = datetime.utcnow()
    study.updated_by = current_user.id
    
    db.add(study)
    db.commit()
    db.refresh(study)
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="configure_pipeline",
        resource_type="study",
        resource_id=str(study_id),
        details={"pipeline_config": pipeline_config},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return {
        "message": "Pipeline configured successfully",
        "study_id": str(study_id)
    }


@router.post("/data-sources/{data_source_id}/test")
async def test_data_source_connection(
    *,
    db: Session = Depends(get_db),
    data_source_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    request: Request
) -> Any:
    """Test data source connection"""
    # Get data source
    from app.models import DataSource
    data_source = db.get(DataSource, data_source_id)
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    # Get study to check permissions
    study = crud_study.get_study(db, study_id=data_source.study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Start test task
    task = test_data_source.delay(str(data_source_id))
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="test_data_source",
        resource_type="data_source",
        resource_id=str(data_source_id),
        details={
            "data_source_name": data_source.name,
            "task_id": task.id
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    # Wait for result (with timeout)
    try:
        result = task.get(timeout=30)
        return result
    except Exception as e:
        return {
            "task_id": task.id,
            "status": "timeout",
            "message": "Test is taking longer than expected. Check task status."
        }


@router.post("/data-sources/{data_source_id}/sync")
async def sync_data_source_data(
    *,
    db: Session = Depends(get_db),
    data_source_id: uuid.UUID,
    datasets: Optional[List[str]] = None,
    current_user: User = Depends(PermissionChecker(Permission.MANAGE_STUDY_DATA)),
    request: Request
) -> Any:
    """Synchronize data from a data source"""
    # Get data source
    from app.models import DataSource
    data_source = db.get(DataSource, data_source_id)
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found"
        )
    
    # Get study to check permissions
    study = crud_study.get_study(db, study_id=data_source.study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Start sync task
    task = sync_data_source.delay(
        str(data_source_id),
        datasets,
        str(current_user.id)
    )
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="sync_data_source",
        resource_type="data_source",
        resource_id=str(data_source_id),
        details={
            "data_source_name": data_source.name,
            "task_id": task.id,
            "datasets": datasets
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return {
        "task_id": task.id,
        "status": "started",
        "message": "Data synchronization started",
        "data_source_id": str(data_source_id)
    }


# Import datetime
from datetime import datetime