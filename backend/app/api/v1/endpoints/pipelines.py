# ABOUTME: API endpoints for data pipeline management
# ABOUTME: Handles pipeline execution, monitoring, and configuration

from typing import List, Any, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks, Query
from sqlmodel import Session, select
import uuid
from datetime import datetime, timedelta

from app.api.deps import get_db, get_current_user
from app.models import Study, User, Message
from app.crud import study as crud_study
from app.crud import activity_log as crud_activity
from app.core.permissions import Permission, PermissionChecker, require_permission
from app.clinical_modules.pipeline.tasks import execute_pipeline, get_pipeline_status
from app.clinical_modules.data_sources.tasks import test_data_source, sync_data_source
from app.core.celery_app import celery_app
from celery.result import AsyncResult

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


@router.get("/pipelines/{pipeline_id}/status", response_model=Dict[str, Any])
async def get_pipeline_status_detailed(
    pipeline_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_PIPELINE_LOGS))
) -> Any:
    """
    Get detailed status of a pipeline execution.
    """
    task_result = AsyncResult(pipeline_id, app=celery_app)
    
    if not task_result:
        raise HTTPException(status_code=404, detail="Pipeline execution not found")
    
    # Get basic task info
    status_info = {
        "task_id": pipeline_id,
        "status": task_result.status,
        "ready": task_result.ready(),
        "successful": task_result.successful() if task_result.ready() else None,
        "failed": task_result.failed() if task_result.ready() else None
    }
    
    # Add result or error info
    if task_result.ready():
        if task_result.successful():
            status_info["result"] = task_result.result
        elif task_result.failed():
            status_info["error"] = str(task_result.info)
            status_info["traceback"] = task_result.traceback
    else:
        # Task is still running, get progress info if available
        status_info["info"] = task_result.info
    
    return status_info


@router.get("/pipelines/{pipeline_id}/logs", response_model=List[Dict[str, Any]])
async def get_pipeline_logs(
    pipeline_id: str,
    limit: int = Query(100, description="Maximum number of log entries to return"),
    offset: int = Query(0, description="Number of log entries to skip"),
    level: Optional[str] = Query(None, description="Filter by log level (DEBUG, INFO, WARNING, ERROR)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_PIPELINE_LOGS))
) -> Any:
    """
    Get execution logs for a pipeline.
    """
    # In a real implementation, this would query a logging database or service
    # For now, return mock data
    logs = [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "message": f"Pipeline {pipeline_id} execution started",
            "context": {"step": "initialization"}
        },
        {
            "timestamp": (datetime.utcnow() + timedelta(seconds=1)).isoformat(),
            "level": "INFO",
            "message": "Connecting to data source",
            "context": {"step": "data_acquisition"}
        },
        {
            "timestamp": (datetime.utcnow() + timedelta(seconds=2)).isoformat(),
            "level": "INFO",
            "message": "Data download completed",
            "context": {"step": "data_acquisition", "records": 1000}
        }
    ]
    
    # Filter by level if specified
    if level:
        logs = [log for log in logs if log["level"] == level]
    
    # Apply pagination
    return logs[offset:offset + limit]


@router.post("/pipelines/{pipeline_id}/cancel")
async def cancel_pipeline_execution(
    pipeline_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.EXECUTE_PIPELINE))
) -> Any:
    """
    Cancel a running pipeline execution.
    """
    task_result = AsyncResult(pipeline_id, app=celery_app)
    
    if not task_result:
        raise HTTPException(status_code=404, detail="Pipeline execution not found")
    
    if task_result.ready():
        return {
            "message": "Pipeline has already completed",
            "status": task_result.status
        }
    
    # Revoke the task
    task_result.revoke(terminate=True)
    
    # Log the cancellation
    # TODO: Add proper activity logging
    
    return {
        "message": "Pipeline cancellation requested",
        "task_id": pipeline_id,
        "status": "REVOKED"
    }


@router.post("/pipelines/{pipeline_id}/retry")
async def retry_pipeline_execution(
    pipeline_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.EXECUTE_PIPELINE))
) -> Any:
    """
    Retry a failed pipeline execution.
    """
    task_result = AsyncResult(pipeline_id, app=celery_app)
    
    if not task_result:
        raise HTTPException(status_code=404, detail="Pipeline execution not found")
    
    if not task_result.failed():
        return {
            "message": "Pipeline has not failed, cannot retry",
            "status": task_result.status
        }
    
    # Get the original task arguments
    # In a real implementation, we would store these in a database
    # For now, return a mock response
    return {
        "message": "Pipeline retry functionality not yet implemented",
        "original_task_id": pipeline_id,
        "status": "pending_implementation"
    }


@router.get("/pipelines/executions", response_model=List[Dict[str, Any]])
async def list_pipeline_executions(
    study_id: Optional[uuid.UUID] = Query(None, description="Filter by study ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(100, description="Maximum number of executions to return"),
    offset: int = Query(0, description="Number of executions to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_PIPELINE_LOGS))
) -> Any:
    """
    List pipeline executions with filtering and pagination.
    """
    # In a real implementation, this would query a pipeline execution history table
    # For now, return mock data
    executions = [
        {
            "id": str(uuid.uuid4()),
            "study_id": str(study_id) if study_id else str(uuid.uuid4()),
            "status": "SUCCESS",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
            "duration_seconds": 300,
            "records_processed": 1000,
            "created_by": str(current_user.id)
        }
    ]
    
    return executions[offset:offset + limit]


@router.get("/pipelines/executions/{execution_id}", response_model=Dict[str, Any])
async def get_pipeline_execution_details(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_PIPELINE_LOGS))
) -> Any:
    """
    Get detailed information about a specific pipeline execution.
    """
    # In a real implementation, this would query execution details from database
    # For now, return mock data
    return {
        "id": execution_id,
        "study_id": str(uuid.uuid4()),
        "status": "SUCCESS",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
        "duration_seconds": 300,
        "pipeline_config": {
            "data_sources": ["medidata_rave"],
            "transformations": ["standardize", "validate"],
            "output_format": "parquet"
        },
        "execution_steps": [
            {
                "step": "data_acquisition",
                "status": "SUCCESS",
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": (datetime.utcnow() + timedelta(minutes=2)).isoformat(),
                "records": 1000
            },
            {
                "step": "transformation",
                "status": "SUCCESS",
                "started_at": (datetime.utcnow() + timedelta(minutes=2)).isoformat(),
                "completed_at": (datetime.utcnow() + timedelta(minutes=4)).isoformat(),
                "records": 950
            },
            {
                "step": "validation",
                "status": "SUCCESS",
                "started_at": (datetime.utcnow() + timedelta(minutes=4)).isoformat(),
                "completed_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                "issues": 0
            }
        ],
        "created_by": str(current_user.id),
        "error": None
    }