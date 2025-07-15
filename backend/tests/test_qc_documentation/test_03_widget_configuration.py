# ABOUTME: Tests documenting all widget types and their configurations
# ABOUTME: Shows metric, chart, table, text, and composite widgets with data mappings
"""
Widget Configuration Documentation
==================================

This test suite documents all widget types available in the dashboard system.
Widgets are the building blocks of dashboards, displaying data in various formats.

Widget Types:
1. metric - Single value KPIs (count, percentage, average, sum)
2. chart - Visualizations (line, bar, pie, donut, scatter, heatmap)
3. table - Data grids with sorting, filtering, and export
4. text - Markdown content for instructions or notes
5. composite - Multiple related metrics in one widget

Key Concepts:
- Each widget has a unique ID within the dashboard
- Widgets define their data requirements
- Position and size use grid layout system
- Real-time updates via WebSocket optional
"""

import pytest
from typing import Dict, List, Any
from sqlmodel import Session
from app.models import DashboardTemplate, User
from app.schemas.dashboard_template import DashboardTemplateCreate
from app.crud.dashboard_template import dashboard_template as crud_template


class TestWidgetConfigurations:
    """
    QC Documentation: Widget Types and Configuration Options
    
    This test class documents all widget types and their configuration options.
    Each widget type serves specific data visualization needs.
    
    Business Requirements:
    - Support various data visualization types
    - Enable real-time data updates
    - Provide interactive features (drill-down, export)
    - Maintain performance with large datasets
    """
    
    def test_metric_widget_types(self, db: Session, normal_user: User):
        """
        Test Case: All metric widget variations
        
        Purpose: Display single numeric values with formatting
        Use Cases: KPIs, counts, percentages, averages
        
        Configuration options:
        - metric_type: count, sum, average, percentage, ratio
        - format: number, currency, percentage, duration
        - comparison: previous period, target, baseline
        - color thresholds: conditional formatting
        """
        template_data = DashboardTemplateCreate(
            name="Metric Widget Showcase",
            description="All metric widget types and configurations",
            category="demo",
            version="1.0.0",
            menu_structure=[
                {
                    "id": "metrics-dashboard",
                    "label": "Metric Examples",
                    "type": "dashboard",
                    "dashboard_config": {
                        "layout": "grid",
                        "widgets": [
                            # Simple count metric
                            {
                                "id": "total-subjects",
                                "type": "metric",
                                "title": "Total Subjects",
                                "description": "Currently enrolled subjects",
                                "position": {"x": 0, "y": 0, "w": 2, "h": 2},
                                "config": {
                                    "metric_type": "count",
                                    "data_field": "subjects.id",
                                    "format": "number",
                                    "decimal_places": 0,
                                    "thousand_separator": True
                                }
                            },
                            # Percentage metric with color coding
                            {
                                "id": "screen-failure-rate",
                                "type": "metric",
                                "title": "Screen Failure Rate",
                                "position": {"x": 2, "y": 0, "w": 2, "h": 2},
                                "config": {
                                    "metric_type": "percentage",
                                    "numerator_field": "subjects.screen_failed",
                                    "denominator_field": "subjects.screened",
                                    "format": "percentage",
                                    "decimal_places": 1,
                                    "invert_colors": True,  # Lower is better
                                    "color_thresholds": [
                                        {"value": 20, "color": "red", "label": "High"},
                                        {"value": 10, "color": "yellow", "label": "Medium"},
                                        {"value": 0, "color": "green", "label": "Low"}
                                    ]
                                }
                            },
                            # Average with comparison
                            {
                                "id": "avg-enrollment-time",
                                "type": "metric",
                                "title": "Avg. Days to Enrollment",
                                "position": {"x": 4, "y": 0, "w": 2, "h": 2},
                                "config": {
                                    "metric_type": "average",
                                    "data_field": "subjects.days_to_enrollment",
                                    "format": "number",
                                    "decimal_places": 1,
                                    "suffix": " days",
                                    "comparison": {
                                        "type": "target",
                                        "target_value": 14,
                                        "show_difference": True,
                                        "show_arrow": True
                                    }
                                }
                            },
                            # Sum with currency format
                            {
                                "id": "total-budget-spent",
                                "type": "metric",
                                "title": "Budget Utilized",
                                "position": {"x": 0, "y": 2, "w": 2, "h": 2},
                                "config": {
                                    "metric_type": "sum",
                                    "data_field": "financials.amount_spent",
                                    "format": "currency",
                                    "currency_code": "USD",
                                    "decimal_places": 0,
                                    "comparison": {
                                        "type": "percentage_of_total",
                                        "total_field": "financials.total_budget",
                                        "show_progress_bar": True
                                    }
                                }
                            },
                            # Ratio metric
                            {
                                "id": "subject-site-ratio",
                                "type": "metric",
                                "title": "Subjects per Site",
                                "position": {"x": 2, "y": 2, "w": 2, "h": 2},
                                "config": {
                                    "metric_type": "ratio",
                                    "numerator_field": "subjects.enrolled",
                                    "denominator_field": "sites.active",
                                    "format": "number",
                                    "decimal_places": 1,
                                    "prefix": "~",
                                    "suffix": " subjects/site"
                                }
                            },
                            # Metric with sparkline
                            {
                                "id": "enrollment-trend",
                                "type": "metric",
                                "title": "Weekly Enrollment",
                                "position": {"x": 4, "y": 2, "w": 2, "h": 2},
                                "config": {
                                    "metric_type": "count",
                                    "data_field": "subjects.enrolled_this_week",
                                    "format": "number",
                                    "show_sparkline": True,
                                    "sparkline_field": "subjects.weekly_enrollment_history",
                                    "sparkline_type": "line",
                                    "comparison": {
                                        "type": "previous_period",
                                        "period": "week",
                                        "show_percentage_change": True
                                    }
                                }
                            }
                        ]
                    }
                }
            ],
            data_requirements=[
                {
                    "widget_id": "total-subjects",
                    "dataset": "subjects",
                    "required_fields": ["id"],
                    "data_config": {
                        "fields": {"id": {"data_type": "string", "required": True}},
                        "aggregation": "count"
                    }
                },
                {
                    "widget_id": "screen-failure-rate",
                    "dataset": "subjects",
                    "required_fields": ["screened", "screen_failed"],
                    "data_config": {
                        "fields": {
                            "screened": {"data_type": "boolean", "required": True},
                            "screen_failed": {"data_type": "boolean", "required": True}
                        }
                    }
                },
                {
                    "widget_id": "avg-enrollment-time",
                    "dataset": "subjects",
                    "required_fields": ["days_to_enrollment"],
                    "data_config": {
                        "fields": {"days_to_enrollment": {"data_type": "number", "required": True}},
                        "aggregation": "average"
                    }
                },
                {
                    "widget_id": "total-budget-spent",
                    "dataset": "financials",
                    "required_fields": ["amount_spent", "total_budget"],
                    "data_config": {
                        "fields": {
                            "amount_spent": {"data_type": "number", "required": True},
                            "total_budget": {"data_type": "number", "required": True}
                        }
                    }
                },
                {
                    "widget_id": "subject-site-ratio",
                    "dataset": "multi",
                    "required_fields": ["subjects.enrolled", "sites.active"],
                    "data_config": {
                        "joins": [
                            {"from": "subjects", "to": "sites", "on": "site_id"}
                        ]
                    }
                },
                {
                    "widget_id": "enrollment-trend",
                    "dataset": "subjects",
                    "required_fields": ["enrolled_date"],
                    "data_config": {
                        "time_series": True,
                        "time_field": "enrolled_date",
                        "aggregation_period": "week"
                    }
                }
            ]
        )
        
        template = crud_template.create_with_owner(
            db=db, obj_in=template_data, owner_id=normal_user.id, org_id=normal_user.org_id
        )
        
        # Verify metric configurations
        widgets = template.menu_structure[0]["dashboard_config"]["widgets"]
        assert len(widgets) == 6
        
        # Check metric types
        metric_types = {w["config"]["metric_type"] for w in widgets}
        assert metric_types == {"count", "percentage", "average", "sum", "ratio"}
        
        # Verify formatting options
        formats = {w["config"]["format"] for w in widgets}
        assert "currency" in formats
        assert "percentage" in formats
        
        # Check advanced features
        enrollment_trend = next(w for w in widgets if w["id"] == "enrollment-trend")
        assert enrollment_trend["config"]["show_sparkline"] == True
        assert enrollment_trend["config"]["comparison"]["type"] == "previous_period"
    
    def test_chart_widget_types(self, db: Session, normal_user: User):
        """
        Test Case: All chart widget variations
        
        Purpose: Visualize data trends and distributions
        Chart Types: line, bar, pie, donut, scatter, heatmap, waterfall
        
        Features:
        - Multiple series support
        - Interactive legends
        - Drill-down capabilities
        - Export to image/data
        """
        template_data = DashboardTemplateCreate(
            name="Chart Widget Showcase",
            description="All chart types and configurations",
            category="demo",
            version="1.0.0",
            menu_structure=[
                {
                    "id": "charts-dashboard",
                    "label": "Chart Examples",
                    "type": "dashboard",
                    "dashboard_config": {
                        "layout": "grid",
                        "widgets": [
                            # Multi-series line chart
                            {
                                "id": "enrollment-timeline",
                                "type": "chart",
                                "title": "Enrollment Timeline by Site",
                                "position": {"x": 0, "y": 0, "w": 6, "h": 4},
                                "config": {
                                    "chart_type": "line",
                                    "x_axis": {
                                        "field": "date",
                                        "type": "datetime",
                                        "format": "MMM DD",
                                        "label": "Date"
                                    },
                                    "y_axis": {
                                        "field": "cumulative_enrolled",
                                        "type": "number",
                                        "label": "Cumulative Enrollment"
                                    },
                                    "series": {
                                        "group_by": "site_name",
                                        "limit": 10,
                                        "show_total": True
                                    },
                                    "interactions": {
                                        "zoom": True,
                                        "pan": True,
                                        "export": ["png", "csv"]
                                    },
                                    "annotations": [
                                        {
                                            "type": "line",
                                            "value": 500,
                                            "axis": "y",
                                            "label": "Target",
                                            "color": "red",
                                            "style": "dashed"
                                        }
                                    ]
                                }
                            },
                            # Stacked bar chart
                            {
                                "id": "ae-by-severity",
                                "type": "chart",
                                "title": "Adverse Events by Severity",
                                "position": {"x": 0, "y": 4, "w": 3, "h": 3},
                                "config": {
                                    "chart_type": "bar",
                                    "orientation": "vertical",
                                    "stacked": True,
                                    "x_axis": {
                                        "field": "month",
                                        "type": "category",
                                        "label": "Month"
                                    },
                                    "y_axis": {
                                        "field": "count",
                                        "type": "number",
                                        "label": "Number of AEs"
                                    },
                                    "series": {
                                        "group_by": "severity",
                                        "colors": {
                                            "mild": "#FFC107",
                                            "moderate": "#FF9800",
                                            "severe": "#F44336"
                                        }
                                    },
                                    "legend": {
                                        "position": "top",
                                        "interactive": True
                                    }
                                }
                            },
                            # Donut chart with center metric
                            {
                                "id": "site-status-donut",
                                "type": "chart",
                                "title": "Site Status Distribution",
                                "position": {"x": 3, "y": 4, "w": 3, "h": 3},
                                "config": {
                                    "chart_type": "donut",
                                    "data_field": "site_status",
                                    "value_field": "count",
                                    "center_text": {
                                        "type": "total",
                                        "label": "Total Sites"
                                    },
                                    "labels": {
                                        "show": True,
                                        "format": "{name}: {value} ({percentage}%)"
                                    },
                                    "interactions": {
                                        "drill_down": {
                                            "enabled": True,
                                            "target_dashboard": "site-details",
                                            "pass_filters": ["status"]
                                        }
                                    }
                                }
                            },
                            # Scatter plot with regression
                            {
                                "id": "age-response-scatter",
                                "type": "chart",
                                "title": "Age vs Treatment Response",
                                "position": {"x": 0, "y": 7, "w": 4, "h": 4},
                                "config": {
                                    "chart_type": "scatter",
                                    "x_axis": {
                                        "field": "age",
                                        "type": "number",
                                        "label": "Age (years)"
                                    },
                                    "y_axis": {
                                        "field": "response_score",
                                        "type": "number",
                                        "label": "Response Score"
                                    },
                                    "point_options": {
                                        "size_field": "dose_level",
                                        "color_field": "treatment_arm",
                                        "shape_field": "gender"
                                    },
                                    "statistics": {
                                        "show_regression": True,
                                        "show_r_squared": True,
                                        "confidence_interval": 0.95
                                    }
                                }
                            },
                            # Heatmap for correlation
                            {
                                "id": "lab-correlation-heatmap",
                                "type": "chart",
                                "title": "Lab Parameter Correlations",
                                "position": {"x": 4, "y": 7, "w": 2, "h": 4},
                                "config": {
                                    "chart_type": "heatmap",
                                    "x_axis": {
                                        "field": "lab_test_1",
                                        "type": "category"
                                    },
                                    "y_axis": {
                                        "field": "lab_test_2",
                                        "type": "category"
                                    },
                                    "value_field": "correlation_coefficient",
                                    "color_scale": {
                                        "type": "diverging",
                                        "min": -1,
                                        "max": 1,
                                        "center": 0,
                                        "colors": ["#2166AC", "#FFFFFF", "#B2182B"]
                                    },
                                    "cell_labels": {
                                        "show": True,
                                        "format": ".2f"
                                    }
                                }
                            },
                            # Waterfall chart for patient flow
                            {
                                "id": "patient-flow-waterfall",
                                "type": "chart",
                                "title": "Patient Disposition",
                                "position": {"x": 0, "y": 11, "w": 6, "h": 3},
                                "config": {
                                    "chart_type": "waterfall",
                                    "categories": [
                                        {"name": "Screened", "value": 500},
                                        {"name": "Screen Failures", "value": -75},
                                        {"name": "Enrolled", "value": 0, "subtotal": True},
                                        {"name": "Withdrawn", "value": -25},
                                        {"name": "Completed", "value": 0, "total": True}
                                    ],
                                    "colors": {
                                        "increase": "#4CAF50",
                                        "decrease": "#F44336",
                                        "total": "#2196F3"
                                    }
                                }
                            }
                        ]
                    }
                }
            ],
            data_requirements=[
                {
                    "widget_id": "enrollment-timeline",
                    "dataset": "enrollment",
                    "required_fields": ["date", "site_name", "enrolled_count"],
                    "data_config": {
                        "time_series": True,
                        "aggregation": "cumulative_sum"
                    }
                },
                {
                    "widget_id": "ae-by-severity",
                    "dataset": "adverse_events",
                    "required_fields": ["month", "severity", "event_id"],
                    "data_config": {
                        "aggregation": "count",
                        "group_by": ["month", "severity"]
                    }
                },
                {
                    "widget_id": "site-status-donut",
                    "dataset": "sites",
                    "required_fields": ["site_id", "status"],
                    "data_config": {
                        "aggregation": "count",
                        "group_by": "status"
                    }
                },
                {
                    "widget_id": "age-response-scatter",
                    "dataset": "efficacy",
                    "required_fields": ["subject_id", "age", "response_score", "treatment_arm", "gender", "dose_level"],
                    "data_config": {
                        "no_aggregation": True
                    }
                },
                {
                    "widget_id": "lab-correlation-heatmap",
                    "dataset": "lab_correlations",
                    "required_fields": ["lab_test_1", "lab_test_2", "correlation_coefficient"],
                    "data_config": {
                        "pre_calculated": True
                    }
                },
                {
                    "widget_id": "patient-flow-waterfall",
                    "dataset": "disposition",
                    "required_fields": ["category", "count"],
                    "data_config": {
                        "special_calculation": "patient_flow"
                    }
                }
            ]
        )
        
        template = crud_template.create_with_owner(
            db=db, obj_in=template_data, owner_id=normal_user.id, org_id=normal_user.org_id
        )
        
        # Verify chart types
        widgets = template.menu_structure[0]["dashboard_config"]["widgets"]
        chart_types = {w["config"]["chart_type"] for w in widgets}
        assert chart_types == {"line", "bar", "donut", "scatter", "heatmap", "waterfall"}
        
        # Check interactive features
        line_chart = next(w for w in widgets if w["id"] == "enrollment-timeline")
        assert line_chart["config"]["interactions"]["zoom"] == True
        assert "annotations" in line_chart["config"]
        
        # Check drill-down
        donut_chart = next(w for w in widgets if w["id"] == "site-status-donut")
        assert donut_chart["config"]["interactions"]["drill_down"]["enabled"] == True
    
    def test_table_widget_configurations(self, db: Session, normal_user: User):
        """
        Test Case: Table widget with advanced features
        
        Purpose: Display tabular data with sorting, filtering, pagination
        Features: Column formatting, row actions, export, search
        
        Use Cases:
        - Subject listings
        - Query management
        - Audit trails
        - Data review
        """
        template_data = DashboardTemplateCreate(
            name="Table Widget Showcase",
            description="Advanced table configurations",
            category="demo",
            version="1.0.0",
            menu_structure=[
                {
                    "id": "tables-dashboard",
                    "label": "Table Examples",
                    "type": "dashboard",
                    "dashboard_config": {
                        "layout": "grid",
                        "widgets": [
                            # Advanced subject listing table
                            {
                                "id": "subject-listing",
                                "type": "table",
                                "title": "Subject Registry",
                                "position": {"x": 0, "y": 0, "w": 6, "h": 6},
                                "config": {
                                    "columns": [
                                        {
                                            "field": "subject_id",
                                            "header": "Subject ID",
                                            "width": 120,
                                            "frozen": True,  # Frozen column
                                            "sortable": True,
                                            "cell_renderer": "link",
                                            "link_template": "/subjects/{subject_id}"
                                        },
                                        {
                                            "field": "site_name",
                                            "header": "Site",
                                            "width": 150,
                                            "sortable": True,
                                            "filterable": True,
                                            "filter_type": "select"
                                        },
                                        {
                                            "field": "enrollment_date",
                                            "header": "Enrolled",
                                            "width": 100,
                                            "sortable": True,
                                            "format": "date",
                                            "date_format": "MM/DD/YYYY"
                                        },
                                        {
                                            "field": "age",
                                            "header": "Age",
                                            "width": 60,
                                            "sortable": True,
                                            "format": "number",
                                            "align": "right"
                                        },
                                        {
                                            "field": "status",
                                            "header": "Status",
                                            "width": 100,
                                            "filterable": True,
                                            "cell_renderer": "badge",
                                            "badge_colors": {
                                                "active": "green",
                                                "withdrawn": "red",
                                                "completed": "blue"
                                            }
                                        },
                                        {
                                            "field": "compliance_rate",
                                            "header": "Compliance",
                                            "width": 100,
                                            "format": "percentage",
                                            "cell_renderer": "progress_bar",
                                            "color_thresholds": [
                                                {"value": 90, "color": "green"},
                                                {"value": 70, "color": "yellow"},
                                                {"value": 0, "color": "red"}
                                            ]
                                        }
                                    ],
                                    "features": {
                                        "pagination": {
                                            "enabled": True,
                                            "page_size": 25,
                                            "page_size_options": [10, 25, 50, 100]
                                        },
                                        "search": {
                                            "enabled": True,
                                            "placeholder": "Search subjects...",
                                            "fields": ["subject_id", "site_name"]
                                        },
                                        "export": {
                                            "enabled": True,
                                            "formats": ["csv", "excel", "pdf"],
                                            "filename_template": "subjects_{date}"
                                        },
                                        "row_selection": {
                                            "enabled": True,
                                            "mode": "multiple"
                                        },
                                        "column_resize": True,
                                        "column_reorder": True,
                                        "save_state": True  # Remember user preferences
                                    },
                                    "row_actions": [
                                        {
                                            "label": "View Details",
                                            "icon": "eye",
                                            "action": "navigate",
                                            "url": "/subjects/{subject_id}"
                                        },
                                        {
                                            "label": "Download CRF",
                                            "icon": "download",
                                            "action": "download",
                                            "url": "/api/subjects/{subject_id}/crf"
                                        },
                                        {
                                            "label": "Add Query",
                                            "icon": "comment",
                                            "action": "modal",
                                            "modal": "add_query",
                                            "permissions": ["create_query"]
                                        }
                                    ],
                                    "empty_state": {
                                        "message": "No subjects enrolled yet",
                                        "icon": "users",
                                        "action": {
                                            "label": "Import Subjects",
                                            "url": "/import/subjects"
                                        }
                                    }
                                }
                            },
                            # Query management table with grouping
                            {
                                "id": "query-management",
                                "type": "table",
                                "title": "Data Queries",
                                "position": {"x": 0, "y": 6, "w": 6, "h": 4},
                                "config": {
                                    "columns": [
                                        {
                                            "field": "query_id",
                                            "header": "Query ID",
                                            "width": 100
                                        },
                                        {
                                            "field": "subject_id",
                                            "header": "Subject",
                                            "width": 100
                                        },
                                        {
                                            "field": "form_name",
                                            "header": "Form",
                                            "width": 150
                                        },
                                        {
                                            "field": "field_name",
                                            "header": "Field",
                                            "width": 150
                                        },
                                        {
                                            "field": "query_text",
                                            "header": "Query",
                                            "width": 300,
                                            "cell_renderer": "expandable"
                                        },
                                        {
                                            "field": "status",
                                            "header": "Status",
                                            "width": 100,
                                            "filterable": True
                                        },
                                        {
                                            "field": "days_open",
                                            "header": "Days Open",
                                            "width": 80,
                                            "format": "number",
                                            "cell_renderer": "colored_number",
                                            "color_thresholds": [
                                                {"value": 30, "color": "red"},
                                                {"value": 14, "color": "yellow"},
                                                {"value": 0, "color": "green"}
                                            ]
                                        }
                                    ],
                                    "features": {
                                        "grouping": {
                                            "enabled": True,
                                            "default_group_by": "form_name",
                                            "collapsible": True,
                                            "show_counts": True
                                        },
                                        "sorting": {
                                            "enabled": True,
                                            "multi_column": True,
                                            "default_sort": [
                                                {"field": "days_open", "order": "desc"},
                                                {"field": "subject_id", "order": "asc"}
                                            ]
                                        },
                                        "virtual_scroll": True,  # For large datasets
                                        "row_height": "dynamic"  # Adjust for content
                                    }
                                }
                            }
                        ]
                    }
                }
            ],
            data_requirements=[
                {
                    "widget_id": "subject-listing",
                    "dataset": "subjects",
                    "required_fields": [
                        "subject_id", "site_name", "enrollment_date", 
                        "age", "status", "compliance_rate"
                    ],
                    "data_config": {
                        "real_time": False,
                        "cache_duration": 300  # 5 minutes
                    }
                },
                {
                    "widget_id": "query-management",
                    "dataset": "queries",
                    "required_fields": [
                        "query_id", "subject_id", "form_name", "field_name",
                        "query_text", "status", "created_date"
                    ],
                    "data_config": {
                        "calculated_fields": {
                            "days_open": "CURRENT_DATE - created_date"
                        }
                    }
                }
            ]
        )
        
        template = crud_template.create_with_owner(
            db=db, obj_in=template_data, owner_id=normal_user.id, org_id=normal_user.org_id
        )
        
        # Verify table features
        table_widget = template.menu_structure[0]["dashboard_config"]["widgets"][0]
        features = table_widget["config"]["features"]
        
        assert features["pagination"]["enabled"] == True
        assert features["search"]["enabled"] == True
        assert features["export"]["enabled"] == True
        assert features["row_selection"]["mode"] == "multiple"
        
        # Check column renderers
        columns = table_widget["config"]["columns"]
        renderers = {col["cell_renderer"] for col in columns if "cell_renderer" in col}
        assert renderers == {"link", "badge", "progress_bar"}
        
        # Verify row actions
        assert len(table_widget["config"]["row_actions"]) == 3
        action_types = {action["action"] for action in table_widget["config"]["row_actions"]}
        assert action_types == {"navigate", "download", "modal"}
    
    def test_composite_and_text_widgets(self, db: Session, normal_user: User):
        """
        Test Case: Composite metrics and text/markdown widgets
        
        Composite: Multiple related metrics in one widget
        Text: Instructions, notes, or dynamic content
        
        Use Cases:
        - Executive summaries
        - Dashboard instructions
        - Dynamic alerts and notifications
        """
        template_data = DashboardTemplateCreate(
            name="Composite and Text Widgets",
            description="Multi-metric and content widgets",
            category="demo",
            version="1.0.0",
            menu_structure=[
                {
                    "id": "summary-dashboard",
                    "label": "Executive Summary",
                    "type": "dashboard",
                    "dashboard_config": {
                        "layout": "grid",
                        "widgets": [
                            # Composite metric widget
                            {
                                "id": "enrollment-summary",
                                "type": "composite",
                                "title": "Enrollment Overview",
                                "position": {"x": 0, "y": 0, "w": 6, "h": 2},
                                "config": {
                                    "layout": "horizontal",  # or vertical, grid
                                    "metrics": [
                                        {
                                            "id": "screened",
                                            "label": "Screened",
                                            "data_field": "subjects.screened",
                                            "format": "number",
                                            "icon": "user-check",
                                            "color": "blue"
                                        },
                                        {
                                            "id": "enrolled",
                                            "label": "Enrolled",
                                            "data_field": "subjects.enrolled",
                                            "format": "number",
                                            "icon": "user-plus",
                                            "color": "green",
                                            "show_percentage_of": "screened"
                                        },
                                        {
                                            "id": "active",
                                            "label": "Active",
                                            "data_field": "subjects.active",
                                            "format": "number",
                                            "icon": "user",
                                            "color": "primary"
                                        },
                                        {
                                            "id": "completed",
                                            "label": "Completed",
                                            "data_field": "subjects.completed",
                                            "format": "number",
                                            "icon": "user-graduate",
                                            "color": "success",
                                            "show_percentage_of": "enrolled"
                                        }
                                    ],
                                    "show_trend": True,  # Small sparkline for each
                                    "comparison_period": "last_month"
                                }
                            },
                            # Dynamic text widget with markdown
                            {
                                "id": "study-alerts",
                                "type": "text",
                                "title": "Study Alerts & Notifications",
                                "position": {"x": 0, "y": 2, "w": 3, "h": 3},
                                "config": {
                                    "content_type": "dynamic",  # vs static
                                    "data_source": "alerts.current",
                                    "template": """
## Current Alerts ({alert_count})

{#alerts}
### {severity_icon} {title}
**Date:** {date}  
**Impact:** {impact_level}

{description}

---
{/alerts}

{^alerts}
✅ No active alerts at this time.
{/alerts}
                                    """,
                                    "format": "markdown",
                                    "refresh_interval": 60,  # Refresh every minute
                                    "max_items": 5
                                }
                            },
                            # Static instruction text
                            {
                                "id": "dashboard-guide",
                                "type": "text",
                                "title": "Dashboard Guide",
                                "position": {"x": 3, "y": 2, "w": 3, "h": 3},
                                "config": {
                                    "content_type": "static",
                                    "content": """
## How to Use This Dashboard

### Navigation
- Click on any metric to see details
- Use the menu on the left to access other dashboards
- Export data using the ⬇️ button on each widget

### Data Updates
- **Real-time metrics**: Every 5 minutes
- **Reports**: Daily at 6 AM EST
- **Enrollment**: As subjects are entered

### Key Metrics
1. **Screen Failure Rate**: Target < 15%
2. **Enrollment Rate**: Target 10/week
3. **Retention**: Target > 90%

### Need Help?
Contact the data management team:
- Email: dm-team@study.com
- Slack: #study-dashboard
                                    """,
                                    "format": "markdown",
                                    "collapsible": True,
                                    "default_collapsed": False
                                }
                            },
                            # Composite with different layout
                            {
                                "id": "site-performance",
                                "type": "composite",
                                "title": "Top Performing Sites",
                                "position": {"x": 0, "y": 5, "w": 6, "h": 3},
                                "config": {
                                    "layout": "table",  # Tabular layout
                                    "data_source": "sites.top_performers",
                                    "columns": [
                                        {
                                            "field": "site_name",
                                            "header": "Site",
                                            "width": "30%"
                                        },
                                        {
                                            "field": "enrolled",
                                            "header": "Enrolled",
                                            "format": "number",
                                            "width": "15%"
                                        },
                                        {
                                            "field": "screen_failure_rate",
                                            "header": "Screen Fail %",
                                            "format": "percentage",
                                            "width": "15%",
                                            "color_code": True
                                        },
                                        {
                                            "field": "query_rate",
                                            "header": "Queries/Subject",
                                            "format": "number",
                                            "decimal_places": 1,
                                            "width": "20%"
                                        },
                                        {
                                            "field": "performance_score",
                                            "header": "Score",
                                            "format": "number",
                                            "width": "20%",
                                            "cell_renderer": "star_rating",
                                            "max_stars": 5
                                        }
                                    ],
                                    "limit": 5,
                                    "sort_by": "performance_score",
                                    "sort_order": "desc"
                                }
                            }
                        ]
                    }
                }
            ],
            data_requirements=[
                {
                    "widget_id": "enrollment-summary",
                    "dataset": "subjects",
                    "required_fields": ["screened", "enrolled", "active", "completed"],
                    "data_config": {
                        "aggregation": "count",
                        "time_comparison": True
                    }
                },
                {
                    "widget_id": "study-alerts",
                    "dataset": "alerts",
                    "required_fields": ["title", "severity", "date", "impact_level", "description"],
                    "data_config": {
                        "filters": [{"field": "active", "value": True}],
                        "sort": [{"field": "severity", "order": "desc"}]
                    }
                },
                {
                    "widget_id": "site-performance",
                    "dataset": "site_metrics",
                    "required_fields": [
                        "site_name", "enrolled", "screened", "screen_failures",
                        "total_queries", "performance_score"
                    ],
                    "data_config": {
                        "calculated_fields": {
                            "screen_failure_rate": "(screen_failures / screened) * 100",
                            "query_rate": "total_queries / enrolled"
                        }
                    }
                }
            ]
        )
        
        template = crud_template.create_with_owner(
            db=db, obj_in=template_data, owner_id=normal_user.id, org_id=normal_user.org_id
        )
        
        # Verify composite layouts
        widgets = template.menu_structure[0]["dashboard_config"]["widgets"]
        composite_widgets = [w for w in widgets if w["type"] == "composite"]
        
        layouts = {w["config"]["layout"] for w in composite_widgets}
        assert layouts == {"horizontal", "table"}
        
        # Check text widget types
        text_widgets = [w for w in widgets if w["type"] == "text"]
        content_types = {w["config"]["content_type"] for w in text_widgets}
        assert content_types == {"dynamic", "static"}
        
        # Verify dynamic content template
        dynamic_text = next(w for w in text_widgets if w["config"]["content_type"] == "dynamic")
        assert "{#alerts}" in dynamic_text["config"]["template"]  # Mustache-style template