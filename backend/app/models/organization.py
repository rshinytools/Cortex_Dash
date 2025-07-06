# ABOUTME: Organization model for multi-tenant support in Clinical Dashboard Platform
# ABOUTME: Represents pharmaceutical companies using the platform with isolation and configuration

import uuid
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import JSON, DateTime, String

if TYPE_CHECKING:
    from .user import User
    from .study import Study


class OrganizationBase(SQLModel):
    name: str = Field(index=True, max_length=255)
    slug: str = Field(unique=True, index=True, max_length=100)  # Unique identifier like 'pharma-corp'
    
    # Features for tenant-specific features
    features: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Status
    active: bool = Field(default=True)
    

class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(SQLModel):
    name: Optional[str] = Field(default=None, max_length=255)
    features: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None


class Organization(OrganizationBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Audit fields
    created_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    )
    
    # Subscription/License tracking
    license_type: str = Field(default="trial", max_length=50)  # trial, basic, professional, enterprise
    max_users: int = Field(default=10)
    max_studies: int = Field(default=5)
    
    # Compliance settings
    compliance_settings: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Relationships
    users: List["User"] = Relationship(back_populates="organization")
    studies: List["Study"] = Relationship(back_populates="organization", cascade_delete=True)


class OrganizationPublic(OrganizationBase):
    id: uuid.UUID
    created_at: datetime
    license_type: str
    user_count: Optional[int] = None
    study_count: Optional[int] = None


class OrganizationsPublic(SQLModel):
    data: List[OrganizationPublic]
    count: int