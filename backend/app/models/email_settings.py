# ABOUTME: Models for email configuration, templates, queue, and user preferences
# ABOUTME: Supports dynamic SMTP settings, customizable templates, and email audit trail

from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from sqlalchemy import Text, UniqueConstraint
from pydantic import EmailStr


class EmailStatus(str, Enum):
    """Email queue status options"""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DigestFrequency(str, Enum):
    """Email digest frequency options"""
    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NEVER = "never"


class EmailSettings(SQLModel, table=True):
    """
    Email configuration settings for SMTP
    Store encrypted passwords and connection details
    """
    __tablename__ = "email_settings"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    smtp_host: str = Field(nullable=False, description="SMTP server hostname")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP authentication username")
    smtp_password: Optional[str] = Field(default=None, description="Encrypted SMTP password")
    smtp_from_email: EmailStr = Field(nullable=False, description="From email address")
    smtp_from_name: Optional[str] = Field(default=None, description="From display name")
    smtp_use_tls: bool = Field(default=True, description="Use TLS encryption")
    smtp_use_ssl: bool = Field(default=False, description="Use SSL encryption")
    smtp_timeout: int = Field(default=30, description="Connection timeout in seconds")
    is_active: bool = Field(default=True, description="Whether this configuration is active")
    test_recipient_email: Optional[EmailStr] = Field(default=None, description="Email for testing")
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[UUID] = Field(foreign_key="user.id", default=None)
    
    # Advanced settings
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: int = Field(default=300, description="Delay between retries in seconds")
    rate_limit: Optional[int] = Field(default=None, description="Max emails per hour")
    
    # Additional settings stored as JSON
    settings_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column("metadata", JSON))


class EmailTemplate(SQLModel, table=True):
    """
    Email templates for various system events
    Supports both HTML and plain text with variables
    """
    __tablename__ = "email_templates"
    __table_args__ = (UniqueConstraint("template_key"),)
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    template_key: str = Field(nullable=False, index=True, description="Unique template identifier")
    template_name: str = Field(nullable=False, description="Human-readable template name")
    subject: str = Field(nullable=False, description="Email subject with variables")
    html_template: str = Field(sa_column=Column(Text), description="HTML template content")
    plain_text_template: Optional[str] = Field(sa_column=Column(Text), default=None)
    
    # Template configuration
    variables: Dict[str, Any] = Field(
        default_factory=dict, 
        sa_column=Column(JSON),
        description="Available template variables and descriptions"
    )
    category: str = Field(default="system", description="Template category")
    is_active: bool = Field(default=True)
    is_system: bool = Field(default=False, description="System template (cannot be deleted)")
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[UUID] = Field(foreign_key="user.id", default=None)
    
    # Version control
    version: int = Field(default=1, description="Template version number")
    previous_version_id: Optional[UUID] = Field(default=None, description="Link to previous version")


class EmailQueue(SQLModel, table=True):
    """
    Email queue for reliable delivery
    Tracks status, retries, and scheduling
    """
    __tablename__ = "email_queue"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Recipient information
    recipient_email: EmailStr = Field(nullable=False, index=True)
    recipient_name: Optional[str] = Field(default=None)
    cc_emails: Optional[str] = Field(default=None, description="Comma-separated CC emails")
    bcc_emails: Optional[str] = Field(default=None, description="Comma-separated BCC emails")
    
    # Email content
    subject: str = Field(nullable=False)
    html_content: str = Field(sa_column=Column(Text))
    plain_text_content: Optional[str] = Field(sa_column=Column(Text), default=None)
    
    # Template reference
    template_id: Optional[UUID] = Field(foreign_key="email_templates.id", default=None)
    template_variables: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Queue management
    priority: int = Field(default=5, ge=1, le=10, description="1=highest, 10=lowest priority")
    status: EmailStatus = Field(default=EmailStatus.PENDING, index=True)
    attempts: int = Field(default=0)
    max_attempts: int = Field(default=3)
    
    # Scheduling
    scheduled_at: Optional[datetime] = Field(default=None, index=True)
    sent_at: Optional[datetime] = Field(default=None)
    next_retry_at: Optional[datetime] = Field(default=None)
    
    # Error tracking
    error_message: Optional[str] = Field(sa_column=Column(Text), default=None)
    error_code: Optional[str] = Field(default=None)
    
    # Additional context stored as JSON
    queue_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column("metadata", JSON))
    reference_type: Optional[str] = Field(default=None, description="Related entity type")
    reference_id: Optional[str] = Field(default=None, description="Related entity ID")
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = Field(foreign_key="user.id", default=None)


class EmailHistory(SQLModel, table=True):
    """
    Historical record of all sent emails
    For audit trail and analytics
    """
    __tablename__ = "email_history"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Link to queue
    queue_id: Optional[UUID] = Field(foreign_key="email_queue.id", default=None)
    
    # Email details
    recipient_email: EmailStr = Field(nullable=False, index=True)
    subject: str = Field(nullable=False)
    template_used: Optional[str] = Field(default=None, description="Template key used")
    
    # Status tracking
    status: str = Field(nullable=False)
    sent_at: Optional[datetime] = Field(default=None, index=True)
    delivered_at: Optional[datetime] = Field(default=None)
    
    # Engagement tracking
    opened_at: Optional[datetime] = Field(default=None)
    opened_count: int = Field(default=0)
    clicked_at: Optional[datetime] = Field(default=None)
    clicked_links: Dict[str, int] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Bounce and error tracking
    bounced: bool = Field(default=False)
    bounce_type: Optional[str] = Field(default=None, description="hard/soft bounce")
    bounce_reason: Optional[str] = Field(sa_column=Column(Text), default=None)
    
    # Spam and compliance
    marked_as_spam: bool = Field(default=False)
    unsubscribed: bool = Field(default=False)
    
    # Provider information
    provider_message_id: Optional[str] = Field(default=None, description="Provider's message ID")
    provider_response: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Metrics
    size_bytes: Optional[int] = Field(default=None, description="Email size in bytes")
    send_duration_ms: Optional[int] = Field(default=None, description="Time to send in ms")


class UserEmailPreferences(SQLModel, table=True):
    """
    User-specific email notification preferences
    Controls what types of emails users receive
    """
    __tablename__ = "user_email_preferences"
    __table_args__ = (UniqueConstraint("user_id"),)
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", nullable=False, unique=True)
    
    # Notification categories
    receive_account_updates: bool = Field(default=True, description="Account-related notifications")
    receive_study_updates: bool = Field(default=True, description="Study creation/modification")
    receive_data_updates: bool = Field(default=True, description="Data upload/processing")
    receive_system_alerts: bool = Field(default=True, description="System maintenance/issues")
    receive_backup_notifications: bool = Field(default=True, description="Backup operations")
    receive_audit_reports: bool = Field(default=False, description="Compliance/audit reports")
    receive_security_alerts: bool = Field(default=True, description="Security-related alerts")
    receive_pipeline_updates: bool = Field(default=True, description="Pipeline status updates")
    receive_collaboration_invites: bool = Field(default=True, description="Study sharing invites")
    receive_marketing: bool = Field(default=False, description="Product updates/newsletters")
    
    # Delivery preferences
    digest_frequency: DigestFrequency = Field(default=DigestFrequency.IMMEDIATE)
    quiet_hours_enabled: bool = Field(default=False, description="Enable quiet hours")
    quiet_hours_start: Optional[str] = Field(default=None, description="HH:MM format")
    quiet_hours_end: Optional[str] = Field(default=None, description="HH:MM format")
    timezone: str = Field(default="UTC", description="User's timezone")
    
    # Format preferences
    prefer_plain_text: bool = Field(default=False, description="Prefer plain text over HTML")
    include_attachments: bool = Field(default=True, description="Include relevant attachments")
    
    # Language and localization
    language_code: str = Field(default="en", description="Preferred language")
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Unsubscribe token for one-click unsubscribe
    unsubscribe_token: str = Field(default_factory=lambda: str(uuid4()))
    last_email_sent_at: Optional[datetime] = Field(default=None)
    
    # Metadata for custom preferences
    custom_preferences: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))