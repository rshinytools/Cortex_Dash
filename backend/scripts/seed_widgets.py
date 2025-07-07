#!/usr/bin/env python3

# ABOUTME: Seed script to populate default widgets, dashboard templates, and menu templates
# ABOUTME: Creates a complete set of default configurations for clinical trial dashboards

"""
Seed script for widget library and dashboard templates.

Usage:
    python backend/scripts/seed_widgets.py

This script creates:
- Default widget definitions for common clinical trial visualizations
- Default dashboard templates for various study types
- Default menu templates for navigation
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select
from datetime import datetime
import uuid

from app.core.db import engine
from app.models import (
    WidgetDefinition,
    WidgetDefinitionCreate,
    WidgetCategory,
    DashboardTemplate,
    DashboardTemplateCreate,
    DashboardCategory,
    DashboardWidget,
    DashboardWidgetBase,
    MenuTemplate,
    MenuTemplateCreate,
    User
)
from app.crud import widget as crud_widget
from app.crud import dashboard as crud_dashboard
from app.crud import menu as crud_menu


def create_default_widgets(db: Session, admin_user: User) -> dict:
    """Create default widget definitions"""
    print("Creating default widget definitions...")
    
    widgets = {}
    
    # Metric Card Widget
    metric_card = WidgetDefinitionCreate(
        code="metric_card",
        name="Metric Card",
        description="Display a single metric with optional trend indicator",
        category=WidgetCategory.METRICS,
        config_schema={
            "type": "object",
            "required": ["title", "dataset", "field", "calculation"],
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Widget title",
                    "minLength": 1,
                    "maxLength": 100
                },
                "dataset": {
                    "type": "string",
                    "description": "Source dataset",
                    "enum": ["ADSL", "ADAE", "ADLB", "ADVS", "ADCM", "ADDV"]
                },
                "field": {
                    "type": "string",
                    "description": "Field to calculate metric from"
                },
                "calculation": {
                    "type": "string",
                    "description": "Calculation type",
                    "enum": ["count", "sum", "avg", "min", "max", "distinct"],
                    "default": "count"
                },
                "showTrend": {
                    "type": "boolean",
                    "description": "Show trend indicator",
                    "default": True
                },
                "format": {
                    "type": "string",
                    "description": "Number format",
                    "enum": ["number", "percentage", "currency"],
                    "default": "number"
                },
                "filters": {
                    "type": "array",
                    "description": "Data filters",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"},
                            "operator": {"type": "string"},
                            "value": {}
                        }
                    }
                }
            }
        },
        default_config={
            "showTrend": True,
            "calculation": "count",
            "format": "number"
        },
        size_constraints={
            "min_width": 2,
            "min_height": 2,
            "max_width": 6,
            "max_height": 4,
            "default_width": 3,
            "default_height": 2
        },
        data_requirements={
            "min_datasets": 1,
            "required_fields": ["field"],
            "supports_aggregation": True
        }
    )
    
    db_widget = crud_widget.create_widget(db, metric_card, admin_user)
    widgets["metric_card"] = db_widget
    print(f"  ✓ Created metric card widget: {db_widget.id}")
    
    # Line Chart Widget
    line_chart = WidgetDefinitionCreate(
        code="line_chart",
        name="Line Chart",
        description="Time series visualization with multiple lines",
        category=WidgetCategory.CHARTS,
        config_schema={
            "type": "object",
            "required": ["title", "dataset", "xAxis", "yAxis"],
            "properties": {
                "title": {"type": "string"},
                "dataset": {
                    "type": "string",
                    "enum": ["ADSL", "ADAE", "ADLB", "ADVS", "ADCM", "ADDV"]
                },
                "xAxis": {
                    "type": "string",
                    "description": "X-axis field (usually date/time)"
                },
                "yAxis": {
                    "type": "string",
                    "description": "Y-axis field (value to plot)"
                },
                "groupBy": {
                    "type": "string",
                    "description": "Field to group by (creates multiple lines)"
                },
                "chartType": {
                    "type": "string",
                    "enum": ["line", "area", "bar"],
                    "default": "line"
                },
                "timeRange": {
                    "type": "string",
                    "enum": ["1w", "1m", "3m", "6m", "1y", "all"],
                    "default": "all"
                }
            }
        },
        default_config={
            "chartType": "line",
            "timeRange": "all"
        },
        size_constraints={
            "min_width": 4,
            "min_height": 3,
            "max_width": 12,
            "max_height": 8,
            "default_width": 6,
            "default_height": 4
        }
    )
    
    db_widget = crud_widget.create_widget(db, line_chart, admin_user)
    widgets["line_chart"] = db_widget
    print(f"  ✓ Created line chart widget: {db_widget.id}")
    
    # Bar Chart Widget
    bar_chart = WidgetDefinitionCreate(
        code="bar_chart",
        name="Bar Chart",
        description="Categorical data visualization",
        category=WidgetCategory.CHARTS,
        config_schema={
            "type": "object",
            "required": ["title", "dataset", "categoryField", "valueField"],
            "properties": {
                "title": {"type": "string"},
                "dataset": {
                    "type": "string",
                    "enum": ["ADSL", "ADAE", "ADLB", "ADVS", "ADCM", "ADDV"]
                },
                "categoryField": {
                    "type": "string",
                    "description": "Field for categories (X-axis)"
                },
                "valueField": {
                    "type": "string",
                    "description": "Field for values (Y-axis)"
                },
                "calculation": {
                    "type": "string",
                    "enum": ["count", "sum", "avg"],
                    "default": "count"
                },
                "orientation": {
                    "type": "string",
                    "enum": ["vertical", "horizontal"],
                    "default": "vertical"
                }
            }
        },
        size_constraints={
            "min_width": 4,
            "min_height": 3,
            "max_width": 12,
            "max_height": 8,
            "default_width": 6,
            "default_height": 4
        }
    )
    
    db_widget = crud_widget.create_widget(db, bar_chart, admin_user)
    widgets["bar_chart"] = db_widget
    print(f"  ✓ Created bar chart widget: {db_widget.id}")
    
    # Data Table Widget
    data_table = WidgetDefinitionCreate(
        code="data_table",
        name="Data Table",
        description="Paginated table with sorting and filtering",
        category=WidgetCategory.TABLES,
        config_schema={
            "type": "object",
            "required": ["title", "dataset", "columns"],
            "properties": {
                "title": {"type": "string"},
                "dataset": {
                    "type": "string",
                    "enum": ["ADSL", "ADAE", "ADLB", "ADVS", "ADCM", "ADDV"]
                },
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 20
                },
                "pageSize": {
                    "type": "integer",
                    "default": 20,
                    "minimum": 5,
                    "maximum": 100
                },
                "enableSearch": {
                    "type": "boolean",
                    "default": True
                },
                "enableExport": {
                    "type": "boolean",
                    "default": True
                },
                "enableSorting": {
                    "type": "boolean",
                    "default": True
                }
            }
        },
        default_config={
            "pageSize": 20,
            "enableSearch": True,
            "enableExport": True,
            "enableSorting": True
        },
        size_constraints={
            "min_width": 4,
            "min_height": 3,
            "max_width": 12,
            "max_height": 8,
            "default_width": 8,
            "default_height": 4
        }
    )
    
    db_widget = crud_widget.create_widget(db, data_table, admin_user)
    widgets["data_table"] = db_widget
    print(f"  ✓ Created data table widget: {db_widget.id}")
    
    # Pie Chart Widget
    pie_chart = WidgetDefinitionCreate(
        code="pie_chart",
        name="Pie Chart",
        description="Proportional data visualization",
        category=WidgetCategory.CHARTS,
        config_schema={
            "type": "object",
            "required": ["title", "dataset", "categoryField"],
            "properties": {
                "title": {"type": "string"},
                "dataset": {
                    "type": "string",
                    "enum": ["ADSL", "ADAE", "ADLB", "ADVS", "ADCM", "ADDV"]
                },
                "categoryField": {
                    "type": "string",
                    "description": "Field for categories"
                },
                "valueField": {
                    "type": "string",
                    "description": "Field for values (optional, defaults to count)"
                },
                "showLegend": {
                    "type": "boolean",
                    "default": True
                },
                "showLabels": {
                    "type": "boolean",
                    "default": True
                }
            }
        },
        size_constraints={
            "min_width": 3,
            "min_height": 3,
            "max_width": 8,
            "max_height": 8,
            "default_width": 4,
            "default_height": 4
        }
    )
    
    db_widget = crud_widget.create_widget(db, pie_chart, admin_user)
    widgets["pie_chart"] = db_widget
    print(f"  ✓ Created pie chart widget: {db_widget.id}")
    
    return widgets


def create_default_dashboards(db: Session, admin_user: User, widgets: dict) -> dict:
    """Create default dashboard templates"""
    print("Creating default dashboard templates...")
    
    dashboards = {}
    
    # Overview Dashboard
    overview_dashboard = DashboardTemplateCreate(
        code="clinical_overview",
        name="Clinical Study Overview",
        description="Main dashboard showing key study metrics and enrollment progress",
        category=DashboardCategory.OVERVIEW,
        layout_config={
            "type": "grid",
            "breakpoints": {"lg": 1200, "md": 996, "sm": 768, "xs": 480, "xxs": 0},
            "cols": {"lg": 12, "md": 10, "sm": 6, "xs": 4, "xxs": 2},
            "rowHeight": 60,
            "margin": [10, 10],
            "containerPadding": [10, 10],
            "isDraggable": True,
            "isResizable": True
        }
    )
    
    db_dashboard = crud_dashboard.create_dashboard(db, overview_dashboard, admin_user)
    dashboards["clinical_overview"] = db_dashboard
    
    # Add widgets to overview dashboard
    widget_configs = [
        {
            "widget": widgets["metric_card"],
            "position": {"x": 0, "y": 0, "w": 3, "h": 2},
            "config": {
                "title": "Total Enrolled",
                "dataset": "ADSL",
                "field": "USUBJID",
                "calculation": "count",
                "showTrend": True
            }
        },
        {
            "widget": widgets["metric_card"],
            "position": {"x": 3, "y": 0, "w": 3, "h": 2},
            "config": {
                "title": "Active Subjects",
                "dataset": "ADSL",
                "field": "USUBJID",
                "calculation": "count",
                "filters": [{"field": "DCDECOD", "operator": "!=", "value": "COMPLETED"}]
            }
        },
        {
            "widget": widgets["line_chart"],
            "position": {"x": 6, "y": 0, "w": 6, "h": 4},
            "config": {
                "title": "Enrollment Over Time",
                "dataset": "ADSL",
                "xAxis": "RANDDT",
                "yAxis": "USUBJID",
                "groupBy": "ARM",
                "chartType": "line"
            }
        },
        {
            "widget": widgets["bar_chart"],
            "position": {"x": 0, "y": 2, "w": 6, "h": 3},
            "config": {
                "title": "Enrollment by Site",
                "dataset": "ADSL",
                "categoryField": "SITEID",
                "valueField": "USUBJID",
                "calculation": "count"
            }
        }
    ]
    
    for widget_config in widget_configs:
        widget_data = DashboardWidgetBase(
            dashboard_template_id=db_dashboard.id,
            widget_definition_id=widget_config["widget"].id,
            instance_config=widget_config["config"],
            position=widget_config["position"]
        )
        crud_dashboard.add_widget_to_dashboard(db, db_dashboard.id, widget_data)
    
    print(f"  ✓ Created overview dashboard with {len(widget_configs)} widgets: {db_dashboard.id}")
    
    # Safety Dashboard
    safety_dashboard = DashboardTemplateCreate(
        code="safety_monitoring",
        name="Safety Monitoring Dashboard",
        description="Dashboard for monitoring adverse events and safety signals",
        category=DashboardCategory.SAFETY,
        layout_config={
            "type": "grid",
            "breakpoints": {"lg": 1200, "md": 996, "sm": 768, "xs": 480, "xxs": 0},
            "cols": {"lg": 12, "md": 10, "sm": 6, "xs": 4, "xxs": 2},
            "rowHeight": 60,
            "margin": [10, 10]
        }
    )
    
    db_dashboard = crud_dashboard.create_dashboard(db, safety_dashboard, admin_user)
    dashboards["safety_monitoring"] = db_dashboard
    
    # Add widgets to safety dashboard
    safety_widgets = [
        {
            "widget": widgets["metric_card"],
            "position": {"x": 0, "y": 0, "w": 3, "h": 2},
            "config": {
                "title": "Total AEs",
                "dataset": "ADAE",
                "field": "AESEQ",
                "calculation": "count"
            }
        },
        {
            "widget": widgets["metric_card"],
            "position": {"x": 3, "y": 0, "w": 3, "h": 2},
            "config": {
                "title": "Serious AEs",
                "dataset": "ADAE",
                "field": "AESEQ",
                "calculation": "count",
                "filters": [{"field": "AESER", "operator": "=", "value": "Y"}]
            }
        },
        {
            "widget": widgets["bar_chart"],
            "position": {"x": 6, "y": 0, "w": 6, "h": 4},
            "config": {
                "title": "AEs by System Organ Class",
                "dataset": "ADAE",
                "categoryField": "AESOC",
                "valueField": "AESEQ",
                "calculation": "count"
            }
        },
        {
            "widget": widgets["data_table"],
            "position": {"x": 0, "y": 4, "w": 12, "h": 4},
            "config": {
                "title": "Recent Adverse Events",
                "dataset": "ADAE",
                "columns": ["USUBJID", "AETERM", "AESOC", "AESEV", "AESER", "AESTDT"]
            }
        }
    ]
    
    for widget_config in safety_widgets:
        widget_data = DashboardWidgetBase(
            dashboard_template_id=db_dashboard.id,
            widget_definition_id=widget_config["widget"].id,
            instance_config=widget_config["config"],
            position=widget_config["position"]
        )
        crud_dashboard.add_widget_to_dashboard(db, db_dashboard.id, widget_data)
    
    print(f"  ✓ Created safety dashboard with {len(safety_widgets)} widgets: {db_dashboard.id}")
    
    return dashboards


def create_default_menus(db: Session, admin_user: User, dashboards: dict) -> dict:
    """Create default menu templates"""
    print("Creating default menu templates...")
    
    menus = {}
    
    # Standard Study Menu
    standard_menu = MenuTemplateCreate(
        code="standard_study_menu",
        name="Standard Study Menu",
        description="Standard navigation menu for clinical studies",
        menu_structure={
            "items": [
                {
                    "id": "overview",
                    "type": "dashboard",
                    "label": "Overview",
                    "icon": "LayoutDashboard",
                    "dashboard_code": "clinical_overview",
                    "order": 1
                },
                {
                    "id": "enrollment",
                    "type": "group",
                    "label": "Enrollment",
                    "icon": "Users",
                    "order": 2,
                    "children": [
                        {
                            "id": "enrollment_summary",
                            "type": "dashboard",
                            "label": "Summary",
                            "icon": "BarChart3",
                            "dashboard_code": "clinical_overview",
                            "order": 1
                        },
                        {
                            "id": "enrollment_timeline",
                            "type": "dashboard",
                            "label": "Timeline",
                            "icon": "TrendingUp",
                            "dashboard_code": "clinical_overview",
                            "order": 2
                        }
                    ]
                },
                {
                    "id": "safety",
                    "type": "group",
                    "label": "Safety",
                    "icon": "Shield",
                    "order": 3,
                    "permissions": ["view_safety_data"],
                    "children": [
                        {
                            "id": "safety_overview",
                            "type": "dashboard",
                            "label": "Overview",
                            "icon": "Activity",
                            "dashboard_code": "safety_monitoring",
                            "order": 1
                        },
                        {
                            "id": "adverse_events",
                            "type": "dashboard",
                            "label": "Adverse Events",
                            "icon": "AlertTriangle",
                            "dashboard_code": "safety_monitoring",
                            "order": 2
                        }
                    ]
                },
                {
                    "id": "divider1",
                    "type": "separator",
                    "label": "",
                    "order": 4
                },
                {
                    "id": "reports",
                    "type": "link",
                    "label": "Reports",
                    "icon": "FileText",
                    "url": "/reports",
                    "order": 5
                }
            ]
        }
    )
    
    db_menu = crud_menu.create_menu(db, standard_menu, admin_user)
    menus["standard_study_menu"] = db_menu
    print(f"  ✓ Created standard study menu: {db_menu.id}")
    
    # Safety-Focused Menu
    safety_menu = MenuTemplateCreate(
        code="safety_focused_menu",
        name="Safety-Focused Menu",
        description="Navigation menu emphasizing safety monitoring",
        menu_structure={
            "items": [
                {
                    "id": "safety_dashboard",
                    "type": "dashboard",
                    "label": "Safety Overview",
                    "icon": "Shield",
                    "dashboard_code": "safety_monitoring",
                    "order": 1
                },
                {
                    "id": "ae_monitoring",
                    "type": "group",
                    "label": "AE Monitoring",
                    "icon": "AlertCircle",
                    "order": 2,
                    "children": [
                        {
                            "id": "all_aes",
                            "type": "dashboard",
                            "label": "All AEs",
                            "icon": "List",
                            "dashboard_code": "safety_monitoring",
                            "order": 1
                        },
                        {
                            "id": "serious_aes",
                            "type": "dashboard",
                            "label": "Serious AEs",
                            "icon": "AlertTriangle",
                            "dashboard_code": "safety_monitoring",
                            "order": 2,
                            "permissions": ["view_serious_aes"]
                        }
                    ]
                },
                {
                    "id": "study_overview",
                    "type": "dashboard",
                    "label": "Study Overview",
                    "icon": "LayoutDashboard",
                    "dashboard_code": "clinical_overview",
                    "order": 3
                }
            ]
        }
    )
    
    db_menu = crud_menu.create_menu(db, safety_menu, admin_user)
    menus["safety_focused_menu"] = db_menu
    print(f"  ✓ Created safety-focused menu: {db_menu.id}")
    
    return menus


def main():
    """Main function to run the seeding process"""
    print("Starting widget library and dashboard template seeding...")
    
    # Get database session
    with Session(engine) as session:
        try:
            # Get or create admin user for seeding
            admin_user = session.exec(
                select(User).where(User.email == "admin@sagarmatha.ai")
            ).first()
            
            if not admin_user:
                print("Error: Admin user not found. Please create an admin user first.")
                return
            
            print(f"Using admin user: {admin_user.email}")
            
            # Create default widgets
            widgets = create_default_widgets(session, admin_user)
            
            # Create default dashboard templates
            dashboards = create_default_dashboards(session, admin_user, widgets)
            
            # Create default menu templates
            menus = create_default_menus(session, admin_user, dashboards)
            
            print("\n✅ Seeding completed successfully!")
            print(f"Created {len(widgets)} widget definitions")
            print(f"Created {len(dashboards)} dashboard templates")
            print(f"Created {len(menus)} menu templates")
            
        except Exception as e:
            print(f"❌ Error during seeding: {str(e)}")
            session.rollback()
            raise


if __name__ == "__main__":
    main()