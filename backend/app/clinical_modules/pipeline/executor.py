# ABOUTME: Pipeline executor that orchestrates data processing workflows
# ABOUTME: Manages pipeline execution, monitoring, and error handling

import uuid
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path
import logging
import json

from sqlmodel import Session, select
from app.models import Study, DataSource, User
from app.crud import activity_log as crud_activity
from app.clinical_modules.data_sources.factory import DataSourceFactory
from app.clinical_modules.transformations.engine import TransformationEngine


class PipelineExecutor:
    """Executes data processing pipelines"""
    
    def __init__(
        self,
        study: Study,
        db: Session,
        user: Optional[User] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.study = study
        self.db = db
        self.user = user
        self.logger = logger or logging.getLogger(__name__)
        self.pipeline_id = str(uuid.uuid4())
        self.start_time = None
        self.status = "initialized"
        self.progress = 0
        self.current_step = ""
        self.errors = []
        
    async def execute(
        self,
        pipeline_config: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Execute a data processing pipeline
        
        Args:
            pipeline_config: Pipeline configuration dict
            progress_callback: Optional callback for progress updates
            
        Returns:
            Execution results dictionary
        """
        self.start_time = datetime.utcnow()
        self.status = "running"
        results = {
            "pipeline_id": self.pipeline_id,
            "study_id": str(self.study.id),
            "start_time": self.start_time.isoformat(),
            "steps": []
        }
        
        try:
            # Log pipeline start
            self._log_activity("pipeline_started", {
                "pipeline_id": self.pipeline_id,
                "config": pipeline_config
            })
            
            # Step 1: Data Acquisition
            self._update_progress(10, "Starting data acquisition", progress_callback)
            acquisition_results = await self._execute_data_acquisition(
                pipeline_config.get("data_sources", []),
                progress_callback
            )
            results["steps"].append(acquisition_results)
            
            # Step 2: Data Validation
            self._update_progress(30, "Validating data", progress_callback)
            validation_results = await self._execute_validation(
                acquisition_results.get("downloaded_files", []),
                pipeline_config.get("validation_rules", {}),
                progress_callback
            )
            results["steps"].append(validation_results)
            
            # Step 3: Data Transformation
            self._update_progress(50, "Transforming data", progress_callback)
            transformation_results = await self._execute_transformations(
                validation_results.get("valid_files", []),
                pipeline_config.get("transformations", []),
                progress_callback
            )
            results["steps"].append(transformation_results)
            
            # Step 4: Data Storage
            self._update_progress(80, "Storing processed data", progress_callback)
            storage_results = await self._execute_storage(
                transformation_results.get("output_files", []),
                pipeline_config.get("storage_config", {}),
                progress_callback
            )
            results["steps"].append(storage_results)
            
            # Step 5: Cleanup
            self._update_progress(90, "Cleaning up", progress_callback)
            cleanup_results = await self._execute_cleanup(
                pipeline_config.get("cleanup_config", {}),
                progress_callback
            )
            results["steps"].append(cleanup_results)
            
            # Complete
            self.status = "completed"
            self._update_progress(100, "Pipeline completed successfully", progress_callback)
            
            results["end_time"] = datetime.utcnow().isoformat()
            results["duration_seconds"] = (
                datetime.utcnow() - self.start_time
            ).total_seconds()
            results["status"] = "success"
            results["errors"] = self.errors
            
            # Save pipeline results
            await self._save_pipeline_results(results)
            
            # Log completion
            self._log_activity("pipeline_completed", {
                "pipeline_id": self.pipeline_id,
                "duration": results["duration_seconds"],
                "files_processed": len(transformation_results.get("output_files", []))
            })
            
        except Exception as e:
            self.status = "failed"
            self.errors.append(str(e))
            results["status"] = "failed"
            results["error"] = str(e)
            results["errors"] = self.errors
            
            self._log_activity("pipeline_failed", {
                "pipeline_id": self.pipeline_id,
                "error": str(e)
            }, success=False)
            
            if progress_callback:
                progress_callback(self.progress, f"Pipeline failed: {str(e)}")
            
            raise
        
        return results
    
    async def _execute_data_acquisition(
        self,
        data_sources: List[str],
        progress_callback: Optional[Callable]
    ) -> Dict[str, Any]:
        """Execute data acquisition step"""
        results = {
            "step": "data_acquisition",
            "start_time": datetime.utcnow().isoformat(),
            "data_sources": [],
            "downloaded_files": []
        }
        
        try:
            # Get active data sources for the study
            query = select(DataSource).where(
                DataSource.study_id == self.study.id,
                DataSource.active == True
            )
            
            if data_sources:
                query = query.where(DataSource.id.in_(data_sources))
            
            sources = self.db.exec(query).all()
            
            for i, source in enumerate(sources):
                source_progress = 10 + (20 * i / len(sources))
                self._update_progress(
                    source_progress,
                    f"Acquiring data from {source.name}",
                    progress_callback
                )
                
                try:
                    # Create connector
                    connector = DataSourceFactory.create_connector(
                        source, self.study, self.db, self.logger
                    )
                    
                    # Test connection
                    connected, error = await connector.test_connection()
                    if not connected:
                        raise Exception(f"Connection failed: {error}")
                    
                    # List available data
                    available_data = await connector.list_available_data()
                    
                    # Download each dataset
                    for dataset in available_data:
                        download_path = connector.get_download_path(dataset["id"])
                        success, error = await connector.download_data(
                            dataset["id"],
                            download_path,
                            lambda p, m: self._update_progress(
                                source_progress + (p * 0.2),
                                m,
                                progress_callback
                            )
                        )
                        
                        if success:
                            results["downloaded_files"].append({
                                "source_id": str(source.id),
                                "source_name": source.name,
                                "dataset_id": dataset["id"],
                                "path": str(download_path),
                                "size": dataset.get("size_estimate"),
                                "format": dataset.get("format")
                            })
                        else:
                            self.errors.append(f"Failed to download {dataset['id']}: {error}")
                    
                    results["data_sources"].append({
                        "id": str(source.id),
                        "name": source.name,
                        "status": "success",
                        "datasets_downloaded": len(available_data)
                    })
                    
                except Exception as e:
                    error_msg = f"Error with source {source.name}: {str(e)}"
                    self.errors.append(error_msg)
                    results["data_sources"].append({
                        "id": str(source.id),
                        "name": source.name,
                        "status": "failed",
                        "error": str(e)
                    })
            
            results["end_time"] = datetime.utcnow().isoformat()
            results["total_files"] = len(results["downloaded_files"])
            
        except Exception as e:
            results["error"] = str(e)
            raise
        
        return results
    
    async def _execute_validation(
        self,
        files: List[Dict[str, Any]],
        validation_rules: Dict[str, Any],
        progress_callback: Optional[Callable]
    ) -> Dict[str, Any]:
        """Execute data validation step"""
        results = {
            "step": "validation",
            "start_time": datetime.utcnow().isoformat(),
            "files_validated": 0,
            "valid_files": [],
            "invalid_files": []
        }
        
        for i, file_info in enumerate(files):
            progress = 30 + (20 * i / len(files))
            self._update_progress(
                progress,
                f"Validating {Path(file_info['path']).name}",
                progress_callback
            )
            
            # Basic validation for now
            file_path = Path(file_info["path"])
            
            if file_path.exists():
                # Add more sophisticated validation based on file type
                is_valid = True
                validation_errors = []
                
                # Check file size
                if validation_rules.get("max_file_size_mb"):
                    max_size = validation_rules["max_file_size_mb"] * 1024 * 1024
                    if file_path.stat().st_size > max_size:
                        is_valid = False
                        validation_errors.append("File exceeds maximum size")
                
                # Check file format
                allowed_formats = validation_rules.get("allowed_formats", [])
                if allowed_formats and file_info.get("format") not in allowed_formats:
                    is_valid = False
                    validation_errors.append(f"Invalid format: {file_info.get('format')}")
                
                if is_valid:
                    results["valid_files"].append(file_info)
                else:
                    results["invalid_files"].append({
                        **file_info,
                        "validation_errors": validation_errors
                    })
                
                results["files_validated"] += 1
            else:
                results["invalid_files"].append({
                    **file_info,
                    "validation_errors": ["File not found"]
                })
        
        results["end_time"] = datetime.utcnow().isoformat()
        return results
    
    async def _execute_transformations(
        self,
        files: List[Dict[str, Any]],
        transformations: List[Dict[str, Any]],
        progress_callback: Optional[Callable]
    ) -> Dict[str, Any]:
        """Execute data transformation step"""
        results = {
            "step": "transformation",
            "start_time": datetime.utcnow().isoformat(),
            "transformations_applied": [],
            "output_files": []
        }
        
        # Initialize transformation engine
        engine = TransformationEngine(self.study, self.logger)
        
        output_base = Path(self.study.folder_path) / "processed" / "current"
        output_base.mkdir(parents=True, exist_ok=True)
        
        for i, transformation in enumerate(transformations):
            progress = 50 + (30 * i / len(transformations))
            self._update_progress(
                progress,
                f"Applying transformation: {transformation.get('name', 'Unknown')}",
                progress_callback
            )
            
            try:
                # Apply transformation
                output_files = await engine.apply_transformation(
                    input_files=[f["path"] for f in files],
                    transformation_config=transformation,
                    output_path=output_base
                )
                
                results["output_files"].extend(output_files)
                results["transformations_applied"].append({
                    "name": transformation.get("name"),
                    "type": transformation.get("type"),
                    "status": "success",
                    "output_count": len(output_files)
                })
                
            except Exception as e:
                error_msg = f"Transformation failed: {str(e)}"
                self.errors.append(error_msg)
                results["transformations_applied"].append({
                    "name": transformation.get("name"),
                    "type": transformation.get("type"),
                    "status": "failed",
                    "error": str(e)
                })
        
        results["end_time"] = datetime.utcnow().isoformat()
        return results
    
    async def _execute_storage(
        self,
        files: List[Dict[str, Any]],
        storage_config: Dict[str, Any],
        progress_callback: Optional[Callable]
    ) -> Dict[str, Any]:
        """Execute data storage step"""
        results = {
            "step": "storage",
            "start_time": datetime.utcnow().isoformat(),
            "files_stored": 0,
            "storage_locations": []
        }
        
        # For now, files are already in the processed folder
        # This step would handle additional storage like database loading
        
        results["files_stored"] = len(files)
        results["storage_locations"].append({
            "type": "filesystem",
            "path": str(Path(self.study.folder_path) / "processed" / "current"),
            "file_count": len(files)
        })
        
        results["end_time"] = datetime.utcnow().isoformat()
        return results
    
    async def _execute_cleanup(
        self,
        cleanup_config: Dict[str, Any],
        progress_callback: Optional[Callable]
    ) -> Dict[str, Any]:
        """Execute cleanup step"""
        results = {
            "step": "cleanup",
            "start_time": datetime.utcnow().isoformat(),
            "actions": []
        }
        
        # Clean temporary files
        temp_path = Path(self.study.folder_path) / "temp"
        if temp_path.exists() and cleanup_config.get("clean_temp", True):
            for temp_file in temp_path.iterdir():
                try:
                    if temp_file.is_file():
                        temp_file.unlink()
                    results["actions"].append({
                        "action": "delete_temp_file",
                        "path": str(temp_file),
                        "status": "success"
                    })
                except Exception as e:
                    results["actions"].append({
                        "action": "delete_temp_file",
                        "path": str(temp_file),
                        "status": "failed",
                        "error": str(e)
                    })
        
        results["end_time"] = datetime.utcnow().isoformat()
        return results
    
    async def _save_pipeline_results(self, results: Dict[str, Any]):
        """Save pipeline execution results"""
        logs_path = Path(self.study.folder_path) / "logs"
        logs_path.mkdir(parents=True, exist_ok=True)
        
        result_file = logs_path / f"pipeline_{self.pipeline_id}.json"
        with open(result_file, "w") as f:
            json.dump(results, f, indent=2)
    
    def _update_progress(
        self,
        progress: int,
        message: str,
        callback: Optional[Callable]
    ):
        """Update progress and notify callback"""
        self.progress = progress
        self.current_step = message
        
        if callback:
            callback(progress, message)
    
    def _log_activity(
        self,
        action: str,
        details: Dict[str, Any],
        success: bool = True
    ):
        """Log pipeline activity"""
        if self.user:
            crud_activity.create_activity_log(
                self.db,
                user=self.user,
                action=f"pipeline_{action}",
                resource_type="pipeline",
                resource_id=self.pipeline_id,
                details={
                    **details,
                    "study_id": str(self.study.id)
                },
                success=success
            )