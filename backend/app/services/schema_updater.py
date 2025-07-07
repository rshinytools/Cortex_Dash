# ABOUTME: Schema updater service for updating template schemas and handling schema evolution
# ABOUTME: Manages template schema versioning, validation rules, and automated schema migrations

import uuid
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json
import jsonschema
from jsonschema import validate, ValidationError

from ..models.dashboard import DashboardTemplate


class SchemaChangeType(str, Enum):
    """Types of schema changes"""
    FIELD_ADDED = "field_added"
    FIELD_REMOVED = "field_removed"
    FIELD_RENAMED = "field_renamed"
    FIELD_TYPE_CHANGED = "field_type_changed"
    VALIDATION_RULE_ADDED = "validation_rule_added"
    VALIDATION_RULE_REMOVED = "validation_rule_removed"
    STRUCTURE_REORGANIZED = "structure_reorganized"


@dataclass
class SchemaChange:
    """Represents a change in schema"""
    change_type: SchemaChangeType
    path: str
    old_value: Any
    new_value: Any
    description: str
    is_breaking: bool = False


@dataclass
class SchemaVersion:
    """Represents a version of the template schema"""
    version: str
    schema: Dict[str, Any]
    changes: List[SchemaChange]
    created_at: datetime
    description: str


class SchemaUpdateError(Exception):
    """Exception raised during schema updates"""
    pass


class SchemaUpdaterService:
    """Service for managing template schema evolution"""
    
    def __init__(self):
        self.schema_versions: Dict[str, SchemaVersion] = {}
        self._initialize_default_schemas()
    
    def _initialize_default_schemas(self):
        """Initialize default schema versions"""
        
        # Schema version 1.0.0 - Basic template structure
        v1_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "menu": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "type": {"type": "string", "enum": ["dashboard", "static_page", "external", "group", "divider"]},
                                    "label": {"type": "string"},
                                    "icon": {"type": "string"},
                                    "dashboard": {
                                        "type": "object",
                                        "properties": {
                                            "layout": {
                                                "type": "object",
                                                "properties": {
                                                    "type": {"type": "string", "enum": ["grid"]},
                                                    "columns": {"type": "integer", "minimum": 1},
                                                    "rows": {"type": "integer", "minimum": 1}
                                                },
                                                "required": ["type", "columns"]
                                            },
                                            "widgets": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "widget_code": {"type": "string"},
                                                        "position": {
                                                            "type": "object",
                                                            "properties": {
                                                                "x": {"type": "number", "minimum": 0},
                                                                "y": {"type": "number", "minimum": 0},
                                                                "w": {"type": "number", "minimum": 1},
                                                                "h": {"type": "number", "minimum": 1}
                                                            },
                                                            "required": ["x", "y", "w", "h"]
                                                        },
                                                        "instance_config": {"type": "object"},
                                                        "data_requirements": {
                                                            "type": "object",
                                                            "properties": {
                                                                "dataset": {"type": "string"},
                                                                "fields": {"type": "array", "items": {"type": "string"}},
                                                                "calculation": {"type": "string"}
                                                            }
                                                        }
                                                    },
                                                    "required": ["widget_code", "position"]
                                                }
                                            }
                                        },
                                        "required": ["layout"]
                                    }
                                },
                                "required": ["type", "label"]
                            }
                        }
                    },
                    "required": ["items"]
                },
                "data_mappings": {
                    "type": "object",
                    "properties": {
                        "required_datasets": {"type": "array", "items": {"type": "string"}},
                        "field_mappings": {
                            "type": "object",
                            "additionalProperties": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "required": ["menu"]
        }
        
        self.register_schema_version("1.0.0", v1_schema, "Initial template schema")
        
        # Schema version 1.1.0 - Add theme support
        v1_1_schema = self._create_v1_1_schema(v1_schema)
        self.register_schema_version("1.1.0", v1_1_schema, "Added theme support to widgets")
        
        # Schema version 2.0.0 - Responsive layout
        v2_schema = self._create_v2_schema(v1_1_schema)
        self.register_schema_version("2.0.0", v2_schema, "Added responsive layout support")
    
    def register_schema_version(self, version: str, schema: Dict[str, Any], description: str):
        """Register a new schema version"""
        changes = []
        
        # Compare with previous version to detect changes
        if self.schema_versions:
            latest_version = max(self.schema_versions.keys(), key=lambda v: tuple(map(int, v.split('.'))))
            previous_schema = self.schema_versions[latest_version].schema
            changes = self._detect_schema_changes(previous_schema, schema)
        
        schema_version = SchemaVersion(
            version=version,
            schema=schema,
            changes=changes,
            created_at=datetime.utcnow(),
            description=description
        )
        
        self.schema_versions[version] = schema_version
    
    def validate_against_schema(self, template_structure: Dict[str, Any], schema_version: str = None) -> Tuple[bool, List[str]]:
        """
        Validate template structure against schema.
        
        Args:
            template_structure: Template structure to validate
            schema_version: Schema version to validate against (latest if None)
            
        Returns:
            (is_valid, list_of_errors)
        """
        if schema_version is None:
            schema_version = self.get_latest_schema_version()
        
        if schema_version not in self.schema_versions:
            return False, [f"Schema version {schema_version} not found"]
        
        schema = self.schema_versions[schema_version].schema
        
        try:
            validate(instance=template_structure, schema=schema)
            return True, []
        except ValidationError as e:
            return False, [str(e)]
        except Exception as e:
            return False, [f"Schema validation error: {str(e)}"]
    
    def get_latest_schema_version(self) -> str:
        """Get the latest schema version"""
        if not self.schema_versions:
            return "1.0.0"
        
        return max(self.schema_versions.keys(), key=lambda v: tuple(map(int, v.split('.'))))
    
    def get_schema_for_version(self, version: str) -> Optional[Dict[str, Any]]:
        """Get schema for specific version"""
        if version in self.schema_versions:
            return self.schema_versions[version].schema
        return None
    
    def upgrade_template_to_schema(self, template_structure: Dict[str, Any], target_schema_version: str) -> Tuple[Dict[str, Any], List[str]]:
        """
        Upgrade template structure to match target schema version.
        
        Args:
            template_structure: Current template structure
            target_schema_version: Target schema version
            
        Returns:
            (upgraded_structure, list_of_changes_made)
        """
        if target_schema_version not in self.schema_versions:
            raise SchemaUpdateError(f"Schema version {target_schema_version} not found")
        
        # Detect current schema version
        current_version = self._detect_template_schema_version(template_structure)
        
        if current_version == target_schema_version:
            return template_structure, ["No changes needed - already at target schema version"]
        
        # Apply schema upgrades step by step
        upgraded_structure = template_structure.copy()
        changes_made = []
        
        # Get ordered list of versions to upgrade through
        version_path = self._get_upgrade_path(current_version, target_schema_version)
        
        for from_version, to_version in zip(version_path[:-1], version_path[1:]):
            upgraded_structure, step_changes = self._apply_schema_upgrade(
                upgraded_structure, from_version, to_version
            )
            changes_made.extend(step_changes)
        
        return upgraded_structure, changes_made
    
    def _detect_template_schema_version(self, template_structure: Dict[str, Any]) -> str:
        """Detect which schema version a template structure matches"""
        
        # Check each schema version from newest to oldest
        versions = sorted(self.schema_versions.keys(), key=lambda v: tuple(map(int, v.split('.'))), reverse=True)
        
        for version in versions:
            is_valid, _ = self.validate_against_schema(template_structure, version)
            if is_valid:
                return version
        
        # If no exact match, try to infer based on structure
        return self._infer_schema_version(template_structure)
    
    def _infer_schema_version(self, template_structure: Dict[str, Any]) -> str:
        """Infer schema version based on structure characteristics"""
        
        # Check for v2.0 features (responsive layout)
        if self._has_responsive_layout(template_structure):
            return "2.0.0"
        
        # Check for v1.1 features (theme support)
        if self._has_theme_support(template_structure):
            return "1.1.0"
        
        # Default to v1.0
        return "1.0.0"
    
    def _has_responsive_layout(self, structure: Dict[str, Any]) -> bool:
        """Check if structure has responsive layout features"""
        if "menu" not in structure:
            return False
        
        for item in structure["menu"].get("items", []):
            if item.get("type") == "dashboard" and "dashboard" in item:
                layout = item["dashboard"].get("layout", {})
                if layout.get("type") == "responsive_grid" and "breakpoints" in layout:
                    return True
        
        return False
    
    def _has_theme_support(self, structure: Dict[str, Any]) -> bool:
        """Check if structure has theme support features"""
        if "menu" not in structure:
            return False
        
        for item in structure["menu"].get("items", []):
            if item.get("type") == "dashboard" and "dashboard" in item:
                for widget in item["dashboard"].get("widgets", []):
                    instance_config = widget.get("instance_config", {})
                    if "theme" in instance_config:
                        return True
        
        return False
    
    def _get_upgrade_path(self, from_version: str, to_version: str) -> List[str]:
        """Get ordered list of versions to upgrade through"""
        
        # For now, implement simple sequential upgrade
        # In production, you might want more sophisticated path finding
        all_versions = sorted(self.schema_versions.keys(), key=lambda v: tuple(map(int, v.split('.'))))
        
        from_idx = all_versions.index(from_version)
        to_idx = all_versions.index(to_version)
        
        if from_idx > to_idx:
            raise SchemaUpdateError("Downgrade not supported")
        
        return all_versions[from_idx:to_idx + 1]
    
    def _apply_schema_upgrade(self, structure: Dict[str, Any], from_version: str, to_version: str) -> Tuple[Dict[str, Any], List[str]]:
        """Apply schema upgrade from one version to the next"""
        
        upgrade_path = f"{from_version}->{to_version}"
        changes_made = []
        
        # Apply version-specific upgrades
        if upgrade_path == "1.0.0->1.1.0":
            structure, step_changes = self._upgrade_1_0_to_1_1(structure)
            changes_made.extend(step_changes)
        elif upgrade_path == "1.1.0->2.0.0":
            structure, step_changes = self._upgrade_1_1_to_2_0(structure)
            changes_made.extend(step_changes)
        
        return structure, changes_made
    
    def _upgrade_1_0_to_1_1(self, structure: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """Upgrade from schema 1.0.0 to 1.1.0 (add theme support)"""
        changes = []
        
        if "menu" in structure:
            for item in structure["menu"].get("items", []):
                if item.get("type") == "dashboard" and "dashboard" in item:
                    for widget in item["dashboard"].get("widgets", []):
                        if "instance_config" not in widget:
                            widget["instance_config"] = {}
                        
                        # Add default theme if not present
                        if "theme" not in widget["instance_config"]:
                            widget["instance_config"]["theme"] = {
                                "primary_color": "#3b82f6",
                                "background_color": "#ffffff",
                                "text_color": "#1f2937"
                            }
                            changes.append(f"Added default theme to widget {widget.get('widget_code', 'unknown')}")
        
        return structure, changes
    
    def _upgrade_1_1_to_2_0(self, structure: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """Upgrade from schema 1.1.0 to 2.0.0 (responsive layout)"""
        changes = []
        
        if "menu" in structure:
            for item in structure["menu"].get("items", []):
                if item.get("type") == "dashboard" and "dashboard" in item:
                    dashboard = item["dashboard"]
                    layout = dashboard.get("layout", {})
                    
                    # Convert grid layout to responsive grid
                    if layout.get("type") == "grid":
                        old_columns = layout.get("columns", 12)
                        dashboard["layout"] = {
                            "type": "responsive_grid",
                            "breakpoints": {
                                "lg": {"columns": old_columns, "row_height": 60},
                                "md": {"columns": max(6, old_columns // 2), "row_height": 60},
                                "sm": {"columns": 4, "row_height": 60},
                                "xs": {"columns": 2, "row_height": 60}
                            }
                        }
                        changes.append(f"Converted grid layout to responsive grid ({old_columns} columns)")
                    
                    # Convert widget positions to responsive
                    for widget in dashboard.get("widgets", []):
                        position = widget.get("position", {})
                        if "x" in position and isinstance(position, dict) and "lg" not in position:
                            # Convert old position to responsive
                            widget["position"] = {
                                "lg": {
                                    "x": position.get("x", 0),
                                    "y": position.get("y", 0),
                                    "w": position.get("w", 3),
                                    "h": position.get("h", 2)
                                },
                                "md": {
                                    "x": min(position.get("x", 0), 4),
                                    "y": position.get("y", 0),
                                    "w": min(position.get("w", 3), 6),
                                    "h": position.get("h", 2)
                                },
                                "sm": {
                                    "x": 0,
                                    "y": position.get("y", 0) * 2,
                                    "w": 4,
                                    "h": position.get("h", 2)
                                },
                                "xs": {
                                    "x": 0,
                                    "y": position.get("y", 0) * 3,
                                    "w": 2,
                                    "h": position.get("h", 2)
                                }
                            }
                            changes.append(f"Converted widget position to responsive layout")
        
        return structure, changes
    
    def _detect_schema_changes(self, old_schema: Dict[str, Any], new_schema: Dict[str, Any]) -> List[SchemaChange]:
        """Detect changes between two schemas"""
        changes = []
        
        # This is a simplified implementation
        # In production, you'd want more sophisticated schema diffing
        
        # Check for added/removed required fields
        old_required = self._get_required_fields(old_schema)
        new_required = self._get_required_fields(new_schema)
        
        for field in new_required - old_required:
            changes.append(SchemaChange(
                change_type=SchemaChangeType.VALIDATION_RULE_ADDED,
                path=field,
                old_value=None,
                new_value="required",
                description=f"Field '{field}' is now required",
                is_breaking=True
            ))
        
        for field in old_required - new_required:
            changes.append(SchemaChange(
                change_type=SchemaChangeType.VALIDATION_RULE_REMOVED,
                path=field,
                old_value="required",
                new_value=None,
                description=f"Field '{field}' is no longer required",
                is_breaking=False
            ))
        
        return changes
    
    def _get_required_fields(self, schema: Dict[str, Any], path: str = "") -> Set[str]:
        """Get all required fields from schema"""
        required_fields = set()
        
        if isinstance(schema, dict):
            if "required" in schema and isinstance(schema["required"], list):
                for field in schema["required"]:
                    field_path = f"{path}.{field}" if path else field
                    required_fields.add(field_path)
            
            if "properties" in schema:
                for prop, prop_schema in schema["properties"].items():
                    prop_path = f"{path}.{prop}" if path else prop
                    required_fields.update(self._get_required_fields(prop_schema, prop_path))
        
        return required_fields
    
    def _create_v1_1_schema(self, base_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create v1.1 schema with theme support"""
        schema = json.loads(json.dumps(base_schema))  # Deep copy
        
        # Add theme properties to widget instance_config
        widget_schema = schema["properties"]["menu"]["properties"]["items"]["items"]["properties"]["dashboard"]["properties"]["widgets"]["items"]
        
        if "properties" in widget_schema and "instance_config" in widget_schema["properties"]:
            widget_schema["properties"]["instance_config"]["properties"] = {
                "theme": {
                    "type": "object",
                    "properties": {
                        "primary_color": {"type": "string"},
                        "background_color": {"type": "string"},
                        "text_color": {"type": "string"}
                    }
                }
            }
        
        return schema
    
    def _create_v2_schema(self, base_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create v2.0 schema with responsive layout"""
        schema = json.loads(json.dumps(base_schema))  # Deep copy
        
        # Update layout schema to support responsive grid
        layout_schema = schema["properties"]["menu"]["properties"]["items"]["items"]["properties"]["dashboard"]["properties"]["layout"]
        layout_schema["properties"]["type"]["enum"].append("responsive_grid")
        layout_schema["properties"]["breakpoints"] = {
            "type": "object",
            "properties": {
                "lg": {"type": "object"},
                "md": {"type": "object"},
                "sm": {"type": "object"},
                "xs": {"type": "object"}
            }
        }
        
        # Update widget position schema to support responsive positions
        position_schema = schema["properties"]["menu"]["properties"]["items"]["items"]["properties"]["dashboard"]["properties"]["widgets"]["items"]["properties"]["position"]
        position_schema["oneOf"] = [
            {
                "type": "object",
                "properties": {
                    "x": {"type": "number"},
                    "y": {"type": "number"},
                    "w": {"type": "number"},
                    "h": {"type": "number"}
                },
                "required": ["x", "y", "w", "h"]
            },
            {
                "type": "object",
                "properties": {
                    "lg": {"type": "object"},
                    "md": {"type": "object"},
                    "sm": {"type": "object"},
                    "xs": {"type": "object"}
                }
            }
        ]
        
        return schema
    
    def get_schema_changes_summary(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """Get summary of changes between schema versions"""
        
        if from_version not in self.schema_versions or to_version not in self.schema_versions:
            return {"error": "One or both schema versions not found"}
        
        # Get all changes in the upgrade path
        version_path = self._get_upgrade_path(from_version, to_version)
        all_changes = []
        
        for i in range(len(version_path) - 1):
            version = version_path[i + 1]
            version_changes = self.schema_versions[version].changes
            all_changes.extend(version_changes)
        
        # Categorize changes
        breaking_changes = [c for c in all_changes if c.is_breaking]
        non_breaking_changes = [c for c in all_changes if not c.is_breaking]
        
        return {
            "from_version": from_version,
            "to_version": to_version,
            "total_changes": len(all_changes),
            "breaking_changes": len(breaking_changes),
            "non_breaking_changes": len(non_breaking_changes),
            "changes": [
                {
                    "type": change.change_type,
                    "path": change.path,
                    "description": change.description,
                    "is_breaking": change.is_breaking
                }
                for change in all_changes
            ]
        }