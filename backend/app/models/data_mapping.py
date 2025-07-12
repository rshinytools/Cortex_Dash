# ABOUTME: Models for widget data mapping configuration
# ABOUTME: Handles field mappings between data sources and widget requirements

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid
from sqlmodel import Field, SQLModel, Column, JSON, Relationship
from pydantic import BaseModel

class MappingType(str, Enum):
    """Types of field mappings"""
    DIRECT = "direct"  # Direct column mapping
    CALCULATED = "calculated"  # Calculated from multiple columns
    CONSTANT = "constant"  # Fixed value
    TRANSFORMATION = "transformation"  # Requires transformation

class DataType(str, Enum):
    """Supported data types for mapping"""
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"

# Widget Data Mapping Configuration
class WidgetDataMapping(SQLModel, table=True):
    """Maps data fields to widget requirements"""
    __tablename__ = "widget_data_mappings"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    study_id: uuid.UUID = Field(foreign_key="study.id", index=True)
    widget_id: uuid.UUID = Field(foreign_key="widget_definitions.id", index=True)
    
    # Mapping configuration
    field_mappings: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    # Example structure:
    # {
    #   "value": {
    #     "type": "direct",
    #     "source_field": "lab_value",
    #     "data_type": "number"
    #   },
    #   "label": {
    #     "type": "direct", 
    #     "source_field": "test_name",
    #     "data_type": "string"
    #   },
    #   "category": {
    #     "type": "calculated",
    #     "expression": "CONCAT(visit_name, ' - ', test_category)",
    #     "data_type": "string"
    #   }
    # }
    
    # Data source configuration
    data_source_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    # Example:
    # {
    #   "dataset_name": "lab_results",
    #   "filters": [{"column": "test_type", "operator": "==", "value": "HEMATOLOGY"}],
    #   "pipeline_id": "uuid"  # Optional: use transformed data from pipeline
    # }
    
    # Validation rules
    validation_rules: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Metadata
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: uuid.UUID = Field(foreign_key="user.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    
    # Relationships
    study: Optional["Study"] = Relationship(back_populates="widget_mappings")
    widget: Optional["WidgetDefinition"] = Relationship(back_populates="data_mappings")

# Study Data Configuration
class StudyDataConfiguration(SQLModel, table=True):
    """Overall data configuration for a study"""
    __tablename__ = "study_data_configurations"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    study_id: uuid.UUID = Field(foreign_key="study.id", unique=True, index=True)
    
    # Available datasets and their schemas
    dataset_schemas: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    # Example:
    # {
    #   "demographics": {
    #     "columns": {
    #       "subject_id": {"type": "string", "nullable": false},
    #       "age": {"type": "number", "nullable": true},
    #       "sex": {"type": "string", "nullable": false}
    #     },
    #     "row_count": 1500,
    #     "last_updated": "2024-01-04T10:00:00Z"
    #   }
    # }
    
    # Global mappings that apply to all widgets
    global_mappings: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Data quality metrics
    data_quality_metrics: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Configuration status
    is_initialized: bool = Field(default=False)
    initialization_completed_at: Optional[datetime] = None
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: uuid.UUID = Field(foreign_key="user.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")

# Field Mapping Template
class FieldMappingTemplate(SQLModel, table=True):
    """Reusable field mapping templates"""
    __tablename__ = "field_mapping_templates"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    org_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    
    name: str = Field(index=True)
    description: Optional[str] = None
    category: str  # e.g., "demographics", "lab_results", "adverse_events"
    
    # Template configuration
    field_mappings: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    applicable_widget_types: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Usage tracking
    usage_count: int = Field(default=0)
    last_used_at: Optional[datetime] = None
    
    # Metadata
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: uuid.UUID = Field(foreign_key="user.id")

# Request/Response models
class FieldMappingRequest(BaseModel):
    """Request to create or update field mapping"""
    field_name: str
    mapping_type: MappingType
    source_field: Optional[str] = None
    expression: Optional[str] = None
    constant_value: Optional[Any] = None
    data_type: DataType
    transformation_config: Optional[Dict[str, Any]] = None

class DataMappingConfigRequest(BaseModel):
    """Request to configure widget data mapping"""
    widget_id: uuid.UUID
    field_mappings: Dict[str, FieldMappingRequest]
    data_source_config: Dict[str, Any]
    validation_rules: Optional[List[Dict[str, Any]]] = None

class StudyInitializationRequest(BaseModel):
    """Request to initialize study data configuration"""
    study_id: uuid.UUID
    dataset_uploads: List[uuid.UUID]  # List of DataSourceUpload IDs to analyze
    auto_detect_mappings: bool = True

class MappingValidationResult(BaseModel):
    """Result of mapping validation"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    sample_data: Optional[List[Dict[str, Any]]] = None
    coverage: Dict[str, float] = {}  # Field coverage percentage

class MappingSuggestion(BaseModel):
    """Suggested mapping for a field"""
    field_name: str
    suggested_source_field: str
    confidence: float  # 0.0 to 1.0
    reason: str
    data_type_match: bool
    sample_values: List[Any] = []