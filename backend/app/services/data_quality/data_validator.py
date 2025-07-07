# ABOUTME: Data validator service for validating data against expected formats and ranges
# ABOUTME: Implements CDISC validation rules and custom business logic validation

from typing import Dict, List, Optional, Any, Union, Callable
import pandas as pd
import numpy as np
from datetime import datetime, date
import re
from decimal import Decimal, InvalidOperation
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class ValidationRule:
    """Represents a single validation rule."""
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        severity: str,
        category: str,
        validator: Callable,
        **kwargs
    ):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.severity = severity  # critical, high, medium, low
        self.category = category  # format, range, business, consistency
        self.validator = validator
        self.params = kwargs
    
    def validate(self, value: Any, context: Dict = None) -> Dict[str, Any]:
        """Execute validation rule."""
        try:
            result = self.validator(value, context or {}, **self.params)
            return {
                'rule_id': self.rule_id,
                'passed': result.get('passed', True),
                'message': result.get('message', ''),
                'severity': self.severity,
                'category': self.category
            }
        except Exception as e:
            return {
                'rule_id': self.rule_id,
                'passed': False,
                'message': f"Validation error: {str(e)}",
                'severity': 'critical',
                'category': 'system'
            }


class DataValidator:
    """Service for validating data against business rules and CDISC standards."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.validation_rules = self._load_validation_rules()
        
    def validate_dataset(
        self,
        data: pd.DataFrame,
        dataset_name: str,
        field_mappings: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Validate an entire dataset.
        
        Args:
            data: DataFrame to validate
            dataset_name: Name of the target dataset (e.g., 'ADSL', 'ADAE')
            field_mappings: Optional field mappings
            
        Returns:
            Validation results with errors, warnings, and statistics
        """
        try:
            validation_results = {
                'overall_status': 'passed',
                'total_errors': 0,
                'total_warnings': 0,
                'field_validations': {},
                'record_validations': [],
                'cross_field_validations': [],
                'business_rule_validations': [],
                'statistics': {
                    'total_records': len(data),
                    'total_fields': len(data.columns),
                    'fields_with_errors': 0,
                    'fields_with_warnings': 0,
                    'records_with_errors': 0,
                    'validation_coverage': 0.0
                },
                'validation_timestamp': datetime.utcnow().isoformat()
            }
            
            # Validate individual fields
            for column in data.columns:
                field_result = self._validate_field(
                    data[column],
                    column,
                    dataset_name,
                    field_mappings
                )
                validation_results['field_validations'][column] = field_result
                
                if field_result['errors']:
                    validation_results['statistics']['fields_with_errors'] += 1
                if field_result['warnings']:
                    validation_results['statistics']['fields_with_warnings'] += 1
            
            # Validate cross-field relationships
            cross_field_results = self._validate_cross_field_relationships(
                data,
                dataset_name
            )
            validation_results['cross_field_validations'] = cross_field_results
            
            # Validate business rules
            business_rule_results = self._validate_business_rules(
                data,
                dataset_name
            )
            validation_results['business_rule_validations'] = business_rule_results
            
            # Calculate summary statistics
            validation_results = self._calculate_validation_summary(validation_results)
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating dataset: {str(e)}")
            return self._empty_validation_result(len(data), len(data.columns) if not data.empty else 0)
    
    def validate_field(
        self,
        values: pd.Series,
        field_name: str,
        expected_type: str,
        constraints: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Validate a single field against type and constraints.
        
        Args:
            values: Series of values to validate
            field_name: Name of the field
            expected_type: Expected data type
            constraints: Optional validation constraints
            
        Returns:
            Field validation results
        """
        try:
            result = {
                'field_name': field_name,
                'total_values': len(values),
                'null_count': values.isna().sum(),
                'errors': [],
                'warnings': [],
                'statistics': {}
            }
            
            constraints = constraints or {}
            
            # Type validation
            type_validation = self._validate_data_type(values, expected_type)
            if type_validation['errors']:
                result['errors'].extend(type_validation['errors'])
            if type_validation['warnings']:
                result['warnings'].extend(type_validation['warnings'])
            
            # Constraint validation
            if constraints:
                constraint_validation = self._validate_constraints(values, constraints)
                if constraint_validation['errors']:
                    result['errors'].extend(constraint_validation['errors'])
                if constraint_validation['warnings']:
                    result['warnings'].extend(constraint_validation['warnings'])
            
            # Pattern validation
            pattern_validation = self._validate_patterns(values, field_name)
            if pattern_validation['errors']:
                result['errors'].extend(pattern_validation['errors'])
            if pattern_validation['warnings']:
                result['warnings'].extend(pattern_validation['warnings'])
            
            # Calculate field statistics
            result['statistics'] = self._calculate_field_statistics(values, expected_type)
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating field {field_name}: {str(e)}")
            return {
                'field_name': field_name,
                'total_values': len(values),
                'null_count': values.isna().sum(),
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'statistics': {}
            }
    
    def validate_record(
        self,
        record: Dict[str, Any],
        dataset_name: str,
        record_index: int = 0
    ) -> Dict[str, Any]:
        """
        Validate a single record against business rules.
        
        Args:
            record: Dictionary representing a single record
            dataset_name: Name of the dataset
            record_index: Index of the record for error reporting
            
        Returns:
            Record validation results
        """
        try:
            result = {
                'record_index': record_index,
                'errors': [],
                'warnings': [],
                'rule_violations': []
            }
            
            # Get applicable rules for the dataset
            applicable_rules = self._get_applicable_rules(dataset_name, 'record')
            
            for rule in applicable_rules:
                validation_result = rule.validate(record, {'record_index': record_index})
                
                if not validation_result['passed']:
                    violation = {
                        'rule_id': validation_result['rule_id'],
                        'message': validation_result['message'],
                        'severity': validation_result['severity'],
                        'category': validation_result['category']
                    }
                    
                    result['rule_violations'].append(violation)
                    
                    if validation_result['severity'] in ['critical', 'high']:
                        result['errors'].append(validation_result['message'])
                    else:
                        result['warnings'].append(validation_result['message'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating record {record_index}: {str(e)}")
            return {
                'record_index': record_index,
                'errors': [f"Record validation error: {str(e)}"],
                'warnings': [],
                'rule_violations': []
            }
    
    def _validate_field(
        self,
        values: pd.Series,
        field_name: str,
        dataset_name: str,
        field_mappings: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Validate a field using dataset-specific rules."""
        field_spec = self._get_field_specification(field_name, dataset_name)
        
        return self.validate_field(
            values,
            field_name,
            field_spec.get('type', 'string'),
            field_spec.get('constraints', {})
        )
    
    def _validate_data_type(self, values: pd.Series, expected_type: str) -> Dict[str, Any]:
        """Validate data type compliance."""
        result = {'errors': [], 'warnings': []}
        
        non_null_values = values.dropna()
        if non_null_values.empty:
            return result
        
        if expected_type == 'integer':
            try:
                pd.to_numeric(non_null_values, errors='raise', downcast='integer')
            except (ValueError, TypeError):
                invalid_count = len(non_null_values) - pd.to_numeric(non_null_values, errors='coerce').count()
                result['errors'].append(f"{invalid_count} values are not valid integers")
        
        elif expected_type == 'float':
            try:
                pd.to_numeric(non_null_values, errors='raise')
            except (ValueError, TypeError):
                invalid_count = len(non_null_values) - pd.to_numeric(non_null_values, errors='coerce').count()
                result['errors'].append(f"{invalid_count} values are not valid numbers")
        
        elif expected_type == 'date':
            try:
                pd.to_datetime(non_null_values, errors='raise')
            except (ValueError, TypeError):
                invalid_count = len(non_null_values) - pd.to_datetime(non_null_values, errors='coerce').count()
                result['errors'].append(f"{invalid_count} values are not valid dates")
        
        elif expected_type == 'string':
            # Check for unexpected numeric values in string fields
            numeric_values = pd.to_numeric(non_null_values, errors='coerce').count()
            if numeric_values > len(non_null_values) * 0.8:
                result['warnings'].append("Field appears to contain mostly numeric values but is expected to be string")
        
        return result
    
    def _validate_constraints(self, values: pd.Series, constraints: Dict) -> Dict[str, Any]:
        """Validate field constraints."""
        result = {'errors': [], 'warnings': []}
        
        non_null_values = values.dropna()
        
        # Enum validation
        if 'enum' in constraints:
            invalid_values = ~non_null_values.isin(constraints['enum'])
            if invalid_values.any():
                invalid_count = invalid_values.sum()
                result['errors'].append(
                    f"{invalid_count} values not in allowed set: {constraints['enum']}"
                )
        
        # Range validation for numeric fields
        if 'min' in constraints:
            try:
                numeric_values = pd.to_numeric(non_null_values, errors='coerce')
                below_min = (numeric_values < constraints['min']).sum()
                if below_min > 0:
                    result['errors'].append(f"{below_min} values below minimum: {constraints['min']}")
            except:
                pass
        
        if 'max' in constraints:
            try:
                numeric_values = pd.to_numeric(non_null_values, errors='coerce')
                above_max = (numeric_values > constraints['max']).sum()
                if above_max > 0:
                    result['errors'].append(f"{above_max} values above maximum: {constraints['max']}")
            except:
                pass
        
        # Length validation for string fields
        if 'max_length' in constraints:
            too_long = non_null_values.astype(str).str.len() > constraints['max_length']
            if too_long.any():
                result['errors'].append(
                    f"{too_long.sum()} values exceed maximum length: {constraints['max_length']}"
                )
        
        # Pattern validation
        if 'pattern' in constraints:
            pattern_matches = non_null_values.astype(str).str.match(constraints['pattern'])
            if not pattern_matches.all():
                invalid_count = (~pattern_matches).sum()
                result['errors'].append(
                    f"{invalid_count} values don't match pattern: {constraints['pattern']}"
                )
        
        # Required field validation
        if constraints.get('required', False):
            null_count = values.isna().sum()
            if null_count > 0:
                result['errors'].append(f"Required field has {null_count} null values")
        
        return result
    
    def _validate_patterns(self, values: pd.Series, field_name: str) -> Dict[str, Any]:
        """Validate common field patterns."""
        result = {'errors': [], 'warnings': []}
        
        field_upper = field_name.upper()
        non_null_values = values.dropna().astype(str)
        
        # Subject ID pattern
        if 'USUBJID' in field_upper or 'SUBJID' in field_upper:
            # Check for consistent format
            if len(non_null_values) > 0:
                lengths = non_null_values.str.len()
                if lengths.nunique() > 3:  # Allow some variation
                    result['warnings'].append("Subject IDs have inconsistent lengths")
        
        # Site ID pattern
        if 'SITEID' in field_upper:
            # Check for numeric site IDs
            non_numeric = ~non_null_values.str.match(r'^\d+$')
            if non_numeric.any():
                result['warnings'].append(f"{non_numeric.sum()} site IDs are not numeric")
        
        # Date field pattern
        if any(x in field_upper for x in ['DT', 'DATE']):
            # Check for ISO date format
            iso_pattern = r'^\d{4}-\d{2}-\d{2}'
            non_iso = ~non_null_values.str.match(iso_pattern)
            if non_iso.any() and len(non_null_values) > 0:
                result['warnings'].append(f"{non_iso.sum()} dates not in ISO format (YYYY-MM-DD)")
        
        return result
    
    def _validate_cross_field_relationships(
        self,
        data: pd.DataFrame,
        dataset_name: str
    ) -> List[Dict[str, Any]]:
        """Validate relationships between fields."""
        violations = []
        
        # Start date <= End date validation
        date_pairs = [
            ('RFSTDTC', 'RFENDTC'),
            ('AESTDTC', 'AEENDTC'),
            ('CMSTDTC', 'CMENDTC'),
            ('EXSTDTC', 'EXENDTC')
        ]
        
        for start_field, end_field in date_pairs:
            if start_field in data.columns and end_field in data.columns:
                try:
                    start_dates = pd.to_datetime(data[start_field], errors='coerce')
                    end_dates = pd.to_datetime(data[end_field], errors='coerce')
                    
                    # Find records where start > end
                    invalid_records = (start_dates > end_dates) & start_dates.notna() & end_dates.notna()
                    
                    if invalid_records.any():
                        violations.append({
                            'rule_id': f"date_sequence_{start_field}_{end_field}",
                            'description': f"{start_field} should be <= {end_field}",
                            'affected_records': invalid_records.sum(),
                            'severity': 'high',
                            'category': 'consistency'
                        })
                except:
                    pass
        
        # Age consistency validation
        if 'AGE' in data.columns and 'RFSTDTC' in data.columns and 'BRTHDTC' in data.columns:
            try:
                ages = pd.to_numeric(data['AGE'], errors='coerce')
                ref_dates = pd.to_datetime(data['RFSTDTC'], errors='coerce')
                birth_dates = pd.to_datetime(data['BRTHDTC'], errors='coerce')
                
                calculated_ages = ((ref_dates - birth_dates).dt.days / 365.25).round()
                age_diff = abs(ages - calculated_ages)
                
                # Allow 1 year difference
                inconsistent_ages = (age_diff > 1) & ages.notna() & calculated_ages.notna()
                
                if inconsistent_ages.any():
                    violations.append({
                        'rule_id': 'age_consistency',
                        'description': 'Age inconsistent with birth date and reference date',
                        'affected_records': inconsistent_ages.sum(),
                        'severity': 'medium',
                        'category': 'consistency'
                    })
            except:
                pass
        
        return violations
    
    def _validate_business_rules(
        self,
        data: pd.DataFrame,
        dataset_name: str
    ) -> List[Dict[str, Any]]:
        """Validate dataset-specific business rules."""
        violations = []
        
        # ADSL specific rules
        if dataset_name == 'ADSL':
            # Each subject should have only one record
            if 'USUBJID' in data.columns:
                duplicate_subjects = data['USUBJID'].duplicated().sum()
                if duplicate_subjects > 0:
                    violations.append({
                        'rule_id': 'adsl_unique_subjects',
                        'description': 'ADSL should have one record per subject',
                        'affected_records': duplicate_subjects,
                        'severity': 'critical',
                        'category': 'business'
                    })
        
        # ADAE specific rules
        elif dataset_name == 'ADAE':
            # Serious AEs should have severity
            if 'AESER' in data.columns and 'AESEV' in data.columns:
                serious_aes = data['AESER'] == 'Y'
                missing_severity = data['AESEV'].isna()
                serious_without_severity = (serious_aes & missing_severity).sum()
                
                if serious_without_severity > 0:
                    violations.append({
                        'rule_id': 'serious_ae_severity',
                        'description': 'Serious AEs must have severity specified',
                        'affected_records': serious_without_severity,
                        'severity': 'high',
                        'category': 'business'
                    })
        
        # ADLB specific rules
        elif dataset_name == 'ADLB':
            # Analysis value should be present for analysis records
            if 'AVAL' in data.columns and 'ANL01FL' in data.columns:
                analysis_records = data['ANL01FL'] == 'Y'
                missing_aval = data['AVAL'].isna()
                analysis_without_value = (analysis_records & missing_aval).sum()
                
                if analysis_without_value > 0:
                    violations.append({
                        'rule_id': 'analysis_value_required',
                        'description': 'Analysis records must have analysis value',
                        'affected_records': analysis_without_value,
                        'severity': 'high',
                        'category': 'business'
                    })
        
        return violations
    
    def _calculate_field_statistics(self, values: pd.Series, expected_type: str) -> Dict[str, Any]:
        """Calculate field-level statistics."""
        stats = {
            'total_count': len(values),
            'null_count': values.isna().sum(),
            'unique_count': values.nunique(),
            'completeness_rate': ((len(values) - values.isna().sum()) / len(values) * 100) if len(values) > 0 else 0
        }
        
        if expected_type in ['integer', 'float']:
            numeric_values = pd.to_numeric(values, errors='coerce')
            stats.update({
                'min_value': numeric_values.min(),
                'max_value': numeric_values.max(),
                'mean_value': numeric_values.mean(),
                'std_value': numeric_values.std()
            })
        
        elif expected_type == 'string':
            string_values = values.astype(str)
            stats.update({
                'min_length': string_values.str.len().min(),
                'max_length': string_values.str.len().max(),
                'avg_length': string_values.str.len().mean()
            })
        
        return stats
    
    def _calculate_validation_summary(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate validation summary statistics."""
        total_errors = 0
        total_warnings = 0
        
        # Count field validation issues
        for field_result in validation_results['field_validations'].values():
            total_errors += len(field_result['errors'])
            total_warnings += len(field_result['warnings'])
        
        # Count cross-field validation issues
        for violation in validation_results['cross_field_validations']:
            if violation['severity'] in ['critical', 'high']:
                total_errors += 1
            else:
                total_warnings += 1
        
        # Count business rule violations
        for violation in validation_results['business_rule_validations']:
            if violation['severity'] in ['critical', 'high']:
                total_errors += 1
            else:
                total_warnings += 1
        
        validation_results['total_errors'] = total_errors
        validation_results['total_warnings'] = total_warnings
        
        # Determine overall status
        if total_errors > 0:
            validation_results['overall_status'] = 'failed'
        elif total_warnings > 0:
            validation_results['overall_status'] = 'passed_with_warnings'
        else:
            validation_results['overall_status'] = 'passed'
        
        # Calculate validation coverage
        total_fields = validation_results['statistics']['total_fields']
        validated_fields = len(validation_results['field_validations'])
        validation_results['statistics']['validation_coverage'] = (
            (validated_fields / total_fields * 100) if total_fields > 0 else 0
        )
        
        return validation_results
    
    def _get_field_specification(self, field_name: str, dataset_name: str) -> Dict[str, Any]:
        """Get field specification for validation."""
        # This would normally load from a configuration database
        # For now, return sample specifications
        
        specifications = {
            'USUBJID': {'type': 'string', 'constraints': {'required': True, 'max_length': 50}},
            'STUDYID': {'type': 'string', 'constraints': {'required': True, 'max_length': 20}},
            'SITEID': {'type': 'string', 'constraints': {'pattern': r'^\d{3}$'}},
            'AGE': {'type': 'integer', 'constraints': {'min': 0, 'max': 120}},
            'SEX': {'type': 'string', 'constraints': {'enum': ['M', 'F', 'MALE', 'FEMALE']}},
            'AESTDTC': {'type': 'date', 'constraints': {}},
            'AEENDTC': {'type': 'date', 'constraints': {}},
            'AESEV': {'type': 'string', 'constraints': {'enum': ['MILD', 'MODERATE', 'SEVERE']}},
            'AESER': {'type': 'string', 'constraints': {'enum': ['Y', 'N']}},
            'AVAL': {'type': 'float', 'constraints': {}},
            'VISITNUM': {'type': 'integer', 'constraints': {'min': 1}},
        }
        
        return specifications.get(field_name, {'type': 'string', 'constraints': {}})
    
    def _get_applicable_rules(self, dataset_name: str, rule_type: str) -> List[ValidationRule]:
        """Get applicable validation rules for a dataset."""
        return [
            rule for rule in self.validation_rules
            if rule.category == rule_type and 
            (dataset_name in rule.params.get('datasets', [dataset_name]))
        ]
    
    def _load_validation_rules(self) -> List[ValidationRule]:
        """Load validation rules."""
        # This would normally load from a configuration database
        # For now, return sample rules
        return []
    
    def _empty_validation_result(self, record_count: int, field_count: int) -> Dict[str, Any]:
        """Return empty validation result."""
        return {
            'overall_status': 'error',
            'total_errors': 1,
            'total_warnings': 0,
            'field_validations': {},
            'record_validations': [],
            'cross_field_validations': [],
            'business_rule_validations': [],
            'statistics': {
                'total_records': record_count,
                'total_fields': field_count,
                'fields_with_errors': 0,
                'fields_with_warnings': 0,
                'records_with_errors': 0,
                'validation_coverage': 0.0
            },
            'validation_timestamp': datetime.utcnow().isoformat()
        }


def get_data_validator(db: Session = None) -> DataValidator:
    """Get data validator instance."""
    if db is None:
        from app.core.db import get_db
        db = next(get_db())
    return DataValidator(db)