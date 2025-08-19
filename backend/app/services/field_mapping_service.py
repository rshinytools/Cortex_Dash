# ABOUTME: Field mapping service with smart CDISC SDTM/ADaM pattern recognition
# ABOUTME: Automatically maps study data fields to widget requirements using ML-like patterns

import re
import uuid
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable, Set
from sqlmodel import Session
import asyncio
from datetime import datetime
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
from app.models import Study

logger = logging.getLogger(__name__)


class FieldMappingService:
    """Smart field mapping service with CDISC pattern recognition"""
    
    # CDISC SDTM domain patterns
    SDTM_PATTERNS = {
        "DM": {  # Demographics
            "USUBJID": r"(?i)(usubjid|subject.*id|subj.*id)",
            "SUBJID": r"(?i)(subjid|subject.*id)",
            "SITEID": r"(?i)(siteid|site.*id|center.*id)",
            "AGE": r"(?i)(age|^age$)",
            "SEX": r"(?i)(sex|gender)",
            "RACE": r"(?i)(race)",
            "ETHNIC": r"(?i)(ethnic)",
            "COUNTRY": r"(?i)(country)",
            "ARM": r"(?i)(arm|treatment.*group|trt.*grp)",
            "ARMCD": r"(?i)(armcd|arm.*code)"
        },
        "AE": {  # Adverse Events
            "AETERM": r"(?i)(aeterm|adverse.*event|ae.*term)",
            "AEDECOD": r"(?i)(aedecod|ae.*decode|preferred.*term)",
            "AESEV": r"(?i)(aesev|severity|ae.*severity)",
            "AESER": r"(?i)(aeser|serious|ae.*serious)",
            "AESTDTC": r"(?i)(aestdtc|ae.*start.*date)",
            "AEENDTC": r"(?i)(aeendtc|ae.*end.*date)"
        },
        "LB": {  # Laboratory
            "LBTEST": r"(?i)(lbtest|lab.*test|test.*name)",
            "LBTESTCD": r"(?i)(lbtestcd|lab.*test.*code)",
            "LBORRES": r"(?i)(lborres|result|lab.*result|original.*result)",
            "LBORRESU": r"(?i)(lborresu|unit|lab.*unit)",
            "LBSTRESN": r"(?i)(lbstresn|numeric.*result|standard.*result)",
            "LBSTRESU": r"(?i)(lbstresu|standard.*unit)",
            "VISITNUM": r"(?i)(visitnum|visit.*num)",
            "VISIT": r"(?i)(visit|visit.*name)"
        },
        "VS": {  # Vital Signs
            "VSTEST": r"(?i)(vstest|vital.*test|parameter)",
            "VSORRES": r"(?i)(vsorres|result|vital.*result)",
            "VSORRESU": r"(?i)(vsorresu|unit|vital.*unit)",
            "VSSTRESN": r"(?i)(vsstresn|numeric.*result)",
            "VSSTRESU": r"(?i)(vsstresu|standard.*unit)"
        }
    }
    
    # ADaM patterns
    ADAM_PATTERNS = {
        "ADSL": {  # Subject Level Analysis Dataset
            "STUDYID": r"(?i)(studyid|study.*id)",
            "USUBJID": r"(?i)(usubjid|unique.*subject.*id)",
            "TRTSDT": r"(?i)(trtsdt|treatment.*start.*date)",
            "TRTEDT": r"(?i)(trtedt|treatment.*end.*date)",
            "TRTDUR": r"(?i)(trtdur|treatment.*duration)",
            "ITTFL": r"(?i)(ittfl|itt.*flag)",
            "SAFFL": r"(?i)(saffl|safety.*flag)"
        },
        "ADAE": {  # Adverse Events Analysis Dataset
            "AEBODSYS": r"(?i)(aebodsys|body.*system|soc)",
            "AEDECOD": r"(?i)(aedecod|preferred.*term)",
            "TRTEMFL": r"(?i)(trtemfl|treatment.*emergent.*flag)"
        }
    }
    
    # Common metric patterns
    METRIC_PATTERNS = {
        "enrollment": {
            "patterns": [r"(?i)(enrolled|enrollment|randomized)"],
            "aggregation": "count"
        },
        "completion": {
            "patterns": [r"(?i)(completed|completion|discontinued)"],
            "aggregation": "count"
        },
        "safety": {
            "patterns": [r"(?i)(ae|adverse|safety|sae)"],
            "aggregation": "count"
        },
        "efficacy": {
            "patterns": [r"(?i)(efficacy|response|endpoint)"],
            "aggregation": "mean"
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    async def generate_smart_mappings(
        self,
        study_id: uuid.UUID,
        widget_requirements: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        Generate smart field mappings based on widget requirements and available data
        
        Args:
            study_id: The study ID
            widget_requirements: List of widget data requirements
            progress_callback: Optional progress callback
            
        Returns:
            Dictionary of field mappings
        """
        mappings = {
            "study_id": str(study_id),
            "generated_at": datetime.utcnow().isoformat(),
            "widget_mappings": {},
            "global_mappings": {},
            "unmapped_requirements": []
        }
        
        try:
            # Step 1: Analyze available datasets
            if progress_callback:
                await progress_callback(10)
            
            available_fields = await self._analyze_study_datasets(study_id)
            
            # Step 2: Process each widget requirement
            total_widgets = len(widget_requirements)
            for idx, requirement in enumerate(widget_requirements):
                if progress_callback:
                    progress = 10 + int((idx / total_widgets) * 80)
                    await progress_callback(progress)
                
                widget_mapping = await self._map_widget_requirements(
                    requirement,
                    available_fields
                )
                
                if widget_mapping:
                    mappings["widget_mappings"][requirement["widget_id"]] = widget_mapping
                else:
                    mappings["unmapped_requirements"].append(requirement["widget_id"])
            
            # Step 3: Generate global mappings for common fields
            mappings["global_mappings"] = self._generate_global_mappings(available_fields)
            
            if progress_callback:
                await progress_callback(100)
            
            return mappings
            
        except Exception as e:
            logger.error(f"Failed to generate smart mappings: {str(e)}")
            raise
    
    async def _analyze_study_datasets(self, study_id: uuid.UUID) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze available datasets and their fields"""
        available_fields = {}
        
        # Get parquet files directory
        # Get organization ID from study
        study = self.db.get(Study, study_id)
        if not study:
            return {}
        
        timestamp = datetime.now().strftime("%Y-%m-%d")
        parquet_dir = Path(f"/data/{study.org_id}/studies/{study_id}/processed_data/{timestamp}")
        if not parquet_dir.exists():
            logger.warning(f"No parquet data found for study {study_id}")
            return available_fields
        
        # Analyze each parquet file
        for parquet_file in parquet_dir.glob("*.parquet"):
            try:
                # Read parquet schema
                table = pq.read_table(str(parquet_file))
                df = table.to_pandas()
                
                dataset_name = parquet_file.stem
                fields = []
                
                for col in df.columns:
                    # Analyze field characteristics
                    field_info = {
                        "name": col,
                        "type": str(df[col].dtype),
                        "non_null_count": df[col].notna().sum(),
                        "unique_count": df[col].nunique(),
                        "sample_values": df[col].dropna().head(5).tolist() if not df[col].empty else []
                    }
                    
                    # Detect CDISC patterns
                    field_info["detected_patterns"] = self._detect_field_patterns(col, df[col])
                    
                    fields.append(field_info)
                
                available_fields[dataset_name] = fields
                
            except Exception as e:
                logger.error(f"Failed to analyze dataset {parquet_file}: {str(e)}")
                continue
        
        return available_fields
    
    def _detect_field_patterns(self, field_name: str, series: pd.Series) -> List[str]:
        """Detect CDISC and other patterns in field"""
        patterns = []
        
        # Check SDTM patterns
        for domain, fields in self.SDTM_PATTERNS.items():
            for sdtm_field, pattern in fields.items():
                if re.match(pattern, field_name):
                    patterns.append(f"SDTM.{domain}.{sdtm_field}")
        
        # Check ADaM patterns
        for dataset, fields in self.ADAM_PATTERNS.items():
            for adam_field, pattern in fields.items():
                if re.match(pattern, field_name):
                    patterns.append(f"ADaM.{dataset}.{adam_field}")
        
        # Check data type patterns
        if series.dtype == 'object':
            # Check if it's a date field
            try:
                pd.to_datetime(series.dropna().head(10))
                patterns.append("DATE_FIELD")
            except:
                pass
            
            # Check if it's a categorical field
            if series.nunique() < 20 and len(series) > 20:
                patterns.append("CATEGORICAL")
        
        elif series.dtype in ['int64', 'float64']:
            patterns.append("NUMERIC")
            
            # Check if it's a count or rate
            if all(series.dropna() >= 0):
                patterns.append("NON_NEGATIVE")
                if all(series.dropna() == series.dropna().astype(int)):
                    patterns.append("COUNT")
        
        return patterns
    
    async def _map_widget_requirements(
        self,
        requirement: Dict[str, Any],
        available_fields: Dict[str, List[Dict[str, Any]]]
    ) -> Optional[Dict[str, Any]]:
        """Map widget requirements to available fields"""
        widget_type = requirement.get("widget_type", "")
        data_config = requirement.get("data_config", {})
        
        mapping = {
            "widget_id": requirement["widget_id"],
            "widget_type": widget_type,
            "mapped_fields": {},
            "confidence": 0.0
        }
        
        # Extract required fields from data configuration
        required_fields = self._extract_required_fields(data_config)
        
        # Try to map each required field
        total_confidence = 0
        mapped_count = 0
        
        for req_field in required_fields:
            best_match = self._find_best_field_match(req_field, available_fields)
            if best_match:
                mapping["mapped_fields"][req_field["name"]] = best_match
                total_confidence += best_match["confidence"]
                mapped_count += 1
        
        if mapped_count > 0:
            mapping["confidence"] = total_confidence / mapped_count
            return mapping
        
        return None
    
    def _extract_required_fields(self, data_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract required fields from widget data configuration"""
        required_fields = []
        
        # Common patterns in data configuration
        if "dataset" in data_config:
            dataset_config = data_config["dataset"]
            if isinstance(dataset_config, dict):
                for field_name in ["valueField", "categoryField", "dateField", "measureField"]:
                    if field_name in dataset_config:
                        required_fields.append({
                            "name": field_name,
                            "type": self._infer_field_type(field_name),
                            "original_value": dataset_config[field_name]
                        })
        
        # Metric specific fields
        if "metric" in data_config:
            metric_config = data_config["metric"]
            if isinstance(metric_config, dict):
                if "field" in metric_config:
                    required_fields.append({
                        "name": "metricField",
                        "type": "numeric",
                        "original_value": metric_config["field"]
                    })
        
        return required_fields
    
    def _infer_field_type(self, field_name: str) -> str:
        """Infer field type from name"""
        if "date" in field_name.lower():
            return "date"
        elif "value" in field_name.lower() or "measure" in field_name.lower():
            return "numeric"
        elif "category" in field_name.lower():
            return "categorical"
        return "any"
    
    def _find_best_field_match(
        self,
        required_field: Dict[str, Any],
        available_fields: Dict[str, List[Dict[str, Any]]]
    ) -> Optional[Dict[str, Any]]:
        """Find best matching field from available fields"""
        best_match = None
        best_score = 0
        
        original_value = required_field.get("original_value", "")
        required_type = required_field.get("type", "any")
        
        for dataset_name, fields in available_fields.items():
            for field in fields:
                # Calculate match score
                score = self._calculate_field_match_score(
                    original_value,
                    required_type,
                    field
                )
                
                if score > best_score:
                    best_score = score
                    best_match = {
                        "dataset": dataset_name,
                        "field": field["name"],
                        "confidence": score,
                        "patterns": field.get("detected_patterns", [])
                    }
        
        # Only return if confidence is above threshold
        if best_score > 0.3:
            return best_match
        
        return None
    
    def _calculate_field_match_score(
        self,
        required_name: str,
        required_type: str,
        field_info: Dict[str, Any]
    ) -> float:
        """Calculate match score between required and available field"""
        score = 0.0
        
        # Name similarity
        name_score = self._string_similarity(required_name.lower(), field_info["name"].lower())
        score += name_score * 0.4
        
        # Pattern matching
        detected_patterns = field_info.get("detected_patterns", [])
        
        # Check if patterns match the required field
        if required_name.upper() in ["USUBJID", "SUBJID", "SUBJECTID"]:
            if any("USUBJID" in p for p in detected_patterns):
                score += 0.4
        elif "DATE" in required_name.upper():
            if "DATE_FIELD" in detected_patterns:
                score += 0.3
        elif required_type == "numeric":
            if "NUMERIC" in detected_patterns:
                score += 0.2
        elif required_type == "categorical":
            if "CATEGORICAL" in detected_patterns:
                score += 0.2
        
        # Type compatibility
        field_type = field_info.get("type", "")
        if required_type == "numeric" and "float" in field_type or "int" in field_type:
            score += 0.2
        elif required_type == "date" and "datetime" in field_type:
            score += 0.2
        elif required_type == "categorical" and field_info.get("unique_count", 0) < 50:
            score += 0.1
        
        return min(score, 1.0)
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two strings"""
        # Simple Levenshtein-like similarity
        if s1 == s2:
            return 1.0
        
        # Check if one contains the other
        if s1 in s2 or s2 in s1:
            return 0.8
        
        # Check common substrings
        common_length = 0
        for i in range(min(len(s1), len(s2))):
            if s1[i] == s2[i]:
                common_length += 1
            else:
                break
        
        return common_length / max(len(s1), len(s2))
    
    def _generate_global_mappings(self, available_fields: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Generate global mappings for common fields"""
        global_mappings = {
            "subject_identifier": None,
            "visit_identifier": None,
            "date_fields": [],
            "treatment_fields": [],
            "demographic_fields": []
        }
        
        for dataset_name, fields in available_fields.items():
            for field in fields:
                patterns = field.get("detected_patterns", [])
                
                # Subject identifier
                if any("USUBJID" in p for p in patterns):
                    global_mappings["subject_identifier"] = {
                        "dataset": dataset_name,
                        "field": field["name"]
                    }
                
                # Visit identifier
                if any("VISIT" in p for p in patterns):
                    if "visit_identifier" not in global_mappings or "VISITNUM" in str(patterns):
                        global_mappings["visit_identifier"] = {
                            "dataset": dataset_name,
                            "field": field["name"]
                        }
                
                # Date fields
                if "DATE_FIELD" in patterns:
                    global_mappings["date_fields"].append({
                        "dataset": dataset_name,
                        "field": field["name"]
                    })
                
                # Treatment fields
                if any("ARM" in p or "TRT" in p for p in patterns):
                    global_mappings["treatment_fields"].append({
                        "dataset": dataset_name,
                        "field": field["name"]
                    })
                
                # Demographic fields
                if any("DM" in p for p in patterns):
                    global_mappings["demographic_fields"].append({
                        "dataset": dataset_name,
                        "field": field["name"],
                        "type": next((p.split(".")[-1] for p in patterns if "DM" in p), "unknown")
                    })
        
        return global_mappings