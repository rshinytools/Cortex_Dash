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
from app.models.dashboard import (
    TemplateDraft, TemplateDraftCreate, TemplateDraftUpdate,
    TemplateVersion, TemplateVersionCreate,
    TemplateChangeLog
)
from app.services.template_draft_service import TemplateDraftService
from app.services.template_auto_version import TemplateAutoVersionService
from app.services.template_change_detector import TemplateChangeDetector, ChangeType
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
        
        # Count dashboards and widgets
        dashboards_array = template_structure.get("dashboardTemplates", [])
        dashboard_count = len(dashboards_array)
        
        # Count total widgets across all dashboards
        for dashboard in dashboards_array:
            widgets = dashboard.get("widgets", [])
            widget_count += len(widgets)
        
        # Create public template with all required fields
        template_dict = template.model_dump()
        template_dict["version"] = f"{template.major_version}.{template.minor_version}.{template.patch_version}"
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
    
    # A template always represents ONE dashboard
    dashboard_count = 1
    widget_count = 0
    
    # Count widgets from dashboard templates
    widget_count = 0
    dashboards = template_structure.get("dashboardTemplates", [])
    dashboard_count = len(dashboards)
    for dashboard in dashboards:
        widgets = dashboard.get("widgets", [])
        widget_count += len(widgets)
    
    # Count menu items from menu_structure
    menu_structure = template_structure.get("menu_structure", {})
    def count_menu_items(items):
        count = 0
        for item in items:
            count += 1
            if "children" in item and isinstance(item["children"], list):
                count += count_menu_items(item["children"])
        return count
    menu_items = menu_structure.get("items", [])
    menu_count = count_menu_items(menu_items)
    
    # Create public template with all required fields
    template_dict = template.model_dump()
    template_dict["version"] = f"{template.major_version}.{template.minor_version}.{template.patch_version}"
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
    
    # Iterate through dashboardTemplates array
    dashboards = template_structure.get("dashboardTemplates", [])
    for dashboard in dashboards:
        widgets = dashboard.get("widgets", [])
        for widget in widgets:
            # Check if widget has instance data
            widget_instance = widget.get("widgetInstance", {})
            widget_def = widget_instance.get("widgetDefinition", {})
            if widget_def.get("data_requirements"):
                widget_req = {
                    "widget_code": widget_def.get("code", widget_def.get("type")),
                    "title": widget_instance.get("config", {}).get("title", widget_def.get("name")),
                    "requirements": widget_def["data_requirements"]
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
    
    # A template always represents ONE dashboard
    dashboard_count = 1
    widget_count = 0
    
    # Count widgets from dashboard templates
    widget_count = 0
    dashboards = template_structure.get("dashboardTemplates", [])
    dashboard_count = len(dashboards)
    for dashboard in dashboards:
        widgets = dashboard.get("widgets", [])
        widget_count += len(widgets)
    
    # Count menu items from menu_structure
    menu_structure = template_structure.get("menu_structure", {})
    def count_menu_items(items):
        count = 0
        for item in items:
            count += 1
            if "children" in item and isinstance(item["children"], list):
                count += count_menu_items(item["children"])
        return count
    menu_items = menu_structure.get("items", [])
    menu_count = count_menu_items(menu_items)
    
    # Create public template with all required fields
    template_dict = template.model_dump()
    template_dict["version"] = f"{template.major_version}.{template.minor_version}.{template.patch_version}"
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
    import json
    print(f"[BACKEND] Updating template {template_id}")
    print(f"[BACKEND] Received data: {template_in.model_dump()}")
    if hasattr(template_in, 'template_structure') and template_in.template_structure:
        print(f"[BACKEND] template_structure keys: {template_in.template_structure.keys() if isinstance(template_in.template_structure, dict) else 'not a dict'}")
        if isinstance(template_in.template_structure, dict):
            dashboards = template_in.template_structure.get('dashboardTemplates', [])
            print(f"[BACKEND] dashboardTemplates count: {len(dashboards)}")
            for idx, dashboard in enumerate(dashboards):
                if isinstance(dashboard, dict):
                    widgets = dashboard.get('widgets', [])
                    print(f"[BACKEND] Dashboard {idx}: {dashboard.get('name', 'unnamed')}, widgets: {len(widgets)}")
    
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
    
    # A template always represents ONE dashboard
    dashboard_count = 1
    widget_count = 0
    
    # Count widgets from dashboard templates
    widget_count = 0
    dashboards = template_structure.get("dashboardTemplates", [])
    dashboard_count = len(dashboards)
    for dashboard in dashboards:
        widgets = dashboard.get("widgets", [])
        widget_count += len(widgets)
    
    # Count menu items from menu_structure
    menu_structure = template_structure.get("menu_structure", {})
    def count_menu_items(items):
        count = 0
        for item in items:
            count += 1
            if "children" in item and isinstance(item["children"], list):
                count += count_menu_items(item["children"])
        return count
    menu_items = menu_structure.get("items", [])
    menu_count = count_menu_items(menu_items)
    
    # Create public template with all required fields
    template_dict = template.model_dump()
    template_dict["version"] = f"{template.major_version}.{template.minor_version}.{template.patch_version}"
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


# Draft Management Endpoints

@router.get("/{template_id}/draft")
async def get_template_draft(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID
) -> Any:
    """
    Get or create active draft for template editing.
    """
    draft_service = TemplateDraftService(db)
    draft = await draft_service.get_or_create_draft(template_id, current_user.id)
    
    return {
        "id": draft.id,
        "template_id": draft.template_id,
        "draft_content": draft.draft_content,
        "changes_summary": draft.changes_summary,
        "created_at": draft.created_at,
        "updated_at": draft.updated_at,
        "auto_save_at": draft.auto_save_at
    }


@router.put("/{template_id}/draft")
async def update_template_draft(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID,
    content: Dict[str, Any]
) -> Any:
    """
    Update draft content with automatic change tracking.
    """
    draft_service = TemplateDraftService(db)
    
    # Get or create draft first
    draft = await draft_service.get_or_create_draft(template_id, current_user.id)
    
    # Update draft
    draft = await draft_service.update_draft(
        draft_id=draft.id,
        user_id=current_user.id,
        content=content,
        track_changes=True
    )
    
    return {
        "id": draft.id,
        "changes_summary": draft.changes_summary,
        "updated_at": draft.updated_at,
        "auto_save_at": draft.auto_save_at
    }


@router.delete("/{template_id}/draft")
async def discard_template_draft(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID
) -> Any:
    """
    Discard active draft changes.
    """
    draft_service = TemplateDraftService(db)
    
    # Find user's active draft
    draft = db.query(TemplateDraft).filter(
        TemplateDraft.template_id == template_id,
        TemplateDraft.created_by == current_user.id,
        TemplateDraft.is_active == True
    ).first()
    
    if draft:
        await draft_service.discard_draft(draft.id, current_user.id)
    
    return {"message": "Draft discarded successfully"}


# Version Management Endpoints

@router.get("/{template_id}/versions")
async def get_template_versions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50
) -> Any:
    """
    Get version history for a template.
    """
    versions = db.query(TemplateVersion).filter(
        TemplateVersion.template_id == template_id
    ).order_by(
        TemplateVersion.major_version.desc(),
        TemplateVersion.minor_version.desc(),
        TemplateVersion.patch_version.desc()
    ).offset(skip).limit(limit).all()
    
    version_list = []
    for version in versions:
        version_list.append({
            "id": version.id,
            "version": version.version_string,
            "version_type": version.version_type,
            "auto_created": version.auto_created,
            "change_description": version.change_description,
            "change_summary": version.change_summary,
            "created_by_name": version.created_by_name,
            "created_at": version.created_at,
            "breaking_changes": version.breaking_changes
        })
    
    return {
        "versions": version_list,
        "total": db.query(TemplateVersion).filter(
            TemplateVersion.template_id == template_id
        ).count()
    }


@router.get("/{template_id}/versions/{version_id}")
async def get_template_version(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID,
    version_id: uuid.UUID
) -> Any:
    """
    Get specific version details including full template structure.
    """
    version = db.query(TemplateVersion).filter(
        TemplateVersion.id == version_id,
        TemplateVersion.template_id == template_id
    ).first()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    return {
        "id": version.id,
        "version": version.version_string,
        "version_type": version.version_type,
        "template_structure": version.template_structure,
        "change_description": version.change_description,
        "change_summary": version.change_summary,
        "migration_notes": version.migration_notes,
        "breaking_changes": version.breaking_changes,
        "created_by_name": version.created_by_name,
        "created_at": version.created_at
    }


@router.post("/{template_id}/versions", dependencies=[Depends(PermissionChecker(Permission.EDIT_DASHBOARD))])
async def create_template_version(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID,
    version_data: Dict[str, Any]
) -> Any:
    """
    Manually create a new version from current draft or template state.
    """
    template = db.get(DashboardTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Get active draft if exists
    draft = db.query(TemplateDraft).filter(
        TemplateDraft.template_id == template_id,
        TemplateDraft.created_by == current_user.id,
        TemplateDraft.is_active == True
    ).first()
    
    # Use draft content or current template content
    if draft:
        template_content = draft.draft_content
    else:
        # Extract from template_structure
        template_data = template.template_structure or {}
        template_content = {
            "name": template.name,
            "description": template.description,
            "menu_structure": template_data.get("menu_structure", {"items": []}),
            "dashboardTemplates": template_data.get("dashboardTemplates", []),
            "theme": template_data.get("theme", {}),
            "settings": template_data.get("settings", {})
        }
    
    # Determine version type
    version_type = ChangeType(version_data.get("version_type", "patch"))
    
    # Calculate new version numbers
    new_major = template.major_version
    new_minor = template.minor_version
    new_patch = template.patch_version
    
    if version_type == ChangeType.MAJOR:
        new_major += 1
        new_minor = 0
        new_patch = 0
    elif version_type == ChangeType.MINOR:
        new_minor += 1
        new_patch = 0
    else:  # PATCH
        new_patch += 1
    
    # Create version
    change_detector = TemplateChangeDetector()
    version = TemplateVersion(
        template_id=template_id,
        major_version=new_major,
        minor_version=new_minor,
        patch_version=new_patch,
        template_structure=template_content,
        change_description=version_data.get("change_description", "Manual version"),
        migration_notes=version_data.get("migration_notes"),
        breaking_changes=version_data.get("breaking_changes", False),
        version_type=version_type.value,
        auto_created=False,
        created_by_name=current_user.full_name or current_user.email,
        comparison_hash=change_detector._generate_hash(template_content),
        created_by=current_user.id
    )
    
    db.add(version)
    
    # Update template version numbers
    template.major_version = new_major
    template.minor_version = new_minor
    template.patch_version = new_patch
    
    # Update template content
    template.name = template_content.get('name', template.name)
    template.description = template_content.get('description', template.description)
    
    # Update template_structure JSON field with the complete content
    template.template_structure = {
        'menu_structure': template_content.get('menu_structure', {"items": []}),
        'dashboardTemplates': template_content.get('dashboardTemplates', []),
        'theme': template_content.get('theme', {}),
        'settings': template_content.get('settings', {}),
        'data_mappings': template_content.get('data_mappings', {})
    }
    
    # Mark draft as inactive if exists
    if draft:
        draft.is_active = False
        draft.conflict_status = f"Versioned as {new_major}.{new_minor}.{new_patch}"
    
    db.commit()
    db.refresh(version)
    
    return {
        "id": version.id,
        "version": version.version_string,
        "message": f"Version {version.version_string} created successfully"
    }


@router.post("/{template_id}/versions/{version_id}/restore", dependencies=[Depends(PermissionChecker(Permission.EDIT_DASHBOARD))])
async def restore_template_version(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID,
    version_id: uuid.UUID
) -> Any:
    """
    Restore template to a previous version (creates new version).
    """
    # Get the version to restore
    version = db.query(TemplateVersion).filter(
        TemplateVersion.id == version_id,
        TemplateVersion.template_id == template_id
    ).first()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    template = db.get(DashboardTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Create new version with restored content
    new_version = TemplateVersion(
        template_id=template_id,
        major_version=template.major_version,
        minor_version=template.minor_version + 1,
        patch_version=0,
        template_structure=version.template_structure,
        change_description=f"Restored from version {version.version_string}",
        version_type="minor",
        auto_created=False,
        created_by_name=current_user.full_name or current_user.email,
        created_by=current_user.id
    )
    
    db.add(new_version)
    
    # Update template
    template.major_version = new_version.major_version
    template.minor_version = new_version.minor_version
    template.patch_version = new_version.patch_version
    
    if version.template_structure:
        template.name = version.template_structure.get('name', template.name)
        template.description = version.template_structure.get('description', template.description)
        template.menu_structure = version.template_structure.get('menu_structure', template.menu_structure)
        template.dashboard_templates = version.template_structure.get('dashboardTemplates', template.dashboard_templates)
        template.theme = version.template_structure.get('theme', template.theme)
        template.settings = version.template_structure.get('settings', template.settings)
    
    db.commit()
    db.refresh(new_version)
    
    return {
        "id": new_version.id,
        "version": new_version.version_string,
        "message": f"Template restored to version {version.version_string}"
    }


@router.get("/{template_id}/versions/compare")
async def compare_template_versions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID,
    version1_id: uuid.UUID,
    version2_id: uuid.UUID
) -> Any:
    """
    Compare two template versions and show differences.
    """
    version1 = db.query(TemplateVersion).filter(
        TemplateVersion.id == version1_id,
        TemplateVersion.template_id == template_id
    ).first()
    
    version2 = db.query(TemplateVersion).filter(
        TemplateVersion.id == version2_id,
        TemplateVersion.template_id == template_id
    ).first()
    
    if not version1 or not version2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both versions not found"
        )
    
    # Use change detector to compare
    change_detector = TemplateChangeDetector()
    change_type, changes = change_detector.detect_changes(
        version1.template_structure or {},
        version2.template_structure or {}
    )
    
    return {
        "version1": {
            "id": version1.id,
            "version": version1.version_string,
            "created_at": version1.created_at
        },
        "version2": {
            "id": version2.id,
            "version": version2.version_string,
            "created_at": version2.created_at
        },
        "change_type": change_type.value,
        "changes": changes,
        "summary": change_detector.generate_change_summary(changes),
        "has_breaking_changes": change_detector.has_breaking_changes(changes)
    }


@router.post("/{template_id}/versions/{version_id}/restore")
async def restore_template_version(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID,
    version_id: uuid.UUID
) -> Any:
    """
    Restore a template to a specific version.
    """
    template = db.get(DashboardTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    version = db.get(TemplateVersion, version_id)
    if not version or version.template_id != template_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    # Create a new version with the content from the selected version
    new_patch = template.patch_version + 1
    
    # Create new version
    new_version = TemplateVersion(
        template_id=template_id,
        major_version=template.major_version,
        minor_version=template.minor_version,
        patch_version=new_patch,
        template_structure=version.template_structure,
        change_description=f"Restored from version {version.version_string}",
        version_type="patch",
        auto_created=False,
        created_by_name=current_user.full_name or current_user.email,
        created_by=current_user.id
    )
    
    db.add(new_version)
    
    # Update template with restored content
    template.patch_version = new_patch
    template.template_structure = version.template_structure
    
    # Extract name and description if available
    if version.template_structure:
        template.name = version.template_structure.get('name', template.name)
        template.description = version.template_structure.get('description', template.description)
    
    db.commit()
    db.refresh(new_version)
    
    return {
        "id": new_version.id,
        "version": new_version.version_string,
        "message": f"Successfully restored template to version {version.version_string}"
    }


@router.get("/{template_id}/version-status")
async def get_template_version_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID
) -> Any:
    """
    Get current version status and draft information.
    """
    template = db.get(DashboardTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Get active drafts
    active_drafts = db.query(TemplateDraft).filter(
        TemplateDraft.template_id == template_id,
        TemplateDraft.is_active == True
    ).all()
    
    # Get recent changes
    draft_service = TemplateDraftService(db)
    recent_changes = await draft_service.get_recent_changes(template_id, limit=10)
    
    # Calculate next version suggestions
    change_counts = {"major": 0, "minor": 0, "patch": 0}
    for change in recent_changes:
        change_counts[change.change_type] = change_counts.get(change.change_type, 0) + 1
    
    suggested_version_type = "patch"
    if change_counts["major"] > 0:
        suggested_version_type = "major"
    elif change_counts["minor"] > 0:
        suggested_version_type = "minor"
    
    return {
        "current_version": template.version_string,
        "active_drafts": len(active_drafts),
        "draft_users": [
            {
                "user_id": draft.created_by,
                "user_name": "User",  # Creator relationship is not available
                "last_update": draft.updated_at
            }
            for draft in active_drafts
        ],
        "recent_changes": len(recent_changes),
        "change_breakdown": change_counts,
        "suggested_version_type": suggested_version_type,
        "last_version_created": template.updated_at
    }


@router.get("/{template_id}/changes")
async def get_template_changes(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50
) -> Any:
    """
    Get recent changes for a template.
    """
    changes = db.query(TemplateChangeLog).filter(
        TemplateChangeLog.template_id == template_id
    ).order_by(
        TemplateChangeLog.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    change_list = []
    for change in changes:
        change_list.append({
            "id": change.id,
            "change_type": change.change_type,
            "change_category": change.change_category,
            "change_description": change.change_description,
            "created_by_name": change.creator.name if change.creator else "Unknown",
            "created_at": change.created_at
        })
    
    return {
        "changes": change_list,
        "total": db.query(TemplateChangeLog).filter(
            TemplateChangeLog.template_id == template_id
        ).count()
    }


