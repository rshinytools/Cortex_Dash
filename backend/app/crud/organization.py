# ABOUTME: CRUD operations for Organization model
# ABOUTME: Handles create, read, update, delete operations with multi-tenant support

from typing import List, Optional
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy import func
import uuid

from app.models import Organization, OrganizationCreate, OrganizationUpdate
from app.core.security import get_password_hash


def create_organization(db: Session, org_create: OrganizationCreate) -> Organization:
    """Create a new organization"""
    # Generate a unique slug if not provided
    if not org_create.slug:
        base_slug = org_create.name.lower().replace(" ", "-")
        slug = base_slug
        counter = 1
        # Ensure slug is unique
        while db.exec(select(Organization).where(Organization.slug == slug)).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        org_create.slug = slug
    
    db_org = Organization(
        **org_create.model_dump(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org


def get_organization(db: Session, org_id: uuid.UUID) -> Optional[Organization]:
    """Get organization by ID"""
    return db.get(Organization, org_id)


def get_organization_by_slug(db: Session, slug: str) -> Optional[Organization]:
    """Get organization by slug"""
    return db.exec(select(Organization).where(Organization.slug == slug)).first()


def get_organizations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True
) -> List[Organization]:
    """Get list of organizations"""
    query = select(Organization)
    if active_only:
        query = query.where(Organization.active == True)
    query = query.offset(skip).limit(limit)
    return list(db.exec(query).all())


def update_organization(
    db: Session,
    org_id: uuid.UUID,
    org_update: OrganizationUpdate
) -> Optional[Organization]:
    """Update organization"""
    db_org = db.get(Organization, org_id)
    if not db_org:
        return None
    
    update_data = org_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(db_org, field, value)
    
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org


def delete_organization(db: Session, org_id: uuid.UUID) -> bool:
    """Soft delete organization by setting active=False"""
    db_org = db.get(Organization, org_id)
    if not db_org:
        return False
    
    db_org.active = False
    db_org.updated_at = datetime.utcnow()
    db.add(db_org)
    db.commit()
    return True


def get_organization_user_count(db: Session, org_id: uuid.UUID) -> int:
    """Get count of users in organization"""
    from app.models import User
    return db.exec(
        select(func.count(User.id)).where(User.org_id == org_id)
    ).first() or 0


def get_organization_study_count(db: Session, org_id: uuid.UUID) -> int:
    """Get count of studies in organization"""
    from app.models import Study
    return db.exec(
        select(func.count(Study.id)).where(Study.org_id == org_id)
    ).first() or 0


def check_organization_limits(db: Session, org_id: uuid.UUID, resource: str) -> bool:
    """Check if organization has reached resource limits"""
    org = get_organization(db, org_id)
    if not org:
        return False
    
    if resource == "users":
        current_count = get_organization_user_count(db, org_id)
        return current_count < org.max_users
    elif resource == "studies":
        current_count = get_organization_study_count(db, org_id)
        return current_count < org.max_studies
    
    return True