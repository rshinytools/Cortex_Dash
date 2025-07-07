# ABOUTME: API endpoints for managing scheduled dashboard exports with email delivery
# ABOUTME: Supports CRUD operations, cron scheduling, and export history tracking

from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import croniter

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models.user import User
from app.models.scheduled_export import (
    ScheduledExport,
    ScheduledExportCreate,
    ScheduledExportUpdate,
    ScheduledExportRead,
    ScheduledExportHistory,
    ScheduledExportHistoryRead
)
from app.models.dashboard import DashboardTemplate
from app.core.permissions import has_dashboard_access
from app.crud.base import CRUDBase


router = APIRouter()


class CRUDScheduledExport(CRUDBase[ScheduledExport, ScheduledExportCreate, ScheduledExportUpdate]):
    async def create_with_owner(
        self, db: AsyncSession, *, obj_in: ScheduledExportCreate, owner_id: UUID
    ) -> ScheduledExport:
        # Calculate next run time
        cron = croniter.croniter(obj_in.schedule, datetime.utcnow())
        next_run = cron.get_next(datetime)
        
        db_obj = ScheduledExport(
            **obj_in.dict(),
            created_by=owner_id,
            next_run_at=next_run
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self, db: AsyncSession, *, db_obj: ScheduledExport, obj_in: ScheduledExportUpdate
    ) -> ScheduledExport:
        update_data = obj_in.dict(exclude_unset=True)
        
        # If schedule is updated, recalculate next run time
        if "schedule" in update_data:
            cron = croniter.croniter(update_data["schedule"], datetime.utcnow())
            update_data["next_run_at"] = cron.get_next(datetime)
        
        update_data["updated_at"] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


scheduled_export_crud = CRUDScheduledExport(ScheduledExport)


@router.post("/dashboards/{dashboard_id}/scheduled-exports", response_model=ScheduledExportRead)
async def create_scheduled_export(
    dashboard_id: str,
    scheduled_export_in: ScheduledExportCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> ScheduledExportRead:
    """Create a new scheduled export for a dashboard"""
    # Check dashboard access
    if not await has_dashboard_access(db, current_user, dashboard_id):
        raise HTTPException(status_code=403, detail="Access denied to dashboard")
    
    # Validate cron expression
    try:
        croniter.croniter(scheduled_export_in.schedule)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid cron expression. Example: '0 9 * * 1' for Monday 9am"
        )
    
    # Validate format
    if scheduled_export_in.format not in ["pdf", "pptx", "xlsx"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format: {scheduled_export_in.format}. Supported formats: pdf, pptx, xlsx"
        )
    
    # Validate email recipients
    if scheduled_export_in.email_recipients:
        # Basic email validation
        for email in scheduled_export_in.email_recipients:
            if "@" not in email:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid email address: {email}"
                )
    
    # Create scheduled export
    scheduled_export_in.dashboard_id = UUID(dashboard_id)
    scheduled_export = await scheduled_export_crud.create_with_owner(
        db, obj_in=scheduled_export_in, owner_id=current_user.id
    )
    
    # Get dashboard name for response
    dashboard = await db.get(DashboardTemplate, UUID(dashboard_id))
    
    return ScheduledExportRead(
        **scheduled_export.__dict__,
        dashboard_name=dashboard.name if dashboard else None,
        creator_name=current_user.email
    )


@router.get("/dashboards/{dashboard_id}/scheduled-exports", response_model=List[ScheduledExportRead])
async def list_scheduled_exports(
    dashboard_id: str,
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> List[ScheduledExportRead]:
    """List scheduled exports for a dashboard"""
    # Check dashboard access
    if not await has_dashboard_access(db, current_user, dashboard_id):
        raise HTTPException(status_code=403, detail="Access denied to dashboard")
    
    # Build query
    query = select(ScheduledExport).where(
        ScheduledExport.dashboard_id == UUID(dashboard_id)
    ).options(
        selectinload(ScheduledExport.dashboard),
        selectinload(ScheduledExport.creator)
    )
    
    if is_active is not None:
        query = query.where(ScheduledExport.is_active == is_active)
    
    query = query.order_by(ScheduledExport.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    scheduled_exports = result.scalars().all()
    
    return [
        ScheduledExportRead(
            **se.__dict__,
            dashboard_name=se.dashboard.name if se.dashboard else None,
            creator_name=se.creator.email if se.creator else None
        )
        for se in scheduled_exports
    ]


@router.get("/scheduled-exports/{export_id}", response_model=ScheduledExportRead)
async def get_scheduled_export(
    export_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> ScheduledExportRead:
    """Get a scheduled export by ID"""
    scheduled_export = await db.get(ScheduledExport, export_id)
    if not scheduled_export:
        raise HTTPException(status_code=404, detail="Scheduled export not found")
    
    # Check dashboard access
    if not await has_dashboard_access(db, current_user, str(scheduled_export.dashboard_id)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Load related data
    await db.refresh(scheduled_export, ["dashboard", "creator"])
    
    return ScheduledExportRead(
        **scheduled_export.__dict__,
        dashboard_name=scheduled_export.dashboard.name if scheduled_export.dashboard else None,
        creator_name=scheduled_export.creator.email if scheduled_export.creator else None
    )


@router.put("/scheduled-exports/{export_id}", response_model=ScheduledExportRead)
async def update_scheduled_export(
    export_id: UUID,
    scheduled_export_in: ScheduledExportUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> ScheduledExportRead:
    """Update a scheduled export"""
    scheduled_export = await db.get(ScheduledExport, export_id)
    if not scheduled_export:
        raise HTTPException(status_code=404, detail="Scheduled export not found")
    
    # Check dashboard access
    if not await has_dashboard_access(db, current_user, str(scheduled_export.dashboard_id)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate updates
    if scheduled_export_in.schedule:
        try:
            croniter.croniter(scheduled_export_in.schedule)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid cron expression"
            )
    
    if scheduled_export_in.format and scheduled_export_in.format not in ["pdf", "pptx", "xlsx"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format: {scheduled_export_in.format}"
        )
    
    # Update
    scheduled_export = await scheduled_export_crud.update(
        db, db_obj=scheduled_export, obj_in=scheduled_export_in
    )
    
    # Load related data
    await db.refresh(scheduled_export, ["dashboard", "creator"])
    
    return ScheduledExportRead(
        **scheduled_export.__dict__,
        dashboard_name=scheduled_export.dashboard.name if scheduled_export.dashboard else None,
        creator_name=scheduled_export.creator.email if scheduled_export.creator else None
    )


@router.delete("/scheduled-exports/{export_id}")
async def delete_scheduled_export(
    export_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> dict:
    """Delete a scheduled export"""
    scheduled_export = await db.get(ScheduledExport, export_id)
    if not scheduled_export:
        raise HTTPException(status_code=404, detail="Scheduled export not found")
    
    # Check dashboard access
    if not await has_dashboard_access(db, current_user, str(scheduled_export.dashboard_id)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.delete(scheduled_export)
    await db.commit()
    
    return {"message": "Scheduled export deleted successfully"}


@router.post("/scheduled-exports/{export_id}/run")
async def run_scheduled_export_now(
    export_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> dict:
    """Manually trigger a scheduled export"""
    scheduled_export = await db.get(ScheduledExport, export_id)
    if not scheduled_export:
        raise HTTPException(status_code=404, detail="Scheduled export not found")
    
    # Check dashboard access
    if not await has_dashboard_access(db, current_user, str(scheduled_export.dashboard_id)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Trigger export job via Celery
    # For now, we'll just update the last run time
    scheduled_export.last_run_at = datetime.utcnow()
    scheduled_export.last_run_status = "processing"
    
    db.add(scheduled_export)
    await db.commit()
    
    return {
        "message": "Export triggered successfully",
        "export_id": str(export_id),
        "status": "processing"
    }


@router.get("/scheduled-exports/{export_id}/history", response_model=List[ScheduledExportHistoryRead])
async def get_scheduled_export_history(
    export_id: UUID,
    status: Optional[str] = Query(None, enum=["success", "failed", "skipped"]),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> List[ScheduledExportHistoryRead]:
    """Get execution history for a scheduled export"""
    # Check if scheduled export exists
    scheduled_export = await db.get(ScheduledExport, export_id)
    if not scheduled_export:
        raise HTTPException(status_code=404, detail="Scheduled export not found")
    
    # Check dashboard access
    if not await has_dashboard_access(db, current_user, str(scheduled_export.dashboard_id)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Build query
    query = select(ScheduledExportHistory).where(
        ScheduledExportHistory.scheduled_export_id == export_id
    )
    
    if status:
        query = query.where(ScheduledExportHistory.status == status)
    
    if start_date:
        query = query.where(ScheduledExportHistory.executed_at >= start_date)
    
    if end_date:
        query = query.where(ScheduledExportHistory.executed_at <= end_date)
    
    query = query.order_by(ScheduledExportHistory.executed_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    history_items = result.scalars().all()
    
    return [ScheduledExportHistoryRead(**item.__dict__) for item in history_items]


@router.get("/scheduled-exports/upcoming", response_model=List[ScheduledExportRead])
async def get_upcoming_exports(
    hours: int = Query(24, ge=1, le=168, description="Hours to look ahead"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> List[ScheduledExportRead]:
    """Get upcoming scheduled exports in the next N hours"""
    cutoff_time = datetime.utcnow() + timedelta(hours=hours)
    
    # Get all scheduled exports the user has access to
    query = select(ScheduledExport).where(
        ScheduledExport.is_active == True,
        ScheduledExport.next_run_at <= cutoff_time
    ).options(
        selectinload(ScheduledExport.dashboard),
        selectinload(ScheduledExport.creator)
    )
    
    result = await db.execute(query)
    scheduled_exports = result.scalars().all()
    
    # Filter by dashboard access
    accessible_exports = []
    for se in scheduled_exports:
        if await has_dashboard_access(db, current_user, str(se.dashboard_id)):
            accessible_exports.append(
                ScheduledExportRead(
                    **se.__dict__,
                    dashboard_name=se.dashboard.name if se.dashboard else None,
                    creator_name=se.creator.email if se.creator else None
                )
            )
    
    # Sort by next run time
    accessible_exports.sort(key=lambda x: x.next_run_at or datetime.max)
    
    return accessible_exports