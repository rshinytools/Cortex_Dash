# ABOUTME: Template requirements endpoint for extracting widget data needs
# ABOUTME: Provides field requirements and auto-mapping suggestions for dashboard templates

from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.api import deps
from app.models import User, DashboardTemplate
from app.api.deps import get_db, get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard-templates/{template_id}/requirements")
def get_template_requirements(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Extract data requirements from a dashboard template.
    Returns the fields needed by each widget in the template.
    """
    
    # Get the template
    template = db.get(DashboardTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    requirements = []
    auto_mappings = {}
    
    # Parse template structure to extract widget requirements
    if template.template_structure:
        dashboards = template.template_structure.get("dashboardTemplates", [])
        
        for dashboard in dashboards:
            for widget_config in dashboard.get("widgets", []):
                # Handle the nested widget structure
                widget_instance = widget_config.get("widgetInstance", {})
                widget_def = widget_instance.get("widgetDefinition", {})
                
                widget_id = widget_instance.get("id", "")
                widget_code = widget_def.get("code", "")
                # Get the actual widget title from the overrides
                widget_overrides = widget_config.get("overrides", {})
                widget_name = widget_overrides.get("title") or widget_def.get("name", "Unknown Widget")
                widget_category = widget_def.get("category", "")
                
                # Extract required fields from data_contract
                required_fields = []
                optional_fields = []
                
                data_contract = widget_def.get("data_contract")
                if data_contract:
                    # Parse the data_contract JSON string if needed
                    if isinstance(data_contract, str):
                        import json
                        try:
                            data_contract = json.loads(data_contract)
                        except:
                            logger.warning(f"Failed to parse data_contract for widget {widget_id}")
                            data_contract = {}
                    
                    required_fields = data_contract.get("required_fields", [])
                    optional_fields = data_contract.get("optional_fields", [])
                
                # Also check data_requirements
                data_requirements = widget_def.get("data_requirements", {})
                if isinstance(data_requirements, str):
                    import json
                    try:
                        data_requirements = json.loads(data_requirements)
                    except:
                        data_requirements = {}
                
                # Combine all fields
                all_fields = list(set(required_fields + optional_fields))
                
                # Add to requirements if there are fields
                if all_fields:
                    requirements.append({
                        "widget_id": widget_id,
                        "widget_title": widget_name,
                        "widget_type": widget_code,
                        "widget_category": widget_category,
                        "required_fields": required_fields,
                        "optional_fields": optional_fields,
                        "data_contract": data_contract,
                        "data_requirements": data_requirements
                    })
                    
                    # Generate auto-mapping suggestions based on common patterns
                    auto_mappings[widget_id] = generate_auto_mappings(all_fields)
    
    return {
        "template_id": template_id,
        "template_name": template.name,
        "requirements": requirements,
        "auto_mappings": auto_mappings,
        "total_widgets": len(requirements)
    }


def generate_auto_mappings(required_fields: List[str]) -> Dict[str, Any]:
    """
    Generate auto-mapping suggestions based on common clinical data patterns.
    """
    mappings = {}
    
    # Common clinical data field mappings
    common_mappings = {
        # Subject/Patient identifiers
        "subject_id": ["USUBJID", "SUBJID", "PATIENT_ID", "SUBJECT"],
        "patient_id": ["USUBJID", "SUBJID", "PATIENT_ID", "SUBJECT"],
        
        # Site information
        "site_id": ["SITEID", "SITE", "CENTER", "SITE_ID"],
        "site_name": ["SITENAME", "SITE_NAME", "CENTER_NAME"],
        
        # Demographics
        "age": ["AGE", "AAGE", "BAGE"],
        "sex": ["SEX", "GENDER", "SEX_CD"],
        "race": ["RACE", "RACE_CD", "ETHNIC"],
        
        # Dates
        "date_field": ["VISITDT", "VISIT_DATE", "DATE", "DTC"],
        "visit_date": ["VISITDT", "VISIT_DATE", "SVSTDTC"],
        "enrollment_date": ["RFSTDTC", "ENROLL_DATE", "RANDDT"],
        
        # Adverse Events
        "ae_term": ["AETERM", "AEDECOD", "AE_TERM"],
        "ae_severity": ["AESEV", "AESER", "SEVERITY"],
        "sae_flag": ["AESER", "SAE_FLAG", "SERIOUS"],
        
        # Lab values
        "lab_test": ["LBTEST", "LBTESTCD", "TEST_NAME"],
        "lab_result": ["LBSTRESN", "LBORRES", "RESULT"],
        "lab_unit": ["LBSTRESU", "LBORRESU", "UNIT"],
        
        # Status fields
        "status_field": ["STATUS", "DSDECOD", "DSTERM"],
        "event_field": ["EVENT", "AETERM", "DSTERM"],
        
        # Metrics
        "value_field": ["VALUE", "RESULT", "AVAL", "STRESN"],
        "trend_field": ["CHANGE", "CHG", "PCHG", "TREND"]
    }
    
    for field in required_fields:
        field_lower = field.lower()
        
        # Look for exact or partial matches
        for pattern, candidates in common_mappings.items():
            if pattern in field_lower or field_lower in pattern:
                # Find the first matching candidate in actual data
                # For now, return the first candidate with confidence score
                mappings[field] = {
                    "dataset": "primary",  # Will be determined from actual data
                    "column": candidates[0],
                    "confidence": 85,  # Base confidence for pattern match
                    "candidates": candidates
                }
                break
        
        # If no pattern match, use the field name itself
        if field not in mappings:
            mappings[field] = {
                "dataset": "primary",
                "column": field.upper(),
                "confidence": 50,  # Lower confidence for direct mapping
                "candidates": [field.upper()]
            }
    
    return mappings


@router.post("/studies/{study_id}/field-mappings")
def save_field_mappings(
    study_id: UUID,
    mappings_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Save field mappings for a study.
    """
    from app.models import Study
    
    # Get the study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check permissions
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Save mappings to study
    if not study.initialization_steps:
        study.initialization_steps = {}
    
    study.initialization_steps["field_mappings"] = mappings_data.get("mappings", {})
    study.initialization_steps["accept_auto_mappings"] = mappings_data.get("accept_auto_mappings", True)
    
    # Update wizard state
    wizard_state = study.initialization_steps.get("wizard_state", {})
    wizard_state["current_step"] = 5  # Move to review step
    completed_steps = wizard_state.get("completed_steps", [])
    if "field_mapping" not in completed_steps:
        completed_steps.append("field_mapping")
    wizard_state["completed_steps"] = completed_steps
    study.initialization_steps["wizard_state"] = wizard_state
    
    db.add(study)
    db.commit()
    
    return {
        "message": "Field mappings saved successfully",
        "study_id": str(study_id),
        "mappings_count": len(mappings_data.get("mappings", {}))
    }