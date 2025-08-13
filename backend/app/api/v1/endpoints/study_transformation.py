# ABOUTME: API endpoints for study data transformation within the wizard workflow
# ABOUTME: Handles pipeline creation, execution, and monitoring for study initialization

import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel, Field
from celery.result import AsyncResult

from app.api.deps import get_db, get_current_user
from app.models import User, Study, StudyDataConfiguration, PipelineConfig, PipelineExecution, PipelineStatus
from app.core.permissions import has_permission, Permission
from app.core.celery_app import celery_app
from app.clinical_modules.pipeline.tasks import execute_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()


class TransformationPipelineConfig(BaseModel):
    """Configuration for a transformation pipeline"""
    name: str
    description: Optional[str] = None
    source_dataset: str  # Dataset name from study data
    transformation_type: str  # aggregation, filter, custom, etc.
    transformation_config: Dict[str, Any]
    output_dataset_name: str
    output_format: str = "parquet"


class CreatePipelinesRequest(BaseModel):
    """Request to create multiple transformation pipelines"""
    pipelines: List[TransformationPipelineConfig]
    auto_execute: bool = Field(default=False, description="Automatically execute after creation")


class PipelineCreationResponse(BaseModel):
    """Response after creating pipelines"""
    created_pipelines: List[Dict[str, Any]]
    total_created: int
    auto_execution_triggered: bool = False
    execution_task_ids: Optional[List[str]] = None


class ExecuteTransformationsRequest(BaseModel):
    """Request to execute transformation pipelines"""
    pipeline_ids: Optional[List[uuid.UUID]] = Field(
        default=None, 
        description="Specific pipeline IDs to execute. If None, executes all pending pipelines"
    )
    force_rerun: bool = Field(default=False, description="Force re-run even if already executed")


class TransformationStatusResponse(BaseModel):
    """Response for transformation execution status"""
    study_id: uuid.UUID
    total_pipelines: int
    pipelines: List[Dict[str, Any]]
    overall_progress: int
    overall_status: str
    has_errors: bool
    error_messages: Optional[List[str]] = None


class DerivedDatasetInfo(BaseModel):
    """Information about a derived dataset"""
    name: str
    source_dataset: str
    transformation_type: str
    created_at: datetime
    record_count: int
    file_size_mb: float
    file_path: str
    schema: Dict[str, str]


@router.post("/wizard/{study_id}/pipelines", response_model=PipelineCreationResponse)
async def create_transformation_pipelines(
    study_id: uuid.UUID,
    request: CreatePipelinesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create transformation pipelines for the study wizard"""
    # Get study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check wizard state
    wizard_state = study.initialization_steps.get("wizard_state", {})
    if wizard_state.get("current_step", 0) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create pipelines before completing data upload step"
        )
    
    # Get study data configuration
    study_data_config = db.exec(
        select(StudyDataConfiguration).where(
            StudyDataConfiguration.study_id == study_id
        )
    ).first()
    
    if not study_data_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data configuration found for study"
        )
    
    created_pipelines = []
    execution_task_ids = []
    
    # Create each pipeline configuration
    for pipeline_cfg in request.pipelines:
        # Validate source dataset exists
        if pipeline_cfg.source_dataset not in study_data_config.dataset_schemas:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Source dataset '{pipeline_cfg.source_dataset}' not found in study data"
            )
        
        # Build pipeline configuration
        source_config = {
            "type": "study_dataset",
            "dataset_name": pipeline_cfg.source_dataset,
            "study_id": str(study_id),
            "data_folder": study.initialization_steps.get("data_folder", "")
        }
        
        transformation_steps = [{
            "step_name": f"{pipeline_cfg.transformation_type}_step",
            "step_type": pipeline_cfg.transformation_type,
            "config": pipeline_cfg.transformation_config
        }]
        
        output_config = {
            "type": "derived_dataset",
            "dataset_name": pipeline_cfg.output_dataset_name,
            "format": pipeline_cfg.output_format,
            "folder": "derived_data",
            "compression": "snappy" if pipeline_cfg.output_format == "parquet" else None
        }
        
        # Create pipeline config in database
        pipeline_config = PipelineConfig(
            name=pipeline_cfg.name,
            description=pipeline_cfg.description,
            study_id=study_id,
            source_config=source_config,
            transformation_steps=transformation_steps,
            output_config=output_config,
            created_by=current_user.id,
            is_active=True
        )
        
        db.add(pipeline_config)
        db.commit()
        db.refresh(pipeline_config)
        
        created_pipelines.append({
            "id": str(pipeline_config.id),
            "name": pipeline_config.name,
            "source": pipeline_cfg.source_dataset,
            "output": pipeline_cfg.output_dataset_name,
            "transformation_type": pipeline_cfg.transformation_type
        })
        
        # Execute if requested
        if request.auto_execute:
            task = execute_pipeline.delay(
                str(study_id),
                {
                    "pipeline_id": str(pipeline_config.id),
                    "source_config": source_config,
                    "transformation_steps": transformation_steps,
                    "output_config": output_config
                },
                str(current_user.id)
            )
            execution_task_ids.append(task.id)
            
            # Create execution record
            execution = PipelineExecution(
                pipeline_config_id=pipeline_config.id,
                task_id=task.id,
                status=PipelineStatus.PENDING,
                triggered_by="wizard_auto",
                created_by=current_user.id
            )
            db.add(execution)
    
    # Update initialization steps
    if "transformation_pipelines" not in study.initialization_steps:
        study.initialization_steps["transformation_pipelines"] = []
    
    study.initialization_steps["transformation_pipelines"].extend(created_pipelines)
    
    db.add(study)
    db.commit()
    
    return PipelineCreationResponse(
        created_pipelines=created_pipelines,
        total_created=len(created_pipelines),
        auto_execution_triggered=request.auto_execute,
        execution_task_ids=execution_task_ids if request.auto_execute else None
    )


@router.post("/wizard/{study_id}/execute-transformations")
async def execute_transformations(
    study_id: uuid.UUID,
    request: ExecuteTransformationsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute transformation pipelines for the study"""
    # Get study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get pipelines to execute
    if request.pipeline_ids:
        pipelines = db.exec(
            select(PipelineConfig).where(
                PipelineConfig.study_id == study_id,
                PipelineConfig.id.in_(request.pipeline_ids),
                PipelineConfig.is_active == True
            )
        ).all()
    else:
        # Get all active pipelines for the study
        pipelines = db.exec(
            select(PipelineConfig).where(
                PipelineConfig.study_id == study_id,
                PipelineConfig.is_active == True,
                PipelineConfig.is_current_version == True
            )
        ).all()
    
    if not pipelines:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pipelines found to execute"
        )
    
    execution_tasks = []
    
    for pipeline in pipelines:
        # Check if already executed (unless force rerun)
        if not request.force_rerun:
            existing_execution = db.exec(
                select(PipelineExecution).where(
                    PipelineExecution.pipeline_config_id == pipeline.id,
                    PipelineExecution.status == PipelineStatus.SUCCESS.value
                )
            ).first()
            
            if existing_execution:
                logger.info(f"Pipeline {pipeline.id} already executed successfully, skipping")
                continue
        
        # Execute pipeline
        task = execute_pipeline.delay(
            str(study_id),
            {
                "pipeline_id": str(pipeline.id),
                "source_config": pipeline.source_config,
                "transformation_steps": pipeline.transformation_steps,
                "output_config": pipeline.output_config
            },
            str(current_user.id)
        )
        
        # Create execution record
        execution = PipelineExecution(
            pipeline_config_id=pipeline.id,
            task_id=task.id,
            status=PipelineStatus.PENDING,
            triggered_by="wizard_manual",
            created_by=current_user.id
        )
        db.add(execution)
        
        execution_tasks.append({
            "pipeline_id": str(pipeline.id),
            "pipeline_name": pipeline.name,
            "task_id": task.id,
            "status": "pending"
        })
    
    db.commit()
    
    # Update wizard state
    if "transformation_executions" not in study.initialization_steps:
        study.initialization_steps["transformation_executions"] = []
    
    study.initialization_steps["transformation_executions"].append({
        "executed_at": datetime.utcnow().isoformat(),
        "task_count": len(execution_tasks),
        "tasks": execution_tasks
    })
    
    db.add(study)
    db.commit()
    
    return {
        "message": f"Started execution of {len(execution_tasks)} pipelines",
        "executions": execution_tasks
    }


@router.get("/wizard/{study_id}/transformation-status", response_model=TransformationStatusResponse)
async def get_transformation_status(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get status of all transformation pipeline executions"""
    # Get study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get all pipelines and their latest executions
    pipelines = db.exec(
        select(PipelineConfig).where(
            PipelineConfig.study_id == study_id,
            PipelineConfig.is_current_version == True
        )
    ).all()
    
    pipeline_statuses = []
    total_progress = 0
    has_errors = False
    error_messages = []
    
    for pipeline in pipelines:
        # Get latest execution
        latest_execution = db.exec(
            select(PipelineExecution).where(
                PipelineExecution.pipeline_config_id == pipeline.id
            ).order_by(PipelineExecution.created_at.desc())
        ).first()
        
        if latest_execution:
            # Get task status from Celery
            task_status = {"state": "UNKNOWN", "info": {}}
            if latest_execution.task_id:
                try:
                    result = AsyncResult(latest_execution.task_id, app=celery_app)
                    task_status = {
                        "state": result.state,
                        "info": result.info if result.info else {}
                    }
                except Exception as e:
                    logger.error(f"Error getting task status: {str(e)}")
            
            # Calculate progress
            progress = 0
            if latest_execution.status == PipelineStatus.SUCCESS.value:
                progress = 100
            elif latest_execution.status == PipelineStatus.FAILED.value:
                progress = 0
                has_errors = True
                if latest_execution.error_message:
                    error_messages.append(f"{pipeline.name}: {latest_execution.error_message}")
            elif task_status["state"] == "PROGRESS":
                progress = task_status["info"].get("current", 0)
            elif latest_execution.status == PipelineStatus.RUNNING.value:
                progress = 50
            
            pipeline_statuses.append({
                "pipeline_id": str(pipeline.id),
                "pipeline_name": pipeline.name,
                "execution_id": str(latest_execution.id),
                "status": latest_execution.status,
                "task_status": task_status["state"],
                "progress": progress,
                "started_at": latest_execution.started_at.isoformat() if latest_execution.started_at else None,
                "completed_at": latest_execution.completed_at.isoformat() if latest_execution.completed_at else None,
                "error_message": latest_execution.error_message
            })
            
            total_progress += progress
        else:
            pipeline_statuses.append({
                "pipeline_id": str(pipeline.id),
                "pipeline_name": pipeline.name,
                "execution_id": None,
                "status": "not_started",
                "task_status": None,
                "progress": 0,
                "started_at": None,
                "completed_at": None,
                "error_message": None
            })
    
    # Calculate overall status
    if not pipeline_statuses:
        overall_status = "no_pipelines"
        overall_progress = 0
    else:
        overall_progress = int(total_progress / len(pipeline_statuses))
        
        if all(p["status"] == PipelineStatus.SUCCESS.value for p in pipeline_statuses):
            overall_status = "completed"
        elif any(p["status"] == PipelineStatus.FAILED.value for p in pipeline_statuses):
            overall_status = "failed"
        elif any(p["status"] in [PipelineStatus.RUNNING, PipelineStatus.PENDING] for p in pipeline_statuses):
            overall_status = "in_progress"
        elif all(p["status"] == "not_started" for p in pipeline_statuses):
            overall_status = "not_started"
        else:
            overall_status = "partial"
    
    return TransformationStatusResponse(
        study_id=study_id,
        total_pipelines=len(pipeline_statuses),
        pipelines=pipeline_statuses,
        overall_progress=overall_progress,
        overall_status=overall_status,
        has_errors=has_errors,
        error_messages=error_messages if error_messages else None
    )


@router.get("/wizard/{study_id}/derived-datasets", response_model=List[DerivedDatasetInfo])
async def get_derived_datasets(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of all derived datasets generated by transformations"""
    # Get study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get study data folder
    data_folder = study.initialization_steps.get("data_folder", "")
    if not data_folder:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Study data folder not configured"
        )
    
    from pathlib import Path
    import pyarrow.parquet as pq
    
    derived_datasets = []
    derived_data_path = Path(data_folder) / "derived_data"
    
    if derived_data_path.exists():
        # Get all successful pipeline executions
        successful_executions = db.exec(
            select(PipelineExecution).join(PipelineConfig).where(
                PipelineConfig.study_id == study_id,
                PipelineExecution.status == PipelineStatus.SUCCESS
            ).order_by(PipelineExecution.completed_at.desc())
        ).all()
        
        # Map output names to pipeline info
        output_to_pipeline = {}
        for execution in successful_executions:
            pipeline = db.get(PipelineConfig, execution.pipeline_config_id)
            if pipeline and pipeline.output_config:
                output_name = pipeline.output_config.get("dataset_name", "")
                if output_name:
                    output_to_pipeline[output_name] = {
                        "pipeline": pipeline,
                        "execution": execution
                    }
        
        # Scan for parquet files
        for file_path in derived_data_path.glob("*.parquet"):
            dataset_name = file_path.stem
            
            try:
                # Read parquet metadata
                parquet_file = pq.ParquetFile(file_path)
                metadata = parquet_file.metadata
                schema = parquet_file.schema
                
                # Get file info
                file_stat = file_path.stat()
                
                # Build schema dict
                schema_dict = {}
                for field in schema:
                    schema_dict[field.name] = str(field.type)
                
                # Get pipeline info if available
                pipeline_info = output_to_pipeline.get(dataset_name, {})
                pipeline = pipeline_info.get("pipeline")
                execution = pipeline_info.get("execution")
                
                derived_datasets.append(DerivedDatasetInfo(
                    name=dataset_name,
                    source_dataset=pipeline.source_config.get("dataset_name", "unknown") if pipeline else "unknown",
                    transformation_type=pipeline.transformation_steps[0].get("step_type", "unknown") if pipeline and pipeline.transformation_steps else "unknown",
                    created_at=execution.completed_at if execution and execution.completed_at else datetime.fromtimestamp(file_stat.st_mtime),
                    record_count=metadata.num_rows,
                    file_size_mb=round(file_stat.st_size / (1024 * 1024), 2),
                    file_path=str(file_path),
                    schema=schema_dict
                ))
            except Exception as e:
                logger.error(f"Error reading parquet file {file_path}: {str(e)}")
                continue
    
    # Sort by creation date
    derived_datasets.sort(key=lambda x: x.created_at, reverse=True)
    
    # Update study initialization steps with derived datasets info
    study.initialization_steps["derived_datasets"] = [
        {
            "name": ds.name,
            "source": ds.source_dataset,
            "type": ds.transformation_type,
            "created_at": ds.created_at.isoformat(),
            "record_count": ds.record_count,
            "file_size_mb": ds.file_size_mb
        }
        for ds in derived_datasets
    ]
    db.add(study)
    db.commit()
    
    return derived_datasets