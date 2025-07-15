# ABOUTME: Tests documenting dashboard template creation and management
# ABOUTME: Shows how to create templates with menus, widgets, and configurations
"""
Dashboard Template System Documentation
======================================

This test suite documents the dashboard template creation and management system.
Templates define the structure and widgets for clinical study dashboards.

Key Concepts:
- Templates are reusable dashboard configurations
- Each template contains menu structures and widget definitions
- Templates can be versioned and shared via marketplace
- Organizations can create custom templates or use shared ones
"""

import pytest
import uuid
from typing import Dict, List, Any
from sqlmodel import Session, select
from app.models import DashboardTemplate, Organization, User
from app.crud.dashboard_template import dashboard_template as crud_template
from app.schemas.dashboard_template import DashboardTemplateCreate
from tests.utils.utils import random_email, random_lower_string


class TestDashboardTemplateCreation:
    """
    QC Documentation: Dashboard Template Creation Process
    
    This test class documents how to create and configure dashboard templates
    with various menu structures and widget configurations.
    
    Business Requirements:
    - Templates define the structure for study dashboards
    - Each template must have at least one menu item with widgets
    - Templates support versioning for updates without breaking existing studies
    - Templates can be organization-specific or shared in marketplace
    """
    
    def test_create_basic_template_with_single_menu(self, db: Session, normal_user: User):
        """
        Test Case: Create a simple dashboard template with one menu page
        
        Scenario: Safety monitoring dashboard with overview page
        Expected: Template created with menu structure and widgets
        
        This demonstrates the simplest template structure:
        - Single menu item of type 'dashboard'
        - Multiple widgets on the page
        - Basic metric and chart widgets
        """
        template_data = DashboardTemplateCreate(
            name="Basic Safety Dashboard",
            description="Simple safety monitoring dashboard with key metrics",
            category="safety",
            version="1.0.0",
            menu_structure=[
                {
                    "id": "safety-overview",
                    "label": "Safety Overview",
                    "type": "dashboard",
                    "icon": "activity",
                    "dashboard_config": {
                        "layout": "grid",
                        "widgets": [
                            {
                                "id": "ae-count",
                                "type": "metric",
                                "title": "Total Adverse Events",
                                "position": {"x": 0, "y": 0, "w": 3, "h": 2},
                                "config": {
                                    "metric_type": "count",
                                    "data_field": "adverse_events.count"
                                }
                            },
                            {
                                "id": "sae-count", 
                                "type": "metric",
                                "title": "Serious AEs",
                                "position": {"x": 3, "y": 0, "w": 3, "h": 2},
                                "config": {
                                    "metric_type": "count",
                                    "data_field": "serious_adverse_events.count",
                                    "color": "red"
                                }
                            },
                            {
                                "id": "ae-timeline",
                                "type": "chart",
                                "title": "AE Timeline",
                                "position": {"x": 0, "y": 2, "w": 6, "h": 4},
                                "config": {
                                    "chart_type": "line",
                                    "x_axis": "event_date",
                                    "y_axis": "count",
                                    "group_by": "severity"
                                }
                            }
                        ]
                    }
                }
            ],
            data_requirements=[
                {
                    "widget_id": "ae-count",
                    "dataset": "adverse_events",
                    "required_fields": ["event_id", "subject_id"],
                    "data_config": {
                        "fields": {
                            "event_id": {"data_type": "string", "required": True},
                            "subject_id": {"data_type": "string", "required": True}
                        }
                    }
                },
                {
                    "widget_id": "sae-count",
                    "dataset": "adverse_events", 
                    "required_fields": ["event_id", "subject_id", "severity"],
                    "data_config": {
                        "fields": {
                            "event_id": {"data_type": "string", "required": True},
                            "subject_id": {"data_type": "string", "required": True},
                            "severity": {"data_type": "string", "required": True}
                        },
                        "filters": [{"field": "severity", "operator": "in", "value": ["serious", "life-threatening"]}]
                    }
                },
                {
                    "widget_id": "ae-timeline",
                    "dataset": "adverse_events",
                    "required_fields": ["event_date", "severity"],
                    "data_config": {
                        "fields": {
                            "event_date": {"data_type": "date", "required": True},
                            "severity": {"data_type": "string", "required": True}
                        }
                    }
                }
            ]
        )
        
        # Create template
        template = crud_template.create_with_owner(
            db=db,
            obj_in=template_data,
            owner_id=normal_user.id,
            org_id=normal_user.org_id
        )
        
        # Verify template structure
        assert template.name == "Basic Safety Dashboard"
        assert len(template.menu_structure) == 1
        assert template.menu_structure[0]["type"] == "dashboard"
        assert len(template.menu_structure[0]["dashboard_config"]["widgets"]) == 3
        
        # Verify data requirements
        assert len(template.data_requirements) == 3
        assert all(req["dataset"] == "adverse_events" for req in template.data_requirements)
        
        # Calculate widget count
        widget_count = crud_template.count_widgets(template)
        assert widget_count == 3
    
    def test_create_complex_template_with_nested_menus(self, db: Session, normal_user: User):
        """
        Test Case: Create complex dashboard template with nested menu structure
        
        Scenario: Comprehensive clinical trial dashboard with multiple sections
        Expected: Template with groups, submenus, external links, and dashboard pages
        
        This demonstrates advanced menu structures:
        - Groups for organizing related items
        - Submenus for hierarchical navigation  
        - External URL links
        - Multiple dashboard pages with different widget types
        """
        template_data = DashboardTemplateCreate(
            name="Comprehensive Clinical Trial Dashboard",
            description="Full-featured dashboard for clinical trial monitoring",
            category="clinical_operations",
            version="2.0.0",
            menu_structure=[
                {
                    "id": "overview",
                    "label": "Overview",
                    "type": "dashboard",
                    "icon": "home",
                    "dashboard_config": {
                        "layout": "grid",
                        "widgets": [
                            {
                                "id": "enrollment-metric",
                                "type": "metric",
                                "title": "Total Enrollment",
                                "position": {"x": 0, "y": 0, "w": 3, "h": 2},
                                "config": {"metric_type": "count", "data_field": "subjects.enrolled"}
                            },
                            {
                                "id": "site-status",
                                "type": "chart",
                                "title": "Site Status",
                                "position": {"x": 3, "y": 0, "w": 3, "h": 2},
                                "config": {"chart_type": "donut", "data_field": "sites.status"}
                            }
                        ]
                    }
                },
                {
                    "id": "safety-group",
                    "label": "Safety Monitoring",
                    "type": "group",
                    "icon": "shield",
                    "children": [
                        {
                            "id": "ae-summary",
                            "label": "AE Summary",
                            "type": "dashboard",
                            "dashboard_config": {
                                "layout": "grid",
                                "widgets": [
                                    {
                                        "id": "ae-by-system",
                                        "type": "chart",
                                        "title": "AEs by System Organ Class",
                                        "position": {"x": 0, "y": 0, "w": 6, "h": 4},
                                        "config": {"chart_type": "bar", "x_axis": "soc", "y_axis": "count"}
                                    },
                                    {
                                        "id": "ae-table",
                                        "type": "table",
                                        "title": "Recent Adverse Events",
                                        "position": {"x": 0, "y": 4, "w": 6, "h": 4},
                                        "config": {
                                            "columns": ["subject_id", "event_term", "start_date", "severity"],
                                            "page_size": 10
                                        }
                                    }
                                ]
                            }
                        },
                        {
                            "id": "lab-safety",
                            "label": "Lab Safety",
                            "type": "dashboard",
                            "dashboard_config": {
                                "layout": "grid",
                                "widgets": [
                                    {
                                        "id": "lab-outliers",
                                        "type": "metric",
                                        "title": "Lab Outliers",
                                        "position": {"x": 0, "y": 0, "w": 2, "h": 2},
                                        "config": {"metric_type": "count", "data_field": "labs.outliers"}
                                    }
                                ]
                            }
                        }
                    ]
                },
                {
                    "id": "data-management",
                    "label": "Data Management",
                    "type": "submenu",
                    "icon": "database",
                    "children": [
                        {
                            "id": "query-dashboard",
                            "label": "Query Management",
                            "type": "dashboard",
                            "dashboard_config": {
                                "layout": "grid",
                                "widgets": [
                                    {
                                        "id": "open-queries",
                                        "type": "metric",
                                        "title": "Open Queries",
                                        "position": {"x": 0, "y": 0, "w": 2, "h": 2},
                                        "config": {"metric_type": "count", "data_field": "queries.open"}
                                    }
                                ]
                            }
                        },
                        {
                            "id": "data-review",
                            "label": "Data Review Tool",
                            "type": "url",
                            "url": "/external/data-review",
                            "target": "_blank"
                        }
                    ]
                },
                {
                    "id": "reports",
                    "label": "Reports",
                    "type": "url",
                    "icon": "file-text",
                    "url": "https://reports.example.com/study/{study_id}",
                    "target": "_blank"
                }
            ],
            data_requirements=[
                {
                    "widget_id": "enrollment-metric",
                    "dataset": "demographics",
                    "required_fields": ["subject_id", "enrollment_date"],
                    "data_config": {
                        "fields": {
                            "subject_id": {"data_type": "string", "required": True},
                            "enrollment_date": {"data_type": "date", "required": True}
                        }
                    }
                },
                {
                    "widget_id": "site-status",
                    "dataset": "sites",
                    "required_fields": ["site_id", "status"],
                    "data_config": {
                        "fields": {
                            "site_id": {"data_type": "string", "required": True},
                            "status": {"data_type": "string", "required": True}
                        }
                    }
                },
                {
                    "widget_id": "ae-by-system",
                    "dataset": "adverse_events",
                    "required_fields": ["soc", "event_id"],
                    "data_config": {
                        "fields": {
                            "soc": {"data_type": "string", "required": True},
                            "event_id": {"data_type": "string", "required": True}
                        }
                    }
                },
                {
                    "widget_id": "ae-table",
                    "dataset": "adverse_events",
                    "required_fields": ["subject_id", "event_term", "start_date", "severity"],
                    "data_config": {
                        "fields": {
                            "subject_id": {"data_type": "string", "required": True},
                            "event_term": {"data_type": "string", "required": True},
                            "start_date": {"data_type": "date", "required": True},
                            "severity": {"data_type": "string", "required": True}
                        }
                    }
                },
                {
                    "widget_id": "lab-outliers",
                    "dataset": "laboratory",
                    "required_fields": ["result_value", "normal_range_low", "normal_range_high"],
                    "data_config": {
                        "fields": {
                            "result_value": {"data_type": "number", "required": True},
                            "normal_range_low": {"data_type": "number", "required": True},
                            "normal_range_high": {"data_type": "number", "required": True}
                        }
                    }
                },
                {
                    "widget_id": "open-queries",
                    "dataset": "data_queries",
                    "required_fields": ["query_id", "status"],
                    "data_config": {
                        "fields": {
                            "query_id": {"data_type": "string", "required": True},
                            "status": {"data_type": "string", "required": True}
                        }
                    }
                }
            ]
        )
        
        # Create template
        template = crud_template.create_with_owner(
            db=db,
            obj_in=template_data,
            owner_id=normal_user.id,
            org_id=normal_user.org_id
        )
        
        # Verify complex menu structure
        assert len(template.menu_structure) == 4
        
        # Check menu types
        menu_types = {item["type"] for item in template.menu_structure}
        assert menu_types == {"dashboard", "group", "submenu", "url"}
        
        # Verify group structure
        safety_group = next(item for item in template.menu_structure if item["id"] == "safety-group")
        assert len(safety_group["children"]) == 2
        assert all(child["type"] == "dashboard" for child in safety_group["children"])
        
        # Verify submenu structure
        data_mgmt = next(item for item in template.menu_structure if item["id"] == "data-management")
        assert len(data_mgmt["children"]) == 2
        assert data_mgmt["children"][0]["type"] == "dashboard"
        assert data_mgmt["children"][1]["type"] == "url"
        
        # Count total widgets
        widget_count = crud_template.count_widgets(template)
        assert widget_count == 6  # Total widgets across all dashboard pages
        
        # Count dashboard pages
        dashboard_count = crud_template.count_dashboard_pages(template)
        assert dashboard_count == 5  # Overview + 2 in safety group + 2 in data management

    def test_widget_types_and_configurations(self, db: Session, normal_user: User):
        """
        Test Case: Create template showcasing all widget types
        
        Scenario: Template demonstrating each widget type with configurations
        Expected: All widget types properly configured with their specific options
        
        Widget types documented:
        - metric: Single value KPIs with formatting options
        - chart: Various chart types (line, bar, pie, donut, scatter)
        - table: Data grids with sorting and pagination
        - text: Markdown content for instructions or notes
        - composite: Multiple metrics in one widget
        """
        template_data = DashboardTemplateCreate(
            name="Widget Showcase Template",
            description="Demonstrates all available widget types and configurations",
            category="demo",
            version="1.0.0",
            menu_structure=[
                {
                    "id": "metrics-page",
                    "label": "Metrics Gallery",
                    "type": "dashboard",
                    "dashboard_config": {
                        "layout": "grid",
                        "widgets": [
                            # Basic metric widget
                            {
                                "id": "simple-count",
                                "type": "metric",
                                "title": "Total Subjects",
                                "position": {"x": 0, "y": 0, "w": 2, "h": 2},
                                "config": {
                                    "metric_type": "count",
                                    "data_field": "subjects.total",
                                    "format": "number",
                                    "prefix": "",
                                    "suffix": " subjects"
                                }
                            },
                            # Percentage metric
                            {
                                "id": "completion-rate",
                                "type": "metric", 
                                "title": "Completion Rate",
                                "position": {"x": 2, "y": 0, "w": 2, "h": 2},
                                "config": {
                                    "metric_type": "percentage",
                                    "numerator_field": "subjects.completed",
                                    "denominator_field": "subjects.enrolled",
                                    "format": "percentage",
                                    "decimal_places": 1,
                                    "color_thresholds": [
                                        {"value": 90, "color": "green"},
                                        {"value": 70, "color": "yellow"},
                                        {"value": 0, "color": "red"}
                                    ]
                                }
                            },
                            # Average metric
                            {
                                "id": "avg-age",
                                "type": "metric",
                                "title": "Average Age",
                                "position": {"x": 4, "y": 0, "w": 2, "h": 2},
                                "config": {
                                    "metric_type": "average",
                                    "data_field": "demographics.age",
                                    "format": "number",
                                    "decimal_places": 1,
                                    "suffix": " years"
                                }
                            },
                            # Composite metric widget
                            {
                                "id": "enrollment-summary",
                                "type": "composite",
                                "title": "Enrollment Summary",
                                "position": {"x": 0, "y": 2, "w": 6, "h": 2},
                                "config": {
                                    "metrics": [
                                        {
                                            "label": "Screened",
                                            "data_field": "subjects.screened",
                                            "format": "number"
                                        },
                                        {
                                            "label": "Enrolled", 
                                            "data_field": "subjects.enrolled",
                                            "format": "number"
                                        },
                                        {
                                            "label": "Completed",
                                            "data_field": "subjects.completed",
                                            "format": "number"
                                        },
                                        {
                                            "label": "Withdrawn",
                                            "data_field": "subjects.withdrawn",
                                            "format": "number"
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                },
                {
                    "id": "charts-page",
                    "label": "Charts Gallery",
                    "type": "dashboard",
                    "dashboard_config": {
                        "layout": "grid",
                        "widgets": [
                            # Line chart
                            {
                                "id": "enrollment-timeline",
                                "type": "chart",
                                "title": "Enrollment Over Time",
                                "position": {"x": 0, "y": 0, "w": 6, "h": 4},
                                "config": {
                                    "chart_type": "line",
                                    "x_axis": "enrollment_date",
                                    "y_axis": "cumulative_count",
                                    "group_by": "site",
                                    "time_interval": "week",
                                    "show_legend": True,
                                    "show_data_labels": False
                                }
                            },
                            # Bar chart
                            {
                                "id": "ae-by-severity",
                                "type": "chart",
                                "title": "AEs by Severity",
                                "position": {"x": 0, "y": 4, "w": 3, "h": 3},
                                "config": {
                                    "chart_type": "bar",
                                    "x_axis": "severity",
                                    "y_axis": "count",
                                    "orientation": "vertical",
                                    "color_scheme": "severity",
                                    "sort_order": "value_desc"
                                }
                            },
                            # Pie chart
                            {
                                "id": "gender-distribution",
                                "type": "chart",
                                "title": "Gender Distribution",
                                "position": {"x": 3, "y": 4, "w": 3, "h": 3},
                                "config": {
                                    "chart_type": "pie",
                                    "data_field": "demographics.gender",
                                    "show_percentages": True,
                                    "show_legend": True
                                }
                            },
                            # Scatter plot
                            {
                                "id": "age-vs-response",
                                "type": "chart",
                                "title": "Age vs Treatment Response",
                                "position": {"x": 0, "y": 7, "w": 6, "h": 4},
                                "config": {
                                    "chart_type": "scatter",
                                    "x_axis": "demographics.age",
                                    "y_axis": "efficacy.response_value",
                                    "color_by": "treatment_arm",
                                    "size_by": "demographics.weight",
                                    "show_trend_line": True
                                }
                            }
                        ]
                    }
                },
                {
                    "id": "tables-page",
                    "label": "Tables & Text",
                    "type": "dashboard",
                    "dashboard_config": {
                        "layout": "grid",
                        "widgets": [
                            # Data table
                            {
                                "id": "subject-listing",
                                "type": "table",
                                "title": "Subject Listing",
                                "position": {"x": 0, "y": 0, "w": 6, "h": 5},
                                "config": {
                                    "columns": [
                                        {"field": "subject_id", "header": "Subject ID", "sortable": True},
                                        {"field": "site", "header": "Site", "sortable": True},
                                        {"field": "enrollment_date", "header": "Enrolled", "format": "date"},
                                        {"field": "status", "header": "Status", "filterable": True},
                                        {"field": "age", "header": "Age", "format": "number"}
                                    ],
                                    "page_size": 20,
                                    "enable_export": True,
                                    "enable_search": True,
                                    "row_actions": ["view_details", "export_data"]
                                }
                            },
                            # Text widget
                            {
                                "id": "instructions",
                                "type": "text",
                                "title": "Dashboard Instructions",
                                "position": {"x": 0, "y": 5, "w": 6, "h": 3},
                                "config": {
                                    "content": "## How to Use This Dashboard\\n\\nThis dashboard provides real-time monitoring of your clinical trial. Key features:\\n\\n- **Metrics**: Track enrollment and completion rates\\n- **Charts**: Visualize trends and distributions\\n- **Tables**: Review detailed subject data\\n\\n### Data Updates\\nData refreshes every 4 hours automatically.",
                                    "format": "markdown"
                                }
                            }
                        ]
                    }
                }
            ],
            data_requirements=[
                # Metric widgets requirements
                {"widget_id": "simple-count", "dataset": "demographics", "required_fields": ["subject_id"]},
                {"widget_id": "completion-rate", "dataset": "demographics", "required_fields": ["subject_id", "status"]},
                {"widget_id": "avg-age", "dataset": "demographics", "required_fields": ["age"]},
                {"widget_id": "enrollment-summary", "dataset": "demographics", "required_fields": ["subject_id", "status"]},
                # Chart widgets requirements
                {"widget_id": "enrollment-timeline", "dataset": "demographics", "required_fields": ["enrollment_date", "site"]},
                {"widget_id": "ae-by-severity", "dataset": "adverse_events", "required_fields": ["severity"]},
                {"widget_id": "gender-distribution", "dataset": "demographics", "required_fields": ["gender"]},
                {"widget_id": "age-vs-response", "dataset": "efficacy", "required_fields": ["age", "response_value", "treatment_arm"]},
                # Table widget requirements
                {"widget_id": "subject-listing", "dataset": "demographics", "required_fields": ["subject_id", "site", "enrollment_date", "status", "age"]}
            ]
        )
        
        # Create and verify template
        template = crud_template.create_with_owner(
            db=db,
            obj_in=template_data,
            owner_id=normal_user.id,
            org_id=normal_user.org_id
        )
        
        # Count widget types
        widget_types = {}
        for menu_item in template.menu_structure:
            if menu_item["type"] == "dashboard":
                for widget in menu_item["dashboard_config"]["widgets"]:
                    widget_type = widget["type"]
                    widget_types[widget_type] = widget_types.get(widget_type, 0) + 1
        
        # Verify all widget types are present
        assert "metric" in widget_types
        assert "chart" in widget_types
        assert "table" in widget_types
        assert "text" in widget_types
        assert "composite" in widget_types
        
        # Verify widget counts
        assert widget_types["metric"] == 3
        assert widget_types["chart"] == 4
        assert widget_types["table"] == 1
        assert widget_types["text"] == 1
        assert widget_types["composite"] == 1

    def test_template_versioning_and_updates(self, db: Session, normal_user: User):
        """
        Test Case: Template versioning system
        
        Scenario: Create template versions and track changes
        Expected: Version history maintained, existing studies unaffected
        
        Documents:
        - Semantic versioning (major.minor.patch)
        - Backward compatibility requirements
        - Version history tracking
        """
        # Create initial version
        v1_data = DashboardTemplateCreate(
            name="Evolving Dashboard",
            description="Template that will be updated",
            category="operations",
            version="1.0.0",
            menu_structure=[
                {
                    "id": "main",
                    "label": "Main Dashboard",
                    "type": "dashboard",
                    "dashboard_config": {
                        "widgets": [
                            {
                                "id": "metric-1",
                                "type": "metric",
                                "title": "Key Metric",
                                "position": {"x": 0, "y": 0, "w": 2, "h": 2}
                            }
                        ]
                    }
                }
            ]
        )
        
        template_v1 = crud_template.create_with_owner(
            db=db, obj_in=v1_data, owner_id=normal_user.id, org_id=normal_user.org_id
        )
        
        # Create minor update (backward compatible)
        v1_1_data = DashboardTemplateCreate(
            name="Evolving Dashboard",
            description="Template with new features",
            category="operations", 
            version="1.1.0",
            parent_template_id=template_v1.id,  # Links to previous version
            menu_structure=[
                {
                    "id": "main",
                    "label": "Main Dashboard",
                    "type": "dashboard",
                    "dashboard_config": {
                        "widgets": [
                            {
                                "id": "metric-1",
                                "type": "metric",
                                "title": "Key Metric",
                                "position": {"x": 0, "y": 0, "w": 2, "h": 2}
                            },
                            {
                                "id": "metric-2",  # New widget added
                                "type": "metric",
                                "title": "Additional Metric",
                                "position": {"x": 2, "y": 0, "w": 2, "h": 2}
                            }
                        ]
                    }
                }
            ]
        )
        
        template_v1_1 = crud_template.create_with_owner(
            db=db, obj_in=v1_1_data, owner_id=normal_user.id, org_id=normal_user.org_id
        )
        
        # Verify versioning
        assert template_v1_1.parent_template_id == template_v1.id
        assert len(template_v1.menu_structure[0]["dashboard_config"]["widgets"]) == 1
        assert len(template_v1_1.menu_structure[0]["dashboard_config"]["widgets"]) == 2
        
        # Both versions should coexist
        all_versions = db.exec(
            select(DashboardTemplate).where(
                DashboardTemplate.name == "Evolving Dashboard"
            )
        ).all()
        assert len(all_versions) == 2

    def test_template_marketplace_sharing(self, db: Session, normal_user: User, admin_user: User):
        """
        Test Case: Template marketplace functionality
        
        Scenario: Share templates between organizations
        Expected: Templates can be published, discovered, and cloned
        
        Documents:
        - Public vs private templates
        - Template discovery and search
        - Cloning and customization process
        """
        # Create a template to share
        template_data = DashboardTemplateCreate(
            name="Best Practice Safety Dashboard",
            description="Industry standard safety monitoring template",
            category="safety",
            version="2.0.0",
            is_public=True,  # Makes it available in marketplace
            tags=["safety", "fda-compliant", "best-practice"],
            menu_structure=[
                {
                    "id": "safety",
                    "label": "Safety Monitoring",
                    "type": "dashboard",
                    "dashboard_config": {"widgets": []}
                }
            ]
        )
        
        # Admin creates and publishes template
        public_template = crud_template.create_with_owner(
            db=db,
            obj_in=template_data,
            owner_id=admin_user.id,
            org_id=admin_user.org_id
        )
        
        # Normal user searches marketplace
        marketplace_templates = db.exec(
            select(DashboardTemplate).where(
                DashboardTemplate.is_public == True,
                DashboardTemplate.is_active == True
            )
        ).all()
        
        assert len(marketplace_templates) >= 1
        assert public_template in marketplace_templates
        
        # Normal user clones template to their org
        cloned_data = DashboardTemplateCreate(
            name="Safety Dashboard (Customized)",
            description=f"Based on {public_template.name}",
            category="safety",
            version="1.0.0",
            is_public=False,  # Keep private to org
            parent_template_id=public_template.id,
            menu_structure=public_template.menu_structure,
            data_requirements=public_template.data_requirements
        )
        
        cloned_template = crud_template.create_with_owner(
            db=db,
            obj_in=cloned_data,
            owner_id=normal_user.id,
            org_id=normal_user.org_id
        )
        
        # Verify clone
        assert cloned_template.parent_template_id == public_template.id
        assert cloned_template.org_id == normal_user.org_id
        assert cloned_template.is_public == False