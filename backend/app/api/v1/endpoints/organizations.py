# ABOUTME: API endpoints for organization management
# ABOUTME: Handles CRUD operations for organizations with RBAC

from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session
import uuid

from app.api.deps import get_db, get_current_user
from app.models import (
    Organization, OrganizationCreate, OrganizationUpdate, OrganizationPublic,
    User, Message
)
from app.crud import organization as crud_org
from app.crud import activity_log as crud_activity
from app.core.permissions import (
    Permission, PermissionChecker, has_permission
)

router = APIRouter()


@router.post("/", response_model=OrganizationPublic)
async def create_organization(
    *,
    db: Session = Depends(get_db),
    org_in: OrganizationCreate,
    current_user: User = Depends(PermissionChecker(Permission.MANAGE_SYSTEM)),
    request: Request
) -> Any:
    """
    Create new organization. Only system admins can create organizations.
    """
    # Check if organization with same slug exists
    if crud_org.get_organization_by_slug(db, slug=org_in.slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this slug already exists"
        )
    
    org = crud_org.create_organization(db, org_create=org_in)
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="create_organization",
        resource_type="organization",
        resource_id=str(org.id),
        details={"name": org.name, "slug": org.slug},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return org


@router.get("/", response_model=List[OrganizationPublic])
async def read_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve organizations. System admins see all, others see only their own.
    """
    if current_user.is_superuser:
        organizations = crud_org.get_organizations(db, skip=skip, limit=limit)
    else:
        # Non-admins only see their own organization
        org = crud_org.get_organization(db, org_id=current_user.org_id)
        organizations = [org] if org else []
    
    return organizations


@router.get("/{org_id}", response_model=OrganizationPublic)
async def read_organization(
    *,
    db: Session = Depends(get_db),
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get organization by ID.
    """
    org = crud_org.get_organization(db, org_id=org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return org


@router.patch("/{org_id}", response_model=OrganizationPublic)
async def update_organization(
    *,
    db: Session = Depends(get_db),
    org_id: uuid.UUID,
    org_in: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    request: Request
) -> Any:
    """
    Update organization.
    """
    org = crud_org.get_organization(db, org_id=org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check permissions
    if not current_user.is_superuser:
        if str(current_user.org_id) != str(org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        if not has_permission(current_user, Permission.MANAGE_ORG_SETTINGS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to manage organization settings"
            )
    
    org = crud_org.update_organization(db, org_id=org_id, org_update=org_in)
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="update_organization",
        resource_type="organization",
        resource_id=str(org.id),
        details={"updated_fields": list(org_in.model_dump(exclude_unset=True).keys())},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return org


@router.delete("/{org_id}", response_model=Message)
async def delete_organization(
    *,
    db: Session = Depends(get_db),
    org_id: uuid.UUID,
    current_user: User = Depends(PermissionChecker(Permission.MANAGE_SYSTEM)),
    request: Request
) -> Any:
    """
    Delete organization. Only system admins can delete organizations.
    """
    org = crud_org.get_organization(db, org_id=org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check if organization has users or studies
    user_count = crud_org.get_organization_user_count(db, org_id=org_id)
    study_count = crud_org.get_organization_study_count(db, org_id=org_id)
    
    if user_count > 0 or study_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete organization with {user_count} users and {study_count} studies"
        )
    
    success = crud_org.delete_organization(db, org_id=org_id)
    
    if success:
        # Log activity
        crud_activity.create_activity_log(
            db,
            user=current_user,
            action="delete_organization",
            resource_type="organization",
            resource_id=str(org_id),
            details={"name": org.name},
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        return {"message": "Organization deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete organization"
        )


@router.get("/{org_id}/stats", response_model=dict)
async def get_organization_stats(
    *,
    db: Session = Depends(get_db),
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get organization statistics.
    """
    org = crud_org.get_organization(db, org_id=org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return {
        "organization_id": str(org.id),
        "name": org.name,
        "user_count": crud_org.get_organization_user_count(db, org_id=org_id),
        "study_count": crud_org.get_organization_study_count(db, org_id=org_id),
        "max_users": org.max_users,
        "max_studies": org.max_studies,
        "license_type": org.license_type,
        "active": org.active
    }