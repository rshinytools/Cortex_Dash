# ABOUTME: API endpoints for study initialization wizard
# ABOUTME: Provides step-by-step initialization flow with validation

import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_user
from app.models import User, Study, UnifiedDashboardTemplate, Organization
from app.core.permissions import has_permission, Permission

logger = logging.getLogger(__name__)

router = APIRouter()


class WizardStep(BaseModel):
    """Base model for wizard steps"""
    step_id: str
    step_name: str
    is_completed: bool = False
    is_current: bool = False
    validation_errors: List[str] = Field(default_factory=list)


class StudyBasicInfoRequest(BaseModel):
    """Step 1: Basic study information"""
    name: str
    protocol_number: str
    description: Optional[str] = None
    phase: Optional[str] = None
    therapeutic_area: Optional[str] = None
    indication: Optional[str] = None


class TemplateSelectionRequest(BaseModel):
    """Step 2: Template selection"""
    template_id: uuid.UUID


class DataUploadInfo(BaseModel):
    """Step 3: Data upload information"""
    total_files: int
    uploaded_files: List[Dict[str, Any]]
    is_complete: bool


class MappingReviewRequest(BaseModel):
    """Step 4: Field mapping review"""
    accept_auto_mappings: bool
    custom_mappings: Optional[Dict[str, Any]] = None


class WizardStateResponse(BaseModel):
    """Current wizard state"""
    study_id: uuid.UUID
    current_step: int
    total_steps: int
    steps: List[WizardStep]
    can_proceed: bool
    can_go_back: bool
    is_complete: bool
    next_action: Optional[str] = None


class TemplateOption(BaseModel):
    """Template option for selection"""
    id: uuid.UUID
    name: str
    description: Optional[str]
    preview_url: Optional[str]
    widget_count: int
    dashboard_count: int
    is_recommended: bool = False


@router.post("/wizard/start", response_model=WizardStateResponse)
async def start_initialization_wizard(
    study_info: StudyBasicInfoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start the study initialization wizard
    
    Creates a new study and returns the wizard state
    """
    # Check permissions
    if not has_permission(current_user, Permission.CREATE_STUDY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create study"
        )
    
    # Check if protocol number already exists
    existing = db.exec(
        select(Study).where(Study.protocol_number == study_info.protocol_number)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Study with this protocol number already exists"
        )
    
    # Create study
    study = Study(
        name=study_info.name,
        protocol_number=study_info.protocol_number,
        description=study_info.description,
        phase=study_info.phase,
        therapeutic_area=study_info.therapeutic_area,
        indication=study_info.indication,
        org_id=current_user.org_id,
        created_by=current_user.id,
        status="SETUP",
        initialization_status="wizard_started",
        initialization_steps={
            "wizard_state": {
                "current_step": 1,
                "completed_steps": [],
                "started_at": datetime.utcnow().isoformat()
            }
        }
    )
    
    db.add(study)
    db.commit()
    db.refresh(study)
    
    # Return wizard state
    return WizardStateResponse(
        study_id=study.id,
        current_step=1,
        total_steps=4,
        steps=[
            WizardStep(
                step_id="basic_info",
                step_name="Basic Information",
                is_completed=True,
                is_current=False
            ),
            WizardStep(
                step_id="template_selection",
                step_name="Select Template",
                is_completed=False,
                is_current=True
            ),
            WizardStep(
                step_id="data_upload",
                step_name="Upload Data",
                is_completed=False,
                is_current=False
            ),
            WizardStep(
                step_id="review_mappings",
                step_name="Review & Activate",
                is_completed=False,
                is_current=False
            )
        ],
        can_proceed=True,
        can_go_back=False,
        is_complete=False,
        next_action="Select a dashboard template"
    )


@router.get("/wizard/{study_id}/state", response_model=WizardStateResponse)
async def get_wizard_state(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current wizard state for a study"""
    # Get study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get wizard state from initialization steps
    wizard_state = study.initialization_steps.get("wizard_state", {})
    current_step = wizard_state.get("current_step", 1)
    completed_steps = wizard_state.get("completed_steps", [])
    
    # Build steps
    steps = [
        WizardStep(
            step_id="basic_info",
            step_name="Basic Information",
            is_completed="basic_info" in completed_steps or current_step > 1,
            is_current=current_step == 1
        ),
        WizardStep(
            step_id="template_selection",
            step_name="Select Template",
            is_completed="template_selection" in completed_steps or current_step > 2,
            is_current=current_step == 2
        ),
        WizardStep(
            step_id="data_upload",
            step_name="Upload Data",
            is_completed="data_upload" in completed_steps or current_step > 3,
            is_current=current_step == 3
        ),
        WizardStep(
            step_id="review_mappings",
            step_name="Review & Activate",
            is_completed="review_mappings" in completed_steps,
            is_current=current_step == 4
        )
    ]
    
    # Determine next action
    next_action = None
    if current_step == 2:
        next_action = "Select a dashboard template"
    elif current_step == 3:
        next_action = "Upload study data files"
    elif current_step == 4:
        next_action = "Review field mappings and activate study"
    
    return WizardStateResponse(
        study_id=study.id,
        current_step=current_step,
        total_steps=4,
        steps=steps,
        can_proceed=current_step < 4,
        can_go_back=current_step > 1,
        is_complete=current_step == 4 and "review_mappings" in completed_steps,
        next_action=next_action
    )


@router.get("/wizard/{study_id}/templates", response_model=List[TemplateOption])
async def get_available_templates(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available templates for study initialization"""
    # Get study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get templates for organization
    templates = db.exec(
        select(UnifiedDashboardTemplate).where(
            UnifiedDashboardTemplate.org_id == study.org_id
        )
    ).all()
    
    # Build template options
    options = []
    for template in templates:
        # Count widgets and dashboards
        widget_count = template.widgetCount or 0
        dashboard_count = template.dashboardCount or 0
        
        # Determine if recommended based on study characteristics
        is_recommended = False
        if study.phase and "safety" in template.name.lower() and study.phase in ["I", "II"]:
            is_recommended = True
        elif study.phase and "efficacy" in template.name.lower() and study.phase in ["III", "IV"]:
            is_recommended = True
        
        options.append(TemplateOption(
            id=template.id,
            name=template.name,
            description=template.description,
            preview_url=f"/api/v1/dashboard-templates/{template.id}/preview",
            widget_count=widget_count,
            dashboard_count=dashboard_count,
            is_recommended=is_recommended
        ))
    
    # Sort with recommended first
    options.sort(key=lambda x: (not x.is_recommended, x.name))
    
    return options


@router.post("/wizard/{study_id}/select-template")
async def select_template(
    study_id: uuid.UUID,
    request: TemplateSelectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Select template and proceed to next step"""
    # Get study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Verify template exists
    template = db.get(UnifiedDashboardTemplate, request.template_id)
    if not template or template.org_id != study.org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Update study
    study.dashboard_template_id = request.template_id
    study.template_applied_at = datetime.utcnow()
    
    # Update wizard state
    wizard_state = study.initialization_steps.get("wizard_state", {})
    wizard_state["current_step"] = 3
    completed_steps = wizard_state.get("completed_steps", [])
    if "template_selection" not in completed_steps:
        completed_steps.append("template_selection")
    wizard_state["completed_steps"] = completed_steps
    wizard_state["selected_template_id"] = str(request.template_id)
    study.initialization_steps["wizard_state"] = wizard_state
    
    db.add(study)
    db.commit()
    
    return {
        "message": "Template selected successfully",
        "next_step": "data_upload",
        "template_name": template.name
    }


@router.get("/wizard/{study_id}/upload-status", response_model=DataUploadInfo)
async def get_upload_status(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get data upload status"""
    # Get study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get uploaded files from metadata
    uploaded_files = []
    if study.metadata and "pending_uploads" in study.metadata:
        uploaded_files = study.metadata["pending_uploads"]
    
    return DataUploadInfo(
        total_files=len(uploaded_files),
        uploaded_files=uploaded_files,
        is_complete=len(uploaded_files) > 0
    )


@router.post("/wizard/{study_id}/complete-upload")
async def complete_upload_step(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark upload step as complete and proceed"""
    # Get study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if files were uploaded
    uploaded_files = []
    if study.metadata and "pending_uploads" in study.metadata:
        uploaded_files = study.metadata["pending_uploads"]
    
    if not uploaded_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files uploaded. Please upload at least one data file."
        )
    
    # Update wizard state
    wizard_state = study.initialization_steps.get("wizard_state", {})
    wizard_state["current_step"] = 4
    completed_steps = wizard_state.get("completed_steps", [])
    if "data_upload" not in completed_steps:
        completed_steps.append("data_upload")
    wizard_state["completed_steps"] = completed_steps
    study.initialization_steps["wizard_state"] = wizard_state
    
    study.data_uploaded_at = datetime.utcnow()
    
    db.add(study)
    db.commit()
    
    return {
        "message": "Upload step completed",
        "next_step": "review_mappings",
        "uploaded_files_count": len(uploaded_files)
    }


@router.post("/wizard/{study_id}/complete")
async def complete_wizard(
    study_id: uuid.UUID,
    request: MappingReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete the wizard and activate the study"""
    # Get study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Verify all steps are completed
    wizard_state = study.initialization_steps.get("wizard_state", {})
    completed_steps = wizard_state.get("completed_steps", [])
    
    required_steps = ["template_selection", "data_upload"]
    missing_steps = [step for step in required_steps if step not in completed_steps]
    
    if missing_steps:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete wizard. Missing steps: {', '.join(missing_steps)}"
        )
    
    # Update wizard state
    if "review_mappings" not in completed_steps:
        completed_steps.append("review_mappings")
    wizard_state["completed_steps"] = completed_steps
    wizard_state["completed_at"] = datetime.utcnow().isoformat()
    wizard_state["current_step"] = 4
    study.initialization_steps["wizard_state"] = wizard_state
    
    # Store mapping preferences
    if request.custom_mappings:
        study.field_mappings = request.custom_mappings
    
    study.initialization_steps["auto_mappings_accepted"] = request.accept_auto_mappings
    study.initialization_status = "wizard_completed"
    
    db.add(study)
    db.commit()
    
    # Return initialization endpoint for actual processing
    return {
        "message": "Wizard completed successfully",
        "study_id": study_id,
        "next_action": "Initialize study",
        "initialization_endpoint": f"/api/v1/studies/{study_id}/initialize"
    }


@router.post("/wizard/{study_id}/cancel")
async def cancel_wizard(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel the wizard and optionally delete the study"""
    # Get study
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if study has been initialized
    if study.initialization_status not in ["wizard_started", "wizard_completed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel wizard for initialized study"
        )
    
    # Delete the study if no significant data
    if study.initialization_status == "wizard_started":
        db.delete(study)
        db.commit()
        return {"message": "Wizard cancelled and study deleted"}
    else:
        # Just mark as cancelled
        study.initialization_status = "wizard_cancelled"
        wizard_state = study.initialization_steps.get("wizard_state", {})
        wizard_state["cancelled_at"] = datetime.utcnow().isoformat()
        study.initialization_steps["wizard_state"] = wizard_state
        db.add(study)
        db.commit()
        return {"message": "Wizard cancelled"}