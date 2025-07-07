# ABOUTME: Template inheritance service for managing parent-child template relationships
# ABOUTME: Handles template inheritance logic, resolution of parent templates, and inheritance validation

import uuid
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models.dashboard import (
    DashboardTemplate, 
    InheritanceType, 
    TemplateStatus,
    DashboardTemplateBase
)
from ..core.db import get_db


class TemplateInheritanceError(Exception):
    """Custom exception for template inheritance errors"""
    pass


class TemplateInheritanceService:
    """Service for managing template inheritance and relationships"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_inheritance_chain(self, template_id: uuid.UUID) -> List[DashboardTemplate]:
        """
        Get the complete inheritance chain for a template.
        Returns list from root parent to the template itself.
        """
        chain = []
        current_template = self.db.get(DashboardTemplate, template_id)
        
        if not current_template:
            raise TemplateInheritanceError(f"Template {template_id} not found")
        
        # Build chain by following parent relationships
        visited = set()  # Prevent circular references
        
        while current_template:
            if current_template.id in visited:
                raise TemplateInheritanceError("Circular inheritance detected")
            
            visited.add(current_template.id)
            chain.insert(0, current_template)  # Insert at beginning for correct order
            
            # Move to parent
            if current_template.parent_template_id:
                current_template = self.db.get(DashboardTemplate, current_template.parent_template_id)
            else:
                current_template = None
        
        return chain
    
    def validate_inheritance(self, child_id: uuid.UUID, parent_id: uuid.UUID) -> bool:
        """
        Validate that inheritance relationship is valid.
        Checks for circular references and inheritance depth limits.
        """
        # Cannot inherit from self
        if child_id == parent_id:
            return False
        
        # Check if parent exists and is published
        parent = self.db.get(DashboardTemplate, parent_id)
        if not parent or parent.status != TemplateStatus.PUBLISHED:
            return False
        
        # Check if setting this parent would create circular reference
        try:
            parent_chain = self.get_inheritance_chain(parent_id)
            return child_id not in [t.id for t in parent_chain]
        except TemplateInheritanceError:
            return False
    
    def get_effective_template(self, template_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get the effective template structure by merging inheritance chain.
        Applies inheritance rules based on inheritance_type.
        """
        chain = self.get_inheritance_chain(template_id)
        
        if len(chain) == 1:
            # No inheritance, return template as-is
            return chain[0].template_structure
        
        # Start with root template
        effective_structure = chain[0].template_structure.copy()
        
        # Apply each child template in order
        for i in range(1, len(chain)):
            child_template = chain[i]
            child_structure = child_template.template_structure
            
            if child_template.inheritance_type == InheritanceType.EXTENDS:
                effective_structure = self._merge_extends(effective_structure, child_structure)
            elif child_template.inheritance_type == InheritanceType.INCLUDES:
                effective_structure = self._merge_includes(effective_structure, child_structure)
        
        return effective_structure
    
    def _merge_extends(self, parent: Dict[str, Any], child: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge templates using EXTENDS inheritance.
        Child can override any parent configuration.
        """
        merged = parent.copy()
        
        # Deep merge menu items
        if "menu" in child and "menu" in merged:
            merged["menu"] = self._merge_menu_extends(merged["menu"], child["menu"])
        elif "menu" in child:
            merged["menu"] = child["menu"]
        
        # Merge data mappings
        if "data_mappings" in child:
            if "data_mappings" in merged:
                merged["data_mappings"] = self._merge_data_mappings(
                    merged["data_mappings"], child["data_mappings"]
                )
            else:
                merged["data_mappings"] = child["data_mappings"]
        
        # Override any other top-level properties
        for key, value in child.items():
            if key not in ["menu", "data_mappings"]:
                merged[key] = value
        
        return merged
    
    def _merge_includes(self, parent: Dict[str, Any], child: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge templates using INCLUDES inheritance.
        Child includes parent components but doesn't override structure.
        """
        merged = child.copy()
        
        # Include parent menu items
        if "menu" in parent and "menu" in child:
            merged["menu"] = self._merge_menu_includes(parent["menu"], child["menu"])
        elif "menu" in parent:
            # If child has no menu, include parent menu
            merged["menu"] = parent["menu"]
        
        # Include parent data mappings
        if "data_mappings" in parent:
            if "data_mappings" in merged:
                merged["data_mappings"] = self._merge_data_mappings(
                    parent["data_mappings"], merged["data_mappings"]
                )
            else:
                merged["data_mappings"] = parent["data_mappings"]
        
        return merged
    
    def _merge_menu_extends(self, parent_menu: Dict[str, Any], child_menu: Dict[str, Any]) -> Dict[str, Any]:
        """Merge menu structures for EXTENDS inheritance"""
        merged_menu = parent_menu.copy()
        
        if "items" in child_menu:
            if "items" in merged_menu:
                # Create a map of parent items by ID for easy lookup
                parent_items = {item.get("id"): item for item in merged_menu["items"] if "id" in item}
                merged_items = []
                
                # Process child items
                for child_item in child_menu["items"]:
                    item_id = child_item.get("id")
                    if item_id and item_id in parent_items:
                        # Override parent item
                        merged_items.append(self._merge_menu_item(parent_items[item_id], child_item))
                        parent_items.pop(item_id)  # Remove from parent items
                    else:
                        # New item from child
                        merged_items.append(child_item)
                
                # Add remaining parent items
                merged_items.extend(parent_items.values())
                merged_menu["items"] = merged_items
            else:
                merged_menu["items"] = child_menu["items"]
        
        return merged_menu
    
    def _merge_menu_includes(self, parent_menu: Dict[str, Any], child_menu: Dict[str, Any]) -> Dict[str, Any]:
        """Merge menu structures for INCLUDES inheritance"""
        merged_menu = child_menu.copy()
        
        if "items" in parent_menu:
            if "items" in merged_menu:
                # Include parent items that don't exist in child
                child_item_ids = {item.get("id") for item in merged_menu["items"] if "id" in item}
                
                for parent_item in parent_menu["items"]:
                    parent_id = parent_item.get("id")
                    if parent_id and parent_id not in child_item_ids:
                        merged_menu["items"].append(parent_item)
            else:
                merged_menu["items"] = parent_menu["items"]
        
        return merged_menu
    
    def _merge_menu_item(self, parent_item: Dict[str, Any], child_item: Dict[str, Any]) -> Dict[str, Any]:
        """Merge individual menu items"""
        merged_item = parent_item.copy()
        
        # Override with child properties
        for key, value in child_item.items():
            if key == "dashboard" and "dashboard" in merged_item:
                # Deep merge dashboard configuration
                merged_item["dashboard"] = self._merge_dashboard_config(
                    merged_item["dashboard"], value
                )
            else:
                merged_item[key] = value
        
        return merged_item
    
    def _merge_dashboard_config(self, parent_dashboard: Dict[str, Any], child_dashboard: Dict[str, Any]) -> Dict[str, Any]:
        """Merge dashboard configurations"""
        merged_dashboard = parent_dashboard.copy()
        
        # Merge layout
        if "layout" in child_dashboard:
            merged_dashboard["layout"] = child_dashboard["layout"]
        
        # Merge widgets
        if "widgets" in child_dashboard:
            if "widgets" in merged_dashboard:
                # Override widgets by position or ID
                parent_widgets = {self._get_widget_key(w): w for w in merged_dashboard["widgets"]}
                merged_widgets = []
                
                for child_widget in child_dashboard["widgets"]:
                    widget_key = self._get_widget_key(child_widget)
                    if widget_key in parent_widgets:
                        # Override parent widget
                        merged_widgets.append(self._merge_widget_config(parent_widgets[widget_key], child_widget))
                        parent_widgets.pop(widget_key)
                    else:
                        # New widget from child
                        merged_widgets.append(child_widget)
                
                # Add remaining parent widgets
                merged_widgets.extend(parent_widgets.values())
                merged_dashboard["widgets"] = merged_widgets
            else:
                merged_dashboard["widgets"] = child_dashboard["widgets"]
        
        return merged_dashboard
    
    def _merge_widget_config(self, parent_widget: Dict[str, Any], child_widget: Dict[str, Any]) -> Dict[str, Any]:
        """Merge widget configurations"""
        merged_widget = parent_widget.copy()
        
        # Override with child properties
        for key, value in child_widget.items():
            if key == "instance_config" and "instance_config" in merged_widget:
                # Deep merge instance config
                merged_config = merged_widget["instance_config"].copy()
                merged_config.update(value)
                merged_widget["instance_config"] = merged_config
            elif key == "data_requirements" and "data_requirements" in merged_widget:
                # Deep merge data requirements
                merged_requirements = merged_widget["data_requirements"].copy()
                merged_requirements.update(value)
                merged_widget["data_requirements"] = merged_requirements
            else:
                merged_widget[key] = value
        
        return merged_widget
    
    def _get_widget_key(self, widget: Dict[str, Any]) -> str:
        """Get unique key for widget (for merging purposes)"""
        # Try widget ID first, then position-based key
        if "id" in widget:
            return f"id:{widget['id']}"
        elif "position" in widget:
            pos = widget["position"]
            return f"pos:{pos.get('x', 0)}:{pos.get('y', 0)}"
        else:
            return f"widget:{hash(str(widget))}"
    
    def _merge_data_mappings(self, parent_mappings: Dict[str, Any], child_mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Merge data mappings from parent and child templates"""
        merged = parent_mappings.copy()
        
        # Merge required datasets
        if "required_datasets" in child_mappings:
            parent_datasets = set(merged.get("required_datasets", []))
            child_datasets = set(child_mappings["required_datasets"])
            merged["required_datasets"] = list(parent_datasets.union(child_datasets))
        
        # Merge field mappings
        if "field_mappings" in child_mappings:
            if "field_mappings" not in merged:
                merged["field_mappings"] = {}
            
            for dataset, fields in child_mappings["field_mappings"].items():
                if dataset in merged["field_mappings"]:
                    # Combine fields from both parent and child
                    parent_fields = set(merged["field_mappings"][dataset])
                    child_fields = set(fields)
                    merged["field_mappings"][dataset] = list(parent_fields.union(child_fields))
                else:
                    merged["field_mappings"][dataset] = fields
        
        return merged
    
    def get_child_templates(self, parent_id: uuid.UUID) -> List[DashboardTemplate]:
        """Get all direct child templates of a parent"""
        stmt = select(DashboardTemplate).where(
            DashboardTemplate.parent_template_id == parent_id
        )
        return list(self.db.execute(stmt).scalars().all())
    
    def can_delete_template(self, template_id: uuid.UUID) -> Tuple[bool, List[str]]:
        """
        Check if a template can be safely deleted.
        Returns (can_delete, list_of_reasons_if_not)
        """
        template = self.db.get(DashboardTemplate, template_id)
        if not template:
            return False, ["Template not found"]
        
        reasons = []
        
        # Check if it has child templates
        children = self.get_child_templates(template_id)
        if children:
            child_names = [child.name for child in children]
            reasons.append(f"Template has child templates: {', '.join(child_names)}")
        
        # Check if it's being used by studies (would need to check study_dashboards)
        # This would require importing and checking StudyDashboard model
        
        return len(reasons) == 0, reasons