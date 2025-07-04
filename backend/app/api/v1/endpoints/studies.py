# ABOUTME: API endpoints for study management
# ABOUTME: Handles CRUD operations for clinical studies with RBAC

from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session
import uuid

from app.api.deps import get_db, get_current_user
from app.models import (
    Study, StudyCreate, StudyUpdate, StudyPublic,
    User, Message
)
from app.crud import study as crud_study
from app.crud import organization as crud_org
from app.crud import activity_log as crud_activity
from app.core.permissions import (
    Permission, PermissionChecker, has_permission,
    require_study_access
)

router = APIRouter()


@router.post("/", response_model=StudyPublic)
async def create_study(
    *,
    db: Session = Depends(get_db),
    study_in: StudyCreate,
    current_user: User = Depends(PermissionChecker(Permission.CREATE_STUDY)),
    request: Request
) -> Any:
    """
    Create new study. User must have CREATE_STUDY permission.
    """
    # Check if organization exists and user has access
    org = crud_org.get_organization(db, org_id=study_in.org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check organization access
    if not current_user.is_superuser and str(current_user.org_id) != str(study_in.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create study in different organization"
        )
    
    # Check organization limits
    if not crud_org.check_organization_limits(db, org_id=study_in.org_id, resource="studies"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization has reached maximum number of studies"
        )
    
    # Check if protocol number is unique
    if crud_study.get_study_by_protocol(db, protocol_number=study_in.protocol_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Study with this protocol number already exists"
        )
    
    study = await crud_study.create_study(db, study_create=study_in, current_user=current_user)
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="create_study",
        resource_type="study",
        resource_id=str(study.id),
        details={
            "name": study.name,
            "protocol_number": study.protocol_number,
            "org_id": str(study.org_id)
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return study


@router.get("/", response_model=List[StudyPublic])
async def read_studies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve studies. Users see studies based on their permissions.
    """
    # System admins can filter by org_id
    if current_user.is_superuser and org_id:
        studies = crud_study.get_studies(db, org_id=org_id, skip=skip, limit=limit)
    else:
        # Regular users see their organization's studies
        studies = crud_study.get_user_studies(db, user=current_user, skip=skip, limit=limit)
    
    return studies


@router.get("/{study_id}", response_model=StudyPublic)
async def read_study(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get study by ID.
    """
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if not has_permission(current_user, Permission.VIEW_STUDY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view study"
        )
    
    return study


@router.patch("/{study_id}", response_model=StudyPublic)
async def update_study(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    study_in: StudyUpdate,
    current_user: User = Depends(PermissionChecker(Permission.EDIT_STUDY)),
    request: Request
) -> Any:
    """
    Update study.
    """
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    study = crud_study.update_study(
        db, study_id=study_id, study_update=study_in, current_user=current_user
    )
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="update_study",
        resource_type="study",
        resource_id=str(study.id),
        details={"updated_fields": list(study_in.model_dump(exclude_unset=True).keys())},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return study


@router.delete("/{study_id}", response_model=Message)
async def delete_study(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    current_user: User = Depends(PermissionChecker(Permission.DELETE_STUDY)),
    request: Request
) -> Any:
    """
    Delete (archive) study.
    """
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    success = crud_study.delete_study(db, study_id=study_id)
    
    if success:
        # Log activity
        crud_activity.create_activity_log(
            db,
            user=current_user,
            action="delete_study",
            resource_type="study",
            resource_id=str(study_id),
            details={"name": study.name, "protocol_number": study.protocol_number},
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        return {"message": "Study archived successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to archive study"
        )


@router.get("/{study_id}/stats", response_model=dict)
async def get_study_statistics(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get study statistics.
    """
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if not has_permission(current_user, Permission.VIEW_STUDY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view study statistics"
        )
    
    return crud_study.get_study_statistics(db, study_id=study_id)


# Import Optional
from typing import Optional