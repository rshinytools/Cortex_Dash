# ABOUTME: API endpoints for managing data refresh schedules
# ABOUTME: Handles CRUD operations for refresh schedules and execution monitoring

from typing import List, Any, Optional, Dict
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlmodel import Session, select
import uuid

from app.api.deps import get_db, get_current_user
from app.models import (
    RefreshSchedule, RefreshScheduleCreate, RefreshScheduleUpdate, RefreshScheduleResponse,
    RefreshExecution, RefreshExecutionCreate, RefreshExecutionUpdate, RefreshExecutionResponse,
    RefreshExecutionSummary, User, Message,
    RefreshType, ScheduleStatus, ExecutionStatus
)
from app.core.permissions import (
    Permission, PermissionChecker, has_permission,
    require_study_access
)
from app.services.data_refresh_scheduler import get_data_refresh_scheduler
from app.services.data_quality.data_quality_analyzer import get_data_quality_analyzer
from app.crud import study as crud_study
from app.crud import activity_log as crud_activity

router = APIRouter()


@router.post("/", response_model=RefreshScheduleResponse)
async def create_refresh_schedule(
    *,
    db: Session = Depends(get_db),
    schedule_in: RefreshScheduleCreate,
    current_user: User = Depends(PermissionChecker(Permission.MANAGE_STUDY_DATA)),
    request: Request
) -> Any:
    """
    Create new refresh schedule. User must have MANAGE_STUDY_DATA permission.
    """
    # Verify study exists and user has access
    study = await require_study_access(db, schedule_in.study_id, current_user)
    
    # Validate cron expression and data sources
    scheduler = get_data_refresh_scheduler(db)
    
    try:
        result = scheduler.create_refresh_schedule(
            study_id=str(schedule_in.study_id),
            schedule_name=schedule_in.schedule_name,
            cron_expression=schedule_in.cron_expression,
            data_sources=schedule_in.data_sources,
            refresh_type=schedule_in.refresh_type,
            enabled=schedule_in.enabled,
            notification_settings=schedule_in.notification_settings
        )
        
        # Log activity
        await crud_activity.create_activity_log(
            db=db,
            action="create_refresh_schedule",
            resource_type="refresh_schedule",
            resource_id=result['schedule_id'],
            user_id=current_user.id,
            org_id=current_user.org_id,
            details={
                "schedule_name": schedule_in.schedule_name,
                "study_id": str(schedule_in.study_id),
                "cron_expression": schedule_in.cron_expression,
                "refresh_type": schedule_in.refresh_type
            }
        )
        
        # Create the actual database record
        schedule_data = RefreshSchedule(
            **schedule_in.model_dump(),
            id=uuid.UUID(result['schedule_id']),
            org_id=current_user.org_id,
            created_by=current_user.id
        )
        
        db.add(schedule_data)
        db.commit()
        db.refresh(schedule_data)
        
        return RefreshScheduleResponse(**schedule_data.model_dump())
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create refresh schedule: {str(e)}"
        )


@router.get("/", response_model=List[RefreshScheduleResponse])
async def get_refresh_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    study_id: Optional[uuid.UUID] = None,
    enabled_only: bool = False,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get refresh schedules. Can filter by study_id and enabled status.
    """
    query = select(RefreshSchedule).where(RefreshSchedule.org_id == current_user.org_id)
    
    if study_id:
        # Verify user has access to the study
        await require_study_access(db, study_id, current_user)
        query = query.where(RefreshSchedule.study_id == study_id)
    
    if enabled_only:
        query = query.where(RefreshSchedule.enabled == True)
    
    query = query.offset(skip).limit(limit)
    schedules = db.exec(query).all()
    
    # Enhance with calculated fields
    response_schedules = []
    for schedule in schedules:
        schedule_dict = schedule.model_dump()
        
        # Calculate success rate
        if schedule.total_runs > 0:
            schedule_dict['success_rate'] = (schedule.successful_runs / schedule.total_runs) * 100
        else:
            schedule_dict['success_rate'] = 100.0
        
        # Get average duration from recent executions
        recent_executions = db.exec(
            select(RefreshExecution)
            .where(RefreshExecution.schedule_id == schedule.id)
            .where(RefreshExecution.status == ExecutionStatus.COMPLETED)
            .order_by(RefreshExecution.started_at.desc())
            .limit(10)
        ).all()
        
        if recent_executions:
            durations = [ex.duration_seconds for ex in recent_executions if ex.duration_seconds]
            schedule_dict['average_duration'] = sum(durations) / len(durations) if durations else None
            schedule_dict['last_execution_status'] = recent_executions[0].status
        else:
            schedule_dict['average_duration'] = None
            schedule_dict['last_execution_status'] = None
        
        # Calculate health score
        health_score = 100.0
        if not schedule.enabled:
            health_score -= 50
        if schedule_dict['success_rate'] < 80:
            health_score -= 30
        if recent_executions and recent_executions[0].status == ExecutionStatus.FAILED:
            health_score -= 20
        
        schedule_dict['health_score'] = max(0.0, health_score)
        
        response_schedules.append(RefreshScheduleResponse(**schedule_dict))
    
    return response_schedules


@router.get("/{schedule_id}", response_model=RefreshScheduleResponse)
async def get_refresh_schedule(
    schedule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific refresh schedule by ID.
    """
    schedule = db.get(RefreshSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh schedule not found"
        )
    
    # Check access
    await require_study_access(db, schedule.study_id, current_user)
    
    # Get scheduler service for status
    scheduler = get_data_refresh_scheduler(db)
    status_info = scheduler.get_schedule_status(str(schedule_id))
    
    schedule_dict = schedule.model_dump()
    schedule_dict.update(status_info)
    
    return RefreshScheduleResponse(**schedule_dict)


@router.put("/{schedule_id}", response_model=RefreshScheduleResponse)
async def update_refresh_schedule(
    schedule_id: uuid.UUID,
    schedule_update: RefreshScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(Permission.MANAGE_STUDY_DATA))
) -> Any:
    """
    Update a refresh schedule. User must have MANAGE_STUDY_DATA permission.
    """
    schedule = db.get(RefreshSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh schedule not found"
        )
    
    # Check access
    await require_study_access(db, schedule.study_id, current_user)
    
    # Update through scheduler service
    scheduler = get_data_refresh_scheduler(db)
    
    try:
        update_data = schedule_update.model_dump(exclude_unset=True)
        result = scheduler.update_refresh_schedule(str(schedule_id), update_data)
        
        # Update database record
        for field, value in update_data.items():
            setattr(schedule, field, value)
        
        schedule.updated_at = datetime.utcnow()
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        
        # Log activity
        await crud_activity.create_activity_log(
            db=db,
            action="update_refresh_schedule",
            resource_type="refresh_schedule",
            resource_id=str(schedule_id),
            user_id=current_user.id,
            org_id=current_user.org_id,
            details=update_data
        )
        
        return RefreshScheduleResponse(**schedule.model_dump())
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update refresh schedule: {str(e)}"
        )


@router.delete("/{schedule_id}", response_model=Message)
async def delete_refresh_schedule(
    schedule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(Permission.MANAGE_STUDY_DATA))
) -> Any:
    """
    Delete a refresh schedule. User must have MANAGE_STUDY_DATA permission.
    """
    schedule = db.get(RefreshSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh schedule not found"
        )
    
    # Check access
    await require_study_access(db, schedule.study_id, current_user)
    
    # Delete through scheduler service
    scheduler = get_data_refresh_scheduler(db)
    
    try:
        result = scheduler.delete_refresh_schedule(str(schedule_id))
        
        # Delete from database
        db.delete(schedule)
        db.commit()
        
        # Log activity
        await crud_activity.create_activity_log(
            db=db,
            action="delete_refresh_schedule",
            resource_type="refresh_schedule",
            resource_id=str(schedule_id),
            user_id=current_user.id,
            org_id=current_user.org_id,
            details={"schedule_name": schedule.schedule_name}
        )
        
        return Message(message="Refresh schedule deleted successfully")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete refresh schedule: {str(e)}"
        )


@router.post("/{schedule_id}/execute", response_model=RefreshExecutionResponse)
async def execute_refresh_now(
    schedule_id: uuid.UUID,
    force: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(Permission.MANAGE_STUDY_DATA))
) -> Any:
    """
    Execute a refresh schedule immediately. User must have MANAGE_STUDY_DATA permission.
    """
    schedule = db.get(RefreshSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh schedule not found"
        )
    
    # Check access
    await require_study_access(db, schedule.study_id, current_user)
    
    # Execute through scheduler service
    scheduler = get_data_refresh_scheduler(db)
    
    try:
        result = scheduler.execute_refresh_now(str(schedule_id), force)
        
        # Create execution record
        execution = RefreshExecution(
            id=uuid.UUID(result['execution_id']),
            schedule_id=schedule_id,
            study_id=schedule.study_id,
            org_id=current_user.org_id,
            execution_name=f"Manual execution by {current_user.full_name or current_user.email}",
            refresh_type=schedule.refresh_type,
            data_sources=schedule.data_sources,
            refresh_options=schedule.refresh_options,
            started_at=datetime.utcnow(),
            status=ExecutionStatus.RUNNING,
            triggered_by="manual",
            triggered_by_user_id=current_user.id
        )
        
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # Log activity
        await crud_activity.create_activity_log(
            db=db,
            action="execute_refresh_schedule",
            resource_type="refresh_schedule",
            resource_id=str(schedule_id),
            user_id=current_user.id,
            org_id=current_user.org_id,
            details={
                "execution_id": result['execution_id'],
                "force": force,
                "trigger": "manual"
            }
        )
        
        return RefreshExecutionResponse(**execution.model_dump(), schedule_name=schedule.schedule_name)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to execute refresh: {str(e)}"
        )


@router.post("/{schedule_id}/pause", response_model=Message)
async def pause_refresh_schedule(
    schedule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(Permission.MANAGE_STUDY_DATA))
) -> Any:
    """
    Pause a refresh schedule. User must have MANAGE_STUDY_DATA permission.
    """
    schedule = db.get(RefreshSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh schedule not found"
        )
    
    # Check access
    await require_study_access(db, schedule.study_id, current_user)
    
    # Pause through scheduler service
    scheduler = get_data_refresh_scheduler(db)
    result = scheduler.pause_schedule(str(schedule_id))
    
    # Update database
    schedule.enabled = False
    schedule.status = ScheduleStatus.PAUSED
    schedule.updated_at = datetime.utcnow()
    db.add(schedule)
    db.commit()
    
    # Log activity
    await crud_activity.create_activity_log(
        db=db,
        action="pause_refresh_schedule",
        resource_type="refresh_schedule",
        resource_id=str(schedule_id),
        user_id=current_user.id,
        org_id=current_user.org_id,
        details={"schedule_name": schedule.schedule_name}
    )
    
    return Message(message="Refresh schedule paused successfully")


@router.post("/{schedule_id}/resume", response_model=Message)
async def resume_refresh_schedule(
    schedule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(Permission.MANAGE_STUDY_DATA))
) -> Any:
    """
    Resume a paused refresh schedule. User must have MANAGE_STUDY_DATA permission.
    """
    schedule = db.get(RefreshSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh schedule not found"
        )
    
    # Check access
    await require_study_access(db, schedule.study_id, current_user)
    
    # Resume through scheduler service
    scheduler = get_data_refresh_scheduler(db)
    result = scheduler.resume_schedule(str(schedule_id))
    
    # Update database
    schedule.enabled = True
    schedule.status = ScheduleStatus.ACTIVE
    schedule.updated_at = datetime.utcnow()
    db.add(schedule)
    db.commit()
    
    # Log activity
    await crud_activity.create_activity_log(
        db=db,
        action="resume_refresh_schedule",
        resource_type="refresh_schedule",
        resource_id=str(schedule_id),
        user_id=current_user.id,
        org_id=current_user.org_id,
        details={"schedule_name": schedule.schedule_name}
    )
    
    return Message(message="Refresh schedule resumed successfully")


@router.get("/{schedule_id}/executions", response_model=List[RefreshExecutionResponse])
async def get_refresh_executions(
    schedule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50
) -> Any:
    """
    Get execution history for a refresh schedule.
    """
    schedule = db.get(RefreshSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh schedule not found"
        )
    
    # Check access
    await require_study_access(db, schedule.study_id, current_user)
    
    executions = db.exec(
        select(RefreshExecution)
        .where(RefreshExecution.schedule_id == schedule_id)
        .order_by(RefreshExecution.started_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()
    
    response_executions = []
    for execution in executions:
        execution_dict = execution.model_dump()
        execution_dict['schedule_name'] = schedule.schedule_name
        response_executions.append(RefreshExecutionResponse(**execution_dict))
    
    return response_executions


@router.get("/{schedule_id}/summary", response_model=RefreshExecutionSummary)
async def get_refresh_summary(
    schedule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get execution summary statistics for a refresh schedule.
    """
    schedule = db.get(RefreshSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh schedule not found"
        )
    
    # Check access
    await require_study_access(db, schedule.study_id, current_user)
    
    # Get execution statistics
    executions = db.exec(
        select(RefreshExecution)
        .where(RefreshExecution.schedule_id == schedule_id)
    ).all()
    
    total_executions = len(executions)
    successful_executions = len([ex for ex in executions if ex.status == ExecutionStatus.COMPLETED])
    failed_executions = len([ex for ex in executions if ex.status == ExecutionStatus.FAILED])
    
    success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 100.0
    
    # Calculate average duration
    completed_executions = [ex for ex in executions if ex.duration_seconds is not None]
    average_duration = (
        sum(ex.duration_seconds for ex in completed_executions) / len(completed_executions)
        if completed_executions else 0.0
    )
    
    # Calculate total records processed
    total_records_processed = sum(ex.records_processed for ex in executions)
    
    # Get dates
    last_execution_date = max((ex.started_at for ex in executions), default=None)
    next_execution_date = schedule.next_run_at
    
    return RefreshExecutionSummary(
        total_executions=total_executions,
        successful_executions=successful_executions,
        failed_executions=failed_executions,
        success_rate=success_rate,
        average_duration=average_duration,
        total_records_processed=total_records_processed,
        last_execution_date=last_execution_date,
        next_execution_date=next_execution_date
    )


# Data Quality endpoints
@router.post("/{schedule_id}/analyze-quality", response_model=Dict[str, Any])
async def analyze_data_quality(
    schedule_id: uuid.UUID,
    dataset_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Analyze data quality for datasets associated with a refresh schedule.
    """
    schedule = db.get(RefreshSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh schedule not found"
        )
    
    # Check access
    await require_study_access(db, schedule.study_id, current_user)
    
    # Get data quality analyzer
    analyzer = get_data_quality_analyzer(db)
    
    try:
        if dataset_name:
            # Analyze specific dataset
            quality_results = analyzer.analyze_dataset_quality(
                str(schedule.study_id),
                dataset_name
            )
        else:
            # Analyze all datasets for the study
            quality_results = analyzer.analyze_study_quality(str(schedule.study_id))
        
        return quality_results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze data quality: {str(e)}"
        )