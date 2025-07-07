# ABOUTME: CRUD operations for unified dashboard templates with embedded menus and data mappings
# ABOUTME: Manages complete dashboard templates, study assignments, and data requirement extraction

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy import and_, or_
import uuid
import json

from app.models import (
    DashboardTemplate,
    DashboardTemplateCreate,
    DashboardTemplateUpdate,
    StudyDashboard,
    StudyDashboardCreate,
    User,
    Study,
    DashboardCategory,
    DashboardTemplateDataRequirements
)


def create_dashboard(
    db: Session,
    dashboard_create: DashboardTemplateCreate,
    current_user: User
) -> DashboardTemplate:
    """Create a new dashboard template"""
    db_dashboard = DashboardTemplate(
        **dashboard_create.model_dump(),
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_dashboard)
    db.commit()
    db.refresh(db_dashboard)
    return db_dashboard


def get_dashboard(db: Session, dashboard_id: uuid.UUID) -> Optional[DashboardTemplate]:
    """Get dashboard template by ID"""
    return db.get(DashboardTemplate, dashboard_id)


def get_dashboard_by_code(db: Session, code: str) -> Optional[DashboardTemplate]:
    """Get dashboard template by unique code"""
    return db.exec(
        select(DashboardTemplate).where(DashboardTemplate.code == code)
    ).first()


def get_dashboards(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category: Optional[DashboardCategory] = None,
    is_active: Optional[bool] = None
) -> List[DashboardTemplate]:
    """Get list of dashboard templates with optional filters"""
    query = select(DashboardTemplate)
    
    conditions = []
    if category:
        conditions.append(DashboardTemplate.category == category)
    if is_active is not None:
        conditions.append(DashboardTemplate.is_active == is_active)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(DashboardTemplate.category, DashboardTemplate.name)
    query = query.offset(skip).limit(limit)
    
    return list(db.exec(query).all())


def update_dashboard(
    db: Session,
    dashboard_id: uuid.UUID,
    dashboard_update: DashboardTemplateUpdate,
    current_user: User
) -> Optional[DashboardTemplate]:
    """Update dashboard template"""
    db_dashboard = db.get(DashboardTemplate, dashboard_id)
    if not db_dashboard:
        return None
    
    update_data = dashboard_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    # Track if version should be incremented
    if "template_structure" in update_data:
        update_data["version"] = db_dashboard.version + 1
    
    for field, value in update_data.items():
        setattr(db_dashboard, field, value)
    
    db.add(db_dashboard)
    db.commit()
    db.refresh(db_dashboard)
    return db_dashboard


def delete_dashboard(db: Session, dashboard_id: uuid.UUID) -> bool:
    """Soft delete dashboard by setting is_active to False"""
    db_dashboard = db.get(DashboardTemplate, dashboard_id)
    if not db_dashboard:
        return False
    
    # Check if dashboard is assigned to any studies
    study_usage = db.exec(
        select(StudyDashboard).where(
            StudyDashboard.dashboard_template_id == dashboard_id,
            StudyDashboard.is_active == True
        ).limit(1)
    ).first()
    
    if study_usage:
        # Don't delete if dashboard is in use
        return False
    
    db_dashboard.is_active = False
    db_dashboard.updated_at = datetime.utcnow()
    db.add(db_dashboard)
    db.commit()
    return True


def clone_dashboard(
    db: Session,
    dashboard_id: uuid.UUID,
    new_name: str,
    new_code: str,
    current_user: User
) -> Optional[DashboardTemplate]:
    """Clone an existing dashboard template with complete structure"""
    source_dashboard = get_dashboard(db, dashboard_id)
    if not source_dashboard:
        return None
    
    # Deep copy the template structure
    template_structure = json.loads(json.dumps(source_dashboard.template_structure))
    
    # Create new dashboard
    new_dashboard = DashboardTemplate(
        code=new_code,
        name=new_name,
        description=f"Cloned from {source_dashboard.name}",
        category=source_dashboard.category,
        template_structure=template_structure,
        version=1,
        is_active=True,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_dashboard)
    db.commit()
    db.refresh(new_dashboard)
    return new_dashboard


# Template Structure Helper Functions

def extract_data_requirements(
    dashboard_template: DashboardTemplate
) -> DashboardTemplateDataRequirements:
    """Extract data requirements from a dashboard template"""
    template = dashboard_template.template_structure
    data_mappings = template.get("data_mappings", {})
    
    # Extract widget requirements from all dashboards in the template
    widget_requirements = []
    menu_items = template.get("menu", {}).get("items", [])
    
    def extract_from_menu(items):
        for item in items:
            if item.get("type") == "dashboard" and "dashboard" in item:
                dashboard = item["dashboard"]
                for widget in dashboard.get("widgets", []):
                    if "data_requirements" in widget:
                        widget_requirements.append({
                            "widget_code": widget.get("widget_code"),
                            "menu_item_id": item.get("id"),
                            "requirements": widget["data_requirements"]
                        })
            elif item.get("type") == "group" and "children" in item:
                extract_from_menu(item["children"])
    
    extract_from_menu(menu_items)
    
    return DashboardTemplateDataRequirements(
        template_id=dashboard_template.id,
        template_code=dashboard_template.code,
        required_datasets=data_mappings.get("required_datasets", []),
        field_mappings=data_mappings.get("field_mappings", {}),
        widget_requirements=widget_requirements
    )


def validate_template_structure(template_structure: Dict[str, Any]) -> List[str]:
    """Validate a dashboard template structure"""
    errors = []
    
    # Check required top-level keys
    if "menu" not in template_structure:
        errors.append("Missing 'menu' in template structure")
    elif "items" not in template_structure["menu"]:
        errors.append("Missing 'items' in menu structure")
    
    if "data_mappings" not in template_structure:
        errors.append("Missing 'data_mappings' in template structure")
    
    # Validate menu items recursively
    def validate_menu_items(items, path="menu.items"):
        for i, item in enumerate(items):
            item_path = f"{path}[{i}]"
            
            # Required fields
            if "id" not in item:
                errors.append(f"{item_path}: Missing 'id'")
            if "type" not in item:
                errors.append(f"{item_path}: Missing 'type'")
            if "label" not in item:
                errors.append(f"{item_path}: Missing 'label'")
            
            # Type-specific validation
            item_type = item.get("type")
            if item_type == "dashboard":
                if "dashboard" not in item:
                    errors.append(f"{item_path}: Dashboard type requires 'dashboard' object")
                else:
                    # Validate dashboard structure
                    dashboard = item["dashboard"]
                    if "layout" not in dashboard:
                        errors.append(f"{item_path}.dashboard: Missing 'layout'")
                    if "widgets" not in dashboard:
                        errors.append(f"{item_path}.dashboard: Missing 'widgets'")
            elif item_type == "group":
                if "children" in item:
                    validate_menu_items(item["children"], f"{item_path}.children")
    
    if "menu" in template_structure and "items" in template_structure["menu"]:
        validate_menu_items(template_structure["menu"]["items"])
    
    return errors


# Study Dashboard CRUD operations

def create_study_dashboard(
    db: Session,
    study_dashboard_create: StudyDashboardCreate,
    current_user: User
) -> StudyDashboard:
    """Assign a dashboard template to a study"""
    # Verify study exists and user has access
    study = db.get(Study, study_dashboard_create.study_id)
    if not study:
        raise ValueError("Study not found")
    
    # Check if this dashboard is already assigned to the study
    existing = db.exec(
        select(StudyDashboard).where(
            and_(
                StudyDashboard.study_id == study_dashboard_create.study_id,
                StudyDashboard.dashboard_template_id == study_dashboard_create.dashboard_template_id
            )
        )
    ).first()
    
    if existing:
        # Reactivate if it was deactivated
        existing.is_active = True
        existing.updated_at = datetime.utcnow()
        existing.customizations = study_dashboard_create.customizations
        existing.data_mappings = study_dashboard_create.data_mappings
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing
    
    # Create new assignment
    db_study_dashboard = StudyDashboard(
        **study_dashboard_create.model_dump(),
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_study_dashboard)
    db.commit()
    db.refresh(db_study_dashboard)
    return db_study_dashboard


def get_study_dashboards(
    db: Session,
    study_id: uuid.UUID,
    is_active: Optional[bool] = True
) -> List[StudyDashboard]:
    """Get all dashboards assigned to a study"""
    query = select(StudyDashboard).where(StudyDashboard.study_id == study_id)
    
    if is_active is not None:
        query = query.where(StudyDashboard.is_active == is_active)
    
    return list(db.exec(query).all())


def update_study_dashboard(
    db: Session,
    study_dashboard_id: uuid.UUID,
    customizations: Optional[Dict[str, Any]] = None,
    data_mappings: Optional[Dict[str, Any]] = None,
    is_active: Optional[bool] = None
) -> Optional[StudyDashboard]:
    """Update study-specific dashboard customizations"""
    db_study_dashboard = db.get(StudyDashboard, study_dashboard_id)
    if not db_study_dashboard:
        return None
    
    if customizations is not None:
        db_study_dashboard.customizations = customizations
    if data_mappings is not None:
        db_study_dashboard.data_mappings = data_mappings
    if is_active is not None:
        db_study_dashboard.is_active = is_active
    
    db_study_dashboard.updated_at = datetime.utcnow()
    
    db.add(db_study_dashboard)
    db.commit()
    db.refresh(db_study_dashboard)
    return db_study_dashboard


def remove_study_dashboard(
    db: Session,
    study_dashboard_id: uuid.UUID
) -> bool:
    """Remove dashboard assignment from study (soft delete)"""
    db_study_dashboard = db.get(StudyDashboard, study_dashboard_id)
    if not db_study_dashboard:
        return False
    
    db_study_dashboard.is_active = False
    db_study_dashboard.updated_at = datetime.utcnow()
    
    db.add(db_study_dashboard)
    db.commit()
    return True


def get_dashboard_count_by_category(db: Session) -> dict:
    """Get count of dashboards grouped by category"""
    from sqlalchemy import func
    
    results = db.exec(
        select(
            DashboardTemplate.category,
            func.count(DashboardTemplate.id).label("count")
        )
        .where(DashboardTemplate.is_active == True)
        .group_by(DashboardTemplate.category)
    ).all()
    
    return {str(category): count for category, count in results}