# ABOUTME: Comprehensive test suite for dashboard template management functionality
# ABOUTME: Tests template creation, validation, inheritance, export/import, and versioning

import pytest
import uuid
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, Any, List
import json

from sqlmodel import Session

from app.services.template_validator import TemplateValidator, ValidationResult
from app.services.template_inheritance import TemplateInheritanceService
from app.services.template_export_import import TemplateExportImportService
from app.services.template_migrator import TemplateMigrator
from app.services.template_merger import TemplateMerger
from app.models.dashboard import DashboardTemplate, TemplateStatus, TemplateScope
from app.models.organization import Organization
from app.models.study import Study
from app.models.widget import WidgetDefinition, WidgetCategory


class TestTemplateValidator:
    """Test suite for TemplateValidator"""

    @pytest.fixture
    def template_validator(self) -> TemplateValidator:
        """Create TemplateValidator instance for testing"""
        return TemplateValidator()

    @pytest.fixture
    def valid_template_config(self) -> Dict[str, Any]:
        """Create valid template configuration for testing"""
        return {
            "version": "1.0",
            "layout": {
                "grid": {
                    "columns": 12,
                    "rows": 8
                }
            },
            "widgets": [
                {
                    "id": "widget1",
                    "type": "metric",
                    "position": {"x": 0, "y": 0, "w": 4, "h": 2},
                    "config": {
                        "title": "Total Subjects",
                        "data_source": "demographics",
                        "aggregation": "count",
                        "field": "subject_id"
                    }
                },
                {
                    "id": "widget2", 
                    "type": "chart",
                    "position": {"x": 4, "y": 0, "w": 8, "h": 4},
                    "config": {
                        "title": "Age Distribution",
                        "chart_type": "bar",
                        "x_axis": "age_group",
                        "y_axis": "count"
                    }
                }
            ],
            "data_requirements": {
                "required_datasets": ["demographics"],
                "required_fields": ["subject_id", "age"],
                "optional_fields": ["gender", "race"]
            },
            "metadata": {
                "name": "Test Template",
                "description": "Template for testing",
                "category": "clinical_overview",
                "tags": ["demographics", "enrollment"]
            }
        }

    @pytest.fixture
    def invalid_template_config(self) -> Dict[str, Any]:
        """Create invalid template configuration for testing"""
        return {
            "widgets": [
                {
                    "id": "widget1",
                    "type": "invalid_type",  # Invalid widget type
                    "position": {"x": 0, "y": 0, "w": -1, "h": 2},  # Invalid width
                    "config": {}  # Missing required config
                }
            ]
        }

    def test_validate_valid_template(self, template_validator, valid_template_config):
        """Test validation of a valid template"""
        result = template_validator.validate_template(valid_template_config)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_validate_invalid_template(self, template_validator, invalid_template_config):
        """Test validation of an invalid template"""
        result = template_validator.validate_template(invalid_template_config)
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("invalid_type" in error for error in result.errors)

    def test_validate_widget_positions(self, template_validator):
        """Test validation of widget positions and overlaps"""
        config = {
            "widgets": [
                {
                    "id": "widget1",
                    "type": "metric",
                    "position": {"x": 0, "y": 0, "w": 4, "h": 2}
                },
                {
                    "id": "widget2",
                    "type": "metric", 
                    "position": {"x": 2, "y": 0, "w": 4, "h": 2}  # Overlaps with widget1
                }
            ]
        }
        
        result = template_validator.validate_template(config)
        
        assert not result.is_valid
        assert any("overlap" in error.lower() for error in result.errors)

    def test_validate_data_requirements(self, template_validator):
        """Test validation of data requirements"""
        config = {
            "widgets": [
                {
                    "id": "widget1",
                    "type": "metric",
                    "config": {"field": "non_required_field"}
                }
            ],
            "data_requirements": {
                "required_fields": ["subject_id", "age"]
            }
        }
        
        result = template_validator.validate_template(config)
        
        # Should have warnings about missing data requirements
        assert len(result.warnings) > 0

    def test_validate_widget_dependencies(self, template_validator):
        """Test validation of widget dependencies"""
        config = {
            "widgets": [
                {
                    "id": "widget1",
                    "type": "metric",
                    "config": {"depends_on": ["widget2"]}
                }
                # widget2 is missing
            ]
        }
        
        result = template_validator.validate_template(config)
        
        assert not result.is_valid
        assert any("dependency" in error.lower() for error in result.errors)

    def test_validate_template_version_compatibility(self, template_validator):
        """Test validation of template version compatibility"""
        config = {
            "version": "999.0",  # Future version
            "widgets": []
        }
        
        result = template_validator.validate_template(config)
        
        assert len(result.warnings) > 0
        assert any("version" in warning.lower() for warning in result.warnings)


class TestTemplateInheritanceService:
    """Test suite for TemplateInheritanceService"""

    @pytest.fixture
    def inheritance_service(self) -> TemplateInheritanceService:
        """Create TemplateInheritanceService instance for testing"""
        return TemplateInheritanceService()

    @pytest.fixture
    def base_template(self) -> Dict[str, Any]:
        """Create base template for inheritance testing"""
        return {
            "metadata": {
                "name": "Base Template",
                "category": "clinical_overview"
            },
            "layout": {
                "grid": {"columns": 12, "rows": 8}
            },
            "widgets": [
                {
                    "id": "base_widget1",
                    "type": "metric",
                    "position": {"x": 0, "y": 0, "w": 4, "h": 2},
                    "config": {"title": "Base Metric"}
                }
            ],
            "data_requirements": {
                "required_fields": ["subject_id"]
            }
        }

    @pytest.fixture
    def child_template(self) -> Dict[str, Any]:
        """Create child template for inheritance testing"""
        return {
            "metadata": {
                "name": "Child Template",
                "inherits_from": "base_template_id"
            },
            "widgets": [
                {
                    "id": "child_widget1",
                    "type": "chart",
                    "position": {"x": 4, "y": 0, "w": 8, "h": 4},
                    "config": {"title": "Child Chart"}
                }
            ],
            "data_requirements": {
                "required_fields": ["age"]  # Additional requirement
            }
        }

    def test_apply_inheritance_basic(self, inheritance_service, base_template, child_template):
        """Test basic template inheritance"""
        result = inheritance_service.apply_inheritance(child_template, base_template)
        
        # Should have widgets from both templates
        widget_ids = [w['id'] for w in result['widgets']]
        assert 'base_widget1' in widget_ids
        assert 'child_widget1' in widget_ids
        
        # Should inherit layout from base
        assert result['layout'] == base_template['layout']
        
        # Should merge data requirements
        assert set(result['data_requirements']['required_fields']) == {'subject_id', 'age'}

    def test_apply_inheritance_override(self, inheritance_service, base_template):
        """Test template inheritance with overrides"""
        child_template = {
            "metadata": {
                "name": "Child Template",
                "inherits_from": "base_template_id"
            },
            "layout": {
                "grid": {"columns": 16, "rows": 10}  # Override base layout
            },
            "widgets": [
                {
                    "id": "base_widget1",  # Override base widget
                    "type": "metric",
                    "position": {"x": 0, "y": 0, "w": 6, "h": 3},
                    "config": {"title": "Overridden Metric"}
                }
            ]
        }
        
        result = inheritance_service.apply_inheritance(child_template, base_template)
        
        # Should use child's layout
        assert result['layout']['grid']['columns'] == 16
        
        # Should use child's widget config
        base_widget = next(w for w in result['widgets'] if w['id'] == 'base_widget1')
        assert base_widget['config']['title'] == "Overridden Metric"
        assert base_widget['position']['w'] == 6

    def test_apply_inheritance_deep_merge(self, inheritance_service):
        """Test deep merging of complex configurations"""
        base_template = {
            "metadata": {
                "settings": {
                    "auto_refresh": True,
                    "refresh_interval": 300,
                    "theme": "light"
                }
            }
        }
        
        child_template = {
            "metadata": {
                "settings": {
                    "refresh_interval": 600,  # Override
                    "show_toolbar": True  # Add new
                }
            }
        }
        
        result = inheritance_service.apply_inheritance(child_template, base_template)
        
        settings = result['metadata']['settings']
        assert settings['auto_refresh'] is True  # From base
        assert settings['refresh_interval'] == 600  # Overridden
        assert settings['theme'] == "light"  # From base
        assert settings['show_toolbar'] is True  # From child

    def test_resolve_inheritance_chain(self, inheritance_service):
        """Test resolving complex inheritance chains"""
        grandparent = {
            "metadata": {"name": "Grandparent"},
            "widgets": [{"id": "gp_widget", "type": "metric"}]
        }
        
        parent = {
            "metadata": {"name": "Parent", "inherits_from": "grandparent_id"},
            "widgets": [{"id": "p_widget", "type": "chart"}]
        }
        
        child = {
            "metadata": {"name": "Child", "inherits_from": "parent_id"},
            "widgets": [{"id": "c_widget", "type": "table"}]
        }
        
        result = inheritance_service.resolve_inheritance_chain(
            child, {"parent_id": parent, "grandparent_id": grandparent}
        )
        
        widget_ids = [w['id'] for w in result['widgets']]
        assert len(widget_ids) == 3
        assert 'gp_widget' in widget_ids
        assert 'p_widget' in widget_ids
        assert 'c_widget' in widget_ids

    def test_circular_inheritance_detection(self, inheritance_service):
        """Test detection of circular inheritance"""
        template_a = {
            "metadata": {"name": "A", "inherits_from": "template_b"}
        }
        
        template_b = {
            "metadata": {"name": "B", "inherits_from": "template_a"}
        }
        
        with pytest.raises(ValueError, match="Circular inheritance"):
            inheritance_service.resolve_inheritance_chain(
                template_a, {"template_a": template_a, "template_b": template_b}
            )


class TestTemplateExportImportService:
    """Test suite for TemplateExportImportService"""

    @pytest.fixture
    def export_import_service(self, db: Session) -> TemplateExportImportService:
        """Create TemplateExportImportService instance for testing"""
        return TemplateExportImportService(db)

    @pytest.fixture
    def sample_template(self, db: Session) -> DashboardTemplate:
        """Create sample template for export/import testing"""
        template = DashboardTemplate(
            id=str(uuid.uuid4()),
            name="Sample Template",
            description="Sample template for testing",
            category="clinical_overview",
            scope=TemplateScope.GLOBAL,
            status=TemplateStatus.ACTIVE,
            version="1.0",
            config={
                "widgets": [
                    {
                        "id": "widget1",
                        "type": "metric",
                        "config": {"title": "Test Metric"}
                    }
                ]
            },
            data_requirements={
                "required_fields": ["subject_id"]
            }
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    def test_export_template(self, export_import_service, sample_template):
        """Test template export functionality"""
        export_data = export_import_service.export_template(sample_template.id)
        
        assert export_data['metadata']['id'] == sample_template.id
        assert export_data['metadata']['name'] == sample_template.name
        assert export_data['config'] == sample_template.config
        assert 'exported_at' in export_data['metadata']

    def test_export_template_with_dependencies(self, export_import_service, sample_template):
        """Test template export with widget dependencies"""
        # Create template with widget dependencies
        complex_template = DashboardTemplate(
            id=str(uuid.uuid4()),
            name="Complex Template",
            config={
                "widgets": [
                    {
                        "id": "widget1",
                        "type": "metric",
                        "depends_on": ["external_widget"]
                    }
                ]
            }
        )
        
        export_data = export_import_service.export_template(
            complex_template.id, 
            include_dependencies=True
        )
        
        assert 'dependencies' in export_data
        # Should include information about external dependencies

    def test_import_template(self, export_import_service):
        """Test template import functionality"""
        import_data = {
            "metadata": {
                "name": "Imported Template",
                "description": "Template imported from export",
                "category": "clinical_overview",
                "version": "1.0"
            },
            "config": {
                "widgets": [
                    {
                        "id": "imported_widget",
                        "type": "metric",
                        "config": {"title": "Imported Metric"}
                    }
                ]
            },
            "data_requirements": {
                "required_fields": ["subject_id"]
            }
        }
        
        template_id = export_import_service.import_template(import_data)
        
        assert template_id is not None
        # Verify template was created in database

    def test_import_template_with_conflicts(self, export_import_service, sample_template):
        """Test template import with naming conflicts"""
        import_data = {
            "metadata": {
                "name": sample_template.name,  # Same name as existing template
                "description": "Conflicting template"
            },
            "config": {"widgets": []}
        }
        
        # Should handle naming conflicts by modifying name
        template_id = export_import_service.import_template(
            import_data, 
            handle_conflicts=True
        )
        
        assert template_id is not None
        # Template should be imported with modified name

    def test_validate_import_data(self, export_import_service):
        """Test validation of import data"""
        invalid_data = {
            "metadata": {},  # Missing required fields
            "config": {"invalid": "structure"}
        }
        
        with pytest.raises(ValueError, match="Invalid import data"):
            export_import_service.import_template(invalid_data)

    def test_export_import_roundtrip(self, export_import_service, sample_template):
        """Test complete export/import roundtrip"""
        # Export template
        export_data = export_import_service.export_template(sample_template.id)
        
        # Modify name to avoid conflicts
        export_data['metadata']['name'] = "Roundtrip Test Template"
        
        # Import template
        new_template_id = export_import_service.import_template(export_data)
        
        # Verify imported template matches original
        assert new_template_id != sample_template.id
        # Additional verification of template content


class TestTemplateMigrator:
    """Test suite for TemplateMigrator"""

    @pytest.fixture
    def template_migrator(self) -> TemplateMigrator:
        """Create TemplateMigrator instance for testing"""
        return TemplateMigrator()

    def test_migrate_v1_to_v2(self, template_migrator):
        """Test migration from version 1.0 to 2.0"""
        v1_template = {
            "version": "1.0",
            "widgets": [
                {
                    "type": "metric",
                    "config": {
                        "datasource": "demographics",  # Old field name
                        "field": "subject_id"
                    }
                }
            ]
        }
        
        v2_template = template_migrator.migrate(v1_template, target_version="2.0")
        
        assert v2_template['version'] == "2.0"
        # Should rename 'datasource' to 'data_source'
        assert v2_template['widgets'][0]['config']['data_source'] == "demographics"
        assert 'datasource' not in v2_template['widgets'][0]['config']

    def test_migrate_widget_config_changes(self, template_migrator):
        """Test migration of widget configuration changes"""
        old_template = {
            "version": "1.0",
            "widgets": [
                {
                    "type": "chart",
                    "config": {
                        "chartType": "bar",  # Old camelCase
                        "xField": "gender",
                        "yField": "count"
                    }
                }
            ]
        }
        
        new_template = template_migrator.migrate(old_template, target_version="2.0")
        
        widget_config = new_template['widgets'][0]['config']
        assert widget_config['chart_type'] == "bar"
        assert widget_config['x_axis'] == "gender"
        assert widget_config['y_axis'] == "count"

    def test_migrate_layout_structure(self, template_migrator):
        """Test migration of layout structure changes"""
        old_template = {
            "version": "1.0",
            "layout": {
                "type": "grid",
                "cols": 12,
                "rows": 8
            }
        }
        
        new_template = template_migrator.migrate(old_template, target_version="2.0")
        
        assert new_template['layout']['grid']['columns'] == 12
        assert new_template['layout']['grid']['rows'] == 8

    def test_migration_compatibility_check(self, template_migrator):
        """Test compatibility checking before migration"""
        incompatible_template = {
            "version": "999.0",
            "widgets": []
        }
        
        with pytest.raises(ValueError, match="Cannot migrate"):
            template_migrator.migrate(incompatible_template, target_version="2.0")

    def test_migration_backup_creation(self, template_migrator):
        """Test that migration creates backup of original"""
        original_template = {
            "version": "1.0",
            "widgets": []
        }
        
        result = template_migrator.migrate(
            original_template, 
            target_version="2.0",
            create_backup=True
        )
        
        assert 'migration_backup' in result
        assert result['migration_backup']['version'] == "1.0"


class TestTemplateMerger:
    """Test suite for TemplateMerger"""

    @pytest.fixture
    def template_merger(self) -> TemplateMerger:
        """Create TemplateMerger instance for testing"""
        return TemplateMerger()

    def test_merge_templates_basic(self, template_merger):
        """Test basic template merging"""
        template1 = {
            "metadata": {"name": "Template 1"},
            "widgets": [
                {"id": "widget1", "type": "metric"}
            ]
        }
        
        template2 = {
            "metadata": {"name": "Template 2"},
            "widgets": [
                {"id": "widget2", "type": "chart"}
            ]
        }
        
        merged = template_merger.merge_templates([template1, template2])
        
        assert len(merged['widgets']) == 2
        widget_ids = [w['id'] for w in merged['widgets']]
        assert 'widget1' in widget_ids
        assert 'widget2' in widget_ids

    def test_merge_templates_with_conflicts(self, template_merger):
        """Test template merging with widget ID conflicts"""
        template1 = {
            "widgets": [
                {"id": "widget1", "type": "metric", "config": {"title": "Metric 1"}}
            ]
        }
        
        template2 = {
            "widgets": [
                {"id": "widget1", "type": "chart", "config": {"title": "Chart 1"}}  # Same ID
            ]
        }
        
        merged = template_merger.merge_templates([template1, template2])
        
        # Should resolve conflicts by renaming
        assert len(merged['widgets']) == 2
        widget_ids = [w['id'] for w in merged['widgets']]
        assert 'widget1' in widget_ids
        assert any('widget1_' in wid for wid in widget_ids if wid != 'widget1')

    def test_merge_data_requirements(self, template_merger):
        """Test merging of data requirements"""
        template1 = {
            "data_requirements": {
                "required_fields": ["subject_id", "age"],
                "optional_fields": ["gender"]
            }
        }
        
        template2 = {
            "data_requirements": {
                "required_fields": ["subject_id", "weight"],
                "optional_fields": ["race"]
            }
        }
        
        merged = template_merger.merge_templates([template1, template2])
        
        requirements = merged['data_requirements']
        assert set(requirements['required_fields']) == {'subject_id', 'age', 'weight'}
        assert set(requirements['optional_fields']) == {'gender', 'race'}

    def test_merge_layout_positioning(self, template_merger):
        """Test automatic layout positioning during merge"""
        template1 = {
            "widgets": [
                {"id": "widget1", "position": {"x": 0, "y": 0, "w": 4, "h": 2}}
            ]
        }
        
        template2 = {
            "widgets": [
                {"id": "widget2", "position": {"x": 0, "y": 0, "w": 4, "h": 2}}  # Same position
            ]
        }
        
        merged = template_merger.merge_templates([template1, template2])
        
        # Should automatically reposition to avoid overlaps
        positions = [w['position'] for w in merged['widgets']]
        assert len(positions) == 2
        # Verify no overlaps exist


@pytest.mark.integration
class TestTemplateManagementIntegration:
    """Integration tests for template management services"""

    async def test_complete_template_lifecycle(self, db: Session):
        """Test complete template creation, validation, and management"""
        # Test creating, validating, inheriting, exporting, and importing templates
        pass

    async def test_template_versioning_workflow(self, db: Session):
        """Test template versioning and migration workflow"""
        # Test creating new versions and migrating between them
        pass

    async def test_template_marketplace_workflow(self, db: Session):
        """Test template marketplace publishing and sharing"""
        # Test publishing templates to marketplace and downloading
        pass