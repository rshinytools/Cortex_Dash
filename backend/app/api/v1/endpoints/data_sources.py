# ABOUTME: API endpoints for data source management
# ABOUTME: Handles data source configuration, testing, and synchronization

from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File, Form
from sqlmodel import Session, select
from datetime import datetime
import uuid
import os
import zipfile
import shutil
from pathlib import Path

from app.api.deps import get_db, get_current_user
from app.models import (
    User, DataSource, DataSourceCreate, DataSourceUpdate, DataSourceConfig,
    Study, Message, DataSourceType
)
from app.core.permissions import Permission, require_permission
# TODO: Implement these connectors
# from app.clinical_modules.data_sources.medidata_rave import MedidataRaveConnector
# from app.clinical_modules.data_sources.sftp import SFTPConnector
# from app.clinical_modules.data_sources.manual_upload import ManualUploadHandler
from app.core.celery_app import celery_app

router = APIRouter()


@router.get("/types", response_model=List[Dict[str, Any]])
async def get_data_source_types(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get list of supported data source types and their configuration schemas.
    """
    return [
        {
            "type": DataSourceType.MEDIDATA_API,
            "name": "Medidata Rave",
            "description": "Connect to Medidata Rave EDC system",
            "config_schema": {
                "base_url": {"type": "string", "required": True},
                "username": {"type": "string", "required": True},
                "password": {"type": "string", "required": True, "secret": True},
                "study_oid": {"type": "string", "required": True}
            }
        },
        {
            "type": DataSourceType.SFTP,
            "name": "SFTP Server",
            "description": "Connect to SFTP server for file transfers",
            "config_schema": {
                "host": {"type": "string", "required": True},
                "port": {"type": "integer", "default": 22},
                "username": {"type": "string", "required": True},
                "password": {"type": "string", "required": False, "secret": True},
                "private_key": {"type": "string", "required": False, "secret": True},
                "remote_path": {"type": "string", "required": True}
            }
        },
        {
            "type": DataSourceType.ZIP_UPLOAD,
            "name": "ZIP File Upload",
            "description": "Manual file uploads via web interface",
            "config_schema": {
                "allowed_extensions": {"type": "array", "default": [".sas7bdat", ".xpt", ".csv", ".xlsx"]}
            }
        }
    ]


@router.post("/test-connection", response_model=Dict[str, Any])
async def test_data_source_connection(
    data_source_config: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.MANAGE_STUDY_DATA))
) -> Any:
    """
    Test connection to a data source without saving configuration.
    """
    source_type = data_source_config.get("type")
    config = data_source_config.get("config", {})
    
    if not source_type:
        raise HTTPException(status_code=400, detail="Data source type is required")
    
    try:
        if source_type == DataSourceType.MEDIDATA_API:
            connector = MedidataRaveConnector(config)
            success, message = await connector.test_connection()
        elif source_type == DataSourceType.SFTP:
            connector = SFTPConnector(config)
            success, message = await connector.test_connection()
        elif source_type == DataSourceType.ZIP_UPLOAD:
            # Manual upload doesn't need connection testing
            success, message = True, "Manual upload ready"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported data source type: {source_type}")
        
        return {
            "success": success,
            "message": message,
            "tested_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "tested_at": datetime.utcnow().isoformat()
        }


@router.get("/studies/{study_id}/data-sources", response_model=List[DataSource])
async def get_study_data_sources(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Get all data sources configured for a study.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Check if user has access to this study
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get data sources
    data_sources = db.exec(
        select(DataSource).where(DataSource.study_id == study_id)
    ).all()
    
    return data_sources


@router.post("/studies/{study_id}/data-sources", response_model=DataSource)
async def create_study_data_source(
    study_id: uuid.UUID,
    data_source_in: DataSourceCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.MANAGE_STUDY_DATA))
) -> Any:
    """
    Create a new data source for a study.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create data source
    data_source = DataSource(
        study_id=study_id,
        name=data_source_in.name,
        source_type=data_source_in.source_type,
        config=data_source_in.config.dict() if isinstance(data_source_in.config, DataSourceConfig) else data_source_in.config,
        active=data_source_in.active,
        sync_schedule=data_source_in.sync_schedule,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    db.add(data_source)
    db.commit()
    db.refresh(data_source)
    
    # Schedule initial sync if requested
    if data_source_in.sync_on_create:
        background_tasks.add_task(
            trigger_data_source_sync,
            data_source.id,
            current_user.id
        )
    
    return data_source


@router.get("/studies/{study_id}/data-sources/{ds_id}", response_model=DataSource)
async def get_data_source(
    study_id: uuid.UUID,
    ds_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_STUDY))
) -> Any:
    """
    Get specific data source details.
    """
    data_source = db.exec(
        select(DataSource).where(
            DataSource.id == ds_id,
            DataSource.study_id == study_id
        )
    ).first()
    
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    # Check access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return data_source


@router.put("/studies/{study_id}/data-sources/{ds_id}", response_model=DataSource)
async def update_data_source(
    study_id: uuid.UUID,
    ds_id: uuid.UUID,
    data_source_update: DataSourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.MANAGE_STUDY_DATA))
) -> Any:
    """
    Update data source configuration.
    """
    data_source = db.exec(
        select(DataSource).where(
            DataSource.id == ds_id,
            DataSource.study_id == study_id
        )
    ).first()
    
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    # Check access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update fields
    update_data = data_source_update.dict(exclude_unset=True)
    if "config" in update_data and isinstance(update_data["config"], DataSourceConfig):
        update_data["config"] = update_data["config"].dict()
    
    for field, value in update_data.items():
        setattr(data_source, field, value)
    
    data_source.updated_by = current_user.id
    data_source.updated_at = datetime.utcnow()
    
    db.add(data_source)
    db.commit()
    db.refresh(data_source)
    
    return data_source


@router.delete("/studies/{study_id}/data-sources/{ds_id}")
async def delete_data_source(
    study_id: uuid.UUID,
    ds_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.MANAGE_STUDY_DATA))
) -> Any:
    """
    Delete a data source.
    """
    data_source = db.exec(
        select(DataSource).where(
            DataSource.id == ds_id,
            DataSource.study_id == study_id
        )
    ).first()
    
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    # Check access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(data_source)
    db.commit()
    
    return Message(message="Data source deleted successfully")


@router.post("/studies/{study_id}/data-sources/{ds_id}/sync")
async def sync_data_source(
    study_id: uuid.UUID,
    ds_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.EXECUTE_PIPELINE))
) -> Any:
    """
    Trigger manual synchronization of a data source.
    """
    data_source = db.exec(
        select(DataSource).where(
            DataSource.id == ds_id,
            DataSource.study_id == study_id
        )
    ).first()
    
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    # Check access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Trigger sync task
    task = celery_app.send_task(
        "app.tasks.sync_data_source",
        args=[str(ds_id), str(current_user.id)]
    )
    
    return {
        "message": "Data source sync initiated",
        "task_id": task.id,
        "status": "pending"
    }


def trigger_data_source_sync(data_source_id: uuid.UUID, user_id: uuid.UUID):
    """
    Helper function to trigger data source sync in background.
    """
    celery_app.send_task(
        "app.tasks.sync_data_source",
        args=[str(data_source_id), str(user_id)]
    )


@router.post("/studies/{study_id}/data-sources/{ds_id}/upload")
async def upload_data_file(
    study_id: uuid.UUID,
    ds_id: uuid.UUID,
    file: UploadFile = File(...),
    password: str = Form(None),
    extract_date: str = Form(...),  # EDC Extract Date in DDMMMYYYY format
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.MANAGE_STUDY_DATA))
) -> Any:
    """
    Upload a ZIP file for manual data source.
    """
    # Verify data source exists and is manual upload type
    data_source = db.exec(
        select(DataSource).where(
            DataSource.id == ds_id,
            DataSource.study_id == study_id
        )
    ).first()
    
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    if data_source.source_type != DataSourceType.ZIP_UPLOAD:
        raise HTTPException(
            status_code=400, 
            detail="Upload is only supported for manual upload data sources"
        )
    
    # Verify study and access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
        
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate extract date format
    import re
    date_pattern = re.compile(r'^[0-9]{2}[A-Z]{3}[0-9]{4}$')
    if not date_pattern.match(extract_date):
        raise HTTPException(
            status_code=400, 
            detail="Invalid extract date format. Must be DDMMMYYYY (e.g., 05JUL2025)"
        )
    
    # Check file extension
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are accepted")
    
    # Check file size (500MB limit)
    if file.size > 500 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 500MB limit")
    
    # Create folder structure using extract date as subfolder
    base_path = Path("/data/studies") / str(study.org_id) / str(study_id)
    upload_path = base_path / "raw" / "uploads" / extract_date
    upload_path.mkdir(parents=True, exist_ok=True)
    
    # Use original filename (can have multiple uploads for same date)
    filename = file.filename
    file_path = upload_path / filename
    
    try:
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Test if ZIP is valid and potentially password protected
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # Try to list files - this will fail if password protected and no password given
            try:
                file_list = zip_ref.namelist()
                if password:
                    # If password provided but ZIP is not encrypted
                    raise HTTPException(
                        status_code=400, 
                        detail="Password provided but ZIP file is not encrypted"
                    )
            except RuntimeError as e:
                if "encrypted" in str(e).lower():
                    if not password:
                        os.remove(file_path)
                        raise HTTPException(
                            status_code=400, 
                            detail="ZIP file is password protected. Please provide password."
                        )
                    # Try with password
                    zip_ref.setpassword(password.encode())
                    try:
                        file_list = zip_ref.namelist()
                    except Exception:
                        os.remove(file_path)
                        raise HTTPException(
                            status_code=400, 
                            detail="Invalid password for ZIP file"
                        )
                else:
                    raise
        
        # Update data source with upload info
        if not data_source.config:
            data_source.config = {}
        
        data_source.config["last_upload"] = {
            "filename": filename,
            "original_filename": file.filename,
            "extract_date": extract_date,
            "uploaded_at": datetime.utcnow().isoformat(),
            "uploaded_by": current_user.email,
            "file_path": str(file_path),
            "file_size": file.size
        }
        data_source.last_sync = datetime.utcnow()
        data_source.updated_by = current_user.id
        data_source.updated_at = datetime.utcnow()
        
        db.add(data_source)
        db.commit()
        
        # TODO: Trigger data processing pipeline
        
        return {
            "message": "File uploaded successfully",
            "filename": filename,
            "extract_date": extract_date,
            "size": file.size,
            "uploaded_at": datetime.utcnow().isoformat(),
            "upload_path": str(upload_path)
        }
        
    except Exception as e:
        # Clean up file if something went wrong
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))