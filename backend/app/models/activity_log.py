# ABOUTME: Activity log model for comprehensive audit trail supporting 21 CFR Part 11 compliance
# ABOUTME: Tracks all user actions with immutable records for regulatory compliance

import uuid
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel, Column, Index
from sqlalchemy import JSON, DateTime, String, Text, BigInteger

if TYPE_CHECKING:
    from .user import User
    from .study import Study


class ActivityAction(str, Enum):
    """Standard activity actions for audit trail"""
    # Authentication
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOGIN_FAILED = "LOGIN_FAILED"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    
    # Data operations
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    
    # Study operations
    STUDY_CREATED = "STUDY_CREATED"
    STUDY_UPDATED = "STUDY_UPDATED"
    STUDY_ARCHIVED = "STUDY_ARCHIVED"
    
    # Dashboard operations
    DASHBOARD_TEMPLATE_APPLIED = "DASHBOARD_TEMPLATE_APPLIED"
    DASHBOARD_CREATED = "DASHBOARD_CREATED"
    DASHBOARD_UPDATED = "DASHBOARD_UPDATED"
    DASHBOARD_DELETED = "DASHBOARD_DELETED"
    
    # Data pipeline
    PIPELINE_STARTED = "PIPELINE_STARTED"
    PIPELINE_COMPLETED = "PIPELINE_COMPLETED"
    PIPELINE_FAILED = "PIPELINE_FAILED"
    
    # Data access
    DATA_VIEWED = "DATA_VIEWED"
    DATA_EXPORTED = "DATA_EXPORTED"
    DATA_UPLOADED = "DATA_UPLOADED"
    
    # Compliance
    SIGNATURE_CREATED = "SIGNATURE_CREATED"
    PROTOCOL_APPROVED = "PROTOCOL_APPROVED"
    AUDIT_VIEWED = "AUDIT_VIEWED"
    
    # PHI access (HIPAA)
    PHI_ACCESSED = "PHI_ACCESSED"
    PHI_EXPORTED = "PHI_EXPORTED"


class ActivityLogBase(SQLModel):
    # Who
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    
    # What
    action: ActivityAction = Field(index=True)
    resource_type: str = Field(max_length=50, index=True)  # study, user, pipeline, etc.
    resource_id: Optional[str] = Field(default=None, max_length=100, index=True)
    
    # When - using both for 21 CFR Part 11 compliance
    timestamp: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    )
    
    # Where
    ip_address: Optional[str] = Field(default=None, max_length=45)  # Support IPv6
    user_agent: Optional[str] = Field(default=None, max_length=500)
    
    # Additional context
    details: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Optional study context
    study_id: Optional[uuid.UUID] = Field(default=None, foreign_key="study.id", index=True)
    org_id: Optional[uuid.UUID] = Field(default=None, foreign_key="organization.id", index=True)


class ActivityLogCreate(ActivityLogBase):
    pass


class ActivityLog(ActivityLogBase, table=True):
    __tablename__ = "activity_log"
    __table_args__ = (
        Index("idx_activity_timestamp_user", "timestamp", "user_id"),
        Index("idx_activity_resource", "resource_type", "resource_id"),
        Index("idx_activity_org_study", "org_id", "study_id"),
    )
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # 21 CFR Part 11 specific fields
    system_timestamp: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )
    sequence_number: int = Field(
        sa_column=Column(BigInteger, nullable=False, index=True)
    )
    
    # Audit trail integrity
    checksum: Optional[str] = Field(default=None, max_length=64)  # SHA-256 hash
    
    # For tracking data changes
    old_value: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    new_value: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Why - for regulatory compliance
    reason: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Relationships
    user: "User" = Relationship(back_populates="activity_logs")
    study: Optional["Study"] = Relationship(back_populates="activity_logs")
    
    class Config:
        # Make this table append-only for compliance
        # In practice, enforce this at database level with triggers
        arbitrary_types_allowed = True


class ActivityLogPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    action: ActivityAction
    resource_type: str
    resource_id: Optional[str] = None
    timestamp: datetime
    ip_address: Optional[str] = None
    details: Dict[str, Any]
    study_id: Optional[uuid.UUID] = None
    reason: Optional[str] = None


class ActivityLogsPublic(SQLModel):
    data: list[ActivityLogPublic]
    count: int