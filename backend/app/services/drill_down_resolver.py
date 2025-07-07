# ABOUTME: Drill-down resolver service for handling hierarchical data navigation and detail views
# ABOUTME: Manages drill-down paths, data resolution, and navigation logic for dashboard widgets

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
import pandas as pd
import logging

from sqlmodel import Session, select
from pydantic import BaseModel, Field

from app.models.widget import WidgetDefinition
from app.models.study import Study
from app.services.data_source_manager import get_data_source_manager
from app.services.query_builder import QueryBuilder
from app.services.widget_interaction_service import DrillDownLevel, DrillDownPath
from app.services.filter_query_builder import FilterQueryBuilder, QueryType

logger = logging.getLogger(__name__)


class DrillDownStrategy(str, Enum):
    """Drill-down strategies"""
    HIERARCHICAL = "hierarchical"  # Follow predefined hierarchy
    DIMENSIONAL = "dimensional"    # Drill across dimensions
    TEMPORAL = "temporal"          # Drill through time periods
    CATEGORICAL = "categorical"    # Drill through categories
    CUSTOM = "custom"             # Custom drill-down logic


class DrillDownTarget(BaseModel):
    """Drill-down target configuration"""
    field: str
    label: str
    target_dataset: Optional[str] = None
    target_widget_type: Optional[str] = None
    sort_order: Optional[str] = "asc"
    filter_mapping: Optional[Dict[str, str]] = None
    aggregation: Optional[str] = None
    display_format: Optional[str] = None


class DrillDownRule(BaseModel):
    """Drill-down rule definition"""
    id: str
    source_field: str
    source_widget_type: str
    strategy: DrillDownStrategy
    targets: List[DrillDownTarget]
    conditions: Optional[Dict[str, Any]] = None
    max_depth: int = 5
    enabled: bool = True


class DrillDownContext(BaseModel):
    """Context for drill-down resolution"""
    study_id: str
    dashboard_id: str
    widget_id: str
    current_path: Optional[DrillDownPath] = None
    field_mappings: Dict[str, str] = Field(default_factory=dict)
    data_source: str = "primary"
    query_context: Dict[str, Any] = Field(default_factory=dict)


class DrillDownResult(BaseModel):
    """Result of drill-down resolution"""
    success: bool
    path_id: Optional[str] = None
    level_data: Optional[Dict[str, Any]] = None
    available_targets: List[DrillDownTarget] = Field(default_factory=list)
    detail_view_config: Optional[Dict[str, Any]] = None
    navigation_options: List[Dict[str, Any]] = Field(default_factory=list)
    error_message: Optional[str] = None


class DrillDownResolver:
    """Service for resolving drill-down operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.data_source_manager = get_data_source_manager()
        self.query_builder = QueryBuilder()
        self.filter_query_builder = FilterQueryBuilder()
        self.drill_rules: Dict[str, DrillDownRule] = {}
        self.default_hierarchies = self._load_default_hierarchies()
        
    def _load_default_hierarchies(self) -> Dict[str, List[str]]:
        """Load default drill-down hierarchies for clinical data"""
        return {
            "subject_hierarchy": ["COUNTRY", "SITEID", "USUBJID", "VISITNUM"],
            "temporal_hierarchy": ["YEAR", "QUARTER", "MONTH", "WEEK", "DAY"],
            "adverse_event_hierarchy": ["AEBODSYS", "AEHLT", "AEPT", "AETERM"],
            "medical_hierarchy": ["MHBODSYS", "MHHLT", "MHPT", "MHTERM"],
            "concomitant_med_hierarchy": ["CMCLAS", "CMCLASX", "CMDECOD", "CMTRT"],
            "lab_hierarchy": ["LBCAT", "LBSCAT", "LBTEST", "LBTESTCD"],
            "vital_signs_hierarchy": ["VSCAT", "VSTESTCD", "VSTRESU"],
        }
    
    def register_drill_rule(self, rule: DrillDownRule) -> None:
        """Register a drill-down rule"""
        self.drill_rules[rule.id] = rule
        logger.info(f"Registered drill-down rule: {rule.id}")
    
    def get_drill_rule(self, rule_id: str) -> Optional[DrillDownRule]:
        """Get drill-down rule by ID"""
        return self.drill_rules.get(rule_id)
    
    async def resolve_drill_down(
        self,
        context: DrillDownContext,
        field: str,
        value: Any,
        display_value: Optional[str] = None,
        target_field: Optional[str] = None
    ) -> DrillDownResult:
        """Resolve drill-down operation"""
        try:
            # Find applicable drill-down rules
            applicable_rules = self._find_applicable_rules(
                field, 
                context.widget_id,
                context.current_path
            )
            
            if not applicable_rules:
                return DrillDownResult(
                    success=False,
                    error_message=f"No drill-down rules found for field: {field}"
                )
            
            # Select best rule (for now, use first one)
            rule = applicable_rules[0]
            
            # Determine target field
            if target_field:
                # Use specified target
                target = next((t for t in rule.targets if t.field == target_field), None)
                if not target:
                    return DrillDownResult(
                        success=False,
                        error_message=f"Target field {target_field} not found in rule"
                    )
            else:
                # Auto-select next target in hierarchy
                target = self._select_next_target(rule, context.current_path)
                if not target:
                    return DrillDownResult(
                        success=False,
                        error_message="No more drill-down targets available"
                    )
            
            # Execute drill-down
            result = await self._execute_drill_down(
                context, 
                rule, 
                target, 
                field, 
                value, 
                display_value
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error resolving drill-down: {str(e)}")
            return DrillDownResult(
                success=False,
                error_message=f"Error resolving drill-down: {str(e)}"
            )
    
    async def get_drill_down_data(
        self,
        context: DrillDownContext,
        path: DrillDownPath,
        level: Optional[int] = None
    ) -> DrillDownResult:
        """Get data for specific drill-down level"""
        try:
            target_level = level if level is not None else path.current_level
            
            if target_level < 0 or target_level >= len(path.levels):
                return DrillDownResult(
                    success=False,
                    error_message=f"Invalid drill-down level: {target_level}"
                )
            
            current_level = path.levels[target_level]
            
            # Build filters from drill-down path
            filters = self._build_path_filters(path, target_level)
            
            # Determine target dataset and widget type
            target_dataset = self._determine_target_dataset(current_level, context)
            target_widget_type = current_level.widget_type or "table"
            
            # Build and execute query
            query_result = await self._execute_drill_down_query(
                context,
                target_dataset,
                filters,
                current_level
            )
            
            # Build detail view configuration
            detail_view_config = self._build_detail_view_config(
                target_widget_type,
                target_dataset,
                filters,
                current_level
            )
            
            # Get navigation options
            navigation_options = self._get_navigation_options(path, target_level)
            
            return DrillDownResult(
                success=True,
                path_id=path.id,
                level_data=query_result,
                detail_view_config=detail_view_config,
                navigation_options=navigation_options
            )
            
        except Exception as e:
            logger.error(f"Error getting drill-down data: {str(e)}")
            return DrillDownResult(
                success=False,
                error_message=f"Error getting drill-down data: {str(e)}"
            )
    
    async def get_available_targets(
        self,
        context: DrillDownContext,
        field: str,
        value: Any
    ) -> List[DrillDownTarget]:
        """Get available drill-down targets for a field/value"""
        try:
            applicable_rules = self._find_applicable_rules(
                field,
                context.widget_id,
                context.current_path
            )
            
            available_targets = []
            for rule in applicable_rules:
                for target in rule.targets:
                    # Check if target is applicable given current context
                    if self._is_target_applicable(target, context, field, value):
                        available_targets.append(target)
            
            return available_targets
            
        except Exception as e:
            logger.error(f"Error getting available targets: {str(e)}")
            return []
    
    def _find_applicable_rules(
        self,
        field: str,
        widget_id: str,
        current_path: Optional[DrillDownPath] = None
    ) -> List[DrillDownRule]:
        """Find drill-down rules applicable to the given context"""
        applicable_rules = []
        
        for rule in self.drill_rules.values():
            if not rule.enabled:
                continue
                
            # Check field match
            if rule.source_field != field and rule.source_field != "*":
                continue
            
            # Check depth limit
            current_depth = len(current_path.levels) if current_path else 0
            if current_depth >= rule.max_depth:
                continue
            
            # Check conditions
            if rule.conditions and not self._evaluate_conditions(rule.conditions, current_path):
                continue
            
            applicable_rules.append(rule)
        
        # Sort by priority or specificity
        applicable_rules.sort(key=lambda r: (
            0 if r.source_field == field else 1,  # Exact field match first
            -len(r.targets)  # More targets = higher priority
        ))
        
        return applicable_rules
    
    def _select_next_target(
        self,
        rule: DrillDownRule,
        current_path: Optional[DrillDownPath] = None
    ) -> Optional[DrillDownTarget]:
        """Select next drill-down target based on strategy"""
        
        if not rule.targets:
            return None
        
        if not current_path or not current_path.levels:
            # First level - return first target
            return rule.targets[0]
        
        # Find current position in hierarchy
        current_level = current_path.levels[-1]
        current_field = current_level.field
        
        # Find next target in sequence
        current_index = -1
        for i, target in enumerate(rule.targets):
            if target.field == current_field:
                current_index = i
                break
        
        # Return next target if available
        if current_index >= 0 and current_index < len(rule.targets) - 1:
            return rule.targets[current_index + 1]
        
        return None
    
    async def _execute_drill_down(
        self,
        context: DrillDownContext,
        rule: DrillDownRule,
        target: DrillDownTarget,
        field: str,
        value: Any,
        display_value: Optional[str] = None
    ) -> DrillDownResult:
        """Execute drill-down operation"""
        
        # Determine target dataset
        target_dataset = target.target_dataset or self._infer_dataset(target.field)
        
        # Build filters for drill-down
        filters = []
        if context.current_path:
            filters = self._build_path_filters(context.current_path)
        
        # Add current field filter
        from app.services.widget_interaction_service import FilterDefinition, FilterOperator
        current_filter = FilterDefinition(
            id=f"drill_{uuid.uuid4()}",
            field=field,
            label=f"Drill-down: {display_value or str(value)}",
            operator=FilterOperator.EQ,
            values=[value],
            active=True,
            temporary=True,
            created_at=datetime.utcnow()
        )
        filters.append(current_filter)
        
        # Execute query to get drill-down data
        query_result = await self._execute_drill_down_query(
            context,
            target_dataset,
            filters,
            None,  # New level, not existing
            target
        )
        
        # Build detail view configuration
        detail_view_config = self._build_detail_view_config(
            target.target_widget_type or "table",
            target_dataset,
            filters,
            None,
            target
        )
        
        # Get available next targets
        available_targets = []
        for next_target in rule.targets:
            if next_target.field != target.field:
                available_targets.append(next_target)
        
        return DrillDownResult(
            success=True,
            level_data=query_result,
            available_targets=available_targets,
            detail_view_config=detail_view_config
        )
    
    async def _execute_drill_down_query(
        self,
        context: DrillDownContext,
        dataset: str,
        filters: List[Any],
        current_level: Optional[DrillDownLevel] = None,
        target: Optional[DrillDownTarget] = None
    ) -> Dict[str, Any]:
        """Execute query for drill-down data"""
        
        try:
            # Apply field mappings
            mapped_filters = []
            for filter_def in filters:
                mapped_field = context.field_mappings.get(filter_def.field, filter_def.field)
                filter_def.field = mapped_field
                mapped_filters.append(filter_def)
            
            # Build query using filter query builder
            self.filter_query_builder.set_field_mappings(context.field_mappings)
            
            query = self.filter_query_builder.build_query(
                mapped_filters,
                QueryType.PANDAS  # Use pandas for now
            )
            
            # Determine columns to select
            columns = ["*"]  # Default to all columns
            if target and target.field:
                # Ensure target field is included
                columns = [target.field, "USUBJID", "SITEID", "VISITNUM"]  # Common fields
            
            # Build final query
            final_query = {
                "dataset": dataset,
                "columns": columns,
                "limit": 1000,  # Reasonable limit for drill-down
                **query
            }
            
            # Execute query through data source manager
            data_sources = await self.data_source_manager.list_sources()
            if context.data_source not in data_sources:
                # Auto-discover sources if needed
                discovered = await self.data_source_manager.auto_discover_sources(context.study_id)
                if discovered:
                    first_path = list(discovered.keys())[0]
                    first_type = discovered[first_path]
                    await self.data_source_manager.register_data_source(
                        context.data_source,
                        first_type,
                        base_path=first_path
                    )
            
            # Execute query
            df = await self.data_source_manager.query(context.data_source, final_query)
            
            # Convert to result format
            result = {
                "data": df.to_dict('records') if not df.empty else [],
                "columns": df.columns.tolist() if not df.empty else [],
                "total_rows": len(df),
                "dataset": dataset,
                "query_time": datetime.utcnow().isoformat()
            }
            
            # Add aggregation if specified
            if target and target.aggregation:
                result["aggregation"] = self._calculate_aggregation(df, target)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing drill-down query: {str(e)}")
            # Return empty result with error info
            return {
                "data": [],
                "columns": [],
                "total_rows": 0,
                "dataset": dataset,
                "error": str(e),
                "query_time": datetime.utcnow().isoformat()
            }
    
    def _build_path_filters(
        self,
        path: DrillDownPath,
        up_to_level: Optional[int] = None
    ) -> List[Any]:
        """Build filters from drill-down path"""
        from app.services.widget_interaction_service import FilterDefinition, FilterOperator
        
        filters = []
        end_level = up_to_level if up_to_level is not None else len(path.levels)
        
        for i in range(min(end_level + 1, len(path.levels))):
            level = path.levels[i]
            
            filter_def = FilterDefinition(
                id=f"drill_level_{i}",
                field=level.field,
                label=f"Level {i}: {level.display_value or str(level.value)}",
                operator=FilterOperator.EQ,
                values=[level.value],
                active=True,
                temporary=True,
                created_at=level.timestamp
            )
            filters.append(filter_def)
        
        return filters
    
    def _build_detail_view_config(
        self,
        widget_type: str,
        dataset: str,
        filters: List[Any],
        current_level: Optional[DrillDownLevel] = None,
        target: Optional[DrillDownTarget] = None
    ) -> Dict[str, Any]:
        """Build configuration for detail view widget"""
        
        config = {
            "widget_type": widget_type,
            "dataset": dataset,
            "filters": [f.model_dump() for f in filters],
            "title": f"Detail View - {dataset}",
            "auto_refresh": False
        }
        
        if widget_type == "table":
            config.update({
                "columns": self._get_table_columns(dataset),
                "pagination": {"page_size": 50, "page": 1},
                "sorting": {"field": "USUBJID", "order": "asc"}
            })
        elif widget_type == "chart":
            config.update({
                "chart_type": "bar",
                "x_field": target.field if target else "USUBJID",
                "y_field": "COUNT",
                "aggregation": "count"
            })
        
        if current_level:
            config["title"] = f"Detail View - {current_level.display_value or current_level.value}"
        
        return config
    
    def _get_table_columns(self, dataset: str) -> List[Dict[str, str]]:
        """Get default table columns for dataset"""
        
        common_columns = [
            {"field": "USUBJID", "label": "Subject ID", "type": "string"},
            {"field": "SITEID", "label": "Site ID", "type": "string"},
        ]
        
        dataset_columns = {
            "ADSL": [
                {"field": "AGE", "label": "Age", "type": "number"},
                {"field": "SEX", "label": "Sex", "type": "string"},
                {"field": "RACE", "label": "Race", "type": "string"},
                {"field": "COUNTRY", "label": "Country", "type": "string"},
            ],
            "ADAE": [
                {"field": "VISITNUM", "label": "Visit", "type": "number"},
                {"field": "AETERM", "label": "AE Term", "type": "string"},
                {"field": "AESEV", "label": "Severity", "type": "string"},
                {"field": "AESTDT", "label": "Start Date", "type": "date"},
            ],
            "ADLB": [
                {"field": "VISITNUM", "label": "Visit", "type": "number"},
                {"field": "LBTEST", "label": "Lab Test", "type": "string"},
                {"field": "LBSTRESN", "label": "Result (Numeric)", "type": "number"},
                {"field": "LBSTRESU", "label": "Unit", "type": "string"},
            ]
        }
        
        return common_columns + dataset_columns.get(dataset, [])
    
    def _get_navigation_options(
        self,
        path: DrillDownPath,
        current_level: int
    ) -> List[Dict[str, Any]]:
        """Get navigation options for drill-down path"""
        
        options = []
        
        # Add breadcrumb navigation
        for i, level in enumerate(path.levels):
            options.append({
                "type": "breadcrumb",
                "level": i,
                "title": level.display_value or str(level.value),
                "field": level.field,
                "value": level.value,
                "active": i == current_level
            })
        
        # Add back navigation
        if current_level > 0:
            options.append({
                "type": "back",
                "target_level": current_level - 1,
                "title": "Go Back"
            })
        
        # Add clear navigation
        options.append({
            "type": "clear",
            "title": "Clear Drill-down"
        })
        
        return options
    
    def _determine_target_dataset(
        self,
        level: DrillDownLevel,
        context: DrillDownContext
    ) -> str:
        """Determine target dataset for drill-down level"""
        
        # Use context if available
        if level.context and level.context.get("target_dataset"):
            return level.context["target_dataset"]
        
        # Infer from field name
        return self._infer_dataset(level.field)
    
    def _infer_dataset(self, field: str) -> str:
        """Infer dataset from field name"""
        
        field_upper = field.upper()
        
        # CDISC naming conventions
        if field_upper.startswith("AE"):
            return "ADAE"
        elif field_upper.startswith("LB"):
            return "ADLB"
        elif field_upper.startswith("VS"):
            return "ADVS"
        elif field_upper.startswith("CM"):
            return "ADCM"
        elif field_upper.startswith("MH"):
            return "ADMH"
        elif field_upper.startswith("EX"):
            return "ADEX"
        else:
            return "ADSL"  # Default to subject-level data
    
    def _is_target_applicable(
        self,
        target: DrillDownTarget,
        context: DrillDownContext,
        field: str,
        value: Any
    ) -> bool:
        """Check if drill-down target is applicable"""
        
        # Basic checks
        if not target.field:
            return False
        
        # Check if target field is different from source field
        if target.field == field:
            return False
        
        # Add more sophisticated checks here based on data availability,
        # user permissions, etc.
        
        return True
    
    def _evaluate_conditions(
        self,
        conditions: Dict[str, Any],
        current_path: Optional[DrillDownPath] = None
    ) -> bool:
        """Evaluate drill-down rule conditions"""
        
        # Simple condition evaluation - can be extended
        for key, expected_value in conditions.items():
            if key == "max_levels":
                current_depth = len(current_path.levels) if current_path else 0
                if current_depth >= expected_value:
                    return False
            elif key == "required_fields":
                # Check if required fields are present in path
                if current_path:
                    path_fields = {level.field for level in current_path.levels}
                    required_fields = set(expected_value)
                    if not required_fields.issubset(path_fields):
                        return False
        
        return True
    
    def _calculate_aggregation(
        self,
        df: pd.DataFrame,
        target: DrillDownTarget
    ) -> Dict[str, Any]:
        """Calculate aggregation for target field"""
        
        if df.empty or not target.aggregation:
            return {}
        
        try:
            if target.aggregation == "count":
                return {
                    "type": "count",
                    "value": len(df),
                    "field": target.field
                }
            elif target.aggregation == "distinct_count":
                return {
                    "type": "distinct_count",
                    "value": df[target.field].nunique(),
                    "field": target.field
                }
            elif target.aggregation == "sum" and target.field in df.columns:
                return {
                    "type": "sum",
                    "value": df[target.field].sum(),
                    "field": target.field
                }
            elif target.aggregation == "avg" and target.field in df.columns:
                return {
                    "type": "avg",
                    "value": df[target.field].mean(),
                    "field": target.field
                }
        except Exception as e:
            logger.error(f"Error calculating aggregation: {str(e)}")
        
        return {}


# Factory function
def get_drill_down_resolver(db: Session) -> DrillDownResolver:
    """Get drill-down resolver instance"""
    return DrillDownResolver(db)