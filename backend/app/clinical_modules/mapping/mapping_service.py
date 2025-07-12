# ABOUTME: Service layer for data mapping and field configuration
# ABOUTME: Handles mapping suggestions, validation, and execution

import uuid
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json
from sqlmodel import Session, select
from fuzzywuzzy import fuzz

from app.models.data_mapping import (
    WidgetDataMapping, StudyDataConfiguration, FieldMappingTemplate,
    MappingType, DataType, FieldMappingRequest, MappingValidationResult,
    MappingSuggestion
)
from app.models import Study, WidgetDefinition, DataSourceUpload
from app.clinical_modules.utils.folder_structure import get_study_data_path
import logging

logger = logging.getLogger(__name__)

class MappingService:
    """Service for managing data mappings"""
    
    def __init__(self, db: Session):
        self.db = db
        self.common_field_patterns = {
            'subject_id': ['subject', 'patient', 'participant', 'subjid', 'usubjid', 'pid'],
            'visit': ['visit', 'visitnum', 'visitname', 'timepoint', 'week'],
            'date': ['date', 'dt', 'visitdat', 'collection_date'],
            'value': ['value', 'result', 'aval', 'stresn', 'score'],
            'unit': ['unit', 'units', 'stresu'],
            'category': ['category', 'cat', 'type', 'test', 'param'],
            'sex': ['sex', 'gender'],
            'age': ['age', 'age_years'],
            'race': ['race', 'ethnicity'],
            'treatment': ['treatment', 'arm', 'trt', 'cohort', 'group'],
        }
    
    def initialize_study_data(self, study_id: uuid.UUID, upload_ids: List[uuid.UUID], 
                            auto_detect: bool = True) -> StudyDataConfiguration:
        """Initialize study data configuration by analyzing uploaded datasets"""
        study = self.db.get(Study, study_id)
        if not study:
            raise ValueError("Study not found")
        
        # Get uploads
        uploads = self.db.exec(
            select(DataSourceUpload)
            .where(DataSourceUpload.id.in_(upload_ids))
            .where(DataSourceUpload.study_id == study_id)
        ).all()
        
        if not uploads:
            raise ValueError("No valid uploads found")
        
        # Analyze datasets
        dataset_schemas = {}
        for upload in uploads:
            if upload.files_extracted:
                for file_info in upload.files_extracted:
                    dataset_name = file_info['dataset_name']
                    
                    # Load sample data
                    data_path = get_study_data_path(study.org_id, study.id, upload.folder_timestamp)
                    parquet_file = data_path / file_info['parquet_path'].split('/')[-1]
                    
                    if parquet_file.exists():
                        # Read schema
                        df = pd.read_parquet(parquet_file, engine='pyarrow')
                        
                        schema = {
                            'columns': {},
                            'row_count': len(df),
                            'last_updated': upload.upload_timestamp.isoformat(),
                            'upload_id': str(upload.id)
                        }
                        
                        # Analyze columns
                        for col in df.columns:
                            col_info = {
                                'type': self._infer_data_type(df[col]),
                                'nullable': df[col].isnull().any(),
                                'unique_count': df[col].nunique(),
                                'sample_values': df[col].dropna().head(5).tolist()
                            }
                            
                            # Add statistics for numeric columns
                            if col_info['type'] == 'number':
                                col_info['stats'] = {
                                    'min': float(df[col].min()),
                                    'max': float(df[col].max()),
                                    'mean': float(df[col].mean()),
                                    'std': float(df[col].std())
                                }
                            
                            schema['columns'][col] = col_info
                        
                        dataset_schemas[dataset_name] = schema
        
        # Create or update study data configuration
        config = self.db.exec(
            select(StudyDataConfiguration)
            .where(StudyDataConfiguration.study_id == study_id)
        ).first()
        
        if not config:
            config = StudyDataConfiguration(
                study_id=study_id,
                created_by=study.created_by
            )
        
        config.dataset_schemas = dataset_schemas
        config.is_initialized = True
        config.initialization_completed_at = datetime.utcnow()
        config.updated_at = datetime.utcnow()
        
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        
        return config
    
    def suggest_mappings(self, study_id: uuid.UUID, widget_id: uuid.UUID) -> List[MappingSuggestion]:
        """Suggest field mappings for a widget based on data schema"""
        # Get widget and its required fields
        widget = self.db.get(WidgetDefinition, widget_id)
        if not widget:
            raise ValueError("Widget not found")
        
        # Get study data configuration
        config = self.db.exec(
            select(StudyDataConfiguration)
            .where(StudyDataConfiguration.study_id == study_id)
        ).first()
        
        if not config or not config.dataset_schemas:
            raise ValueError("Study data not initialized")
        
        suggestions = []
        
        # Get required fields from widget data contract
        if widget.data_contract and 'required_fields' in widget.data_contract:
            required_fields = widget.data_contract['required_fields']
            
            for field_name, field_config in required_fields.items():
                # Find best matching column across all datasets
                best_match = self._find_best_field_match(
                    field_name,
                    field_config,
                    config.dataset_schemas
                )
                
                if best_match:
                    suggestions.append(best_match)
        
        return suggestions
    
    def _find_best_field_match(self, target_field: str, field_config: Dict[str, Any],
                             dataset_schemas: Dict[str, Any]) -> Optional[MappingSuggestion]:
        """Find the best matching field in available datasets"""
        best_match = None
        best_score = 0
        
        # Check common patterns
        patterns = self.common_field_patterns.get(target_field, [target_field])
        
        for dataset_name, schema in dataset_schemas.items():
            for col_name, col_info in schema['columns'].items():
                # Calculate match score
                score = 0
                reason_parts = []
                
                # Name similarity
                name_score = max([fuzz.ratio(col_name.lower(), pattern.lower()) 
                                for pattern in patterns])
                if name_score > 70:
                    score += name_score / 100
                    reason_parts.append(f"name similarity: {name_score}%")
                
                # Data type compatibility
                expected_type = field_config.get('data_type', 'string')
                if self._are_types_compatible(col_info['type'], expected_type):
                    score += 0.3
                    reason_parts.append("compatible data type")
                    data_type_match = True
                else:
                    data_type_match = False
                
                # Value range compatibility for numeric fields
                if expected_type == 'number' and 'stats' in col_info:
                    if 'min_value' in field_config and col_info['stats']['min'] >= field_config['min_value']:
                        score += 0.1
                    if 'max_value' in field_config and col_info['stats']['max'] <= field_config['max_value']:
                        score += 0.1
                
                # Pattern matching for categorical fields
                if 'allowed_values' in field_config and col_info['sample_values']:
                    overlap = set(field_config['allowed_values']) & set(col_info['sample_values'])
                    if overlap:
                        score += 0.2
                        reason_parts.append(f"matching values: {list(overlap)[:3]}")
                
                if score > best_score:
                    best_score = score
                    best_match = MappingSuggestion(
                        field_name=target_field,
                        suggested_source_field=f"{dataset_name}.{col_name}",
                        confidence=min(score, 1.0),
                        reason="; ".join(reason_parts),
                        data_type_match=data_type_match,
                        sample_values=col_info['sample_values'][:5]
                    )
        
        return best_match if best_score > 0.3 else None
    
    def _infer_data_type(self, series: pd.Series) -> str:
        """Infer data type from pandas series"""
        # Remove nulls for type checking
        non_null = series.dropna()
        
        if len(non_null) == 0:
            return 'string'
        
        # Check for boolean
        if series.dtype == bool or set(non_null.unique()) <= {True, False, 1, 0, '1', '0', 'true', 'false'}:
            return 'boolean'
        
        # Check for dates
        if pd.api.types.is_datetime64_any_dtype(series):
            return 'datetime'
        
        try:
            pd.to_datetime(non_null.astype(str), errors='raise')
            return 'date'
        except:
            pass
        
        # Check for numeric
        if pd.api.types.is_numeric_dtype(series):
            return 'number'
        
        try:
            pd.to_numeric(non_null, errors='raise')
            return 'number'
        except:
            pass
        
        # Default to string
        return 'string'
    
    def _are_types_compatible(self, source_type: str, target_type: str) -> bool:
        """Check if source and target data types are compatible"""
        if source_type == target_type:
            return True
        
        # Allow some conversions
        compatible = {
            'number': ['string'],
            'date': ['datetime', 'string'],
            'datetime': ['date', 'string'],
            'boolean': ['number', 'string'],
        }
        
        return target_type in compatible.get(source_type, [])
    
    def validate_mapping(self, mapping: WidgetDataMapping, sample_size: int = 100) -> MappingValidationResult:
        """Validate a data mapping configuration"""
        errors = []
        warnings = []
        coverage = {}
        sample_data = []
        
        try:
            # Get study data configuration
            config = self.db.exec(
                select(StudyDataConfiguration)
                .where(StudyDataConfiguration.study_id == mapping.study_id)
            ).first()
            
            if not config:
                errors.append("Study data configuration not found")
                return MappingValidationResult(is_valid=False, errors=errors)
            
            # Load source data
            dataset_name = mapping.data_source_config.get('dataset_name')
            if not dataset_name:
                errors.append("No dataset specified in data source configuration")
                return MappingValidationResult(is_valid=False, errors=errors)
            
            # Get dataset info
            if dataset_name not in config.dataset_schemas:
                errors.append(f"Dataset '{dataset_name}' not found")
                return MappingValidationResult(is_valid=False, errors=errors)
            
            schema = config.dataset_schemas[dataset_name]
            
            # Load actual data for validation
            study = self.db.get(Study, mapping.study_id)
            upload_id = schema.get('upload_id')
            if upload_id:
                upload = self.db.get(DataSourceUpload, uuid.UUID(upload_id))
                if upload:
                    data_path = get_study_data_path(study.org_id, study.id, upload.folder_timestamp)
                    
                    # Find parquet file
                    for file_info in upload.files_extracted or []:
                        if file_info['dataset_name'] == dataset_name:
                            parquet_file = data_path / file_info['parquet_path'].split('/')[-1]
                            if parquet_file.exists():
                                df = pd.read_parquet(parquet_file, nrows=sample_size)
                                
                                # Validate each field mapping
                                for field_name, mapping_config in mapping.field_mappings.items():
                                    try:
                                        # Check if source field exists
                                        if mapping_config['type'] == MappingType.DIRECT:
                                            source_field = mapping_config.get('source_field')
                                            if source_field not in df.columns:
                                                errors.append(f"Source field '{source_field}' not found for '{field_name}'")
                                            else:
                                                # Calculate coverage
                                                non_null_count = df[source_field].notna().sum()
                                                coverage[field_name] = non_null_count / len(df)
                                                
                                                if coverage[field_name] < 0.5:
                                                    warnings.append(f"Low data coverage for '{field_name}': {coverage[field_name]:.1%}")
                                        
                                        elif mapping_config['type'] == MappingType.CALCULATED:
                                            # Validate expression
                                            expression = mapping_config.get('expression')
                                            if not expression:
                                                errors.append(f"No expression provided for calculated field '{field_name}'")
                                        
                                    except Exception as e:
                                        errors.append(f"Error validating field '{field_name}': {str(e)}")
                                
                                # Generate sample data
                                sample_records = []
                                for _, row in df.head(5).iterrows():
                                    record = {}
                                    for field_name, mapping_config in mapping.field_mappings.items():
                                        try:
                                            if mapping_config['type'] == MappingType.DIRECT:
                                                record[field_name] = row.get(mapping_config['source_field'])
                                            elif mapping_config['type'] == MappingType.CONSTANT:
                                                record[field_name] = mapping_config['constant_value']
                                        except:
                                            record[field_name] = None
                                    sample_records.append(record)
                                
                                sample_data = sample_records
                                
                            break
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return MappingValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sample_data=sample_data,
            coverage=coverage
        )
    
    def create_mapping_template(self, name: str, description: str, category: str,
                              field_mappings: Dict[str, Any], org_id: uuid.UUID,
                              user_id: uuid.UUID) -> FieldMappingTemplate:
        """Create a reusable mapping template"""
        template = FieldMappingTemplate(
            org_id=org_id,
            name=name,
            description=description,
            category=category,
            field_mappings=field_mappings,
            created_by=user_id
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        return template
    
    def apply_template(self, template_id: uuid.UUID, widget_id: uuid.UUID, 
                      study_id: uuid.UUID, user_id: uuid.UUID) -> WidgetDataMapping:
        """Apply a mapping template to a widget"""
        template = self.db.get(FieldMappingTemplate, template_id)
        if not template:
            raise ValueError("Template not found")
        
        # Create mapping from template
        mapping = WidgetDataMapping(
            study_id=study_id,
            widget_id=widget_id,
            field_mappings=template.field_mappings,
            created_by=user_id
        )
        
        # Update template usage
        template.usage_count += 1
        template.last_used_at = datetime.utcnow()
        
        self.db.add(mapping)
        self.db.add(template)
        self.db.commit()
        self.db.refresh(mapping)
        
        return mapping