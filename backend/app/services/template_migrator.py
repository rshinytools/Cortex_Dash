# ABOUTME: Template migration service for migrating templates between versions and handling breaking changes
# ABOUTME: Manages template version upgrades, data transformation, and migration rollback functionality

import uuid
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session

from ..models.dashboard import (
    DashboardTemplate, 
    TemplateVersion, 
    StudyDashboard,
    TemplateStatus
)
from .template_validator import TemplateValidatorService, ValidationSeverity


class MigrationType(str, Enum):
    """Types of migrations"""
    PATCH = "patch"          # Bug fixes, no breaking changes
    MINOR = "minor"          # New features, backwards compatible
    MAJOR = "major"          # Breaking changes


@dataclass
class MigrationStep:
    """Represents a single migration step"""
    name: str
    description: str
    migration_function: Callable[[Dict[str, Any]], Dict[str, Any]]
    rollback_function: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    is_breaking: bool = False


@dataclass
class MigrationPlan:
    """Plan for migrating from one version to another"""
    from_version: str
    to_version: str
    steps: List[MigrationStep]
    requires_backup: bool = True
    estimated_time_minutes: int = 5


class TemplateMigrationError(Exception):
    """Exception raised during template migration"""
    pass


class TemplateMigratorService:
    """Service for migrating templates between versions"""
    
    def __init__(self, db: Session):
        self.db = db
        self.validator = TemplateValidatorService()
        self.migration_registry: Dict[str, List[MigrationStep]] = {}
        self._register_default_migrations()
    
    def _register_default_migrations(self):
        """Register common migration patterns"""
        
        # Version 1.0.0 to 1.1.0 - Add new widget properties
        self.register_migration(
            "1.0.0->1.1.0",
            [
                MigrationStep(
                    name="add_widget_theme_support",
                    description="Add theme configuration to widgets",
                    migration_function=self._add_widget_theme_support,
                    rollback_function=self._remove_widget_theme_support,
                    is_breaking=False
                )
            ]
        )
        
        # Version 1.1.0 to 2.0.0 - Breaking changes to layout structure
        self.register_migration(
            "1.1.0->2.0.0",
            [
                MigrationStep(
                    name="modernize_layout_structure",
                    description="Update layout structure to new format",
                    migration_function=self._modernize_layout_structure,
                    rollback_function=self._revert_layout_structure,
                    is_breaking=True
                ),
                MigrationStep(
                    name="update_widget_positioning",
                    description="Convert old positioning to new grid system",
                    migration_function=self._update_widget_positioning,
                    rollback_function=self._revert_widget_positioning,
                    is_breaking=True
                )
            ]
        )
    
    def register_migration(self, version_path: str, steps: List[MigrationStep]):
        """Register migration steps for a version path"""
        self.migration_registry[version_path] = steps
    
    def get_migration_plan(self, from_version: str, to_version: str) -> Optional[MigrationPlan]:
        """Get migration plan between two versions"""
        
        # Direct migration path
        direct_path = f"{from_version}->{to_version}"
        if direct_path in self.migration_registry:
            steps = self.migration_registry[direct_path]
            return MigrationPlan(
                from_version=from_version,
                to_version=to_version,
                steps=steps,
                requires_backup=any(step.is_breaking for step in steps),
                estimated_time_minutes=len(steps) * 2
            )
        
        # Try to find multi-step path
        # For now, return None if no direct path exists
        # In a production system, you'd implement path finding
        return None
    
    def migrate_template(
        self, 
        template_id: uuid.UUID, 
        target_version: str,
        user_id: uuid.UUID,
        dry_run: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Migrate a template to a target version.
        
        Args:
            template_id: Template to migrate
            target_version: Target version string (e.g., "2.0.0")
            user_id: User performing the migration
            dry_run: If True, don't actually save changes
            
        Returns:
            (success, migration_result)
        """
        template = self.db.get(DashboardTemplate, template_id)
        if not template:
            raise TemplateMigrationError(f"Template {template_id} not found")
        
        current_version = template.version_string
        
        # Check if migration is needed
        if current_version == target_version:
            return True, {"message": "Template is already at target version"}
        
        # Get migration plan
        migration_plan = self.get_migration_plan(current_version, target_version)
        if not migration_plan:
            raise TemplateMigrationError(
                f"No migration path found from {current_version} to {target_version}"
            )
        
        # Create backup if required
        backup_data = None
        if migration_plan.requires_backup:
            backup_data = self._create_migration_backup(template)
        
        try:
            # Apply migration steps
            migrated_structure = template.template_structure.copy()
            migration_log = []
            
            for step in migration_plan.steps:
                step_start = datetime.utcnow()
                
                try:
                    migrated_structure = step.migration_function(migrated_structure)
                    migration_log.append({
                        "step": step.name,
                        "status": "success",
                        "message": step.description,
                        "duration_ms": (datetime.utcnow() - step_start).total_seconds() * 1000
                    })
                except Exception as e:
                    migration_log.append({
                        "step": step.name,
                        "status": "error",
                        "message": str(e),
                        "duration_ms": (datetime.utcnow() - step_start).total_seconds() * 1000
                    })
                    raise TemplateMigrationError(f"Migration step '{step.name}' failed: {str(e)}")
            
            # Validate migrated structure
            is_valid, validation_issues = self.validator.validate_template_structure(migrated_structure)
            if not is_valid:
                error_issues = [issue for issue in validation_issues if issue.severity == ValidationSeverity.ERROR]
                raise TemplateMigrationError(f"Migrated template is invalid: {error_issues}")
            
            if not dry_run:
                # Update template
                major, minor, patch = target_version.split(".")
                template.major_version = int(major)
                template.minor_version = int(minor)
                template.patch_version = int(patch)
                template.template_structure = migrated_structure
                template.updated_at = datetime.utcnow()
                
                # Create version history entry
                self._create_version_entry(
                    template, 
                    user_id, 
                    f"Migrated from {current_version} to {target_version}",
                    migration_log
                )
                
                self.db.commit()
            
            return True, {
                "message": f"Successfully migrated from {current_version} to {target_version}",
                "migration_log": migration_log,
                "validation_issues": [
                    {
                        "severity": issue.severity,
                        "message": issue.message,
                        "path": issue.path
                    }
                    for issue in validation_issues
                ],
                "backup_created": backup_data is not None
            }
            
        except Exception as e:
            # Rollback changes if not dry run
            if not dry_run and backup_data:
                self._restore_from_backup(template, backup_data)
                self.db.rollback()
            
            return False, {
                "error": str(e),
                "migration_log": migration_log if 'migration_log' in locals() else []
            }
    
    def migrate_study_templates(
        self, 
        study_id: uuid.UUID, 
        target_version: str,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Migrate all templates used by a study to target version"""
        
        # Get all study dashboards
        study_dashboards = self.db.query(StudyDashboard).filter(
            StudyDashboard.study_id == study_id
        ).all()
        
        results = []
        for study_dashboard in study_dashboards:
            template = study_dashboard.dashboard_template
            
            try:
                success, result = self.migrate_template(
                    template.id, target_version, user_id, dry_run=False
                )
                results.append({
                    "template_id": str(template.id),
                    "template_name": template.name,
                    "success": success,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "template_id": str(template.id),
                    "template_name": template.name,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "study_id": str(study_id),
            "target_version": target_version,
            "total_templates": len(results),
            "successful_migrations": sum(1 for r in results if r["success"]),
            "results": results
        }
    
    def _create_migration_backup(self, template: DashboardTemplate) -> Dict[str, Any]:
        """Create backup data for migration rollback"""
        return {
            "template_id": str(template.id),
            "version": template.version_string,
            "template_structure": template.template_structure.copy(),
            "backup_timestamp": datetime.utcnow().isoformat()
        }
    
    def _restore_from_backup(self, template: DashboardTemplate, backup_data: Dict[str, Any]):
        """Restore template from backup data"""
        version_parts = backup_data["version"].split(".")
        template.major_version = int(version_parts[0])
        template.minor_version = int(version_parts[1])
        template.patch_version = int(version_parts[2])
        template.template_structure = backup_data["template_structure"]
    
    def _create_version_entry(
        self, 
        template: DashboardTemplate, 
        user_id: uuid.UUID, 
        description: str,
        migration_log: List[Dict[str, Any]]
    ):
        """Create version history entry"""
        version_entry = TemplateVersion(
            template_id=template.id,
            major_version=template.major_version,
            minor_version=template.minor_version,
            patch_version=template.patch_version,
            change_description=description,
            template_structure=template.template_structure,
            is_published=template.status == TemplateStatus.PUBLISHED.value,
            migration_notes=f"Migration log: {migration_log}",
            breaking_changes=any(step.get("is_breaking", False) for step in migration_log),
            created_by=user_id
        )
        
        self.db.add(version_entry)
    
    # Migration functions for specific version transitions
    
    def _add_widget_theme_support(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Add theme configuration to widgets (1.0.0 -> 1.1.0)"""
        if "menu" not in structure:
            return structure
        
        for menu_item in structure["menu"].get("items", []):
            if menu_item.get("type") == "dashboard" and "dashboard" in menu_item:
                dashboard = menu_item["dashboard"]
                for widget in dashboard.get("widgets", []):
                    if "instance_config" not in widget:
                        widget["instance_config"] = {}
                    
                    # Add default theme configuration
                    if "theme" not in widget["instance_config"]:
                        widget["instance_config"]["theme"] = {
                            "primary_color": "#3b82f6",
                            "background_color": "#ffffff",
                            "text_color": "#1f2937"
                        }
        
        return structure
    
    def _remove_widget_theme_support(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Remove theme configuration from widgets (rollback)"""
        if "menu" not in structure:
            return structure
        
        for menu_item in structure["menu"].get("items", []):
            if menu_item.get("type") == "dashboard" and "dashboard" in menu_item:
                dashboard = menu_item["dashboard"]
                for widget in dashboard.get("widgets", []):
                    if "instance_config" in widget and "theme" in widget["instance_config"]:
                        del widget["instance_config"]["theme"]
        
        return structure
    
    def _modernize_layout_structure(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Update layout structure to new format (1.1.0 -> 2.0.0)"""
        if "menu" not in structure:
            return structure
        
        for menu_item in structure["menu"].get("items", []):
            if menu_item.get("type") == "dashboard" and "dashboard" in menu_item:
                dashboard = menu_item["dashboard"]
                layout = dashboard.get("layout", {})
                
                # Convert old layout format to new format
                if layout.get("type") == "grid":
                    # Old format: {"type": "grid", "columns": 12, "rows": 10}
                    # New format: {"type": "responsive_grid", "breakpoints": {...}}
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
        
        return structure
    
    def _revert_layout_structure(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Revert layout structure to old format (rollback)"""
        if "menu" not in structure:
            return structure
        
        for menu_item in structure["menu"].get("items", []):
            if menu_item.get("type") == "dashboard" and "dashboard" in menu_item:
                dashboard = menu_item["dashboard"]
                layout = dashboard.get("layout", {})
                
                # Convert new layout format back to old format
                if layout.get("type") == "responsive_grid":
                    breakpoints = layout.get("breakpoints", {})
                    lg_columns = breakpoints.get("lg", {}).get("columns", 12)
                    dashboard["layout"] = {
                        "type": "grid",
                        "columns": lg_columns,
                        "rows": 10
                    }
        
        return structure
    
    def _update_widget_positioning(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Convert old positioning to new grid system (1.1.0 -> 2.0.0)"""
        if "menu" not in structure:
            return structure
        
        for menu_item in structure["menu"].get("items", []):
            if menu_item.get("type") == "dashboard" and "dashboard" in menu_item:
                dashboard = menu_item["dashboard"]
                for widget in dashboard.get("widgets", []):
                    position = widget.get("position", {})
                    
                    # Convert old position format
                    if "x" in position and "y" in position:
                        # Old format used simple x,y coordinates
                        # New format uses responsive positioning
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
                                "y": position.get("y", 0) * 2,  # Stack vertically
                                "w": 4,
                                "h": position.get("h", 2)
                            },
                            "xs": {
                                "x": 0,
                                "y": position.get("y", 0) * 3,  # Stack vertically
                                "w": 2,
                                "h": position.get("h", 2)
                            }
                        }
        
        return structure
    
    def _revert_widget_positioning(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Revert widget positioning to old format (rollback)"""
        if "menu" not in structure:
            return structure
        
        for menu_item in structure["menu"].get("items", []):
            if menu_item.get("type") == "dashboard" and "dashboard" in menu_item:
                dashboard = menu_item["dashboard"]
                for widget in dashboard.get("widgets", []):
                    position = widget.get("position", {})
                    
                    # Convert new position format back to old
                    if isinstance(position, dict) and "lg" in position:
                        lg_position = position["lg"]
                        widget["position"] = {
                            "x": lg_position.get("x", 0),
                            "y": lg_position.get("y", 0),
                            "w": lg_position.get("w", 3),
                            "h": lg_position.get("h", 2)
                        }
        
        return structure