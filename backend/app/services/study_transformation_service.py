# ABOUTME: Service for executing data transformation pipelines in a sandboxed environment
# ABOUTME: Handles batch pipeline execution, progress tracking, and derived dataset management

import os
import sys
import json
import hashlib
import traceback
import asyncio
import uuid
import subprocess
# resource module not available on all platforms, skip for now
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Awaitable, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass

try:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:
    pd = None
    pa = None
    pq = None

from app.clinical_modules.utils.folder_structure import (
    get_timestamp_folder,
    ensure_folder_exists
)
from app.models.pipeline import (
    PipelineConfig,
    PipelineExecution,
    PipelineExecutionStep,
    TransformationScript,
    PipelineStatus,
    TransformationType
)

logger = logging.getLogger(__name__)


@dataclass
class TransformationResult:
    """Result of a transformation execution"""
    success: bool
    output_path: str
    datasets_created: List[Dict[str, Any]]
    total_records: int
    execution_time: float
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None
    logs: Optional[List[str]] = None


@dataclass
class DatasetSchema:
    """Schema information for a generated dataset"""
    name: str
    path: str
    row_count: int
    column_count: int
    columns: Dict[str, Dict[str, Any]]
    file_size_mb: float
    sample_data: List[Dict[str, Any]]


class StudyTransformationService:
    """Service for executing study data transformation pipelines"""
    
    # Default resource limits
    DEFAULT_MEMORY_LIMIT_MB = 1024  # 1GB
    DEFAULT_CPU_TIME_SECONDS = 300  # 5 minutes
    DEFAULT_WALL_TIME_SECONDS = 600  # 10 minutes
    DEFAULT_OUTPUT_SIZE_MB = 500  # 500MB max output
    
    # Allowed imports for sandboxed execution
    ALLOWED_IMPORTS = [
        'pandas', 'numpy', 'datetime', 're', 'json', 'math',
        'statistics', 'collections', 'itertools', 'functools'
    ]
    
    # Restricted functions/modules
    RESTRICTED_PATTERNS = [
        'eval', 'exec', '__import__', 'compile', 'open',
        'subprocess', 'os.system', 'os.popen', 'socket',
        'urllib', 'requests', 'http', 'ftplib', 'telnetlib'
    ]
    
    def __init__(self):
        self.warnings = []
        self.logs = []
    
    async def execute_pipelines(
        self,
        org_id: uuid.UUID,
        study_id: uuid.UUID,
        pipeline_configs: List[PipelineConfig],
        source_data_path: str,
        progress_callback: Optional[Callable[[int, Optional[str]], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        Execute multiple pipeline configurations in batch
        
        Args:
            org_id: Organization ID
            study_id: Study ID
            pipeline_configs: List of pipeline configurations to execute
            source_data_path: Path to source data directory
            progress_callback: Async callback for progress updates
            
        Returns:
            Comprehensive results including derived datasets and execution details
        """
        self.warnings = []
        self.logs = []
        
        # Setup output directory
        timestamp = get_timestamp_folder()
        derived_path = Path("/data/studies") / str(org_id) / str(study_id) / "derived_data" / timestamp
        ensure_folder_exists(derived_path)
        
        results = {
            "org_id": str(org_id),
            "study_id": str(study_id),
            "timestamp": timestamp,
            "executed_at": datetime.utcnow().isoformat(),
            "source_data_path": source_data_path,
            "derived_data_path": str(derived_path),
            "pipelines": {},
            "datasets": {},
            "errors": [],
            "warnings": []
        }
        
        # Calculate total steps for progress tracking
        total_steps = len(pipeline_configs) * 3  # Validate, execute, extract schema for each
        current_step = 0
        
        async def update_progress(message: str):
            nonlocal current_step
            current_step += 1
            if progress_callback:
                percent = int((current_step / total_steps) * 100)
                await progress_callback(percent, message)
        
        # Execute each pipeline
        for config in pipeline_configs:
            pipeline_name = config.name
            try:
                # Step 1: Validate pipeline
                await update_progress(f"Validating pipeline: {pipeline_name}")
                validation_result = await self._validate_pipeline(config)
                
                if not validation_result["is_valid"]:
                    results["errors"].append({
                        "pipeline": pipeline_name,
                        "error": "Validation failed",
                        "details": validation_result["errors"]
                    })
                    continue
                
                # Step 2: Execute pipeline
                await update_progress(f"Executing pipeline: {pipeline_name}")
                execution_result = await self._execute_pipeline(
                    config=config,
                    source_path=Path(source_data_path),
                    output_path=derived_path / pipeline_name.lower().replace(" ", "_")
                )
                
                if execution_result.success:
                    # Step 3: Extract schemas from generated datasets
                    await update_progress(f"Extracting schemas for: {pipeline_name}")
                    
                    for dataset_info in execution_result.datasets_created:
                        dataset_path = Path(dataset_info["path"])
                        if dataset_path.exists() and dataset_path.suffix == ".parquet":
                            schema = await self._extract_parquet_schema(dataset_path)
                            dataset_name = dataset_path.stem.lower()
                            results["datasets"][dataset_name] = schema
                    
                    # Store pipeline results
                    results["pipelines"][pipeline_name] = {
                        "status": "success",
                        "output_path": execution_result.output_path,
                        "datasets_created": execution_result.datasets_created,
                        "total_records": execution_result.total_records,
                        "execution_time": execution_result.execution_time,
                        "logs": execution_result.logs
                    }
                else:
                    results["pipelines"][pipeline_name] = {
                        "status": "failed",
                        "error": execution_result.error_message,
                        "warnings": execution_result.warnings,
                        "logs": execution_result.logs
                    }
                    results["errors"].append({
                        "pipeline": pipeline_name,
                        "error": execution_result.error_message
                    })
                    
            except Exception as e:
                logger.error(f"Error executing pipeline {pipeline_name}: {str(e)}")
                results["errors"].append({
                    "pipeline": pipeline_name,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
        
        # Final progress update
        if progress_callback:
            await progress_callback(100, "Pipeline execution complete")
        
        # Add summary
        results["summary"] = {
            "total_pipelines": len(pipeline_configs),
            "successful_pipelines": sum(1 for p in results["pipelines"].values() if p.get("status") == "success"),
            "failed_pipelines": sum(1 for p in results["pipelines"].values() if p.get("status") == "failed"),
            "total_datasets_created": len(results["datasets"]),
            "has_errors": len(results["errors"]) > 0
        }
        
        # Merge warnings
        if self.warnings:
            results["warnings"].extend(self.warnings)
        
        return results
    
    async def _validate_pipeline(self, config: PipelineConfig) -> Dict[str, Any]:
        """Validate pipeline configuration and scripts"""
        errors = []
        warnings = []
        
        # Validate transformation steps
        for idx, step in enumerate(config.transformation_steps):
            step_type = step.get("type")
            
            if step_type == TransformationType.PYTHON_SCRIPT:
                # Validate Python script
                script_content = step.get("script", "")
                validation = self._validate_python_script(script_content)
                
                if validation["errors"]:
                    errors.extend([f"Step {idx + 1}: {e}" for e in validation["errors"]])
                if validation["warnings"]:
                    warnings.extend([f"Step {idx + 1}: {w}" for w in validation["warnings"]])
            
            elif step_type in [TransformationType.FILTER, TransformationType.AGGREGATION]:
                # Validate configuration
                if not step.get("config"):
                    errors.append(f"Step {idx + 1}: Missing configuration")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_python_script(self, script: str) -> Dict[str, Any]:
        """Validate Python script for security and syntax"""
        errors = []
        warnings = []
        
        # Check for restricted patterns
        for pattern in self.RESTRICTED_PATTERNS:
            if pattern in script:
                errors.append(f"Restricted function/module '{pattern}' found in script")
        
        # Validate syntax
        try:
            compile(script, "<string>", "exec")
        except SyntaxError as e:
            errors.append(f"Syntax error: {str(e)}")
        
        # Check imports
        import_lines = [line.strip() for line in script.split('\n') if line.strip().startswith(('import ', 'from '))]
        for line in import_lines:
            # Extract module name
            if line.startswith('import '):
                module = line.split()[1].split('.')[0]
            else:  # from X import Y
                module = line.split()[1].split('.')[0]
            
            if module not in self.ALLOWED_IMPORTS:
                warnings.append(f"Import of '{module}' may be restricted")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _execute_pipeline(
        self,
        config: PipelineConfig,
        source_path: Path,
        output_path: Path
    ) -> TransformationResult:
        """Execute a single pipeline with sandboxing"""
        start_time = datetime.utcnow()
        datasets_created = []
        total_records = 0
        
        try:
            # Create output directory
            ensure_folder_exists(output_path)
            
            # Create temporary execution directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Copy source data to temp directory (read-only)
                temp_source = temp_path / "source_data"
                shutil.copytree(source_path, temp_source)
                
                # Create output directory in temp
                temp_output = temp_path / "output"
                temp_output.mkdir()
                
                # Execute transformation steps
                for idx, step in enumerate(config.transformation_steps):
                    self.logs.append(f"Executing step {idx + 1}: {step.get('name', 'Unnamed')}")
                    
                    step_type = step.get("type")
                    
                    if step_type == TransformationType.PYTHON_SCRIPT:
                        # Execute Python script in sandbox
                        result = await self._execute_python_script(
                            script=step.get("script", ""),
                            source_dir=temp_source,
                            output_dir=temp_output,
                            config=step.get("config", {}),
                            resource_limits=config.output_config.get("resource_limits", {})
                        )
                        
                        if not result["success"]:
                            raise Exception(f"Step {idx + 1} failed: {result['error']}")
                        
                        if result.get("datasets_created"):
                            datasets_created.extend(result["datasets_created"])
                            total_records += result.get("total_records", 0)
                    
                    elif step_type == TransformationType.FILTER:
                        # Apply filter transformation
                        result = await self._apply_filter(
                            source_dir=temp_source,
                            output_dir=temp_output,
                            filter_config=step.get("config", {})
                        )
                        
                        if not result["success"]:
                            raise Exception(f"Step {idx + 1} failed: {result['error']}")
                        
                        datasets_created.extend(result.get("datasets_created", []))
                        total_records += result.get("total_records", 0)
                
                # Copy results to final output directory
                for item in temp_output.iterdir():
                    if item.is_file() and item.suffix == ".parquet":
                        final_path = output_path / item.name
                        shutil.copy2(item, final_path)
                        
                        # Update dataset paths
                        for dataset in datasets_created:
                            if dataset["name"] == item.stem:
                                dataset["path"] = str(final_path)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return TransformationResult(
                success=True,
                output_path=str(output_path),
                datasets_created=datasets_created,
                total_records=total_records,
                execution_time=execution_time,
                warnings=self.warnings,
                logs=self.logs
            )
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return TransformationResult(
                success=False,
                output_path=str(output_path),
                datasets_created=[],
                total_records=0,
                execution_time=execution_time,
                error_message=str(e),
                warnings=self.warnings,
                logs=self.logs
            )
    
    async def _execute_python_script(
        self,
        script: str,
        source_dir: Path,
        output_dir: Path,
        config: Dict[str, Any],
        resource_limits: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Python script in sandboxed environment"""
        
        # Create execution script
        exec_script = f"""
import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import re
import math
import statistics
from collections import defaultdict, Counter
import itertools
import functools

# Setup paths
SOURCE_DIR = r"{source_dir}"
OUTPUT_DIR = r"{output_dir}"
CONFIG = {json.dumps(config)}

# Load source data
source_files = {{}}
for file in os.listdir(SOURCE_DIR):
    if file.endswith('.parquet'):
        name = file.replace('.parquet', '')
        source_files[name] = pd.read_parquet(os.path.join(SOURCE_DIR, file))

# User script
{script}

# Save output datasets
output_info = []
for name, df in globals().items():
    if isinstance(df, pd.DataFrame) and name not in source_files:
        output_path = os.path.join(OUTPUT_DIR, f"{{name}}.parquet")
        df.to_parquet(output_path, engine='pyarrow', compression='snappy')
        output_info.append({{
            "name": name,
            "path": output_path,
            "rows": len(df),
            "columns": len(df.columns)
        }})

# Write execution results
with open(os.path.join(OUTPUT_DIR, '_execution_result.json'), 'w') as f:
    json.dump({{
        "success": True,
        "datasets_created": output_info,
        "total_records": sum(info["rows"] for info in output_info)
    }}, f)
"""
        
        # Write script to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(exec_script)
            script_path = f.name
        
        try:
            # Set resource limits
            memory_limit = resource_limits.get("max_memory_mb", self.DEFAULT_MEMORY_LIMIT_MB)
            cpu_time = resource_limits.get("max_cpu_seconds", self.DEFAULT_CPU_TIME_SECONDS)
            wall_time = resource_limits.get("max_wall_seconds", self.DEFAULT_WALL_TIME_SECONDS)
            
            # Execute script with timeout and resource limits
            loop = asyncio.get_event_loop()
            
            # Use subprocess with resource limits
            process = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    [sys.executable, script_path],
                    capture_output=True,
                    text=True,
                    timeout=wall_time,
                    env={
                        **os.environ,
                        "PYTHONPATH": "",  # Clear PYTHONPATH
                        "OMP_NUM_THREADS": "1",  # Limit threads
                    }
                )
            )
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": process.stderr or "Script execution failed"
                }
            
            # Read execution results
            result_path = output_dir / "_execution_result.json"
            if result_path.exists():
                with open(result_path, 'r') as f:
                    return json.load(f)
            else:
                return {
                    "success": False,
                    "error": "No execution result found"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Script execution timeout ({wall_time}s exceeded)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Script execution error: {str(e)}"
            }
        finally:
            # Clean up script file
            if os.path.exists(script_path):
                os.unlink(script_path)
    
    async def _apply_filter(
        self,
        source_dir: Path,
        output_dir: Path,
        filter_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply filter transformation to datasets"""
        try:
            datasets_created = []
            total_records = 0
            
            # Get filter parameters
            dataset_name = filter_config.get("dataset")
            conditions = filter_config.get("conditions", [])
            output_name = filter_config.get("output_name", f"{dataset_name}_filtered")
            
            # Load source dataset
            source_file = source_dir / f"{dataset_name}.parquet"
            if not source_file.exists():
                return {
                    "success": False,
                    "error": f"Source dataset '{dataset_name}' not found"
                }
            
            # Read parquet file
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: pd.read_parquet(source_file)
            )
            
            # Apply filters
            for condition in conditions:
                column = condition.get("column")
                operator = condition.get("operator")
                value = condition.get("value")
                
                if column not in df.columns:
                    self.warnings.append(f"Column '{column}' not found in dataset")
                    continue
                
                if operator == "equals":
                    df = df[df[column] == value]
                elif operator == "not_equals":
                    df = df[df[column] != value]
                elif operator == "greater_than":
                    df = df[df[column] > value]
                elif operator == "less_than":
                    df = df[df[column] < value]
                elif operator == "contains":
                    df = df[df[column].astype(str).str.contains(value, case=False, na=False)]
                elif operator == "in":
                    df = df[df[column].isin(value)]
            
            # Save filtered dataset
            output_path = output_dir / f"{output_name}.parquet"
            await loop.run_in_executor(
                None,
                lambda: df.to_parquet(output_path, engine='pyarrow', compression='snappy')
            )
            
            datasets_created.append({
                "name": output_name,
                "path": str(output_path),
                "rows": len(df),
                "columns": len(df.columns)
            })
            total_records = len(df)
            
            return {
                "success": True,
                "datasets_created": datasets_created,
                "total_records": total_records
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Filter transformation failed: {str(e)}"
            }
    
    async def _extract_parquet_schema(self, parquet_path: Path) -> Dict[str, Any]:
        """Extract detailed schema information from parquet file"""
        if pq is None or pd is None:
            logger.error("pyarrow/pandas not available for schema extraction")
            return {}
        
        try:
            loop = asyncio.get_event_loop()
            
            # Read parquet metadata and sample data
            def read_schema():
                parquet_file = pq.ParquetFile(parquet_path)
                metadata = parquet_file.metadata
                schema = parquet_file.schema
                
                # Read sample data
                table = parquet_file.read(columns=None, use_threads=True)
                df = table.to_pandas()
                
                return metadata, schema, df
            
            metadata, schema, df = await loop.run_in_executor(None, read_schema)
            
            # Build schema information
            schema_info = {
                "name": parquet_path.stem,
                "path": str(parquet_path),
                "row_count": metadata.num_rows,
                "column_count": len(schema),
                "file_size_mb": round(parquet_path.stat().st_size / (1024 * 1024), 2),
                "columns": {},
                "sample_data": []
            }
            
            # Extract column details
            for field in schema:
                col_name = field.name
                pandas_dtype = str(df[col_name].dtype)
                
                # Determine data type
                if 'int' in pandas_dtype or 'float' in pandas_dtype:
                    data_type = 'numeric'
                elif 'bool' in pandas_dtype:
                    data_type = 'boolean'
                elif 'datetime' in pandas_dtype:
                    data_type = 'datetime'
                else:
                    data_type = 'string'
                
                col_info = {
                    "type": data_type,
                    "nullable": field.nullable,
                    "null_count": int(df[col_name].isnull().sum()),
                    "unique_count": int(df[col_name].nunique()),
                    "pandas_dtype": pandas_dtype
                }
                
                # Add statistics for numeric columns
                if data_type == 'numeric' and not df[col_name].isnull().all():
                    col_info["stats"] = {
                        "min": float(df[col_name].min()) if not pd.isna(df[col_name].min()) else None,
                        "max": float(df[col_name].max()) if not pd.isna(df[col_name].max()) else None,
                        "mean": float(df[col_name].mean()) if not pd.isna(df[col_name].mean()) else None,
                        "std": float(df[col_name].std()) if not pd.isna(df[col_name].std()) else None
                    }
                
                # Sample values for categorical columns
                if col_info["unique_count"] <= 20:
                    unique_values = df[col_name].dropna().unique().tolist()
                    col_info["unique_values"] = [str(v) for v in unique_values[:20]]
                
                schema_info["columns"][col_name] = col_info
            
            # Add sample rows
            sample_df = df.head(5).fillna('')
            schema_info["sample_data"] = sample_df.to_dict('records')
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Error extracting parquet schema: {str(e)}")
            return {
                "name": parquet_path.stem,
                "path": str(parquet_path),
                "error": str(e)
            }
    
    def get_derived_data_path(
        self,
        org_id: uuid.UUID,
        study_id: uuid.UUID,
        timestamp: Optional[str] = None
    ) -> Path:
        """Get the path for derived data storage"""
        if timestamp is None:
            timestamp = get_timestamp_folder()
        
        return Path("/data/studies") / str(org_id) / str(study_id) / "derived_data" / timestamp