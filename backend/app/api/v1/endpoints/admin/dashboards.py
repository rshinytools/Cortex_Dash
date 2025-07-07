# ABOUTME: Unified dashboard template management endpoints for system administrators
# ABOUTME: Handles complete dashboard templates with embedded menus, widgets, and data mappings

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlmodel import Session, select
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_user
from app.models import (
    User, 
    Message,
    DashboardTemplate,
    DashboardTemplateCreate,
    DashboardTemplateUpdate,
    DashboardTemplatePublic,
    DashboardTemplatesPublic,
    DashboardCategory,
    MenuItemType,
    StudyDashboard,
    DashboardTemplateDataRequirements
)
from app.core.permissions import Permission, has_permission
from app.crud import dashboard as crud_dashboard
from app.core.audit import create_activity_log, ActivityAction


router = APIRouter()


# Request/Response Models for API-specific functionality
class DashboardCloneRequest(BaseModel):
    new_code: str = Field(..., description="Unique code for the cloned dashboard template")
    new_name: str = Field(..., description="Display name for the cloned dashboard template")
    new_description: Optional[str] = Field(None, description="Description of the cloned dashboard template")
    modifications: Optional[Dict[str, Any]] = Field(None, description="Modifications to apply to the template structure")


class DashboardPreviewRequest(BaseModel):
    study_id: UUID = Field(..., description="Study to use for sample data")
    sample_data_size: Optional[int] = Field(10, description="Number of sample records to load")
    preview_duration: Optional[int] = Field(60, description="Preview session duration in seconds")


class DashboardPreviewResponse(BaseModel):
    preview_id: UUID
    preview_url: str
    expires_at: datetime
    sample_widgets: List[Dict[str, Any]]
    menu_structure: List[Dict[str, Any]]


class DashboardTemplateValidationResult(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    data_requirements: Optional[DashboardTemplateDataRequirements] = None


def check_system_admin(current_user: User) -> None:
    """Check if user is a system admin"""
    if not current_user.is_superuser and not has_permission(current_user, Permission.MANAGE_SYSTEM):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only system administrators can access this endpoint"
        )


@router.get("", response_model=DashboardTemplatesPublic)
async def list_dashboards(
    category: Optional[DashboardCategory] = Query(None, description="Filter by dashboard category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name or description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    List all dashboard templates.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Get dashboards from database
    dashboards = crud_dashboard.get_dashboards(
        db=db,
        skip=skip,
        limit=limit,
        category=category,
        is_active=is_active
    )
    
    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        dashboards = [
            d for d in dashboards 
            if search_lower in d.name.lower() or 
               (d.description and search_lower in d.description.lower())
        ]
    
    # Convert to public models with counts
    dashboard_data = []
    for dashboard in dashboards:
        public_dashboard = DashboardTemplatePublic.model_validate(dashboard)
        
        # Count dashboards and widgets in template structure
        template = dashboard.template_structure
        menu_items = template.get("menu", {}).get("items", [])
        dashboard_count = 0
        widget_count = 0
        
        def count_items(items):
            nonlocal dashboard_count, widget_count
            for item in items:
                if item.get("type") == "dashboard":
                    dashboard_count += 1
                    if "dashboard" in item:
                        widget_count += len(item["dashboard"].get("widgets", []))
                elif item.get("type") == "group" and "children" in item:
                    count_items(item["children"])
        
        count_items(menu_items)
        public_dashboard.dashboard_count = dashboard_count
        public_dashboard.widget_count = widget_count
        dashboard_data.append(public_dashboard)
    
    return DashboardTemplatesPublic(data=dashboard_data, count=len(dashboard_data))


@router.post("", response_model=DashboardTemplatePublic, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard_data: DashboardTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new dashboard template.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Check if dashboard code already exists
    existing_dashboard = crud_dashboard.get_dashboard_by_code(db, code=dashboard_data.code)
    if existing_dashboard:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dashboard with code '{dashboard_data.code}' already exists"
        )
    
    # Validate template structure
    validation_errors = crud_dashboard.validate_template_structure(dashboard_data.template_structure)
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid template structure", "errors": validation_errors}
        )
    
    # Create dashboard in database
    db_dashboard = crud_dashboard.create_dashboard(
        db=db,
        dashboard_create=dashboard_data,
        current_user=current_user
    )
    
    # Log activity
    create_activity_log(
        db=db,
        user_id=current_user.id,
        action=ActivityAction.CREATE,
        resource_type="dashboard",
        resource_id=str(db_dashboard.id),
        details={"dashboard_code": db_dashboard.code, "dashboard_name": db_dashboard.name}
    )
    
    return DashboardTemplatePublic.model_validate(db_dashboard)


@router.get("/{dashboard_id}", response_model=DashboardTemplatePublic)
async def get_dashboard(
    dashboard_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get detailed information about a specific dashboard template.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Fetch dashboard from database
    db_dashboard = crud_dashboard.get_dashboard(db, dashboard_id=dashboard_id)
    if not db_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    # Convert to public model with counts
    public_dashboard = DashboardTemplatePublic.model_validate(db_dashboard)
    
    # Count dashboards and widgets
    template = db_dashboard.template_structure
    menu_items = template.get("menu", {}).get("items", [])
    dashboard_count = 0
    widget_count = 0
    
    def count_items(items):
        nonlocal dashboard_count, widget_count
        for item in items:
            if item.get("type") == "dashboard":
                dashboard_count += 1
                if "dashboard" in item:
                    widget_count += len(item["dashboard"].get("widgets", []))
            elif item.get("type") == "group" and "children" in item:
                count_items(item["children"])
    
    count_items(menu_items)
    public_dashboard.dashboard_count = dashboard_count
    public_dashboard.widget_count = widget_count
    
    return public_dashboard


@router.put("/{dashboard_id}", response_model=DashboardTemplatePublic)
async def update_dashboard(
    dashboard_id: UUID,
    dashboard_update: DashboardTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update an existing dashboard template.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Check if dashboard exists
    db_dashboard = crud_dashboard.get_dashboard(db, dashboard_id=dashboard_id)
    if not db_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    # Validate template structure if provided
    if dashboard_update.template_structure is not None:
        validation_errors = crud_dashboard.validate_template_structure(dashboard_update.template_structure)
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Invalid template structure", "errors": validation_errors}
            )
    
    # Update dashboard
    updated_dashboard = crud_dashboard.update_dashboard(
        db=db,
        dashboard_id=dashboard_id,
        dashboard_update=dashboard_update,
        current_user=current_user
    )
    
    if not updated_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    # Log activity
    create_activity_log(
        db=db,
        user_id=current_user.id,
        action=ActivityAction.UPDATE,
        resource_type="dashboard",
        resource_id=str(dashboard_id),
        details={"dashboard_code": updated_dashboard.code, "version": updated_dashboard.version}
    )
    
    return DashboardTemplatePublic.model_validate(updated_dashboard)


@router.delete("/{dashboard_id}", response_model=Message)
async def delete_dashboard(
    dashboard_id: UUID,
    force: bool = Query(False, description="Force delete even if dashboard is in use"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Delete a dashboard template.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Check if dashboard exists
    db_dashboard = crud_dashboard.get_dashboard(db, dashboard_id=dashboard_id)
    if not db_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    # Check if dashboard is assigned to any studies
    study_usage = db.exec(
        select(StudyDashboard).where(
            StudyDashboard.dashboard_template_id == dashboard_id,
            StudyDashboard.is_active == True
        ).limit(1)
    ).first()
    
    if study_usage and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dashboard is assigned to studies. Use force=true to delete anyway."
        )
    
    # Perform soft delete
    success = crud_dashboard.delete_dashboard(db, dashboard_id=dashboard_id)
    if not success and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete dashboard. It may be in use."
        )
    
    # If force delete and dashboard is in use, deactivate all study assignments
    if force and study_usage:
        db.exec(
            select(StudyDashboard).where(
                StudyDashboard.dashboard_template_id == dashboard_id
            )
        ).update({"is_active": False})
        # Then soft delete the dashboard
        db_dashboard.is_active = False
        db_dashboard.updated_at = datetime.utcnow()
        db.add(db_dashboard)
        db.commit()
    
    # Log activity
    create_activity_log(
        db=db,
        user_id=current_user.id,
        action=ActivityAction.DELETE,
        resource_type="dashboard",
        resource_id=str(dashboard_id),
        details={"dashboard_code": db_dashboard.code, "force": force}
    )
    
    return Message(message=f"Dashboard {db_dashboard.code} deleted successfully")


@router.post("/{dashboard_id}/clone", response_model=DashboardTemplatePublic, status_code=status.HTTP_201_CREATED)
async def clone_dashboard(
    dashboard_id: UUID,
    clone_data: DashboardCloneRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Clone an existing dashboard template with modifications.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Check if new code already exists
    existing_dashboard = crud_dashboard.get_dashboard_by_code(db, code=clone_data.new_code)
    if existing_dashboard:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dashboard with code '{clone_data.new_code}' already exists"
        )
    
    # Clone dashboard
    cloned_dashboard = crud_dashboard.clone_dashboard(
        db=db,
        dashboard_id=dashboard_id,
        new_name=clone_data.new_name,
        new_code=clone_data.new_code,
        current_user=current_user
    )
    
    if not cloned_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source dashboard not found"
        )
    
    # Update description if provided
    if clone_data.new_description:
        update_data = DashboardTemplateUpdate(description=clone_data.new_description)
        cloned_dashboard = crud_dashboard.update_dashboard(
            db=db,
            dashboard_id=cloned_dashboard.id,
            dashboard_update=update_data,
            current_user=current_user
        )
    
    # Apply modifications if provided
    if clone_data.modifications and isinstance(clone_data.modifications, dict):
        # Deep merge modifications into template structure
        import json
        template_structure = json.loads(json.dumps(cloned_dashboard.template_structure))
        
        # Merge modifications (simple update for now, could be more sophisticated)
        def deep_merge(base, updates):
            for key, value in updates.items():
                if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(template_structure, clone_data.modifications)
        
        update_data = DashboardTemplateUpdate(template_structure=template_structure)
        cloned_dashboard = crud_dashboard.update_dashboard(
            db=db,
            dashboard_id=cloned_dashboard.id,
            dashboard_update=update_data,
            current_user=current_user
        )
    
    # Log activity
    create_activity_log(
        db=db,
        user_id=current_user.id,
        action=ActivityAction.CREATE,
        resource_type="dashboard_clone",
        resource_id=str(cloned_dashboard.id),
        details={
            "source_dashboard_id": str(dashboard_id),
            "new_code": clone_data.new_code,
            "new_name": clone_data.new_name
        }
    )
    
    return DashboardTemplatePublic.model_validate(cloned_dashboard)


@router.post("/{dashboard_id}/preview", response_model=DashboardPreviewResponse)
async def preview_dashboard(
    dashboard_id: UUID,
    preview_request: DashboardPreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Preview dashboard with sample data from a specific study.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Fetch dashboard configuration
    db_dashboard = crud_dashboard.get_dashboard(db, dashboard_id=dashboard_id)
    if not db_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    # Verify study exists and user has access
    from app.models import Study
    study = db.get(Study, preview_request.study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Generate preview data
    preview_id = uuid4()
    expires_at = datetime.utcnow().replace(second=0, microsecond=0) + timedelta(
        seconds=preview_request.preview_duration
    )
    
    # Extract menu structure and generate sample widget data
    template = db_dashboard.template_structure
    menu_structure = template.get("menu", {}).get("items", [])
    
    # Generate sample data for widgets
    sample_widgets = []
    
    def process_menu_items(items):
        for item in items:
            if item.get("type") == "dashboard" and "dashboard" in item:
                dashboard = item["dashboard"]
                for widget in dashboard.get("widgets", []):
                    widget_code = widget.get("widget_code")
                    
                    # Load widget definition
                    from app.crud import widget as crud_widget
                    widget_def = crud_widget.get_widget_by_code(db, widget_code) if widget_code else None
                    
                    if widget_def:
                        sample_data = {
                            "menu_item_id": item.get("id"),
                            "widget_code": widget_code,
                            "widget_name": widget_def.name,
                            "sample_data": {}
                        }
                        
                        # Generate type-specific sample data
                        if widget_def.category == "metrics":
                            sample_data["sample_data"] = {
                                "value": 342,
                                "previous_value": 298,
                                "change": 44,
                                "change_percent": 14.77,
                                "trend": "up"
                            }
                        elif widget_def.category == "charts":
                            sample_data["sample_data"] = {
                                "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                                "datasets": [
                                    {
                                        "label": "Treatment A",
                                        "data": [25, 45, 78, 95]
                                    },
                                    {
                                        "label": "Treatment B",
                                        "data": [22, 41, 73, 89]
                                    }
                                ]
                            }
                        elif widget_def.category == "tables":
                            sample_data["sample_data"] = {
                                "headers": ["Subject ID", "Site", "Status", "Enrollment Date"],
                                "rows": [
                                    ["001-001", "Site 01", "Active", "2024-01-15"],
                                    ["001-002", "Site 01", "Active", "2024-01-16"],
                                    ["002-001", "Site 02", "Completed", "2024-01-10"]
                                ],
                                "total_count": preview_request.sample_data_size
                            }
                        
                        sample_widgets.append(sample_data)
            elif item.get("type") == "group" and "children" in item:
                process_menu_items(item["children"])
    
    process_menu_items(menu_structure)
    
    # Log activity
    create_activity_log(
        db=db,
        user_id=current_user.id,
        action=ActivityAction.READ,
        resource_type="dashboard_preview",
        resource_id=str(dashboard_id),
        details={
            "study_id": str(preview_request.study_id),
            "preview_id": str(preview_id)
        }
    )
    
    return DashboardPreviewResponse(
        preview_id=preview_id,
        preview_url=f"/preview/dashboard/{dashboard_id}?session={preview_id}",
        expires_at=expires_at,
        sample_widgets=sample_widgets,
        menu_structure=menu_structure
    )


@router.post("/{dashboard_id}/validate", response_model=DashboardTemplateValidationResult)
async def validate_dashboard_template(
    dashboard_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Validate a dashboard template and extract data requirements.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Fetch dashboard template
    db_dashboard = crud_dashboard.get_dashboard(db, dashboard_id=dashboard_id)
    if not db_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard template not found"
        )
    
    # Validate structure
    errors = crud_dashboard.validate_template_structure(db_dashboard.template_structure)
    
    # Extract data requirements
    data_requirements = None
    if not errors:
        data_requirements = crud_dashboard.extract_data_requirements(db_dashboard)
    
    # Check for warnings (non-blocking issues)
    warnings = []
    template = db_dashboard.template_structure
    
    # Check if any dashboards have no widgets
    def check_empty_dashboards(items, path=""):
        for item in items:
            if item.get("type") == "dashboard" and "dashboard" in item:
                widgets = item["dashboard"].get("widgets", [])
                if not widgets:
                    warnings.append(f"Dashboard '{item.get('label', item.get('id'))}' has no widgets")
            elif item.get("type") == "group" and "children" in item:
                check_empty_dashboards(item["children"], f"{path}/{item.get('id')}")
    
    menu_items = template.get("menu", {}).get("items", [])
    check_empty_dashboards(menu_items)
    
    return DashboardTemplateValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        data_requirements=data_requirements
    )


@router.get("/{dashboard_id}/data-requirements", response_model=DashboardTemplateDataRequirements)
async def get_dashboard_data_requirements(
    dashboard_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get data requirements for a dashboard template.
    
    Returns the datasets and fields required by all widgets in the template.
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Fetch dashboard template
    db_dashboard = crud_dashboard.get_dashboard(db, dashboard_id=dashboard_id)
    if not db_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard template not found"
        )
    
    # Extract and return data requirements
    data_requirements = crud_dashboard.extract_data_requirements(db_dashboard)
    
    return data_requirements


@router.get("/templates", response_model=List[Dict[str, Any]])
async def list_dashboard_template_codes(
    category: Optional[DashboardCategory] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    List all available dashboard template codes and names.
    
    Returns a simplified list for dropdowns and selections.
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Get active templates
    templates = crud_dashboard.get_dashboards(
        db=db,
        category=category,
        is_active=True
    )
    
    # Return simplified list
    return [
        {
            "id": str(template.id),
            "code": template.code,
            "name": template.name,
            "category": template.category,
            "description": template.description
        }
        for template in templates
    ]