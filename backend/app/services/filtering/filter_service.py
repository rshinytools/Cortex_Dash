# ABOUTME: Advanced filtering service for dashboard data
# ABOUTME: Provides complex filtering, saved filters, and filter templates

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
from sqlmodel import Session, select

from app.core.logging import logger

class FilterOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN_OR_EQUAL = "lte"
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    REGEX = "regex"

class FilterLogic(str, Enum):
    AND = "and"
    OR = "or"
    NOT = "not"

class FilterService:
    """Advanced filtering service for clinical data"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def build_filter_query(self, filters: List[Dict[str, Any]], logic: str = "and") -> str:
        """Build SQL WHERE clause from filter configuration"""
        
        if not filters:
            return ""
        
        conditions = []
        
        for filter_item in filters:
            condition = self._build_single_condition(filter_item)
            if condition:
                conditions.append(condition)
        
        if conditions:
            if logic.upper() == "OR":
                return f"({' OR '.join(conditions)})"
            else:
                return f"({' AND '.join(conditions)})"
        
        return ""
    
    def _build_single_condition(self, filter_item: Dict[str, Any]) -> str:
        """Build single filter condition"""
        
        field = filter_item.get("field")
        operator = filter_item.get("operator")
        value = filter_item.get("value")
        
        if not field or not operator:
            return ""
        
        # Handle different operators
        if operator == FilterOperator.EQUALS:
            return f"{field} = '{value}'"
        
        elif operator == FilterOperator.NOT_EQUALS:
            return f"{field} != '{value}'"
        
        elif operator == FilterOperator.GREATER_THAN:
            return f"{field} > {value}"
        
        elif operator == FilterOperator.LESS_THAN:
            return f"{field} < {value}"
        
        elif operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            return f"{field} >= {value}"
        
        elif operator == FilterOperator.LESS_THAN_OR_EQUAL:
            return f"{field} <= {value}"
        
        elif operator == FilterOperator.BETWEEN:
            if isinstance(value, list) and len(value) == 2:
                return f"{field} BETWEEN {value[0]} AND {value[1]}"
        
        elif operator == FilterOperator.IN:
            if isinstance(value, list):
                values = "', '".join(str(v) for v in value)
                return f"{field} IN ('{values}')"
        
        elif operator == FilterOperator.NOT_IN:
            if isinstance(value, list):
                values = "', '".join(str(v) for v in value)
                return f"{field} NOT IN ('{values}')"
        
        elif operator == FilterOperator.CONTAINS:
            return f"{field} LIKE '%{value}%'"
        
        elif operator == FilterOperator.NOT_CONTAINS:
            return f"{field} NOT LIKE '%{value}%'"
        
        elif operator == FilterOperator.STARTS_WITH:
            return f"{field} LIKE '{value}%'"
        
        elif operator == FilterOperator.ENDS_WITH:
            return f"{field} LIKE '%{value}'"
        
        elif operator == FilterOperator.IS_NULL:
            return f"{field} IS NULL"
        
        elif operator == FilterOperator.IS_NOT_NULL:
            return f"{field} IS NOT NULL"
        
        elif operator == FilterOperator.REGEX:
            return f"{field} ~ '{value}'"
        
        return ""
    
    def apply_filters_to_dataframe(self, df, filters: List[Dict[str, Any]], logic: str = "and"):
        """Apply filters to pandas DataFrame"""
        
        import pandas as pd
        
        if df is None or df.empty or not filters:
            return df
        
        mask = None
        
        for filter_item in filters:
            condition = self._build_dataframe_condition(df, filter_item)
            
            if condition is not None:
                if mask is None:
                    mask = condition
                elif logic.lower() == "or":
                    mask = mask | condition
                else:  # and
                    mask = mask & condition
        
        if mask is not None:
            return df[mask]
        
        return df
    
    def _build_dataframe_condition(self, df, filter_item: Dict[str, Any]):
        """Build pandas DataFrame condition"""
        
        field = filter_item.get("field")
        operator = filter_item.get("operator")
        value = filter_item.get("value")
        
        if field not in df.columns:
            return None
        
        # Handle different operators
        if operator == FilterOperator.EQUALS:
            return df[field] == value
        
        elif operator == FilterOperator.NOT_EQUALS:
            return df[field] != value
        
        elif operator == FilterOperator.GREATER_THAN:
            return df[field] > value
        
        elif operator == FilterOperator.LESS_THAN:
            return df[field] < value
        
        elif operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            return df[field] >= value
        
        elif operator == FilterOperator.LESS_THAN_OR_EQUAL:
            return df[field] <= value
        
        elif operator == FilterOperator.BETWEEN:
            if isinstance(value, list) and len(value) == 2:
                return (df[field] >= value[0]) & (df[field] <= value[1])
        
        elif operator == FilterOperator.IN:
            if isinstance(value, list):
                return df[field].isin(value)
        
        elif operator == FilterOperator.NOT_IN:
            if isinstance(value, list):
                return ~df[field].isin(value)
        
        elif operator == FilterOperator.CONTAINS:
            return df[field].str.contains(str(value), na=False)
        
        elif operator == FilterOperator.NOT_CONTAINS:
            return ~df[field].str.contains(str(value), na=False)
        
        elif operator == FilterOperator.STARTS_WITH:
            return df[field].str.startswith(str(value), na=False)
        
        elif operator == FilterOperator.ENDS_WITH:
            return df[field].str.endswith(str(value), na=False)
        
        elif operator == FilterOperator.IS_NULL:
            return df[field].isna()
        
        elif operator == FilterOperator.IS_NOT_NULL:
            return df[field].notna()
        
        elif operator == FilterOperator.REGEX:
            return df[field].str.match(str(value), na=False)
        
        return None
    
    def get_filter_templates(self) -> List[Dict[str, Any]]:
        """Get predefined filter templates"""
        
        templates = [
            {
                "id": "active_subjects",
                "name": "Active Subjects",
                "description": "Filter for currently active subjects",
                "filters": [
                    {"field": "status", "operator": "equals", "value": "active"},
                    {"field": "completion_date", "operator": "is_null", "value": None}
                ],
                "logic": "and"
            },
            {
                "id": "recent_adverse_events",
                "name": "Recent Adverse Events",
                "description": "Adverse events in the last 30 days",
                "filters": [
                    {"field": "event_type", "operator": "equals", "value": "AE"},
                    {"field": "event_date", "operator": "gte", "value": "{{30_days_ago}}"}
                ],
                "logic": "and"
            },
            {
                "id": "serious_events",
                "name": "Serious Events",
                "description": "Serious adverse events or protocol deviations",
                "filters": [
                    {"field": "severity", "operator": "in", "value": ["serious", "life-threatening"]},
                    {"field": "sae_flag", "operator": "equals", "value": "Y"}
                ],
                "logic": "or"
            },
            {
                "id": "screening_failures",
                "name": "Screening Failures",
                "description": "Subjects who failed screening",
                "filters": [
                    {"field": "visit", "operator": "equals", "value": "screening"},
                    {"field": "eligible", "operator": "equals", "value": "N"}
                ],
                "logic": "and"
            },
            {
                "id": "protocol_deviations",
                "name": "Protocol Deviations",
                "description": "All protocol deviations",
                "filters": [
                    {"field": "deviation_flag", "operator": "equals", "value": "Y"}
                ],
                "logic": "and"
            },
            {
                "id": "missing_data",
                "name": "Missing Data",
                "description": "Records with missing critical data",
                "filters": [
                    {"field": "primary_endpoint", "operator": "is_null", "value": None}
                ],
                "logic": "and"
            }
        ]
        
        # Process template variables
        for template in templates:
            template["filters"] = self._process_template_variables(template["filters"])
        
        return templates
    
    def _process_template_variables(self, filters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process template variables in filters"""
        
        processed = []
        
        for filter_item in filters:
            if isinstance(filter_item.get("value"), str) and "{{" in filter_item["value"]:
                # Process template variables
                value = filter_item["value"]
                
                if value == "{{30_days_ago}}":
                    filter_item["value"] = (datetime.utcnow() - timedelta(days=30)).isoformat()
                elif value == "{{7_days_ago}}":
                    filter_item["value"] = (datetime.utcnow() - timedelta(days=7)).isoformat()
                elif value == "{{today}}":
                    filter_item["value"] = datetime.utcnow().date().isoformat()
                elif value == "{{yesterday}}":
                    filter_item["value"] = (datetime.utcnow() - timedelta(days=1)).date().isoformat()
            
            processed.append(filter_item)
        
        return processed
    
    def save_filter_preset(
        self,
        user_id: str,
        study_id: str,
        name: str,
        filters: List[Dict[str, Any]],
        logic: str = "and",
        is_global: bool = False
    ) -> Dict[str, Any]:
        """Save filter preset for reuse"""
        
        # This would save to database
        preset = {
            "id": f"preset_{datetime.utcnow().timestamp()}",
            "user_id": user_id,
            "study_id": study_id,
            "name": name,
            "filters": filters,
            "logic": logic,
            "is_global": is_global,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # In real implementation, save to database
        logger.info(f"Saved filter preset: {name} for user {user_id}")
        
        return preset
    
    def get_user_presets(self, user_id: str, study_id: str) -> List[Dict[str, Any]]:
        """Get saved filter presets for user"""
        
        # This would fetch from database
        # For now, return example presets
        return [
            {
                "id": "preset_1",
                "name": "My Active Patients",
                "filters": [
                    {"field": "assigned_to", "operator": "equals", "value": user_id},
                    {"field": "status", "operator": "equals", "value": "active"}
                ],
                "logic": "and",
                "created_at": datetime.utcnow().isoformat()
            }
        ]
    
    def validate_filter(self, filter_item: Dict[str, Any]) -> bool:
        """Validate filter configuration"""
        
        required_fields = ["field", "operator"]
        
        for field in required_fields:
            if field not in filter_item:
                return False
        
        # Validate operator
        try:
            FilterOperator(filter_item["operator"])
        except ValueError:
            return False
        
        # Validate value based on operator
        operator = filter_item["operator"]
        
        if operator in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            # These operators don't need a value
            pass
        elif operator == FilterOperator.BETWEEN:
            # Needs array with 2 values
            if not isinstance(filter_item.get("value"), list) or len(filter_item["value"]) != 2:
                return False
        elif operator in [FilterOperator.IN, FilterOperator.NOT_IN]:
            # Needs array
            if not isinstance(filter_item.get("value"), list):
                return False
        else:
            # Needs single value
            if "value" not in filter_item:
                return False
        
        return True