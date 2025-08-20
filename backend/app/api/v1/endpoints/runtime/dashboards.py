# ABOUTME: Runtime dashboard endpoints for end users to access dashboard configurations and widget data
# ABOUTME: Provides study-specific dashboard access with permission checks and data loading

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlmodel import Session, select
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_user
from app.models import (
    User,
    Study,
    StudyDashboard,
    DashboardTemplate,
    DashboardWidget,
    MenuTemplate
)
from app.core.permissions import Permission, has_permission
from app.crud import dashboard as crud_dashboard
from app.crud import menu as crud_menu

router = APIRouter()


# Request/Response Models
class StudyDashboardResponse(BaseModel):
    id: UUID
    dashboard_template_id: UUID
    dashboard_code: str
    dashboard_name: str
    layout_config: Dict[str, Any]
    widgets: List[Dict[str, Any]]
    customizations: Optional[Dict[str, Any]] = None
    menu_layouts: Optional[Dict[str, List[Dict[str, Any]]]] = None  # Layout per menu item


class WidgetDataRequest(BaseModel):
    widget_ids: List[UUID] = Field(..., description="List of widget IDs to load data for")
    time_range: Optional[str] = Field(None, description="Time range filter (e.g., '1w', '1m', '3m')")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters to apply")


class WidgetDataResponse(BaseModel):
    widget_id: UUID
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    last_updated: datetime
    error: Optional[str] = None


class BatchWidgetDataResponse(BaseModel):
    widgets: List[WidgetDataResponse]
    errors: List[Dict[str, str]] = Field(default_factory=list)


class StudyMenuResponse(BaseModel):
    menu_structure: Dict[str, Any]
    version: int
    last_updated: datetime


def check_study_access(
    db: Session,
    study_id: UUID,
    current_user: User,
    required_permission: Optional[Permission] = None
) -> Study:
    """Check if user has access to a study"""
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check if user belongs to the study's organization
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this study"
        )
    
    # Check specific permission if required
    if required_permission and not has_permission(current_user, required_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have {required_permission.value} permission"
        )
    
    return study


@router.get("/{study_id}/dashboards", response_model=List[StudyDashboardResponse])
async def list_study_dashboards(
    study_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    List all dashboards available for a study.
    
    Returns dashboards assigned to the study with their configurations.
    """
    # Check study access
    study = check_study_access(db, study_id, current_user, Permission.VIEW_DASHBOARDS)
    
    # Get all active dashboards for the study
    study_dashboards = crud_dashboard.get_study_dashboards(
        db=db,
        study_id=study_id,
        is_active=True
    )
    
    # Build response with dashboard details
    dashboard_responses = []
    for study_dashboard in study_dashboards:
        dashboard_template = study_dashboard.dashboard_template
        
        # Apply customizations if any
        layout_config = dashboard_template.layout_config.copy()
        if study_dashboard.customizations:
            # Merge customizations into layout config
            layout_config.update(study_dashboard.customizations)
        
        # Get widgets with configurations
        widgets = []
        for widget in dashboard_template.widgets:
            widget_data = {
                "id": str(widget.id),
                "widget_definition_id": str(widget.widget_definition_id),
                "widget_code": widget.widget_definition.code,
                "widget_name": widget.widget_definition.name,
                "instance_config": widget.instance_config,
                "position": widget.position,
                "data_binding": widget.data_binding
            }
            
            # Apply widget customizations if any
            if study_dashboard.customizations and "widget_overrides" in study_dashboard.customizations:
                widget_overrides = study_dashboard.customizations["widget_overrides"].get(str(widget.id), {})
                if widget_overrides:
                    widget_data["instance_config"].update(widget_overrides)
            
            widgets.append(widget_data)
        
        dashboard_response = StudyDashboardResponse(
            id=study_dashboard.id,
            dashboard_template_id=dashboard_template.id,
            dashboard_code=dashboard_template.code,
            dashboard_name=dashboard_template.name,
            layout_config=layout_config,
            widgets=widgets,
            customizations=study_dashboard.customizations
        )
        
        dashboard_responses.append(dashboard_response)
    
    return dashboard_responses


@router.get("/{study_id}/dashboards/{dashboard_id}", response_model=StudyDashboardResponse)
async def get_study_dashboard(
    study_id: UUID,
    dashboard_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific dashboard configuration for a study.
    
    Returns the dashboard template with study-specific customizations applied.
    """
    # Check study access
    study = check_study_access(db, study_id, current_user, Permission.VIEW_DASHBOARDS)
    
    # Get the study dashboard assignment
    study_dashboard = db.exec(
        select(StudyDashboard).where(
            StudyDashboard.study_id == study_id,
            StudyDashboard.dashboard_template_id == dashboard_id,
            StudyDashboard.is_active == True
        )
    ).first()
    
    if not study_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found for this study"
        )
    
    dashboard_template = study_dashboard.dashboard_template
    
    # Apply customizations if any
    layout_config = dashboard_template.layout_config.copy()
    if study_dashboard.customizations:
        layout_config.update(study_dashboard.customizations)
    
    # Get widgets with configurations
    widgets = []
    for widget in dashboard_template.widgets:
        widget_data = {
            "id": str(widget.id),
            "widget_definition_id": str(widget.widget_definition_id),
            "widget_code": widget.widget_definition.code,
            "widget_name": widget.widget_definition.name,
            "widget_category": widget.widget_definition.category,
            "instance_config": widget.instance_config,
            "position": widget.position,
            "data_binding": widget.data_binding,
            "config_schema": widget.widget_definition.config_schema
        }
        
        # Apply widget customizations if any
        if study_dashboard.customizations and "widget_overrides" in study_dashboard.customizations:
            widget_overrides = study_dashboard.customizations["widget_overrides"].get(str(widget.id), {})
            if widget_overrides:
                widget_data["instance_config"].update(widget_overrides)
        
        widgets.append(widget_data)
    
    return StudyDashboardResponse(
        id=study_dashboard.id,
        dashboard_template_id=dashboard_template.id,
        dashboard_code=dashboard_template.code,
        dashboard_name=dashboard_template.name,
        layout_config=layout_config,
        widgets=widgets,
        customizations=study_dashboard.customizations
    )


@router.post("/{study_id}/widget-data", response_model=BatchWidgetDataResponse)
async def get_widget_data(
    study_id: UUID,
    request: WidgetDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Load data for multiple widgets in a batch.
    
    This endpoint loads actual data for widgets based on their configurations
    and the study's available datasets.
    """
    # Check study access
    study = check_study_access(db, study_id, current_user, Permission.VIEW_DATA)
    
    # TODO: Import the widget_data CRUD module once created
    # from app.crud import widget_data as crud_widget_data
    
    widget_responses = []
    errors = []
    
    for widget_id in request.widget_ids:
        try:
            # Get widget configuration
            widget = db.get(DashboardWidget, widget_id)
            if not widget:
                errors.append({
                    "widget_id": str(widget_id),
                    "error": "Widget not found"
                })
                continue
            
            # TODO: Load actual data using widget_data CRUD
            # For now, return mock data based on widget type
            widget_def = widget.widget_definition
            
            # Generate mock data based on widget category
            mock_data = {}
            if widget_def.category == "metrics":
                mock_data = {
                    "value": 342,
                    "previous_value": 298,
                    "change": 44,
                    "change_percent": 14.77,
                    "trend": "up",
                    "calculation": widget.instance_config.get("calculation", "count"),
                    "dataset": widget.instance_config.get("dataset", "ADSL"),
                    "field": widget.instance_config.get("field", "USUBJID")
                }
            elif widget_def.category == "charts":
                mock_data = {
                    "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                    "datasets": [
                        {
                            "label": "Treatment A",
                            "data": [25, 45, 78, 95],
                            "borderColor": "#3b82f6",
                            "backgroundColor": "rgba(59, 130, 246, 0.1)"
                        },
                        {
                            "label": "Treatment B",
                            "data": [22, 41, 73, 89],
                            "borderColor": "#ef4444",
                            "backgroundColor": "rgba(239, 68, 68, 0.1)"
                        }
                    ],
                    "xAxis": widget.instance_config.get("xAxis", "Time"),
                    "yAxis": widget.instance_config.get("yAxis", "Count")
                }
            elif widget_def.category == "tables":
                mock_data = {
                    "headers": ["Subject ID", "Site", "Status", "Enrollment Date"],
                    "rows": [
                        ["001-001", "Site 01", "Active", "2024-01-15"],
                        ["001-002", "Site 01", "Active", "2024-01-16"],
                        ["002-001", "Site 02", "Completed", "2024-01-10"],
                        ["002-002", "Site 02", "Active", "2024-01-12"],
                        ["003-001", "Site 03", "Screening", "2024-01-18"]
                    ],
                    "total_count": 150,
                    "page": 1,
                    "page_size": 5
                }
            
            # Apply time range filter if provided
            if request.time_range:
                mock_data["time_range"] = request.time_range
            
            # Apply additional filters if provided
            if request.filters:
                mock_data["applied_filters"] = request.filters
            
            widget_response = WidgetDataResponse(
                widget_id=widget_id,
                data=mock_data,
                metadata={
                    "widget_type": widget_def.code,
                    "widget_name": widget_def.name,
                    "study_id": str(study_id),
                    "time_range": request.time_range
                },
                last_updated=datetime.utcnow()
            )
            
            widget_responses.append(widget_response)
            
        except Exception as e:
            errors.append({
                "widget_id": str(widget_id),
                "error": str(e)
            })
            
            # Still create a response with error
            widget_responses.append(
                WidgetDataResponse(
                    widget_id=widget_id,
                    data={},
                    last_updated=datetime.utcnow(),
                    error=str(e)
                )
            )
    
    return BatchWidgetDataResponse(
        widgets=widget_responses,
        errors=errors
    )


@router.get("/{study_id}/dashboard-config")
async def get_study_dashboard_config(
    study_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get the complete dashboard configuration for a study including menu layouts.
    
    This returns the dashboard template structure with all menu items and their
    associated widget layouts.
    """
    # Check study access
    study = check_study_access(db, study_id, current_user, Permission.VIEW_DASHBOARDS)
    
    # Get the active study dashboard
    study_dashboard = db.exec(
        select(StudyDashboard).where(
            StudyDashboard.study_id == study_id,
            StudyDashboard.is_active == True
        )
    ).first()
    
    if not study_dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active dashboard found for this study"
        )
    
    dashboard_template = study_dashboard.dashboard_template
    template_structure = dashboard_template.template_structure or {}
    
    # Extract menu layouts from template structure
    menu_layouts = {}
    dashboards = template_structure.get("dashboards", [])
    
    for dashboard in dashboards:
        menu_item_id = dashboard.get("id")
        if menu_item_id:
            menu_layouts[menu_item_id] = dashboard.get("layout", dashboard.get("widgets", []))
    
    # Get the default layout (for items without specific layouts)
    default_dashboard = next((d for d in dashboards if d.get("id") == "default"), None)
    if not default_dashboard and dashboards:
        default_dashboard = dashboards[0]
    
    default_layout = default_dashboard.get("layout", default_dashboard.get("widgets", [])) if default_dashboard else []
    
    # Apply study customizations if any
    if study_dashboard.customizations and "menu_layouts" in study_dashboard.customizations:
        menu_layouts.update(study_dashboard.customizations["menu_layouts"])
    
    return {
        "id": study_dashboard.id,
        "dashboard_template_id": dashboard_template.id,
        "dashboard_code": dashboard_template.code,
        "dashboard_name": dashboard_template.name,
        "template_structure": template_structure,
        "menu_layouts": menu_layouts,
        "default_layout": default_layout,
        "customizations": study_dashboard.customizations
    }


@router.get("/{study_id}/menus", response_model=StudyMenuResponse)
async def get_study_menu(
    study_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get the menu structure for a study.
    
    Returns the menu filtered by user permissions.
    """
    # Check study access
    study = check_study_access(db, study_id, current_user)
    
    # Get the study's dashboard configuration to find the menu
    study_dashboard = db.exec(
        select(StudyDashboard).where(
            StudyDashboard.study_id == study_id,
            StudyDashboard.is_active == True
        )
    ).first()
    
    if not study_dashboard or not study_dashboard.dashboard_template:
        # Return a default menu structure if no menu is assigned
        default_menu = {
            "items": [
                {
                    "id": "overview",
                    "type": "dashboard",
                    "label": "Overview",
                    "icon": "LayoutDashboard",
                    "dashboard_code": "overview_dashboard",
                    "order": 1
                }
            ]
        }
        
        return StudyMenuResponse(
            menu_structure=default_menu,
            version=1,
            last_updated=datetime.utcnow()
        )
    
    dashboard_template = study_dashboard.dashboard_template
    
    # Extract menu structure from the template
    menu_structure = dashboard_template.template_structure.get("menu_structure", {})
    if not menu_structure:
        # Check if it's under "menu" key instead
        menu_structure = dashboard_template.template_structure.get("menu", {})
    
    if not menu_structure:
        # Return default menu if no menu structure found
        default_menu = {
            "items": [
                {
                    "id": "overview",
                    "type": "dashboard",
                    "label": "Dashboard",
                    "icon": "LayoutDashboard",
                    "dashboard_code": dashboard_template.code,
                    "order": 1
                }
            ]
        }
        
        return StudyMenuResponse(
            menu_structure=default_menu,
            version=dashboard_template.major_version,
            last_updated=dashboard_template.updated_at
        )
    
    # Get user permissions
    user_permissions = set()
    if current_user.role:
        # Extract permissions from user role
        # TODO: Implement proper permission extraction from role
        user_permissions = {"view_dashboard", "view_data"}
        
        # Add role-specific permissions
        if current_user.role.name == "admin":
            user_permissions.update(["view_safety_data", "view_efficacy_data"])
        elif current_user.role.name == "safety_officer":
            user_permissions.add("view_safety_data")
    
    # Filter menu by permissions
    filtered_menu = crud_menu.filter_menu_by_permissions(
        menu_structure,
        user_permissions
    )
    
    return StudyMenuResponse(
        menu_structure=filtered_menu,
        version=dashboard_template.major_version,
        last_updated=dashboard_template.updated_at
    )