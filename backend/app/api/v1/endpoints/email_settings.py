# ABOUTME: API endpoints for managing email settings, templates, and sending emails
# ABOUTME: Provides CRUD operations and testing functionality for email system

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from sqlmodel import Session, select
from pydantic import BaseModel, EmailStr

from app.api.deps import get_current_active_superuser, get_current_user, SessionDep
from app.models import User
from app.models.email_settings import (
    EmailSettings, EmailTemplate, EmailQueue,
    EmailHistory, UserEmailPreferences,
    EmailStatus, DigestFrequency
)
from app.core.encryption import encryption_service
from app.services.email.email_service import email_service

router = APIRouter()


# Request/Response Models
class EmailSettingsCreate(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: EmailStr
    smtp_from_name: Optional[str] = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_timeout: int = 30
    test_recipient_email: Optional[EmailStr] = None
    max_retries: int = 3
    retry_delay: int = 300
    rate_limit: Optional[int] = None


class EmailSettingsUpdate(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[EmailStr] = None
    smtp_from_name: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    smtp_use_ssl: Optional[bool] = None
    smtp_timeout: Optional[int] = None
    test_recipient_email: Optional[EmailStr] = None
    max_retries: Optional[int] = None
    retry_delay: Optional[int] = None
    rate_limit: Optional[int] = None
    is_active: Optional[bool] = None


class EmailSettingsResponse(BaseModel):
    id: UUID
    smtp_host: str
    smtp_port: int
    smtp_username: Optional[str]
    smtp_from_email: str
    smtp_from_name: Optional[str]
    smtp_use_tls: bool
    smtp_use_ssl: bool
    smtp_timeout: int
    is_active: bool
    test_recipient_email: Optional[str]
    max_retries: int
    retry_delay: int
    rate_limit: Optional[int]
    created_at: datetime
    updated_at: datetime


class EmailTemplateCreate(BaseModel):
    template_key: str
    template_name: str
    subject: str
    html_template: str
    plain_text_template: Optional[str] = None
    variables: Dict[str, Any] = {}
    category: str = "system"
    is_active: bool = True


class EmailTemplateUpdate(BaseModel):
    template_name: Optional[str] = None
    subject: Optional[str] = None
    html_template: Optional[str] = None
    plain_text_template: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class TestEmailRequest(BaseModel):
    to_email: EmailStr
    test_connection: bool = True


class SendEmailRequest(BaseModel):
    to_email: EmailStr
    template_key: str
    variables: Dict[str, Any] = {}
    priority: int = 5
    scheduled_at: Optional[datetime] = None


class UserPreferencesUpdate(BaseModel):
    receive_account_updates: Optional[bool] = None
    receive_study_updates: Optional[bool] = None
    receive_data_updates: Optional[bool] = None
    receive_system_alerts: Optional[bool] = None
    receive_backup_notifications: Optional[bool] = None
    receive_audit_reports: Optional[bool] = None
    receive_security_alerts: Optional[bool] = None
    receive_pipeline_updates: Optional[bool] = None
    receive_collaboration_invites: Optional[bool] = None
    receive_marketing: Optional[bool] = None
    digest_frequency: Optional[DigestFrequency] = None
    timezone: Optional[str] = None
    language_code: Optional[str] = None


# Email Settings Endpoints
@router.get("/settings", response_model=EmailSettingsResponse)
async def get_email_settings(
    session: SessionDep,
    current_user: User = Depends(get_current_active_superuser)
):
    """Get current active email settings"""
    statement = select(EmailSettings).where(EmailSettings.is_active == True)
    settings = session.exec(statement).first()
    
    if not settings:
        raise HTTPException(status_code=404, detail="No active email settings found")
    
    # Don't return encrypted password
    return EmailSettingsResponse(
        id=settings.id,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_from_email=settings.smtp_from_email,
        smtp_from_name=settings.smtp_from_name,
        smtp_use_tls=settings.smtp_use_tls,
        smtp_use_ssl=settings.smtp_use_ssl,
        smtp_timeout=settings.smtp_timeout,
        is_active=settings.is_active,
        test_recipient_email=settings.test_recipient_email,
        max_retries=settings.max_retries,
        retry_delay=settings.retry_delay,
        rate_limit=settings.rate_limit,
        created_at=settings.created_at,
        updated_at=settings.updated_at
    )


@router.post("/settings", response_model=EmailSettingsResponse)
async def create_email_settings(
    settings_data: EmailSettingsCreate,
    session: SessionDep,
    current_user: User = Depends(get_current_active_superuser)
):
    """Create new email settings configuration"""
    
    # Deactivate any existing active settings
    statement = select(EmailSettings).where(EmailSettings.is_active == True)
    existing = session.exec(statement).all()
    for setting in existing:
        setting.is_active = False
        session.add(setting)
    
    # Create new settings
    settings = EmailSettings(
        **settings_data.model_dump(exclude={"smtp_password"}),
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        updated_by=current_user.id
    )
    
    # Encrypt password if provided
    if settings_data.smtp_password:
        settings.smtp_password = encryption_service.encrypt(settings_data.smtp_password)
    
    session.add(settings)
    session.commit()
    session.refresh(settings)
    
    return EmailSettingsResponse(
        id=settings.id,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_from_email=settings.smtp_from_email,
        smtp_from_name=settings.smtp_from_name,
        smtp_use_tls=settings.smtp_use_tls,
        smtp_use_ssl=settings.smtp_use_ssl,
        smtp_timeout=settings.smtp_timeout,
        is_active=settings.is_active,
        test_recipient_email=settings.test_recipient_email,
        max_retries=settings.max_retries,
        retry_delay=settings.retry_delay,
        rate_limit=settings.rate_limit,
        created_at=settings.created_at,
        updated_at=settings.updated_at
    )


@router.put("/settings/{settings_id}", response_model=EmailSettingsResponse)
async def update_email_settings(
    settings_id: UUID,
    settings_update: EmailSettingsUpdate,
    session: SessionDep,
    current_user: User = Depends(get_current_active_superuser)
):
    """Update existing email settings"""
    
    settings = session.get(EmailSettings, settings_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Email settings not found")
    
    update_data = settings_update.model_dump(exclude_unset=True)
    
    # Handle password specially
    if "smtp_password" in update_data:
        if update_data["smtp_password"]:
            # Encrypt password if provided
            update_data["smtp_password"] = encryption_service.encrypt(update_data["smtp_password"])
        else:
            # Don't update password if empty string provided - keep existing
            del update_data["smtp_password"]
    
    for key, value in update_data.items():
        setattr(settings, key, value)
    
    settings.updated_at = datetime.utcnow()
    settings.updated_by = current_user.id
    
    session.add(settings)
    session.commit()
    session.refresh(settings)
    
    return EmailSettingsResponse(
        id=settings.id,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_from_email=settings.smtp_from_email,
        smtp_from_name=settings.smtp_from_name,
        smtp_use_tls=settings.smtp_use_tls,
        smtp_use_ssl=settings.smtp_use_ssl,
        smtp_timeout=settings.smtp_timeout,
        is_active=settings.is_active,
        test_recipient_email=settings.test_recipient_email,
        max_retries=settings.max_retries,
        retry_delay=settings.retry_delay,
        rate_limit=settings.rate_limit,
        created_at=settings.created_at,
        updated_at=settings.updated_at
    )


@router.post("/settings/test")
async def test_email_settings(
    test_request: TestEmailRequest,
    session: SessionDep,
    current_user: User = Depends(get_current_active_superuser)
):
    """Test email configuration by sending a test email"""
    
    # Test SMTP connection first if requested
    if test_request.test_connection:
        connection_result = await email_service.test_smtp_connection()
        if not connection_result["success"]:
            return {
                "success": False,
                "connection_test": connection_result,
                "email_sent": False
            }
    
    # Send test email
    email_result = await email_service.send_test_email(test_request.to_email)
    
    return {
        "success": email_result["success"],
        "connection_test": connection_result if test_request.test_connection else None,
        "email_sent": email_result["success"],
        "details": email_result
    }


# Email Template Endpoints
@router.get("/templates", response_model=List[EmailTemplate])
async def list_email_templates(
    session: SessionDep,
    current_user: User = Depends(get_current_active_superuser),
    category: Optional[str] = None,
    is_active: Optional[bool] = True
):
    """List all email templates"""
    
    statement = select(EmailTemplate)
    if category:
        statement = statement.where(EmailTemplate.category == category)
    if is_active is not None:
        statement = statement.where(EmailTemplate.is_active == is_active)
    
    templates = session.exec(statement).all()
    return templates


@router.get("/templates/{template_key}", response_model=EmailTemplate)
async def get_email_template(
    template_key: str,
    session: SessionDep,
    current_user: User = Depends(get_current_active_superuser)
):
    """Get specific email template by key"""
    
    statement = select(EmailTemplate).where(EmailTemplate.template_key == template_key)
    template = session.exec(statement).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


@router.post("/templates", response_model=EmailTemplate)
async def create_email_template(
    template_data: EmailTemplateCreate,
    session: SessionDep,
    current_user: User = Depends(get_current_active_superuser)
):
    """Create new email template"""
    
    # Check if template key already exists
    statement = select(EmailTemplate).where(EmailTemplate.template_key == template_data.template_key)
    existing = session.exec(statement).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Template key already exists")
    
    template = EmailTemplate(
        **template_data.model_dump(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        updated_by=current_user.id,
        version=1
    )
    
    session.add(template)
    session.commit()
    session.refresh(template)
    
    return template


@router.put("/templates/{template_key}", response_model=EmailTemplate)
async def update_email_template(
    template_key: str,
    template_update: EmailTemplateUpdate,
    session: SessionDep,
    current_user: User = Depends(get_current_active_superuser)
):
    """Update existing email template"""
    
    statement = select(EmailTemplate).where(EmailTemplate.template_key == template_key)
    template = session.exec(statement).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if template.is_system:
        raise HTTPException(status_code=403, detail="Cannot modify system templates")
    
    update_data = template_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(template, key, value)
    
    template.updated_at = datetime.utcnow()
    template.updated_by = current_user.id
    template.version += 1
    
    session.add(template)
    session.commit()
    session.refresh(template)
    
    return template


# Email Sending Endpoints
@router.post("/send")
async def send_email(
    email_request: SendEmailRequest,
    background_tasks: BackgroundTasks,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """Queue an email for sending"""
    
    try:
        queue_id = await email_service.queue_email(
            to_email=email_request.to_email,
            template_key=email_request.template_key,
            variables=email_request.variables,
            user_id=current_user.id,
            priority=email_request.priority,
            scheduled_at=email_request.scheduled_at
        )
        
        # Process queue in background if not scheduled
        if not email_request.scheduled_at:
            background_tasks.add_task(email_service.process_queue)
        
        return {
            "success": True,
            "queue_id": queue_id,
            "message": "Email queued successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Email History Endpoints
@router.get("/history")
async def get_email_history(
    session: SessionDep,
    current_user: User = Depends(get_current_active_superuser),
    recipient_email: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """Get email history with optional filters"""
    
    statement = select(EmailHistory).order_by(EmailHistory.created_at.desc())
    
    if recipient_email:
        statement = statement.where(EmailHistory.recipient_email == recipient_email)
    if status:
        statement = statement.where(EmailHistory.status == status)
    
    statement = statement.limit(limit)
    
    history = session.exec(statement).all()
    return history


# User Email Preferences
@router.get("/preferences/me", response_model=UserEmailPreferences)
async def get_my_email_preferences(
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """Get current user's email preferences"""
    
    statement = select(UserEmailPreferences).where(UserEmailPreferences.user_id == current_user.id)
    preferences = session.exec(statement).first()
    
    if not preferences:
        # Create default preferences
        preferences = UserEmailPreferences(
            user_id=current_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(preferences)
        session.commit()
        session.refresh(preferences)
    
    return preferences


@router.put("/preferences/me", response_model=UserEmailPreferences)
async def update_my_email_preferences(
    preferences_update: UserPreferencesUpdate,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    """Update current user's email preferences"""
    
    statement = select(UserEmailPreferences).where(UserEmailPreferences.user_id == current_user.id)
    preferences = session.exec(statement).first()
    
    if not preferences:
        preferences = UserEmailPreferences(
            user_id=current_user.id,
            created_at=datetime.utcnow()
        )
    
    update_data = preferences_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(preferences, key, value)
    
    preferences.updated_at = datetime.utcnow()
    
    session.add(preferences)
    session.commit()
    session.refresh(preferences)
    
    return preferences


# Email Queue Management
@router.get("/queue")
async def get_email_queue(
    session: SessionDep,
    current_user: User = Depends(get_current_active_superuser),
    status: Optional[EmailStatus] = None,
    limit: int = 100
):
    """Get emails in queue with optional status filter"""
    
    statement = select(EmailQueue).order_by(EmailQueue.priority, EmailQueue.created_at)
    
    if status:
        statement = statement.where(EmailQueue.status == status)
    
    statement = statement.limit(limit)
    
    queue_items = session.exec(statement).all()
    return queue_items


@router.post("/queue/{queue_id}/retry")
async def retry_email(
    queue_id: UUID,
    background_tasks: BackgroundTasks,
    session: SessionDep,
    current_user: User = Depends(get_current_active_superuser)
):
    """Retry a failed email"""
    
    queue_item = session.get(EmailQueue, queue_id)
    
    if not queue_item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    # Reset status and schedule for immediate retry
    queue_item.status = EmailStatus.PENDING
    queue_item.attempts = 0
    queue_item.error_message = None
    queue_item.next_retry_at = None
    
    session.add(queue_item)
    session.commit()
    
    # Process in background
    background_tasks.add_task(email_service.process_queue)
    
    return {
        "success": True,
        "message": "Email scheduled for retry"
    }


@router.post("/queue/process")
async def process_email_queue(
    session: SessionDep,
    current_user: User = Depends(get_current_active_superuser),
    batch_size: int = Query(10, ge=1, le=100, description="Number of emails to process")
):
    """
    Manually trigger email queue processing
    """
    # Process the queue
    result = await email_service.process_queue(batch_size=batch_size)
    
    return {
        "success": True,
        "processed": result.get("processed", 0),
        "sent": result.get("sent", 0),
        "failed": result.get("failed", 0),
        "errors": result.get("errors", [])
    }


@router.delete("/queue/{queue_id}")
async def cancel_email(
    queue_id: UUID,
    session: SessionDep,
    current_user: User = Depends(get_current_active_superuser)
):
    """Cancel a queued email"""
    
    queue_item = session.get(EmailQueue, queue_id)
    
    if not queue_item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    if queue_item.status == EmailStatus.SENT:
        raise HTTPException(status_code=400, detail="Cannot cancel already sent email")
    
    queue_item.status = EmailStatus.CANCELLED
    
    session.add(queue_item)
    session.commit()
    
    return {
        "success": True,
        "message": "Email cancelled"
    }