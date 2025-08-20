# ABOUTME: API endpoints for study management
# ABOUTME: Handles CRUD operations for clinical studies with RBAC

from typing import List, Any, Optional, Dict
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlmodel import Session, select
from pydantic import BaseModel, Field
import uuid

from app.api.deps import get_db, get_current_user
from app.models import (
    Study, StudyCreate, StudyUpdate, StudyPublic, StudyStatus,
    User, Message, DashboardTemplate
)
from app.models.widget import WidgetDefinition
from app.crud import study as crud_study
from app.crud import organization as crud_org
from app.crud import activity_log as crud_activity
from app.core.permissions import (
    Permission, PermissionChecker, has_permission,
    require_study_access
)
from app.services.widget_data_executor_real import (
    WidgetDataRequest, WidgetDataResponse, WidgetDataExecutorFactory
)
# from app.services.redis_cache import get_cache

router = APIRouter()


class InitializeStudyRequest(BaseModel):
    """Request model for study initialization"""
    dashboard_template_id: Optional[uuid.UUID] = None
    data_source_config: Optional[Dict[str, Any]] = None
    pipeline_config: Optional[Dict[str, Any]] = None
    auto_configure: bool = True  # Automatically configure with defaults


class InitializeStudyResponse(BaseModel):
    """Response model for study initialization"""
    success: bool
    message: str
    study_id: uuid.UUID
    status: str
    initialized_components: List[str]
    dashboard_template_id: Optional[uuid.UUID] = None


@router.post("/", response_model=StudyPublic)
async def create_study(
    *,
    db: Session = Depends(get_db),
    study_in: StudyCreate,
    current_user: User = Depends(PermissionChecker(Permission.CREATE_STUDY)),
    request: Request
) -> Any:
    """
    Create new study. User must have CREATE_STUDY permission.
    """
    # Check if organization exists and user has access
    org = crud_org.get_organization(db, org_id=study_in.org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check organization access
    if not current_user.is_superuser and str(current_user.org_id) != str(study_in.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create study in different organization"
        )
    
    # Check organization limits
    if not crud_org.check_organization_limits(db, org_id=study_in.org_id, resource="studies"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization has reached maximum number of studies"
        )
    
    # Check if protocol number is unique
    if crud_study.get_study_by_protocol(db, protocol_number=study_in.protocol_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Study with this protocol number already exists"
        )
    
    study = await crud_study.create_study(db, study_create=study_in, current_user=current_user)
    
    # TODO: Fix activity logging schema mismatch
    # # Log activity
    # crud_activity.create_activity_log(
    #     db,
    #     user=current_user,
    #     action="create_study",
    #     resource_type="study",
    #     resource_id=str(study.id),
    #     details={
    #         "name": study.name,
    #         "protocol_number": study.protocol_number,
    #         "org_id": str(study.org_id)
    #     },
    #     ip_address=request.client.host,
    #     user_agent=request.headers.get("user-agent")
    # )
    
    return study


@router.get("/", response_model=List[StudyPublic])
async def read_studies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve studies. Users see studies based on their permissions.
    """
    # System admins can filter by org_id
    if current_user.is_superuser and org_id:
        studies = crud_study.get_studies(db, org_id=org_id, skip=skip, limit=limit, active_only=False)
    else:
        # Regular users see their organization's studies (including archived)
        studies = crud_study.get_studies(db, org_id=current_user.org_id, skip=skip, limit=limit, active_only=False)
    
    return studies


@router.get("/{study_id}", response_model=StudyPublic)
async def read_study(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get study by ID.
    """
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if not has_permission(current_user, Permission.VIEW_STUDY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view study"
        )
    
    return study


@router.patch("/{study_id}", response_model=StudyPublic)
async def update_study(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    study_in: StudyUpdate,
    current_user: User = Depends(PermissionChecker(Permission.EDIT_STUDY)),
    request: Request
) -> Any:
    """
    Update study.
    """
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    study = crud_study.update_study(
        db, study_id=study_id, study_update=study_in, current_user=current_user
    )
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="update_study",
        resource_type="study",
        resource_id=str(study.id),
        details={"updated_fields": list(study_in.model_dump(exclude_unset=True).keys())},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return study


@router.delete("/{study_id}", response_model=Message)
async def delete_study(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    current_user: User = Depends(PermissionChecker(Permission.DELETE_STUDY)),
    request: Request,
    hard_delete: bool = False  # Query parameter to force hard delete
) -> Any:
    """
    Delete study - by default archives it (soft delete).
    
    Use hard_delete=true to permanently delete the study and all its data.
    Only system admins can perform hard deletes.
    """
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Only superusers can perform hard deletes
    if hard_delete and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only system administrators can permanently delete studies"
        )
    
    try:
        success = crud_study.delete_study(db, study_id=study_id, hard_delete=hard_delete)
        
        if success:
            action = "hard_delete_study" if hard_delete else "archive_study"
            message = "Study permanently deleted" if hard_delete else "Study archived successfully"
            
            # Log activity
            crud_activity.create_activity_log(
                db,
                user=current_user,
                action=action,
                resource_type="study",
                resource_id=str(study_id),
                details={
                    "name": study.name,
                    "protocol_number": study.protocol_number,
                    "hard_delete": hard_delete
                },
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent")
            )
            return {"message": message}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete study"
            )
    except Exception as e:
        # Handle foreign key constraint violations
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete study: It has dependent data that must be removed first"
            )
        elif "violates foreign key constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete study: Other records depend on this study"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete study: {str(e)}"
            )


# NOTE: This endpoint has been replaced by the new initialization flow in study_initialization.py
# The new endpoint provides real-time progress tracking and better integration with the widget system
# The old initialize_study endpoint has been deprecated - see study_initialization.py for the new implementation


@router.get("/{study_id}/stats", response_model=dict)
async def get_study_statistics(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get study statistics.
    """
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if not has_permission(current_user, Permission.VIEW_STUDY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view study statistics"
        )
    
    return crud_study.get_study_statistics(db, study_id=study_id)


class StudyConfigurationUpdate(BaseModel):
    """Request model for updating study configuration"""
    config: Optional[Dict[str, Any]] = None
    pipeline_config: Optional[Dict[str, Any]] = None
    dashboard_config: Optional[Dict[str, Any]] = None
    dashboard_template_id: Optional[uuid.UUID] = None
    field_mappings: Optional[Dict[str, str]] = None
    template_overrides: Optional[Dict[str, Any]] = None


class StudyConfigurationResponse(BaseModel):
    """Response model for study configuration"""
    config: Dict[str, Any]
    pipeline_config: Dict[str, Any]
    dashboard_config: Dict[str, Any]
    dashboard_template_id: Optional[uuid.UUID]
    field_mappings: Dict[str, str]
    template_overrides: Dict[str, Any]
    updated_at: datetime


@router.put("/{study_id}/configuration", response_model=StudyConfigurationResponse)
async def update_study_configuration(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    configuration: StudyConfigurationUpdate,
    current_user: User = Depends(PermissionChecker(Permission.EDIT_STUDY)),
    request: Request
) -> Any:
    """
    Update study configuration including dashboard widgets, data sources, and pipeline settings.
    """
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update configuration fields
    update_data = {}
    if configuration.config is not None:
        study.config = configuration.config
        update_data["config"] = True
    
    if configuration.pipeline_config is not None:
        study.pipeline_config = configuration.pipeline_config
        update_data["pipeline_config"] = True
    
    if configuration.dashboard_config is not None:
        study.dashboard_config = configuration.dashboard_config
        update_data["dashboard_config"] = True
    
    if configuration.dashboard_template_id is not None:
        study.dashboard_template_id = configuration.dashboard_template_id
        update_data["dashboard_template_id"] = True
    
    if configuration.field_mappings is not None:
        study.field_mappings = configuration.field_mappings
        update_data["field_mappings"] = True
    
    if configuration.template_overrides is not None:
        study.template_overrides = configuration.template_overrides
        update_data["template_overrides"] = True
    
    # Update timestamps
    study.updated_at = datetime.utcnow()
    study.updated_by = current_user.id
    
    # Save to database
    db.add(study)
    db.commit()
    db.refresh(study)
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="update_study_configuration",
        resource_type="study",
        resource_id=str(study.id),
        details={
            "study_name": study.name,
            "updated_fields": list(update_data.keys())
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return StudyConfigurationResponse(
        config=study.config,
        pipeline_config=study.pipeline_config,
        dashboard_config=study.dashboard_config,
        dashboard_template_id=study.dashboard_template_id,
        field_mappings=study.field_mappings,
        template_overrides=study.template_overrides,
        updated_at=study.updated_at
    )


@router.get("/{study_id}/configuration", response_model=StudyConfigurationResponse)
async def get_study_configuration(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get study configuration including dashboard widgets, data sources, and pipeline settings.
    """
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if not has_permission(current_user, Permission.VIEW_STUDY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view study configuration"
        )
    
    return StudyConfigurationResponse(
        config=study.config,
        pipeline_config=study.pipeline_config,
        dashboard_config=study.dashboard_config,
        dashboard_template_id=study.dashboard_template_id,
        field_mappings=study.field_mappings,
        template_overrides=study.template_overrides,
        updated_at=study.updated_at
    )


@router.post("/{study_id}/activate", response_model=StudyPublic)
async def activate_study(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    request: Request
) -> Any:
    """
    Activate a study. Only system admins can activate studies.
    """
    # Only system admins can activate/deactivate studies
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only system administrators can activate studies"
        )
    
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Update study status to active
    study.status = StudyStatus.ACTIVE
    study.is_active = True
    study.updated_at = datetime.utcnow()
    study.updated_by = current_user.id
    
    db.add(study)
    db.commit()
    db.refresh(study)
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="activate_study",
        resource_type="study",
        resource_id=str(study_id),
        details={"name": study.name, "protocol_number": study.protocol_number},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return study


@router.post("/{study_id}/deactivate", response_model=StudyPublic)
async def deactivate_study(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    request: Request
) -> Any:
    """
    Deactivate a study. Only system admins can deactivate studies.
    """
    # Only system admins can activate/deactivate studies
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only system administrators can deactivate studies"
        )
    
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Update study to inactive - keep all data
    study.is_active = False
    study.updated_at = datetime.utcnow()
    study.updated_by = current_user.id
    
    # Don't change status - just mark as inactive
    # This preserves the study state (active, completed, etc.) while making it invisible
    
    db.add(study)
    db.commit()
    db.refresh(study)
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="deactivate_study",
        resource_type="study",
        resource_id=str(study_id),
        details={"name": study.name, "protocol_number": study.protocol_number},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return study


class ApplyTemplateRequest(BaseModel):
    """Request model for applying a dashboard template to a study"""
    dashboard_template_id: uuid.UUID
    field_mappings: Dict[str, str]  # template_field -> study_field
    auto_map_fields: bool = True  # Whether to attempt auto-mapping based on field names


class FieldMappingValidation(BaseModel):
    """Response model for field mapping validation"""
    is_valid: bool
    missing_mappings: List[str]
    suggested_mappings: Dict[str, str]
    warnings: List[str]


@router.post("/{study_id}/apply-template", response_model=StudyConfigurationResponse)
async def apply_dashboard_template(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    template_request: ApplyTemplateRequest,
    current_user: User = Depends(PermissionChecker(Permission.EDIT_STUDY)),
    request: Request
) -> Any:
    """
    Apply a dashboard template to a study with field mappings.
    """
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get the template
    from app.models import DashboardTemplate
    template = db.get(DashboardTemplate, template_request.dashboard_template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard template not found"
        )
    
    # Apply template to study
    study.dashboard_template_id = template.id
    study.field_mappings = template_request.field_mappings
    study.template_overrides = {}  # Start with no overrides
    
    # Update timestamps
    study.updated_at = datetime.utcnow()
    study.updated_by = current_user.id
    
    # Save to database
    db.add(study)
    db.commit()
    db.refresh(study)
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="DASHBOARD_TEMPLATE_APPLIED",
        resource_type="study",
        resource_id=str(study.id),
        details={
            "study_name": study.name,
            "template_name": template.name,
            "template_id": str(template.id),
            "field_mappings_count": len(template_request.field_mappings)
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        study_id=study.id
    )
    
    return StudyConfigurationResponse(
        config=study.config,
        pipeline_config=study.pipeline_config,
        dashboard_config=study.dashboard_config,
        dashboard_template_id=study.dashboard_template_id,
        field_mappings=study.field_mappings,
        template_overrides=study.template_overrides,
        updated_at=study.updated_at
    )


@router.post("/{study_id}/validate-field-mappings", response_model=FieldMappingValidation)
async def validate_field_mappings(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    template_id: uuid.UUID,
    field_mappings: Dict[str, str],
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Validate field mappings for a template and suggest auto-mappings.
    """
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get the template
    from app.models import DashboardTemplate
    template = db.get(DashboardTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard template not found"
        )
    
    # Extract required fields from template
    template_structure = template.template_structure or {}
    data_mappings = template_structure.get("data_mappings", {})
    field_requirements = data_mappings.get("field_mappings", {})
    
    # Flatten all required fields
    required_fields = set()
    for dataset, fields in field_requirements.items():
        for field in fields:
            required_fields.add(f"{dataset}.{field}")
    
    # Check missing mappings
    mapped_fields = set(field_mappings.keys())
    missing_mappings = list(required_fields - mapped_fields)
    
    # Generate suggested mappings based on field names
    suggested_mappings = {}
    for missing_field in missing_mappings:
        dataset, field = missing_field.split(".", 1)
        # Simple heuristic: look for similar field names
        # In a real implementation, this would check actual study data schemas
        if field.upper() in ["USUBJID", "SUBJID"]:
            suggested_mappings[missing_field] = "subject_id"
        elif field.upper() in ["VISITNUM", "VISIT"]:
            suggested_mappings[missing_field] = "visit_number"
        elif field.upper() in ["VISITDAT", "VISITDT"]:
            suggested_mappings[missing_field] = "visit_date"
    
    # Generate warnings
    warnings = []
    if len(missing_mappings) > 0:
        warnings.append(f"{len(missing_mappings)} required fields are not mapped")
    
    return FieldMappingValidation(
        is_valid=len(missing_mappings) == 0,
        missing_mappings=missing_mappings,
        suggested_mappings=suggested_mappings,
        warnings=warnings
    )


# Dashboard Runtime Models
class WidgetRuntimeConfig(BaseModel):
    """Runtime configuration for a widget with resolved field mappings"""
    widget_code: str
    instance_config: Dict[str, Any]
    position: Dict[str, Any]  # x, y, w, h
    data_requirements: Dict[str, Any]
    resolved_fields: Dict[str, str]  # Mapped fields for this study


class DashboardRuntimeConfig(BaseModel):
    """Runtime configuration for a dashboard with resolved data"""
    id: str
    name: str
    description: Optional[str] = None
    layout: Dict[str, Any]
    widgets: List[WidgetRuntimeConfig]
    last_updated: datetime


class MenuItemRuntime(BaseModel):
    """Runtime menu item with resolved dashboard reference"""
    id: str
    type: str  # dashboard, static_page, external, group, divider
    label: str
    icon: Optional[str] = None
    path: Optional[str] = None
    dashboard_id: Optional[str] = None
    children: Optional[List['MenuItemRuntime']] = None
    visible: bool = True
    badge: Optional[Dict[str, Any]] = None


class StudyMenuResponse(BaseModel):
    """Response model for study menu structure"""
    study_id: uuid.UUID
    study_name: str
    menu_items: List[MenuItemRuntime]
    template_id: Optional[uuid.UUID] = None
    template_name: Optional[str] = None


class StudyDashboardsResponse(BaseModel):
    """Response model for listing study dashboards"""
    study_id: uuid.UUID
    study_name: str
    dashboards: List[DashboardRuntimeConfig]
    template_id: Optional[uuid.UUID] = None
    template_name: Optional[str] = None


class DashboardUpdateRequest(BaseModel):
    """Request model for updating dashboard configuration"""
    widget_overrides: Optional[Dict[str, Any]] = None  # widget_id -> override config
    layout_overrides: Optional[Dict[str, Any]] = None
    custom_widgets: Optional[List[Dict[str, Any]]] = None  # New widgets to add


# Forward reference resolution
MenuItemRuntime.model_rebuild()


def apply_field_mappings(template_field: str, field_mappings: Dict[str, str]) -> str:
    """Apply field mappings to resolve template fields to study fields"""
    return field_mappings.get(template_field, template_field)


def process_widget_for_runtime(
    widget: Dict[str, Any], 
    field_mappings: Dict[str, str],
    widget_overrides: Optional[Dict[str, Any]] = None
) -> WidgetRuntimeConfig:
    """Process a widget configuration for runtime use"""
    # Handle nested widget structure from template
    widget_instance_id = widget.get("widgetInstanceId", widget.get("id", ""))
    widget_instance = widget.get("widgetInstance", {})
    widget_def = widget_instance.get("widgetDefinition", {})
    overrides = widget.get("overrides", {})
    
    # Extract widget code from definition
    widget_code = widget_def.get("code", widget.get("widget_code", widget.get("type", "kpi_card")))
    
    # Apply any widget-specific overrides
    if widget_overrides and widget_instance_id in widget_overrides:
        widget = {**widget, **widget_overrides[widget_instance_id]}
    
    # Resolve data requirements fields
    data_requirements = widget.get("data_requirements", {})
    resolved_fields = {}
    
    if "fields" in data_requirements:
        for field in data_requirements["fields"]:
            dataset = data_requirements.get("dataset", "")
            template_field = f"{dataset}.{field}" if dataset else field
            resolved_fields[field] = apply_field_mappings(template_field, field_mappings)
    
    # Build instance config with all necessary fields
    instance_config = widget.get("instance_config", widget_instance.get("config", {}))
    if isinstance(instance_config, str):
        import json
        try:
            instance_config = json.loads(instance_config)
        except:
            instance_config = {}
    
    instance_config["id"] = widget_instance_id
    instance_config["title"] = overrides.get("title", widget.get("title", ""))
    instance_config["type"] = widget_code
    
    # Extract position
    position = widget.get("position", {})
    
    return WidgetRuntimeConfig(
        widget_code=widget_code,
        instance_config=instance_config,
        position={
            "x": position.get("x", 0),
            "y": position.get("y", 0),
            "w": position.get("width", position.get("w", 3)),
            "h": position.get("height", position.get("h", 2))
        },
        data_requirements=data_requirements,
        resolved_fields=resolved_fields
    )


@router.get("/{study_id}/dashboards", response_model=StudyDashboardsResponse)
async def get_study_dashboards(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    request: Request
) -> Any:
    """
    Get all dashboards for a study with resolved field mappings.
    """
    # Get study and check access
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if not has_permission(current_user, Permission.VIEW_DASHBOARD):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view dashboards"
        )
    
    # Get dashboard template
    if not study.dashboard_template_id:
        return StudyDashboardsResponse(
            study_id=study.id,
            study_name=study.name,
            dashboards=[],
            template_id=None,
            template_name=None
        )
    
    template = db.get(DashboardTemplate, study.dashboard_template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard template not found"
        )
    
    # Process template structure
    template_structure = template.template_structure or {}
    menu_config = template_structure.get("menu_structure", template_structure.get("menu", {}))
    field_mappings = study.field_mappings or {}
    template_overrides = study.template_overrides or {}
    
    # Extract all dashboards from menu items
    dashboards = []
    
    def extract_dashboards_from_menu(items: List[Dict[str, Any]]) -> None:
        for item in items:
            # Support both 'dashboard' and 'dashboard_page' types
            if item.get("type") in ["dashboard", "dashboard_page"] and ("dashboard" in item or "widgets" in item):
                # Support both 'dashboard' field and 'widgets' field directly
                if "dashboard" in item:
                    dashboard_config = item["dashboard"]
                else:
                    dashboard_config = {"widgets": item.get("widgets", [])}
                dashboard_id = item.get("id", "")
                
                # Apply any dashboard-specific overrides
                if dashboard_id in template_overrides:
                    dashboard_config = {**dashboard_config, **template_overrides[dashboard_id]}
                
                # Process widgets
                widgets = []
                for widget in dashboard_config.get("widgets", []):
                    widget_overrides = template_overrides.get("widget_overrides", {})
                    widgets.append(process_widget_for_runtime(widget, field_mappings, widget_overrides))
                
                dashboards.append(DashboardRuntimeConfig(
                    id=dashboard_id,
                    name=item.get("label", "Dashboard"),
                    description=dashboard_config.get("description"),
                    layout=dashboard_config.get("layout", {}),
                    widgets=widgets,
                    last_updated=study.updated_at
                ))
            
            # Recursively process children
            if "children" in item:
                extract_dashboards_from_menu(item["children"])
    
    menu_items = menu_config.get("items", [])
    extract_dashboards_from_menu(menu_items)
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="READ",
        resource_type="study",
        resource_id=str(study.id),
        details={
            "study_name": study.name,
            "dashboard_count": len(dashboards)
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        study_id=study.id
    )
    
    return StudyDashboardsResponse(
        study_id=study.id,
        study_name=study.name,
        dashboards=dashboards,
        template_id=template.id,
        template_name=template.name
    )


@router.get("/{study_id}/dashboards/{dashboard_id}", response_model=DashboardRuntimeConfig)
async def get_study_dashboard(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    request: Request
) -> Any:
    """
    Get specific dashboard configuration for a study.
    """
    # Get study and check access
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if not has_permission(current_user, Permission.VIEW_DASHBOARD):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view dashboard"
        )
    
    # Get dashboard template
    if not study.dashboard_template_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dashboard template assigned to study"
        )
    
    template = db.get(DashboardTemplate, study.dashboard_template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard template not found"
        )
    
    # Find the specific dashboard in template
    template_structure = template.template_structure or {}
    menu_config = template_structure.get("menu_structure", template_structure.get("menu", {}))
    field_mappings = study.field_mappings or {}
    template_overrides = study.template_overrides or {}
    
    dashboard_config = None
    dashboard_name = None
    
    def find_dashboard_in_menu(items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for item in items:
            # Support both 'dashboard' and 'dashboard_page' types
            if item.get("id") == dashboard_id and item.get("type") in ["dashboard", "dashboard_page"]:
                return item
            if "children" in item:
                found = find_dashboard_in_menu(item["children"])
                if found:
                    return found
        return None
    
    menu_items = menu_config.get("items", [])
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Looking for dashboard {dashboard_id}")
    logger.info(f"Menu items: {[item.get('id') for item in menu_items]}")
    
    dashboard_item = find_dashboard_in_menu(menu_items)
    
    if not dashboard_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    # Support both 'dashboard' field and 'widgets' field directly
    if "dashboard" in dashboard_item:
        dashboard_config = dashboard_item["dashboard"]
    elif "widgets" in dashboard_item:
        dashboard_config = {"widgets": dashboard_item["widgets"]}
    else:
        dashboard_config = {}
    dashboard_name = dashboard_item.get("label", "Dashboard")
    
    # Apply any dashboard-specific overrides
    if dashboard_id in template_overrides:
        dashboard_config = {**dashboard_config, **template_overrides[dashboard_id]}
    
    # Process widgets
    widgets = []
    widget_overrides = template_overrides.get("widget_overrides", {})
    for widget in dashboard_config.get("widgets", []):
        widgets.append(process_widget_for_runtime(widget, field_mappings, widget_overrides))
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="READ",
        resource_type="dashboard",
        resource_id=dashboard_id,
        details={
            "study_name": study.name,
            "dashboard_name": dashboard_name
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        study_id=study.id
    )
    
    return DashboardRuntimeConfig(
        id=dashboard_id,
        name=dashboard_name,
        description=dashboard_config.get("description"),
        layout=dashboard_config.get("layout", {}),
        widgets=widgets,
        last_updated=study.updated_at
    )


@router.get("/{study_id}/menu", response_model=StudyMenuResponse)
async def get_study_menu(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    request: Request
) -> Any:
    """
    Get menu structure for a study.
    """
    # Get study and check access
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if not has_permission(current_user, Permission.VIEW_DASHBOARD):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view menu"
        )
    
    # Get dashboard template
    if not study.dashboard_template_id:
        return StudyMenuResponse(
            study_id=study.id,
            study_name=study.name,
            menu_items=[],
            template_id=None,
            template_name=None
        )
    
    template = db.get(DashboardTemplate, study.dashboard_template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard template not found"
        )
    
    # Process template structure
    template_structure = template.template_structure or {}
    menu_config = template_structure.get("menu_structure", template_structure.get("menu", {}))
    
    def process_menu_item(item: Dict[str, Any]) -> MenuItemRuntime:
        """Process a menu item for runtime"""
        menu_item = MenuItemRuntime(
            id=item.get("id", ""),
            type=item.get("type", ""),
            label=item.get("label", ""),
            icon=item.get("icon"),
            path=item.get("path"),
            dashboard_id=item.get("id") if item.get("type") == "dashboard" else None,
            visible=item.get("visible", True),
            badge=item.get("badge")
        )
        
        # Process children recursively
        if "children" in item:
            menu_item.children = [process_menu_item(child) for child in item["children"]]
        
        return menu_item
    
    menu_items = [process_menu_item(item) for item in menu_config.get("items", [])]
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="VIEW_STUDY_MENU",
        resource_type="study",
        resource_id=str(study.id),
        details={
            "study_name": study.name,
            "menu_items_count": len(menu_items)
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        study_id=study.id
    )
    
    return StudyMenuResponse(
        study_id=study.id,
        study_name=study.name,
        menu_items=menu_items,
        template_id=template.id,
        template_name=template.name
    )


@router.patch("/{study_id}/dashboards/{dashboard_id}", response_model=DashboardRuntimeConfig)
async def update_study_dashboard(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    dashboard_id: str,
    dashboard_update: DashboardUpdateRequest,
    current_user: User = Depends(PermissionChecker(Permission.EDIT_DASHBOARD)),
    request: Request
) -> Any:
    """
    Update dashboard configuration for a study (widget overrides, layout changes, etc).
    """
    # Get study and check access
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get dashboard template
    if not study.dashboard_template_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dashboard template assigned to study"
        )
    
    template = db.get(DashboardTemplate, study.dashboard_template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard template not found"
        )
    
    # Update template overrides
    template_overrides = study.template_overrides or {}
    
    # Update widget overrides
    if dashboard_update.widget_overrides:
        if "widget_overrides" not in template_overrides:
            template_overrides["widget_overrides"] = {}
        template_overrides["widget_overrides"].update(dashboard_update.widget_overrides)
    
    # Update layout overrides
    if dashboard_update.layout_overrides:
        if dashboard_id not in template_overrides:
            template_overrides[dashboard_id] = {}
        template_overrides[dashboard_id]["layout"] = dashboard_update.layout_overrides
    
    # Handle custom widgets (if any)
    if dashboard_update.custom_widgets:
        if dashboard_id not in template_overrides:
            template_overrides[dashboard_id] = {}
        if "custom_widgets" not in template_overrides[dashboard_id]:
            template_overrides[dashboard_id]["custom_widgets"] = []
        template_overrides[dashboard_id]["custom_widgets"].extend(dashboard_update.custom_widgets)
    
    # Update study
    study.template_overrides = template_overrides
    study.updated_at = datetime.utcnow()
    study.updated_by = current_user.id
    
    db.add(study)
    db.commit()
    db.refresh(study)
    
    # Log activity
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action="UPDATE_DASHBOARD",
        resource_type="dashboard",
        resource_id=dashboard_id,
        details={
            "study_name": study.name,
            "dashboard_id": dashboard_id,
            "update_types": list(dashboard_update.model_dump(exclude_unset=True).keys())
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        study_id=study.id
    )
    
    # Return updated dashboard configuration
    return await get_study_dashboard(
        db=db,
        study_id=study_id,
        dashboard_id=dashboard_id,
        current_user=current_user,
        request=request
    )


# Widget Data Endpoints

class WidgetDataQueryParams(BaseModel):
    """Query parameters for widget data requests"""
    filters: Optional[Dict[str, Any]] = None
    page: Optional[int] = Field(default=1, ge=1)
    page_size: Optional[int] = Field(default=20, ge=1, le=100)
    refresh: bool = Field(default=False)


@router.get("/{study_id}/dashboards/{dashboard_id}/widgets/{widget_id}/data", response_model=WidgetDataResponse)
async def get_widget_data(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    dashboard_id: str,
    widget_id: str,
    query_params: WidgetDataQueryParams = Depends(),
    current_user: User = Depends(get_current_user),
    request: Request,
    background_tasks: BackgroundTasks
) -> Any:
    """
    Get data for a specific widget in a dashboard.
    
    This endpoint:
    - Validates study and dashboard access
    - Retrieves widget configuration from the dashboard
    - Applies field mappings from study to widget
    - Executes the appropriate data query based on widget type
    - Returns cached data when available (unless refresh=true)
    """
    # Get study and check access
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if not has_permission(current_user, Permission.VIEW_DASHBOARD):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view widget data"
        )
    
    # Get dashboard configuration
    dashboard_config = await get_study_dashboard(
        db=db,
        study_id=study_id,
        dashboard_id=dashboard_id,
        current_user=current_user,
        request=request
    )
    
    # Find the widget in the dashboard
    widget_config = None
    widget_code = None
    for widget in dashboard_config.widgets:
        # Widget ID could be in instance_config or generated
        widget_instance_id = widget.instance_config.get("id", f"{widget.widget_code}_{dashboard_config.widgets.index(widget)}")
        if widget_instance_id == widget_id:
            widget_config = widget
            widget_code = widget.widget_code
            break
    
    if not widget_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found in dashboard"
        )
    
    # Get widget definition
    stmt = select(WidgetDefinition).where(WidgetDefinition.code == widget_code)
    widget_definition = db.execute(stmt).scalars().first()
    if not widget_definition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget definition not found"
        )
    
    # Create widget data request
    widget_request = WidgetDataRequest(
        widget_id=widget_id,
        widget_config=widget_config.instance_config,
        filters=query_params.filters or {},
        pagination={"page": query_params.page, "page_size": query_params.page_size} if widget_definition.category == "tables" else None,
        refresh=query_params.refresh
    )
    
    # Execute widget data query (skip cache for now)
    executor = WidgetDataExecutorFactory.create_executor(db, study, widget_definition)
    response = await executor.execute(widget_request)
    
    # Log activity (in background to not slow down response)
    background_tasks.add_task(
        crud_activity.create_activity_log,
        db,
        user=current_user,
        action="READ",
        resource_type="widget",
        resource_id=widget_id,
        details={
            "study_name": study.name,
            "dashboard_id": dashboard_id,
            "widget_code": widget_code,
            "cached": False,
            "filters_applied": len(query_params.filters) if query_params.filters else 0
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        study_id=study.id
    )
    
    return response


# Temporarily disabled - WidgetDataResponse not defined
# @router.post("/{study_id}/dashboards/{dashboard_id}/widgets/{widget_id}/refresh", response_model=WidgetDataResponse)
# async def refresh_widget_data(
#     *,
#     db: Session = Depends(get_db),
#     study_id: uuid.UUID,
#     dashboard_id: str,
#     widget_id: str,
#     current_user: User = Depends(get_current_user),
#     request: Request,
#     background_tasks: BackgroundTasks
# ) -> Any:
#     """
#     Force refresh data for a specific widget, bypassing cache.
#     
#     This endpoint:
#     - Invalidates cached data for the widget
#     - Fetches fresh data from the data source
#     - Updates the cache with new data
#     """
#     # Get cache instance
#     cache = await get_cache()
#     
#     # Invalidate cache for this widget
#     cache_key = f"widget_data:{study_id}:{widget_id}:{dashboard_id}"
#     await cache.delete(cache_key)
#     
#     # Call get_widget_data with refresh=true
#     query_params = WidgetDataQueryParams(refresh=True)
#     return await get_widget_data(
#         db=db,
#         study_id=study_id,
#         dashboard_id=dashboard_id,
#         widget_id=widget_id,
#         query_params=query_params,
#         current_user=current_user,
#         request=request,
#         background_tasks=background_tasks
#     )


@router.post("/{study_id}/refresh-all-widgets", response_model=Message)
async def refresh_all_study_widgets(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    current_user: User = Depends(PermissionChecker(Permission.EDIT_DASHBOARD)),
    request: Request,
    background_tasks: BackgroundTasks
) -> Any:
    """
    Force refresh all widget data for a study.
    
    This endpoint:
    - Requires EDIT_DASHBOARD permission
    - Invalidates all cached widget data for the study
    - Returns immediately (cache invalidation happens in background)
    """
    # Get study and check access
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get cache instance
    cache = await get_cache()
    
    # Invalidate all widget cache for this study (in background)
    background_tasks.add_task(cache.invalidate_study_cache, str(study_id))
    
    # Log activity
    background_tasks.add_task(
        crud_activity.create_activity_log,
        db,
        user=current_user,
        action="REFRESH_ALL_WIDGETS",
        resource_type="study",
        resource_id=str(study_id),
        details={
            "study_name": study.name
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        study_id=study.id
    )
    
    return {"message": f"Cache refresh initiated for all widgets in study '{study.name}'"}


@router.get("/{study_id}/cache-stats", response_model=Dict[str, Any])
async def get_study_cache_stats(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    current_user: User = Depends(PermissionChecker(Permission.VIEW_ANALYTICS)),
    request: Request
) -> Any:
    """
    Get cache statistics for a study's widget data.
    
    Returns:
    - Cache hit/miss rates
    - Memory usage
    - Number of cached widgets
    """
    # Get study and check access
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get cache instance
    cache = await get_cache()
    
    # Get overall cache stats
    cache_stats = await cache.get_cache_stats()
    
    # For now, return general stats
    # In a real implementation, we would track study-specific stats
    return {
        "study_id": str(study_id),
        "study_name": study.name,
        "cache_stats": cache_stats,
        "message": "Study-specific cache statistics will be available in a future update"
    }


@router.get("/{study_id}/data-sources")
async def list_data_sources(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    current_user: User = Depends(PermissionChecker(Permission.VIEW_STUDY)),
    request: Request
) -> Any:
    """
    List available data sources for a study.
    
    Returns:
    - sources: Dictionary of registered data sources
    - discovered: Dictionary of discovered but not registered sources
    """
    from app.services.data_source_manager import get_data_source_manager
    
    # Get study and check access
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get data source manager
    data_source_manager = get_data_source_manager()
    
    # Get registered sources
    registered_sources = await data_source_manager.list_sources()
    
    # Auto-discover available sources
    discovered_sources = await data_source_manager.auto_discover_sources(str(study_id))
    
    # Get available files for each registered source
    source_details = {}
    for source_name in registered_sources:
        try:
            files = await data_source_manager.get_available_files(source_name)
            schema = await data_source_manager.get_schema(source_name)
            source_details[source_name] = {
                "type": registered_sources[source_name]["type"],
                "files": files,
                "file_count": len(files),
                "schema_available": bool(schema)
            }
        except Exception as e:
            source_details[source_name] = {
                "type": registered_sources[source_name]["type"],
                "error": str(e)
            }
    
    return {
        "study_id": str(study_id),
        "registered_sources": source_details,
        "discovered_sources": {
            path: source_type.value 
            for path, source_type in discovered_sources.items()
        },
        "total_registered": len(registered_sources),
        "total_discovered": len(discovered_sources)
    }


@router.get("/{study_id}/data-sources/{source_name}/preview")
async def preview_data_source(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    source_name: str,
    table_or_file: str,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(PermissionChecker(Permission.VIEW_STUDY)),
    request: Request
) -> Any:
    """
    Preview data from a specific data source.
    
    Parameters:
    - study_id: Study identifier
    - source_name: Name of the data source (e.g., "primary", "secondary")
    - table_or_file: Name of the table or file to preview
    - limit: Number of rows to return (max 1000)
    - offset: Number of rows to skip
    
    Returns:
    - data: List of rows
    - columns: Column definitions
    - total_rows: Total number of rows available
    """
    from app.services.data_source_manager import get_data_source_manager
    
    # Get study and check access
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Validate limit
    if limit > 1000:
        limit = 1000
    if limit < 1:
        limit = 1
    
    # Get data source manager
    data_source_manager = get_data_source_manager()
    
    try:
        # Check if data source is registered
        sources = await data_source_manager.list_sources()
        
        # If source not registered, try to auto-discover
        if source_name not in sources:
            discovered = await data_source_manager.auto_discover_sources(str(study_id))
            if not discovered:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No data sources found for study {study.name}"
                )
            
            # Register the first discovered source with the requested name
            first_path = list(discovered.keys())[0]
            first_type = discovered[first_path]
            await data_source_manager.register_data_source(
                source_name,
                first_type,
                base_path=first_path
            )
        
        # Get preview data
        preview_data = await data_source_manager.preview_data(
            source_name,
            table_or_file,
            limit=limit,
            offset=offset
        )
        
        # Log activity
        crud_activity.create_activity_log(
            db,
            user=current_user,
            action="preview_data",
            resource_type="study",
            resource_id=str(study_id),
            details={
                "source": source_name,
                "table_or_file": table_or_file,
                "rows_previewed": len(preview_data.get("data", []))
            },
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return preview_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error previewing data: {str(e)}"
        )


@router.get("/{study_id}/data-versions")
async def get_data_versions(
    *,
    db: Session = Depends(get_db),
    study_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    request: Request
) -> Any:
    """
    Get all data versions for a study.
    """
    from pathlib import Path
    import os
    
    # Get study and check access
    study = crud_study.get_study(db, study_id=study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if not current_user.is_superuser and str(current_user.org_id) != str(study.org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Use correct path structure: /data/{org_id}/studies/{study_id}/source_data/
    data_path = Path(f"/data/{study.org_id}/studies/{study_id}/source_data")
    
    versions = []
    if data_path.exists():
        # List all timestamped directories
        for version_dir in sorted(data_path.iterdir(), reverse=True):
            if version_dir.is_dir() and version_dir.name != ".gitkeep":
                # Get file count and total size (only Parquet files)
                file_count = 0
                total_size = 0
                for file_path in version_dir.rglob("*.parquet"):
                    if file_path.is_file():
                        file_count += 1
                        total_size += file_path.stat().st_size
                
                # Parse timestamp from directory name 
                # Supports formats: YYYY-MM-DD, YYYYMMDD_HHMMSS, YYYY-MM-DD_HH-MM-SS
                try:
                    timestamp_str = version_dir.name
                    # Try different formats
                    for fmt in ["%Y-%m-%d", "%Y%m%d_%H%M%S", "%Y-%m-%d_%H-%M-%S", "%Y%m%d"]:
                        try:
                            dt = datetime.strptime(timestamp_str, fmt)
                            formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S") if "_" in timestamp_str else dt.strftime("%Y-%m-%d")
                            break
                        except:
                            continue
                    else:
                        formatted_date = version_dir.name
                except:
                    formatted_date = version_dir.name
                
                versions.append({
                    "version": version_dir.name,
                    "date": formatted_date,
                    "file_count": file_count,
                    "total_size": total_size,
                    "size_readable": f"{total_size / (1024*1024):.2f} MB" if total_size > 0 else "0 MB",
                    "status": "current" if versions == [] else "archived",  # First one is current
                    "uploaded_by": "System"  # Could be enhanced to track actual user
                })
    
    # Log activity
    from app.models.activity_log import ActivityAction
    crud_activity.create_activity_log(
        db,
        user=current_user,
        action=ActivityAction.DATA_VIEWED,
        resource_type="study",
        resource_id=str(study.id),
        details={
            "study_name": study.name,
            "version_count": len(versions),
            "data_type": "data_versions"
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return {
        "study_id": str(study.id),
        "versions": versions
    }
