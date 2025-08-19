# ABOUTME: Debug endpoint to check StudyDataConfiguration
# ABOUTME: Temporary endpoint for troubleshooting data mapping issues

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.api.deps import get_db, get_current_user
from app.models import User, Study, StudyDataConfiguration

router = APIRouter()

@router.get("/debug/study/{study_id}/data-config")
async def debug_study_data_config(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to check StudyDataConfiguration"""
    
    # Get study
    study = db.get(Study, study_id)
    if not study:
        return {"error": "Study not found"}
    
    # Get StudyDataConfiguration
    study_data_config = db.exec(
        select(StudyDataConfiguration).where(
            StudyDataConfiguration.study_id == study_id
        )
    ).first()
    
    result = {
        "study_id": str(study_id),
        "study_name": study.name,
        "has_data_config": study_data_config is not None,
        "initialization_steps": study.initialization_steps,
        "data_uploaded_at": study.data_uploaded_at
    }
    
    if study_data_config:
        result.update({
            "data_config_id": str(study_data_config.id),
            "dataset_schemas": study_data_config.dataset_schemas,
            "datasets_count": len(study_data_config.dataset_schemas) if study_data_config.dataset_schemas else 0,
            "created_at": study_data_config.created_at,
            "updated_at": study_data_config.updated_at
        })
    
    return result