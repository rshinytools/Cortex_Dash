# ABOUTME: API endpoints for data source file uploads and parquet conversion
# ABOUTME: Handles file uploads, conversion tracking, and data source management

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, BackgroundTasks
from sqlmodel import Session, select
from datetime import datetime
import uuid
import os
import aiofiles
from pathlib import Path
import logging

from app.api.deps import get_db, get_current_user
from app.models import (
    User, Study, 
    DataSourceUpload, DataSourceUploadCreate, DataSourceUploadUpdate, 
    DataSourceUploadPublic, DataSourceUploadsPublic,
    UploadStatus, FileFormat, Message
)
from app.core.permissions import Permission, require_permission
from app.services.file_conversion_service import FileConversionService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/studies/{study_id}/uploads", response_model=DataSourceUploadPublic)
async def upload_data_source(
    study_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    upload_name: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Upload a data source file (ZIP, CSV, SAS7BDAT, XPT, etc.) for a study.
    
    The file will be:
    1. Uploaded to the raw storage location
    2. Processed in the background to extract and convert to parquet
    3. Made available for widget data mapping
    """
    await require_permission(current_user, Permission.STUDY_UPLOAD, db)
    
    # Verify study exists and user has access
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Validate file format
    file_extension = file.filename.split('.')[-1].lower()
    try:
        if file_extension == "sas7bdat":
            file_format = FileFormat.SAS7BDAT
        else:
            file_format = FileFormat(file_extension)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format: {file_extension}. Supported formats: {', '.join([f.value for f in FileFormat])}"
        )
    
    # Import the unified folder structure utility
    from app.clinical_modules.utils.folder_structure import get_study_data_path, ensure_folder_exists
    
    # Create unified upload directory structure
    base_path = get_study_data_path(
        org_id=study.org_id,
        study_id=study_id,
        timestamp=None  # Will generate current timestamp
    )
    raw_path = base_path / "raw"
    processed_path = base_path / "processed"
    
    raw_path.mkdir(parents=True, exist_ok=True)
    processed_path.mkdir(parents=True, exist_ok=True)
    
    # Save uploaded file
    file_path = raw_path / file.filename
    file_size_mb = 0
    
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
            file_size_mb = len(content) / (1024 * 1024)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")
    
    # Create upload record
    upload_data = DataSourceUploadCreate(
        study_id=study_id,
        upload_name=upload_name,
        description=description,
        status=UploadStatus.UPLOADED,
        original_filename=file.filename,
        file_format=file_format,
        file_size_mb=file_size_mb,
        raw_path=str(file_path),
        processed_path=str(processed_path),
        upload_metadata={
            "uploaded_by": current_user.email,
            "timestamp": timestamp
        }
    )
    
    upload = DataSourceUpload.model_validate(upload_data, update={"created_by": current_user.id})
    db.add(upload)
    db.commit()
    db.refresh(upload)
    
    # Queue background processing
    background_tasks.add_task(
        process_upload,
        upload_id=upload.id,
        db=db
    )
    
    return upload


@router.get("/studies/{study_id}/uploads", response_model=DataSourceUploadsPublic)
async def list_study_uploads(
    study_id: uuid.UUID,
    status: Optional[UploadStatus] = Query(None, description="Filter by upload status"),
    active_only: bool = Query(True, description="Show only active versions"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    List all data source uploads for a study.
    """
    # Verify study exists and user has access
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Build query
    query = select(DataSourceUpload).where(DataSourceUpload.study_id == study_id)
    
    if status:
        query = query.where(DataSourceUpload.status == status)
    
    if active_only:
        query = query.where(DataSourceUpload.is_active_version == True)
    
    # Order by upload timestamp descending
    query = query.order_by(DataSourceUpload.upload_timestamp.desc())
    
    # Execute query with pagination
    total_query = select(func.count()).select_from(DataSourceUpload).where(DataSourceUpload.study_id == study_id)
    if status:
        total_query = total_query.where(DataSourceUpload.status == status)
    if active_only:
        total_query = total_query.where(DataSourceUpload.is_active_version == True)
    
    total = db.exec(total_query).one()
    uploads = db.exec(query.offset(skip).limit(limit)).all()
    
    return DataSourceUploadsPublic(
        data=[DataSourceUploadPublic.model_validate(upload) for upload in uploads],
        count=total
    )


@router.get("/uploads/{upload_id}", response_model=DataSourceUploadPublic)
async def get_upload_details(
    upload_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get details of a specific upload.
    """
    upload = db.get(DataSourceUpload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Verify user has access to the study
    study = db.get(Study, upload.study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    return upload


@router.delete("/uploads/{upload_id}")
async def delete_upload(
    upload_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Delete an upload and its associated files.
    """
    await require_permission(current_user, Permission.STUDY_DELETE, db)
    
    upload = db.get(DataSourceUpload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Check if this is an active version
    if upload.is_active_version:
        # Find the previous version to activate
        previous = db.exec(
            select(DataSourceUpload)
            .where(DataSourceUpload.study_id == upload.study_id)
            .where(DataSourceUpload.version_number < upload.version_number)
            .order_by(DataSourceUpload.version_number.desc())
            .limit(1)
        ).first()
        
        if previous:
            previous.is_active_version = True
            db.add(previous)
    
    # Delete files
    try:
        if upload.raw_path and os.path.exists(upload.raw_path):
            # Delete the entire timestamp directory
            timestamp_dir = Path(upload.raw_path).parent.parent
            if timestamp_dir.exists():
                import shutil
                shutil.rmtree(timestamp_dir)
    except Exception as e:
        logger.error(f"Failed to delete files for upload {upload_id}: {str(e)}")
    
    # Delete database record
    db.delete(upload)
    db.commit()
    
    return {"message": "Upload deleted successfully"}


@router.post("/uploads/{upload_id}/reprocess")
async def reprocess_upload(
    upload_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Reprocess an upload to regenerate parquet files.
    """
    await require_permission(current_user, Permission.STUDY_UPLOAD, db)
    
    upload = db.get(DataSourceUpload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Reset processing status
    upload.status = UploadStatus.PROCESSING
    upload.processing_started_at = datetime.utcnow()
    upload.processing_completed_at = None
    upload.error_message = None
    upload.warnings = None
    db.add(upload)
    db.commit()
    
    # Queue background processing
    background_tasks.add_task(
        process_upload,
        upload_id=upload.id,
        db=db
    )
    
    return {"message": "Upload queued for reprocessing", "upload_id": str(upload_id)}


async def process_upload(upload_id: uuid.UUID, db: Session):
    """
    Background task to process an uploaded file.
    """
    try:
        upload = db.get(DataSourceUpload, upload_id)
        if not upload:
            logger.error(f"Upload {upload_id} not found for processing")
            return
        
        # Update status
        upload.status = UploadStatus.PROCESSING
        upload.processing_started_at = datetime.utcnow()
        db.add(upload)
        db.commit()
        
        # Initialize conversion service
        conversion_service = FileConversionService()
        
        # Process the file
        result = await conversion_service.process_upload(
            upload_id=upload.id,
            file_path=upload.raw_path,
            output_path=upload.processed_path,
            file_format=upload.file_format
        )
        
        # Update upload record with results
        upload.status = UploadStatus.COMPLETED if result.success else UploadStatus.FAILED
        upload.processing_completed_at = datetime.utcnow()
        upload.processing_duration_seconds = (
            upload.processing_completed_at - upload.processing_started_at
        ).total_seconds()
        
        if result.success:
            upload.files_extracted = result.files_extracted
            upload.total_rows = result.total_rows
            upload.total_columns = result.total_columns
        else:
            upload.error_message = result.error_message
        
        upload.warnings = result.warnings
        
        db.add(upload)
        db.commit()
        
        logger.info(f"Upload {upload_id} processing completed with status: {upload.status}")
        
    except Exception as e:
        logger.error(f"Failed to process upload {upload_id}: {str(e)}")
        
        # Update upload record with error
        try:
            upload = db.get(DataSourceUpload, upload_id)
            if upload:
                upload.status = UploadStatus.FAILED
                upload.error_message = str(e)
                upload.processing_completed_at = datetime.utcnow()
                db.add(upload)
                db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update upload status: {str(update_error)}")


# Import at the end to avoid circular imports
from sqlalchemy import func


# Version Management Endpoints

@router.post("/studies/{study_id}/uploads/{upload_id}/activate", response_model=Message)
async def activate_upload_version(
    study_id: uuid.UUID,
    upload_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Activate a specific upload version as the current active version.
    Deactivates all other versions for the study.
    """
    await require_permission(current_user, Permission.STUDY_UPLOAD, db)
    
    # Verify upload exists and belongs to study
    upload = db.exec(
        select(DataSourceUpload)
        .where(DataSourceUpload.id == upload_id)
        .where(DataSourceUpload.study_id == study_id)
    ).first()
    
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Check if already active
    if upload.is_active_version:
        return Message(message="Version is already active")
    
    # Deactivate all other versions
    db.exec(
        select(DataSourceUpload)
        .where(DataSourceUpload.study_id == study_id)
        .where(DataSourceUpload.is_active_version == True)
    ).all()
    
    for other_upload in db.exec(
        select(DataSourceUpload)
        .where(DataSourceUpload.study_id == study_id)
        .where(DataSourceUpload.is_active_version == True)
    ):
        other_upload.is_active_version = False
        db.add(other_upload)
    
    # Activate selected version
    upload.is_active_version = True
    db.add(upload)
    db.commit()
    
    return Message(message=f"Version {upload.version_number} activated successfully")


@router.get("/studies/{study_id}/uploads/active", response_model=DataSourceUploadPublic)
async def get_active_version(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get the currently active upload version for a study.
    """
    await require_permission(current_user, Permission.VIEW_STUDY, db)
    
    active_upload = db.exec(
        select(DataSourceUpload)
        .where(DataSourceUpload.study_id == study_id)
        .where(DataSourceUpload.is_active_version == True)
    ).first()
    
    if not active_upload:
        raise HTTPException(
            status_code=404, 
            detail="No active version found. Please upload data first."
        )
    
    return active_upload


@router.get("/studies/{study_id}/uploads/compare")
async def compare_upload_versions(
    study_id: uuid.UUID,
    version1_id: uuid.UUID = Query(..., description="First version ID"),
    version2_id: uuid.UUID = Query(..., description="Second version ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Compare two upload versions, returning detailed differences.
    """
    await require_permission(current_user, Permission.VIEW_STUDY, db)
    
    # Get both versions
    version1 = db.exec(
        select(DataSourceUpload)
        .where(DataSourceUpload.id == version1_id)
        .where(DataSourceUpload.study_id == study_id)
    ).first()
    
    version2 = db.exec(
        select(DataSourceUpload)
        .where(DataSourceUpload.id == version2_id)
        .where(DataSourceUpload.study_id == study_id)
    ).first()
    
    if not version1 or not version2:
        raise HTTPException(status_code=404, detail="One or both versions not found")
    
    # Build comparison data
    comparison = {
        "version1": {
            "id": str(version1.id),
            "version_number": version1.version_number,
            "upload_name": version1.upload_name,
            "upload_timestamp": version1.upload_timestamp.isoformat(),
            "file_count": len(version1.files_extracted or []),
            "total_rows": version1.total_rows or 0,
            "total_size_mb": version1.file_size_mb
        },
        "version2": {
            "id": str(version2.id),
            "version_number": version2.version_number,
            "upload_name": version2.upload_name,
            "upload_timestamp": version2.upload_timestamp.isoformat(),
            "file_count": len(version2.files_extracted or []),
            "total_rows": version2.total_rows or 0,
            "total_size_mb": version2.file_size_mb
        },
        "differences": {
            "file_count_change": len(version2.files_extracted or []) - len(version1.files_extracted or []),
            "row_count_change": (version2.total_rows or 0) - (version1.total_rows or 0),
            "size_change_mb": version2.file_size_mb - version1.file_size_mb
        },
        "dataset_comparison": []
    }
    
    # Compare datasets
    v1_files = {f["dataset_name"]: f for f in (version1.files_extracted or [])}
    v2_files = {f["dataset_name"]: f for f in (version2.files_extracted or [])}
    
    all_datasets = set(v1_files.keys()) | set(v2_files.keys())
    
    for dataset_name in sorted(all_datasets):
        v1_file = v1_files.get(dataset_name)
        v2_file = v2_files.get(dataset_name)
        
        dataset_comp = {
            "dataset_name": dataset_name,
            "status": "unchanged",
            "v1_rows": v1_file["rows"] if v1_file else None,
            "v2_rows": v2_file["rows"] if v2_file else None,
            "row_change": 0,
            "column_changes": []
        }
        
        if not v1_file:
            dataset_comp["status"] = "new"
            dataset_comp["row_change"] = v2_file["rows"] if v2_file else 0
        elif not v2_file:
            dataset_comp["status"] = "removed"
            dataset_comp["row_change"] = -(v1_file["rows"] if v1_file else 0)
        else:
            # Both versions have this dataset
            if v1_file["rows"] != v2_file["rows"]:
                dataset_comp["status"] = "modified"
                dataset_comp["row_change"] = v2_file["rows"] - v1_file["rows"]
            
            # Compare columns
            v1_cols = {col["name"]: col for col in (v1_file.get("column_info", []))}
            v2_cols = {col["name"]: col for col in (v2_file.get("column_info", []))}
            
            all_cols = set(v1_cols.keys()) | set(v2_cols.keys())
            
            for col_name in sorted(all_cols):
                v1_col = v1_cols.get(col_name)
                v2_col = v2_cols.get(col_name)
                
                if not v1_col:
                    dataset_comp["column_changes"].append({
                        "column_name": col_name,
                        "change_type": "added",
                        "v1_type": None,
                        "v2_type": v2_col["type"] if v2_col else None
                    })
                    if dataset_comp["status"] == "unchanged":
                        dataset_comp["status"] = "modified"
                elif not v2_col:
                    dataset_comp["column_changes"].append({
                        "column_name": col_name,
                        "change_type": "removed",
                        "v1_type": v1_col["type"] if v1_col else None,
                        "v2_type": None
                    })
                    if dataset_comp["status"] == "unchanged":
                        dataset_comp["status"] = "modified"
                elif v1_col.get("type") != v2_col.get("type"):
                    dataset_comp["column_changes"].append({
                        "column_name": col_name,
                        "change_type": "type_changed",
                        "v1_type": v1_col["type"],
                        "v2_type": v2_col["type"]
                    })
                    if dataset_comp["status"] == "unchanged":
                        dataset_comp["status"] = "modified"
        
        comparison["dataset_comparison"].append(dataset_comp)
    
    return comparison