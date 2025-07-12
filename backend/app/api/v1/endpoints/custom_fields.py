# ABOUTME: API endpoints for managing custom field definitions and configurations
# ABOUTME: Handles dynamic field creation for studies, forms, and data collection

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlmodel import Session, select
from datetime import datetime
import uuid

from app.api.deps import get_db, get_current_user
from app.models import User, Study
from app.core.permissions import Permission, require_permission

router = APIRouter()


@router.get("/definitions", response_model=List[Dict[str, Any]])
async def get_custom_field_definitions(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    study_id: Optional[uuid.UUID] = Query(None, description="Filter by study"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get custom field definitions for the organization.
    """
    # TODO: Implement actual field definition retrieval
    definitions = [
        {
            "id": "field_001",
            "name": "Protocol Version",
            "field_name": "protocol_version",
            "entity_type": "study",
            "field_type": "text",
            "required": True,
            "default_value": None,
            "validation": {
                "pattern": "^v\\d+\\.\\d+$",
                "message": "Must be in format v1.0"
            },
            "display_order": 1,
            "active": True,
            "created_at": "2024-11-01T00:00:00"
        },
        {
            "id": "field_002",
            "name": "Therapeutic Area",
            "field_name": "therapeutic_area",
            "entity_type": "study",
            "field_type": "select",
            "required": True,
            "options": [
                {"value": "oncology", "label": "Oncology"},
                {"value": "cardiology", "label": "Cardiology"},
                {"value": "neurology", "label": "Neurology"},
                {"value": "immunology", "label": "Immunology"},
                {"value": "other", "label": "Other"}
            ],
            "default_value": None,
            "display_order": 2,
            "active": True,
            "created_at": "2024-11-01T00:00:00"
        },
        {
            "id": "field_003",
            "name": "Risk Category",
            "field_name": "risk_category",
            "entity_type": "subject",
            "field_type": "select",
            "required": False,
            "options": [
                {"value": "low", "label": "Low Risk"},
                {"value": "medium", "label": "Medium Risk"},
                {"value": "high", "label": "High Risk"}
            ],
            "default_value": "low",
            "display_order": 1,
            "active": True,
            "created_at": "2024-12-01T00:00:00"
        },
        {
            "id": "field_004",
            "name": "Concomitant Medications",
            "field_name": "concomitant_meds",
            "entity_type": "visit",
            "field_type": "multitext",
            "required": False,
            "max_items": 10,
            "display_order": 3,
            "active": True,
            "created_at": "2025-01-01T00:00:00"
        },
        {
            "id": "field_005",
            "name": "Site Contact Email",
            "field_name": "site_contact_email",
            "entity_type": "site",
            "field_type": "email",
            "required": True,
            "validation": {
                "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                "message": "Must be a valid email address"
            },
            "display_order": 4,
            "active": True,
            "created_at": "2024-11-15T00:00:00"
        },
        {
            "id": "field_006",
            "name": "Enrollment Target Date",
            "field_name": "enrollment_target_date",
            "entity_type": "study",
            "field_type": "date",
            "required": False,
            "validation": {
                "min_date": "2024-01-01",
                "max_date": "2030-12-31"
            },
            "display_order": 5,
            "active": True,
            "created_at": "2024-12-15T00:00:00"
        },
        {
            "id": "field_007",
            "name": "Adverse Event Severity",
            "field_name": "ae_severity",
            "entity_type": "adverse_event",
            "field_type": "number",
            "required": True,
            "validation": {
                "min": 1,
                "max": 5,
                "message": "Severity must be between 1 and 5"
            },
            "display_order": 2,
            "active": True,
            "created_at": "2025-01-10T00:00:00"
        }
    ]
    
    # Apply filters
    if entity_type:
        definitions = [d for d in definitions if d["entity_type"] == entity_type]
    
    if study_id:
        # TODO: Filter by study-specific fields
        pass
    
    return definitions


@router.post("/definitions", response_model=Dict[str, Any])
async def create_custom_field_definition(
    definition: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new custom field definition.
    """
    # Extract definition data
    name = definition.get("name")
    field_name = definition.get("field_name")
    entity_type = definition.get("entity_type")
    field_type = definition.get("field_type")
    
    if not all([name, field_name, entity_type, field_type]):
        raise HTTPException(
            status_code=400,
            detail="Name, field_name, entity_type, and field_type are required"
        )
    
    # Validate entity type
    valid_entity_types = ["study", "subject", "visit", "site", "adverse_event", "lab_result"]
    if entity_type not in valid_entity_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity type. Must be one of: {', '.join(valid_entity_types)}"
        )
    
    # Validate field type
    valid_field_types = ["text", "number", "date", "datetime", "boolean", "select", 
                        "multiselect", "multitext", "email", "url", "json"]
    if field_type not in valid_field_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid field type. Must be one of: {', '.join(valid_field_types)}"
        )
    
    # TODO: Implement actual field definition creation
    
    new_definition = {
        "id": f"field_{uuid.uuid4().hex[:8]}",
        "name": name,
        "field_name": field_name,
        "entity_type": entity_type,
        "field_type": field_type,
        "required": definition.get("required", False),
        "default_value": definition.get("default_value"),
        "options": definition.get("options", []) if field_type in ["select", "multiselect"] else None,
        "validation": definition.get("validation", {}),
        "display_order": definition.get("display_order", 999),
        "active": True,
        "org_id": str(current_user.org_id),
        "created_by": current_user.email,
        "created_at": datetime.utcnow().isoformat()
    }
    
    return new_definition


@router.put("/definitions/{field_id}", response_model=Dict[str, Any])
async def update_custom_field_definition(
    field_id: str,
    definition: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a custom field definition.
    """
    # TODO: Implement actual field definition update
    
    updated_definition = {
        "id": field_id,
        **definition,
        "updated_by": current_user.email,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    return updated_definition


@router.delete("/definitions/{field_id}")
async def delete_custom_field_definition(
    field_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a custom field definition.
    """
    # TODO: Check if field is in use before deletion
    # TODO: Implement actual field deletion
    
    return {
        "message": f"Custom field {field_id} has been deleted",
        "deleted_by": current_user.email,
        "deleted_at": datetime.utcnow().isoformat()
    }


@router.get("/values/{entity_type}/{entity_id}", response_model=Dict[str, Any])
async def get_custom_field_values(
    entity_type: str,
    entity_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get custom field values for a specific entity.
    """
    # TODO: Implement actual value retrieval
    
    # Mock values based on entity type
    values = {}
    
    if entity_type == "study":
        values = {
            "protocol_version": "v2.1",
            "therapeutic_area": "oncology",
            "enrollment_target_date": "2025-06-30"
        }
    elif entity_type == "subject":
        values = {
            "risk_category": "medium"
        }
    elif entity_type == "visit":
        values = {
            "concomitant_meds": ["Aspirin", "Metformin", "Lisinopril"]
        }
    elif entity_type == "site":
        values = {
            "site_contact_email": "contact@site001.com"
        }
    
    return {
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "values": values,
        "last_updated": datetime.utcnow().isoformat()
    }


@router.put("/values/{entity_type}/{entity_id}", response_model=Dict[str, Any])
async def update_custom_field_values(
    entity_type: str,
    entity_id: uuid.UUID,
    values: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update custom field values for a specific entity.
    """
    # TODO: Validate values against field definitions
    # TODO: Implement actual value update
    
    return {
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "values": values,
        "updated_by": current_user.email,
        "updated_at": datetime.utcnow().isoformat(),
        "message": "Custom field values updated successfully"
    }


@router.get("/forms/{study_id}", response_model=List[Dict[str, Any]])
async def get_custom_forms(
    study_id: uuid.UUID,
    form_type: Optional[str] = Query(None, description="Filter by form type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get custom forms for a study.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Implement actual form retrieval
    forms = [
        {
            "id": "form_001",
            "name": "Baseline Assessment",
            "form_type": "assessment",
            "description": "Initial patient assessment form",
            "fields": [
                {
                    "field_id": "field_003",
                    "order": 1,
                    "conditional": None
                },
                {
                    "field_id": "field_007",
                    "order": 2,
                    "conditional": {
                        "field": "risk_category",
                        "operator": "equals",
                        "value": "high"
                    }
                }
            ],
            "active": True,
            "created_at": "2025-01-01T00:00:00"
        },
        {
            "id": "form_002",
            "name": "Visit Checklist",
            "form_type": "visit",
            "description": "Standard visit checklist form",
            "fields": [
                {
                    "field_id": "field_004",
                    "order": 1,
                    "conditional": None
                }
            ],
            "active": True,
            "created_at": "2025-01-05T00:00:00"
        }
    ]
    
    if form_type:
        forms = [f for f in forms if f["form_type"] == form_type]
    
    return forms


@router.post("/forms/{study_id}", response_model=Dict[str, Any])
async def create_custom_form(
    study_id: uuid.UUID,
    form: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a custom form for a study.
    """
    # Verify study exists and user has access
    study = db.exec(select(Study).where(Study.id == study_id)).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not current_user.is_superuser and study.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Extract form data
    name = form.get("name")
    form_type = form.get("form_type")
    fields = form.get("fields", [])
    
    if not all([name, form_type]):
        raise HTTPException(
            status_code=400,
            detail="Name and form_type are required"
        )
    
    # TODO: Implement actual form creation
    
    new_form = {
        "id": f"form_{uuid.uuid4().hex[:8]}",
        "study_id": str(study_id),
        "name": name,
        "form_type": form_type,
        "description": form.get("description", ""),
        "fields": fields,
        "active": True,
        "created_by": current_user.email,
        "created_at": datetime.utcnow().isoformat()
    }
    
    return new_form