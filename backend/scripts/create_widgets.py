# ABOUTME: Script to create initial widget definitions based on our architecture
# ABOUTME: Creates the 5 core widget types with data contracts

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session
from app.core.db import engine
from app.models.widget import WidgetDefinition
from uuid import uuid4
import json

def create_widgets():
    """Create the 5 core widget types from our architecture"""
    
    # Get system user for created_by
    from app.models import User
    from sqlmodel import select
    
    with Session(engine) as db:
        # Get the admin user for created_by
        admin_user = db.exec(select(User).where(User.email == "admin@sagarmatha.ai")).first()
        if not admin_user:
            print("Admin user not found, creating widgets without created_by")
            created_by_id = None
        else:
            created_by_id = admin_user.id
    
    widgets = [
        {
            "name": "KPI Metric Card",
            "code": "kpi_card",
            "type": "metric",
            "category": "metrics",
            "description": "Display key performance indicators with comparisons and trends",
            "data_contract": {
                "required_fields": ["value_field"],
                "optional_fields": ["comparison_field", "target_field", "trend_field"],
                "aggregations": ["SUM", "AVG", "COUNT", "MIN", "MAX"],
                "filters": True,
                "grouping": False
            },
            "default_config": {
                "display": {
                    "show_trend": True,
                    "show_comparison": True,
                    "format": "number",
                    "decimals": 2
                }
            },
            "is_active": True
        },
        {
            "name": "Time Series Chart",
            "code": "time_series",
            "type": "chart",
            "category": "charts",
            "description": "Visualize data trends over time with multiple aggregation periods",
            "data_contract": {
                "required_fields": ["date_field", "value_field"],
                "optional_fields": ["group_field", "filter_field"],
                "aggregations": ["DAILY", "WEEKLY", "MONTHLY", "QUARTERLY"],
                "filters": True,
                "grouping": True
            },
            "default_config": {
                "chart_type": "line",
                "show_legend": True,
                "show_grid": True,
                "interpolation": "linear"
            },
            "is_active": True
        },
        {
            "name": "Distribution Chart",
            "code": "distribution",
            "type": "chart",
            "category": "charts",
            "description": "Show data distribution with various chart types",
            "data_contract": {
                "required_fields": ["category_field", "value_field"],
                "optional_fields": ["sub_category_field"],
                "chart_types": ["pie", "bar", "histogram", "donut"],
                "filters": True,
                "grouping": True
            },
            "default_config": {
                "chart_type": "bar",
                "show_values": True,
                "show_legend": True,
                "orientation": "vertical"
            },
            "is_active": True
        },
        {
            "name": "Data Table",
            "code": "data_table",
            "type": "table",
            "category": "tables",
            "description": "Flexible data tables with sorting, filtering, and computed columns",
            "data_contract": {
                "required_fields": ["columns"],
                "optional_fields": ["computed_columns", "filters", "sort_config"],
                "features": ["sorting", "filtering", "pagination", "export"],
                "exports": ["CSV", "EXCEL", "PDF"]
            },
            "default_config": {
                "pagination": True,
                "page_size": 25,
                "show_filters": True,
                "allow_export": True
            },
            "is_active": True
        },
        {
            "name": "Subject Timeline",
            "code": "timeline",
            "type": "visualization",
            "category": "specialized",
            "description": "Visualize subject events and milestones over time",
            "data_contract": {
                "required_fields": ["subject_field", "date_field", "event_field"],
                "optional_fields": ["duration_field", "category_field", "status_field"],
                "view_modes": ["gantt", "calendar", "list", "swimlane"],
                "filters": True,
                "grouping": True
            },
            "default_config": {
                "view_mode": "gantt",
                "show_milestones": True,
                "color_by": "category",
                "zoom_level": "month"
            },
            "is_active": True
        }
    ]
    
    with Session(engine) as db:
        created_count = 0
        
        for widget_data in widgets:
            # Check if widget already exists
            existing = db.query(WidgetDefinition).filter_by(code=widget_data["code"]).first()
            
            if not existing:
                widget = WidgetDefinition(
                    id=uuid4(),
                    name=widget_data["name"],
                    code=widget_data["code"],
                    type=widget_data["type"],
                    category=widget_data["category"],
                    description=widget_data["description"],
                    data_contract=json.dumps(widget_data["data_contract"]),
                    default_config=json.dumps(widget_data["default_config"]),
                    is_active=widget_data["is_active"],
                    created_by=created_by_id
                )
                db.add(widget)
                created_count += 1
                print(f"Created widget: {widget_data['name']}")
            else:
                print(f"Widget already exists: {widget_data['name']}")
        
        db.commit()
        
        print(f"\n=== Widget Creation Complete ===")
        print(f"Created {created_count} new widgets")
        
        # List all widgets
        all_widgets = db.query(WidgetDefinition).all()
        print(f"Total widgets in system: {len(all_widgets)}")
        for widget in all_widgets:
            print(f"  - {widget.name} ({widget.code}): {widget.type}")

if __name__ == "__main__":
    create_widgets()
    print("\nWidget creation complete!")