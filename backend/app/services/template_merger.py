# ABOUTME: Template merger service for combining multiple templates into unified structures
# ABOUTME: Handles template merging operations, conflict resolution, and structure validation

import uuid
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from ..models.dashboard import DashboardTemplate, InheritanceType


class ConflictResolution(str, Enum):
    """Strategies for resolving merge conflicts"""
    KEEP_FIRST = "keep_first"      # Keep first template's value
    KEEP_LAST = "keep_last"        # Keep last template's value
    MERGE_ARRAYS = "merge_arrays"   # Merge array values
    THROW_ERROR = "throw_error"     # Throw error on conflict


@dataclass
class MergeConflict:
    """Represents a conflict during template merging"""
    path: str
    first_value: Any
    second_value: Any
    resolution: Optional[ConflictResolution] = None


class TemplateMergeError(Exception):
    """Exception raised during template merging"""
    def __init__(self, message: str, conflicts: List[MergeConflict] = None):
        super().__init__(message)
        self.conflicts = conflicts or []


class TemplateMergerService:
    """Service for merging multiple templates into unified structures"""
    
    def __init__(self):
        self.conflicts: List[MergeConflict] = []
    
    def merge_templates(
        self,
        templates: List[DashboardTemplate],
        conflict_resolution: ConflictResolution = ConflictResolution.KEEP_LAST,
        custom_rules: Optional[Dict[str, ConflictResolution]] = None
    ) -> Dict[str, Any]:
        """
        Merge multiple templates into a single unified structure.
        
        Args:
            templates: List of templates to merge (in order of precedence)
            conflict_resolution: Default strategy for resolving conflicts
            custom_rules: Path-specific conflict resolution rules
            
        Returns:
            Merged template structure
        """
        if not templates:
            return {}
        
        if len(templates) == 1:
            return templates[0].template_structure
        
        self.conflicts = []
        custom_rules = custom_rules or {}
        
        # Start with first template
        merged = templates[0].template_structure.copy()
        
        # Merge each subsequent template
        for i, template in enumerate(templates[1:], 1):
            merged = self._merge_two_structures(
                merged,
                template.template_structure,
                conflict_resolution,
                custom_rules,
                f"template_{i}"
            )
        
        return merged
    
    def merge_template_versions(
        self,
        base_template: DashboardTemplate,
        version_structures: List[Dict[str, Any]],
        conflict_resolution: ConflictResolution = ConflictResolution.KEEP_LAST
    ) -> Dict[str, Any]:
        """
        Merge multiple versions of a template to create final structure.
        Used for template migration and version reconciliation.
        """
        if not version_structures:
            return base_template.template_structure
        
        self.conflicts = []
        merged = base_template.template_structure.copy()
        
        for i, version_structure in enumerate(version_structures):
            merged = self._merge_two_structures(
                merged,
                version_structure,
                conflict_resolution,
                {},
                f"version_{i}"
            )
        
        return merged
    
    def _merge_two_structures(
        self,
        first: Dict[str, Any],
        second: Dict[str, Any],
        default_resolution: ConflictResolution,
        custom_rules: Dict[str, ConflictResolution],
        context: str = ""
    ) -> Dict[str, Any]:
        """Merge two template structures"""
        merged = {}
        all_keys = set(first.keys()) | set(second.keys())
        
        for key in all_keys:
            path = f"{context}.{key}" if context else key
            resolution = custom_rules.get(path, default_resolution)
            
            if key not in first:
                merged[key] = second[key]
            elif key not in second:
                merged[key] = first[key]
            else:
                # Both have the key - potential conflict
                merged[key] = self._resolve_value_conflict(
                    first[key], second[key], resolution, path
                )
        
        return merged
    
    def _resolve_value_conflict(
        self,
        first_value: Any,
        second_value: Any,
        resolution: ConflictResolution,
        path: str
    ) -> Any:
        """Resolve conflict between two values"""
        
        # If values are equal, no conflict
        if first_value == second_value:
            return first_value
        
        # Record the conflict
        conflict = MergeConflict(path, first_value, second_value, resolution)
        self.conflicts.append(conflict)
        
        # Apply resolution strategy
        if resolution == ConflictResolution.KEEP_FIRST:
            return first_value
        elif resolution == ConflictResolution.KEEP_LAST:
            return second_value
        elif resolution == ConflictResolution.THROW_ERROR:
            raise TemplateMergeError(f"Conflict at path {path}", [conflict])
        elif resolution == ConflictResolution.MERGE_ARRAYS:
            return self._merge_arrays_or_objects(first_value, second_value, path)
        else:
            return second_value  # Default to keep_last
    
    def _merge_arrays_or_objects(self, first_value: Any, second_value: Any, path: str) -> Any:
        """Merge arrays or objects when using MERGE_ARRAYS strategy"""
        
        if isinstance(first_value, list) and isinstance(second_value, list):
            return self._merge_arrays(first_value, second_value, path)
        elif isinstance(first_value, dict) and isinstance(second_value, dict):
            return self._merge_objects(first_value, second_value, path)
        else:
            # Can't merge different types, keep second value
            return second_value
    
    def _merge_arrays(self, first_list: List[Any], second_list: List[Any], path: str) -> List[Any]:
        """Merge two arrays based on their content type"""
        
        # If arrays contain objects with IDs, merge by ID
        if (first_list and isinstance(first_list[0], dict) and "id" in first_list[0] and
            second_list and isinstance(second_list[0], dict) and "id" in second_list[0]):
            return self._merge_arrays_by_id(first_list, second_list, path)
        
        # For menu items, try to merge by position or type
        if path.endswith(".items") and first_list and isinstance(first_list[0], dict):
            return self._merge_menu_items(first_list, second_list, path)
        
        # For widget arrays, merge by position
        if path.endswith(".widgets") and first_list and isinstance(first_list[0], dict):
            return self._merge_widgets(first_list, second_list, path)
        
        # Default: combine arrays and remove duplicates
        combined = first_list + second_list
        return list(dict.fromkeys(combined)) if all(isinstance(x, (str, int, float)) for x in combined) else combined
    
    def _merge_arrays_by_id(self, first_list: List[Dict[str, Any]], second_list: List[Dict[str, Any]], path: str) -> List[Dict[str, Any]]:
        """Merge arrays of objects by their ID field"""
        merged_dict = {}
        
        # Add all items from first list
        for item in first_list:
            if "id" in item:
                merged_dict[item["id"]] = item.copy()
        
        # Merge items from second list
        for item in second_list:
            if "id" in item:
                item_id = item["id"]
                if item_id in merged_dict:
                    # Merge the objects
                    merged_dict[item_id] = self._merge_objects(
                        merged_dict[item_id], item, f"{path}[{item_id}]"
                    )
                else:
                    merged_dict[item_id] = item.copy()
        
        return list(merged_dict.values())
    
    def _merge_menu_items(self, first_list: List[Dict[str, Any]], second_list: List[Dict[str, Any]], path: str) -> List[Dict[str, Any]]:
        """Merge menu item arrays"""
        merged_dict = {}
        
        # Use ID if available, otherwise use label as key
        def get_key(item):
            return item.get("id") or item.get("label", str(hash(str(item))))
        
        # Add all items from first list
        for item in first_list:
            key = get_key(item)
            merged_dict[key] = item.copy()
        
        # Merge items from second list
        for item in second_list:
            key = get_key(item)
            if key in merged_dict:
                merged_dict[key] = self._merge_objects(
                    merged_dict[key], item, f"{path}[{key}]"
                )
            else:
                merged_dict[key] = item.copy()
        
        return list(merged_dict.values())
    
    def _merge_widgets(self, first_list: List[Dict[str, Any]], second_list: List[Dict[str, Any]], path: str) -> List[Dict[str, Any]]:
        """Merge widget arrays by position or ID"""
        merged_dict = {}
        
        def get_widget_key(widget):
            if "id" in widget:
                return f"id:{widget['id']}"
            elif "position" in widget:
                pos = widget["position"]
                return f"pos:{pos.get('x', 0)}:{pos.get('y', 0)}"
            else:
                return f"widget:{hash(str(widget))}"
        
        # Add all widgets from first list
        for widget in first_list:
            key = get_widget_key(widget)
            merged_dict[key] = widget.copy()
        
        # Merge widgets from second list
        for widget in second_list:
            key = get_widget_key(widget)
            if key in merged_dict:
                merged_dict[key] = self._merge_objects(
                    merged_dict[key], widget, f"{path}[{key}]"
                )
            else:
                merged_dict[key] = widget.copy()
        
        return list(merged_dict.values())
    
    def _merge_objects(self, first_obj: Dict[str, Any], second_obj: Dict[str, Any], path: str) -> Dict[str, Any]:
        """Merge two dictionary objects"""
        merged = first_obj.copy()
        
        for key, value in second_obj.items():
            new_path = f"{path}.{key}"
            if key in merged:
                if isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key] = self._merge_objects(merged[key], value, new_path)
                elif isinstance(merged[key], list) and isinstance(value, list):
                    merged[key] = self._merge_arrays(merged[key], value, new_path)
                else:
                    # Conflict - use second value (KEEP_LAST behavior)
                    merged[key] = value
            else:
                merged[key] = value
        
        return merged
    
    def get_merge_conflicts(self) -> List[MergeConflict]:
        """Get list of conflicts from last merge operation"""
        return self.conflicts.copy()
    
    def create_merge_report(self) -> Dict[str, Any]:
        """Create detailed report of last merge operation"""
        return {
            "total_conflicts": len(self.conflicts),
            "conflicts": [
                {
                    "path": conflict.path,
                    "first_value": conflict.first_value,
                    "second_value": conflict.second_value,
                    "resolution": conflict.resolution
                }
                for conflict in self.conflicts
            ],
            "conflict_paths": [conflict.path for conflict in self.conflicts]
        }
    
    def validate_merged_structure(self, merged_structure: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that merged structure is well-formed.
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required top-level keys
        if "menu" not in merged_structure:
            errors.append("Missing required 'menu' section")
        
        # Validate menu structure
        if "menu" in merged_structure:
            menu_errors = self._validate_menu_structure(merged_structure["menu"])
            errors.extend(menu_errors)
        
        # Validate data mappings
        if "data_mappings" in merged_structure:
            mapping_errors = self._validate_data_mappings(merged_structure["data_mappings"])
            errors.extend(mapping_errors)
        
        return len(errors) == 0, errors
    
    def _validate_menu_structure(self, menu: Dict[str, Any]) -> List[str]:
        """Validate menu structure"""
        errors = []
        
        if "items" not in menu:
            errors.append("Menu missing 'items' array")
            return errors
        
        if not isinstance(menu["items"], list):
            errors.append("Menu 'items' must be an array")
            return errors
        
        # Validate each menu item
        for i, item in enumerate(menu["items"]):
            if not isinstance(item, dict):
                errors.append(f"Menu item {i} must be an object")
                continue
            
            if "type" not in item:
                errors.append(f"Menu item {i} missing 'type' field")
            
            if "label" not in item:
                errors.append(f"Menu item {i} missing 'label' field")
            
            # Validate dashboard structure if present
            if item.get("type") == "dashboard" and "dashboard" in item:
                dashboard_errors = self._validate_dashboard_structure(item["dashboard"], f"Menu item {i}")
                errors.extend(dashboard_errors)
        
        return errors
    
    def _validate_dashboard_structure(self, dashboard: Dict[str, Any], context: str) -> List[str]:
        """Validate dashboard structure"""
        errors = []
        
        if "layout" not in dashboard:
            errors.append(f"{context}: Dashboard missing 'layout' configuration")
        
        if "widgets" in dashboard:
            if not isinstance(dashboard["widgets"], list):
                errors.append(f"{context}: Dashboard 'widgets' must be an array")
            else:
                for i, widget in enumerate(dashboard["widgets"]):
                    widget_errors = self._validate_widget_structure(widget, f"{context} widget {i}")
                    errors.extend(widget_errors)
        
        return errors
    
    def _validate_widget_structure(self, widget: Dict[str, Any], context: str) -> List[str]:
        """Validate widget structure"""
        errors = []
        
        required_fields = ["widget_code", "position"]
        for field in required_fields:
            if field not in widget:
                errors.append(f"{context}: Missing required field '{field}'")
        
        # Validate position
        if "position" in widget:
            position = widget["position"]
            if not isinstance(position, dict):
                errors.append(f"{context}: Position must be an object")
            else:
                pos_fields = ["x", "y", "w", "h"]
                for field in pos_fields:
                    if field not in position:
                        errors.append(f"{context}: Position missing '{field}' field")
        
        return errors
    
    def _validate_data_mappings(self, data_mappings: Dict[str, Any]) -> List[str]:
        """Validate data mappings structure"""
        errors = []
        
        if "required_datasets" in data_mappings:
            if not isinstance(data_mappings["required_datasets"], list):
                errors.append("Data mappings 'required_datasets' must be an array")
        
        if "field_mappings" in data_mappings:
            if not isinstance(data_mappings["field_mappings"], dict):
                errors.append("Data mappings 'field_mappings' must be an object")
            else:
                for dataset, fields in data_mappings["field_mappings"].items():
                    if not isinstance(fields, list):
                        errors.append(f"Field mapping for dataset '{dataset}' must be an array")
        
        return errors