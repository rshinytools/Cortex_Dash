# ABOUTME: CRUD operations for Study model
# ABOUTME: Handles create, read, update, delete operations for clinical studies

from typing import List, Optional
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy import and_
import uuid

from app.models import Study, StudyCreate, StudyUpdate, User, StudyStatus
from app.clinical_modules.services import FileService


async def create_study(
    db: Session,
    study_create: StudyCreate,
    current_user: User
) -> Study:
    """Create a new study and initialize folder structure"""
    db_study = Study(
        **study_create.model_dump(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=current_user.id,
        updated_by=current_user.id
    )
    db.add(db_study)
    db.commit()
    db.refresh(db_study)
    
    # TODO: Fix folder permissions issue
    # # Initialize study folder structure
    # file_service = FileService()
    # await file_service.initialize_study_folders(db_study)
    # 
    # # Update study with folder path
    # db.add(db_study)
    # db.commit()
    # db.refresh(db_study)
    
    return db_study


def get_study(db: Session, study_id: uuid.UUID) -> Optional[Study]:
    """Get study by ID"""
    return db.get(Study, study_id)


def get_study_by_protocol(db: Session, protocol_number: str) -> Optional[Study]:
    """Get study by protocol number"""
    return db.exec(
        select(Study).where(Study.protocol_number == protocol_number)
    ).first()


def get_studies(
    db: Session,
    org_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True
) -> List[Study]:
    """Get list of studies, optionally filtered by organization"""
    query = select(Study)
    
    conditions = []
    if org_id:
        conditions.append(Study.org_id == org_id)
    if active_only:
        # Only show studies that are active AND not in planning or archived status
        # Studies in setup, active, paused, or completed are shown
        conditions.append(Study.is_active == True)
        conditions.append(Study.status.in_([StudyStatus.SETUP, StudyStatus.ACTIVE, StudyStatus.PAUSED, StudyStatus.COMPLETED]))
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.offset(skip).limit(limit)
    return list(db.exec(query).all())


def get_user_studies(
    db: Session,
    user: User,
    skip: int = 0,
    limit: int = 100
) -> List[Study]:
    """Get studies accessible to a user"""
    # System admins can see all studies
    if user.is_superuser:
        return get_studies(db, skip=skip, limit=limit)
    
    # Other users see studies from their organization
    return get_studies(db, org_id=user.org_id, skip=skip, limit=limit)


def update_study(
    db: Session,
    study_id: uuid.UUID,
    study_update: StudyUpdate,
    current_user: User
) -> Optional[Study]:
    """Update study"""
    db_study = db.get(Study, study_id)
    if not db_study:
        return None
    
    update_data = study_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by"] = current_user.id
    
    for field, value in update_data.items():
        setattr(db_study, field, value)
    
    db.add(db_study)
    db.commit()
    db.refresh(db_study)
    return db_study


def delete_study(db: Session, study_id: uuid.UUID, hard_delete: bool = False) -> bool:
    """Delete study - either archive (soft delete) or permanently delete (hard delete)"""
    db_study = db.get(Study, study_id)
    if not db_study:
        return False
    
    try:
        if hard_delete:
            # Hard delete - permanently remove from database
            db.delete(db_study)
            db.commit()
        else:
            # Soft delete - archive the study
            db_study.status = StudyStatus.ARCHIVED
            db_study.is_active = False
            db_study.updated_at = datetime.utcnow()
            db.add(db_study)
            db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e


def get_study_statistics(db: Session, study_id: uuid.UUID) -> dict:
    """Get study statistics"""
    study = get_study(db, study_id)
    if not study:
        return {}
    
    # This will be expanded with actual data statistics
    return {
        "study_id": str(study.id),
        "protocol_number": study.protocol_number,
        "status": study.status,
        "created_at": study.created_at.isoformat(),
        "last_updated": study.updated_at.isoformat(),
        "data_sources": 0,  # Will be populated later
        "data_points": 0,   # Will be populated later
        "last_sync": None,  # Will be populated later
    }