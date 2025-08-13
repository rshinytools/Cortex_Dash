# ABOUTME: Widget library management endpoints for system administrators
# ABOUTME: Handles widget creation, versioning, and configuration schema management

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlmodel import Session, select
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_user
from app.models import (
    User, 
    Message,
    WidgetDefinition,
    WidgetDefinitionCreate,
    WidgetDefinitionUpdate,
    WidgetDefinitionPublic,
    WidgetDefinitionsPublic,
    WidgetCategory
)
from app.core.permissions import Permission, has_permission
from app.crud import widget as crud_widget
from app.core.audit import create_activity_log, ActivityAction


router = APIRouter()


# Request/Response Models for API-specific functionality
class WidgetVersionRequest(BaseModel):
    config_schema: Optional[Dict[str, Any]] = None
    default_config: Optional[Dict[str, Any]] = None
    changelog: str = Field(..., description="Description of changes in this version")


class WidgetSchemaResponse(BaseModel):
    widget_id: UUID
    code: str
    version: int
    config_schema: Dict[str, Any]
    example_config: Optional[Dict[str, Any]]
    validation_rules: Optional[Dict[str, Any]]


class WidgetDataContractResponse(BaseModel):
    widget_id: UUID
    code: str
    data_contract: Optional[Dict[str, Any]]
    field_count: int
    mapping_suggestions: Optional[Dict[str, Any]]


def check_system_admin(current_user: User) -> None:
    """Check if user is a system admin"""
    if not current_user.is_superuser and not has_permission(current_user, Permission.MANAGE_SYSTEM):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only system administrators can access this endpoint"
        )


@router.get("", response_model=WidgetDefinitionsPublic)
async def list_widgets(
    category: Optional[WidgetCategory] = Query(None, description="Filter by widget category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name or description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    List all widgets in the widget library.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Get widgets from database
    widgets = crud_widget.get_widgets(
        db=db,
        skip=skip,
        limit=limit,
        category=category,
        is_active=is_active
    )
    
    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        widgets = [
            w for w in widgets 
            if search_lower in w.name.lower() or 
               (w.description and search_lower in w.description.lower())
        ]
    
    # Convert to public models
    widget_data = [WidgetDefinitionPublic.model_validate(w) for w in widgets]
    
    return WidgetDefinitionsPublic(data=widget_data, count=len(widget_data))


@router.post("", response_model=WidgetDefinitionPublic, status_code=status.HTTP_201_CREATED)
async def create_widget(
    widget_data: WidgetDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new widget in the widget library.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Check if widget code already exists
    existing_widget = crud_widget.get_widget_by_code(db, code=widget_data.code)
    if existing_widget:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Widget with code '{widget_data.code}' already exists"
        )
    
    # Validate schema structure
    if not isinstance(widget_data.config_schema, dict) or "type" not in widget_data.config_schema:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid config_schema: must be a valid JSON Schema object"
        )
    
    # Create widget in database
    db_widget = crud_widget.create_widget(
        db=db,
        widget_create=widget_data,
        current_user=current_user
    )
    
    # Log activity
    create_activity_log(
        db=db,
        user_id=current_user.id,
        action=ActivityAction.CREATE,
        resource_type="widget",
        resource_id=str(db_widget.id),
        details={"widget_code": db_widget.code, "widget_name": db_widget.name}
    )
    
    return WidgetDefinitionPublic.model_validate(db_widget)


@router.get("/{widget_id}", response_model=WidgetDefinitionPublic)
async def get_widget_details(
    widget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get detailed information about a specific widget.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Fetch widget from database
    db_widget = crud_widget.get_widget(db, widget_id=widget_id)
    if not db_widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    return WidgetDefinitionPublic.model_validate(db_widget)


@router.put("/{widget_id}", response_model=WidgetDefinitionPublic)
async def update_widget(
    widget_id: UUID,
    widget_update: WidgetDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update an existing widget definition.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Check if widget exists
    db_widget = crud_widget.get_widget(db, widget_id=widget_id)
    if not db_widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # Validate schema structure if provided
    if widget_update.config_schema is not None:
        if not isinstance(widget_update.config_schema, dict) or "type" not in widget_update.config_schema:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid config_schema: must be a valid JSON Schema object"
            )
    
    # Update widget
    updated_widget = crud_widget.update_widget(
        db=db,
        widget_id=widget_id,
        widget_update=widget_update,
        current_user=current_user
    )
    
    if not updated_widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # Log activity
    create_activity_log(
        db=db,
        user_id=current_user.id,
        action=ActivityAction.UPDATE,
        resource_type="widget",
        resource_id=str(widget_id),
        details={"widget_code": updated_widget.code, "version": updated_widget.version}
    )
    
    return WidgetDefinitionPublic.model_validate(updated_widget)


@router.delete("/{widget_id}", response_model=Message)
async def delete_widget(
    widget_id: UUID,
    force: bool = Query(False, description="Force delete even if widget is in use"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Delete a widget from the library.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Check if widget exists
    db_widget = crud_widget.get_widget(db, widget_id=widget_id)
    if not db_widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # TODO: Check if widget is in use by any dashboards once DashboardWidget model is implemented
    # For now, allow deletion
    widget_usage = None
    
    # Perform soft delete
    success = crud_widget.delete_widget(db, widget_id=widget_id)
    if not success and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete widget. It may be in use."
        )
    
    # If force delete and soft delete failed, hard delete
    if force:
        # TODO: Remove all widget instances from dashboards once DashboardWidget model is implemented
        db.exec(
            select(DashboardWidget).where(
                DashboardWidget.widget_definition_id == widget_id
            )
        ).delete()
        # Then soft delete the widget
        db_widget.is_active = False
        db_widget.updated_at = datetime.utcnow()
        db.add(db_widget)
        db.commit()
    
    # Log activity
    create_activity_log(
        db=db,
        user_id=current_user.id,
        action=ActivityAction.DELETE,
        resource_type="widget",
        resource_id=str(widget_id),
        details={"widget_code": db_widget.code, "force": force}
    )
    
    return Message(message=f"Widget {db_widget.code} deleted successfully")


@router.post("/{widget_id}/version", response_model=WidgetDefinitionPublic, status_code=status.HTTP_201_CREATED)
async def create_widget_version(
    widget_id: UUID,
    version_data: WidgetVersionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new version of an existing widget.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Fetch current widget
    db_widget = crud_widget.get_widget(db, widget_id=widget_id)
    if not db_widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # Create update data with new version info
    update_data = WidgetDefinitionUpdate()
    if version_data.config_schema:
        update_data.config_schema = version_data.config_schema
    if version_data.default_config:
        update_data.default_config = version_data.default_config
    
    # Update widget (this will increment version automatically)
    updated_widget = crud_widget.update_widget(
        db=db,
        widget_id=widget_id,
        widget_update=update_data,
        current_user=current_user
    )
    
    # Log activity with changelog
    create_activity_log(
        db=db,
        user_id=current_user.id,
        action=ActivityAction.UPDATE,
        resource_type="widget_version",
        resource_id=str(widget_id),
        details={
            "widget_code": updated_widget.code,
            "new_version": updated_widget.version,
            "changelog": version_data.changelog
        }
    )
    
    return WidgetDefinitionPublic.model_validate(updated_widget)


@router.get("/{widget_id}/schema", response_model=WidgetSchemaResponse)
async def get_widget_schema(
    widget_id: UUID,
    version: Optional[int] = Query(None, description="Specific version, defaults to latest"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get the configuration schema for a specific widget.
    
    Only accessible by system administrators.
    """
    check_system_admin(current_user)
    
    # Fetch widget from database
    db_widget = crud_widget.get_widget(db, widget_id=widget_id)
    if not db_widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # For now, we don't have version history, so ignore version parameter
    # In a real implementation, you would store version history
    
    # Build example config based on the schema
    example_config = db_widget.default_config or {}
    
    # Add example values for required fields not in default config
    if "properties" in db_widget.config_schema:
        for prop, schema in db_widget.config_schema["properties"].items():
            if prop not in example_config:
                if schema.get("type") == "string":
                    example_config[prop] = f"Example {prop}"
                elif schema.get("type") == "number":
                    example_config[prop] = 0
                elif schema.get("type") == "boolean":
                    example_config[prop] = False
                elif schema.get("type") == "array":
                    example_config[prop] = []
    
    # Define standard validation rules
    validation_rules = {
        "required_fields_must_be_provided": True,
        "field_types_must_match_schema": True,
        "enum_values_must_be_valid": True
    }
    
    # Add widget-specific validation rules
    if db_widget.category == WidgetCategory.CHARTS.value:
        validation_rules["axis_fields_must_exist"] = True
    elif db_widget.category == WidgetCategory.TABLES.value:
        validation_rules["columns_must_be_array"] = True
    
    schema_response = WidgetSchemaResponse(
        widget_id=db_widget.id,
        code=db_widget.code,
        version=db_widget.version,
        config_schema=db_widget.config_schema,
        example_config=example_config,
        validation_rules=validation_rules
    )
    
    return schema_response


@router.get("/{widget_id}/data-contract", response_model=WidgetDataContractResponse)
async def get_widget_data_contract(
    widget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get the data contract for a specific widget.
    
    The data contract defines what fields the widget expects from data sources,
    including required and optional fields, types, and mapping suggestions.
    """
    check_system_admin(current_user)
    
    # Fetch widget from database
    db_widget = crud_widget.get_widget(db, widget_id=widget_id)
    if not db_widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found"
        )
    
    # Count fields if data contract exists
    field_count = 0
    mapping_suggestions = None
    
    if db_widget.data_contract:
        # Count required and optional fields
        required_fields = db_widget.data_contract.get("required_fields", [])
        optional_fields = db_widget.data_contract.get("optional_fields", [])
        field_count = len(required_fields) + len(optional_fields)
        
        # Extract mapping suggestions if present
        mapping_suggestions = db_widget.data_contract.get("mapping_suggestions", {})
    
    return WidgetDataContractResponse(
        widget_id=db_widget.id,
        code=db_widget.code,
        data_contract=db_widget.data_contract,
        field_count=field_count,
        mapping_suggestions=mapping_suggestions
    )