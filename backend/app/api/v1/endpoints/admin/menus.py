# ABOUTME: DEPRECATED - Menu management is now part of unified dashboard templates
# ABOUTME: These endpoints redirect to the new dashboard template endpoints for compatibility

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlmodel import Session, select
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel
from enum import Enum

from app.api.deps import get_db, get_current_user
from app.models import User, Message
from app.core.permissions import Permission, has_permission


router = APIRouter()


# Enums
class MenuItemType(str, Enum):
    DASHBOARD = "dashboard"
    STATIC_PAGE = "static_page"
    EXTERNAL_LINK = "external"
    GROUP = "group"
    DIVIDER = "divider"


# Request/Response Models
class MenuItem(BaseModel):
    id: str
    type: MenuItemType
    label: str
    icon: Optional[str] = None
    permissions: Optional[List[str]] = None
    order: Optional[int] = None
    
    # Type-specific properties
    dashboard_code: Optional[str] = None  # For DASHBOARD type
    page_component: Optional[str] = None  # For STATIC_PAGE type
    url: Optional[str] = None  # For EXTERNAL_LINK type
    children: Optional[List['MenuItem']] = None  # For GROUP type
    
    # Visibility rules
    visible_conditions: Optional[Dict[str, Any]] = None


class MenuTemplate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    menu_structure: List[MenuItem]


class MenuTemplateResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    menu_structure: List[MenuItem]
    version: int
    is_active: bool
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime


class MenuValidationResult(BaseModel):
    is_valid: bool
    errors: List[Dict[str, str]]
    warnings: List[Dict[str, str]]
    menu_preview: Optional[Dict[str, Any]] = None


class MenuCloneRequest(BaseModel):
    new_code: str
    new_name: str
    new_description: Optional[str] = None


class MenuTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    menu_structure: Optional[List[MenuItem]] = None
    is_active: Optional[bool] = None


# Update forward reference for recursive model
MenuItem.model_rebuild()


def check_system_admin(current_user: User) -> None:
    """Check if user is a system admin"""
    if not current_user.is_superuser and not has_permission(current_user, Permission.MANAGE_SYSTEM):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only system administrators can access this endpoint"
        )


def validate_menu_structure(menu_items: List[MenuItem]) -> List[str]:
    """Validate menu structure for errors"""
    errors = []
    
    for item in menu_items:
        # For menu templates, dashboard_code is not required as it will be assigned during study setup
        # Only validate required fields for other types
        if item.type == MenuItemType.STATIC_PAGE and not item.page_component:
            errors.append(f"Menu item '{item.label}' of type STATIC_PAGE must have page_component")
        elif item.type == MenuItemType.EXTERNAL_LINK and not item.url:
            errors.append(f"Menu item '{item.label}' of type EXTERNAL_LINK must have url")
        
        # Allow empty groups in templates - they can be populated during study setup
        
        # Recursively validate children
        if item.children:
            errors.extend(validate_menu_structure(item.children))
    
    return errors


@router.get("", response_model=List[MenuTemplateResponse])
async def list_menu_templates(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name or description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    List all menu templates.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # TODO: Implement actual database query
    # For now, return mock data
    menus = []
    
    # Mock menu templates
    mock_menus = [
        {
            "id": uuid4(),
            "code": "default_study_menu",
            "name": "Default Study Menu",
            "description": "Standard menu structure for clinical studies",
            "version": 1,
            "is_active": True,
            "menu_structure": [
                {
                    "id": "overview",
                    "type": MenuItemType.DASHBOARD,
                    "label": "Overview",
                    "icon": "home",
                    "dashboard_code": "overview_dashboard",
                    "order": 1
                },
                {
                    "id": "data",
                    "type": MenuItemType.GROUP,
                    "label": "Data",
                    "icon": "database",
                    "order": 2,
                    "children": [
                        {
                            "id": "enrollment",
                            "type": MenuItemType.DASHBOARD,
                            "label": "Enrollment",
                            "icon": "users",
                            "dashboard_code": "enrollment_dashboard",
                            "order": 1
                        },
                        {
                            "id": "demographics",
                            "type": MenuItemType.DASHBOARD,
                            "label": "Demographics",
                            "icon": "user",
                            "dashboard_code": "demographics_dashboard",
                            "order": 2
                        }
                    ]
                },
                {
                    "id": "safety",
                    "type": MenuItemType.GROUP,
                    "label": "Safety",
                    "icon": "shield",
                    "order": 3,
                    "permissions": ["view_safety_data"],
                    "children": [
                        {
                            "id": "adverse_events",
                            "type": MenuItemType.DASHBOARD,
                            "label": "Adverse Events",
                            "icon": "alert-triangle",
                            "dashboard_code": "ae_dashboard",
                            "order": 1
                        },
                        {
                            "id": "lab_results",
                            "type": MenuItemType.DASHBOARD,
                            "label": "Lab Results",
                            "icon": "activity",
                            "dashboard_code": "lab_dashboard",
                            "order": 2
                        }
                    ]
                },
                {
                    "id": "divider1",
                    "type": MenuItemType.DIVIDER,
                    "label": "",
                    "order": 4
                },
                {
                    "id": "reports",
                    "type": MenuItemType.STATIC_PAGE,
                    "label": "Reports",
                    "icon": "file-text",
                    "page_component": "reports_page",
                    "order": 5
                },
                {
                    "id": "external_docs",
                    "type": MenuItemType.EXTERNAL_LINK,
                    "label": "Documentation",
                    "icon": "book",
                    "url": "https://docs.example.com",
                    "order": 6
                }
            ],
            "created_by": current_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": uuid4(),
            "code": "safety_focused_menu",
            "name": "Safety-Focused Study Menu",
            "description": "Menu structure emphasizing safety monitoring",
            "version": 1,
            "is_active": True,
            "menu_structure": [
                {
                    "id": "safety_overview",
                    "type": MenuItemType.DASHBOARD,
                    "label": "Safety Overview",
                    "icon": "shield",
                    "dashboard_code": "safety_overview_dashboard",
                    "order": 1
                },
                {
                    "id": "ae_monitoring",
                    "type": MenuItemType.GROUP,
                    "label": "AE Monitoring",
                    "icon": "alert-circle",
                    "order": 2,
                    "children": [
                        {
                            "id": "serious_ae",
                            "type": MenuItemType.DASHBOARD,
                            "label": "Serious AEs",
                            "icon": "alert-triangle",
                            "dashboard_code": "sae_dashboard",
                            "order": 1,
                            "visible_conditions": {
                                "user_roles": ["safety_officer", "medical_monitor"]
                            }
                        }
                    ]
                }
            ],
            "created_by": current_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    # Apply filters
    for menu in mock_menus:
        if is_active is not None and menu["is_active"] != is_active:
            continue
        if search and search.lower() not in menu["name"].lower() and search.lower() not in menu.get("description", "").lower():
            continue
        menus.append(menu)
    
    # Apply pagination
    total = len(menus)
    menus = menus[skip:skip + limit]
    
    return menus


@router.post("", response_model=MenuTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_template(
    menu_data: MenuTemplate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new menu template.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Validate menu structure
    errors = validate_menu_structure(menu_data.menu_structure)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid menu structure", "errors": errors}
        )
    
    # TODO: Check if menu code already exists
    # TODO: Create menu in database
    
    # Mock response
    new_menu = {
        **menu_data.dict(),
        "id": uuid4(),
        "version": 1,
        "is_active": True,
        "created_by": current_user.id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    return new_menu


@router.get("/{menu_id}", response_model=MenuTemplateResponse)
async def get_menu_template(
    menu_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get detailed information about a specific menu template.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # TODO: Fetch menu from database
    # For now, return mock data
    
    menu = {
        "id": menu_id,
        "code": "default_study_menu",
        "name": "Default Study Menu",
        "description": "Standard menu structure for clinical studies",
        "version": 1,
        "is_active": True,
        "menu_structure": [
            {
                "id": "overview",
                "type": MenuItemType.DASHBOARD,
                "label": "Overview",
                "icon": "home",
                "dashboard_code": "overview_dashboard",
                "order": 1
            },
            {
                "id": "data",
                "type": MenuItemType.GROUP,
                "label": "Data",
                "icon": "database",
                "order": 2,
                "children": [
                    {
                        "id": "enrollment",
                        "type": MenuItemType.DASHBOARD,
                        "label": "Enrollment",
                        "icon": "users",
                        "dashboard_code": "enrollment_dashboard",
                        "order": 1
                    }
                ]
            }
        ],
        "created_by": current_user.id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    return menu


@router.put("/{menu_id}", response_model=MenuTemplateResponse)
async def update_menu_template(
    menu_id: UUID,
    menu_update: MenuTemplate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update an existing menu template.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Validate menu structure
    errors = validate_menu_structure(menu_update.menu_structure)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid menu structure", "errors": errors}
        )
    
    # TODO: Fetch menu from database
    # TODO: Update menu
    # TODO: Increment version
    # TODO: Log changes to audit trail
    
    # Mock response
    updated_menu = {
        **menu_update.dict(),
        "id": menu_id,
        "version": 2,  # Increment version
        "is_active": True,
        "created_by": current_user.id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    return updated_menu


@router.delete("/{menu_id}", response_model=Message)
async def delete_menu_template(
    menu_id: UUID,
    force: bool = Query(False, description="Force delete even if menu is in use"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Delete a menu template.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # TODO: Check if menu is assigned to any studies
    # TODO: If force=False and menu is in use, return error
    # TODO: Soft delete (set is_active=False) or hard delete based on requirements
    # TODO: Log deletion to audit trail
    
    return Message(message=f"Menu template {menu_id} deleted successfully")


@router.post("/{menu_id}/validate", response_model=MenuValidationResult)
async def validate_menu_template(
    menu_id: UUID,
    test_permissions: Optional[List[str]] = Body(None, description="Test with specific permissions"),
    test_conditions: Optional[Dict[str, Any]] = Body(None, description="Test visibility conditions"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Validate a menu template and preview how it would appear.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # TODO: Fetch menu from database
    # TODO: Validate all dashboard references exist
    # TODO: Validate all page components exist
    # TODO: Apply test permissions and conditions
    # TODO: Generate preview
    
    # Mock response
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": [
            {
                "field": "menu_structure[2].children[0]",
                "message": "Dashboard 'ae_dashboard' has restricted permissions"
            }
        ],
        "menu_preview": {
            "visible_items": [
                {
                    "id": "overview",
                    "label": "Overview",
                    "type": "dashboard",
                    "visible": True
                },
                {
                    "id": "data",
                    "label": "Data",
                    "type": "group",
                    "visible": True,
                    "children": [
                        {
                            "id": "enrollment",
                            "label": "Enrollment",
                            "visible": True
                        }
                    ]
                },
                {
                    "id": "safety",
                    "label": "Safety",
                    "type": "group",
                    "visible": False,  # Hidden due to permissions
                    "reason": "Requires 'view_safety_data' permission"
                }
            ],
            "total_items": 6,
            "visible_count": 3,
            "hidden_count": 3
        }
    }
    
    # Mock validation results for now
    errors = []
    warnings = [
        {
            "field": "menu_structure[2].children[0]",
            "message": "Dashboard 'ae_dashboard' has restricted permissions"
        }
    ]
    menu_preview = {
        "visible_items": [
            {
                "id": "overview",
                "label": "Overview",
                "type": "dashboard",
                "visible": True
            },
            {
                "id": "data",
                "label": "Data",
                "type": "group",
                "visible": True,
                "children": [
                    {
                        "id": "enrollment",
                        "label": "Enrollment",
                        "visible": True
                    }
                ]
            },
            {
                "id": "safety",
                "label": "Safety",
                "type": "group",
                "visible": False,  # Hidden due to permissions
                "reason": "Requires 'view_safety_data' permission"
            }
        ],
        "total_items": 6,
        "visible_count": 3,
        "hidden_count": 3
    }
    
    return MenuValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        menu_preview=menu_preview
    )


@router.post("/{menu_id}/clone", response_model=MenuTemplateResponse, status_code=status.HTTP_201_CREATED)
async def clone_menu_template(
    menu_id: UUID,
    clone_data: MenuCloneRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Clone an existing menu template.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # TODO: Check if new code already exists in database
    # TODO: Fetch source menu from database
    # TODO: Clone menu with new code and name
    # TODO: Log activity to audit trail
    
    # Mock implementation for now
    # Return a cloned menu with the new code and name
    cloned_menu = {
        "id": uuid4(),
        "code": clone_data.new_code,
        "name": clone_data.new_name,
        "description": clone_data.new_description or "Cloned from " + str(menu_id),
        "version": 1,
        "is_active": True,
        "menu_structure": [
            {
                "id": "overview",
                "type": MenuItemType.DASHBOARD,
                "label": "Overview",
                "icon": "home",
                "dashboard_code": "overview_dashboard",
                "order": 1
            },
            {
                "id": "data",
                "type": MenuItemType.GROUP,
                "label": "Data",
                "icon": "database",
                "order": 2,
                "children": [
                    {
                        "id": "enrollment",
                        "type": MenuItemType.DASHBOARD,
                        "label": "Enrollment",
                        "icon": "users",
                        "dashboard_code": "enrollment_dashboard",
                        "order": 1
                    }
                ]
            }
        ],
        "created_by": current_user.id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    return cloned_menu