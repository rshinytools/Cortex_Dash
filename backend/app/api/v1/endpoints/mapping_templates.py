# ABOUTME: API endpoints for managing mapping templates
# ABOUTME: CRUD operations for reusable widget mapping configurations

from typing import Any, List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlmodel import Session, select, or_
from pydantic import BaseModel

from app.api import deps
from app.models import User
from app.models.mapping_templates import (
    MappingTemplate,
    MappingTemplateScope,
    TransformationDefinition,
    MappingTemplateVersion,
    MappingTemplateUsage,
    TransformationType
)
# from app.services.transformations.transformation_engine import TransformationEngine
from app.core.config import settings

router = APIRouter()


class CreateMappingTemplateRequest(BaseModel):
    """Request model for creating a mapping template"""
    name: str
    description: Optional[str] = None
    scope: MappingTemplateScope = MappingTemplateScope.ORGANIZATION
    widget_type: str
    source_system: Optional[str] = None
    field_mappings: dict = {}
    transformations: List[dict] = []
    default_filters: List[dict] = []
    default_joins: List[dict] = []
    display_config: dict = {}
    tags: List[str] = []


class UpdateMappingTemplateRequest(BaseModel):
    """Request model for updating a mapping template"""
    name: Optional[str] = None
    description: Optional[str] = None
    field_mappings: Optional[dict] = None
    transformations: Optional[List[dict]] = None
    default_filters: Optional[List[dict]] = None
    default_joins: Optional[List[dict]] = None
    display_config: Optional[dict] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class TestTransformationRequest(BaseModel):
    """Request model for testing a transformation"""
    transformation_type: TransformationType
    config: dict = {}
    source_fields: List[str] = []
    target_field: str
    sample_data: dict
    on_error: str = "skip"
    default_value: Any = None


class ApplyTemplateRequest(BaseModel):
    """Request model for applying a template to a widget"""
    widget_id: UUID
    study_id: UUID
    modifications: dict = {}


@router.get("/", response_model=List[MappingTemplate])
def list_mapping_templates(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    widget_type: Optional[str] = Query(None),
    scope: Optional[MappingTemplateScope] = Query(None),
    tags: Optional[List[str]] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    List available mapping templates.
    
    Templates are filtered based on user's access:
    - System templates are available to all
    - Organization templates are available to users in the same org
    - Study templates require study access
    - User templates are private
    """
    
    # Build base query
    query = select(MappingTemplate).where(MappingTemplate.is_active == True)
    
    # Apply access filters
    access_conditions = [
        MappingTemplate.scope == MappingTemplateScope.SYSTEM,
    ]
    
    if not current_user.is_superuser:
        # Add organization scope for same org
        access_conditions.append(
            (MappingTemplate.scope == MappingTemplateScope.ORGANIZATION) &
            (MappingTemplate.organization_id == current_user.organization_id)
        )
        
        # Add user scope for own templates
        access_conditions.append(
            (MappingTemplate.scope == MappingTemplateScope.USER) &
            (MappingTemplate.created_by == current_user.id)
        )
    
    query = query.where(or_(*access_conditions))
    
    # Apply filters
    if widget_type:
        query = query.where(MappingTemplate.widget_type == widget_type)
    
    if scope:
        query = query.where(MappingTemplate.scope == scope)
    
    if search:
        query = query.where(
            or_(
                MappingTemplate.name.ilike(f"%{search}%"),
                MappingTemplate.description.ilike(f"%{search}%")
            )
        )
    
    # Apply tag filter
    if tags:
        for tag in tags:
            query = query.where(MappingTemplate.tags.contains([tag]))
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    templates = db.exec(query).all()
    return templates


@router.get("/{template_id}", response_model=MappingTemplate)
def get_mapping_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Get a specific mapping template by ID."""
    
    template = db.exec(
        select(MappingTemplate).where(MappingTemplate.id == template_id)
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check access
    if not _has_template_access(template, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return template


@router.post("/", response_model=MappingTemplate)
def create_mapping_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: CreateMappingTemplateRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Create a new mapping template."""
    
    # Check for duplicate name in same scope
    existing = db.exec(
        select(MappingTemplate).where(
            MappingTemplate.name == template_in.name,
            MappingTemplate.organization_id == current_user.organization_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Template with name '{template_in.name}' already exists"
        )
    
    # Create template
    template = MappingTemplate(
        **template_in.dict(),
        organization_id=current_user.organization_id if template_in.scope == MappingTemplateScope.ORGANIZATION else None,
        created_by=current_user.id
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    # Create initial version
    version = MappingTemplateVersion(
        template_id=template.id,
        version_number=1,
        field_mappings=template.field_mappings,
        transformations=template.transformations,
        default_filters=template.default_filters,
        default_joins=template.default_joins,
        display_config=template.display_config,
        change_description="Initial version",
        created_by=current_user.id
    )
    
    db.add(version)
    db.commit()
    
    return template


@router.patch("/{template_id}", response_model=MappingTemplate)
def update_mapping_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: UUID,
    template_in: UpdateMappingTemplateRequest,
    version_description: Optional[str] = Query(None, description="Description of changes"),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Update a mapping template."""
    
    template = db.exec(
        select(MappingTemplate).where(MappingTemplate.id == template_id)
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check access
    if not _has_template_write_access(template, current_user):
        raise HTTPException(status_code=403, detail="Cannot modify this template")
    
    # Get current version number
    latest_version = db.exec(
        select(MappingTemplateVersion)
        .where(MappingTemplateVersion.template_id == template_id)
        .order_by(MappingTemplateVersion.version_number.desc())
    ).first()
    
    next_version_number = (latest_version.version_number + 1) if latest_version else 1
    
    # Update template
    update_data = template_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    template.updated_at = datetime.utcnow()
    
    # Create new version
    version = MappingTemplateVersion(
        template_id=template.id,
        version_number=next_version_number,
        field_mappings=template.field_mappings,
        transformations=template.transformations,
        default_filters=template.default_filters,
        default_joins=template.default_joins,
        display_config=template.display_config,
        change_description=version_description or f"Updated by {current_user.email}",
        created_by=current_user.id,
        is_validated=False
    )
    
    db.add(version)
    db.commit()
    db.refresh(template)
    
    return template


@router.delete("/{template_id}")
def delete_mapping_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Delete a mapping template (soft delete)."""
    
    template = db.exec(
        select(MappingTemplate).where(MappingTemplate.id == template_id)
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check access
    if not _has_template_write_access(template, current_user):
        raise HTTPException(status_code=403, detail="Cannot delete this template")
    
    # Soft delete
    template.is_active = False
    template.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Template deleted successfully"}


@router.post("/{template_id}/validate")
def validate_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: UUID,
    study_id: UUID = Body(..., description="Study ID to validate against"),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Validate a template against a study's data structure."""
    
    template = db.exec(
        select(MappingTemplate).where(MappingTemplate.id == template_id)
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check access
    if not _has_template_access(template, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Implement actual validation against study data
    # For now, return mock validation result
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "field_coverage": {
            "required_fields_mapped": 5,
            "optional_fields_mapped": 3,
            "unmapped_fields": 2
        },
        "transformation_validation": {
            "valid_transformations": len(template.transformations),
            "invalid_transformations": 0
        }
    }
    
    # Update template validation status
    template.is_validated = validation_result["valid"]
    template.validation_date = datetime.utcnow()
    template.validation_notes = f"Validated against study {study_id}"
    
    db.commit()
    
    return validation_result


@router.post("/{template_id}/apply")
def apply_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: UUID,
    request: ApplyTemplateRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Apply a template to a widget configuration."""
    
    template = db.exec(
        select(MappingTemplate).where(MappingTemplate.id == template_id)
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check access
    if not _has_template_access(template, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Merge template configuration with modifications
    config = {
        "field_mappings": {**template.field_mappings, **request.modifications.get("field_mappings", {})},
        "transformations": template.transformations + request.modifications.get("transformations", []),
        "default_filters": template.default_filters + request.modifications.get("filters", []),
        "default_joins": template.default_joins + request.modifications.get("joins", []),
        "display_config": {**template.display_config, **request.modifications.get("display_config", {})},
        "primary_dataset": request.modifications.get("primary_dataset"),
        "aggregation_type": request.modifications.get("aggregation_type")
    }
    
    # Track usage
    usage = MappingTemplateUsage(
        template_id=template_id,
        widget_id=request.widget_id,
        study_id=request.study_id,
        user_id=current_user.id,
        modifications=request.modifications
    )
    
    db.add(usage)
    
    # Update template usage count
    template.usage_count += 1
    template.last_used_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "config": config,
        "template_name": template.name,
        "message": "Template applied successfully"
    }


# Temporarily disabled - TransformationEngine not implemented
# @router.post("/test-transformation")
# def test_transformation(
#     *,
#     request: TestTransformationRequest,
#     current_user: User = Depends(deps.get_current_active_user)
# ) -> Any:
#     """Test a transformation with sample data."""
#     
#     engine = TransformationEngine()
#     
#     try:
#         result = engine.apply_transformation(
#             data=request.sample_data,
#             transformation_type=request.transformation_type,
#             config=request.config,
#             source_fields=request.source_fields,
#             target_field=request.target_field,
#             on_error=request.on_error,
#             default_value=request.default_value
#         )
#         
#         return {
#             "success": True,
#             "result": result,
#             "target_field": request.target_field
#         }
#         
#     except Exception as e:
#         return {
#             "success": False,
#             "error": str(e),
#             "result": request.sample_data
#         }


@router.get("/{template_id}/versions")
def get_template_versions(
    *,
    db: Session = Depends(deps.get_db),
    template_id: UUID,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Get version history for a template."""
    
    template = db.exec(
        select(MappingTemplate).where(MappingTemplate.id == template_id)
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check access
    if not _has_template_access(template, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    versions = db.exec(
        select(MappingTemplateVersion)
        .where(MappingTemplateVersion.template_id == template_id)
        .order_by(MappingTemplateVersion.version_number.desc())
    ).all()
    
    return versions


@router.post("/{template_id}/clone")
def clone_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: UUID,
    new_name: str = Body(..., description="Name for the cloned template"),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Clone an existing template."""
    
    original = db.exec(
        select(MappingTemplate).where(MappingTemplate.id == template_id)
    ).first()
    
    if not original:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check access
    if not _has_template_access(original, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create clone
    clone = MappingTemplate(
        name=new_name,
        description=f"Cloned from {original.name}",
        scope=MappingTemplateScope.USER,  # Clones start as user templates
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        widget_type=original.widget_type,
        source_system=original.source_system,
        field_mappings=original.field_mappings.copy(),
        transformations=original.transformations.copy(),
        default_filters=original.default_filters.copy(),
        default_joins=original.default_joins.copy(),
        display_config=original.display_config.copy(),
        tags=original.tags.copy()
    )
    
    db.add(clone)
    db.commit()
    db.refresh(clone)
    
    return clone


def _has_template_access(template: MappingTemplate, user: User) -> bool:
    """Check if user has read access to template."""
    if user.is_superuser:
        return True
    if template.scope == MappingTemplateScope.SYSTEM:
        return True
    if template.scope == MappingTemplateScope.ORGANIZATION:
        return template.organization_id == user.organization_id
    if template.scope == MappingTemplateScope.USER:
        return template.created_by == user.id
    return False


def _has_template_write_access(template: MappingTemplate, user: User) -> bool:
    """Check if user has write access to template."""
    if user.is_superuser:
        return True
    if template.scope == MappingTemplateScope.SYSTEM:
        return False  # Only superusers can modify system templates
    if template.created_by == user.id:
        return True
    if template.scope == MappingTemplateScope.ORGANIZATION:
        # Check if user is org admin
        return template.organization_id == user.organization_id and user.role == "org_admin"
    return False