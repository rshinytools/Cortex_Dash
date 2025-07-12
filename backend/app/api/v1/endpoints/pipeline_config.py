# ABOUTME: API endpoints for pipeline configuration and management
# ABOUTME: Handles CRUD operations for pipelines, scripts, and execution control

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlmodel import Session, select
import uuid
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.models import User, Study
from app.models.pipeline import (
    PipelineConfig, PipelineConfigCreate, PipelineConfigUpdate,
    PipelineExecution, PipelineExecuteRequest, PipelineExecutionResponse,
    TransformationScript, TransformationScriptCreate,
    PipelineStatus, TransformationType
)
from app.core.permissions import Permission, require_permission
from app.clinical_modules.pipeline.pipeline_service import PipelineService, execute_pipeline_task
from app.crud import activity_log as crud_activity

router = APIRouter()

# Pipeline Configuration Endpoints
@router.get("/studies/{study_id}/pipelines", response_model=List[Dict[str, Any]])
async def list_study_pipelines(
    study_id: uuid.UUID,
    include_inactive: bool = Query(False, description="Include inactive pipelines"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List all pipelines for a study"""
    # Check permission
    await require_permission(current_user, Permission.VIEW_PIPELINE_LOGS, db)
    
    # Verify study access
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Query pipelines
    query = select(PipelineConfig).where(
        PipelineConfig.study_id == study_id,
        PipelineConfig.is_current_version == True
    )
    
    if not include_inactive:
        query = query.where(PipelineConfig.is_active == True)
    
    pipelines = db.exec(query).all()
    
    # Format response
    return [{
        'id': str(p.id),
        'name': p.name,
        'description': p.description,
        'version': p.version,
        'is_active': p.is_active,
        'schedule_cron': p.schedule_cron,
        'created_at': p.created_at.isoformat(),
        'last_execution': None,  # TODO: Get last execution
        'transformation_steps': len(p.transformation_steps)
    } for p in pipelines]

@router.post("/studies/{study_id}/pipelines", response_model=Dict[str, Any])
async def create_pipeline(
    study_id: uuid.UUID,
    pipeline_data: PipelineConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new pipeline configuration"""
    # Check permission
    await require_permission(current_user, Permission.CONFIGURE_PIPELINE, db)
    
    # Verify study access
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create pipeline
    service = PipelineService(db)
    pipeline_dict = pipeline_data.model_dump()
    pipeline_dict['study_id'] = study_id
    
    pipeline = service.create_pipeline_config(pipeline_dict, current_user)
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="create_pipeline",
        resource_type="pipeline",
        resource_id=str(pipeline.id),
        details={"pipeline_name": pipeline.name}
    )
    
    return {
        'id': str(pipeline.id),
        'name': pipeline.name,
        'version': pipeline.version,
        'message': 'Pipeline created successfully'
    }

@router.get("/pipelines/{pipeline_id}", response_model=Dict[str, Any])
async def get_pipeline_details(
    pipeline_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get detailed pipeline configuration"""
    # Check permission
    await require_permission(current_user, Permission.VIEW_PIPELINE_LOGS, db)
    
    # Get pipeline
    pipeline = db.get(PipelineConfig, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Verify access
    study = db.get(Study, pipeline.study_id)
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get transformation scripts
    scripts = db.exec(
        select(TransformationScript)
        .where(TransformationScript.pipeline_config_id == pipeline_id)
        .where(TransformationScript.is_current_version == True)
    ).all()
    
    return {
        'id': str(pipeline.id),
        'name': pipeline.name,
        'description': pipeline.description,
        'version': pipeline.version,
        'is_active': pipeline.is_active,
        'is_current_version': pipeline.is_current_version,
        'schedule_cron': pipeline.schedule_cron,
        'retry_on_failure': pipeline.retry_on_failure,
        'max_retries': pipeline.max_retries,
        'timeout_seconds': pipeline.timeout_seconds,
        'source_config': pipeline.source_config,
        'transformation_steps': pipeline.transformation_steps,
        'output_config': pipeline.output_config,
        'transformation_scripts': [{
            'id': str(s.id),
            'name': s.name,
            'script_type': s.script_type,
            'is_validated': s.is_validated
        } for s in scripts],
        'created_at': pipeline.created_at.isoformat(),
        'created_by': str(pipeline.created_by)
    }

@router.put("/pipelines/{pipeline_id}", response_model=Dict[str, Any])
async def update_pipeline(
    pipeline_id: uuid.UUID,
    update_data: PipelineConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update pipeline configuration (creates new version)"""
    # Check permission
    await require_permission(current_user, Permission.CONFIGURE_PIPELINE, db)
    
    # Get current pipeline
    pipeline = db.get(PipelineConfig, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Verify access
    study = db.get(Study, pipeline.study_id)
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create new version with updates
    service = PipelineService(db)
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Merge with existing config
    config_data = {
        'name': update_dict.get('name', pipeline.name),
        'description': update_dict.get('description', pipeline.description),
        'study_id': pipeline.study_id,
        'is_active': update_dict.get('is_active', pipeline.is_active),
        'schedule_cron': update_dict.get('schedule_cron', pipeline.schedule_cron),
        'retry_on_failure': update_dict.get('retry_on_failure', pipeline.retry_on_failure),
        'max_retries': update_dict.get('max_retries', pipeline.max_retries),
        'timeout_seconds': update_dict.get('timeout_seconds', pipeline.timeout_seconds),
        'source_config': update_dict.get('source_config', pipeline.source_config),
        'transformation_steps': update_dict.get('transformation_steps', pipeline.transformation_steps),
        'output_config': update_dict.get('output_config', pipeline.output_config)
    }
    
    new_pipeline = service.create_pipeline_config(config_data, current_user)
    
    return {
        'id': str(new_pipeline.id),
        'name': new_pipeline.name,
        'version': new_pipeline.version,
        'message': 'Pipeline updated successfully (new version created)'
    }

@router.get("/pipelines/{pipeline_id}/versions", response_model=List[Dict[str, Any]])
async def get_pipeline_versions(
    pipeline_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all versions of a pipeline"""
    # Check permission
    await require_permission(current_user, Permission.VIEW_PIPELINE_LOGS, db)
    
    # Get versions
    service = PipelineService(db)
    versions = service.get_pipeline_versions(pipeline_id)
    
    if not versions:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Verify access
    study = db.get(Study, versions[0].study_id)
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return [{
        'id': str(v.id),
        'version': v.version,
        'is_current': v.is_current_version,
        'created_at': v.created_at.isoformat(),
        'created_by': str(v.created_by),
        'description': v.description
    } for v in versions]

@router.post("/pipelines/{pipeline_id}/rollback/{version}", response_model=Dict[str, Any])
async def rollback_pipeline_version(
    pipeline_id: uuid.UUID,
    version: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Rollback to a specific pipeline version"""
    # Check permission
    await require_permission(current_user, Permission.CONFIGURE_PIPELINE, db)
    
    # Rollback
    service = PipelineService(db)
    try:
        new_pipeline = service.rollback_pipeline_version(pipeline_id, version, current_user)
        
        return {
            'id': str(new_pipeline.id),
            'version': new_pipeline.version,
            'message': f'Successfully rolled back to version {version}'
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Transformation Script Endpoints
@router.post("/pipelines/{pipeline_id}/scripts", response_model=Dict[str, Any])
async def create_transformation_script(
    pipeline_id: uuid.UUID,
    script_data: TransformationScriptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a transformation script for a pipeline"""
    # Check permission
    await require_permission(current_user, Permission.CONFIGURE_PIPELINE, db)
    
    # Verify pipeline exists and access
    pipeline = db.get(PipelineConfig, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    study = db.get(Study, pipeline.study_id)
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create script
    service = PipelineService(db)
    script_dict = script_data.model_dump()
    script_dict['pipeline_config_id'] = pipeline_id
    
    script = service.create_transformation_script(script_dict, current_user)
    
    return {
        'id': str(script.id),
        'name': script.name,
        'is_validated': script.is_validated,
        'validation_errors': script.validation_errors,
        'message': 'Script created successfully'
    }

@router.post("/scripts/validate", response_model=Dict[str, Any])
async def validate_script(
    script_content: str = Body(...),
    script_type: TransformationType = Body(...),
    allowed_imports: Optional[List[str]] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Validate a transformation script without saving"""
    # Check permission
    await require_permission(current_user, Permission.CONFIGURE_PIPELINE, db)
    
    # Validate
    service = PipelineService(db)
    is_valid, errors = service.validate_transformation_script(
        script_content, script_type, allowed_imports
    )
    
    return {
        'is_valid': is_valid,
        'errors': errors,
        'message': 'Script is valid' if is_valid else 'Script validation failed'
    }

# Pipeline Execution Endpoints
@router.post("/pipelines/execute", response_model=PipelineExecutionResponse)
async def execute_pipeline(
    request: PipelineExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Execute a pipeline"""
    # Check permission
    await require_permission(current_user, Permission.EXECUTE_PIPELINE, db)
    
    # Get pipeline
    pipeline = db.get(PipelineConfig, request.pipeline_config_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Verify access
    study = db.get(Study, pipeline.study_id)
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create execution record
    execution = PipelineExecution(
        pipeline_config_id=request.pipeline_config_id,
        data_version_id=request.data_version_id,
        triggered_by=request.triggered_by,
        status=PipelineStatus.PENDING,
        created_at=datetime.utcnow(),
        created_by=current_user.id
    )
    
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # Start async execution
    task = execute_pipeline_task.delay(str(execution.id), str(db.get_bind().url))
    
    # Update with task ID
    execution.task_id = task.id
    db.add(execution)
    db.commit()
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="execute_pipeline",
        resource_type="pipeline_execution",
        resource_id=str(execution.id),
        details={"pipeline_name": pipeline.name}
    )
    
    return PipelineExecutionResponse(
        execution_id=execution.id,
        task_id=task.id,
        status=PipelineStatus.PENDING,
        message="Pipeline execution started",
        estimated_duration_seconds=pipeline.timeout_seconds
    )

@router.get("/executions/{execution_id}", response_model=Dict[str, Any])
async def get_execution_details(
    execution_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get pipeline execution details"""
    # Check permission
    await require_permission(current_user, Permission.VIEW_PIPELINE_LOGS, db)
    
    # Get execution
    execution = db.get(PipelineExecution, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    # Verify access
    pipeline = execution.config
    study = db.get(Study, pipeline.study_id)
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get execution steps
    steps = db.exec(
        select(PipelineExecutionStep)
        .where(PipelineExecutionStep.execution_id == execution_id)
        .order_by(PipelineExecutionStep.step_index)
    ).all()
    
    return {
        'id': str(execution.id),
        'pipeline_name': pipeline.name,
        'pipeline_version': pipeline.version,
        'status': execution.status,
        'triggered_by': execution.triggered_by,
        'started_at': execution.started_at.isoformat() if execution.started_at else None,
        'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
        'duration_seconds': execution.duration_seconds,
        'input_records': execution.input_records,
        'output_records': execution.output_records,
        'records_failed': execution.records_failed,
        'error_message': execution.error_message,
        'output_path': execution.output_path,
        'execution_steps': [{
            'step_name': s.step_name,
            'step_type': s.step_type,
            'status': s.status,
            'duration_seconds': s.duration_seconds,
            'input_records': s.input_records,
            'output_records': s.output_records,
            'error_message': s.error_message
        } for s in steps],
        'execution_log': execution.execution_log
    }

@router.get("/pipelines/{pipeline_id}/executions", response_model=List[Dict[str, Any]])
async def list_pipeline_executions(
    pipeline_id: uuid.UUID,
    status: Optional[PipelineStatus] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List executions for a pipeline"""
    # Check permission
    await require_permission(current_user, Permission.VIEW_PIPELINE_LOGS, db)
    
    # Get pipeline
    pipeline = db.get(PipelineConfig, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Verify access
    study = db.get(Study, pipeline.study_id)
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Query executions
    query = select(PipelineExecution).where(
        PipelineExecution.pipeline_config_id == pipeline_id
    )
    
    if status:
        query = query.where(PipelineExecution.status == status)
    
    query = query.order_by(PipelineExecution.created_at.desc())
    query = query.offset(offset).limit(limit)
    
    executions = db.exec(query).all()
    
    return [{
        'id': str(e.id),
        'status': e.status,
        'triggered_by': e.triggered_by,
        'started_at': e.started_at.isoformat() if e.started_at else None,
        'completed_at': e.completed_at.isoformat() if e.completed_at else None,
        'duration_seconds': e.duration_seconds,
        'output_records': e.output_records,
        'error_message': e.error_message
    } for e in executions]