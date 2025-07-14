# ABOUTME: API endpoints for study initialization with real-time progress
# ABOUTME: Handles template application, data upload, and field mapping orchestration

import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlmodel import Session
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models import User, Study
from app.services.study_initialization_service import StudyInitializationService
from app.core.permissions import has_permission, Permission
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter()


class StudyInitializeRequest(BaseModel):
    """Request model for study initialization"""
    template_id: uuid.UUID
    skip_data_upload: bool = False


class StudyInitializeResponse(BaseModel):
    """Response model for study initialization"""
    study_id: uuid.UUID
    initialization_status: str
    task_id: Optional[str] = None
    websocket_url: str


class InitializationStatusResponse(BaseModel):
    """Response model for initialization status"""
    study_id: uuid.UUID
    initialization_status: str
    initialization_progress: int
    initialization_steps: Dict[str, Any]
    template_applied_at: Optional[datetime]
    data_uploaded_at: Optional[datetime]
    mappings_configured_at: Optional[datetime]
    activated_at: Optional[datetime]


@router.post("/studies/{study_id}/initialize", response_model=StudyInitializeResponse)
async def initialize_study(
    study_id: uuid.UUID,
    request: StudyInitializeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initialize a study with template and optional data upload
    
    This endpoint starts the study initialization process which includes:
    1. Applying the selected dashboard template
    2. Processing uploaded data files (if provided)
    3. Converting data to parquet format
    4. Automatically mapping fields based on widget requirements
    
    Progress updates are sent via WebSocket connection.
    """
    # Check permissions
    if not has_permission(current_user, Permission.EDIT_STUDY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to initialize study"
        )
    
    # Get study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check organization access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this study"
        )
    
    # Check if already initialized
    if study.initialization_status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Study is already initialized"
        )
    
    # Start initialization in background
    task = celery_app.send_task(
        "app.tasks.study_initialization.initialize_study_task",
        args=[str(study_id), str(request.template_id), str(current_user.id)],
        kwargs={"skip_data_upload": request.skip_data_upload}
    )
    
    # Update study status
    study.initialization_status = "pending"
    study.initialization_progress = 0
    study.initialization_steps = {
        "task_id": task.id,
        "started_at": datetime.utcnow().isoformat(),
        "initiated_by": str(current_user.id)
    }
    db.add(study)
    db.commit()
    
    return StudyInitializeResponse(
        study_id=study_id,
        initialization_status="pending",
        task_id=task.id,
        websocket_url=f"/ws/studies/{study_id}/initialization"
    )


@router.post("/studies/{study_id}/initialize/upload")
async def upload_study_data(
    study_id: uuid.UUID,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload data files for study initialization
    
    Accepts multiple files in various formats:
    - CSV files
    - SAS7BDAT files
    - XPT (SAS Transport) files
    - Excel files (XLSX, XLS)
    - ZIP archives containing any of the above
    """
    # Check permissions
    if not has_permission(current_user, Permission.STUDY_UPLOAD):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to upload study data"
        )
    
    # Get study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check organization access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this study"
        )
    
    # Create upload directory
    upload_dir = Path(f"/data/studies/{study_id}/uploads/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    uploaded_files = []
    
    for file in files:
        try:
            # Save file
            file_path = upload_dir / file.filename
            content = await file.read()
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Determine file type
            file_extension = Path(file.filename).suffix.lower()
            file_type = "unknown"
            
            if file_extension == ".zip":
                file_type = "zip"
            elif file_extension == ".csv":
                file_type = "csv"
            elif file_extension in [".sas7bdat", ".xpt"]:
                file_type = "sas"
            elif file_extension in [".xlsx", ".xls"]:
                file_type = "excel"
            
            uploaded_files.append({
                "name": file.filename,
                "path": str(file_path),
                "size": len(content),
                "type": file_type,
                "uploaded_at": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to save uploaded file {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file {file.filename}"
            )
    
    # Store upload info in study metadata
    if not study.metadata:
        study.metadata = {}
    
    study.metadata["pending_uploads"] = uploaded_files
    db.add(study)
    db.commit()
    
    return {
        "message": "Files uploaded successfully",
        "files": uploaded_files,
        "total_files": len(uploaded_files)
    }


@router.get("/studies/{study_id}/initialization/status", response_model=InitializationStatusResponse)
async def get_initialization_status(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current initialization status for a study"""
    # Check permissions
    if not has_permission(current_user, Permission.VIEW_STUDY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view study"
        )
    
    # Get study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check organization access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this study"
        )
    
    return InitializationStatusResponse(
        study_id=study_id,
        initialization_status=study.initialization_status or "not_started",
        initialization_progress=study.initialization_progress or 0,
        initialization_steps=study.initialization_steps or {},
        template_applied_at=study.template_applied_at,
        data_uploaded_at=study.data_uploaded_at,
        mappings_configured_at=study.mappings_configured_at,
        activated_at=study.activated_at
    )


@router.post("/studies/{study_id}/initialization/retry")
async def retry_initialization(
    study_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retry failed initialization"""
    # Check permissions
    if not has_permission(current_user, Permission.EDIT_STUDY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to initialize study"
        )
    
    # Get study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check organization access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this study"
        )
    
    # Check if can retry
    if study.initialization_status not in ["failed", "error"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only retry failed initializations"
        )
    
    # Get template ID from previous attempt
    template_id = study.dashboard_template_id
    if not template_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No template found from previous initialization"
        )
    
    # Start retry in background
    task = celery_app.send_task(
        "app.tasks.study_initialization.initialize_study_task",
        args=[str(study_id), str(template_id), str(current_user.id)],
        kwargs={"is_retry": True}
    )
    
    # Update study status
    study.initialization_status = "pending"
    study.initialization_progress = 0
    study.initialization_steps["retry_task_id"] = task.id
    study.initialization_steps["retried_at"] = datetime.utcnow().isoformat()
    db.add(study)
    db.commit()
    
    return {
        "message": "Initialization retry started",
        "task_id": task.id,
        "websocket_url": f"/ws/studies/{study_id}/initialization"
    }


@router.delete("/studies/{study_id}/initialization")
async def cancel_initialization(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel ongoing initialization"""
    # Check permissions
    if not has_permission(current_user, Permission.EDIT_STUDY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to manage study"
        )
    
    # Get study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check organization access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this study"
        )
    
    # Check if can cancel
    if study.initialization_status not in ["pending", "initializing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active initialization to cancel"
        )
    
    # Cancel task if exists
    task_id = study.initialization_steps.get("task_id")
    if task_id:
        celery_app.control.revoke(task_id, terminate=True)
    
    # Update status
    study.initialization_status = "cancelled"
    study.initialization_steps["cancelled_at"] = datetime.utcnow().isoformat()
    study.initialization_steps["cancelled_by"] = str(current_user.id)
    db.add(study)
    db.commit()
    
    return {
        "message": "Initialization cancelled",
        "study_id": study_id
    }