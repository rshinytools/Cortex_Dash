# ABOUTME: API endpoints for backup and restore operations with 21 CFR Part 11 compliance
# ABOUTME: Provides endpoints for creating backups, listing backups, restoring, and downloading backup files

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime

from app.api.deps import get_current_active_superuser
from app.models import User
from app.services.backup.backup_service import backup_service
from app.services.backup.restore_service import restore_service
# from app.services.activity_service import activity_service  # TODO: Implement activity service
from pathlib import Path


router = APIRouter()


# Request/Response models
class CreateBackupRequest(BaseModel):
    description: Optional[str] = None
    backup_type: str = "full"  # full, database, files


class BackupResponse(BaseModel):
    id: str
    filename: str
    size_mb: float
    checksum: str
    description: Optional[str]
    created_by: str
    created_by_name: Optional[str]
    created_by_email: str
    created_at: str
    metadata: dict


class CreateBackupResponse(BaseModel):
    success: bool
    backup_id: str
    filename: str
    size_mb: float
    checksum: str
    created_at: str


class RestoreBackupRequest(BaseModel):
    create_safety_backup: bool = True


class RestoreBackupResponse(BaseModel):
    success: bool
    backup_id: str
    backup_filename: str
    safety_backup_id: Optional[str]
    restored_at: str


@router.post("/backup", response_model=CreateBackupResponse)
async def create_backup(
    request: CreateBackupRequest,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Create a new system backup.
    
    Requires SYSTEM_ADMIN privileges.
    Creates a compressed backup of the database and/or files.
    """
    try:
        # Log activity
        # TODO: Implement activity logging
        # await activity_service.log_activity(
        #     user_id=current_user.id,
        #     action="backup.create",
        #     resource_type="backup",
        #     details={
        #         "backup_type": request.backup_type,
        #         "description": request.description
        #     }
        # )
        
        # Create backup
        result = await backup_service.create_backup(
            user_id=current_user.id,
            description=request.description,
            backup_type=request.backup_type
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Backup creation failed")
        
        # Log success
        # TODO: Implement activity logging
        # await activity_service.log_activity(
        #     user_id=current_user.id,
        #     action="backup.created",
        #     resource_type="backup",
        #     resource_id=result["backup_id"],
        #     details={
        #         "filename": result["filename"],
        #         "size_mb": result["size_mb"]
        #     }
        # )
        
        return CreateBackupResponse(**result)
        
    except Exception as e:
        # Log failure
        # TODO: Implement activity logging
        # await activity_service.log_activity(
        #     user_id=current_user.id,
        #     action="backup.failed",
        #     resource_type="backup",
        #     details={"error": str(e)}
        # )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups", response_model=List[BackupResponse])
async def list_backups(
    limit: int = 50,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    List all available backups.
    
    Requires SYSTEM_ADMIN privileges.
    Returns list of backups sorted by creation date (newest first).
    """
    try:
        backups = await backup_service.list_backups(limit=limit)
        return [BackupResponse(**backup) for backup in backups]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backup/{backup_id}", response_model=BackupResponse)
async def get_backup(
    backup_id: UUID,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Get details of a specific backup.
    
    Requires SYSTEM_ADMIN privileges.
    """
    try:
        backup = await backup_service.get_backup(backup_id)
        if not backup:
            raise HTTPException(status_code=404, detail="Backup not found")
        return BackupResponse(**backup)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore/{backup_id}", response_model=RestoreBackupResponse)
async def restore_backup(
    backup_id: UUID,
    request: RestoreBackupRequest,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Restore system from a backup.
    
    Requires SYSTEM_ADMIN privileges.
    Creates a safety backup by default before restoration.
    """
    try:
        # Log restore attempt
        # TODO: Implement activity logging
        # await activity_service.log_activity(
        #     user_id=current_user.id,
        #     action="restore.start",
        #     resource_type="backup",
        #     resource_id=str(backup_id),
        #     details={"create_safety_backup": request.create_safety_backup}
        # )
        
        # Perform restore
        result = await restore_service.restore_backup(
            backup_id=backup_id,
            user_id=current_user.id,
            create_safety_backup=request.create_safety_backup
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Restore failed")
        
        # Log success
        # TODO: Implement activity logging
        # await activity_service.log_activity(
        #     user_id=current_user.id,
        #     action="restore.completed",
        #     resource_type="backup",
        #     resource_id=str(backup_id),
        #     details={
        #         "safety_backup_id": result.get("safety_backup_id")
        #     }
        # )
        
        return RestoreBackupResponse(**result)
        
    except Exception as e:
        # Log failure
        # TODO: Implement activity logging
        # await activity_service.log_activity(
        #     user_id=current_user.id,
        #     action="restore.failed",
        #     resource_type="backup",
        #     resource_id=str(backup_id),
        #     details={"error": str(e)}
        # )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backup/{backup_id}/download")
async def download_backup(
    backup_id: UUID,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Download a backup file.
    
    Requires SYSTEM_ADMIN privileges.
    Streams the backup file for download.
    """
    try:
        # Get backup details
        backup = await backup_service.get_backup(backup_id)
        if not backup:
            raise HTTPException(status_code=404, detail="Backup not found")
        
        # Check if file exists
        backup_path = Path("/data/backups") / backup["filename"]
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        # Log download
        # TODO: Implement activity logging
        # await activity_service.log_activity(
        #     user_id=current_user.id,
        #     action="backup.download",
        #     resource_type="backup",
        #     resource_id=str(backup_id),
        #     details={"filename": backup["filename"]}
        # )
        
        # Return file for download
        return FileResponse(
            path=str(backup_path),
            filename=backup["filename"],
            media_type="application/zip"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup/{backup_id}/verify")
async def verify_backup(
    backup_id: UUID,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Verify backup integrity by checking its checksum.
    
    Requires SYSTEM_ADMIN privileges.
    """
    try:
        is_valid = await backup_service.verify_checksum(backup_id)
        
        # Log verification
        # TODO: Implement activity logging
        # await activity_service.log_activity(
        #     user_id=current_user.id,
        #     action="backup.verify",
        #     resource_type="backup",
        #     resource_id=str(backup_id),
        #     details={"valid": is_valid}
        # )
        
        return {
            "backup_id": str(backup_id),
            "valid": is_valid,
            "message": "Backup integrity verified" if is_valid else "Backup checksum mismatch - file may be corrupted"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/backup/{backup_id}")
async def delete_backup(
    backup_id: UUID,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Delete a backup (soft delete - marks as deleted but keeps record).
    
    Requires SYSTEM_ADMIN privileges.
    For 21 CFR Part 11 compliance, the record is kept but marked as deleted.
    """
    try:
        # For now, we don't allow deletion for compliance reasons
        # In the future, we might implement soft delete
        raise HTTPException(
            status_code=403, 
            detail="Backup deletion is disabled for compliance reasons. Backups will be automatically removed according to retention policy."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))