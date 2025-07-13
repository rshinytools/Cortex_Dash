# ABOUTME: Service for detecting and categorizing changes in dashboard templates
# ABOUTME: Automatically determines change severity (major, minor, patch) based on modifications

from typing import Dict, List, Any, Tuple, Optional
from enum import Enum
import hashlib
import json
from deepdiff import DeepDiff
import logging

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Change severity levels following semantic versioning"""
    MAJOR = "major"  # Breaking changes
    MINOR = "minor"  # New features, backward compatible
    PATCH = "patch"  # Bug fixes, minor updates


class ChangeCategory(str, Enum):
    """Categories of changes for better tracking"""
    STRUCTURE = "structure"
    WIDGET = "widget"
    DATA_SOURCE = "data_source"
    STYLING = "styling"
    METADATA = "metadata"
    MENU = "menu"
    PERMISSION = "permission"


class TemplateChangeDetector:
    """Detects and categorizes changes between template versions"""
    
    # Define what constitutes each type of change
    MAJOR_CHANGE_PATTERNS = {
        "root['menu_structure']['items']": "Menu structure fundamentally changed",
        "root['dashboardTemplates'][*]['widgets']": "Widget structure changed",
        "root['data_requirements']": "Data requirements modified",
        "type_changes": "Data type of critical field changed",
        "removed": "Required elements removed"
    }
    
    MINOR_CHANGE_PATTERNS = {
        "root['menu_structure']['items'][*]['children']": "Submenu items added",
        "root['dashboardTemplates'][*]['widgets'][*]": "New widget added",
        "root['settings']": "New settings added",
        "added": "New optional elements added"
    }
    
    PATCH_CHANGE_PATTERNS = {
        "root['name']": "Template name updated",
        "root['description']": "Description modified",
        "root['dashboardTemplates'][*]['widgets'][*]['config']": "Widget configuration tweaked",
        "root['theme']": "Theme/styling changes",
        "values_changed": "Values updated without structural changes"
    }
    
    def __init__(self):
        self.changes: List[Dict[str, Any]] = []
        
    def detect_changes(
        self, 
        old_template: Dict[str, Any], 
        new_template: Dict[str, Any]
    ) -> Tuple[ChangeType, List[Dict[str, Any]]]:
        """
        Detect changes between two template versions
        
        Returns:
            Tuple of (change_type, list_of_changes)
        """
        self.changes = []
        
        # Deep comparison
        diff = DeepDiff(
            old_template,
            new_template,
            ignore_order=True,
            report_repetition=True,
            verbose_level=2
        )
        
        # Analyze each type of change
        change_type = ChangeType.PATCH  # Default to patch
        
        # Check for removals (potential breaking changes)
        if 'dictionary_item_removed' in diff:
            for removed_item in diff['dictionary_item_removed']:
                change_info = self._analyze_removal(removed_item, old_template)
                if change_info['severity'] == ChangeType.MAJOR:
                    change_type = ChangeType.MAJOR
                self.changes.append(change_info)
        
        # Check for type changes (potential breaking changes)
        if 'type_changes' in diff:
            for path, type_change in diff['type_changes'].items():
                change_info = self._analyze_type_change(path, type_change)
                if change_info['severity'] == ChangeType.MAJOR:
                    change_type = ChangeType.MAJOR
                self.changes.append(change_info)
        
        # Check for additions (new features)
        if 'dictionary_item_added' in diff:
            for added_item in diff['dictionary_item_added']:
                change_info = self._analyze_addition(added_item, new_template)
                if change_info['severity'] == ChangeType.MINOR and change_type != ChangeType.MAJOR:
                    change_type = ChangeType.MINOR
                self.changes.append(change_info)
        
        # Check for value changes (updates)
        if 'values_changed' in diff:
            for path, value_change in diff['values_changed'].items():
                change_info = self._analyze_value_change(path, value_change)
                self.changes.append(change_info)
        
        # Generate comparison hash
        comparison_hash = self._generate_hash(new_template)
        
        return change_type, self.changes
    
    def _analyze_removal(self, path: str, old_template: Dict) -> Dict[str, Any]:
        """Analyze a removed element to determine severity"""
        # Check if it's a critical path
        is_critical = any(pattern in path for pattern in [
            "menu_structure", "widgets", "data_requirements"
        ])
        
        return {
            "type": "removal",
            "path": path,
            "severity": ChangeType.MAJOR if is_critical else ChangeType.MINOR,
            "category": self._categorize_path(path),
            "description": f"Removed: {self._extract_element_name(path)}",
            "breaking": is_critical
        }
    
    def _analyze_addition(self, path: str, new_template: Dict) -> Dict[str, Any]:
        """Analyze an added element"""
        is_feature = "widgets" in path or "menu" in path
        
        return {
            "type": "addition",
            "path": path,
            "severity": ChangeType.MINOR if is_feature else ChangeType.PATCH,
            "category": self._categorize_path(path),
            "description": f"Added: {self._extract_element_name(path)}",
            "breaking": False
        }
    
    def _analyze_type_change(self, path: str, type_change: Dict) -> Dict[str, Any]:
        """Analyze a type change"""
        return {
            "type": "type_change",
            "path": path,
            "severity": ChangeType.MAJOR,
            "category": self._categorize_path(path),
            "description": f"Type changed from {type_change['old_type']} to {type_change['new_type']}",
            "breaking": True,
            "old_type": str(type_change.get('old_type', 'unknown')),
            "new_type": str(type_change.get('new_type', 'unknown'))
        }
    
    def _analyze_value_change(self, path: str, value_change: Dict) -> Dict[str, Any]:
        """Analyze a value change"""
        # Determine if it's just a minor update
        is_styling = "theme" in path or "style" in path or "color" in path
        is_text = "name" in path or "description" in path or "label" in path
        
        return {
            "type": "value_change",
            "path": path,
            "severity": ChangeType.PATCH,
            "category": self._categorize_path(path),
            "description": f"Updated: {self._extract_element_name(path)}",
            "breaking": False,
            "old_value": str(value_change.get('old_value', ''))[:100],  # Truncate long values
            "new_value": str(value_change.get('new_value', ''))[:100]
        }
    
    def _categorize_path(self, path: str) -> ChangeCategory:
        """Categorize change based on path"""
        path_lower = path.lower()
        
        if "menu" in path_lower:
            return ChangeCategory.MENU
        elif "widget" in path_lower:
            return ChangeCategory.WIDGET
        elif "data" in path_lower:
            return ChangeCategory.DATA_SOURCE
        elif "theme" in path_lower or "style" in path_lower:
            return ChangeCategory.STYLING
        elif "permission" in path_lower:
            return ChangeCategory.PERMISSION
        else:
            return ChangeCategory.METADATA
    
    def _extract_element_name(self, path: str) -> str:
        """Extract human-readable element name from path"""
        # Extract the last meaningful part of the path
        parts = path.strip("root[]'").split("']['")
        if parts:
            return parts[-1].replace("_", " ").title()
        return "Unknown Element"
    
    def _generate_hash(self, template: Dict[str, Any]) -> str:
        """Generate a hash of the template for quick comparison"""
        # Sort keys for consistent hashing
        template_str = json.dumps(template, sort_keys=True)
        return hashlib.sha256(template_str.encode()).hexdigest()
    
    def generate_change_summary(self, changes: List[Dict[str, Any]]) -> str:
        """Generate a human-readable summary of changes"""
        if not changes:
            return "No changes detected"
        
        # Group by category
        by_category = {}
        for change in changes:
            category = change.get('category', ChangeCategory.METADATA)
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(change)
        
        # Build summary
        summary_parts = []
        for category, category_changes in by_category.items():
            category_summary = f"{category.value.replace('_', ' ').title()}: "
            descriptions = [c['description'] for c in category_changes[:3]]  # Limit to 3
            category_summary += ", ".join(descriptions)
            if len(category_changes) > 3:
                category_summary += f" and {len(category_changes) - 3} more"
            summary_parts.append(category_summary)
        
        return "; ".join(summary_parts)
    
    def has_breaking_changes(self, changes: List[Dict[str, Any]]) -> bool:
        """Check if any changes are breaking"""
        return any(change.get('breaking', False) for change in changes)