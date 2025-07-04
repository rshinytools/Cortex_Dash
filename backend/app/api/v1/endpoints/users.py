# ABOUTME: Enhanced user management endpoints with role support
# ABOUTME: Handles user CRUD with organization assignment and role management

from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select, and_
import uuid

from app.api.deps import get_db, get_current_user
from app.models import (
    User, UserCreate, UserUpdate, UserPublic,
    Message
)
from app.crud import organization as crud_org
from app.crud import activity_log as crud_activity
from app.core.permissions import (
    Permission, PermissionChecker, has_permission, Role
)
from app.core.security import get_password_hash

router = APIRouter()


@router.post("/", response_model=UserPublic)
async def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: User = Depends(PermissionChecker(Permission.MANAGE_ORG_USERS)),
    request: Request
) -> Any:
    """
    Create new user in organization. Requires MANAGE_ORG_USERS permission.
    """
    # Check if email already exists
    existing_user = db.exec(select(User).where(User.email == user_in.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Validate role
    if user_in.role not in [role.value for role in Role]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join([r.value for r in Role])}"
        )
    
    # Non-superusers can only create users in their own organization
    if not current_user.is_superuser:
        if user_in.org_id != current_user.org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create users in different organization"
            )
        # Org admins cannot create system admins
        if user_in.role == Role.SYSTEM_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only system admins can create other system admins"
            )
    
    # Check organization exists
    org = crud_org.get_organization(db, org_id=user_in.org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check organization user limit
    if not crud_org.check_organization_limits(db, org_id=user_in.org_id, resource="users"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization has reached maximum number of users"
        )
    
    # Create user
    db_user = User(
        **user_in.model_dump(exclude={"password"}),
        hashed_password=get_password_hash(user_in.password),
        created_at=datetime.utcnow(),
        created_by=current_user.id,
        updated_at=datetime.utcnow(),
        updated_by=current_user.id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="create_user",
        resource_type="user",
        resource_id=str(db_user.id),
        details={
            "email": db_user.email,
            "role": db_user.role,
            "org_id": str(db_user.org_id)
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return db_user


@router.get("/", response_model=List[UserPublic])
async def read_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: Optional[uuid.UUID] = None,
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve users. System admins see all, others see only their organization.
    """
    query = select(User)
    conditions = []
    
    # Filter by organization
    if current_user.is_superuser:
        if org_id:
            conditions.append(User.org_id == org_id)
    else:
        # Non-superusers only see their org
        conditions.append(User.org_id == current_user.org_id)
        # Must have permission to view users
        if not has_permission(current_user, Permission.MANAGE_ORG_USERS):
            # Users without manage permission only see themselves
            return [current_user]
    
    # Filter by role
    if role:
        conditions.append(User.role == role)
    
    # Filter active users only
    conditions.append(User.is_active == True)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.offset(skip).limit(limit)
    users = db.exec(query).all()
    
    return users


@router.get("/{user_id}", response_model=UserPublic)
async def read_user(
    *,
    db: Session = Depends(get_db),
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get user by ID.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if not current_user.is_superuser:
        # Users can view themselves
        if str(user_id) == str(current_user.id):
            return user
        # Must be in same org and have permission
        if str(user.org_id) != str(current_user.org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        if not has_permission(current_user, Permission.MANAGE_ORG_USERS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    return user


@router.patch("/{user_id}", response_model=UserPublic)
async def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: uuid.UUID,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    request: Request
) -> Any:
    """
    Update user.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    is_self = str(user_id) == str(current_user.id)
    
    if not current_user.is_superuser:
        # Users can update some of their own fields
        if is_self:
            # Restrict fields that users can update about themselves
            allowed_self_fields = {"full_name", "department", "preferences"}
            update_fields = set(user_in.model_dump(exclude_unset=True).keys())
            if not update_fields.issubset(allowed_self_fields):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot update restricted fields"
                )
        else:
            # Must be in same org and have permission
            if str(user.org_id) != str(current_user.org_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
            if not has_permission(current_user, Permission.MANAGE_ORG_USERS):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
            
            # Org admins cannot promote users to system admin
            if user_in.role == Role.SYSTEM_ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only system admins can create other system admins"
                )
    
    # Update user
    update_data = user_in.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by"] = current_user.id
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="update_user",
        resource_type="user",
        resource_id=str(user_id),
        details={
            "updated_fields": list(user_in.model_dump(exclude_unset=True).keys()),
            "is_self": is_self
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return user


@router.delete("/{user_id}", response_model=Message)
async def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    request: Request
) -> Any:
    """
    Delete (deactivate) user.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cannot delete yourself
    if str(user_id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Check permissions
    if not current_user.is_superuser:
        if str(user.org_id) != str(current_user.org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        if not has_permission(current_user, Permission.MANAGE_ORG_USERS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    # Deactivate user
    user.is_active = False
    user.updated_at = datetime.utcnow()
    user.updated_by = current_user.id
    db.add(user)
    db.commit()
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="delete_user",
        resource_type="user",
        resource_id=str(user_id),
        details={"email": user.email},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return {"message": "User deactivated successfully"}


@router.post("/{user_id}/reset-password", response_model=Message)
async def reset_user_password(
    *,
    db: Session = Depends(get_db),
    user_id: uuid.UUID,
    new_password: str,
    current_user: User = Depends(PermissionChecker(Permission.MANAGE_ORG_USERS)),
    request: Request
) -> Any:
    """
    Reset user password. Requires MANAGE_ORG_USERS permission.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check organization access
    if not current_user.is_superuser and str(user.org_id) != str(current_user.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update password
    user.hashed_password = get_password_hash(new_password)
    user.password_changed_at = datetime.utcnow()
    user.force_password_change = True  # Force user to change on next login
    user.updated_at = datetime.utcnow()
    user.updated_by = current_user.id
    
    db.add(user)
    db.commit()
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="reset_password",
        resource_type="user",
        resource_id=str(user_id),
        details={"forced_change": True},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return {"message": "Password reset successfully"}


# Import datetime
from datetime import datetime