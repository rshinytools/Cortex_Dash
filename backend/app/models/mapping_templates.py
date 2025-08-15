# ABOUTME: Models for reusable mapping templates and transformation definitions
# ABOUTME: Enables saving and reusing common field mappings and data transformations

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

from sqlmodel import Field, SQLModel, Relationship, Column, JSON
from sqlalchemy import UniqueConstraint


class TransformationType(str, Enum):
    """Types of data transformations"""
    FIELD_RENAME = "field_rename"
    VALUE_MAPPING = "value_mapping"
    CALCULATION = "calculation"
    DATE_FORMAT = "date_format"
    UNIT_CONVERSION = "unit_conversion"
    AGGREGATION = "aggregation"
    CONDITIONAL = "conditional"
    REGEX_EXTRACT = "regex_extract"
    CONCATENATION = "concatenation"
    SPLIT = "split"
    CUSTOM_SCRIPT = "custom_script"


class MappingTemplateScope(str, Enum):
    """Scope of mapping template availability"""
    SYSTEM = "system"  # Available to all organizations
    ORGANIZATION = "organization"  # Available within organization
    STUDY = "study"  # Specific to a study
    USER = "user"  # Personal templates


class MappingTemplate(SQLModel, table=True):
    """Reusable mapping template for widget configuration"""
    __tablename__ = "mapping_templates"
    __table_args__ = (
        UniqueConstraint("name", "organization_id", name="uq_mapping_template_name_org"),
    )
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True, description="Template name")
    description: Optional[str] = Field(default=None, description="Template description")
    
    # Scope and ownership
    scope: MappingTemplateScope = Field(default=MappingTemplateScope.ORGANIZATION)
    organization_id: Optional[UUID] = Field(default=None, foreign_key="organization.id")
    study_id: Optional[UUID] = Field(default=None, foreign_key="study.id")
    created_by: UUID = Field(foreign_key="user.id")
    
    # Template configuration
    widget_type: str = Field(description="Widget type this template is for")
    source_system: Optional[str] = Field(default=None, description="Source system (e.g., Medidata Rave)")
    
    # Mapping configuration
    field_mappings: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Field mapping configuration"
    )
    
    # Transformations to apply
    transformations: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="List of transformations to apply"
    )
    
    # Default filters and joins
    default_filters: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Default filters to apply"
    )
    
    default_joins: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Default joins configuration"
    )
    
    # Display configuration defaults
    display_config: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Default display configuration"
    )
    
    # Metadata
    tags: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Tags for categorization"
    )
    
    is_active: bool = Field(default=True)
    is_validated: bool = Field(default=False, description="Has been validated against data")
    validation_date: Optional[datetime] = Field(default=None)
    validation_notes: Optional[str] = Field(default=None)
    
    # Usage tracking
    usage_count: int = Field(default=0, description="Number of times used")
    last_used_at: Optional[datetime] = Field(default=None)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    organization: Optional["Organization"] = Relationship()
    study: Optional["Study"] = Relationship()
    creator: Optional["User"] = Relationship()
    transformations_rel: List["TransformationDefinition"] = Relationship(back_populates="template")


class TransformationDefinition(SQLModel, table=True):
    """Definition of a data transformation"""
    __tablename__ = "transformation_definitions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    template_id: Optional[UUID] = Field(default=None, foreign_key="mapping_templates.id")
    
    # Transformation details
    name: str = Field(description="Transformation name")
    description: Optional[str] = Field(default=None)
    transformation_type: TransformationType
    
    # Source and target
    source_fields: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Source fields for transformation"
    )
    target_field: str = Field(description="Target field name")
    
    # Transformation configuration
    config: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Transformation configuration"
    )
    
    # Execution order
    execution_order: int = Field(default=0, description="Order of execution")
    
    # Validation
    is_valid: bool = Field(default=True)
    validation_rules: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Validation rules for output"
    )
    
    # Error handling
    on_error: str = Field(default="skip", description="Action on error: skip, default, fail")
    default_value: Optional[Any] = Field(default=None, sa_column=Column(JSON))
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    template: Optional["MappingTemplate"] = Relationship(back_populates="transformations_rel")


class MappingTemplateVersion(SQLModel, table=True):
    """Version history for mapping templates"""
    __tablename__ = "mapping_template_versions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    template_id: UUID = Field(foreign_key="mapping_templates.id", index=True)
    
    version_number: int = Field(description="Version number")
    version_tag: Optional[str] = Field(default=None, description="Version tag/label")
    
    # Snapshot of configuration at this version
    field_mappings: Dict[str, Any] = Field(sa_column=Column(JSON))
    transformations: List[Dict[str, Any]] = Field(sa_column=Column(JSON))
    default_filters: List[Dict[str, Any]] = Field(sa_column=Column(JSON))
    default_joins: List[Dict[str, Any]] = Field(sa_column=Column(JSON))
    display_config: Dict[str, Any] = Field(sa_column=Column(JSON))
    
    # Version metadata
    change_description: Optional[str] = Field(default=None)
    created_by: UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Validation status at time of version
    is_validated: bool = Field(default=False)
    validation_notes: Optional[str] = Field(default=None)


class TransformationLibrary(SQLModel, table=True):
    """Library of reusable transformation functions"""
    __tablename__ = "transformation_library"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(unique=True, index=True)
    category: str = Field(index=True, description="Category of transformation")
    description: Optional[str] = Field(default=None)
    
    # Function definition
    function_type: TransformationType
    function_code: Optional[str] = Field(default=None, description="Python code for custom functions")
    
    # Parameters
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Parameter definitions"
    )
    
    # Examples
    examples: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Usage examples"
    )
    
    # Validation
    input_schema: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Expected input schema"
    )
    output_schema: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Expected output schema"
    )
    
    # Metadata
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    is_system: bool = Field(default=False, description="System-provided function")
    is_active: bool = Field(default=True)
    
    # Usage
    usage_count: int = Field(default=0)
    performance_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Performance metrics"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: UUID = Field(foreign_key="user.id")


class MappingTemplateUsage(SQLModel, table=True):
    """Track usage of mapping templates"""
    __tablename__ = "mapping_template_usage"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    template_id: UUID = Field(foreign_key="mapping_templates.id", index=True)
    
    # Usage context
    widget_id: UUID = Field(foreign_key="widget_definitions.id")
    study_id: UUID = Field(foreign_key="study.id")
    user_id: UUID = Field(foreign_key="user.id")
    
    # Usage details
    used_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    modifications: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Modifications made to template"
    )
    
    # Performance metrics
    execution_time_ms: Optional[int] = Field(default=None)
    records_processed: Optional[int] = Field(default=None)
    errors_count: Optional[int] = Field(default=None)
    
    # Feedback
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    feedback: Optional[str] = Field(default=None)