# ABOUTME: API endpoints for data mapping configuration
# ABOUTME: Handles field mapping, validation, and suggestions

from typing import List, Optional, Dict, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_db
from app.core.permissions import require_permission, Permission
from app.models import User, Study, Organization
from app.models.data_mapping import (
    WidgetDataMapping, StudyDataConfiguration, FieldMappingTemplate,
    StudyInitializationRequest, DataMappingConfigRequest, MappingValidationResult,
    MappingSuggestion
)
from app.clinical_modules.mapping.mapping_service import MappingService
# from app.core.utils import track_activity  # TODO: Implement activity tracking
from datetime import datetime

router = APIRouter()

@router.post("/initialize", response_model=StudyDataConfiguration)
async def initialize_study_data(
    request: StudyInitializationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StudyDataConfiguration:
    """Initialize study data configuration by analyzing uploaded datasets"""
    # Check permission
    await require_permission(current_user, Permission.MANAGE_STUDIES, db)
    
    # Verify study access
    study = db.get(Study, request.study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Initialize using service
    mapping_service = MappingService(db)
    config = mapping_service.initialize_study_data(
        study_id=request.study_id,
        upload_ids=request.dataset_uploads,
        auto_detect=request.auto_detect_mappings
    )
    
    # Track activity
    # TODO: Implement activity tracking
    # track_activity(
    #     db,
    #     action="study_data_initialized",
    #     resource_type="study",
    #     resource_id=str(study.id),
    #     details={"datasets_analyzed": len(request.dataset_uploads)},
    #     user_id=current_user.id,
    #     org_id=current_user.org_id
    # )
    
    return config

@router.get("/study/{study_id}/config", response_model=StudyDataConfiguration)
async def get_study_data_config(
    study_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StudyDataConfiguration:
    """Get study data configuration"""
    # Check permission
    await require_permission(current_user, Permission.VIEW_STUDIES, db)
    
    # Verify study access
    study = db.get(Study, study_id)
    if not study or study.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Get configuration
    config = db.exec(
        select(StudyDataConfiguration)
        .where(StudyDataConfiguration.study_id == study_id)
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Study data configuration not found")
    
    return config

@router.post("/mappings", response_model=WidgetDataMapping)
async def create_mapping(
    mapping_config: DataMappingConfigRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> WidgetDataMapping:
    """Create a new widget data mapping"""
    # Check permission
    await require_permission(current_user, Permission.MANAGE_STUDIES, db)
    
    # Create mapping
    mapping = WidgetDataMapping(
        study_id=mapping_config.study_id,
        widget_id=mapping_config.widget_id,
        field_mappings=mapping_config.field_mappings,
        data_source_config=mapping_config.data_source_config,
        validation_rules=mapping_config.validation_rules or [],
        created_by=current_user.id
    )
    
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    
    # Track activity
    # TODO: Implement activity tracking
    # track_activity(
    #     db,
    #     action="widget_mapping_created",
    #     resource_type="widget_mapping",
    #     resource_id=str(mapping.id),
    #     details={"widget_id": str(mapping_config.widget_id)},
    #     user_id=current_user.id,
    #     org_id=current_user.org_id
    # )
    
    return mapping

@router.put("/mappings/{mapping_id}", response_model=WidgetDataMapping)
async def update_mapping(
    mapping_id: uuid.UUID,
    update_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> WidgetDataMapping:
    """Update a widget data mapping"""
    # Check permission
    await require_permission(current_user, Permission.MANAGE_STUDIES, db)
    
    # Get mapping
    mapping = db.get(WidgetDataMapping, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    # Verify access through study
    study = db.get(Study, mapping.study_id)
    if not study or study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update fields
    for field, value in update_data.items():
        if hasattr(mapping, field) and field not in ['id', 'created_at', 'created_by']:
            setattr(mapping, field, value)
    
    mapping.updated_by = current_user.id
    mapping.updated_at = datetime.utcnow()
    
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    
    return mapping

@router.get("/study/{study_id}/widget/{widget_id}/mapping", response_model=Optional[WidgetDataMapping])
async def get_widget_mapping(
    study_id: uuid.UUID,
    widget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Optional[WidgetDataMapping]:
    """Get mapping for a specific widget in a study"""
    # Check permission
    await require_permission(current_user, Permission.VIEW_STUDIES, db)
    
    # Verify study access
    study = db.get(Study, study_id)
    if not study or study.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Get mapping
    mapping = db.exec(
        select(WidgetDataMapping)
        .where(WidgetDataMapping.study_id == study_id)
        .where(WidgetDataMapping.widget_id == widget_id)
        .where(WidgetDataMapping.is_active == True)
    ).first()
    
    return mapping

@router.get("/study/{study_id}/widget/{widget_id}/suggestions", response_model=List[MappingSuggestion])
async def get_mapping_suggestions(
    study_id: uuid.UUID,
    widget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[MappingSuggestion]:
    """Get AI-powered mapping suggestions for a widget"""
    # Check permission
    await require_permission(current_user, Permission.VIEW_STUDIES, db)
    
    # Verify study access
    study = db.get(Study, study_id)
    if not study or study.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Get suggestions
    mapping_service = MappingService(db)
    suggestions = mapping_service.suggest_mappings(study_id, widget_id)
    
    return suggestions

@router.post("/validate", response_model=MappingValidationResult)
async def validate_mapping(
    mapping_config: DataMappingConfigRequest,
    sample_size: int = Query(100, ge=10, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MappingValidationResult:
    """Validate a mapping configuration"""
    # Check permission
    await require_permission(current_user, Permission.VIEW_STUDIES, db)
    
    # Create temporary mapping object for validation
    mapping = WidgetDataMapping(
        study_id=mapping_config.study_id,
        widget_id=mapping_config.widget_id,
        field_mappings=mapping_config.field_mappings,
        data_source_config=mapping_config.data_source_config,
        validation_rules=mapping_config.validation_rules or [],
        created_by=current_user.id
    )
    
    # Validate
    mapping_service = MappingService(db)
    result = mapping_service.validate_mapping(mapping, sample_size)
    
    return result

@router.get("/study/{study_id}/widget/{widget_id}/preview")
async def preview_mapping_data(
    study_id: uuid.UUID,
    widget_id: uuid.UUID,
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Preview data with current mapping configuration"""
    # Check permission
    await require_permission(current_user, Permission.VIEW_STUDIES, db)
    
    # Get mapping
    mapping = db.exec(
        select(WidgetDataMapping)
        .where(WidgetDataMapping.study_id == study_id)
        .where(WidgetDataMapping.widget_id == widget_id)
        .where(WidgetDataMapping.is_active == True)
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="No active mapping found")
    
    # Validate and get sample data
    mapping_service = MappingService(db)
    validation_result = mapping_service.validate_mapping(mapping, limit)
    
    return {
        "data": validation_result.sample_data or [],
        "total_rows": len(validation_result.sample_data or [])
    }

@router.get("/templates", response_model=List[FieldMappingTemplate])
async def get_templates(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[FieldMappingTemplate]:
    """Get available mapping templates for the organization"""
    query = select(FieldMappingTemplate).where(
        FieldMappingTemplate.org_id == current_user.org_id,
        FieldMappingTemplate.is_active == True
    )
    
    if category:
        query = query.where(FieldMappingTemplate.category == category)
    
    templates = db.exec(query).all()
    return templates

@router.post("/templates", response_model=FieldMappingTemplate)
async def create_template(
    name: str,
    description: str,
    category: str,
    field_mappings: Dict[str, Any],
    applicable_widget_types: List[str] = [],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> FieldMappingTemplate:
    """Create a new mapping template"""
    # Check permission
    await require_permission(current_user, Permission.MANAGE_TEMPLATES, db)
    
    template = FieldMappingTemplate(
        org_id=current_user.org_id,
        name=name,
        description=description,
        category=category,
        field_mappings=field_mappings,
        applicable_widget_types=applicable_widget_types,
        created_by=current_user.id
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template

@router.post("/templates/{template_id}/apply", response_model=WidgetDataMapping)
async def apply_template(
    template_id: uuid.UUID,
    study_id: uuid.UUID,
    widget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> WidgetDataMapping:
    """Apply a template to create a new mapping"""
    # Check permission
    await require_permission(current_user, Permission.MANAGE_STUDIES, db)
    
    mapping_service = MappingService(db)
    mapping = mapping_service.apply_template(template_id, widget_id, study_id, current_user.id)
    
    return mapping

@router.post("/study/{study_id}/validate-all")
async def validate_all_mappings(
    study_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, MappingValidationResult]:
    """Validate all mappings for a study"""
    # Check permission
    await require_permission(current_user, Permission.VIEW_STUDIES, db)
    
    # Get all mappings
    mappings = db.exec(
        select(WidgetDataMapping)
        .where(WidgetDataMapping.study_id == study_id)
        .where(WidgetDataMapping.is_active == True)
    ).all()
    
    # Validate each
    mapping_service = MappingService(db)
    results = {}
    
    for mapping in mappings:
        results[str(mapping.id)] = mapping_service.validate_mapping(mapping)
    
    return results

from datetime import datetime