# ABOUTME: API endpoints for dashboard template management
# ABOUTME: Handles CRUD operations for dashboard templates and data requirements extraction

from typing import List, Any, Optional, Dict
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
import uuid

from app.api.deps import get_db, get_current_user
from app.models import (
    DashboardTemplate, DashboardTemplateCreate, DashboardTemplateUpdate, 
    DashboardTemplatePublic, DashboardTemplatesPublic, DashboardTemplateDataRequirements,
    DashboardCategory, User
)
from app.core.permissions import Permission, PermissionChecker

router = APIRouter()


@router.get("/", response_model=DashboardTemplatesPublic)
async def read_dashboard_templates(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    category: Optional[DashboardCategory] = None
) -> Any:
    """
    Get all available dashboard templates.
    """
    query = select(DashboardTemplate)
    
    # Filter by active status unless requested otherwise
    if not include_inactive:
        query = query.where(DashboardTemplate.is_active == True)
    
    # Filter by category if specified
    if category:
        query = query.where(DashboardTemplate.category == category)
    
    # Order by category and name
    query = query.order_by(DashboardTemplate.category, DashboardTemplate.name)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    templates = db.exec(query).all()
    
    # Count total
    count_query = select(DashboardTemplate)
    if not include_inactive:
        count_query = count_query.where(DashboardTemplate.is_active == True)
    if category:
        count_query = count_query.where(DashboardTemplate.category == category)
    
    total = len(db.exec(count_query).all())
    
    # Convert to public models and add counts
    public_templates = []
    for template in templates:
        # Count dashboards and widgets in the template
        template_structure = template.template_structure or {}
        
        dashboard_count = 0
        widget_count = 0
        
        # Handle both old format (menu.items) and new format (menu_structure + dashboards)
        if "menu_structure" in template_structure and "dashboards" in template_structure:
            # New format: A template represents ONE dashboard with multiple views
            # Each view can have widgets
            dashboard_count = 1  # One dashboard per template
            
            # Count total widgets across all views
            dashboards_array = template_structure.get("dashboards", [])
            for dashboard_view in dashboards_array:
                widgets = dashboard_view.get("widgets", [])
                widget_count += len(widgets)
        else:
            # Old format: look for menu.items
            menu_items = template_structure.get("menu", {}).get("items", [])
            
            for item in menu_items:
                if item.get("type") == "dashboard" and "dashboard" in item:
                    dashboard_count += 1
                    widgets = item["dashboard"].get("widgets", [])
                    widget_count += len(widgets)
        
        # Create public template with all required fields
        template_dict = template.model_dump()
        template_dict["version"] = template.major_version
        template_dict["dashboard_count"] = dashboard_count
        template_dict["widget_count"] = widget_count
        
        public_template = DashboardTemplatePublic.model_validate(template_dict)
        public_templates.append(public_template)
    
    return DashboardTemplatesPublic(data=public_templates, count=total)


@router.get("/{template_id}", response_model=DashboardTemplatePublic)
async def read_dashboard_template(
    *,
    db: Session = Depends(get_db),
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get dashboard template by ID.
    """
    template = db.get(DashboardTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard template not found"
        )
    
    # Count dashboards and widgets in the template
    template_structure = template.template_structure or {}
    
    dashboard_count = 0
    widget_count = 0
    
    # Handle both old format (menu.items) and new format (menu_structure + dashboards)
    if "menu_structure" in template_structure and "dashboards" in template_structure:
        # New format: A template represents ONE dashboard with multiple views
        # Each view can have widgets
        dashboard_count = 1  # One dashboard per template
        
        # Count total widgets across all views
        dashboards_array = template_structure.get("dashboards", [])
        for dashboard_view in dashboards_array:
            widgets = dashboard_view.get("widgets", [])
            widget_count += len(widgets)
    else:
        # Old format: look for menu.items
        menu_items = template_structure.get("menu", {}).get("items", [])
        
        for item in menu_items:
            if item.get("type") == "dashboard" and "dashboard" in item:
                dashboard_count += 1
                widgets = item["dashboard"].get("widgets", [])
                widget_count += len(widgets)
    
    # Create public template with all required fields
    template_dict = template.model_dump()
    template_dict["version"] = template.major_version
    template_dict["dashboard_count"] = dashboard_count
    template_dict["widget_count"] = widget_count
    
    public_template = DashboardTemplatePublic.model_validate(template_dict)
    return public_template


@router.get("/{template_id}/data-requirements", response_model=DashboardTemplateDataRequirements)
async def get_template_data_requirements(
    *,
    db: Session = Depends(get_db),
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Extract data requirements from a dashboard template.
    Returns required datasets, fields, and widget-specific requirements.
    """
    template = db.get(DashboardTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard template not found"
        )
    
    # Extract data requirements from template structure
    template_structure = template.template_structure or {}
    data_mappings = template_structure.get("data_mappings", {})
    
    required_datasets = data_mappings.get("required_datasets", [])
    field_mappings = data_mappings.get("field_mappings", {})
    
    # Extract widget-specific requirements
    widget_requirements = []
    
    # Handle both old format (menu.items) and new format (menu_structure + dashboards)
    if "menu_structure" in template_structure and "dashboards" in template_structure:
        # New format: iterate through dashboards array
        dashboards = template_structure.get("dashboards", [])
        for dashboard in dashboards:
            widgets = dashboard.get("widgets", [])
            for widget in widgets:
                if "data_requirements" in widget:
                    widget_req = {
                        "widget_code": widget.get("type"),  # In new format, it's 'type' not 'widget_code'
                        "title": widget.get("config", {}).get("title"),  # In new format, it's 'config' not 'instance_config'
                        "requirements": widget["data_requirements"]
                    }
                    widget_requirements.append(widget_req)
    else:
        # Old format: look for menu.items
        menu_items = template_structure.get("menu", {}).get("items", [])
        
        for item in menu_items:
            if item.get("type") == "dashboard" and "dashboard" in item:
                widgets = item["dashboard"].get("widgets", [])
                for widget in widgets:
                    if "data_requirements" in widget:
                        widget_req = {
                            "widget_code": widget.get("widget_code"),
                            "title": widget.get("instance_config", {}).get("title"),
                            "requirements": widget["data_requirements"]
                        }
                        widget_requirements.append(widget_req)
    
    return DashboardTemplateDataRequirements(
        template_id=template.id,
        template_code=template.code,
        required_datasets=required_datasets,
        field_mappings=field_mappings,
        widget_requirements=widget_requirements
    )


@router.post("/", response_model=DashboardTemplatePublic)
async def create_dashboard_template(
    *,
    db: Session = Depends(get_db),
    template_in: DashboardTemplateCreate,
    current_user: User = Depends(PermissionChecker(Permission.MANAGE_SYSTEM))
) -> Any:
    """
    Create new dashboard template. Requires MANAGE_TEMPLATES permission.
    """
    # Check if code already exists
    existing = db.exec(
        select(DashboardTemplate).where(DashboardTemplate.code == template_in.code)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template with this code already exists"
        )
    
    # Create template
    template = DashboardTemplate(
        **template_in.model_dump(),
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    
    # Count dashboards and widgets in the template
    template_structure = template.template_structure or {}
    
    dashboard_count = 0
    widget_count = 0
    
    # Handle both old format (menu.items) and new format (menu_structure + dashboards)
    if "menu_structure" in template_structure and "dashboards" in template_structure:
        # New format: A template represents ONE dashboard with multiple views
        # Each view can have widgets
        dashboard_count = 1  # One dashboard per template
        
        # Count total widgets across all views
        dashboards_array = template_structure.get("dashboards", [])
        for dashboard_view in dashboards_array:
            widgets = dashboard_view.get("widgets", [])
            widget_count += len(widgets)
    else:
        # Old format: look for menu.items
        menu_items = template_structure.get("menu", {}).get("items", [])
        
        for item in menu_items:
            if item.get("type") == "dashboard" and "dashboard" in item:
                dashboard_count += 1
                widgets = item["dashboard"].get("widgets", [])
                widget_count += len(widgets)
    
    # Create public template with all required fields
    template_dict = template.model_dump()
    template_dict["version"] = template.major_version
    template_dict["dashboard_count"] = dashboard_count
    template_dict["widget_count"] = widget_count
    
    public_template = DashboardTemplatePublic.model_validate(template_dict)
    return public_template


@router.patch("/{template_id}", response_model=DashboardTemplatePublic)
async def update_dashboard_template(
    *,
    db: Session = Depends(get_db),
    template_id: uuid.UUID,
    template_in: DashboardTemplateUpdate,
    current_user: User = Depends(PermissionChecker(Permission.MANAGE_SYSTEM))
) -> Any:
    """
    Update dashboard template. Requires MANAGE_TEMPLATES permission.
    """
    template = db.get(DashboardTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard template not found"
        )
    
    # Update fields
    update_data = template_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    template.updated_at = datetime.utcnow()
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    # Count dashboards and widgets in the template
    template_structure = template.template_structure or {}
    
    dashboard_count = 0
    widget_count = 0
    
    # Handle both old format (menu.items) and new format (menu_structure + dashboards)
    if "menu_structure" in template_structure and "dashboards" in template_structure:
        # New format: A template represents ONE dashboard with multiple views
        # Each view can have widgets
        dashboard_count = 1  # One dashboard per template
        
        # Count total widgets across all views
        dashboards_array = template_structure.get("dashboards", [])
        for dashboard_view in dashboards_array:
            widgets = dashboard_view.get("widgets", [])
            widget_count += len(widgets)
    else:
        # Old format: look for menu.items
        menu_items = template_structure.get("menu", {}).get("items", [])
        
        for item in menu_items:
            if item.get("type") == "dashboard" and "dashboard" in item:
                dashboard_count += 1
                widgets = item["dashboard"].get("widgets", [])
                widget_count += len(widgets)
    
    # Create public template with all required fields
    template_dict = template.model_dump()
    template_dict["version"] = template.major_version
    template_dict["dashboard_count"] = dashboard_count
    template_dict["widget_count"] = widget_count
    
    public_template = DashboardTemplatePublic.model_validate(template_dict)
    return public_template


@router.delete("/{template_id}")
async def delete_dashboard_template(
    *,
    db: Session = Depends(get_db),
    template_id: uuid.UUID,
    current_user: User = Depends(PermissionChecker(Permission.MANAGE_SYSTEM))
) -> Any:
    """
    Delete (deactivate) dashboard template. Requires MANAGE_TEMPLATES permission.
    """
    template = db.get(DashboardTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard template not found"
        )
    
    # Check if template is in use
    if len(template.study_dashboards) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete template. It is used by {len(template.study_dashboards)} studies."
        )
    
    # Soft delete by deactivating
    template.is_active = False
    template.updated_at = datetime.utcnow()
    
    db.add(template)
    db.commit()
    
    return {"message": "Dashboard template deactivated successfully"}


