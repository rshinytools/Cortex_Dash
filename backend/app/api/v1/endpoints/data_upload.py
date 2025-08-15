# ABOUTME: API endpoints for data upload, versioning, and mapping
# ABOUTME: Handles file uploads, Parquet conversion, and widget mapping

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlmodel import Session
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db
from app.api.deps.permissions import require_permission
from app.models.user import User
from app.models.data_source_upload import DataSourceUploadPublic, DataSourceUploadsPublic
from app.services.data.upload_service import DataUploadService
from app.services.data.versioning_service import VersioningService
from app.services.data.mapping_service import WidgetMappingService
from app.core.logging import logger

router = APIRouter()

class MappingRequest(BaseModel):
    widget_id: str
    upload_id: str
    dataset_name: str
    field_mappings: Dict[str, str]

class MappingValidationRequest(BaseModel):
    widget_type: str
    dataset_columns: List[str]
    field_mappings: Dict[str, str]

class VersionTagRequest(BaseModel):
    tag: str

class VersionRollbackRequest(BaseModel):
    target_version: int

@router.post("/studies/{study_id}/upload")
@require_permission("data.upload")
async def upload_data(
    study_id: str,
    file: UploadFile = File(...),
    upload_name: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DataSourceUploadPublic:
    """Upload data file and convert to Parquet"""
    
    service = DataUploadService(db)
    
    try:
        upload = await service.upload_file(
            file=file,
            study_id=study_id,
            user_id=str(current_user.id),
            upload_name=upload_name,
            description=description
        )
        
        return DataSourceUploadPublic.from_orm(upload)
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/studies/{study_id}/uploads")
@require_permission("data.view")
async def get_uploads(
    study_id: str,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DataSourceUploadsPublic:
    """Get all uploads for a study"""
    
    from sqlmodel import select
    from app.models.data_source_upload import DataSourceUpload
    
    stmt = select(DataSourceUpload).where(
        DataSourceUpload.study_id == study_id
    )
    
    if not include_inactive:
        stmt = stmt.where(DataSourceUpload.is_active_version == True)
    
    stmt = stmt.order_by(DataSourceUpload.version_number.desc())
    
    uploads = db.exec(stmt).all()
    
    return DataSourceUploadsPublic(
        data=[DataSourceUploadPublic.from_orm(u) for u in uploads],
        count=len(uploads)
    )

@router.get("/studies/{study_id}/datasets")
@require_permission("data.view")
async def get_available_datasets(
    study_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get available datasets for mapping"""
    
    service = DataUploadService(db)
    return service.get_available_datasets(study_id)

@router.get("/studies/{study_id}/datasets/{dataset_name}/columns")
@require_permission("data.view")
async def get_dataset_columns(
    study_id: str,
    dataset_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, str]]:
    """Get columns for a specific dataset"""
    
    service = DataUploadService(db)
    return service.get_dataset_columns(study_id, dataset_name)

# Version management endpoints

@router.get("/studies/{study_id}/versions")
@require_permission("data.view")
async def get_version_history(
    study_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get version history for a study"""
    
    service = VersioningService(db)
    return service.get_version_history(study_id)

@router.put("/studies/{study_id}/versions/{version_number}/activate")
@require_permission("data.upload")
async def set_active_version(
    study_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Set a specific version as active"""
    
    service = VersioningService(db)
    
    if service.set_active_version(study_id, version_number):
        return {"message": f"Version {version_number} is now active"}
    else:
        raise HTTPException(status_code=500, detail="Failed to set active version")

@router.post("/studies/{study_id}/versions/{version_number}/tag")
@require_permission("data.upload")
async def create_version_tag(
    study_id: str,
    version_number: int,
    request: VersionTagRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Create a tag for a version"""
    
    service = VersioningService(db)
    
    upload = service.create_version_tag(
        study_id=study_id,
        version_number=version_number,
        tag=request.tag,
        user_id=str(current_user.id)
    )
    
    return {"message": f"Tag '{request.tag}' created for version {version_number}"}

@router.get("/studies/{study_id}/versions/compare")
@require_permission("data.view")
async def compare_versions(
    study_id: str,
    version1: int = Query(...),
    version2: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Compare two versions of data"""
    
    service = VersioningService(db)
    return service.compare_versions(study_id, version1, version2)

@router.post("/studies/{study_id}/versions/rollback")
@require_permission("data.upload")
async def rollback_version(
    study_id: str,
    request: VersionRollbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DataSourceUploadPublic:
    """Rollback to a previous version"""
    
    service = VersioningService(db)
    
    upload = service.rollback_to_version(
        study_id=study_id,
        target_version=request.target_version,
        user_id=str(current_user.id)
    )
    
    return DataSourceUploadPublic.from_orm(upload)

# Widget mapping endpoints

@router.get("/studies/{study_id}/widgets/{widget_id}/mapping-options")
@require_permission("widget.map")
async def get_mapping_options(
    study_id: str,
    widget_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get available mapping options for a widget"""
    
    service = WidgetMappingService(db)
    return service.get_available_mappings(study_id, widget_id)

@router.post("/widgets/{widget_id}/mapping")
@require_permission("widget.map")
async def create_widget_mapping(
    widget_id: str,
    request: MappingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create or update widget mapping"""
    
    service = WidgetMappingService(db)
    
    mapping = service.create_mapping(
        widget_id=widget_id,
        upload_id=request.upload_id,
        dataset_name=request.dataset_name,
        field_mappings=request.field_mappings,
        user_id=str(current_user.id)
    )
    
    return {
        "id": mapping.id,
        "widget_id": mapping.widget_id,
        "dataset_name": mapping.dataset_name,
        "field_mappings": mapping.field_mappings,
        "created_at": mapping.created_at.isoformat()
    }

@router.delete("/widgets/{widget_id}/mapping")
@require_permission("widget.map")
async def delete_widget_mapping(
    widget_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete widget mapping"""
    
    service = WidgetMappingService(db)
    
    if service.delete_mapping(widget_id):
        return {"message": "Mapping deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Mapping not found")

@router.post("/mappings/validate")
@require_permission("widget.map")
async def validate_mapping(
    request: MappingValidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Validate a mapping configuration"""
    
    service = WidgetMappingService(db)
    
    return service.validate_mapping(
        widget_type=request.widget_type,
        dataset_columns=request.dataset_columns,
        field_mappings=request.field_mappings
    )

@router.get("/widgets/requirements/{widget_type}")
@require_permission("widget.view")
async def get_widget_requirements(
    widget_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, List[str]]:
    """Get field requirements for a widget type"""
    
    service = WidgetMappingService(db)
    return service.get_widget_requirements(widget_type)

@router.post("/mappings/suggest")
@require_permission("widget.map")
async def suggest_mappings(
    widget_type: str = Form(...),
    dataset_columns: List[Dict[str, str]] = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Get mapping suggestions based on column names"""
    
    service = WidgetMappingService(db)
    
    return service.get_mapping_suggestions(
        widget_type=widget_type,
        dataset_columns=dataset_columns
    )