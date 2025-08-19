# ABOUTME: EDC pattern recognition and auto-mapping service for Medidata Rave and Veeva Vault
# ABOUTME: Automatically detects and maps EDC export patterns to standard widget requirements

import re
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class EDCPatternMapper:
    """Auto-maps EDC export patterns from Medidata Rave and Veeva Vault"""
    
    # Medidata Rave common patterns (CDISC-like)
    RAVE_PATTERNS = {
        "subject_id": [
            r"(?i)^usubjid$",
            r"(?i)^subject.*id$",
            r"(?i)^subj.*id$",
            r"(?i)^patient.*id$"
        ],
        "site_id": [
            r"(?i)^siteid$",
            r"(?i)^site.*id$",
            r"(?i)^center.*id$",
            r"(?i)^inv.*site$"
        ],
        "enrollment_date": [
            r"(?i)^rfstdtc$",
            r"(?i)^enroll.*date$",
            r"(?i)^randomiz.*date$",
            r"(?i)^consent.*date$"
        ],
        "treatment_arm": [
            r"(?i)^arm$",
            r"(?i)^armcd$",
            r"(?i)^trt.*grp$",
            r"(?i)^treatment.*group$"
        ],
        "adverse_event": [
            r"(?i)^aeterm$",
            r"(?i)^ae.*term$",
            r"(?i)^adverse.*event$"
        ],
        "ae_severity": [
            r"(?i)^aesev$",
            r"(?i)^ae.*severity$",
            r"(?i)^severity$"
        ],
        "ae_serious": [
            r"(?i)^aeser$",
            r"(?i)^serious$",
            r"(?i)^sae$"
        ],
        "visit": [
            r"(?i)^visit$",
            r"(?i)^visitnum$",
            r"(?i)^visit.*num$",
            r"(?i)^visitname$"
        ],
        "lab_test": [
            r"(?i)^lbtest$",
            r"(?i)^lab.*test$",
            r"(?i)^test.*name$"
        ],
        "lab_result": [
            r"(?i)^lborres$",
            r"(?i)^lbstresn$",
            r"(?i)^result$",
            r"(?i)^value$"
        ]
    }
    
    # Veeva Vault common patterns
    VEEVA_PATTERNS = {
        "subject_id": [
            r"(?i)^subject.*id$",
            r"(?i)^patient.*id$",
            r"(?i)^participant.*id$",
            r"(?i)^screening.*number$"
        ],
        "site_id": [
            r"(?i)^site.*id$",
            r"(?i)^site.*number$",
            r"(?i)^center.*number$",
            r"(?i)^location.*id$"
        ],
        "enrollment_date": [
            r"(?i)^enrollment.*date$",
            r"(?i)^enrolled.*date$",
            r"(?i)^randomization.*date$",
            r"(?i)^icf.*date$"
        ],
        "status": [
            r"(?i)^status$",
            r"(?i)^subject.*status$",
            r"(?i)^enrollment.*status$"
        ],
        "sae_description": [
            r"(?i)^event.*description$",
            r"(?i)^sae.*description$",
            r"(?i)^adverse.*description$"
        ],
        "onset_date": [
            r"(?i)^onset.*date$",
            r"(?i)^start.*date$",
            r"(?i)^event.*date$"
        ]
    }
    
    # Combined patterns for flexible detection
    COMBINED_PATTERNS = {
        **RAVE_PATTERNS,
        **{f"veeva_{k}": v for k, v in VEEVA_PATTERNS.items()}
    }
    
    def detect_edc_system(self, df: pd.DataFrame) -> str:
        """Detect which EDC system the data is from based on column patterns"""
        columns = df.columns.tolist()
        
        # Count matches for each system
        rave_score = 0
        veeva_score = 0
        
        # Check for CDISC-specific columns (strong indicator of Rave)
        cdisc_columns = ['USUBJID', 'STUDYID', 'DOMAIN', 'VISITNUM', 'AETERM', 'LBTEST']
        for col in columns:
            if col.upper() in cdisc_columns:
                rave_score += 2
        
        # Check for Veeva-specific patterns
        veeva_indicators = ['enrollment_status', 'event_description', 'icf_date']
        for col in columns:
            if any(indicator in col.lower() for indicator in veeva_indicators):
                veeva_score += 2
        
        # Additional pattern matching
        for col in columns:
            # Check Rave patterns
            for pattern_list in self.RAVE_PATTERNS.values():
                if any(re.match(pattern, col) for pattern in pattern_list):
                    rave_score += 1
                    break
            
            # Check Veeva patterns
            for pattern_list in self.VEEVA_PATTERNS.values():
                if any(re.match(pattern, col) for pattern in pattern_list):
                    veeva_score += 1
                    break
        
        logger.info(f"EDC detection scores - Rave: {rave_score}, Veeva: {veeva_score}")
        
        if rave_score > veeva_score:
            return "medidata_rave"
        elif veeva_score > rave_score:
            return "veeva_vault"
        else:
            return "unknown"
    
    def auto_map_columns(
        self,
        df: pd.DataFrame,
        target_fields: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Auto-map DataFrame columns to target fields with confidence scores"""
        mappings = {}
        columns = df.columns.tolist()
        edc_system = self.detect_edc_system(df)
        
        # Select appropriate patterns based on detected system
        if edc_system == "medidata_rave":
            patterns_to_use = self.RAVE_PATTERNS
        elif edc_system == "veeva_vault":
            patterns_to_use = self.VEEVA_PATTERNS
        else:
            patterns_to_use = self.COMBINED_PATTERNS
        
        for target in target_fields:
            best_match = self._find_best_column_match(
                target,
                columns,
                patterns_to_use,
                df
            )
            
            if best_match:
                mappings[target] = best_match
        
        # Add EDC system information
        mappings["_metadata"] = {
            "edc_system": edc_system,
            "total_columns": len(columns),
            "mapped_fields": len([m for m in mappings.values() if m.get("column")])
        }
        
        return mappings
    
    def _find_best_column_match(
        self,
        target_field: str,
        columns: List[str],
        patterns: Dict[str, List[str]],
        df: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """Find the best matching column for a target field"""
        candidates = []
        
        # Check if we have patterns for this target field
        if target_field in patterns:
            pattern_list = patterns[target_field]
            
            for col in columns:
                for pattern in pattern_list:
                    if re.match(pattern, col):
                        # Calculate confidence based on pattern match and data characteristics
                        confidence = self._calculate_confidence(col, target_field, df)
                        candidates.append({
                            "column": col,
                            "confidence": confidence,
                            "match_type": "pattern",
                            "pattern": pattern
                        })
                        break
        
        # If no pattern match, try fuzzy matching
        if not candidates:
            for col in columns:
                similarity = self._calculate_similarity(target_field, col)
                if similarity > 0.5:
                    confidence = similarity * 0.7  # Lower confidence for fuzzy matches
                    candidates.append({
                        "column": col,
                        "confidence": confidence,
                        "match_type": "fuzzy",
                        "similarity": similarity
                    })
        
        # Return best candidate
        if candidates:
            return max(candidates, key=lambda x: x["confidence"])
        
        return None
    
    def _calculate_confidence(
        self,
        column: str,
        target_field: str,
        df: pd.DataFrame
    ) -> float:
        """Calculate confidence score for a mapping"""
        confidence = 0.5  # Base confidence for pattern match
        
        # Exact match (case-insensitive)
        if column.lower() == target_field.lower():
            confidence = 0.95
        
        # Check data characteristics
        if target_field in ["subject_id", "site_id"]:
            # Should have unique or mostly unique values
            unique_ratio = df[column].nunique() / len(df)
            if unique_ratio > 0.8:
                confidence += 0.2
        
        elif target_field in ["enrollment_date", "onset_date"]:
            # Should be parseable as dates
            try:
                pd.to_datetime(df[column].dropna().head(10))
                confidence += 0.3
            except:
                confidence -= 0.2
        
        elif target_field in ["ae_serious", "status"]:
            # Should have limited unique values
            unique_count = df[column].nunique()
            if unique_count < 10:
                confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two strings"""
        s1 = s1.lower().replace("_", "").replace("-", "")
        s2 = s2.lower().replace("_", "").replace("-", "")
        
        if s1 == s2:
            return 1.0
        
        # Check if one contains the other
        if s1 in s2 or s2 in s1:
            return 0.8
        
        # Calculate overlap
        set1 = set(s1)
        set2 = set(s2)
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        if union:
            return len(intersection) / len(union)
        
        return 0.0
    
    def generate_kpi_mappings(
        self,
        df: pd.DataFrame,
        kpi_type: str
    ) -> Dict[str, Any]:
        """Generate mappings specific to KPI requirements"""
        
        if kpi_type == "enrollment_rate":
            # Map fields needed for enrollment rate calculation
            required_fields = ["subject_id", "enrollment_date", "site_id"]
            mappings = self.auto_map_columns(df, required_fields)
            
            # Add calculation logic
            mappings["calculation"] = {
                "type": "enrollment_rate",
                "formula": "COUNT(DISTINCT subject_id) / DATEDIFF(MAX(enrollment_date), MIN(enrollment_date))",
                "group_by": ["site_id"],
                "filters": []
            }
            
        elif kpi_type == "sae_count":
            # Map fields for SAE count
            required_fields = ["subject_id", "ae_serious", "ae_severity", "adverse_event"]
            mappings = self.auto_map_columns(df, required_fields)
            
            # Detect SAE values
            sae_values = self._detect_sae_values(df, mappings)
            
            mappings["calculation"] = {
                "type": "sae_count",
                "formula": "COUNT(*) WHERE ae_serious IN sae_values",
                "sae_values": sae_values,
                "group_by": ["subject_id"],
                "filters": []
            }
        
        else:
            # Generic mapping
            mappings = self.auto_map_columns(df, df.columns.tolist()[:10])
        
        return mappings
    
    def _detect_sae_values(
        self,
        df: pd.DataFrame,
        mappings: Dict[str, Any]
    ) -> List[str]:
        """Detect which values indicate SAEs"""
        sae_values = []
        
        # Check ae_serious field
        if "ae_serious" in mappings and mappings["ae_serious"].get("column"):
            col = mappings["ae_serious"]["column"]
            unique_values = df[col].unique()
            
            # Common SAE indicators
            for val in unique_values:
                if str(val).upper() in ['Y', 'YES', 'TRUE', '1', 'SERIOUS']:
                    sae_values.append(str(val))
        
        # Check severity field
        if "ae_severity" in mappings and mappings["ae_severity"].get("column"):
            col = mappings["ae_severity"]["column"]
            unique_values = df[col].unique()
            
            for val in unique_values:
                if str(val).upper() in ['SEVERE', 'LIFE-THREATENING', 'FATAL', 'GRADE 4', 'GRADE 5']:
                    sae_values.append(str(val))
        
        return sae_values if sae_values else ['Y', 'SEVERE']
    
    def validate_mapping(
        self,
        df: pd.DataFrame,
        mapping: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate that a mapping will work with the data"""
        errors = []
        
        for target, config in mapping.items():
            if target == "_metadata" or not isinstance(config, dict):
                continue
            
            if "column" in config:
                col = config["column"]
                
                # Check column exists
                if col not in df.columns:
                    errors.append(f"Column '{col}' not found in data")
                
                # Check for required data
                elif df[col].isna().all():
                    errors.append(f"Column '{col}' has no data")
                
                # Type-specific validation
                elif target.endswith("_date"):
                    try:
                        pd.to_datetime(df[col].dropna().head(10))
                    except:
                        errors.append(f"Column '{col}' cannot be parsed as date")
        
        return len(errors) == 0, errors