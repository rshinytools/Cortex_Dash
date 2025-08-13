# ABOUTME: Audit logging functionality for tracking user actions
# ABOUTME: Provides activity logging for compliance and security monitoring

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session
import uuid

from app.models import ActivityLog
from app.crud.activity_log import create_activity_log as crud_create_activity_log


class ActivityAction(str, Enum):
    """Standard activity actions for audit logging"""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"


def create_activity_log(
    db: Session,
    user_id: uuid.UUID,
    action: ActivityAction,
    resource_type: str,
    resource_id: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> ActivityLog:
    """
    Create an activity log entry for audit trail
    
    Args:
        db: Database session
        user_id: ID of user performing the action
        action: Type of action performed
        resource_type: Type of resource being acted upon
        resource_id: ID of the resource
        details: Additional details about the action
        ip_address: IP address of the request
    
    Returns:
        Created activity log entry
    """
    # Get user object
    from app.models import User
    user = db.get(User, user_id)
    if not user:
        return None
    
    return crud_create_activity_log(
        db=db,
        user=user,
        action=action.value,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address
    )