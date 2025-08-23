from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from app import crud
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import Message, NewPassword, Token, UserPublic
from app.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)

router = APIRouter(tags=["login"])


@router.post("/login/access-token")
def login_access_token(
    session: SessionDep, 
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    request: Any = None
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    from fastapi import Request
    from datetime import datetime
    from app.crud import activity_log as crud_activity
    
    # Get IP address and user agent if request is available
    ip_address = None
    user_agent = None
    if request and isinstance(request, Request):
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
    
    user = crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Log successful login - keep this as it's a special authentication event
    from app.crud import activity_log as crud_activity
    try:
        crud_activity.create_activity_log(
            db=session,
            user=user,
            action="LOGIN",
            resource_type="authentication",
            resource_id=str(user.id),
            details={"email": user.email, "role": user.role},
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # Log error but don't fail login
        print(f"Failed to log activity: {e}")
    
    # Update last login time
    user.last_login = datetime.utcnow()
    session.add(user)
    session.commit()
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=7)
    
    # Create tokens
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    refresh_token = security.create_refresh_token(
        user.id, expires_delta=refresh_token_expires
    )
    
    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # Security: Use secure cookie in production
        samesite="strict",  # Security: Prevent CSRF attacks
        max_age=7 * 24 * 60 * 60,  # 7 days in seconds
        path="/"
    )
    
    return Token(
        access_token=access_token
    )


@router.post("/login/refresh-token")
def refresh_access_token(
    session: SessionDep,
    response: Response,
    request: Request
) -> Token:
    """
    Refresh access token using httpOnly refresh token cookie
    """
    # Security: Get refresh token from httpOnly cookie
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found")
    
    # Verify refresh token
    user_id = security.verify_refresh_token(refresh_token)
    
    if not user_id:
        # Security: Clear invalid refresh token
        response.delete_cookie("refresh_token")
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # Get user
    user = crud.get_user(session=session, user_id=user_id)
    
    if not user or not user.is_active:
        response.delete_cookie("refresh_token")
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    
    # Optionally rotate refresh token for extra security
    refresh_token_expires = timedelta(days=7)
    new_refresh_token = security.create_refresh_token(
        user.id, expires_delta=refresh_token_expires
    )
    
    # Set new refresh token
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )
    
    return Token(access_token=access_token)


@router.post("/logout")
def logout(
    session: SessionDep,
    current_user: CurrentUser,
    response: Response,
    request: Request
) -> Message:
    """
    Logout the current user
    """
    from app.crud import activity_log as crud_activity
    
    # Log the logout
    try:
        crud_activity.create_activity_log(
            db=session,
            user=current_user,
            action="LOGOUT",
            resource_type="authentication",
            resource_id=str(current_user.id),
            details={"email": current_user.email, "role": current_user.role},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception as e:
        # Log error but don't fail logout
        print(f"Failed to log logout activity: {e}")
    
    # Security: Clear refresh token cookie
    response.delete_cookie("refresh_token")
    
    return Message(message="Logged out successfully")


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}")
def recover_password(email: str, session: SessionDep) -> Message:
    """
    Password Recovery
    """
    user = crud.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    send_email(
        email_to=user.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Password recovery email sent")


@router.post("/reset-password/")
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = crud.get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = get_password_hash(password=body.new_password)
    user.hashed_password = hashed_password
    session.add(user)
    session.commit()
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
)
def recover_password_html_content(email: str, session: SessionDep) -> Any:
    """
    HTML Content for Password Recovery
    """
    user = crud.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )

    return HTMLResponse(
        content=email_data.html_content, headers={"subject:": email_data.subject}
    )
