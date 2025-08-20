# ABOUTME: Core RBAC functionality for permission checking and enforcement
# ABOUTME: Provides decorators and utilities for API endpoint protection

from typing import Optional, List, Set, Union
from functools import wraps
from uuid import UUID
from fastapi import HTTPException, status, Depends
from sqlmodel import Session, select, and_, or_
import logging

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.rbac import Permission, Role, RolePermission, UserRole
from app.core.audit import log_activity

logger = logging.getLogger(__name__)


class PermissionChecker:
    """Permission checking utility"""
    
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self._permissions_cache = None
        self._roles_cache = None
    
    @property
    def permissions(self) -> Set[str]:
        """Get all permissions for the current user (cached)"""
        if self._permissions_cache is None:
            self._permissions_cache = self._load_permissions()
        return self._permissions_cache
    
    @property
    def roles(self) -> List[str]:
        """Get all role names for the current user (cached)"""
        if self._roles_cache is None:
            self._roles_cache = self._load_roles()
        return self._roles_cache
    
    def _load_permissions(self) -> Set[str]:
        """Load all permissions for the user"""
        permissions = set()
        
        # Get user's roles
        user_roles = self.db.exec(
            select(UserRole).where(
                and_(
                    UserRole.user_id == self.user.id,
                    UserRole.is_active == True
                )
            )
        ).all()
        
        # For each role, get permissions
        for user_role in user_roles:
            role_perms = self.db.exec(
                select(Permission).join(RolePermission).where(
                    and_(
                        RolePermission.role_id == user_role.role_id,
                        RolePermission.is_active == True
                    )
                )
            ).all()
            
            for perm in role_perms:
                permissions.add(perm.name)
        
        return permissions
    
    def _load_roles(self) -> List[str]:
        """Load all role names for the user"""
        roles = []
        
        user_roles = self.db.exec(
            select(Role).join(UserRole).where(
                and_(
                    UserRole.user_id == self.user.id,
                    UserRole.is_active == True
                )
            )
        ).all()
        
        for role in user_roles:
            roles.append(role.name)
        
        return roles
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission"""
        # System admin has all permissions
        if 'system_admin' in self.roles:
            return True
        
        return permission in self.permissions
    
    def has_any_permission(self, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions"""
        # System admin has all permissions
        if 'system_admin' in self.roles:
            return True
        
        for perm in permissions:
            if perm in self.permissions:
                return True
        return False
    
    def has_all_permissions(self, permissions: List[str]) -> bool:
        """Check if user has all of the specified permissions"""
        # System admin has all permissions
        if 'system_admin' in self.roles:
            return True
        
        for perm in permissions:
            if perm not in self.permissions:
                return False
        return True
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role"""
        return role in self.roles
    
    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles"""
        for role in roles:
            if role in self.roles:
                return True
        return False
    
    def check_organization_access(self, org_id: UUID) -> bool:
        """Check if user has access to an organization"""
        # System admin has access to all organizations
        if 'system_admin' in self.roles:
            return True
        
        # Check if user belongs to the organization
        return self.user.org_id == org_id
    
    def check_study_access(self, study_id: UUID, permission: Optional[str] = None) -> bool:
        """Check if user has access to a study"""
        # System admin has access to all studies
        if 'system_admin' in self.roles:
            return True
        
        # Get study to check organization
        from app.models.study import Study
        study = self.db.get(Study, study_id)
        if not study:
            return False
        
        # Check organization access first
        if not self.check_organization_access(study.org_id):
            return False
        
        # Check specific study role if needed
        if permission:
            # Check if user has study-specific role with the permission
            study_role = self.db.exec(
                select(UserRole).where(
                    and_(
                        UserRole.user_id == self.user.id,
                        UserRole.study_id == study_id,
                        UserRole.is_active == True
                    )
                )
            ).first()
            
            if study_role:
                # Check if this role has the required permission
                role_perm = self.db.exec(
                    select(Permission).join(RolePermission).where(
                        and_(
                            RolePermission.role_id == study_role.role_id,
                            Permission.name == permission,
                            RolePermission.is_active == True
                        )
                    )
                ).first()
                
                if role_perm:
                    return True
        
        # Check general permission
        if permission:
            return self.has_permission(permission)
        
        return True


def require_permission(permission: Union[str, List[str]]):
    """
    Decorator to require specific permission(s) for an endpoint
    
    Usage:
        @router.get("/admin/users")
        @require_permission("user.view")
        def list_users(...):
            ...
        
        @router.post("/admin/users")
        @require_permission(["user.create", "user.manage_roles"])  # Requires ALL permissions
        def create_user(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get dependencies
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            
            if not db or not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies"
                )
            
            checker = PermissionChecker(db, current_user)
            
            # Check permissions
            if isinstance(permission, str):
                if not checker.has_permission(permission):
                    # Log unauthorized attempt
                    log_activity(
                        db=db,
                        user_id=current_user.id,
                        action="unauthorized_access",
                        resource_type="endpoint",
                        resource_id=None,
                        details={"endpoint": func.__name__, "required_permission": permission}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied. Required: {permission}"
                    )
            else:
                if not checker.has_all_permissions(permission):
                    # Log unauthorized attempt
                    log_activity(
                        db=db,
                        user_id=current_user.id,
                        action="unauthorized_access",
                        resource_type="endpoint",
                        resource_id=None,
                        details={"endpoint": func.__name__, "required_permissions": permission}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied. Required: {', '.join(permission)}"
                    )
            
            # Add checker to kwargs for use in endpoint
            kwargs['permission_checker'] = checker
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_permission(permissions: List[str]):
    """
    Decorator to require ANY of the specified permissions
    
    Usage:
        @router.get("/dashboards")
        @require_any_permission(["dashboard.view", "dashboard.create"])
        def list_dashboards(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get dependencies
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            
            if not db or not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies"
                )
            
            checker = PermissionChecker(db, current_user)
            
            if not checker.has_any_permission(permissions):
                # Log unauthorized attempt
                log_activity(
                    db=db,
                    user_id=current_user.id,
                    action="unauthorized_access",
                    resource_type="endpoint",
                    resource_id=None,
                    details={"endpoint": func.__name__, "required_any_permission": permissions}
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required any of: {', '.join(permissions)}"
                )
            
            # Add checker to kwargs
            kwargs['permission_checker'] = checker
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(role: Union[str, List[str]]):
    """
    Decorator to require specific role(s) for an endpoint
    
    Usage:
        @router.get("/admin/system")
        @require_role("system_admin")
        def system_settings(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get dependencies
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            
            if not db or not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies"
                )
            
            checker = PermissionChecker(db, current_user)
            
            # Check role
            if isinstance(role, str):
                if not checker.has_role(role):
                    # Log unauthorized attempt
                    log_activity(
                        db=db,
                        user_id=current_user.id,
                        action="unauthorized_access",
                        resource_type="endpoint",
                        resource_id=None,
                        details={"endpoint": func.__name__, "required_role": role}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied. Required role: {role}"
                    )
            else:
                if not checker.has_any_role(role):
                    # Log unauthorized attempt
                    log_activity(
                        db=db,
                        user_id=current_user.id,
                        action="unauthorized_access",
                        resource_type="endpoint",
                        resource_id=None,
                        details={"endpoint": func.__name__, "required_roles": role}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied. Required role: {', '.join(role)}"
                    )
            
            # Add checker to kwargs
            kwargs['permission_checker'] = checker
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_permission_checker(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PermissionChecker:
    """FastAPI dependency to get permission checker"""
    return PermissionChecker(db, current_user)


# Export commonly used permission sets
class Permissions:
    """Common permission sets for easy reference"""
    
    # Dashboard permissions
    DASHBOARD_VIEW = "dashboard.view"
    DASHBOARD_CREATE = "dashboard.create"
    DASHBOARD_EDIT = "dashboard.edit"
    DASHBOARD_DELETE = "dashboard.delete"
    DASHBOARD_SHARE = "dashboard.share"
    DASHBOARD_ALL = [DASHBOARD_VIEW, DASHBOARD_CREATE, DASHBOARD_EDIT, DASHBOARD_DELETE, DASHBOARD_SHARE]
    
    # Study permissions
    STUDY_VIEW = "study.view"
    STUDY_CREATE = "study.create"
    STUDY_EDIT = "study.edit"
    STUDY_DELETE = "study.delete"
    STUDY_INITIALIZE = "study.initialize"
    STUDY_ALL = [STUDY_VIEW, STUDY_CREATE, STUDY_EDIT, STUDY_DELETE, STUDY_INITIALIZE]
    
    # Data permissions
    DATA_VIEW = "data.view"
    DATA_UPLOAD = "data.upload"
    DATA_EXPORT = "data.export"
    DATA_DELETE = "data.delete"
    DATA_TRANSFORM = "data.transform"
    DATA_ALL = [DATA_VIEW, DATA_UPLOAD, DATA_EXPORT, DATA_DELETE, DATA_TRANSFORM]
    
    # User permissions
    USER_VIEW = "user.view"
    USER_CREATE = "user.create"
    USER_EDIT = "user.edit"
    USER_DELETE = "user.delete"
    USER_MANAGE_ROLES = "user.manage_roles"
    USER_ALL = [USER_VIEW, USER_CREATE, USER_EDIT, USER_DELETE, USER_MANAGE_ROLES]
    
    # RBAC permissions
    RBAC_VIEW = "rbac.view"
    RBAC_MANAGE = "rbac.manage"
    RBAC_ASSIGN = "rbac.assign"
    RBAC_ALL = [RBAC_VIEW, RBAC_MANAGE, RBAC_ASSIGN]
    
    # System permissions
    SYSTEM_VIEW = "system.view"
    SYSTEM_CONFIGURE = "system.configure"
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_RESTORE = "system.restore"
    SYSTEM_ALL = [SYSTEM_VIEW, SYSTEM_CONFIGURE, SYSTEM_BACKUP, SYSTEM_RESTORE]


class Roles:
    """Role constants for easy reference"""
    SYSTEM_ADMIN = "system_admin"
    ORG_ADMIN = "org_admin"
    STUDY_MANAGER = "study_manager"
    DATA_ANALYST = "data_analyst"
    VIEWER = "viewer"