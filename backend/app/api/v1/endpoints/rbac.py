# ABOUTME: RBAC management API endpoints for dynamic permission control
# ABOUTME: Allows System Admin to manage roles, permissions, and assignments

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user, get_current_active_superuser
from app.models.user import User
from app.models.rbac import (
    Permission, Role, RolePermission, UserRole,
    PermissionPreset, PermissionAuditLog
)
from app.services.rbac.permission_service import PermissionService

router = APIRouter()


# Request/Response Models
class PermissionCreate(BaseModel):
    name: str
    resource: str
    action: str
    description: Optional[str] = None


class PermissionResponse(BaseModel):
    id: UUID
    name: str
    resource: str
    action: str
    description: Optional[str]
    is_system: bool
    created_at: datetime


class RoleResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: Optional[str]
    is_system: bool
    is_active: bool
    permission_count: Optional[int] = 0


class RolePermissionUpdate(BaseModel):
    permissions: List[str]  # List of permission names


class UserRoleAssign(BaseModel):
    user_id: UUID
    role_name: str
    organization_id: Optional[UUID] = None
    study_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None


class PermissionGrantRequest(BaseModel):
    permission_name: str
    conditions: Optional[Dict[str, Any]] = None


class PermissionMatrixResponse(BaseModel):
    roles: List[str]
    permissions: List[str]
    matrix: Dict[str, Dict[str, bool]]


# Permission Endpoints
@router.get("/permissions", response_model=List[PermissionResponse])
def list_permissions(
    resource: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all available permissions"""
    query = select(Permission)
    
    if resource:
        query = query.where(Permission.resource == resource)
    
    permissions = db.execute(query.order_by(Permission.resource, Permission.action)).scalars().all()
    
    return [
        PermissionResponse(
            id=p.id,
            name=p.name,
            resource=p.resource,
            action=p.action,
            description=p.description,
            is_system=p.is_system,
            created_at=p.created_at
        )
        for p in permissions
    ]


@router.post("/permissions", response_model=PermissionResponse)
def create_permission(
    permission_data: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """Create a custom permission (System Admin only)"""
    service = PermissionService(db)
    
    try:
        permission = service.create_custom_permission(
            name=permission_data.name,
            resource=permission_data.resource,
            action=permission_data.action,
            description=permission_data.description,
            created_by=current_user.id
        )
        
        return PermissionResponse(
            id=permission.id,
            name=permission.name,
            resource=permission.resource,
            action=permission.action,
            description=permission.description,
            is_system=permission.is_system,
            created_at=permission.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Role Endpoints
@router.get("/roles", response_model=List[RoleResponse])
def list_roles(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all roles"""
    query = select(Role)
    
    if not include_inactive:
        query = query.where(Role.is_active == True)
    
    roles = db.execute(query.order_by(Role.name)).scalars().all()
    
    responses = []
    for role in roles:
        # Count permissions
        permission_count = db.execute(
            select(RolePermission).where(
                and_(
                    RolePermission.role_id == role.id,
                    RolePermission.is_active == True
                )
            )
        ).scalars().all()
        
        responses.append(
            RoleResponse(
                id=role.id,
                name=role.name,
                display_name=role.display_name,
                description=role.description,
                is_system=role.is_system,
                is_active=role.is_active,
                permission_count=len(permission_count)
            )
        )
    
    return responses


@router.get("/roles/{role_id}/permissions", response_model=List[PermissionResponse])
def get_role_permissions(
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all permissions for a role"""
    service = PermissionService(db)
    permissions = service.get_role_permissions(role_id)
    
    return [
        PermissionResponse(
            id=p.id,
            name=p.name,
            resource=p.resource,
            action=p.action,
            description=p.description,
            is_system=p.is_system,
            created_at=p.created_at
        )
        for p in permissions
    ]


@router.put("/roles/{role_id}/permissions")
def update_role_permissions(
    role_id: UUID,
    update_data: RolePermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """Update all permissions for a role (System Admin only)"""
    service = PermissionService(db)
    
    # Get current permissions
    current_permissions = service.get_role_permissions(role_id)
    current_permission_names = {p.name for p in current_permissions}
    
    # Calculate changes
    new_permission_names = set(update_data.permissions)
    to_grant = new_permission_names - current_permission_names
    to_revoke = current_permission_names - new_permission_names
    
    # Apply changes
    for permission_name in to_grant:
        try:
            service.grant_permission_to_role(
                role_id=role_id,
                permission_name=permission_name,
                granted_by=current_user.id
            )
        except HTTPException:
            pass  # Skip if already exists
    
    for permission_name in to_revoke:
        service.revoke_permission_from_role(
            role_id=role_id,
            permission_name=permission_name,
            revoked_by=current_user.id
        )
    
    return {
        "message": "Permissions updated successfully",
        "granted": list(to_grant),
        "revoked": list(to_revoke)
    }


@router.post("/roles/{role_id}/grant")
def grant_permission(
    role_id: UUID,
    request: PermissionGrantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """Grant a specific permission to a role"""
    from app.models.activity_log import ActivityLog, ActivityAction
    
    service = PermissionService(db)
    
    try:
        role_permission = service.grant_permission_to_role(
            role_id=role_id,
            permission_name=request.permission_name,
            granted_by=current_user.id,
            conditions=request.conditions
        )
        
        # Get role details
        role = db.get(Role, role_id)
        
        # Log permission grant
        activity_log = ActivityLog(
            action="grant",
            resource_type="permission",
            resource_id=str(role_permission.id),
            user_id=current_user.id,
            details={
                "permission": request.permission_name,
                "role": role.name if role else str(role_id),
                "granted_by": current_user.email
            },
            timestamp=datetime.utcnow()
        )
        db.add(activity_log)
        db.commit()
        
        return {
            "message": f"Permission '{request.permission_name}' granted successfully",
            "role_permission_id": role_permission.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/roles/{role_id}/revoke/{permission_name}")
def revoke_permission(
    role_id: UUID,
    permission_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """Revoke a specific permission from a role"""
    from app.models.activity_log import ActivityLog, ActivityAction
    
    service = PermissionService(db)
    
    # Get role details before revoking
    role = db.get(Role, role_id)
    
    success = service.revoke_permission_from_role(
        role_id=role_id,
        permission_name=permission_name,
        revoked_by=current_user.id
    )
    
    if success:
        # Log permission revoke
        activity_log = ActivityLog(
            action="revoke",
            resource_type="permission",
            resource_id=str(role_id),
            user_id=current_user.id,
            details={
                "permission": permission_name,
                "role": role.name if role else str(role_id),
                "revoked_by": current_user.email
            },
            timestamp=datetime.utcnow()
        )
        db.add(activity_log)
        db.commit()
        
        return {"message": f"Permission '{permission_name}' revoked successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found for this role"
        )


# User Role Assignment Endpoints
@router.post("/users/assign-role")
def assign_role_to_user(
    assignment: UserRoleAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a role to a user"""
    from app.models.activity_log import ActivityLog, ActivityAction
    
    service = PermissionService(db)
    
    # Check if assigning system_admin role
    if assignment.role_name == "system_admin" and not service.is_system_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only system administrators can assign the system_admin role"
        )
    
    try:
        user_role = service.assign_role_to_user(
            user_id=assignment.user_id,
            role_name=assignment.role_name,
            assigned_by=current_user.id,
            organization_id=assignment.organization_id,
            study_id=assignment.study_id,
            expires_at=assignment.expires_at
        )
        
        # Get user details
        assigned_user = db.get(User, assignment.user_id)
        
        # Log role assignment
        activity_log = ActivityLog(
            action="grant",
            resource_type="role",
            resource_id=str(assignment.user_id),
            user_id=current_user.id,
            details={
                "role": assignment.role_name,
                "assigned_to": assigned_user.email if assigned_user else str(assignment.user_id),
                "assigned_by": current_user.email,
                "organization_id": str(assignment.organization_id) if assignment.organization_id else None,
                "study_id": str(assignment.study_id) if assignment.study_id else None
            },
            timestamp=datetime.utcnow()
        )
        db.add(activity_log)
        db.commit()
        
        return {
            "message": f"Role '{assignment.role_name}' assigned successfully",
            "user_role_id": user_role.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/users/{user_id}/remove-role/{role_name}")
def remove_role_from_user(
    user_id: UUID,
    role_name: str,
    organization_id: Optional[UUID] = Query(None),
    study_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a role from a user"""
    service = PermissionService(db)
    
    # Check if removing system_admin role
    if role_name == "system_admin" and not service.is_system_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only system administrators can remove the system_admin role"
        )
    
    success = service.remove_role_from_user(
        user_id=user_id,
        role_name=role_name,
        removed_by=current_user.id,
        organization_id=organization_id,
        study_id=study_id
    )
    
    if success:
        return {"message": f"Role '{role_name}' removed successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role assignment not found"
        )


@router.get("/users/{user_id}/roles")
def get_user_roles(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all roles assigned to a user"""
    service = PermissionService(db)
    user_roles = service.get_user_roles(user_id)
    
    results = []
    for user_role in user_roles:
        role = db.get(Role, user_role.role_id)
        results.append({
            "role_name": role.name,
            "display_name": role.display_name,
            "organization_id": user_role.organization_id,
            "study_id": user_role.study_id,
            "assigned_at": user_role.assigned_at,
            "expires_at": user_role.expires_at
        })
    
    return results


@router.get("/users/{user_id}/permissions")
def get_user_permissions_list(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all effective permissions for a user"""
    service = PermissionService(db)
    permissions = service.get_user_permissions(user_id)
    
    return {
        "user_id": user_id,
        "permissions": sorted(list(permissions))
    }


# Current User Endpoints
@router.get("/my-permissions")
def get_my_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's permissions"""
    service = PermissionService(db)
    permissions = service.get_user_permissions(current_user.id)
    
    return {
        "user_id": current_user.id,
        "permissions": sorted(list(permissions)),
        "is_system_admin": service.is_system_admin(current_user)
    }


@router.get("/my-roles")
def get_my_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's roles"""
    service = PermissionService(db)
    user_roles = service.get_user_roles(current_user.id)
    
    results = []
    for user_role in user_roles:
        role = db.get(Role, user_role.role_id)
        results.append({
            "role_name": role.name,
            "display_name": role.display_name,
            "organization_id": user_role.organization_id,
            "study_id": user_role.study_id,
            "assigned_at": user_role.assigned_at,
            "expires_at": user_role.expires_at
        })
    
    return results


# Permission Matrix
@router.get("/permission-matrix", response_model=PermissionMatrixResponse)
def get_permission_matrix(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """Get permission matrix showing all roles and their permissions"""
    service = PermissionService(db)
    
    # Get all roles and permissions
    roles = db.execute(select(Role).where(Role.is_active == True)).scalars().all()
    permissions = db.execute(select(Permission)).scalars().all()
    
    # Build matrix
    matrix = {}
    for role in roles:
        role_permissions = service.get_role_permissions(role.id)
        role_permission_names = {p.name for p in role_permissions}
        
        matrix[role.name] = {}
        for permission in permissions:
            matrix[role.name][permission.name] = permission.name in role_permission_names
    
    return PermissionMatrixResponse(
        roles=[r.name for r in roles],
        permissions=[p.name for p in permissions],
        matrix=matrix
    )


# Initialize Default Permissions
@router.post("/initialize-defaults")
def initialize_default_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """Initialize default permissions and roles (System Admin only)"""
    service = PermissionService(db)
    service.initialize_default_permissions()
    
    return {"message": "Default permissions and roles initialized successfully"}