# ABOUTME: CRUD operations for WidgetDefinition model
# ABOUTME: Handles create, read, update, delete operations for widget library management

from typing import List, Optional
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy import and_
import uuid

from app.models import (
    WidgetDefinition, 
    WidgetDefinitionCreate, 
    WidgetDefinitionUpdate, 
    User,
    WidgetCategory
)


def create_widget(
    db: Session,
    widget_create: WidgetDefinitionCreate,
    current_user: User
) -> WidgetDefinition:
    """Create a new widget definition"""
    db_widget = WidgetDefinition(
        **widget_create.model_dump(),
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_widget)
    db.commit()
    db.refresh(db_widget)
    return db_widget


def get_widget(db: Session, widget_id: uuid.UUID) -> Optional[WidgetDefinition]:
    """Get widget definition by ID"""
    return db.get(WidgetDefinition, widget_id)


def get_widget_by_code(db: Session, code: str) -> Optional[WidgetDefinition]:
    """Get widget definition by unique code"""
    return db.exec(
        select(WidgetDefinition).where(WidgetDefinition.code == code)
    ).first()


def get_widgets(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category: Optional[WidgetCategory] = None,
    is_active: Optional[bool] = None
) -> List[WidgetDefinition]:
    """Get list of widget definitions with optional filters"""
    query = select(WidgetDefinition)
    
    conditions = []
    if category:
        conditions.append(WidgetDefinition.category == category)
    if is_active is not None:
        conditions.append(WidgetDefinition.is_active == is_active)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(WidgetDefinition.category, WidgetDefinition.name)
    query = query.offset(skip).limit(limit)
    
    return list(db.exec(query).all())


def update_widget(
    db: Session,
    widget_id: uuid.UUID,
    widget_update: WidgetDefinitionUpdate,
    current_user: User
) -> Optional[WidgetDefinition]:
    """Update widget definition"""
    db_widget = db.get(WidgetDefinition, widget_id)
    if not db_widget:
        return None
    
    update_data = widget_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    # Track if version should be incremented
    version_changing_fields = {"config_schema", "data_requirements", "size_constraints"}
    should_increment_version = any(
        field in update_data for field in version_changing_fields
    )
    
    if should_increment_version:
        update_data["version"] = db_widget.version + 1
    
    for field, value in update_data.items():
        setattr(db_widget, field, value)
    
    db.add(db_widget)
    db.commit()
    db.refresh(db_widget)
    return db_widget


def delete_widget(db: Session, widget_id: uuid.UUID) -> bool:
    """Soft delete widget by setting is_active to False"""
    db_widget = db.get(WidgetDefinition, widget_id)
    if not db_widget:
        return False
    
    # Check if widget is in use by any dashboards
    from app.models import DashboardWidget
    widget_usage = db.exec(
        select(DashboardWidget).where(
            DashboardWidget.widget_definition_id == widget_id
        ).limit(1)
    ).first()
    
    if widget_usage:
        # Don't delete if widget is in use
        return False
    
    db_widget.is_active = False
    db_widget.updated_at = datetime.utcnow()
    db.add(db_widget)
    db.commit()
    return True


def increment_widget_version(
    db: Session,
    widget_id: uuid.UUID,
    current_user: User
) -> Optional[WidgetDefinition]:
    """Manually increment widget version (used after significant changes)"""
    db_widget = db.get(WidgetDefinition, widget_id)
    if not db_widget:
        return None
    
    db_widget.version += 1
    db_widget.updated_at = datetime.utcnow()
    
    db.add(db_widget)
    db.commit()
    db.refresh(db_widget)
    return db_widget


def get_widget_count_by_category(db: Session) -> dict:
    """Get count of widgets grouped by category"""
    from sqlalchemy import func
    
    results = db.exec(
        select(
            WidgetDefinition.category,
            func.count(WidgetDefinition.id).label("count")
        )
        .where(WidgetDefinition.is_active == True)
        .group_by(WidgetDefinition.category)
    ).all()
    
    return {str(category): count for category, count in results}