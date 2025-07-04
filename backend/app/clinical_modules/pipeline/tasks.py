# ABOUTME: Celery tasks for asynchronous pipeline execution
# ABOUTME: Handles background processing of data pipelines

from celery import shared_task, current_task
from celery.result import AsyncResult
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from sqlmodel import Session, select
from app.core.db import engine
from app.models import Study, DataSource, User
from app.clinical_modules.pipeline.executor import PipelineExecutor


logger = logging.getLogger(__name__)


@shared_task(bind=True, name="app.clinical_modules.pipeline.tasks.execute_pipeline")
def execute_pipeline(
    self,
    study_id: str,
    pipeline_config: Dict[str, Any],
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Execute a data processing pipeline asynchronously
    
    Args:
        study_id: Study ID
        pipeline_config: Pipeline configuration
        user_id: Optional user ID for activity logging
        
    Returns:
        Pipeline execution results
    """
    try:
        with Session(engine) as db:
            # Get study
            study = db.get(Study, study_id)
            if not study:
                raise ValueError(f"Study not found: {study_id}")
            
            # Get user if provided
            user = None
            if user_id:
                user = db.get(User, user_id)
            
            # Create pipeline executor
            executor = PipelineExecutor(study, db, user, logger)
            
            # Define progress callback
            def update_progress(progress: int, message: str):
                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "current": progress,
                        "total": 100,
                        "status": message,
                        "pipeline_id": executor.pipeline_id
                    }
                )
            
            # Execute pipeline
            import asyncio
            results = asyncio.run(
                executor.execute(pipeline_config, update_progress)
            )
            
            return results
            
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        current_task.update_state(
            state="FAILURE",
            meta={
                "error": str(e),
                "exc_type": type(e).__name__
            }
        )
        raise


@shared_task(name="app.clinical_modules.pipeline.tasks.check_scheduled_pipelines")
def check_scheduled_pipelines() -> Dict[str, Any]:
    """Check for scheduled pipelines that need to run"""
    results = {
        "checked_at": datetime.utcnow().isoformat(),
        "pipelines_triggered": []
    }
    
    try:
        with Session(engine) as db:
            # Get all active studies with scheduled pipelines
            studies = db.exec(
                select(Study).where(
                    Study.status == "active",
                    Study.pipeline_config.is_not(None)
                )
            ).all()
            
            for study in studies:
                pipeline_config = study.pipeline_config or {}
                schedule = pipeline_config.get("schedule")
                
                if schedule and schedule.get("enabled"):
                    # Check if it's time to run
                    last_run = schedule.get("last_run")
                    frequency = schedule.get("frequency", "daily")
                    
                    should_run = False
                    
                    if not last_run:
                        should_run = True
                    else:
                        last_run_time = datetime.fromisoformat(last_run)
                        
                        if frequency == "hourly":
                            should_run = datetime.utcnow() - last_run_time > timedelta(hours=1)
                        elif frequency == "daily":
                            should_run = datetime.utcnow() - last_run_time > timedelta(days=1)
                        elif frequency == "weekly":
                            should_run = datetime.utcnow() - last_run_time > timedelta(weeks=1)
                    
                    if should_run:
                        # Trigger pipeline execution
                        task = execute_pipeline.delay(
                            str(study.id),
                            pipeline_config
                        )
                        
                        # Update last run time
                        schedule["last_run"] = datetime.utcnow().isoformat()
                        study.pipeline_config = pipeline_config
                        db.add(study)
                        db.commit()
                        
                        results["pipelines_triggered"].append({
                            "study_id": str(study.id),
                            "study_name": study.name,
                            "task_id": task.id
                        })
            
    except Exception as e:
        logger.error(f"Error checking scheduled pipelines: {str(e)}")
        results["error"] = str(e)
    
    return results


@shared_task(name="app.clinical_modules.pipeline.tasks.cleanup_temp_files")
def cleanup_temp_files() -> Dict[str, Any]:
    """Clean up temporary files from pipeline executions"""
    results = {
        "cleaned_at": datetime.utcnow().isoformat(),
        "files_deleted": 0,
        "space_freed_mb": 0
    }
    
    try:
        from pathlib import Path
        
        with Session(engine) as db:
            studies = db.exec(select(Study)).all()
            
            for study in studies:
                if study.folder_path:
                    temp_path = Path(study.folder_path) / "temp"
                    
                    if temp_path.exists():
                        # Delete files older than 24 hours
                        cutoff_time = datetime.utcnow() - timedelta(days=1)
                        
                        for temp_file in temp_path.iterdir():
                            if temp_file.is_file():
                                file_time = datetime.fromtimestamp(temp_file.stat().st_mtime)
                                
                                if file_time < cutoff_time:
                                    file_size = temp_file.stat().st_size
                                    temp_file.unlink()
                                    results["files_deleted"] += 1
                                    results["space_freed_mb"] += file_size / (1024 * 1024)
    
    except Exception as e:
        logger.error(f"Error cleaning temp files: {str(e)}")
        results["error"] = str(e)
    
    return results


@shared_task(name="app.clinical_modules.pipeline.tasks.get_pipeline_status")
def get_pipeline_status(task_id: str) -> Dict[str, Any]:
    """Get status of a pipeline execution task"""
    try:
        result = AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "state": result.state,
            "info": result.info,
            "result": result.result if result.ready() else None,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None
        }
        
    except Exception as e:
        return {
            "task_id": task_id,
            "error": str(e)
        }