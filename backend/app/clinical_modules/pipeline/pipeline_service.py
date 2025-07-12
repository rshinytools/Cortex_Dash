# ABOUTME: Service layer for pipeline management, execution, and versioning
# ABOUTME: Handles pipeline orchestration, step execution, and result tracking

import uuid
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json
import traceback
from sqlmodel import Session, select

from app.models.pipeline import (
    PipelineConfig, PipelineExecution, PipelineExecutionStep,
    TransformationScript, PipelineStatus, TransformationType
)
from app.models import DataSourceUpload, Study, User
from app.clinical_modules.pipeline.script_executor import TransformationScriptExecutor
from app.clinical_modules.utils.folder_structure import get_study_data_path, get_timestamp_folder
from app.core.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

class PipelineService:
    """Service for managing pipeline configurations and executions"""
    
    def __init__(self, db: Session):
        self.db = db
        self.script_executor = TransformationScriptExecutor()
    
    def create_pipeline_config(self, config_data: Dict[str, Any], user: User) -> PipelineConfig:
        """Create a new pipeline configuration"""
        # Check if there's an existing pipeline with the same name
        existing = self.db.exec(
            select(PipelineConfig)
            .where(PipelineConfig.study_id == config_data['study_id'])
            .where(PipelineConfig.name == config_data['name'])
            .where(PipelineConfig.is_current_version == True)
        ).first()
        
        if existing:
            # Create new version
            config_data['parent_version_id'] = existing.id
            config_data['version'] = existing.version + 1
            
            # Mark old version as not current
            existing.is_current_version = False
            self.db.add(existing)
        
        # Create new config
        pipeline_config = PipelineConfig(
            **config_data,
            created_by=user.id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(pipeline_config)
        self.db.commit()
        self.db.refresh(pipeline_config)
        
        return pipeline_config
    
    def get_pipeline_versions(self, pipeline_id: uuid.UUID) -> List[PipelineConfig]:
        """Get all versions of a pipeline"""
        current = self.db.get(PipelineConfig, pipeline_id)
        if not current:
            return []
        
        # Get all versions with the same name and study
        versions = self.db.exec(
            select(PipelineConfig)
            .where(PipelineConfig.study_id == current.study_id)
            .where(PipelineConfig.name == current.name)
            .order_by(PipelineConfig.version.desc())
        ).all()
        
        return versions
    
    def rollback_pipeline_version(self, pipeline_id: uuid.UUID, target_version: int, user: User) -> PipelineConfig:
        """Rollback to a specific pipeline version"""
        # Get target version
        target_config = self.db.exec(
            select(PipelineConfig)
            .where(PipelineConfig.id == pipeline_id)
        ).first()
        
        if not target_config:
            raise ValueError("Pipeline configuration not found")
        
        # Find the version to rollback to
        old_version = self.db.exec(
            select(PipelineConfig)
            .where(PipelineConfig.study_id == target_config.study_id)
            .where(PipelineConfig.name == target_config.name)
            .where(PipelineConfig.version == target_version)
        ).first()
        
        if not old_version:
            raise ValueError(f"Version {target_version} not found")
        
        # Create new version from old one
        new_config = PipelineConfig(
            name=old_version.name,
            description=f"Rollback to version {target_version}",
            study_id=old_version.study_id,
            source_config=old_version.source_config,
            transformation_steps=old_version.transformation_steps,
            output_config=old_version.output_config,
            schedule_cron=old_version.schedule_cron,
            retry_on_failure=old_version.retry_on_failure,
            max_retries=old_version.max_retries,
            timeout_seconds=old_version.timeout_seconds,
            version=target_config.version + 1,
            parent_version_id=target_config.id,
            is_current_version=True,
            created_by=user.id,
            created_at=datetime.utcnow()
        )
        
        # Mark current as not current
        current_versions = self.db.exec(
            select(PipelineConfig)
            .where(PipelineConfig.study_id == target_config.study_id)
            .where(PipelineConfig.name == target_config.name)
            .where(PipelineConfig.is_current_version == True)
        ).all()
        
        for cv in current_versions:
            cv.is_current_version = False
            self.db.add(cv)
        
        self.db.add(new_config)
        self.db.commit()
        self.db.refresh(new_config)
        
        return new_config
    
    def validate_transformation_script(self, script_content: str, script_type: TransformationType,
                                     allowed_imports: List[str] = None) -> Tuple[bool, List[str]]:
        """Validate a transformation script"""
        if script_type == TransformationType.PYTHON_SCRIPT:
            return self.script_executor.validator.validate(script_content)
        elif script_type == TransformationType.SQL_QUERY:
            # Basic SQL validation
            # TODO: Implement SQL validation
            return True, []
        else:
            return False, ["Unsupported script type"]
    
    def create_transformation_script(self, script_data: Dict[str, Any], user: User) -> TransformationScript:
        """Create and validate a transformation script"""
        # Validate script
        is_valid, errors = self.validate_transformation_script(
            script_data['script_content'],
            script_data['script_type'],
            script_data.get('allowed_imports')
        )
        
        # Create script record
        script = TransformationScript(
            **script_data,
            script_hash=self.script_executor.hash_script(script_data['script_content']),
            is_validated=is_valid,
            validation_errors=errors if not is_valid else None,
            created_by=user.id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(script)
        self.db.commit()
        self.db.refresh(script)
        
        return script

class PipelineExecutor:
    """Handles pipeline execution logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.script_executor = TransformationScriptExecutor()
    
    def execute_pipeline(self, execution_id: uuid.UUID) -> Dict[str, Any]:
        """Execute a pipeline"""
        # Get execution record
        execution = self.db.get(PipelineExecution, execution_id)
        if not execution:
            raise ValueError("Pipeline execution not found")
        
        # Update status to running
        execution.status = PipelineStatus.RUNNING
        execution.started_at = datetime.utcnow()
        self.db.add(execution)
        self.db.commit()
        
        try:
            # Get pipeline configuration
            config = execution.config
            
            # Get data source
            input_data = self._load_input_data(execution, config)
            
            # Execute transformation steps
            current_data = input_data
            for idx, step in enumerate(config.transformation_steps):
                step_result = self._execute_step(execution, idx, step, current_data)
                current_data = step_result['output_data']
            
            # Save output
            output_info = self._save_output(execution, config, current_data)
            
            # Update execution as successful
            execution.status = PipelineStatus.SUCCESS
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
            execution.output_records = len(current_data)
            execution.output_path = output_info['path']
            execution.output_version = output_info['version']
            
            self.db.add(execution)
            self.db.commit()
            
            return {
                'status': 'success',
                'execution_id': str(execution_id),
                'output_path': output_info['path'],
                'records_processed': len(current_data)
            }
            
        except Exception as e:
            # Update execution as failed
            execution.status = PipelineStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
            execution.error_message = str(e)
            execution.error_details = {'traceback': traceback.format_exc()}
            
            self.db.add(execution)
            self.db.commit()
            
            logger.error(f"Pipeline execution {execution_id} failed: {str(e)}")
            raise
    
    def _load_input_data(self, execution: PipelineExecution, config: PipelineConfig) -> pd.DataFrame:
        """Load input data based on source configuration"""
        source_config = config.source_config
        
        if source_config['type'] == 'data_upload':
            # Load from uploaded data
            if execution.data_version_id:
                upload = self.db.get(DataSourceUpload, execution.data_version_id)
            else:
                # Get active version
                upload = self.db.exec(
                    select(DataSourceUpload)
                    .where(DataSourceUpload.study_id == config.study_id)
                    .where(DataSourceUpload.is_active_version == True)
                ).first()
            
            if not upload:
                raise ValueError("No data source found")
            
            # Load the specified dataset
            dataset_name = source_config.get('dataset_name')
            if not dataset_name:
                raise ValueError("Dataset name not specified in source configuration")
            
            # Find the file
            study = self.db.get(Study, config.study_id)
            data_path = get_study_data_path(study.org_id, study.id, upload.folder_timestamp)
            
            parquet_file = None
            for file_info in upload.files_extracted or []:
                if file_info['dataset_name'] == dataset_name:
                    parquet_file = data_path / file_info['parquet_path'].split('/')[-1]
                    break
            
            if not parquet_file or not parquet_file.exists():
                raise ValueError(f"Dataset '{dataset_name}' not found")
            
            # Add execution log
            execution.execution_log.append({
                'timestamp': datetime.utcnow().isoformat(),
                'step': 'load_data',
                'message': f"Loading dataset '{dataset_name}' from {parquet_file}"
            })
            
            return pd.read_parquet(parquet_file)
        
        else:
            raise ValueError(f"Unsupported source type: {source_config['type']}")
    
    def _execute_step(self, execution: PipelineExecution, step_index: int, 
                     step_config: Dict[str, Any], input_data: pd.DataFrame) -> Dict[str, Any]:
        """Execute a single transformation step"""
        # Create step record
        step = PipelineExecutionStep(
            execution_id=execution.id,
            step_index=step_index,
            step_name=step_config.get('name', f'Step {step_index + 1}'),
            step_type=step_config['type'],
            step_config=step_config,
            status=PipelineStatus.RUNNING,
            started_at=datetime.utcnow(),
            input_records=len(input_data)
        )
        self.db.add(step)
        self.db.commit()
        
        try:
            # Execute based on step type
            if step_config['type'] == TransformationType.PYTHON_SCRIPT:
                # Get script
                script_id = step_config.get('script_id')
                if script_id:
                    script = self.db.get(TransformationScript, script_id)
                    script_content = script.script_content
                    allowed_imports = script.allowed_imports
                    resource_limits = script.resource_limits
                else:
                    script_content = step_config.get('script_content', '')
                    allowed_imports = step_config.get('allowed_imports')
                    resource_limits = step_config.get('resource_limits')
                
                # Execute script
                output_data, metadata = self.script_executor.execute_script(
                    script_content,
                    input_data,
                    parameters=step_config.get('parameters'),
                    allowed_imports=allowed_imports,
                    resource_limits=resource_limits
                )
                
            elif step_config['type'] == TransformationType.FILTER:
                # Apply filters
                conditions = step_config.get('conditions', [])
                output_data = input_data.copy()
                
                for condition in conditions:
                    col = condition['column']
                    op = condition['operator']
                    value = condition['value']
                    
                    if op == '==':
                        output_data = output_data[output_data[col] == value]
                    elif op == '!=':
                        output_data = output_data[output_data[col] != value]
                    elif op == '>':
                        output_data = output_data[output_data[col] > value]
                    elif op == '>=':
                        output_data = output_data[output_data[col] >= value]
                    elif op == '<':
                        output_data = output_data[output_data[col] < value]
                    elif op == '<=':
                        output_data = output_data[output_data[col] <= value]
                    elif op == 'in':
                        output_data = output_data[output_data[col].isin(value)]
                    elif op == 'contains':
                        output_data = output_data[output_data[col].str.contains(value, na=False)]
                
                metadata = {'filters_applied': len(conditions)}
                
            else:
                raise ValueError(f"Unsupported step type: {step_config['type']}")
            
            # Update step as successful
            step.status = PipelineStatus.SUCCESS
            step.completed_at = datetime.utcnow()
            step.duration_seconds = (step.completed_at - step.started_at).total_seconds()
            step.output_records = len(output_data)
            step.result_summary = metadata
            
            self.db.add(step)
            self.db.commit()
            
            # Add to execution log
            execution.execution_log.append({
                'timestamp': datetime.utcnow().isoformat(),
                'step': step.step_name,
                'message': f"Step completed successfully. Input: {step.input_records} rows, Output: {step.output_records} rows"
            })
            
            return {
                'output_data': output_data,
                'metadata': metadata
            }
            
        except Exception as e:
            # Update step as failed
            step.status = PipelineStatus.FAILED
            step.completed_at = datetime.utcnow()
            step.duration_seconds = (step.completed_at - step.started_at).total_seconds()
            step.error_message = str(e)
            
            self.db.add(step)
            self.db.commit()
            
            raise
    
    def _save_output(self, execution: PipelineExecution, config: PipelineConfig, 
                    output_data: pd.DataFrame) -> Dict[str, Any]:
        """Save pipeline output"""
        output_config = config.output_config
        
        # Get study for folder structure
        study = self.db.get(Study, config.study_id)
        
        # Create output version folder
        output_version = get_timestamp_folder()
        output_path = get_study_data_path(study.org_id, study.id, output_version) / "pipeline_output"
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save based on output format
        output_format = output_config.get('format', 'parquet')
        output_name = output_config.get('name', f'pipeline_output_{execution.id}')
        
        if output_format == 'parquet':
            output_file = output_path / f"{output_name}.parquet"
            output_data.to_parquet(output_file, index=False)
        elif output_format == 'csv':
            output_file = output_path / f"{output_name}.csv"
            output_data.to_csv(output_file, index=False)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        # Save metadata
        metadata_file = output_path / f"{output_name}_metadata.json"
        metadata = {
            'execution_id': str(execution.id),
            'pipeline_config_id': str(config.id),
            'pipeline_name': config.name,
            'pipeline_version': config.version,
            'created_at': datetime.utcnow().isoformat(),
            'row_count': len(output_data),
            'columns': list(output_data.columns),
            'data_types': {col: str(dtype) for col, dtype in output_data.dtypes.items()}
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        execution.execution_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'step': 'save_output',
            'message': f"Output saved to {output_file}"
        })
        
        return {
            'path': str(output_file),
            'version': output_version,
            'format': output_format,
            'row_count': len(output_data)
        }

# Celery tasks
@celery_app.task(bind=True)
def execute_pipeline_task(self, execution_id: str, db_session_id: str):
    """Celery task to execute a pipeline"""
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        executor = PipelineExecutor(db)
        result = executor.execute_pipeline(uuid.UUID(execution_id))
        return result
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        raise
    finally:
        db.close()