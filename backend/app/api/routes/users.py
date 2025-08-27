import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import col, delete, func, select

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import (
    Item,
    Message,
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.utils import generate_new_account_email, send_email
from app.services.email.email_service import email_service
from app.models.organization import Organization
import asyncio

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users with organization data.
    """
    from app.models.organization import Organization
    from sqlalchemy.orm import selectinload

    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    # Load users with organization relationship
    statement = select(User).options(selectinload(User.organization)).offset(skip).limit(limit)
    users = session.exec(statement).all()
    
    # Enrich with organization data
    enriched_users = []
    for user in users:
        user_dict = {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "department": user.department,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "org_id": str(user.org_id) if user.org_id else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }
        
        # Add organization data
        if user.org_id:
            org = session.get(Organization, user.org_id)
            if org:
                user_dict["organization"] = {
                    "id": str(org.id),
                    "name": org.name
                }
        
        enriched_users.append(user_dict)

    return {"data": enriched_users, "count": count}


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
def create_user(*, session: SessionDep, user_in: UserCreate, current_user: CurrentUser) -> Any:
    """
    Create new user.
    """
    from app.models.activity_log import ActivityLog, ActivityAction
    from datetime import datetime
    
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = crud.create_user(session=session, user_create=user_in)
    
    # Log user creation with proper sequence number for 21 CFR Part 11
    # Get the next sequence number
    from sqlmodel import select, func
    
    max_seq_statement = select(func.coalesce(func.max(ActivityLog.sequence_number), 0))
    max_seq = session.exec(max_seq_statement).one()
    next_seq = max_seq + 1
    
    activity_log = ActivityLog(
        action=ActivityAction.CREATE,
        resource_type="user",
        resource_id=str(user.id),
        user_id=current_user.id,
        details={
            "created_user_email": user.email,
            "created_user_role": user.role,
            "created_by": current_user.email
        },
        timestamp=datetime.utcnow(),
        sequence_number=next_seq,
        org_id=user.org_id if user.org_id else None
    )
    session.add(activity_log)
    session.commit()
    
    # Send email using new email system
    if user_in.email and user_in.password:
        try:
            # Queue email using the new email service with template
            email_variables = {
                "user_name": user.full_name or user.email,
                "user_email": user.email,
                "temp_password": user_in.password,
                "user_role": user.role,
                "organization": session.get(Organization, user.org_id).name if user.org_id else "System",
                "created_by": current_user.full_name or current_user.email,
                "login_url": f"{settings.FRONTEND_HOST or 'http://localhost:3000'}/login"
            }
            
            # Use asyncio to run the async email queue function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            queue_id = loop.run_until_complete(
                email_service.queue_email(
                    to_email=user.email,
                    template_key="user_created",
                    variables=email_variables,
                    user_id=current_user.id,
                    priority=1
                )
            )
            loop.close()
            
            if queue_id:
                print(f"User creation email queued with ID: {queue_id}")
        except Exception as e:
            # Log error but don't fail user creation
            print(f"Failed to queue user creation email: {str(e)}")
            # Fall back to old email system if available
            if settings.emails_enabled:
                try:
                    email_data = generate_new_account_email(
                        email_to=user_in.email, username=user_in.email, password=user_in.password
                    )
                    send_email(
                        email_to=user_in.email,
                        subject=email_data.subject,
                        html_content=email_data.html_content,
                    )
                except Exception as old_e:
                    print(f"Old email system also failed: {str(old_e)}")
    
    return user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """

    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    from app.models.activity_log import ActivityLog, ActivityAction
    from datetime import datetime
    
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    
    # Log password change
    activity_log = ActivityLog(
        action=ActivityAction.PASSWORD_CHANGED,
        resource_type="user",
        resource_id=str(current_user.id),
        user_id=current_user.id,
        details={"email": current_user.email},
        timestamp=datetime.utcnow()
    )
    session.add(activity_log)
    session.commit()
    
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = crud.create_user(session=session, user_create=user_create)
    return user


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = session.get(User, user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
    current_user: CurrentUser,
) -> Any:
    """
    Update a user.
    """
    from app.models.activity_log import ActivityLog, ActivityAction
    from datetime import datetime

    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    # Track what changed
    old_values = {"email": db_user.email, "role": db_user.role, "is_active": db_user.is_active}
    
    db_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)
    
    # Log user update
    new_values = {"email": db_user.email, "role": db_user.role, "is_active": db_user.is_active}
    activity_log = ActivityLog(
        action=ActivityAction.UPDATE,
        resource_type="user",
        resource_id=str(user_id),
        user_id=current_user.id,
        old_value=old_values,
        new_value=new_values,
        details={
            "updated_by": current_user.email,
            "updated_user": db_user.email
        },
        timestamp=datetime.utcnow()
    )
    session.add(activity_log)
    session.commit()
    
    return db_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    from app.models.activity_log import ActivityLog, ActivityAction
    from datetime import datetime
    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    
    # Store user info before deletion
    deleted_user_info = {"email": user.email, "role": user.role}
    
    statement = delete(Item).where(col(Item.owner_id) == user_id)
    session.exec(statement)  # type: ignore
    session.delete(user)
    
    # Log user deletion
    activity_log = ActivityLog(
        action=ActivityAction.DELETE,
        resource_type="user",
        resource_id=str(user_id),
        user_id=current_user.id,
        details={
            "deleted_by": current_user.email,
            "deleted_user": deleted_user_info
        },
        timestamp=datetime.utcnow()
    )
    session.add(activity_log)
    session.commit()
    
    return Message(message="User deleted successfully")
