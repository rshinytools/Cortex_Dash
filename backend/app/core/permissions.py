# ABOUTME: Permission system for Role-Based Access Control (RBAC)
# ABOUTME: Defines roles, permissions, and permission checking logic

from enum import Enum
from typing import List, Set, Dict, Optional
from functools import wraps
from fastapi import HTTPException, Depends, status
from sqlmodel import Session

from app.core.db import engine
from app.models import User
from app.api.deps import get_current_user


class Role(str, Enum):
    """User roles in the system"""
    SYSTEM_ADMIN = "system_admin"
    ORG_ADMIN = "org_admin"
    STUDY_MANAGER = "study_manager"
    DATA_MANAGER = "data_manager"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Permission(str, Enum):
    """System permissions"""
    # System permissions
    MANAGE_SYSTEM = "manage_system"
    VIEW_ALL_ORGS = "view_all_orgs"
    
    # Organization permissions
    MANAGE_ORG = "manage_org"
    VIEW_ORG = "view_org"
    MANAGE_ORG_USERS = "manage_org_users"
    MANAGE_ORG_SETTINGS = "manage_org_settings"
    
    # Study permissions
    CREATE_STUDY = "create_study"
    VIEW_STUDY = "view_study"
    EDIT_STUDY = "edit_study"
    DELETE_STUDY = "delete_study"
    MANAGE_STUDY_DATA = "manage_study_data"
    EXPORT_STUDY_DATA = "export_study_data"
    
    # Data pipeline permissions
    CONFIGURE_PIPELINE = "configure_pipeline"
    EXECUTE_PIPELINE = "execute_pipeline"
    VIEW_PIPELINE_LOGS = "view_pipeline_logs"
    
    # Dashboard permissions
    VIEW_DASHBOARD = "view_dashboard"
    EDIT_DASHBOARD = "edit_dashboard"
    CREATE_WIDGETS = "create_widgets"
    
    # Report permissions
    VIEW_REPORTS = "view_reports"
    CREATE_REPORTS = "create_reports"
    SCHEDULE_REPORTS = "schedule_reports"
    
    # Activity log permissions
    VIEW_ACTIVITY_LOG = "view_activity_log"
    VIEW_AUDIT_TRAIL = "view_audit_trail"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.SYSTEM_ADMIN: set(Permission),  # All permissions
    
    Role.ORG_ADMIN: {
        Permission.VIEW_ORG,
        Permission.MANAGE_ORG_USERS,  # Only user management
        Permission.VIEW_STUDY,
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_REPORTS,
        Permission.VIEW_ACTIVITY_LOG,
    },
    
    Role.STUDY_MANAGER: {
        Permission.VIEW_ORG,
        Permission.VIEW_STUDY,
        Permission.EDIT_STUDY,
        Permission.MANAGE_STUDY_DATA,
        Permission.EXPORT_STUDY_DATA,
        Permission.CONFIGURE_PIPELINE,
        Permission.EXECUTE_PIPELINE,
        Permission.VIEW_PIPELINE_LOGS,
        Permission.VIEW_DASHBOARD,
        Permission.EDIT_DASHBOARD,
        Permission.CREATE_WIDGETS,
        Permission.VIEW_REPORTS,
        Permission.CREATE_REPORTS,
        Permission.SCHEDULE_REPORTS,
        Permission.VIEW_ACTIVITY_LOG,
    },
    
    Role.DATA_MANAGER: {
        Permission.VIEW_ORG,
        Permission.VIEW_STUDY,
        Permission.MANAGE_STUDY_DATA,
        Permission.EXPORT_STUDY_DATA,
        Permission.EXECUTE_PIPELINE,
        Permission.VIEW_PIPELINE_LOGS,
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_REPORTS,
        Permission.VIEW_ACTIVITY_LOG,
    },
    
    Role.ANALYST: {
        Permission.VIEW_ORG,
        Permission.VIEW_STUDY,
        Permission.EXPORT_STUDY_DATA,
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_REPORTS,
        Permission.CREATE_REPORTS,
        Permission.VIEW_ACTIVITY_LOG,
    },
    
    Role.VIEWER: {
        Permission.VIEW_ORG,
        Permission.VIEW_STUDY,
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_REPORTS,
    },
}


def has_permission(user: User, permission: Permission) -> bool:
    """Check if user has a specific permission"""
    if user.is_superuser:
        return True
    
    user_role = Role(user.role)
    role_permissions = ROLE_PERMISSIONS.get(user_role, set())
    return permission in role_permissions


def has_any_permission(user: User, permissions: List[Permission]) -> bool:
    """Check if user has any of the specified permissions"""
    return any(has_permission(user, perm) for perm in permissions)


def has_all_permissions(user: User, permissions: List[Permission]) -> bool:
    """Check if user has all of the specified permissions"""
    return all(has_permission(user, perm) for perm in permissions)


def require_permission(permission: Permission):
    """Decorator to require a specific permission for an endpoint"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from dependencies
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            
            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permissions: List[Permission]):
    """Decorator to require any of the specified permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            
            if not has_any_permission(current_user, permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required one of: {', '.join(permissions)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_org_access(func):
    """Decorator to ensure user has access to the organization"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        org_id = kwargs.get('org_id')
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        # System admins can access all orgs
        if current_user.is_superuser:
            return await func(*args, **kwargs)
        
        # Check if user belongs to the organization
        if str(current_user.org_id) != str(org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        return await func(*args, **kwargs)
    return wrapper


def require_study_access(permission: Optional[Permission] = None):
    """Decorator to ensure user has access to a study"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            study_id = kwargs.get('study_id')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            
            # Get study from database to check org_id
            from app.crud.study import get_study
            db: Session = kwargs.get('db')
            if not db:
                db = Session(engine)
            
            study = get_study(db, study_id=study_id)
            if not study:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Study not found"
                )
            
            # Check organization access
            if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this study"
                )
            
            # Check specific permission if provided
            if permission and not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class PermissionChecker:
    """Dependency class for checking permissions in FastAPI"""
    
    def __init__(self, permission: Permission):
        self.permission = permission
    
    def __call__(self, current_user: User = Depends(get_current_user)):
        if not has_permission(current_user, self.permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {self.permission}"
            )
        return current_user


class MultiPermissionChecker:
    """Check for multiple permissions (any or all)"""
    
    def __init__(self, permissions: List[Permission], require_all: bool = False):
        self.permissions = permissions
        self.require_all = require_all
    
    def __call__(self, current_user: User = Depends(get_current_user)):
        if self.require_all:
            if not has_all_permissions(current_user, self.permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required all of: {', '.join(self.permissions)}"
                )
        else:
            if not has_any_permission(current_user, self.permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required one of: {', '.join(self.permissions)}"
                )
        return current_user