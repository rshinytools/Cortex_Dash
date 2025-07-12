# ABOUTME: SQLModel models for data pipeline management and execution
# ABOUTME: Tracks pipeline configurations, executions, and transformation scripts

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid
from sqlmodel import Field, SQLModel, Column, JSON, Relationship
from pydantic import BaseModel

class PipelineStatus(str, Enum):
    """Pipeline execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"

class TransformationType(str, Enum):
    """Types of transformations available"""
    PYTHON_SCRIPT = "python_script"
    SQL_QUERY = "sql_query"
    MAPPING = "mapping"
    AGGREGATION = "aggregation"
    FILTER = "filter"
    JOIN = "join"
    PIVOT = "pivot"
    CUSTOM = "custom"

# Base Pipeline Configuration
class PipelineConfigBase(SQLModel):
    """Base pipeline configuration model"""
    name: str = Field(index=True)
    description: Optional[str] = None
    study_id: uuid.UUID = Field(foreign_key="study.id", index=True)
    is_active: bool = Field(default=True)
    schedule_cron: Optional[str] = None  # For scheduled pipelines
    retry_on_failure: bool = Field(default=True)
    max_retries: int = Field(default=3)
    timeout_seconds: int = Field(default=3600)  # 1 hour default
    
class PipelineConfig(PipelineConfigBase, table=True):
    """Pipeline configuration stored in database"""
    __tablename__ = "pipeline_configs"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    version: int = Field(default=1, index=True)
    is_current_version: bool = Field(default=True)
    parent_version_id: Optional[uuid.UUID] = Field(default=None, foreign_key="pipeline_configs.id")
    
    # Configuration JSON
    source_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    transformation_steps: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    output_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: uuid.UUID = Field(foreign_key="user.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    
    # Relationships
    executions: List["PipelineExecution"] = Relationship(back_populates="config")
    transformation_scripts: List["TransformationScript"] = Relationship(back_populates="pipeline_config")

# Pipeline Execution
class PipelineExecutionBase(SQLModel):
    """Base pipeline execution model"""
    pipeline_config_id: uuid.UUID = Field(foreign_key="pipeline_configs.id", index=True)
    status: PipelineStatus = Field(default=PipelineStatus.PENDING, index=True)
    triggered_by: str = Field(default="manual")  # manual, scheduled, api, etc.
    
class PipelineExecution(PipelineExecutionBase, table=True):
    """Pipeline execution history"""
    __tablename__ = "pipeline_executions"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: Optional[str] = Field(default=None, index=True)  # Celery task ID
    
    # Execution details
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Data processing metrics
    input_records: Optional[int] = None
    output_records: Optional[int] = None
    records_failed: Optional[int] = None
    
    # Version info - what data version was used
    data_version_id: Optional[uuid.UUID] = Field(default=None, foreign_key="data_source_uploads.id")
    
    # Error handling
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    retry_count: int = Field(default=0)
    
    # Execution log
    execution_log: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Output location
    output_path: Optional[str] = None
    output_version: Optional[str] = None  # YYYYMMDD_HHMMSS format
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: uuid.UUID = Field(foreign_key="user.id")
    
    # Relationships
    config: PipelineConfig = Relationship(back_populates="executions")
    execution_steps: List["PipelineExecutionStep"] = Relationship(back_populates="execution")

# Pipeline Execution Steps
class PipelineExecutionStep(SQLModel, table=True):
    """Individual steps within a pipeline execution"""
    __tablename__ = "pipeline_execution_steps"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    execution_id: uuid.UUID = Field(foreign_key="pipeline_executions.id", index=True)
    step_index: int
    step_name: str
    step_type: TransformationType
    
    # Status
    status: PipelineStatus = Field(default=PipelineStatus.PENDING)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Metrics
    input_records: Optional[int] = None
    output_records: Optional[int] = None
    
    # Configuration used
    step_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Results
    result_summary: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    error_message: Optional[str] = None
    
    # Relationships
    execution: PipelineExecution = Relationship(back_populates="execution_steps")

# Transformation Scripts
class TransformationScript(SQLModel, table=True):
    """User-defined transformation scripts"""
    __tablename__ = "transformation_scripts"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    pipeline_config_id: uuid.UUID = Field(foreign_key="pipeline_configs.id", index=True)
    name: str
    description: Optional[str] = None
    
    # Script details
    script_type: TransformationType
    script_content: str  # The actual Python/SQL code
    script_hash: str  # SHA256 hash for integrity
    
    # Validation
    is_validated: bool = Field(default=False)
    validation_errors: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    
    # Security
    allowed_imports: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    resource_limits: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Version control
    version: int = Field(default=1)
    is_current_version: bool = Field(default=True)
    parent_version_id: Optional[uuid.UUID] = Field(default=None, foreign_key="transformation_scripts.id")
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: uuid.UUID = Field(foreign_key="user.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    
    # Relationships
    pipeline_config: PipelineConfig = Relationship(back_populates="transformation_scripts")

# Request/Response models for API
class PipelineConfigCreate(BaseModel):
    """Create a new pipeline configuration"""
    name: str
    description: Optional[str] = None
    study_id: uuid.UUID
    schedule_cron: Optional[str] = None
    source_config: Dict[str, Any]
    transformation_steps: List[Dict[str, Any]]
    output_config: Dict[str, Any]
    retry_on_failure: bool = True
    max_retries: int = 3
    timeout_seconds: int = 3600

class PipelineConfigUpdate(BaseModel):
    """Update pipeline configuration"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    schedule_cron: Optional[str] = None
    source_config: Optional[Dict[str, Any]] = None
    transformation_steps: Optional[List[Dict[str, Any]]] = None
    output_config: Optional[Dict[str, Any]] = None
    retry_on_failure: Optional[bool] = None
    max_retries: Optional[int] = None
    timeout_seconds: Optional[int] = None

class PipelineExecuteRequest(BaseModel):
    """Request to execute a pipeline"""
    pipeline_config_id: uuid.UUID
    data_version_id: Optional[uuid.UUID] = None  # Use specific data version
    parameters: Optional[Dict[str, Any]] = None  # Runtime parameters
    triggered_by: str = "manual"

class TransformationScriptCreate(BaseModel):
    """Create a transformation script"""
    pipeline_config_id: uuid.UUID
    name: str
    description: Optional[str] = None
    script_type: TransformationType
    script_content: str
    allowed_imports: List[str] = ["pandas", "numpy", "datetime", "re", "json"]
    resource_limits: Dict[str, Any] = {
        "max_memory_mb": 1024,
        "max_execution_time_seconds": 300,
        "max_cpu_percent": 80
    }

class PipelineExecutionResponse(BaseModel):
    """Response after starting pipeline execution"""
    execution_id: uuid.UUID
    task_id: str
    status: PipelineStatus
    message: str
    estimated_duration_seconds: Optional[int] = None