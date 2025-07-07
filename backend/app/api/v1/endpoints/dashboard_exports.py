# ABOUTME: API endpoints for dashboard export functionality including generation, status checking, and download
# ABOUTME: Supports PDF, PowerPoint, and Excel formats with async processing

import os
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from redis import Redis

from app.api import deps
from app.models.user import User
from app.services.export_service import ExportService
from app.core.config import settings
from app.core.permissions import has_dashboard_access


router = APIRouter()


class ExportRequest(BaseModel):
    format: str  # pdf, pptx, xlsx
    options: Optional[dict] = None


class ExportResponse(BaseModel):
    export_id: str
    status: str
    dashboard_id: str
    format: str
    created_at: datetime
    created_by: str
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None


class ExportStatusResponse(BaseModel):
    export_id: str
    status: str  # pending, processing, completed, failed
    progress: Optional[int] = None
    message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None


@router.post("/dashboards/{dashboard_id}/export", response_model=ExportResponse)
async def create_export(
    dashboard_id: str,
    export_request: ExportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    redis: Redis = Depends(deps.get_redis)
) -> ExportResponse:
    """
    Create a new dashboard export.
    
    Supported formats:
    - pdf: PDF document with all widgets
    - pptx: PowerPoint presentation
    - xlsx: Excel workbook with multiple sheets
    """
    # Check access
    if not await has_dashboard_access(db, current_user, dashboard_id):
        raise HTTPException(status_code=403, detail="Access denied to dashboard")
    
    # Validate format
    if export_request.format not in ["pdf", "pptx", "xlsx"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format: {export_request.format}. Supported formats: pdf, pptx, xlsx"
        )
    
    # Create export service
    export_service = ExportService(db)
    
    # Generate export synchronously for now (can be moved to Celery for large exports)
    try:
        export_info = await export_service.export_dashboard(
            dashboard_id=dashboard_id,
            format=export_request.format,
            user=current_user,
            options=export_request.options
        )
        
        # Store export info in Redis with TTL
        export_key = f"export:{export_info['export_id']}"
        export_data = {
            **export_info,
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        # Store in Redis for 24 hours
        await redis.setex(
            export_key,
            86400,  # 24 hours in seconds
            str(export_data)
        )
        
        # Schedule cleanup after 24 hours
        background_tasks.add_task(
            cleanup_export,
            export_info["export_id"],
            delay_seconds=86400
        )
        
        return ExportResponse(
            export_id=export_info["export_id"],
            status="completed",
            dashboard_id=dashboard_id,
            format=export_request.format,
            created_at=export_info["created_at"],
            created_by=export_info["created_by"],
            file_size=export_info["file_size"],
            download_url=f"/api/v1/dashboard-exports/{export_info['export_id']}/download",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
    except Exception as e:
        # Store error in Redis
        error_data = {
            "export_id": str(datetime.utcnow().timestamp()),
            "status": "failed",
            "error": str(e),
            "dashboard_id": dashboard_id,
            "format": export_request.format,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": current_user.email
        }
        
        raise HTTPException(
            status_code=500,
            detail=f"Export generation failed: {str(e)}"
        )


@router.get("/dashboard-exports/{export_id}/status", response_model=ExportStatusResponse)
async def get_export_status(
    export_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    redis: Redis = Depends(deps.get_redis)
) -> ExportStatusResponse:
    """Get the status of an export"""
    export_key = f"export:{export_id}"
    export_data = await redis.get(export_key)
    
    if not export_data:
        raise HTTPException(status_code=404, detail="Export not found or expired")
    
    # Parse export data
    import json
    export_info = json.loads(export_data.decode() if isinstance(export_data, bytes) else export_data)
    
    # Check if user has access to the dashboard
    if not await has_dashboard_access(db, current_user, export_info.get("dashboard_id")):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ExportStatusResponse(
        export_id=export_id,
        status=export_info.get("status", "unknown"),
        progress=export_info.get("progress"),
        message=export_info.get("message"),
        created_at=datetime.fromisoformat(export_info["created_at"]),
        completed_at=datetime.fromisoformat(export_info["completed_at"]) if export_info.get("completed_at") else None,
        download_url=f"/api/v1/dashboard-exports/{export_id}/download" if export_info.get("status") == "completed" else None,
        expires_at=datetime.fromisoformat(export_info["expires_at"]) if export_info.get("expires_at") else None
    )


@router.get("/dashboard-exports/{export_id}/download")
async def download_export(
    export_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    redis: Redis = Depends(deps.get_redis)
) -> FileResponse:
    """Download an export file"""
    export_key = f"export:{export_id}"
    export_data = await redis.get(export_key)
    
    if not export_data:
        raise HTTPException(status_code=404, detail="Export not found or expired")
    
    # Parse export data
    import json
    export_info = json.loads(export_data.decode() if isinstance(export_data, bytes) else export_data)
    
    # Check if user has access to the dashboard
    if not await has_dashboard_access(db, current_user, export_info.get("dashboard_id")):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if export is completed
    if export_info.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Export is not ready for download")
    
    # Get file path
    export_service = ExportService(db)
    file_path = export_service.get_export_path(export_id)
    
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Export file not found")
    
    # Determine media type based on format
    media_types = {
        ".pdf": "application/pdf",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    
    media_type = media_types.get(file_path.suffix, "application/octet-stream")
    
    # Generate filename
    dashboard_name = export_info.get("dashboard_name", "dashboard")
    safe_name = "".join(c for c in dashboard_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    timestamp = datetime.fromisoformat(export_info["created_at"]).strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_name}_{timestamp}{file_path.suffix}"
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.delete("/dashboard-exports/{export_id}")
async def delete_export(
    export_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    redis: Redis = Depends(deps.get_redis)
) -> dict:
    """Delete an export"""
    export_key = f"export:{export_id}"
    export_data = await redis.get(export_key)
    
    if not export_data:
        raise HTTPException(status_code=404, detail="Export not found or expired")
    
    # Parse export data
    import json
    export_info = json.loads(export_data.decode() if isinstance(export_data, bytes) else export_data)
    
    # Check if user has access to the dashboard
    if not await has_dashboard_access(db, current_user, export_info.get("dashboard_id")):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete file
    export_service = ExportService(db)
    deleted = export_service.delete_export(export_id)
    
    # Delete from Redis
    await redis.delete(export_key)
    
    return {"message": "Export deleted successfully", "deleted": deleted}


async def cleanup_export(export_id: str, delay_seconds: int = 0):
    """Background task to cleanup export after delay"""
    if delay_seconds > 0:
        import asyncio
        await asyncio.sleep(delay_seconds)
    
    # Create a new DB session for background task
    from app.db.session import SessionLocal
    async with SessionLocal() as db:
        export_service = ExportService(db)
        export_service.delete_export(export_id)
    
    # Also delete from Redis if still exists
    from app.core.redis import get_redis_client
    redis = await get_redis_client()
    await redis.delete(f"export:{export_id}")