# ABOUTME: CRUD operations for menu templates and navigation management
# ABOUTME: Handles hierarchical menu structures with permission-based visibility

from typing import List, Optional, Dict, Any, Set
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy import and_
import uuid

from app.models import (
    MenuTemplate,
    MenuTemplateCreate,
    MenuTemplateUpdate,
    User
)


def create_menu(
    db: Session,
    menu_create: MenuTemplateCreate,
    current_user: User
) -> MenuTemplate:
    """Create a new menu template"""
    # Validate menu structure before creating
    if not validate_menu_structure(menu_create.menu_structure):
        raise ValueError("Invalid menu structure")
    
    db_menu = MenuTemplate(
        **menu_create.model_dump(),
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    return db_menu


def get_menu(db: Session, menu_id: uuid.UUID) -> Optional[MenuTemplate]:
    """Get menu template by ID"""
    return db.get(MenuTemplate, menu_id)


def get_menu_by_code(db: Session, code: str) -> Optional[MenuTemplate]:
    """Get menu template by unique code"""
    return db.exec(
        select(MenuTemplate).where(MenuTemplate.code == code)
    ).first()


def get_menus(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[MenuTemplate]:
    """Get list of menu templates with optional filters"""
    query = select(MenuTemplate)
    
    if is_active is not None:
        query = query.where(MenuTemplate.is_active == is_active)
    
    query = query.order_by(MenuTemplate.name)
    query = query.offset(skip).limit(limit)
    
    return list(db.exec(query).all())


def update_menu(
    db: Session,
    menu_id: uuid.UUID,
    menu_update: MenuTemplateUpdate,
    current_user: User
) -> Optional[MenuTemplate]:
    """Update menu template"""
    db_menu = db.get(MenuTemplate, menu_id)
    if not db_menu:
        return None
    
    update_data = menu_update.model_dump(exclude_unset=True)
    
    # Validate menu structure if it's being updated
    if "menu_structure" in update_data:
        if not validate_menu_structure(update_data["menu_structure"]):
            raise ValueError("Invalid menu structure")
        # Increment version for structure changes
        update_data["version"] = db_menu.version + 1
    
    update_data["updated_at"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(db_menu, field, value)
    
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    return db_menu


def delete_menu(db: Session, menu_id: uuid.UUID) -> bool:
    """Soft delete menu by setting is_active to False"""
    db_menu = db.get(MenuTemplate, menu_id)
    if not db_menu:
        return False
    
    # Check if menu is in use by any study dashboards
    from app.models import StudyDashboard
    menu_usage = db.exec(
        select(StudyDashboard).where(
            StudyDashboard.menu_template_id == menu_id,
            StudyDashboard.is_active == True
        ).limit(1)
    ).first()
    
    if menu_usage:
        # Don't delete if menu is in use
        return False
    
    db_menu.is_active = False
    db_menu.updated_at = datetime.utcnow()
    db.add(db_menu)
    db.commit()
    return True


def validate_menu_structure(menu_structure: Dict[str, Any]) -> bool:
    """Validate that the menu structure is properly formatted"""
    if not isinstance(menu_structure, dict):
        return False
    
    if "items" not in menu_structure:
        return False
    
    if not isinstance(menu_structure["items"], list):
        return False
    
    # Validate each menu item
    return all(
        validate_menu_item(item) for item in menu_structure["items"]
    )


def validate_menu_item(item: Dict[str, Any]) -> bool:
    """Validate a single menu item structure"""
    required_fields = ["id", "label", "type"]
    
    # Check required fields
    if not all(field in item for field in required_fields):
        return False
    
    # Validate type
    valid_types = ["dashboard", "group", "link", "separator"]
    if item["type"] not in valid_types:
        return False
    
    # Type-specific validation
    if item["type"] == "dashboard" and "dashboard_code" not in item:
        return False
    
    if item["type"] == "link" and "url" not in item:
        return False
    
    if item["type"] == "group":
        if "children" not in item or not isinstance(item["children"], list):
            return False
        # Recursively validate children
        if not all(validate_menu_item(child) for child in item["children"]):
            return False
    
    return True


def get_menu_dashboard_codes(menu_structure: Dict[str, Any]) -> Set[str]:
    """Extract all dashboard codes referenced in a menu structure"""
    dashboard_codes = set()
    
    def extract_from_items(items: List[Dict[str, Any]]):
        for item in items:
            if item.get("type") == "dashboard" and "dashboard_code" in item:
                dashboard_codes.add(item["dashboard_code"])
            elif item.get("type") == "group" and "children" in item:
                extract_from_items(item["children"])
    
    if "items" in menu_structure:
        extract_from_items(menu_structure["items"])
    
    return dashboard_codes


def filter_menu_by_permissions(
    menu_structure: Dict[str, Any],
    user_permissions: Set[str]
) -> Dict[str, Any]:
    """Filter menu items based on user permissions"""
    def filter_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        filtered = []
        
        for item in items:
            # Check permissions
            item_permissions = set(item.get("permissions", []))
            if item_permissions and not item_permissions.intersection(user_permissions):
                continue
            
            # Handle groups recursively
            if item.get("type") == "group" and "children" in item:
                filtered_children = filter_items(item["children"])
                if filtered_children:  # Only include group if it has visible children
                    filtered_item = item.copy()
                    filtered_item["children"] = filtered_children
                    filtered.append(filtered_item)
            else:
                filtered.append(item)
        
        return filtered
    
    filtered_structure = menu_structure.copy()
    if "items" in filtered_structure:
        filtered_structure["items"] = filter_items(filtered_structure["items"])
    
    return filtered_structure


def clone_menu(
    db: Session,
    menu_id: uuid.UUID,
    new_name: str,
    new_code: str,
    current_user: User
) -> Optional[MenuTemplate]:
    """Clone an existing menu template"""
    source_menu = get_menu(db, menu_id)
    if not source_menu:
        return None
    
    # Create new menu
    new_menu = MenuTemplate(
        code=new_code,
        name=new_name,
        description=f"Cloned from {source_menu.name}",
        menu_structure=source_menu.menu_structure.copy(),
        version=1,
        is_active=True,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_menu)
    db.commit()
    db.refresh(new_menu)
    
    return new_menu


def get_menu_statistics(db: Session, menu_id: uuid.UUID) -> Dict[str, Any]:
    """Get statistics about menu usage"""
    menu = get_menu(db, menu_id)
    if not menu:
        return {}
    
    # Count items by type
    item_counts = {"dashboard": 0, "group": 0, "link": 0, "separator": 0}
    
    def count_items(items: List[Dict[str, Any]]):
        for item in items:
            item_type = item.get("type", "")
            if item_type in item_counts:
                item_counts[item_type] += 1
            if item_type == "group" and "children" in item:
                count_items(item["children"])
    
    if "items" in menu.menu_structure:
        count_items(menu.menu_structure["items"])
    
    # Get dashboard codes
    dashboard_codes = get_menu_dashboard_codes(menu.menu_structure)
    
    # Count study usage
    from app.models import StudyDashboard
    study_count = db.exec(
        select(StudyDashboard).where(
            StudyDashboard.menu_template_id == menu_id,
            StudyDashboard.is_active == True
        )
    ).count()
    
    return {
        "menu_id": str(menu.id),
        "code": menu.code,
        "version": menu.version,
        "item_counts": item_counts,
        "total_items": sum(item_counts.values()),
        "dashboard_codes": list(dashboard_codes),
        "study_count": study_count,
        "last_updated": menu.updated_at.isoformat()
    }