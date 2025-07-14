# ABOUTME: Celery tasks for study initialization
# ABOUTME: Handles background processing of study initialization steps

import logging
import uuid
from typing import List, Dict, Any

from celery import current_task
from sqlmodel import Session

from app.core.celery_app import celery_app
from app.core.db import engine
from app.models import Study, User
from app.services.study_initialization_service import StudyInitializationService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.study_initialization.initialize_study_task")
def initialize_study_task(
    self,
    study_id: str,
    template_id: str,
    user_id: str,
    skip_data_upload: bool = False,
    is_retry: bool = False
):
    """
    Background task to initialize a study
    
    Args:
        study_id: The study UUID as string
        template_id: The template UUID as string
        user_id: The user UUID as string
        skip_data_upload: Whether to skip data upload step
        is_retry: Whether this is a retry attempt
    """
    logger.info(f"Starting study initialization task for study {study_id}")
    
    with Session(engine) as db:
        try:
            # Get study and user
            study = db.get(Study, uuid.UUID(study_id))
            if not study:
                logger.error(f"Study {study_id} not found")
                return {"error": "Study not found"}
            
            user = db.get(User, uuid.UUID(user_id))
            if not user:
                logger.error(f"User {user_id} not found")
                return {"error": "User not found"}
            
            # Get uploaded files if any
            uploaded_files = []
            if not skip_data_upload:
                uploaded_files = study.metadata.get("pending_uploads", []) if study.metadata else []
            
            # Create service and run initialization
            service = StudyInitializationService(db)
            
            # Run async initialization in sync context
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    service.initialize_study(
                        study_id=uuid.UUID(study_id),
                        template_id=uuid.UUID(template_id),
                        uploaded_files=uploaded_files,
                        current_user=user
                    )
                )
                
                logger.info(f"Study initialization completed for {study_id}")
                
                return {
                    "status": "completed",
                    "study_id": study_id,
                    "template_id": template_id,
                    "activated_at": result.activated_at.isoformat() if result.activated_at else None
                }
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Study initialization failed for {study_id}: {str(e)}")
            
            # Update study status to failed
            if study:
                study.initialization_status = "failed"
                study.initialization_steps["error"] = str(e)
                study.initialization_steps["failed_at"] = datetime.utcnow().isoformat()
                db.add(study)
                db.commit()
            
            raise


@celery_app.task(name="app.tasks.study_initialization.cleanup_failed_initializations")
def cleanup_failed_initializations():
    """
    Periodic task to cleanup failed or stuck initializations
    """
    logger.info("Running cleanup for failed initializations")
    
    with Session(engine) as db:
        from datetime import datetime, timedelta
        
        # Find stuck initializations (older than 1 hour)
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        stuck_studies = db.query(Study).filter(
            Study.initialization_status.in_(["pending", "initializing"]),
            Study.updated_at < cutoff_time
        ).all()
        
        for study in stuck_studies:
            logger.warning(f"Marking stuck initialization as failed for study {study.id}")
            study.initialization_status = "failed"
            study.initialization_steps["error"] = "Initialization timed out"
            study.initialization_steps["timeout_at"] = datetime.utcnow().isoformat()
            db.add(study)
        
        db.commit()
        
        return {
            "cleaned_up": len(stuck_studies),
            "study_ids": [str(s.id) for s in stuck_studies]
        }


# Import datetime for the task
from datetime import datetime