# ABOUTME: Tests documenting the complete study creation and initialization workflow
# ABOUTME: Shows the 4-phase process from creation to dashboard activation
"""
Study Creation Workflow Documentation
=====================================

This test suite documents the complete study creation and initialization process.
The platform uses a 4-phase wizard to guide users through study setup.

Phases:
1. Basic Information - Study metadata and configuration
2. Template Selection - Choose dashboard template
3. Data Upload - Upload clinical data files
4. Field Mapping - Map data columns to widget requirements

Key Concepts:
- Draft studies don't count against organization limits
- Studies can be paused and resumed at any phase
- File processing extracts schema automatically
- Intelligent mapping suggestions based on column names
- Background initialization after wizard completion
"""

import pytest
import asyncio
from typing import Dict, List, Any
from datetime import datetime
from sqlmodel import Session, select
from app.models import Study, Organization, User, DashboardTemplate
from app.schemas.study import StudyCreate
from app.crud import study as crud_study
from app.services.study_initialization_service import StudyInitializationService
from app.services.file_processing_service import FileProcessingService
from tests.utils.utils import random_lower_string


class TestStudyCreationWorkflow:
    """
    QC Documentation: Complete Study Creation Process
    
    This test class documents the entire workflow from study creation
    through dashboard activation, including all decision points.
    
    Business Requirements:
    - Studies must have valid metadata before proceeding
    - Template selection determines data requirements
    - All required fields must be mapped before activation
    - Initialization runs as background process
    - Users can track progress in real-time
    """
    
    async def test_complete_study_creation_flow(
        self,
        db: Session,
        normal_user: User,
        test_org: Organization,
        sample_dashboard_template: DashboardTemplate
    ):
        """
        Test Case: End-to-end study creation with all phases
        
        Scenario: Create study, upload data, map fields, activate
        Expected: Study fully initialized with working dashboard
        
        This test demonstrates:
        - Draft study creation
        - Template selection with requirements
        - File upload and processing
        - Automatic and manual field mapping
        - Background initialization
        - Progress tracking
        """
        
        # Phase 1: Basic Information (Create Draft Study)
        study_data = {
            "name": "COVID-19 Vaccine Trial",
            "protocol_number": "COV-2023-001",
            "description": "Phase 3 efficacy and safety study",
            "phase": "phase_3",
            "therapeutic_area": "Infectious Disease",
            "indication": "COVID-19 Prevention",
            "planned_enrollment": 30000,
            "number_of_sites": 150,
            "study_duration_months": 24,
            "primary_endpoint": "Vaccine efficacy against symptomatic COVID-19"
        }
        
        # Create draft study
        draft_study = crud_study.create_draft(
            db=db,
            study_data=study_data,
            owner_id=normal_user.id,
            org_id=test_org.id
        )
        
        assert draft_study.status == "draft"
        assert draft_study.initialization_status == "pending"
        
        # Verify draft doesn't count against org limit
        active_count = crud_study.get_organization_study_count(db, test_org.id)
        assert active_count == 0  # Drafts excluded
        
        # Phase 2: Template Selection
        template_id = sample_dashboard_template.id
        
        # Select template and view requirements
        crud_study.select_template(
            db=db,
            study_id=draft_study.id,
            template_id=template_id
        )
        
        # Get data requirements from template
        data_requirements = sample_dashboard_template.data_requirements
        assert len(data_requirements) > 0
        
        # Show required datasets and fields
        required_datasets = {req["dataset"] for req in data_requirements}
        print(f"Required datasets: {required_datasets}")
        
        # Phase 3: Data Upload and Processing
        # Simulate file uploads
        uploaded_files = [
            {
                "name": "demographics.csv",
                "path": "/data/temp/demographics.csv",
                "size": 1024000,
                "type": "text/csv"
            },
            {
                "name": "adverse_events.sas7bdat",
                "path": "/data/temp/adverse_events.sas7bdat",
                "size": 5120000,
                "type": "application/x-sas-data"
            },
            {
                "name": "laboratory.xlsx",
                "path": "/data/temp/laboratory.xlsx",
                "size": 2048000,
                "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        ]
        
        # Process files to extract schema
        file_processor = FileProcessingService()
        schema_results = await file_processor.process_uploaded_files(
            study_id=str(draft_study.id),
            uploaded_files=uploaded_files
        )
        
        # Verify schema extraction
        assert "demographics" in schema_results["datasets"]
        assert "adverse_events" in schema_results["datasets"]
        assert "laboratory" in schema_results["datasets"]
        
        # Example schema structure
        demo_schema = schema_results["datasets"]["demographics"]
        assert "columns" in demo_schema
        assert demo_schema["column_count"] > 0
        
        # Store schema in study
        crud_study.update_study_schema(
            db=db,
            study_id=draft_study.id,
            schema_data=schema_results
        )
        
        # Phase 4: Field Mapping
        # Generate automatic mapping suggestions
        mapping_suggestions = file_processor.generate_mapping_suggestions(
            template_requirements=data_requirements,
            dataset_schemas=schema_results["datasets"]
        )
        
        # Example mapping for demographics widget
        demo_widget_mapping = mapping_suggestions.get("demographics-summary", [])
        
        # User reviews and adjusts mappings
        final_mappings = {}
        for widget_id, suggestions in mapping_suggestions.items():
            widget_mappings = {}
            for suggestion in suggestions:
                if suggestion["confidence"] > 0.7:
                    # Accept high-confidence suggestions
                    widget_mappings[suggestion["field_name"]] = {
                        "dataset": suggestion["suggested_dataset"],
                        "column": suggestion["suggested_column"]
                    }
                else:
                    # Manual mapping for low confidence
                    # In real app, user selects from dropdown
                    widget_mappings[suggestion["field_name"]] = {
                        "dataset": "demographics",
                        "column": "SUBJID"  # Example manual selection
                    }
            final_mappings[widget_id] = widget_mappings
        
        # Save mappings
        crud_study.save_field_mappings(
            db=db,
            study_id=draft_study.id,
            mappings=final_mappings
        )
        
        # Complete wizard and start initialization
        study = crud_study.complete_wizard(
            db=db,
            study_id=draft_study.id,
            final_data={
                "mappings": final_mappings,
                "template_id": template_id,
                "uploaded_files": uploaded_files
            }
        )
        
        assert study.status == "initializing"
        assert study.initialization_status == "in_progress"
        
        # Initialization Process (runs in background)
        init_service = StudyInitializationService()
        
        # Simulate initialization steps
        init_steps = [
            ("applying_template", "Applying dashboard template"),
            ("processing_data", "Processing uploaded files"),
            ("creating_datasets", "Creating study datasets"),
            ("applying_mappings", "Applying field mappings"),
            ("generating_dashboards", "Generating dashboard pages"),
            ("validating", "Validating configuration")
        ]
        
        for step_id, description in init_steps:
            # Update progress
            crud_study.update_initialization_progress(
                db=db,
                study_id=study.id,
                step=step_id,
                progress=0,
                message=description
            )
            
            # Simulate step execution
            await asyncio.sleep(0.1)  # In real app, actual processing
            
            # Update completion
            crud_study.update_initialization_progress(
                db=db,
                study_id=study.id,
                step=step_id,
                progress=100,
                message=f"{description} - Complete"
            )
        
        # Mark initialization complete
        study = crud_study.complete_initialization(
            db=db,
            study_id=study.id,
            success=True
        )
        
        assert study.status == "active"
        assert study.initialization_status == "completed"
        
        # Verify dashboard is ready
        assert study.dashboard_config is not None
        assert len(study.dashboard_config["menu_structure"]) > 0
        
        # Verify datasets created
        study_datasets = crud_study.get_study_datasets(db, study.id)
        assert len(study_datasets) == len(required_datasets)
    
    async def test_study_creation_with_errors(
        self,
        db: Session,
        normal_user: User,
        test_org: Organization
    ):
        """
        Test Case: Study creation with validation errors and recovery
        
        Scenario: Various error conditions during creation
        Expected: Appropriate error handling and user guidance
        
        Error scenarios:
        - Organization at study limit
        - Invalid file formats
        - Missing required fields
        - Mapping conflicts
        - Initialization failures
        """
        
        # Scenario 1: Organization at study limit
        test_org.max_studies = 1
        
        # Create one active study to hit limit
        existing_study = crud_study.create(
            db=db,
            obj_in=StudyCreate(
                name="Existing Study",
                protocol_number="EXIST-001",
                phase="phase_2"
            ),
            owner_id=normal_user.id,
            org_id=test_org.id
        )
        
        # Try to create another (should fail)
        with pytest.raises(ValueError, match="study limit"):
            crud_study.create(
                db=db,
                obj_in=StudyCreate(
                    name="New Study",
                    protocol_number="NEW-001",
                    phase="phase_2"
                ),
                owner_id=normal_user.id,
                org_id=test_org.id
            )
        
        # But draft should work
        draft = crud_study.create_draft(
            db=db,
            study_data={"name": "Draft Study", "protocol_number": "DRAFT-001"},
            owner_id=normal_user.id,
            org_id=test_org.id
        )
        assert draft.status == "draft"
        
        # Scenario 2: Invalid file upload
        file_processor = FileProcessingService()
        
        invalid_files = [
            {
                "name": "document.pdf",
                "path": "/data/temp/document.pdf",
                "size": 1024000,
                "type": "application/pdf"
            }
        ]
        
        result = await file_processor.process_uploaded_files(
            study_id=str(draft.id),
            uploaded_files=invalid_files
        )
        
        assert len(result["errors"]) > 0
        assert "Unsupported file type" in result["errors"][0]
        
        # Scenario 3: Missing required mappings
        template = db.exec(
            select(DashboardTemplate).where(
                DashboardTemplate.is_active == True
            )
        ).first()
        
        # Incomplete mappings (missing required fields)
        incomplete_mappings = {
            "widget-1": {
                "field_1": {"dataset": "demo", "column": "COL1"}
                # Missing field_2 which is required
            }
        }
        
        # Validation should fail
        validation_result = crud_study.validate_mappings(
            template_requirements=template.data_requirements,
            provided_mappings=incomplete_mappings
        )
        
        assert validation_result["valid"] == False
        assert "missing required field" in validation_result["errors"][0].lower()
        
        # Scenario 4: Initialization failure recovery
        study_to_fail = crud_study.create_draft(
            db=db,
            study_data={"name": "Will Fail", "protocol_number": "FAIL-001"},
            owner_id=normal_user.id,
            org_id=test_org.id
        )
        
        # Simulate initialization failure
        crud_study.update_initialization_progress(
            db=db,
            study_id=study_to_fail.id,
            step="processing_data",
            progress=50,
            message="Error: Corrupted data file",
            status="failed"
        )
        
        # Study should be in failed state
        study_to_fail = db.get(Study, study_to_fail.id)
        assert study_to_fail.initialization_status == "failed"
        
        # User can retry initialization
        crud_study.retry_initialization(
            db=db,
            study_id=study_to_fail.id,
            fix_data={"new_file": "path/to/fixed/file.csv"}
        )
        
        assert study_to_fail.initialization_status == "pending"
    
    async def test_resume_draft_study(
        self,
        db: Session,
        normal_user: User,
        test_org: Organization
    ):
        """
        Test Case: Resume draft study from any phase
        
        Scenario: User leaves and returns to continue setup
        Expected: Progress preserved, can continue from last step
        
        Resume points:
        - After basic info before template
        - After template before upload  
        - After upload before mapping
        - During mapping
        """
        
        # Create draft with partial progress
        draft = crud_study.create_draft(
            db=db,
            study_data={
                "name": "Interrupted Study",
                "protocol_number": "INT-001",
                "phase": "phase_2"
            },
            owner_id=normal_user.id,
            org_id=test_org.id
        )
        
        # Save progress at different points
        wizard_state = {
            "current_step": 2,  # On template selection
            "completed_steps": ["basic_info"],
            "step_data": {
                "basic_info": {
                    "name": "Interrupted Study",
                    "protocol_number": "INT-001",
                    "phase": "phase_2",
                    "therapeutic_area": "Oncology"
                }
            }
        }
        
        crud_study.save_wizard_progress(
            db=db,
            study_id=draft.id,
            wizard_state=wizard_state
        )
        
        # User returns - check for draft
        user_drafts = crud_study.get_user_draft_studies(
            db=db,
            user_id=normal_user.id
        )
        
        assert len(user_drafts) == 1
        assert user_drafts[0].id == draft.id
        
        # Resume from saved state
        resumed_state = crud_study.get_wizard_state(
            db=db,
            study_id=draft.id
        )
        
        assert resumed_state["current_step"] == 2
        assert "basic_info" in resumed_state["completed_steps"]
        assert resumed_state["step_data"]["basic_info"]["name"] == "Interrupted Study"
        
        # Continue with template selection
        resumed_state["current_step"] = 3
        resumed_state["completed_steps"].append("template_selection")
        resumed_state["step_data"]["template_selection"] = {
            "template_id": "template-123",
            "template_name": "Safety Dashboard"
        }
        
        crud_study.save_wizard_progress(
            db=db,
            study_id=draft.id,
            wizard_state=resumed_state
        )
        
        # Verify progress saved
        draft = db.get(Study, draft.id)
        assert draft.initialization_steps["current_step"] == 3
    
    async def test_multi_site_study_setup(
        self,
        db: Session,
        normal_user: User,
        test_org: Organization
    ):
        """
        Test Case: Complex multi-site study configuration
        
        Scenario: Large study with site-specific configurations
        Expected: Proper handling of site hierarchies and permissions
        
        Features demonstrated:
        - Site-specific data filtering
        - Regional groupings
        - Site performance tracking
        - Blinded vs unblinded views
        """
        
        # Create study with site structure
        study_data = {
            "name": "Global Diabetes Study",
            "protocol_number": "DIAB-2024-001",
            "phase": "phase_3",
            "number_of_sites": 50,
            "regions": ["North America", "Europe", "Asia-Pacific"],
            "site_structure": {
                "North America": {
                    "countries": ["USA", "Canada"],
                    "sites": [
                        {"id": "US001", "name": "Johns Hopkins", "pi": "Dr. Smith"},
                        {"id": "US002", "name": "Mayo Clinic", "pi": "Dr. Jones"},
                        {"id": "CA001", "name": "Toronto General", "pi": "Dr. Brown"}
                    ]
                },
                "Europe": {
                    "countries": ["UK", "Germany", "France"],
                    "sites": [
                        {"id": "UK001", "name": "Oxford", "pi": "Dr. Wilson"},
                        {"id": "DE001", "name": "Charité", "pi": "Dr. Mueller"},
                        {"id": "FR001", "name": "Salpêtrière", "pi": "Dr. Dubois"}
                    ]
                },
                "Asia-Pacific": {
                    "countries": ["Japan", "Australia"],
                    "sites": [
                        {"id": "JP001", "name": "Tokyo University", "pi": "Dr. Tanaka"},
                        {"id": "AU001", "name": "Melbourne Royal", "pi": "Dr. Taylor"}
                    ]
                }
            }
        }
        
        study = crud_study.create_with_sites(
            db=db,
            study_data=study_data,
            owner_id=normal_user.id,
            org_id=test_org.id
        )
        
        # Configure site-specific dashboards
        site_dashboard_config = {
            "global_view": {
                "menu_items": ["overview", "enrollment", "safety", "efficacy"],
                "permissions": ["global_monitor", "sponsor"]
            },
            "regional_view": {
                "menu_items": ["regional_overview", "site_comparison"],
                "permissions": ["regional_monitor"],
                "data_filter": "region"
            },
            "site_view": {
                "menu_items": ["site_overview", "subject_listing", "queries"],
                "permissions": ["site_staff"],
                "data_filter": "site_id"
            }
        }
        
        crud_study.configure_site_dashboards(
            db=db,
            study_id=study.id,
            config=site_dashboard_config
        )
        
        # Set up blinding configuration
        blinding_config = {
            "blinded_until": "database_lock",
            "unblinded_roles": ["dsmb_member", "statistician"],
            "blinded_fields": ["treatment_arm", "randomization_code"],
            "partially_blinded": {
                "safety_monitor": ["can_see_aggregate_safety", "cannot_see_by_treatment"]
            }
        }
        
        crud_study.configure_blinding(
            db=db,
            study_id=study.id,
            blinding_config=blinding_config
        )
        
        # Verify site structure
        sites = crud_study.get_study_sites(db, study.id)
        assert len(sites) == 8
        
        # Check regional grouping
        na_sites = [s for s in sites if s.region == "North America"]
        assert len(na_sites) == 3
        
        # Verify dashboard access control
        site_user_dashboard = crud_study.get_user_dashboard_config(
            db=db,
            study_id=study.id,
            user_role="site_staff",
            site_id="US001"
        )
        
        assert "site_overview" in site_user_dashboard["menu_items"]
        assert site_user_dashboard["data_filter"]["site_id"] == "US001"
    
    def test_data_agnostic_mapping(self, db: Session, normal_user: User):
        """
        Test Case: Platform handles any data structure (not just CDISC)
        
        Scenario: Custom data format with business-specific columns
        Expected: Successful mapping without CDISC requirements
        
        Demonstrates:
        - No hardcoded CDISC requirements
        - Flexible column naming
        - Custom data structures
        - Business-specific schemas
        """
        
        # Non-CDISC data example (e.g., device/wearable data)
        custom_schema = {
            "activity_data": {
                "columns": {
                    "participant_code": {"type": "string"},
                    "measurement_timestamp": {"type": "datetime"},
                    "steps_count": {"type": "number"},
                    "heart_rate_avg": {"type": "number"},
                    "sleep_quality_score": {"type": "number"},
                    "activity_category": {"type": "string"}
                }
            },
            "survey_responses": {
                "columns": {
                    "response_id": {"type": "string"},
                    "participant_code": {"type": "string"},
                    "survey_date": {"type": "date"},
                    "pain_scale": {"type": "number"},
                    "mood_rating": {"type": "string"},
                    "medication_taken": {"type": "boolean"}
                }
            }
        }
        
        # Widget requirements (also non-CDISC)
        widget_requirements = [
            {
                "widget_id": "activity-summary",
                "required_fields": {
                    "user_identifier": {"type": "string"},
                    "daily_steps": {"type": "number"},
                    "avg_heart_rate": {"type": "number"}
                }
            },
            {
                "widget_id": "wellness-tracker",
                "required_fields": {
                    "user_identifier": {"type": "string"},
                    "pain_level": {"type": "number"},
                    "mood": {"type": "string"}
                }
            }
        ]
        
        # Mapping works with any column names
        mappings = {
            "activity-summary": {
                "user_identifier": {
                    "dataset": "activity_data",
                    "column": "participant_code"
                },
                "daily_steps": {
                    "dataset": "activity_data",
                    "column": "steps_count"
                },
                "avg_heart_rate": {
                    "dataset": "activity_data",
                    "column": "heart_rate_avg"
                }
            },
            "wellness-tracker": {
                "user_identifier": {
                    "dataset": "survey_responses",
                    "column": "participant_code"
                },
                "pain_level": {
                    "dataset": "survey_responses",
                    "column": "pain_scale"
                },
                "mood": {
                    "dataset": "survey_responses",
                    "column": "mood_rating"
                }
            }
        }
        
        # Validate mappings (should pass without CDISC requirements)
        validation = crud_study.validate_custom_mappings(
            schema=custom_schema,
            requirements=widget_requirements,
            mappings=mappings
        )
        
        assert validation["valid"] == True
        assert len(validation["warnings"]) == 0
        
        # Platform accepts any data structure
        print("Platform successfully mapped non-clinical data format")