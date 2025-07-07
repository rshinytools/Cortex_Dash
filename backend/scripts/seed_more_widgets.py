#!/usr/bin/env python3
# ABOUTME: Script to seed additional widget types into the database
# ABOUTME: Includes bar chart, scatter plot, heatmap, KPI comparison, and patient timeline widgets

import sys
import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlmodel import Session, select
from app.core.db import engine
from app.models.widget import WidgetDefinition, WidgetCategory
from app.models.user import User

# Define the additional widgets to seed
ADDITIONAL_WIDGETS = [
    {
        "code": "bar_chart",
        "category": WidgetCategory.CHARTS,
        "name": "Bar Chart",
        "description": "Categorical data comparison with vertical and horizontal bar charts",
        "default_config": {
            "xAxisField": "category",
            "yAxisFields": [{"field": "value", "label": "Value"}],
            "orientation": "vertical",
            "showGrid": True,
            "showLegend": True,
            "showTooltip": True,
            "showValues": False,
            "valueFormat": "number",
            "decimals": 2,
            "sortBy": "none"
        },
        "config_schema": {
            "type": "object",
            "properties": {
                "xAxisField": {"type": "string", "description": "Field for x-axis categories"},
                "yAxisFields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"},
                            "label": {"type": "string"},
                            "color": {"type": "string"},
                            "stackId": {"type": "string"}
                        },
                        "required": ["field", "label"]
                    }
                },
                "orientation": {"type": "string", "enum": ["vertical", "horizontal"]},
                "xAxisLabel": {"type": "string"},
                "yAxisLabel": {"type": "string"},
                "showGrid": {"type": "boolean"},
                "showLegend": {"type": "boolean"},
                "showTooltip": {"type": "boolean"},
                "showValues": {"type": "boolean"},
                "valueFormat": {"type": "string", "enum": ["number", "percentage", "currency"]},
                "decimals": {"type": "integer", "minimum": 0, "maximum": 4},
                "sortBy": {"type": "string", "enum": ["value", "label", "none"]},
                "sortOrder": {"type": "string", "enum": ["asc", "desc"]},
                "maxBars": {"type": "integer", "minimum": 1}
            },
            "required": ["xAxisField", "yAxisFields"]
        },
        "size_constraints": {
            "minWidth": 3,
            "minHeight": 3,
            "maxWidth": 12,
            "maxHeight": 8,
            "defaultWidth": 6,
            "defaultHeight": 4
        },
        "data_requirements": {
            "datasets": ["aggregated"],
            "minimum_fields": ["category", "value"]
        },
        "data_contract": {
            "required_fields": [
                {"name": "category", "type": "string", "description": "Category name for x-axis"},
                {"name": "value", "type": "number", "description": "Numeric value for bar height"}
            ],
            "optional_fields": [
                {"name": "series", "type": "string", "description": "Series identifier for grouped bars"}
            ],
            "data_sources": {
                "primary": {"dataset_type": "aggregated", "refresh_rate": 3600}
            }
        }
    },
    {
        "code": "scatter_plot",
        "category": WidgetCategory.CHARTS,
        "name": "Scatter Plot",
        "description": "Correlation analysis between two variables with trend lines",
        "default_config": {
            "xAxisField": "xValue",
            "yAxisField": "yValue",
            "showGrid": True,
            "showLegend": True,
            "showTooltip": True,
            "showTrendLine": False,
            "trendLineType": "linear",
            "valueFormat": "number",
            "decimals": 2
        },
        "config_schema": {
            "type": "object",
            "properties": {
                "xAxisField": {"type": "string", "description": "Field for x-axis values"},
                "yAxisField": {"type": "string", "description": "Field for y-axis values"},
                "xAxisLabel": {"type": "string"},
                "yAxisLabel": {"type": "string"},
                "groupByField": {"type": "string", "description": "Field to group data points"},
                "sizeField": {"type": "string", "description": "Field for bubble size"},
                "colorField": {"type": "string", "description": "Field for color mapping"},
                "showGrid": {"type": "boolean"},
                "showLegend": {"type": "boolean"},
                "showTooltip": {"type": "boolean"},
                "showTrendLine": {"type": "boolean"},
                "trendLineType": {"type": "string", "enum": ["linear", "polynomial", "exponential"]},
                "valueFormat": {"type": "string", "enum": ["number", "percentage", "currency"]},
                "decimals": {"type": "integer", "minimum": 0, "maximum": 4},
                "minSize": {"type": "integer", "minimum": 10, "maximum": 100},
                "maxSize": {"type": "integer", "minimum": 50, "maximum": 500}
            },
            "required": ["xAxisField", "yAxisField"]
        },
        "size_constraints": {
            "minWidth": 4,
            "minHeight": 3,
            "maxWidth": 12,
            "maxHeight": 8,
            "defaultWidth": 6,
            "defaultHeight": 4
        },
        "data_requirements": {
            "datasets": ["analysis"],
            "minimum_fields": ["xValue", "yValue"]
        },
        "data_contract": {
            "required_fields": [
                {"name": "xValue", "type": "number", "description": "X-axis numeric value"},
                {"name": "yValue", "type": "number", "description": "Y-axis numeric value"}
            ],
            "optional_fields": [
                {"name": "id", "type": "string", "description": "Unique identifier for each point", "sdtm_mapping": "USUBJID"},
                {"name": "group", "type": "string", "description": "Grouping variable for color coding", "sdtm_mapping": "ARM"}
            ],
            "data_sources": {
                "primary": {"dataset_type": "analysis", "refresh_rate": 3600}
            }
        }
    },
    {
        "code": "heatmap",
        "category": WidgetCategory.CHARTS,
        "name": "Heatmap",
        "description": "Matrix visualization with color intensity for correlation data",
        "default_config": {
            "xAxisField": "xCategory",
            "yAxisField": "yCategory",
            "valueField": "value",
            "colorScale": "sequential",
            "minColor": "#eff6ff",
            "midColor": "#3b82f6",
            "maxColor": "#1e3a8a",
            "showValues": True,
            "showTooltip": True,
            "valueFormat": "number",
            "decimals": 2,
            "cellSize": 40,
            "cellGap": 2,
            "showLegend": True
        },
        "config_schema": {
            "type": "object",
            "properties": {
                "xAxisField": {"type": "string", "description": "Field for x-axis categories"},
                "yAxisField": {"type": "string", "description": "Field for y-axis categories"},
                "valueField": {"type": "string", "description": "Field for cell values"},
                "xAxisLabel": {"type": "string"},
                "yAxisLabel": {"type": "string"},
                "colorScale": {"type": "string", "enum": ["sequential", "diverging", "custom"]},
                "minColor": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
                "midColor": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
                "maxColor": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
                "showValues": {"type": "boolean"},
                "showTooltip": {"type": "boolean"},
                "valueFormat": {"type": "string", "enum": ["number", "percentage", "currency"]},
                "decimals": {"type": "integer", "minimum": 0, "maximum": 4},
                "cellSize": {"type": "integer", "minimum": 20, "maximum": 100},
                "cellGap": {"type": "integer", "minimum": 0, "maximum": 10},
                "showLegend": {"type": "boolean"},
                "legendTitle": {"type": "string"},
                "sortX": {"type": "string", "enum": ["asc", "desc", "none"]},
                "sortY": {"type": "string", "enum": ["asc", "desc", "none"]}
            },
            "required": ["xAxisField", "yAxisField", "valueField"]
        },
        "size_constraints": {
            "minWidth": 4,
            "minHeight": 4,
            "maxWidth": 12,
            "maxHeight": 10,
            "defaultWidth": 8,
            "defaultHeight": 6
        },
        "data_requirements": {
            "datasets": ["matrix"],
            "minimum_fields": ["xCategory", "yCategory", "value"]
        },
        "data_contract": {
            "required_fields": [
                {"name": "xCategory", "type": "string", "description": "X-axis category"},
                {"name": "yCategory", "type": "string", "description": "Y-axis category"},
                {"name": "value", "type": "number", "description": "Cell value for color intensity"}
            ],
            "data_sources": {
                "primary": {"dataset_type": "matrix", "refresh_rate": 86400}
            }
        }
    },
    {
        "code": "kpi_comparison",
        "category": WidgetCategory.SPECIALIZED,
        "name": "KPI Comparison",
        "description": "Compare key performance indicators across periods or groups",
        "default_config": {
            "kpiField": "value",
            "comparisonType": "period-over-period",
            "displayType": "cards",
            "valueFormat": "number",
            "decimals": 2,
            "showTrend": True,
            "showVariance": True,
            "colorCoding": True
        },
        "config_schema": {
            "type": "object",
            "properties": {
                "kpiField": {"type": "string", "description": "Field containing KPI value"},
                "groupByField": {"type": "string", "description": "Field to group comparisons"},
                "comparisonType": {
                    "type": "string",
                    "enum": ["period-over-period", "group-comparison", "target-vs-actual", "benchmark"]
                },
                "currentPeriodField": {"type": "string"},
                "previousPeriodField": {"type": "string"},
                "targetField": {"type": "string"},
                "benchmarkField": {"type": "string"},
                "displayType": {"type": "string", "enum": ["cards", "table", "progress", "gauge"]},
                "valueFormat": {"type": "string", "enum": ["number", "percentage", "currency"]},
                "decimals": {"type": "integer", "minimum": 0, "maximum": 4},
                "showTrend": {"type": "boolean"},
                "showVariance": {"type": "boolean"},
                "trendThreshold": {"type": "number"},
                "goodDirection": {"type": "string", "enum": ["up", "down"]},
                "colorCoding": {"type": "boolean"},
                "sortBy": {"type": "string", "enum": ["name", "value", "change"]},
                "sortOrder": {"type": "string", "enum": ["asc", "desc"]}
            },
            "required": ["kpiField", "comparisonType"]
        },
        "size_constraints": {
            "minWidth": 3,
            "minHeight": 3,
            "maxWidth": 12,
            "maxHeight": 8,
            "defaultWidth": 6,
            "defaultHeight": 4
        },
        "data_requirements": {
            "datasets": ["kpi_summary"],
            "minimum_fields": ["kpiValue"]
        },
        "data_contract": {
            "required_fields": [
                {"name": "kpiValue", "type": "number", "description": "Current KPI value"}
            ],
            "optional_fields": [
                {"name": "groupName", "type": "string", "description": "Group or category name"},
                {"name": "previousValue", "type": "number", "description": "Previous period value for comparison"},
                {"name": "targetValue", "type": "number", "description": "Target or goal value"}
            ],
            "data_sources": {
                "primary": {"dataset_type": "kpi_summary", "refresh_rate": 3600}
            }
        }
    },
    {
        "code": "patient_timeline",
        "category": WidgetCategory.SPECIALIZED,
        "name": "Patient Timeline",
        "description": "Chronological visualization of patient events and milestones",
        "default_config": {
            "dateField": "eventDate",
            "eventTypeField": "eventType",
            "displayType": "vertical",
            "showEventDetails": True,
            "showLegend": True,
            "sortOrder": "asc",
            "compactMode": False
        },
        "config_schema": {
            "type": "object",
            "properties": {
                "dateField": {"type": "string", "description": "Field containing event date"},
                "eventTypeField": {"type": "string", "description": "Field containing event type"},
                "eventDescriptionField": {"type": "string"},
                "patientIdField": {"type": "string"},
                "severityField": {"type": "string"},
                "categoryField": {"type": "string"},
                "displayType": {"type": "string", "enum": ["vertical", "horizontal", "gantt"]},
                "groupByPatient": {"type": "boolean"},
                "eventTypes": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "color": {"type": "string"},
                            "icon": {"type": "string", "enum": ["calendar", "pill", "heart", "activity", "file", "alert"]}
                        }
                    }
                },
                "dateFormat": {"type": "string"},
                "showEventDetails": {"type": "boolean"},
                "showLegend": {"type": "boolean"},
                "maxEventsPerPatient": {"type": "integer", "minimum": 1},
                "sortOrder": {"type": "string", "enum": ["asc", "desc"]},
                "highlightSevere": {"type": "boolean"},
                "severityThreshold": {"type": ["string", "number"]},
                "compactMode": {"type": "boolean"}
            },
            "required": ["dateField", "eventTypeField"]
        },
        "size_constraints": {
            "minWidth": 4,
            "minHeight": 4,
            "maxWidth": 12,
            "maxHeight": 10,
            "defaultWidth": 8,
            "defaultHeight": 6
        },
        "data_requirements": {
            "datasets": ["events", "ADAE", "ADCM"],
            "minimum_fields": ["eventDate", "eventType"]
        },
        "data_contract": {
            "required_fields": [
                {"name": "eventDate", "type": "date", "description": "Date/time of the event", "sdtm_mapping": "DTC"},
                {"name": "eventType", "type": "string", "description": "Type or category of event"}
            ],
            "optional_fields": [
                {"name": "patientId", "type": "string", "description": "Patient identifier", "sdtm_mapping": "USUBJID"},
                {"name": "eventDescription", "type": "string", "description": "Detailed description of the event"},
                {"name": "severity", "type": "string", "description": "Severity or grade of event", "sdtm_mapping": "SEV"}
            ],
            "data_sources": {
                "primary": {"dataset_type": "events", "refresh_rate": 3600},
                "secondary": [
                    {"dataset_type": "ADAE", "join_on": "patientId"},
                    {"dataset_type": "ADCM", "join_on": "patientId"}
                ]
            }
        }
    }
]


async def seed_additional_widgets():
    """Seed additional widget types into the database"""
    
    with Session(engine) as session:
        # Get the system user for created_by
        system_user = session.exec(
            select(User).where(User.email == "admin@sagarmatha.ai")
        ).first()
        
        if not system_user:
            print("System user not found. Please ensure the system user exists.")
            return
        
        # Check which widgets already exist
        existing_widgets = session.exec(select(WidgetDefinition)).all()
        existing_codes = {w.code for w in existing_widgets}
        
        widgets_created = 0
        widgets_skipped = 0
        
        for widget_data in ADDITIONAL_WIDGETS:
            if widget_data["code"] in existing_codes:
                print(f"Widget {widget_data['name']} already exists. Skipping...")
                widgets_skipped += 1
                continue
            
            # Create the widget
            widget = WidgetDefinition(
                code=widget_data["code"],
                category=widget_data["category"],
                name=widget_data["name"],
                description=widget_data["description"],
                default_config=widget_data["default_config"],
                config_schema=widget_data["config_schema"],
                size_constraints=widget_data["size_constraints"],
                data_requirements=widget_data["data_requirements"],
                data_contract=widget_data["data_contract"],
                created_by=system_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True
            )
            
            session.add(widget)
            widgets_created += 1
            print(f"Created widget: {widget.name}")
        
        # Commit all changes
        session.commit()
        
        print(f"\nSummary:")
        print(f"  Widgets created: {widgets_created}")
        print(f"  Widgets skipped: {widgets_skipped}")
        print(f"  Total widgets in database: {len(existing_widgets) + widgets_created}")


if __name__ == "__main__":
    print("Seeding additional widgets...")
    asyncio.run(seed_additional_widgets())
    print("Done!")