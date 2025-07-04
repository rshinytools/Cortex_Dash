# ABOUTME: CRUD operations for ActivityLog model
# ABOUTME: Handles audit trail and activity logging for compliance

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy import and_, or_
import uuid

from app.models import ActivityLog, ActivityLogCreate, User


def create_activity_log(
    db: Session,
    user: User,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> ActivityLog:
    """Create an activity log entry"""
    activity = ActivityLog(
        org_id=user.org_id,
        user_id=user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.utcnow(),
        success=success,
        error_message=error_message
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_activity_logs(
    db: Session,
    org_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[ActivityLog]:
    """Get activity logs with filtering"""
    query = select(ActivityLog)
    
    conditions = []
    if org_id:
        conditions.append(ActivityLog.org_id == org_id)
    if user_id:
        conditions.append(ActivityLog.user_id == user_id)
    if action:
        conditions.append(ActivityLog.action == action)
    if resource_type:
        conditions.append(ActivityLog.resource_type == resource_type)
    if resource_id:
        conditions.append(ActivityLog.resource_id == resource_id)
    if start_date:
        conditions.append(ActivityLog.created_at >= start_date)
    if end_date:
        conditions.append(ActivityLog.created_at <= end_date)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(ActivityLog.created_at.desc()).offset(skip).limit(limit)
    return list(db.exec(query).all())


def get_user_activities(
    db: Session,
    user: User,
    days: int = 30,
    skip: int = 0,
    limit: int = 100
) -> List[ActivityLog]:
    """Get recent activities for a user"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Users can see their own activities
    if not user.is_superuser:
        return get_activity_logs(
            db,
            user_id=user.id,
            start_date=start_date,
            skip=skip,
            limit=limit
        )
    
    # Superusers can see all activities
    return get_activity_logs(
        db,
        start_date=start_date,
        skip=skip,
        limit=limit
    )


def get_audit_trail(
    db: Session,
    resource_type: str,
    resource_id: str
) -> List[ActivityLog]:
    """Get complete audit trail for a specific resource"""
    return db.exec(
        select(ActivityLog)
        .where(
            and_(
                ActivityLog.resource_type == resource_type,
                ActivityLog.resource_id == resource_id
            )
        )
        .order_by(ActivityLog.created_at.desc())
    ).all()


def log_login_attempt(
    db: Session,
    email: str,
    success: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    error_message: Optional[str] = None
) -> ActivityLog:
    """Log login attempt"""
    # Try to find user by email
    from app.models import User
    user = db.exec(select(User).where(User.email == email)).first()
    
    if user:
        return create_activity_log(
            db,
            user=user,
            action="login_attempt",
            resource_type="auth",
            details={"email": email, "success": success},
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
    else:
        # Create a system log for unknown user
        activity = ActivityLog(
            org_id=None,  # System level log
            user_id=None,
            action="login_attempt",
            resource_type="auth",
            details={"email": email, "success": False, "reason": "unknown_user"},
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
            success=False,
            error_message="Unknown user"
        )
        db.add(activity)
        db.commit()
        return activity


# Import timedelta for date calculations
from datetime import timedelta