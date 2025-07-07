# ABOUTME: Template validator service for validating template structure and data requirements
# ABOUTME: Ensures template integrity, validates widget configurations, and checks data consistency

import uuid
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from ..models.dashboard import DashboardTemplate, DashboardCategory, MenuItemType


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues"""
    ERROR = "error"       # Template cannot be used
    WARNING = "warning"   # Template may have issues
    INFO = "info"         # Informational notes


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    severity: ValidationSeverity
    code: str
    message: str
    path: str
    context: Optional[Dict[str, Any]] = None


class TemplateValidationError(Exception):
    """Exception raised when template validation fails"""
    def __init__(self, message: str, issues: List[ValidationIssue] = None):
        super().__init__(message)
        self.issues = issues or []


class TemplateValidatorService:
    """Service for validating template structure and configuration"""
    
    def __init__(self):
        self.issues: List[ValidationIssue] = []
        self.widget_registry: Set[str] = set()  # Available widget codes
        self.dataset_registry: Set[str] = set()  # Available datasets
    
    def set_widget_registry(self, widget_codes: Set[str]):
        """Set available widget codes for validation"""
        self.widget_registry = widget_codes
    
    def set_dataset_registry(self, dataset_names: Set[str]):
        """Set available dataset names for validation"""
        self.dataset_registry = dataset_names
    
    def validate_template(self, template: DashboardTemplate) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validate complete template structure.
        Returns (is_valid, list_of_issues)
        """
        self.issues = []
        
        # Validate basic template properties
        self._validate_template_metadata(template)
        
        # Validate template structure
        if template.template_structure:
            self._validate_template_structure(template.template_structure)
        else:
            self._add_issue(
                ValidationSeverity.ERROR,
                "MISSING_STRUCTURE",
                "Template structure is missing or empty",
                "template_structure"
            )
        
        # Check for errors that prevent template usage
        has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
        
        return not has_errors, self.issues.copy()
    
    def validate_template_structure(self, structure: Dict[str, Any]) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validate template structure only (without template metadata).
        Useful for validating imported or merged structures.
        """
        self.issues = []
        self._validate_template_structure(structure)
        
        has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
        return not has_errors, self.issues.copy()
    
    def _validate_template_metadata(self, template: DashboardTemplate):
        """Validate template metadata fields"""
        
        # Check required fields
        if not template.code or not template.code.strip():
            self._add_issue(
                ValidationSeverity.ERROR,
                "MISSING_CODE",
                "Template code is required",
                "code"
            )
        
        if not template.name or not template.name.strip():
            self._add_issue(
                ValidationSeverity.ERROR,
                "MISSING_NAME",
                "Template name is required",
                "name"
            )
        
        # Validate version numbers
        if template.major_version < 1:
            self._add_issue(
                ValidationSeverity.ERROR,
                "INVALID_VERSION",
                "Major version must be >= 1",
                "major_version"
            )
        
        if template.minor_version < 0:
            self._add_issue(
                ValidationSeverity.ERROR,
                "INVALID_VERSION",
                "Minor version must be >= 0",
                "minor_version"
            )
        
        if template.patch_version < 0:
            self._add_issue(
                ValidationSeverity.ERROR,
                "INVALID_VERSION",
                "Patch version must be >= 0",
                "patch_version"
            )
        
        # Validate inheritance
        if template.parent_template_id and template.inheritance_type.value == "none":
            self._add_issue(
                ValidationSeverity.WARNING,
                "INHERITANCE_MISMATCH",
                "Template has parent but inheritance type is 'none'",
                "inheritance_type"
            )
        
        # Validate marketplace fields if public
        if template.is_public:
            if not template.description:
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "MISSING_DESCRIPTION",
                    "Public templates should have descriptions",
                    "description"
                )
            
            if not template.screenshot_urls or len(template.screenshot_urls) == 0:
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "MISSING_SCREENSHOTS",
                    "Public templates should have screenshots",
                    "screenshot_urls"
                )
    
    def _validate_template_structure(self, structure: Dict[str, Any]):
        """Validate the template structure JSON"""
        
        # Check top-level structure
        if "menu" not in structure:
            self._add_issue(
                ValidationSeverity.ERROR,
                "MISSING_MENU",
                "Template must have a 'menu' section",
                "menu"
            )
        else:
            self._validate_menu_structure(structure["menu"], "menu")
        
        # Validate data mappings if present
        if "data_mappings" in structure:
            self._validate_data_mappings(structure["data_mappings"], "data_mappings")
        
        # Check for unknown top-level keys
        known_keys = {"menu", "data_mappings", "metadata", "version"}
        unknown_keys = set(structure.keys()) - known_keys
        if unknown_keys:
            self._add_issue(
                ValidationSeverity.WARNING,
                "UNKNOWN_KEYS",
                f"Unknown top-level keys: {', '.join(unknown_keys)}",
                "structure",
                {"unknown_keys": list(unknown_keys)}
            )
    
    def _validate_menu_structure(self, menu: Dict[str, Any], path: str):
        """Validate menu structure"""
        
        if "items" not in menu:
            self._add_issue(
                ValidationSeverity.ERROR,
                "MISSING_MENU_ITEMS",
                "Menu must have 'items' array",
                f"{path}.items"
            )
            return
        
        if not isinstance(menu["items"], list):
            self._add_issue(
                ValidationSeverity.ERROR,
                "INVALID_MENU_ITEMS",
                "Menu 'items' must be an array",
                f"{path}.items"
            )
            return
        
        if len(menu["items"]) == 0:
            self._add_issue(
                ValidationSeverity.WARNING,
                "EMPTY_MENU",
                "Menu has no items",
                f"{path}.items"
            )
        
        # Validate each menu item
        menu_item_ids = set()
        for i, item in enumerate(menu["items"]):
            item_path = f"{path}.items[{i}]"
            self._validate_menu_item(item, item_path, menu_item_ids)
    
    def _validate_menu_item(self, item: Dict[str, Any], path: str, existing_ids: Set[str]):
        """Validate individual menu item"""
        
        if not isinstance(item, dict):
            self._add_issue(
                ValidationSeverity.ERROR,
                "INVALID_MENU_ITEM",
                "Menu item must be an object",
                path
            )
            return
        
        # Check required fields
        required_fields = ["type", "label"]
        for field in required_fields:
            if field not in item:
                self._add_issue(
                    ValidationSeverity.ERROR,
                    "MISSING_MENU_FIELD",
                    f"Menu item missing required field '{field}'",
                    f"{path}.{field}"
                )
        
        # Validate item type
        if "type" in item:
            try:
                MenuItemType(item["type"])
            except ValueError:
                self._add_issue(
                    ValidationSeverity.ERROR,
                    "INVALID_MENU_TYPE",
                    f"Invalid menu item type: {item['type']}",
                    f"{path}.type"
                )
        
        # Check for duplicate IDs
        if "id" in item:
            item_id = item["id"]
            if item_id in existing_ids:
                self._add_issue(
                    ValidationSeverity.ERROR,
                    "DUPLICATE_MENU_ID",
                    f"Duplicate menu item ID: {item_id}",
                    f"{path}.id"
                )
            else:
                existing_ids.add(item_id)
        
        # Validate dashboard structure if it's a dashboard item
        if item.get("type") == "dashboard" and "dashboard" in item:
            self._validate_dashboard_structure(item["dashboard"], f"{path}.dashboard")
        
        # Validate external links
        if item.get("type") == "external" and "url" in item:
            url = item["url"]
            if not url.startswith(("http://", "https://")):
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "INVALID_URL",
                    "External link should use http:// or https://",
                    f"{path}.url"
                )
    
    def _validate_dashboard_structure(self, dashboard: Dict[str, Any], path: str):
        """Validate dashboard structure"""
        
        # Check layout configuration
        if "layout" not in dashboard:
            self._add_issue(
                ValidationSeverity.ERROR,
                "MISSING_LAYOUT",
                "Dashboard must have 'layout' configuration",
                f"{path}.layout"
            )
        else:
            self._validate_layout_structure(dashboard["layout"], f"{path}.layout")
        
        # Validate widgets
        if "widgets" in dashboard:
            if not isinstance(dashboard["widgets"], list):
                self._add_issue(
                    ValidationSeverity.ERROR,
                    "INVALID_WIDGETS",
                    "Dashboard 'widgets' must be an array",
                    f"{path}.widgets"
                )
            else:
                self._validate_widgets(dashboard["widgets"], f"{path}.widgets")
        else:
            self._add_issue(
                ValidationSeverity.WARNING,
                "NO_WIDGETS",
                "Dashboard has no widgets",
                f"{path}.widgets"
            )
    
    def _validate_layout_structure(self, layout: Dict[str, Any], path: str):
        """Validate layout configuration"""
        
        if not isinstance(layout, dict):
            self._add_issue(
                ValidationSeverity.ERROR,
                "INVALID_LAYOUT",
                "Layout must be an object",
                path
            )
            return
        
        # Check layout type
        if "type" not in layout:
            self._add_issue(
                ValidationSeverity.WARNING,
                "MISSING_LAYOUT_TYPE",
                "Layout missing 'type' field, assuming 'grid'",
                f"{path}.type"
            )
        
        # Validate grid layout specifics
        if layout.get("type") == "grid":
            if "columns" not in layout:
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "MISSING_GRID_COLUMNS",
                    "Grid layout missing 'columns', using default",
                    f"{path}.columns"
                )
            elif not isinstance(layout["columns"], int) or layout["columns"] <= 0:
                self._add_issue(
                    ValidationSeverity.ERROR,
                    "INVALID_GRID_COLUMNS",
                    "Grid columns must be a positive integer",
                    f"{path}.columns"
                )
    
    def _validate_widgets(self, widgets: List[Dict[str, Any]], path: str):
        """Validate widget array"""
        
        widget_positions = set()
        widget_ids = set()
        
        for i, widget in enumerate(widgets):
            widget_path = f"{path}[{i}]"
            self._validate_widget(widget, widget_path, widget_positions, widget_ids)
    
    def _validate_widget(self, widget: Dict[str, Any], path: str, positions: Set[str], widget_ids: Set[str]):
        """Validate individual widget"""
        
        if not isinstance(widget, dict):
            self._add_issue(
                ValidationSeverity.ERROR,
                "INVALID_WIDGET",
                "Widget must be an object",
                path
            )
            return
        
        # Check required fields
        required_fields = ["widget_code", "position"]
        for field in required_fields:
            if field not in widget:
                self._add_issue(
                    ValidationSeverity.ERROR,
                    "MISSING_WIDGET_FIELD",
                    f"Widget missing required field '{field}'",
                    f"{path}.{field}"
                )
        
        # Validate widget code against registry
        if "widget_code" in widget and self.widget_registry:
            widget_code = widget["widget_code"]
            if widget_code not in self.widget_registry:
                self._add_issue(
                    ValidationSeverity.ERROR,
                    "UNKNOWN_WIDGET_CODE",
                    f"Unknown widget code: {widget_code}",
                    f"{path}.widget_code"
                )
        
        # Check for duplicate widget IDs
        if "id" in widget:
            widget_id = widget["id"]
            if widget_id in widget_ids:
                self._add_issue(
                    ValidationSeverity.ERROR,
                    "DUPLICATE_WIDGET_ID",
                    f"Duplicate widget ID: {widget_id}",
                    f"{path}.id"
                )
            else:
                widget_ids.add(widget_id)
        
        # Validate position
        if "position" in widget:
            self._validate_widget_position(widget["position"], f"{path}.position", positions)
        
        # Validate data requirements
        if "data_requirements" in widget:
            self._validate_data_requirements(widget["data_requirements"], f"{path}.data_requirements")
        
        # Validate instance configuration
        if "instance_config" in widget:
            self._validate_instance_config(widget["instance_config"], f"{path}.instance_config")
    
    def _validate_widget_position(self, position: Dict[str, Any], path: str, existing_positions: Set[str]):
        """Validate widget position"""
        
        if not isinstance(position, dict):
            self._add_issue(
                ValidationSeverity.ERROR,
                "INVALID_POSITION",
                "Widget position must be an object",
                path
            )
            return
        
        # Check required position fields
        required_fields = ["x", "y", "w", "h"]
        for field in required_fields:
            if field not in position:
                self._add_issue(
                    ValidationSeverity.ERROR,
                    "MISSING_POSITION_FIELD",
                    f"Position missing required field '{field}'",
                    f"{path}.{field}"
                )
            elif not isinstance(position[field], (int, float)) or position[field] < 0:
                self._add_issue(
                    ValidationSeverity.ERROR,
                    "INVALID_POSITION_VALUE",
                    f"Position '{field}' must be a non-negative number",
                    f"{path}.{field}"
                )
        
        # Check for overlapping positions (simplified check)
        if all(field in position for field in required_fields):
            pos_key = f"{position['x']},{position['y']},{position['w']},{position['h']}"
            if pos_key in existing_positions:
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "OVERLAPPING_WIDGETS",
                    "Widget position may overlap with another widget",
                    path
                )
            else:
                existing_positions.add(pos_key)
    
    def _validate_data_requirements(self, data_req: Dict[str, Any], path: str):
        """Validate widget data requirements"""
        
        if not isinstance(data_req, dict):
            self._add_issue(
                ValidationSeverity.ERROR,
                "INVALID_DATA_REQUIREMENTS",
                "Data requirements must be an object",
                path
            )
            return
        
        # Check dataset reference
        if "dataset" in data_req and self.dataset_registry:
            dataset = data_req["dataset"]
            if dataset not in self.dataset_registry:
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "UNKNOWN_DATASET",
                    f"Referenced dataset may not be available: {dataset}",
                    f"{path}.dataset"
                )
        
        # Validate fields array
        if "fields" in data_req:
            if not isinstance(data_req["fields"], list):
                self._add_issue(
                    ValidationSeverity.ERROR,
                    "INVALID_FIELDS",
                    "Data requirements 'fields' must be an array",
                    f"{path}.fields"
                )
        
        # Validate calculation type
        if "calculation" in data_req:
            valid_calculations = ["count", "sum", "avg", "min", "max", "distinct", "custom"]
            if data_req["calculation"] not in valid_calculations:
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "UNKNOWN_CALCULATION",
                    f"Unknown calculation type: {data_req['calculation']}",
                    f"{path}.calculation"
                )
    
    def _validate_instance_config(self, config: Dict[str, Any], path: str):
        """Validate widget instance configuration"""
        
        if not isinstance(config, dict):
            self._add_issue(
                ValidationSeverity.ERROR,
                "INVALID_INSTANCE_CONFIG",
                "Instance config must be an object",
                path
            )
            return
        
        # Basic validation - check for common configuration issues
        if "title" in config and not isinstance(config["title"], str):
            self._add_issue(
                ValidationSeverity.WARNING,
                "INVALID_TITLE",
                "Widget title should be a string",
                f"{path}.title"
            )
    
    def _validate_data_mappings(self, mappings: Dict[str, Any], path: str):
        """Validate data mappings structure"""
        
        if not isinstance(mappings, dict):
            self._add_issue(
                ValidationSeverity.ERROR,
                "INVALID_DATA_MAPPINGS",
                "Data mappings must be an object",
                path
            )
            return
        
        # Validate required datasets
        if "required_datasets" in mappings:
            if not isinstance(mappings["required_datasets"], list):
                self._add_issue(
                    ValidationSeverity.ERROR,
                    "INVALID_REQUIRED_DATASETS",
                    "Required datasets must be an array",
                    f"{path}.required_datasets"
                )
            elif self.dataset_registry:
                # Check if datasets are available
                for dataset in mappings["required_datasets"]:
                    if dataset not in self.dataset_registry:
                        self._add_issue(
                            ValidationSeverity.WARNING,
                            "UNKNOWN_REQUIRED_DATASET",
                            f"Required dataset may not be available: {dataset}",
                            f"{path}.required_datasets"
                        )
        
        # Validate field mappings
        if "field_mappings" in mappings:
            field_mappings = mappings["field_mappings"]
            if not isinstance(field_mappings, dict):
                self._add_issue(
                    ValidationSeverity.ERROR,
                    "INVALID_FIELD_MAPPINGS",
                    "Field mappings must be an object",
                    f"{path}.field_mappings"
                )
            else:
                for dataset, fields in field_mappings.items():
                    if not isinstance(fields, list):
                        self._add_issue(
                            ValidationSeverity.ERROR,
                            "INVALID_FIELD_LIST",
                            f"Field list for dataset '{dataset}' must be an array",
                            f"{path}.field_mappings.{dataset}"
                        )
    
    def _add_issue(self, severity: ValidationSeverity, code: str, message: str, path: str, context: Optional[Dict[str, Any]] = None):
        """Add validation issue to the list"""
        issue = ValidationIssue(
            severity=severity,
            code=code,
            message=message,
            path=path,
            context=context
        )
        self.issues.append(issue)
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results"""
        error_count = sum(1 for issue in self.issues if issue.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for issue in self.issues if issue.severity == ValidationSeverity.WARNING)
        info_count = sum(1 for issue in self.issues if issue.severity == ValidationSeverity.INFO)
        
        return {
            "total_issues": len(self.issues),
            "errors": error_count,
            "warnings": warning_count,
            "info": info_count,
            "is_valid": error_count == 0,
            "issues": [
                {
                    "severity": issue.severity,
                    "code": issue.code,
                    "message": issue.message,
                    "path": issue.path,
                    "context": issue.context
                }
                for issue in self.issues
            ]
        }