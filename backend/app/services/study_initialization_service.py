# ABOUTME: Study initialization service that orchestrates the entire initialization process
# ABOUTME: Handles template application, data upload, parquet conversion, and field mapping

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import json

from sqlmodel import Session
from sqlalchemy.orm.attributes import flag_modified
from fastapi import HTTPException

from app.models import Study, DashboardTemplate, User
from app.core.db import engine
from app.core.websocket_manager import websocket_manager
from app.services.file_conversion_service import FileConversionService
from app.services.field_mapping_service import FieldMappingService
from app.services.template_service import TemplateService
from app.crud import study as study_crud

logger = logging.getLogger(__name__)


class StudyInitializationService:
    """Orchestrates the study initialization process with real-time progress updates"""
    
    def __init__(self, db: Session):
        self.db = db
        self.file_conversion_service = FileConversionService()
        self.field_mapping_service = FieldMappingService(db)
        self.template_service = TemplateService(db)
    
    async def initialize_study(
        self,
        study_id: uuid.UUID,
        template_id: uuid.UUID,
        uploaded_files: List[Dict[str, Any]],
        current_user: User
    ) -> Study:
        """
        Initialize a study with template, data upload, and mapping
        
        Args:
            study_id: The study to initialize
            template_id: The template to apply
            uploaded_files: List of uploaded file info
            current_user: User performing the initialization
        
        Returns:
            Updated study object
        """
        study = self.db.get(Study, study_id)
        if not study:
            raise HTTPException(status_code=404, detail="Study not found")
        
        if study.org_id != current_user.org_id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Start initialization
        await self._update_status(study, "initializing", 0, {
            "current_step": "starting",
            "total_steps": 4,
            "steps": {
                "template_application": {"status": "pending", "progress": 0},
                "data_upload": {"status": "pending", "progress": 0},
                "data_conversion": {"status": "pending", "progress": 0},
                "field_mapping": {"status": "pending", "progress": 0}
            }
        })
        
        try:
            # Step 1: Apply template
            await self._apply_template(study, template_id)
            
            # Step 2: Process uploaded files
            await self._process_uploaded_files(study, uploaded_files)
            
            # Step 3: Convert to Parquet
            await self._convert_to_parquet(study)
            
            # Step 4: Configure field mappings
            await self._configure_field_mappings(study, template_id)
            
            # Mark as completed
            await self._update_status(study, "completed", 100, {
                "current_step": "completed",
                "completed_at": datetime.utcnow().isoformat()
            })
            
            # Update study activation
            study.activated_at = datetime.utcnow()
            self.db.add(study)
            self.db.commit()
            self.db.refresh(study)
            
            return study
            
        except Exception as e:
            logger.error(f"Study initialization failed for {study_id}: {str(e)}")
            await self._update_status(study, "failed", study.initialization_progress, {
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            })
            raise
    
    async def _apply_template(self, study: Study, template_id: uuid.UUID):
        """Apply dashboard template to study"""
        await self._update_step_status(study, "template_application", "in_progress", 0)
        
        try:
            # Get template
            template = self.db.get(DashboardTemplate, template_id)
            if not template:
                raise ValueError("Template not found")
            
            # Apply template to study
            study.dashboard_template_id = template_id
            study.template_applied_at = datetime.utcnow()
            
            # Copy template structure to study configuration
            study.dashboard_config = template.template_structure
            
            self.db.add(study)
            self.db.commit()
            
            await self._update_step_status(study, "template_application", "completed", 100)
            await self._update_progress(study, 25)
            
        except Exception as e:
            await self._update_step_status(study, "template_application", "failed", 0)
            raise Exception(f"Template application failed: {str(e)}")
    
    async def _process_uploaded_files(self, study: Study, uploaded_files: List[Dict[str, Any]]):
        """Process uploaded data files"""
        await self._update_step_status(study, "data_upload", "in_progress", 0)
        
        try:
            processed_files = []
            total_files = len(uploaded_files)
            
            # Check if files are already in a versioned source_data folder
            if uploaded_files and len(uploaded_files) > 0:
                first_file_path = Path(uploaded_files[0]["path"])
                # Check if already in source_data versioned folder
                if "source_data" in str(first_file_path) and first_file_path.exists():
                    # Files are already in the correct location (uploaded by wizard)
                    logger.info(f"Files already in versioned folder, skipping move operation")
                    for idx, file_info in enumerate(uploaded_files):
                        file_path = Path(file_info["path"])
                        if file_path.exists():
                            processed_files.append({
                                "name": file_path.name,
                                "path": str(file_path),
                                "size": file_path.stat().st_size,
                                "type": file_info.get("type", "unknown")
                            })
                        # Update progress
                        progress = int((idx + 1) / total_files * 100)
                        await self._update_step_status(study, "data_upload", "in_progress", progress)
                else:
                    # Files need to be moved to versioned folder (legacy path)
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    data_dir = Path(f"/data/{study.org_id}/studies/{study.id}/source_data/{timestamp}")
                    data_dir.mkdir(parents=True, exist_ok=True)
                    
                    for idx, file_info in enumerate(uploaded_files):
                        # Process each file
                        file_path = Path(file_info["path"])
                        target_path = data_dir / file_path.name
                        
                        # Move/copy file to study directory
                        if file_path.exists():
                            file_path.rename(target_path)
                            processed_files.append({
                                "name": file_path.name,
                                "path": str(target_path),
                                "size": target_path.stat().st_size,
                                "type": file_info.get("type", "unknown")
                            })
                        
                        # Update progress
                        progress = int((idx + 1) / total_files * 100)
                        await self._update_step_status(study, "data_upload", "in_progress", progress)
            
            # Save file metadata
            study.data_uploaded_at = datetime.utcnow()
            study.config["uploaded_files"] = processed_files
            flag_modified(study, "config")
            
            self.db.add(study)
            self.db.commit()
            
            await self._update_step_status(study, "data_upload", "completed", 100)
            await self._update_progress(study, 50)
            
        except Exception as e:
            await self._update_step_status(study, "data_upload", "failed", 0)
            raise Exception(f"Data upload failed: {str(e)}")
    
    async def _convert_to_parquet(self, study: Study):
        """Convert uploaded files to Parquet format"""
        await self._update_step_status(study, "data_conversion", "in_progress", 0)
        
        try:
            # Get uploaded files
            uploaded_files = study.config.get("uploaded_files", [])
            if not uploaded_files:
                raise ValueError("No uploaded files found")
            
            # Convert files with progress callback
            async def progress_callback(progress: int, current_file: str = None):
                await self._update_step_status(
                    study, 
                    "data_conversion", 
                    "in_progress", 
                    progress,
                    {"current_file": current_file}
                )
            
            # Process conversions
            converted_files = await self.file_conversion_service.convert_study_files(
                org_id=study.org_id,
                study_id=study.id,
                files=uploaded_files,
                progress_callback=progress_callback
            )
            
            # Update metadata
            study.config["converted_files"] = converted_files
            flag_modified(study, "config")
            self.db.add(study)
            self.db.commit()
            
            await self._update_step_status(study, "data_conversion", "completed", 100)
            await self._update_progress(study, 75)
            
        except Exception as e:
            await self._update_step_status(study, "data_conversion", "failed", 0)
            raise Exception(f"Data conversion failed: {str(e)}")
    
    async def _configure_field_mappings(self, study: Study, template_id: uuid.UUID):
        """Configure field mappings based on template requirements"""
        await self._update_step_status(study, "field_mapping", "in_progress", 0)
        
        try:
            # Extract required fields from template
            template = self.db.get(DashboardTemplate, template_id)
            if not template:
                raise ValueError("Template not found")
            
            # Get widget data requirements
            widget_requirements = self._extract_widget_requirements(template.template_structure)
            
            # Check if field mappings already exist (re-initialization scenario)
            if study.field_mappings and len(study.field_mappings) > 0:
                # Preserve existing mappings during re-initialization
                logger.info(f"Preserving existing field mappings for study {study.id}")
                mappings = study.field_mappings
                await self._update_step_status(study, "field_mapping", "in_progress", 50)
            else:
                # Generate smart mappings for new initialization
                mappings = await self.field_mapping_service.generate_smart_mappings(
                    study_id=study.id,
                    widget_requirements=widget_requirements,
                    progress_callback=lambda p: asyncio.create_task(
                        self._update_step_status(study, "field_mapping", "in_progress", p)
                    )
                )
            
            # Save mappings
            study.field_mappings = mappings
            study.mappings_configured_at = datetime.utcnow()
            self.db.add(study)
            self.db.commit()
            
            await self._update_step_status(study, "field_mapping", "completed", 100)
            await self._update_progress(study, 100)
            
        except Exception as e:
            await self._update_step_status(study, "field_mapping", "failed", 0)
            raise Exception(f"Field mapping failed: {str(e)}")
    
    def _extract_widget_requirements(self, template_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract data requirements from all widgets in template"""
        requirements = []
        
        # Extract from all dashboards
        dashboards = template_structure.get("dashboardTemplates", [])
        for dashboard in dashboards:
            for widget in dashboard.get("widgets", []):
                if widget.get("dataConfiguration"):
                    requirements.append({
                        "widget_id": widget["id"],
                        "widget_type": widget["type"],
                        "data_config": widget["dataConfiguration"]
                    })
        
        return requirements
    
    async def _update_status(
        self, 
        study: Study, 
        status: str, 
        progress: int, 
        steps: Optional[Dict[str, Any]] = None
    ):
        """Update study initialization status and broadcast"""
        study.initialization_status = status
        study.initialization_progress = progress
        if steps:
            study.initialization_steps = steps
        
        self.db.add(study)
        self.db.commit()
        
        # Broadcast update
        await websocket_manager.broadcast_status_change(
            str(study.id),
            status,
            {
                "progress": progress,
                "steps": steps
            }
        )
    
    async def _update_progress(self, study: Study, progress: int):
        """Update overall progress"""
        study.initialization_progress = progress
        self.db.add(study)
        self.db.commit()
        
        await websocket_manager.broadcast_progress(
            str(study.id),
            {
                "progress": progress,
                "step": study.initialization_steps.get("current_step", "unknown")
            }
        )
    
    async def _update_step_status(
        self,
        study: Study,
        step_name: str,
        status: str,
        progress: int,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """Update individual step status"""
        if "steps" not in study.initialization_steps:
            study.initialization_steps["steps"] = {}
        
        study.initialization_steps["steps"][step_name] = {
            "status": status,
            "progress": progress,
            "updated_at": datetime.utcnow().isoformat(),
            **(extra_data or {})
        }
        
        study.initialization_steps["current_step"] = step_name
        
        self.db.add(study)
        self.db.commit()
        
        # Broadcast step update
        await websocket_manager.broadcast_progress(
            str(study.id),
            {
                "step": step_name,
                "step_status": status,
                "step_progress": progress,
                "overall_progress": study.initialization_progress
            }
        )