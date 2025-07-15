# ABOUTME: Tests documenting all menu structure types and configurations
# ABOUTME: Shows dashboard, group, submenu, and URL menu items with nesting
"""
Menu Structure System Documentation
===================================

This test suite documents the menu structure system that organizes dashboard navigation.
The platform supports flexible menu hierarchies with different item types.

Menu Item Types:
1. dashboard - Opens a page with configured widgets
2. group - Non-clickable parent for organizing related items
3. submenu - Collapsible section containing child items
4. url - External or internal link

Key Concepts:
- Menus can be nested to any depth
- Icons and labels are customizable
- URLs support template variables like {study_id}
- Menu items can have conditional visibility
"""

import pytest
from typing import Dict, List, Any
from sqlmodel import Session
from app.models import DashboardTemplate, User
from app.crud.dashboard_template import dashboard_template as crud_template
from app.schemas.dashboard_template import DashboardTemplateCreate


class TestMenuStructures:
    """
    QC Documentation: Menu Structure Types and Configurations
    
    This test class documents all possible menu configurations and behaviors.
    Each menu type serves a specific navigation purpose.
    
    Business Requirements:
    - Support hierarchical navigation structures
    - Allow external integrations via URL links
    - Enable logical grouping of related dashboards
    - Provide collapsible sections for better organization
    """
    
    def test_dashboard_menu_item(self, db: Session, normal_user: User):
        """
        Test Case: Dashboard menu item type
        
        Purpose: Most common menu type - opens a dashboard page with widgets
        Behavior: Clicking navigates to dashboard view with configured widgets
        
        Configuration options:
        - icon: Visual indicator (FontAwesome or custom)
        - badge: Optional count or status indicator
        - permissions: Role-based visibility
        """
        template_data = DashboardTemplateCreate(
            name="Dashboard Menu Test",
            description="Testing dashboard menu items",
            category="test",
            version="1.0.0",
            menu_structure=[
                {
                    "id": "overview-dashboard",
                    "label": "Study Overview",
                    "type": "dashboard",
                    "icon": "chart-line",
                    "badge": {
                        "type": "count",
                        "data_field": "alerts.unread"
                    },
                    "dashboard_config": {
                        "layout": "grid",
                        "refresh_interval": 300,  # 5 minutes
                        "widgets": [
                            {
                                "id": "summary-metric",
                                "type": "metric",
                                "title": "Total Enrollment",
                                "position": {"x": 0, "y": 0, "w": 3, "h": 2},
                                "config": {
                                    "metric_type": "count",
                                    "data_field": "subjects.enrolled"
                                }
                            }
                        ]
                    }
                },
                {
                    "id": "real-time-dashboard",
                    "label": "Real-Time Monitoring",
                    "type": "dashboard",
                    "icon": "activity",
                    "permissions": ["view_realtime"],  # Role-based access
                    "dashboard_config": {
                        "layout": "grid",
                        "refresh_interval": 60,  # 1 minute for real-time
                        "widgets": []
                    }
                }
            ]
        )
        
        template = crud_template.create_with_owner(
            db=db, obj_in=template_data, owner_id=normal_user.id, org_id=normal_user.org_id
        )
        
        # Verify dashboard menu items
        assert all(item["type"] == "dashboard" for item in template.menu_structure)
        assert template.menu_structure[0]["dashboard_config"]["refresh_interval"] == 300
        assert "permissions" in template.menu_structure[1]
    
    def test_group_menu_item(self, db: Session, normal_user: User):
        """
        Test Case: Group menu item type
        
        Purpose: Organize related items without being clickable itself
        Behavior: Expands/collapses to show child items, not navigable
        Use Case: Grouping all safety-related dashboards together
        
        Key Features:
        - Always expanded by default
        - Can contain any other menu item types
        - Provides visual hierarchy
        """
        template_data = DashboardTemplateCreate(
            name="Group Menu Test",
            description="Testing group menu organization",
            category="test",
            version="1.0.0",
            menu_structure=[
                {
                    "id": "safety-group",
                    "label": "Safety Monitoring",
                    "type": "group",
                    "icon": "shield-alt",
                    "expanded": True,  # Default state
                    "children": [
                        {
                            "id": "ae-dashboard",
                            "label": "Adverse Events",
                            "type": "dashboard",
                            "icon": "exclamation-triangle",
                            "dashboard_config": {
                                "widgets": [
                                    {
                                        "id": "ae-count",
                                        "type": "metric",
                                        "title": "Total AEs",
                                        "position": {"x": 0, "y": 0, "w": 2, "h": 2}
                                    }
                                ]
                            }
                        },
                        {
                            "id": "sae-dashboard",
                            "label": "Serious AEs",
                            "type": "dashboard",
                            "icon": "exclamation-circle",
                            "badge": {
                                "type": "alert",
                                "data_field": "sae.new_count",
                                "color": "red"
                            },
                            "dashboard_config": {
                                "widgets": []
                            }
                        },
                        {
                            "id": "lab-safety",
                            "label": "Lab Abnormalities",
                            "type": "dashboard",
                            "icon": "vial",
                            "dashboard_config": {
                                "widgets": []
                            }
                        }
                    ]
                },
                {
                    "id": "efficacy-group",
                    "label": "Efficacy Analysis",
                    "type": "group",
                    "icon": "chart-bar",
                    "children": [
                        {
                            "id": "primary-endpoint",
                            "label": "Primary Endpoint",
                            "type": "dashboard",
                            "dashboard_config": {"widgets": []}
                        },
                        {
                            "id": "secondary-endpoints",
                            "label": "Secondary Endpoints",
                            "type": "dashboard",
                            "dashboard_config": {"widgets": []}
                        }
                    ]
                }
            ]
        )
        
        template = crud_template.create_with_owner(
            db=db, obj_in=template_data, owner_id=normal_user.id, org_id=normal_user.org_id
        )
        
        # Verify group structure
        groups = [item for item in template.menu_structure if item["type"] == "group"]
        assert len(groups) == 2
        
        # Check safety group
        safety_group = groups[0]
        assert len(safety_group["children"]) == 3
        assert all(child["type"] == "dashboard" for child in safety_group["children"])
        
        # Verify badges can be on child items
        sae_dashboard = safety_group["children"][1]
        assert sae_dashboard["badge"]["type"] == "alert"
        assert sae_dashboard["badge"]["color"] == "red"
    
    def test_submenu_menu_item(self, db: Session, normal_user: User):
        """
        Test Case: Submenu menu item type
        
        Purpose: Collapsible menu section that can contain mixed item types
        Behavior: Toggles open/closed, remembers state per user
        Use Case: Organizing tools, reports, and dashboards together
        
        Differences from Group:
        - Collapsible (groups are always expanded)
        - Can contain URL items and other submenus
        - Better for deep hierarchies
        """
        template_data = DashboardTemplateCreate(
            name="Submenu Test",
            description="Testing submenu with mixed content",
            category="test",
            version="1.0.0",
            menu_structure=[
                {
                    "id": "data-tools",
                    "label": "Data Management",
                    "type": "submenu",
                    "icon": "database",
                    "collapsed": True,  # Start collapsed
                    "children": [
                        {
                            "id": "query-dashboard",
                            "label": "Query Management",
                            "type": "dashboard",
                            "icon": "question-circle",
                            "dashboard_config": {
                                "widgets": [
                                    {
                                        "id": "open-queries",
                                        "type": "metric",
                                        "title": "Open Queries",
                                        "position": {"x": 0, "y": 0, "w": 2, "h": 2}
                                    }
                                ]
                            }
                        },
                        {
                            "id": "data-review-tool",
                            "label": "Data Review Tool",
                            "type": "url",
                            "icon": "search",
                            "url": "/tools/data-review/{study_id}",
                            "target": "_self"  # Open in same window
                        },
                        {
                            "id": "exports-submenu",
                            "label": "Data Exports",
                            "type": "submenu",
                            "icon": "download",
                            "children": [
                                {
                                    "id": "sas-export",
                                    "label": "Export to SAS",
                                    "type": "url",
                                    "icon": "file-export",
                                    "url": "/api/v1/studies/{study_id}/export/sas",
                                    "target": "_blank"
                                },
                                {
                                    "id": "excel-export",
                                    "label": "Export to Excel",
                                    "type": "url",
                                    "icon": "file-excel",
                                    "url": "/api/v1/studies/{study_id}/export/excel",
                                    "target": "_blank"
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "external-tools",
                    "label": "External Systems",
                    "type": "submenu",
                    "icon": "external-link-alt",
                    "children": [
                        {
                            "id": "edc-system",
                            "label": "EDC System",
                            "type": "url",
                            "icon": "laptop-medical",
                            "url": "https://edc.example.com/study/{protocol_number}",
                            "target": "_blank",
                            "description": "Opens in Medidata Rave"
                        },
                        {
                            "id": "ctms",
                            "label": "CTMS",
                            "type": "url",
                            "icon": "project-diagram",
                            "url": "https://ctms.example.com/study/{study_id}",
                            "target": "_blank"
                        }
                    ]
                }
            ]
        )
        
        template = crud_template.create_with_owner(
            db=db, obj_in=template_data, owner_id=normal_user.id, org_id=normal_user.org_id
        )
        
        # Verify submenu structure
        submenus = [item for item in template.menu_structure if item["type"] == "submenu"]
        assert len(submenus) == 2
        
        # Check nested submenu
        data_tools = submenus[0]
        nested_submenu = next(
            child for child in data_tools["children"] 
            if child["type"] == "submenu"
        )
        assert nested_submenu["label"] == "Data Exports"
        assert len(nested_submenu["children"]) == 2
        
        # Verify mixed content types
        child_types = {child["type"] for child in data_tools["children"]}
        assert child_types == {"dashboard", "url", "submenu"}
    
    def test_url_menu_item(self, db: Session, normal_user: User):
        """
        Test Case: URL menu item type
        
        Purpose: Link to external systems or internal tools
        Behavior: Opens URL in new tab or same window based on target
        
        Features:
        - Template variables: {study_id}, {protocol_number}, {org_id}
        - Conditional parameters based on user context
        - Support for both internal and external URLs
        """
        template_data = DashboardTemplateCreate(
            name="URL Menu Test",
            description="Testing URL menu items with various configurations",
            category="test",
            version="1.0.0",
            menu_structure=[
                {
                    "id": "internal-tool",
                    "label": "Report Builder",
                    "type": "url",
                    "icon": "file-alt",
                    "url": "/tools/report-builder",
                    "target": "_self",
                    "description": "Built-in report creation tool"
                },
                {
                    "id": "external-docs",
                    "label": "Study Protocol",
                    "type": "url",
                    "icon": "book",
                    "url": "https://docs.example.com/protocols/{protocol_number}.pdf",
                    "target": "_blank",
                    "description": "View study protocol document"
                },
                {
                    "id": "dynamic-report",
                    "label": "Monthly Report",
                    "type": "url",
                    "icon": "calendar",
                    "url": "https://reports.example.com/generate?study={study_id}&org={org_id}&month={current_month}",
                    "target": "_blank",
                    "query_params": {
                        "format": "pdf",
                        "include_graphs": "true"
                    }
                },
                {
                    "id": "conditional-url",
                    "label": "Regulatory Submission",
                    "type": "url",
                    "icon": "gavel",
                    "url": "https://regulatory.example.com/submit",
                    "target": "_blank",
                    "permissions": ["submit_regulatory"],
                    "enabled_condition": "study.phase in ['phase_3', 'phase_4']"
                }
            ]
        )
        
        template = crud_template.create_with_owner(
            db=db, obj_in=template_data, owner_id=normal_user.id, org_id=normal_user.org_id
        )
        
        # Verify URL configurations
        urls = [item for item in template.menu_structure if item["type"] == "url"]
        assert len(urls) == 4
        
        # Check internal vs external
        internal_url = urls[0]
        assert internal_url["url"].startswith("/")
        assert internal_url["target"] == "_self"
        
        # Check template variables
        protocol_url = urls[1]
        assert "{protocol_number}" in protocol_url["url"]
        
        # Check query params
        dynamic_url = urls[2]
        assert "query_params" in dynamic_url
        assert dynamic_url["query_params"]["format"] == "pdf"
        
        # Check conditional URL
        conditional_url = urls[3]
        assert "permissions" in conditional_url
        assert "enabled_condition" in conditional_url
    
    def test_complex_nested_menu(self, db: Session, normal_user: User):
        """
        Test Case: Complex multi-level nested menu structure
        
        Purpose: Demonstrate deep nesting and mixed types
        Real-world use case: Large clinical trial with many components
        
        Shows:
        - 3+ levels of nesting
        - Mixed menu types at each level
        - Proper organization for 50+ menu items
        """
        template_data = DashboardTemplateCreate(
            name="Enterprise Clinical Trial Dashboard",
            description="Complex menu structure for large multi-site trial",
            category="enterprise",
            version="3.0.0",
            menu_structure=[
                {
                    "id": "home",
                    "label": "Home",
                    "type": "dashboard",
                    "icon": "home",
                    "dashboard_config": {"widgets": []}
                },
                {
                    "id": "clinical-ops",
                    "label": "Clinical Operations",
                    "type": "group",
                    "icon": "hospital",
                    "children": [
                        {
                            "id": "site-management",
                            "label": "Site Management",
                            "type": "submenu",
                            "icon": "map-marked-alt",
                            "children": [
                                {
                                    "id": "site-performance",
                                    "label": "Site Performance",
                                    "type": "dashboard",
                                    "dashboard_config": {"widgets": []}
                                },
                                {
                                    "id": "site-documents",
                                    "label": "Site Documents",
                                    "type": "submenu",
                                    "icon": "folder",
                                    "children": [
                                        {
                                            "id": "site-contracts",
                                            "label": "Contracts",
                                            "type": "url",
                                            "url": "/documents/contracts/{site_id}"
                                        },
                                        {
                                            "id": "site-regulatory",
                                            "label": "Regulatory Docs",
                                            "type": "url",
                                            "url": "/documents/regulatory/{site_id}"
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "id": "enrollment",
                            "label": "Enrollment",
                            "type": "group",
                            "icon": "users",
                            "children": [
                                {
                                    "id": "enrollment-overview",
                                    "label": "Overview",
                                    "type": "dashboard",
                                    "dashboard_config": {"widgets": []}
                                },
                                {
                                    "id": "enrollment-projections",
                                    "label": "Projections",
                                    "type": "dashboard",
                                    "dashboard_config": {"widgets": []}
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": "data-monitoring",
                    "label": "Data & Monitoring",
                    "type": "group",
                    "icon": "chart-line",
                    "children": [
                        {
                            "id": "safety",
                            "label": "Safety",
                            "type": "group",
                            "icon": "shield-alt",
                            "children": [
                                {
                                    "id": "ae-reporting",
                                    "label": "AE Reporting",
                                    "type": "dashboard",
                                    "dashboard_config": {"widgets": []}
                                },
                                {
                                    "id": "dsmb",
                                    "label": "DSMB Reports",
                                    "type": "submenu",
                                    "icon": "user-md",
                                    "children": [
                                        {
                                            "id": "dsmb-current",
                                            "label": "Current Report",
                                            "type": "url",
                                            "url": "/reports/dsmb/current"
                                        },
                                        {
                                            "id": "dsmb-archive",
                                            "label": "Archive",
                                            "type": "url",
                                            "url": "/reports/dsmb/archive"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        )
        
        template = crud_template.create_with_owner(
            db=db, obj_in=template_data, owner_id=normal_user.id, org_id=normal_user.org_id
        )
        
        # Count nesting levels
        def count_depth(items, current_depth=1):
            max_depth = current_depth
            for item in items:
                if "children" in item and item["children"]:
                    child_depth = count_depth(item["children"], current_depth + 1)
                    max_depth = max(max_depth, child_depth)
            return max_depth
        
        depth = count_depth(template.menu_structure)
        assert depth >= 4  # At least 4 levels deep
        
        # Verify mixed types exist at multiple levels
        def collect_types_by_level(items, level=1, type_map=None):
            if type_map is None:
                type_map = {}
            
            if level not in type_map:
                type_map[level] = set()
            
            for item in items:
                type_map[level].add(item["type"])
                if "children" in item and item["children"]:
                    collect_types_by_level(item["children"], level + 1, type_map)
            
            return type_map
        
        types_by_level = collect_types_by_level(template.menu_structure)
        
        # Level 1 has dashboard and groups
        assert "dashboard" in types_by_level[1]
        assert "group" in types_by_level[1]
        
        # Deeper levels have submenus and URLs
        assert "submenu" in types_by_level[2]
        assert "url" in types_by_level[4]
    
    def test_menu_permissions_and_visibility(self, db: Session, normal_user: User):
        """
        Test Case: Role-based menu visibility and permissions
        
        Purpose: Control menu access based on user roles
        Behavior: Menu items hidden/disabled based on permissions
        
        Permission types:
        - Role-based: ["admin", "data_manager", "monitor"]
        - Feature-based: ["view_pii", "export_data", "modify_queries"]
        - Study-phase based: Conditional on study.phase
        """
        template_data = DashboardTemplateCreate(
            name="Role-Based Menu Test",
            description="Testing permission-controlled menu items",
            category="test",
            version="1.0.0",
            menu_structure=[
                {
                    "id": "public-dashboard",
                    "label": "Public Overview",
                    "type": "dashboard",
                    "icon": "globe",
                    "permissions": [],  # No permissions = everyone can see
                    "dashboard_config": {"widgets": []}
                },
                {
                    "id": "admin-section",
                    "label": "Administration",
                    "type": "group",
                    "icon": "cog",
                    "permissions": ["admin", "study_manager"],
                    "children": [
                        {
                            "id": "user-management",
                            "label": "User Management",
                            "type": "url",
                            "url": "/admin/users",
                            "permissions": ["admin"]  # More restrictive than parent
                        },
                        {
                            "id": "study-config",
                            "label": "Study Configuration",
                            "type": "dashboard",
                            "permissions": ["admin", "study_manager"],
                            "dashboard_config": {"widgets": []}
                        }
                    ]
                },
                {
                    "id": "data-export",
                    "label": "Data Export",
                    "type": "submenu",
                    "icon": "download",
                    "permissions": ["export_data"],
                    "children": [
                        {
                            "id": "export-identified",
                            "label": "Export with PII",
                            "type": "url",
                            "url": "/export/identified",
                            "permissions": ["export_data", "view_pii"]  # Requires both
                        },
                        {
                            "id": "export-deidentified",
                            "label": "Export De-identified",
                            "type": "url",
                            "url": "/export/deidentified",
                            "permissions": ["export_data"]  # Only export permission
                        }
                    ]
                },
                {
                    "id": "interim-analysis",
                    "label": "Interim Analysis",
                    "type": "dashboard",
                    "icon": "chart-pie",
                    "permissions": ["view_interim_data"],
                    "enabled_condition": "study.has_reached_interim_milestone",
                    "dashboard_config": {"widgets": []}
                }
            ]
        )
        
        template = crud_template.create_with_owner(
            db=db, obj_in=template_data, owner_id=normal_user.id, org_id=normal_user.org_id
        )
        
        # Verify permission configurations
        admin_section = next(
            item for item in template.menu_structure 
            if item["id"] == "admin-section"
        )
        assert set(admin_section["permissions"]) == {"admin", "study_manager"}
        
        # Check nested permission (more restrictive)
        user_mgmt = admin_section["children"][0]
        assert user_mgmt["permissions"] == ["admin"]
        
        # Check combined permissions
        export_menu = next(
            item for item in template.menu_structure 
            if item["id"] == "data-export"
        )
        export_pii = export_menu["children"][0]
        assert set(export_pii["permissions"]) == {"export_data", "view_pii"}
        
        # Check conditional visibility
        interim = next(
            item for item in template.menu_structure 
            if item["id"] == "interim-analysis"
        )
        assert "enabled_condition" in interim