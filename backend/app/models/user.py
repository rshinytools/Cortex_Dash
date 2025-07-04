# ABOUTME: Enhanced User model with multi-tenant support and compliance fields
# ABOUTME: Extends the FastAPI template User model with organization relationship and audit fields

import uuid
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import DateTime, JSON

if TYPE_CHECKING:
    from .organization import Organization
    from .study import Study
    from .activity_log import ActivityLog
    from .item import Item


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = Field(default=None, max_length=255)
    # Multi-tenant fields
    org_id: Optional[uuid.UUID] = Field(default=None, foreign_key="organization.id")
    role: str = Field(default="viewer", max_length=50)
    department: Optional[str] = Field(default=None, max_length=100)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: Optional[str] = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: Optional[EmailStr] = Field(default=None, max_length=255)
    password: Optional[str] = Field(default=None, min_length=8, max_length=40)
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    full_name: Optional[str] = Field(default=None, max_length=255)
    org_id: Optional[uuid.UUID] = None


class UserUpdateMe(SQLModel):
    full_name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    
    # Compliance and audit fields
    created_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    )
    last_login: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    password_changed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    
    # 21 CFR Part 11 compliance
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    force_password_change: bool = Field(default=False)
    
    # Additional audit fields
    created_by: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    updated_by: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    preferences: dict = Field(default_factory=dict, sa_column=Column("preferences", JSON))
    
    # Relationships
    organization: Optional["Organization"] = Relationship(back_populates="users")
    items: List["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    activity_logs: List["ActivityLog"] = Relationship(back_populates="user")
    
    # Study relationships will be added through UserStudy association table in RBAC phase


# Properties to return via API
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime
    last_login: Optional[datetime] = None


class UsersPublic(SQLModel):
    data: List[UserPublic]
    count: int