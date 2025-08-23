# ABOUTME: API endpoints for study initialization wizard
# ABOUTME: Provides step-by-step initialization flow with validation

import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlmodel import Session, select
from sqlalchemy.orm.attributes import flag_modified
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_user
from app.models import User, Study, StudyStatus, DashboardTemplate, Organization, StudyDataConfiguration, StudyPhase, PipelineConfig, PipelineExecution, PipelineStatus
from app.core.permissions import has_permission, Permission
from app.services.file_processing_service import FileProcessingService
from app.services.file_conversion_service import FileConversionService
from celery.result import AsyncResult
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter()


class DraftStudyResponse(BaseModel):
    """Response for draft study check"""
    has_draft: bool
    study_id: Optional[uuid.UUID] = None
    study_name: Optional[str] = None
    current_step: Optional[int] = None
    created_at: Optional[datetime] = None


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
    org_id: Optional[uuid.UUID] = None


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


class WizardStateUpdateRequest(BaseModel):
    """Update wizard state"""
    current_step: Optional[int] = None
    completed_steps: Optional[List[str]] = None
    data: Optional[Dict[str, Any]] = None


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
    menu_item_count: Optional[int] = 0
    dashboard_page_count: Optional[int] = 0
    is_recommended: bool = False


@router.get("/wizard/check-draft", response_model=DraftStudyResponse)
async def check_draft_study(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if user has a draft study in progress"""
    # Find any draft studies for this user's organization
    draft_study = db.exec(
        select(Study).where(
            Study.org_id == current_user.org_id,
            Study.status == StudyStatus.DRAFT,
            Study.created_by == current_user.id
        ).order_by(Study.created_at.desc())
    ).first()
    
    if draft_study:
        wizard_state = draft_study.initialization_steps.get("wizard_state", {})
        return DraftStudyResponse(
            has_draft=True,
            study_id=draft_study.id,
            study_name=draft_study.name,
            current_step=wizard_state.get("current_step", 1),
            created_at=draft_study.created_at
        )
    
    return DraftStudyResponse(has_draft=False)


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
    logger.info(f"Starting wizard with data: {study_info.dict()}")
    logger.info(f"Current user: {current_user.email}, org_id: {current_user.org_id}")
    # Check permissions
    if not has_permission(current_user, Permission.CREATE_STUDY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create study"
        )
    
    # Check if user has organization
    if not current_user.org_id:
        logger.error(f"User {current_user.email} has no organization assigned. Run 'docker compose exec backend python scripts/create_default_org.py' to create one.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to create studies. Please contact your administrator to assign you to an organization."
        )
    
    # Check if protocol number already exists
    existing = db.exec(
        select(Study).where(Study.protocol_number == study_info.protocol_number)
    ).first()
    
    if existing:
        # Provide more helpful error message with the existing study info
        error_msg = f"Protocol number '{study_info.protocol_number}' is already in use by study '{existing.name}'"
        if existing.status == StudyStatus.ARCHIVED:
            error_msg += " (archived). Please use a different protocol number."
        else:
            error_msg += f" ({existing.status.value.lower()}). Please use a different protocol number."
        
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_msg
        )
    
    # Generate study code from name if not provided
    study_code = study_info.name.upper().replace(' ', '_')[:20]
    
    # Convert phase string to enum if provided
    phase_enum = None
    if study_info.phase:
        try:
            phase_enum = StudyPhase(study_info.phase)
        except ValueError:
            logger.warning(f"Invalid phase value: {study_info.phase}")
            phase_enum = None
    
    # Determine which org_id to use
    # System admins can specify org_id, others must use their own
    if current_user.is_superuser and study_info.org_id:
        # Verify the org exists
        org = db.get(Organization, study_info.org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified organization not found"
            )
        target_org_id = study_info.org_id
    else:
        target_org_id = current_user.org_id
    
    # Create study
    study = Study(
        name=study_info.name,
        code=study_code,
        protocol_number=study_info.protocol_number,
        description=study_info.description,
        phase=phase_enum,
        therapeutic_area=study_info.therapeutic_area,
        indication=study_info.indication,
        org_id=target_org_id,
        created_by=current_user.id,
        status=StudyStatus.DRAFT,
        initialization_status="wizard_in_progress",
        initialization_steps={
            "wizard_state": {
                "current_step": 2,
                "completed_steps": ["basic_info"],
                "started_at": datetime.utcnow().isoformat()
            }
        }
    )
    
    try:
        db.add(study)
        db.commit()
        db.refresh(study)
    except Exception as e:
        logger.error(f"Error creating study: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create study: {str(e)}"
        )
    
    # Return wizard state
    return WizardStateResponse(
        study_id=study.id,
        current_step=2,
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
        can_go_back=True,
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


@router.patch("/wizard/{study_id}/state")
async def update_wizard_state(
    study_id: uuid.UUID,
    request: WizardStateUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update wizard state for a study"""
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
    
    # Update wizard state
    if not study.initialization_steps:
        study.initialization_steps = {}
    
    if "wizard_state" not in study.initialization_steps:
        study.initialization_steps["wizard_state"] = {}
    
    wizard_state = study.initialization_steps["wizard_state"]
    
    # Update current step if provided
    if request.current_step is not None:
        wizard_state["current_step"] = request.current_step
    
    # Update completed steps if provided
    if request.completed_steps is not None:
        wizard_state["completed_steps"] = request.completed_steps
    
    # Store any additional data
    if request.data:
        wizard_state["data"] = request.data
    
    # Mark the field as modified for SQLAlchemy to detect the change
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(study, "initialization_steps")
    
    study.initialization_steps["wizard_state"] = wizard_state
    
    db.add(study)
    db.commit()
    db.refresh(study)
    
    return {"message": "Wizard state updated successfully"}


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
    
    # Get all active templates (all created templates are published by default)
    templates = db.exec(
        select(DashboardTemplate).where(
            DashboardTemplate.is_active == True
        )
    ).all()
    
    # Build template options
    options = []
    for template in templates:
        # Count widgets and dashboards from template structure
        widget_count = 0
        dashboard_count = 0
        menu_page_count = 0
        menu_item_count = 0
        
        if template.template_structure:
            # Always count menu items from menu_structure
            menu_data = template.template_structure.get("menu_structure") or template.template_structure.get("menu", {})
            menu_items = menu_data.get("items", [])
            menu_item_count = len(menu_items)  # Count top-level menu items
            
            # Method 1: Count widgets from dashboardTemplates array (if exists)
            dashboard_templates = template.template_structure.get("dashboardTemplates", [])
            if dashboard_templates:
                for dt in dashboard_templates:
                    widgets = dt.get("widgets", [])
                    widget_count += len(widgets)
                dashboard_count = 1  # Consider as 1 unified dashboard
                menu_page_count = len(dashboard_templates)
            
            # Method 2: Count from menu_structure (if dashboardTemplates not found)
            if widget_count == 0:
                
                # Recursive function to count widgets in menu items
                def count_widgets_in_menu(items):
                    local_widget_count = 0
                    local_page_count = 0
                    
                    for item in items:
                        if item.get("type") == "dashboard_page":
                            local_page_count += 1
                            dashboard_data = item.get("dashboard") or item.get("dashboardConfig", {})
                            if dashboard_data:
                                widgets = dashboard_data.get("widgets", [])
                                local_widget_count += len(widgets)
                        
                        # Check children/submenus
                        if "children" in item:
                            child_widgets, child_pages = count_widgets_in_menu(item["children"])
                            local_widget_count += child_widgets
                            local_page_count += child_pages
                        if "submenus" in item:
                            sub_widgets, sub_pages = count_widgets_in_menu(item["submenus"])
                            local_widget_count += sub_widgets
                            local_page_count += sub_pages
                    
                    return local_widget_count, local_page_count
                
                widget_count, menu_page_count = count_widgets_in_menu(menu_items)
                dashboard_count = 1 if menu_page_count > 0 else 0
        
        # Determine if recommended based on study characteristics
        is_recommended = False
        if study.phase and "safety" in template.name.lower() and study.phase in ["phase_1", "phase_2"]:
            is_recommended = True
        elif study.phase and "efficacy" in template.name.lower() and study.phase in ["phase_3", "phase_4"]:
            is_recommended = True
        
        options.append(TemplateOption(
            id=template.id,
            name=template.name,
            description=template.description or f"{menu_item_count} menu items, {menu_page_count} dashboard pages, {widget_count} widgets",
            preview_url=f"/api/v1/dashboard-templates/{template.id}/preview",
            widget_count=widget_count,
            dashboard_count=dashboard_count,
            menu_item_count=menu_item_count,
            dashboard_page_count=menu_page_count,
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
    
    # Verify template exists and is active
    template = db.get(DashboardTemplate, request.template_id)
    if not template or not template.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or inactive"
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
    
    # Get uploaded files from initialization steps
    uploaded_files = []
    if study.initialization_steps and "pending_uploads" in study.initialization_steps:
        uploaded_files = study.initialization_steps["pending_uploads"]
    
    return DataUploadInfo(
        total_files=len(uploaded_files),
        uploaded_files=uploaded_files,
        is_complete=len(uploaded_files) > 0
    )


@router.post("/wizard/{study_id}/upload")
async def upload_wizard_files(
    study_id: uuid.UUID,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload files for the study initialization wizard"""
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
    
    # Create upload directory with correct path structure
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    upload_dir = Path(f"/data/{study.org_id}/studies/{study_id}/source_data/{timestamp}")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    uploaded_files = []
    
    for file in files:
        try:
            # Save file
            file_path = upload_dir / file.filename
            content = await file.read()
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Add to uploaded files list
            uploaded_files.append({
                "name": file.filename,
                "path": str(file_path),
                "size": len(content),
                "type": file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown',
                "uploaded_at": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to save file {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file {file.filename}: {str(e)}"
            )
    
    # Store uploaded files in initialization_steps
    if not study.initialization_steps:
        study.initialization_steps = {}
    
    # Add pending uploads
    study.initialization_steps["pending_uploads"] = uploaded_files
    
    # Update wizard state
    wizard_state = study.initialization_steps.get("wizard_state", {})
    if "data" not in wizard_state:
        wizard_state["data"] = {}
    wizard_state["data"]["uploaded_files"] = uploaded_files
    study.initialization_steps["wizard_state"] = wizard_state
    
    # Mark the JSON field as modified to ensure SQLAlchemy detects the change
    flag_modified(study, "initialization_steps")
    
    logger.info(f"Saving uploaded files to study {study_id}: {len(uploaded_files)} files")
    logger.info(f"initialization_steps after update: {study.initialization_steps.keys()}")
    
    db.add(study)
    db.commit()
    db.refresh(study)
    
    # Verify the save
    logger.info(f"After commit - pending_uploads exists: {'pending_uploads' in study.initialization_steps}")
    
    return {
        "message": "Files uploaded successfully",
        "total_files": len(uploaded_files),
        "files": uploaded_files
    }


@router.post("/wizard/{study_id}/complete-upload")
async def complete_upload_step(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark upload step as complete and proceed"""
    # Get study with fresh data
    study = db.get(Study, study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Refresh to ensure we have latest data
    db.refresh(study)
    
    # Check access
    if study.org_id != current_user.org_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if files were uploaded
    logger.info(f"Study initialization_steps: {study.initialization_steps}")
    
    uploaded_files = []
    if study.initialization_steps and "pending_uploads" in study.initialization_steps:
        uploaded_files = study.initialization_steps["pending_uploads"]
    
    logger.info(f"Found {len(uploaded_files)} uploaded files")
    
    if not uploaded_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files uploaded. Please upload at least one data file."
        )
    
    # IMPORTANT: Copy uploaded files to study config for initialization service
    if not study.config:
        study.config = {}
    study.config["uploaded_files"] = uploaded_files
    flag_modified(study, "config")
    
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
    
    # Trigger file conversion and processing
    logger.info("Starting file conversion process...")
    
    # Use FileConversionService for full pipeline
    file_converter = FileConversionService()
    
    # Define progress callback
    async def progress_callback(percent: int, message: str):
        logger.info(f"File processing progress: {percent}% - {message}")
        # Could store progress in database or send via websocket
        study.initialization_progress = percent
        db.add(study)
        db.commit()
    
    # Convert files with proper folder structure
    conversion_results = await file_converter.convert_study_files(
        org_id=study.org_id,
        study_id=study_id,
        files=uploaded_files,
        progress_callback=progress_callback
    )
    
    # Check for errors
    if conversion_results.get("summary", {}).get("has_errors", False):
        logger.error(f"File conversion had errors: {conversion_results.get('errors', [])}")
    
    # Save schema to database
    study_data_config = db.exec(
        select(StudyDataConfiguration).where(
            StudyDataConfiguration.study_id == study_id
        )
    ).first()
    
    if not study_data_config:
        logger.info(f"Creating new StudyDataConfiguration for study {study_id}")
        study_data_config = StudyDataConfiguration(
            study_id=study_id,
            dataset_schemas=conversion_results["datasets"],
            created_by=current_user.id
        )
        db.add(study_data_config)
    else:
        logger.info(f"Updating existing StudyDataConfiguration for study {study_id}")
        study_data_config.dataset_schemas = conversion_results["datasets"]
        study_data_config.updated_at = datetime.utcnow()
        study_data_config.updated_by = current_user.id
        db.add(study_data_config)
    
    # Store processing results
    study.initialization_steps["file_processing"] = conversion_results
    study.initialization_steps["data_folder"] = conversion_results.get("summary", {}).get("data_folder", "")
    
    # Force update flag for JSON fields
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(study, "initialization_steps")
    
    db.add(study)
    db.commit()
    
    # Verify the save was successful
    db.refresh(study_data_config)
    logger.info(f"StudyDataConfiguration saved with {len(study_data_config.dataset_schemas)} datasets")
    
    # Generate mapping suggestions if we have datasets
    if conversion_results["datasets"] and study.dashboard_template_id:
        template = db.get(DashboardTemplate, study.dashboard_template_id)
        if template and template.template_structure:
            # Extract widget data requirements from nested structure
            template_requirements = []
            dashboards = template.template_structure.get("dashboardTemplates", [])
            for dashboard in dashboards:
                for widget in dashboard.get("widgets", []):
                    # Get widget instance and definition
                    widget_instance = widget.get("widgetInstance", {})
                    widget_def = widget_instance.get("widgetDefinition", {})
                    
                    # Parse data_contract from JSON string
                    data_contract_str = widget_def.get("data_contract", "{}")
                    try:
                        import json as json_lib
                        data_contract = json_lib.loads(data_contract_str)
                    except:
                        data_contract = {}
                    
                    # Check if widget has data requirements
                    if data_contract and (data_contract.get("required_fields") or data_contract.get("optional_fields")):
                        # Get the actual widget title from the overrides
                        widget_overrides = widget.get("overrides", {})
                        widget_title = widget_overrides.get("title") or widget_def.get("name", "Unknown Widget")
                        
                        template_requirements.append({
                            "widget_id": widget.get("widgetInstanceId", widget_instance.get("id", "")),
                            "widget_title": widget_title,
                            "widget_type": widget_def.get("code", "unknown"),
                            "data_config": data_contract,
                            "required_fields": data_contract.get("required_fields", []),
                            "optional_fields": data_contract.get("optional_fields", [])
                        })
            
            # Generate mapping suggestions
            file_processor = FileProcessingService()
            mapping_suggestions = file_processor.generate_mapping_suggestions(
                template_requirements,
                conversion_results["datasets"]
            )
            study.initialization_steps["mapping_suggestions"] = mapping_suggestions
    
    return {
        "message": "Upload step completed",
        "next_step": "review_mappings",
        "uploaded_files_count": len(uploaded_files),
        "datasets_found": len(conversion_results["datasets"]),
        "converted_files_count": len(conversion_results.get("converted_files", [])),
        "data_folder": conversion_results.get("summary", {}).get("data_folder", ""),
        "processing_errors": conversion_results.get("errors", []),
        "processing_warnings": conversion_results.get("warnings", [])
    }


@router.get("/wizard/{study_id}/mapping-data")
async def get_mapping_data(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get schema and mapping suggestions for the review step"""
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
    
    # Get study data configuration
    study_data_config = db.exec(
        select(StudyDataConfiguration).where(
            StudyDataConfiguration.study_id == study_id
        )
    ).first()
    
    if not study_data_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No processed data found. Please complete the upload step first."
        )
    
    # Get template requirements
    template_requirements = []
    if study.dashboard_template_id:
        template = db.get(DashboardTemplate, study.dashboard_template_id)
        if template and template.template_structure:
            # Extract widget data requirements from nested structure
            dashboards = template.template_structure.get("dashboardTemplates", [])
            for dashboard in dashboards:
                for widget in dashboard.get("widgets", []):
                    # Get widget instance and definition
                    widget_instance = widget.get("widgetInstance", {})
                    widget_def = widget_instance.get("widgetDefinition", {})
                    
                    # Parse data_contract from JSON string
                    data_contract_str = widget_def.get("data_contract", "{}")
                    try:
                        import json
                        data_contract = json.loads(data_contract_str)
                    except:
                        data_contract = {}
                    
                    # Check if widget has data requirements
                    if data_contract and (data_contract.get("required_fields") or data_contract.get("optional_fields")):
                        # Get the actual widget title from the overrides
                        widget_overrides = widget.get("overrides", {})
                        widget_title = widget_overrides.get("title") or widget_def.get("name", "Unknown Widget")
                        
                        template_requirements.append({
                            "widget_id": widget.get("widgetInstanceId", widget_instance.get("id", "")),
                            "widget_title": widget_title,
                            "widget_type": widget_def.get("code", "unknown"),
                            "data_config": data_contract,
                            "required_fields": data_contract.get("required_fields", []),
                            "optional_fields": data_contract.get("optional_fields", [])
                        })
    
    # Generate mapping suggestions
    file_processor = FileProcessingService()
    mapping_suggestions = file_processor.generate_mapping_suggestions(
        template_requirements,
        study_data_config.dataset_schemas
    )
    
    return {
        "dataset_schemas": study_data_config.dataset_schemas,
        "template_requirements": template_requirements,
        "mapping_suggestions": mapping_suggestions,
        "total_datasets": len(study_data_config.dataset_schemas),
        "total_columns": sum(
            len(ds.get("columns", {})) 
            for ds in study_data_config.dataset_schemas.values()
        ),
        "total_widgets": len(template_requirements)
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
    # Note: field_mappings expects Dict[str, str] so we need to flatten the nested structure
    if request.custom_mappings:
        flattened_mappings = {}
        for widget_id, widget_mappings in request.custom_mappings.items():
            if isinstance(widget_mappings, dict):
                for field_name, mapping in widget_mappings.items():
                    # Create a unique key for each mapping
                    key = f"{widget_id}_{field_name}"
                    # Store as string reference to the dataset.column
                    if isinstance(mapping, dict) and 'dataset' in mapping and 'column' in mapping:
                        value = f"{mapping['dataset']}.{mapping['column']}"
                        flattened_mappings[key] = value
        study.field_mappings = flattened_mappings
    
    study.initialization_steps["auto_mappings_accepted"] = request.accept_auto_mappings
    
    # For re-initialization of existing studies, maintain completed status
    if study.initialization_status == "completed" and study.activated_at is not None:
        # This is a re-initialization, keep status as completed
        study.initialization_status = "completed"
    else:
        # First time initialization
        study.initialization_status = "wizard_completed"
    
    study.mappings_configured_at = datetime.utcnow()
    
    # Change status from DRAFT to SETUP when wizard is completed (only for new studies)
    if study.status == StudyStatus.DRAFT:
        study.status = StudyStatus.SETUP
    
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
    
    # Check if study has been initialized (skip check for drafts that may be re-deleted)
    if study.status not in ["draft", "DRAFT"] and study.initialization_status not in ["wizard_in_progress", "wizard_completed", "wizard_cancelled", None]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel wizard for initialized study"
        )
    
    # Delete the study if it's still a draft
    if study.status == StudyStatus.DRAFT:
        try:
            # Try to delete the study
            db.delete(study)
            db.commit()
            return {"message": "Draft study deleted"}
        except Exception as e:
            logger.error(f"Error deleting draft study: {str(e)}")
            db.rollback()
            
            # Alternative: just mark as archived instead of deleting
            study.initialization_status = "wizard_cancelled"
            study.status = StudyStatus.ARCHIVED
            db.add(study)
            db.commit()
            return {"message": "Draft study cancelled (could not delete due to dependencies)"}
    else:
        # Just mark as cancelled for non-draft studies
        study.initialization_status = "wizard_cancelled"
        wizard_state = study.initialization_steps.get("wizard_state", {})
        wizard_state["cancelled_at"] = datetime.utcnow().isoformat()
        study.initialization_steps["wizard_state"] = wizard_state
        db.add(study)
        db.commit()
        return {"message": "Wizard cancelled"}


@router.get("/wizard/{study_id}/transformation-ready")
async def check_transformation_ready(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if study is ready for transformation step"""
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
    
    # Check prerequisites
    wizard_state = study.initialization_steps.get("wizard_state", {})
    completed_steps = wizard_state.get("completed_steps", [])
    
    is_ready = (
        "template_selection" in completed_steps and
        "data_upload" in completed_steps and
        study.dashboard_template_id is not None
    )
    
    # Get dataset info
    study_data_config = db.exec(
        select(StudyDataConfiguration).where(
            StudyDataConfiguration.study_id == study_id
        )
    ).first()
    
    datasets = []
    if study_data_config and study_data_config.dataset_schemas:
        for name, schema in study_data_config.dataset_schemas.items():
            datasets.append({
                "name": name,
                "columns": list(schema.get("columns", {}).keys()),
                "row_count": schema.get("row_count", 0)
            })
    
    # Check for existing pipelines
    existing_pipelines = db.exec(
        select(PipelineConfig).where(
            PipelineConfig.study_id == study_id,
            PipelineConfig.is_current_version == True
        )
    ).all()
    
    return {
        "is_ready": is_ready,
        "has_template": study.dashboard_template_id is not None,
        "has_data": len(datasets) > 0,
        "available_datasets": datasets,
        "existing_pipelines_count": len(existing_pipelines),
        "wizard_step": wizard_state.get("current_step", 0),
        "missing_requirements": [] if is_ready else [
            step for step in ["template_selection", "data_upload"] 
            if step not in completed_steps
        ]
    }


@router.get("/wizard/{study_id}/suggested-transformations")
async def get_suggested_transformations(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get suggested transformations based on template requirements"""
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
    
    suggestions = []
    
    # Get template and analyze widget requirements
    if study.dashboard_template_id:
        template = db.get(DashboardTemplate, study.dashboard_template_id)
        if template and template.template_structure:
            # Extract unique data requirements from widgets
            widget_requirements = set()
            dashboards = template.template_structure.get("dashboardTemplates", [])
            
            for dashboard in dashboards:
                for widget in dashboard.get("widgets", []):
                    widget_type = widget.get("type", "")
                    data_config = widget.get("dataConfiguration", {})
                    
                    # Analyze widget type for transformation needs
                    if widget_type == "trend" and data_config.get("aggregation"):
                        widget_requirements.add("time_series_aggregation")
                    elif widget_type == "metric" and data_config.get("calculation"):
                        widget_requirements.add("metric_calculation")
                    elif widget_type in ["bar", "pie"] and data_config.get("groupBy"):
                        widget_requirements.add("group_aggregation")
                    elif widget_type == "table" and data_config.get("filters"):
                        widget_requirements.add("filtered_subset")
            
            # Get available datasets
            study_data_config = db.exec(
                select(StudyDataConfiguration).where(
                    StudyDataConfiguration.study_id == study_id
                )
            ).first()
            
            if study_data_config and study_data_config.dataset_schemas:
                # Generate suggestions based on requirements
                for req in widget_requirements:
                    if req == "time_series_aggregation":
                        # Find datasets with date columns
                        for ds_name, schema in study_data_config.dataset_schemas.items():
                            date_columns = [
                                col for col, dtype in schema.get("columns", {}).items()
                                if "date" in dtype.lower() or "dat" in col.lower()
                            ]
                            if date_columns:
                                suggestions.append({
                                    "type": "aggregation",
                                    "name": f"Daily aggregation of {ds_name}",
                                    "description": f"Aggregate {ds_name} data by day for trend analysis",
                                    "source_dataset": ds_name,
                                    "config": {
                                        "group_by": date_columns[0],
                                        "frequency": "daily",
                                        "aggregations": {
                                            "count": "*",
                                            "numeric_columns": "mean"
                                        }
                                    },
                                    "output_name": f"{ds_name}_daily_agg"
                                })
                    
                    elif req == "metric_calculation":
                        # Suggest summary statistics
                        for ds_name, schema in study_data_config.dataset_schemas.items():
                            numeric_columns = [
                                col for col, dtype in schema.get("columns", {}).items()
                                if "int" in dtype.lower() or "float" in dtype.lower() or "numeric" in dtype.lower()
                            ]
                            if numeric_columns:
                                suggestions.append({
                                    "type": "aggregation",
                                    "name": f"Summary statistics for {ds_name}",
                                    "description": f"Calculate key metrics from {ds_name}",
                                    "source_dataset": ds_name,
                                    "config": {
                                        "aggregations": {
                                            "total_records": "count",
                                            **{col: ["mean", "sum", "min", "max"] for col in numeric_columns[:3]}
                                        }
                                    },
                                    "output_name": f"{ds_name}_summary"
                                })
                    
                    elif req == "group_aggregation":
                        # Suggest grouping by categorical columns
                        for ds_name, schema in study_data_config.dataset_schemas.items():
                            categorical_columns = [
                                col for col, dtype in schema.get("columns", {}).items()
                                if "string" in dtype.lower() or "object" in dtype.lower()
                            ]
                            if categorical_columns:
                                suggestions.append({
                                    "type": "aggregation",
                                    "name": f"Group analysis of {ds_name}",
                                    "description": f"Aggregate {ds_name} by categories",
                                    "source_dataset": ds_name,
                                    "config": {
                                        "group_by": categorical_columns[0],
                                        "aggregations": {
                                            "count": "*",
                                            "numeric_columns": "mean"
                                        }
                                    },
                                    "output_name": f"{ds_name}_by_{categorical_columns[0].lower()}"
                                })
    
    return {
        "suggestions": suggestions[:5],  # Limit to top 5 suggestions
        "total_suggestions": len(suggestions),
        "based_on_template": study.dashboard_template_id is not None
    }