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
from app.models import User, Study, DashboardTemplate as UnifiedDashboardTemplate, Organization, StudyDataConfiguration, StudyPhase
from app.core.permissions import has_permission, Permission
from app.services.file_processing_service import FileProcessingService
from app.services.file_conversion_service import FileConversionService

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
            Study.status == "DRAFT",
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization to create studies"
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
    
    # Create study
    study = Study(
        name=study_info.name,
        code=study_code,
        protocol_number=study_info.protocol_number,
        description=study_info.description,
        phase=phase_enum,
        therapeutic_area=study_info.therapeutic_area,
        indication=study_info.indication,
        org_id=current_user.org_id,
        created_by=current_user.id,
        status="draft",  # Use lowercase for enum value
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
    
    # Get all active templates
    templates = db.exec(
        select(UnifiedDashboardTemplate).where(
            UnifiedDashboardTemplate.is_active == True,
            UnifiedDashboardTemplate.status.in_(["published", "PUBLISHED"])
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
    template = db.get(UnifiedDashboardTemplate, request.template_id)
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
        study_data_config = StudyDataConfiguration(
            study_id=study_id,
            dataset_schemas=conversion_results["datasets"],
            created_by=current_user.id
        )
        db.add(study_data_config)
    else:
        study_data_config.dataset_schemas = conversion_results["datasets"]
        study_data_config.updated_at = datetime.utcnow()
        study_data_config.updated_by = current_user.id
    
    # Store processing results
    study.initialization_steps["file_processing"] = conversion_results
    study.initialization_steps["data_folder"] = conversion_results.get("summary", {}).get("data_folder", "")
    db.add(study)
    db.commit()
    
    # Generate mapping suggestions if we have datasets
    if conversion_results["datasets"] and study.dashboard_template_id:
        template = db.get(UnifiedDashboardTemplate, study.dashboard_template_id)
        if template and template.template_structure:
            # Extract widget data requirements
            template_requirements = []
            dashboards = template.template_structure.get("dashboardTemplates", [])
            for dashboard in dashboards:
                for widget in dashboard.get("widgets", []):
                    if widget.get("dataConfiguration"):
                        template_requirements.append({
                            "widget_id": widget["id"],
                            "widget_title": widget.get("title", "Unknown Widget"),
                            "widget_type": widget["type"],
                            "data_config": widget["dataConfiguration"]
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
        template = db.get(UnifiedDashboardTemplate, study.dashboard_template_id)
        if template and template.template_structure:
            # Extract widget data requirements
            dashboards = template.template_structure.get("dashboardTemplates", [])
            for dashboard in dashboards:
                for widget in dashboard.get("widgets", []):
                    if widget.get("dataConfiguration"):
                        template_requirements.append({
                            "widget_id": widget["id"],
                            "widget_title": widget.get("title", "Unknown Widget"),
                            "widget_type": widget["type"],
                            "data_config": widget["dataConfiguration"]
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
    if request.custom_mappings:
        study.field_mappings = request.custom_mappings
    
    study.initialization_steps["auto_mappings_accepted"] = request.accept_auto_mappings
    study.initialization_status = "wizard_completed"
    study.mappings_configured_at = datetime.utcnow()
    
    # Change status from DRAFT to SETUP when wizard is completed
    study.status = "SETUP"
    
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
    if study.status == "draft" or study.status == "DRAFT":  # Handle both cases
        try:
            # Try to delete the study
            db.delete(study)
            db.commit()
            return {"message": "Draft study deleted"}
        except Exception as e:
            logger.error(f"Error deleting draft study: {str(e)}")
            db.rollback()
            
            # Alternative: just mark as cancelled instead of deleting
            study.initialization_status = "wizard_cancelled"
            study.status = "cancelled"
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