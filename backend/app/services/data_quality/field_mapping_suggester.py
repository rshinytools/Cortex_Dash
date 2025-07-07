# ABOUTME: Field mapping suggester service for suggesting field mappings based on data patterns
# ABOUTME: Uses fuzzy matching and semantic analysis to suggest CDISC mappings

from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from difflib import SequenceMatcher
import re
import logging
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class FieldMappingSuggester:
    """Service for suggesting field mappings based on data patterns and CDISC standards."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.cdisc_mappings = self._load_cdisc_mappings()
        self.common_patterns = self._load_common_patterns()
        
    def suggest_field_mappings(
        self,
        study_id: str,
        dataset_name: str,
        source_fields: List[str],
        sample_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Suggest field mappings for a dataset.
        
        Args:
            study_id: Study identifier
            dataset_name: Target dataset name (e.g., 'ADSL', 'ADAE')
            source_fields: List of source field names
            sample_data: Optional sample data for analysis
            
        Returns:
            Dictionary containing mapping suggestions
        """
        try:
            suggestions = {
                'automaticMappings': [],
                'suggestedMappings': [],
                'unmappedFields': [],
                'confidence': {},
                'warnings': [],
                'statistics': {
                    'totalFields': len(source_fields),
                    'automapped': 0,
                    'suggested': 0,
                    'unmapped': 0
                }
            }
            
            target_fields = self._get_target_fields(dataset_name)
            
            for source_field in source_fields:
                mapping_result = self._suggest_field_mapping(
                    source_field,
                    target_fields,
                    dataset_name,
                    sample_data
                )
                
                confidence = mapping_result['confidence']
                
                if confidence >= 0.9:
                    # High confidence - automatic mapping
                    suggestions['automaticMappings'].append({
                        'sourceField': source_field,
                        'targetField': mapping_result['targetField'],
                        'confidence': confidence,
                        'reason': mapping_result['reason'],
                        'dataType': mapping_result.get('dataType', 'unknown')
                    })
                    suggestions['statistics']['automapped'] += 1
                    
                elif confidence >= 0.5:
                    # Medium confidence - suggested mapping
                    suggestions['suggestedMappings'].append({
                        'sourceField': source_field,
                        'targetField': mapping_result['targetField'],
                        'confidence': confidence,
                        'reason': mapping_result['reason'],
                        'alternatives': mapping_result.get('alternatives', []),
                        'dataType': mapping_result.get('dataType', 'unknown')
                    })
                    suggestions['statistics']['suggested'] += 1
                    
                else:
                    # Low confidence - unmapped
                    suggestions['unmappedFields'].append({
                        'sourceField': source_field,
                        'reason': 'No suitable mapping found',
                        'suggestions': mapping_result.get('alternatives', [])[:3]
                    })
                    suggestions['statistics']['unmapped'] += 1
                
                suggestions['confidence'][source_field] = confidence
            
            # Add warnings for missing required fields
            suggestions['warnings'] = self._check_required_fields(
                dataset_name,
                [m['targetField'] for m in suggestions['automaticMappings']] +
                [m['targetField'] for m in suggestions['suggestedMappings']]
            )
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting field mappings: {str(e)}")
            return self._empty_mapping_result(source_fields)
    
    def validate_field_mapping(
        self,
        source_field: str,
        target_field: str,
        dataset_name: str,
        sample_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Validate a specific field mapping.
        
        Args:
            source_field: Source field name
            target_field: Target field name
            dataset_name: Target dataset name
            sample_data: Optional sample data for validation
            
        Returns:
            Validation result with warnings and suggestions
        """
        try:
            validation = {
                'isValid': True,
                'warnings': [],
                'errors': [],
                'suggestions': [],
                'confidence': 0.0
            }
            
            # Check if target field exists in CDISC standards
            target_fields = self._get_target_fields(dataset_name)
            if target_field not in target_fields:
                validation['errors'].append(f"Target field '{target_field}' not found in {dataset_name} standard")
                validation['isValid'] = False
                return validation
            
            # Analyze field compatibility
            field_info = target_fields[target_field]
            
            if sample_data is not None and source_field in sample_data.columns:
                data_validation = self._validate_data_compatibility(
                    sample_data[source_field],
                    field_info
                )
                validation.update(data_validation)
            
            # Calculate confidence based on name similarity and data compatibility
            name_similarity = self._calculate_similarity(source_field, target_field)
            validation['confidence'] = name_similarity
            
            if validation['confidence'] < 0.3:
                validation['warnings'].append(
                    f"Low name similarity between '{source_field}' and '{target_field}'"
                )
            
            return validation
            
        except Exception as e:
            logger.error(f"Error validating field mapping: {str(e)}")
            return {
                'isValid': False,
                'errors': [str(e)],
                'warnings': [],
                'suggestions': [],
                'confidence': 0.0
            }
    
    def suggest_derived_fields(
        self,
        dataset_name: str,
        available_fields: List[str],
        sample_data: Optional[pd.DataFrame] = None
    ) -> List[Dict[str, Any]]:
        """
        Suggest derived fields that can be calculated from available fields.
        
        Args:
            dataset_name: Target dataset name
            available_fields: List of available source fields
            sample_data: Optional sample data for analysis
            
        Returns:
            List of derived field suggestions
        """
        try:
            derived_suggestions = []
            
            # Age derivation
            if 'BIRTHDT' in available_fields and 'RANDDT' in available_fields:
                derived_suggestions.append({
                    'derivedField': 'AGE',
                    'sourceFields': ['BIRTHDT', 'RANDDT'],
                    'formula': '(RANDDT - BIRTHDT) / 365.25',
                    'description': 'Age at randomization in years',
                    'confidence': 0.95
                })
            
            # Visit day derivation
            if 'VISITDT' in available_fields and 'RANDDT' in available_fields:
                derived_suggestions.append({
                    'derivedField': 'ADY',
                    'sourceFields': ['VISITDT', 'RANDDT'],
                    'formula': 'VISITDT - RANDDT + 1',
                    'description': 'Analysis day relative to randomization',
                    'confidence': 0.90
                })
            
            # Change from baseline
            if sample_data is not None:
                baseline_candidates = [f for f in available_fields if 'BASELINE' in f.upper() or 'BL' in f.upper()]
                value_candidates = [f for f in available_fields if any(x in f.upper() for x in ['VAL', 'RESULT', 'STRESN'])]
                
                for baseline_field in baseline_candidates:
                    for value_field in value_candidates:
                        if self._fields_are_compatible(baseline_field, value_field):
                            derived_suggestions.append({
                                'derivedField': f"CHG_{value_field}",
                                'sourceFields': [value_field, baseline_field],
                                'formula': f"{value_field} - {baseline_field}",
                                'description': f"Change from baseline for {value_field}",
                                'confidence': 0.80
                            })
            
            # Treatment emergent flag
            if 'AESTDT' in available_fields and 'TRTSTDT' in available_fields:
                derived_suggestions.append({
                    'derivedField': 'TRTEMFL',
                    'sourceFields': ['AESTDT', 'TRTSTDT'],
                    'formula': 'Y if AESTDT >= TRTSTDT else N',
                    'description': 'Treatment emergent flag',
                    'confidence': 0.90
                })
            
            return derived_suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting derived fields: {str(e)}")
            return []
    
    def _suggest_field_mapping(
        self,
        source_field: str,
        target_fields: Dict[str, Any],
        dataset_name: str,
        sample_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """Suggest mapping for a single field."""
        best_match = None
        best_confidence = 0.0
        alternatives = []
        
        # Clean field name for comparison
        clean_source = self._clean_field_name(source_field)
        
        for target_field, field_info in target_fields.items():
            confidence = self._calculate_mapping_confidence(
                source_field,
                target_field,
                field_info,
                sample_data
            )
            
            if confidence > best_confidence:
                if best_match:
                    alternatives.append({
                        'field': best_match,
                        'confidence': best_confidence
                    })
                best_match = target_field
                best_confidence = confidence
            elif confidence > 0.3:
                alternatives.append({
                    'field': target_field,
                    'confidence': confidence
                })
        
        # Sort alternatives by confidence
        alternatives.sort(key=lambda x: x['confidence'], reverse=True)
        
        reason = self._generate_mapping_reason(source_field, best_match, best_confidence)
        
        return {
            'targetField': best_match or 'UNMAPPED',
            'confidence': best_confidence,
            'reason': reason,
            'alternatives': alternatives[:5],  # Top 5 alternatives
            'dataType': self._infer_data_type(source_field, sample_data)
        }
    
    def _calculate_mapping_confidence(
        self,
        source_field: str,
        target_field: str,
        field_info: Dict[str, Any],
        sample_data: Optional[pd.DataFrame] = None
    ) -> float:
        """Calculate confidence score for a field mapping."""
        confidence = 0.0
        
        # Name similarity (40% weight)
        name_sim = self._calculate_similarity(source_field, target_field)
        confidence += name_sim * 0.4
        
        # Pattern matching (30% weight)
        pattern_score = self._check_pattern_match(source_field, target_field)
        confidence += pattern_score * 0.3
        
        # Data type compatibility (20% weight)
        if sample_data is not None and source_field in sample_data.columns:
            data_compat = self._check_data_compatibility(
                sample_data[source_field],
                field_info
            )
            confidence += data_compat * 0.2
        
        # CDISC standard match (10% weight)
        cdisc_score = self._check_cdisc_match(source_field, target_field)
        confidence += cdisc_score * 0.1
        
        return min(1.0, confidence)
    
    def _calculate_similarity(self, field1: str, field2: str) -> float:
        """Calculate similarity between two field names."""
        # Exact match
        if field1.upper() == field2.upper():
            return 1.0
        
        # Clean field names
        clean1 = self._clean_field_name(field1)
        clean2 = self._clean_field_name(field2)
        
        if clean1 == clean2:
            return 0.95
        
        # Sequence matcher
        seq_sim = SequenceMatcher(None, clean1.lower(), clean2.lower()).ratio()
        
        # Check for common abbreviations
        abbrev_sim = self._check_abbreviation_match(clean1, clean2)
        
        return max(seq_sim, abbrev_sim)
    
    def _clean_field_name(self, field_name: str) -> str:
        """Clean field name for comparison."""
        # Remove common prefixes/suffixes
        cleaned = field_name.upper()
        cleaned = re.sub(r'^(DM|LB|VS|AE|CM|EX|SV)_?', '', cleaned)
        cleaned = re.sub(r'_?(DT|DAT|DATE|NUM|CD|TXT|FL|N)$', '', cleaned)
        cleaned = re.sub(r'[_\-\.]', '', cleaned)
        return cleaned
    
    def _check_pattern_match(self, source_field: str, target_field: str) -> float:
        """Check if fields match common patterns."""
        patterns = self.common_patterns.get(target_field, [])
        
        for pattern in patterns:
            if re.search(pattern, source_field, re.IGNORECASE):
                return 0.8
        
        return 0.0
    
    def _check_data_compatibility(
        self,
        source_data: pd.Series,
        field_info: Dict[str, Any]
    ) -> float:
        """Check data type compatibility."""
        if source_data.empty:
            return 0.5
        
        expected_type = field_info.get('type', 'string')
        
        # Check numeric compatibility
        if expected_type in ['number', 'integer']:
            try:
                pd.to_numeric(source_data.dropna())
                return 0.9
            except (ValueError, TypeError):
                return 0.1
        
        # Check date compatibility
        if expected_type == 'date':
            try:
                pd.to_datetime(source_data.dropna())
                return 0.9
            except (ValueError, TypeError):
                return 0.1
        
        # String fields are generally compatible
        return 0.7
    
    def _check_cdisc_match(self, source_field: str, target_field: str) -> float:
        """Check if mapping follows CDISC conventions."""
        cdisc_mappings = self.cdisc_mappings.get(target_field, [])
        
        for mapping in cdisc_mappings:
            if source_field.upper() in mapping.upper():
                return 0.9
        
        return 0.0
    
    def _check_abbreviation_match(self, field1: str, field2: str) -> float:
        """Check for common abbreviations."""
        abbreviations = {
            'SUBJ': 'SUBJECT',
            'PT': 'PATIENT',
            'DT': 'DATE',
            'NUM': 'NUMBER',
            'ID': 'IDENTIFIER',
            'CD': 'CODE',
            'TXT': 'TEXT',
            'FL': 'FLAG',
            'USUBJID': 'UNIQUE_SUBJECT_IDENTIFIER',
            'STUDYID': 'STUDY_IDENTIFIER',
            'SITEID': 'SITE_IDENTIFIER'
        }
        
        for abbrev, full in abbreviations.items():
            if (abbrev in field1.upper() and full in field2.upper()) or \
               (full in field1.upper() and abbrev in field2.upper()):
                return 0.8
        
        return 0.0
    
    def _generate_mapping_reason(
        self,
        source_field: str,
        target_field: Optional[str],
        confidence: float
    ) -> str:
        """Generate human-readable reason for mapping."""
        if not target_field or target_field == 'UNMAPPED':
            return "No suitable mapping found"
        
        if confidence >= 0.9:
            return f"Exact or near-exact match with {target_field}"
        elif confidence >= 0.7:
            return f"Strong similarity to {target_field}"
        elif confidence >= 0.5:
            return f"Moderate similarity to {target_field}"
        else:
            return f"Weak similarity to {target_field}"
    
    def _infer_data_type(
        self,
        field_name: str,
        sample_data: Optional[pd.DataFrame] = None
    ) -> str:
        """Infer data type from field name and sample data."""
        field_upper = field_name.upper()
        
        # Date fields
        if any(x in field_upper for x in ['DT', 'DATE', 'DATIM']):
            return 'date'
        
        # Numeric fields
        if any(x in field_upper for x in ['NUM', 'STRESN', 'AGE', 'COUNT', 'SCORE']):
            return 'number'
        
        # Flag fields
        if field_upper.endswith('FL') or 'FLAG' in field_upper:
            return 'flag'
        
        # Check sample data if available
        if sample_data is not None and field_name in sample_data.columns:
            dtype = sample_data[field_name].dtype
            if dtype in ['int64', 'float64']:
                return 'number'
            elif dtype == 'bool':
                return 'flag'
            elif 'datetime' in str(dtype):
                return 'date'
        
        return 'string'
    
    def _validate_data_compatibility(
        self,
        source_data: pd.Series,
        field_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate data compatibility for a mapping."""
        result = {
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        expected_type = field_info.get('type', 'string')
        
        # Check data type
        if expected_type == 'number':
            non_numeric = source_data.apply(lambda x: not pd.api.types.is_numeric_dtype(type(x))).sum()
            if non_numeric > 0:
                result['warnings'].append(f"{non_numeric} non-numeric values found")
        
        # Check required values
        if field_info.get('required', False):
            null_count = source_data.isna().sum()
            if null_count > 0:
                result['errors'].append(f"{null_count} null values in required field")
        
        # Check value constraints
        constraints = field_info.get('constraints', {})
        if 'enum' in constraints:
            invalid_values = ~source_data.isin(constraints['enum'])
            if invalid_values.any():
                result['warnings'].append(f"Values not in allowed set: {constraints['enum']}")
        
        return result
    
    def _get_target_fields(self, dataset_name: str) -> Dict[str, Any]:
        """Get target fields for a dataset."""
        # This would normally load from a CDISC standards database
        # For now, return sample field definitions
        
        common_fields = {
            'USUBJID': {'type': 'string', 'required': True, 'description': 'Unique Subject Identifier'},
            'STUDYID': {'type': 'string', 'required': True, 'description': 'Study Identifier'},
            'SITEID': {'type': 'string', 'required': False, 'description': 'Site Identifier'},
            'SUBJID': {'type': 'string', 'required': False, 'description': 'Subject Identifier'},
        }
        
        dataset_fields = {
            'ADSL': {
                **common_fields,
                'AGE': {'type': 'number', 'required': False, 'description': 'Age'},
                'SEX': {'type': 'string', 'required': False, 'description': 'Sex', 'constraints': {'enum': ['M', 'F']}},
                'RACE': {'type': 'string', 'required': False, 'description': 'Race'},
                'ARM': {'type': 'string', 'required': False, 'description': 'Treatment Arm'},
                'ACTARM': {'type': 'string', 'required': False, 'description': 'Actual Treatment Arm'},
                'RFSTDTC': {'type': 'date', 'required': False, 'description': 'Subject Reference Start Date'},
                'RFENDTC': {'type': 'date', 'required': False, 'description': 'Subject Reference End Date'},
            },
            'ADAE': {
                **common_fields,
                'AETERM': {'type': 'string', 'required': True, 'description': 'Adverse Event Term'},
                'AEDECOD': {'type': 'string', 'required': True, 'description': 'Adverse Event Decoded Term'},
                'AESTDTC': {'type': 'date', 'required': False, 'description': 'AE Start Date'},
                'AEENDTC': {'type': 'date', 'required': False, 'description': 'AE End Date'},
                'AESEV': {'type': 'string', 'required': False, 'description': 'Severity', 'constraints': {'enum': ['MILD', 'MODERATE', 'SEVERE']}},
                'AESER': {'type': 'string', 'required': False, 'description': 'Serious Event', 'constraints': {'enum': ['Y', 'N']}},
            },
            'ADLB': {
                **common_fields,
                'PARAM': {'type': 'string', 'required': True, 'description': 'Parameter'},
                'PARAMCD': {'type': 'string', 'required': True, 'description': 'Parameter Code'},
                'AVAL': {'type': 'number', 'required': False, 'description': 'Analysis Value'},
                'BASE': {'type': 'number', 'required': False, 'description': 'Baseline Value'},
                'CHG': {'type': 'number', 'required': False, 'description': 'Change from Baseline'},
                'PCHG': {'type': 'number', 'required': False, 'description': 'Percent Change from Baseline'},
                'ADT': {'type': 'date', 'required': False, 'description': 'Analysis Date'},
                'VISIT': {'type': 'string', 'required': False, 'description': 'Visit Name'},
                'VISITNUM': {'type': 'number', 'required': False, 'description': 'Visit Number'},
            }
        }
        
        return dataset_fields.get(dataset_name, common_fields)
    
    def _check_required_fields(self, dataset_name: str, mapped_fields: List[str]) -> List[str]:
        """Check for missing required fields."""
        target_fields = self._get_target_fields(dataset_name)
        required_fields = [
            field for field, info in target_fields.items()
            if info.get('required', False)
        ]
        
        missing_required = [
            field for field in required_fields
            if field not in mapped_fields
        ]
        
        warnings = []
        for field in missing_required:
            warnings.append(f"Required field '{field}' not mapped")
        
        return warnings
    
    def _fields_are_compatible(self, field1: str, field2: str) -> bool:
        """Check if two fields are likely to be compatible for derivation."""
        # Remove common suffixes to find base field names
        base1 = re.sub(r'(BL|BASELINE|_BASE|_BL)$', '', field1.upper())
        base2 = re.sub(r'(BL|BASELINE|_BASE|_BL)$', '', field2.upper())
        
        return base1 == base2
    
    def _load_cdisc_mappings(self) -> Dict[str, List[str]]:
        """Load CDISC field mappings."""
        # This would normally load from a database or configuration file
        return {
            'USUBJID': ['SUBJECT_ID', 'SUBJ_ID', 'PATIENT_ID', 'PTID'],
            'STUDYID': ['STUDY_ID', 'STUDY', 'PROTOCOL'],
            'SITEID': ['SITE_ID', 'CENTER_ID', 'INVESTIGATOR_ID'],
            'AGE': ['AGE', 'AGE_YRS', 'SUBJ_AGE'],
            'SEX': ['SEX', 'GENDER'],
            'RACE': ['RACE', 'ETHNICITY'],
            'AETERM': ['AE_TERM', 'ADVERSE_EVENT', 'AE_TEXT'],
            'AEDECOD': ['AE_PREFERRED_TERM', 'AE_PT', 'MEDDRA_PT'],
            'AESTDTC': ['AE_START_DATE', 'AE_ONSET_DATE', 'AESTDT'],
            'PARAM': ['PARAMETER', 'TEST_NAME', 'LAB_TEST'],
            'AVAL': ['RESULT', 'VALUE', 'NUMERIC_RESULT', 'STRESN'],
        }
    
    def _load_common_patterns(self) -> Dict[str, List[str]]:
        """Load common field name patterns."""
        return {
            'USUBJID': [r'subj.*id', r'patient.*id', r'pt.*id'],
            'STUDYID': [r'study.*id', r'protocol'],
            'SITEID': [r'site.*id', r'center.*id', r'inv.*id'],
            'AGE': [r'age', r'.*age.*'],
            'SEX': [r'sex', r'gender'],
            'RACE': [r'race', r'ethnic'],
            'VISITNUM': [r'visit.*num', r'vis.*num', r'vnum'],
            'VISITDT': [r'visit.*dt', r'visit.*date', r'vdt'],
            'AETERM': [r'ae.*term', r'adverse.*event', r'ae.*text'],
            'AESTDTC': [r'ae.*start', r'ae.*onset', r'ae.*dt'],
            'PARAM': [r'param', r'test.*name', r'lab.*test'],
            'AVAL': [r'result', r'value', r'numeric', r'stresn'],
        }
    
    def _empty_mapping_result(self, source_fields: List[str]) -> Dict[str, Any]:
        """Return empty mapping result."""
        return {
            'automaticMappings': [],
            'suggestedMappings': [],
            'unmappedFields': [{'sourceField': f, 'reason': 'Analysis failed'} for f in source_fields],
            'confidence': {f: 0.0 for f in source_fields},
            'warnings': ['Failed to analyze field mappings'],
            'statistics': {
                'totalFields': len(source_fields),
                'automapped': 0,
                'suggested': 0,
                'unmapped': len(source_fields)
            }
        }


def get_field_mapping_suggester(db: Session = None) -> FieldMappingSuggester:
    """Get field mapping suggester instance."""
    if db is None:
        from app.core.db import get_db
        db = next(get_db())
    return FieldMappingSuggester(db)