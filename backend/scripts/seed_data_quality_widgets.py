#!/usr/bin/env python3

# ABOUTME: Seed script to populate data quality and validation widgets
# ABOUTME: Creates widget definitions for data quality indicators, compliance status, alerts, and statistical summaries

"""
Seed script for data quality widget library.

Usage:
    python backend/scripts/seed_data_quality_widgets.py

This script creates:
- Data quality indicator widget definitions
- Compliance status widget definitions  
- Alert notification widget definitions
- Statistical summary widget definitions
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
    User
)
from app.crud import widget as crud_widget


def create_data_quality_widgets(db: Session, admin_user: User) -> dict:
    """Create data quality widget definitions"""
    print("Creating data quality widget definitions...")
    
    widgets = {}
    
    # Data Quality Indicator Widget
    data_quality_indicator = WidgetDefinitionCreate(
        code="data_quality_indicator",
        name="Data Quality Indicator",
        description="Display data completeness, accuracy, and quality metrics",
        category=WidgetCategory.METRICS,
        config_schema={
            "type": "object",
            "required": ["title"],
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Widget title",
                    "minLength": 1,
                    "maxLength": 100,
                    "default": "Data Quality"
                },
                "displayType": {
                    "type": "string",
                    "description": "Display format",
                    "enum": ["overview", "detailed", "compact"],
                    "default": "overview"
                },
                "showTrend": {
                    "type": "boolean",
                    "description": "Show quality trend indicator",
                    "default": True
                },
                "showBreakdown": {
                    "type": "boolean",
                    "description": "Show quality breakdown by metric",
                    "default": True
                },
                "thresholds": {
                    "type": "object",
                    "description": "Quality score thresholds",
                    "properties": {
                        "excellent": {"type": "number", "minimum": 0, "maximum": 100, "default": 95},
                        "good": {"type": "number", "minimum": 0, "maximum": 100, "default": 85},
                        "warning": {"type": "number", "minimum": 0, "maximum": 100, "default": 70},
                        "critical": {"type": "number", "minimum": 0, "maximum": 100, "default": 50}
                    }
                },
                "metrics": {
                    "type": "array",
                    "description": "Specific metrics to display",
                    "items": {
                        "type": "string",
                        "enum": ["completeness", "accuracy", "consistency", "timeliness", "validity", "uniqueness"]
                    },
                    "default": ["completeness", "accuracy", "consistency", "timeliness"]
                }
            }
        },
        default_config={
            "displayType": "overview",
            "showTrend": True,
            "showBreakdown": True,
            "thresholds": {
                "excellent": 95,
                "good": 85,
                "warning": 70,
                "critical": 50
            }
        },
        size_constraints={
            "min_width": 3,
            "min_height": 3,
            "max_width": 6,
            "max_height": 6,
            "default_width": 3,
            "default_height": 4
        },
        data_requirements={
            "min_datasets": 1,
            "required_fields": ["overallScore"],
            "supports_aggregation": False,
            "data_source": "quality_metrics"
        }
    )
    
    db_widget = crud_widget.create_widget(db, data_quality_indicator, admin_user)
    widgets["data_quality_indicator"] = db_widget
    print(f"  ✓ Created data quality indicator widget: {db_widget.id}")
    
    # Compliance Status Widget
    compliance_status = WidgetDefinitionCreate(
        code="compliance_status",
        name="Compliance Status",
        description="Show regulatory compliance status and violations",
        category=WidgetCategory.METRICS,
        config_schema={
            "type": "object",
            "required": ["title"],
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Widget title",
                    "default": "Compliance Status"
                },
                "displayType": {
                    "type": "string",
                    "description": "Display format",
                    "enum": ["overview", "detailed", "regulatory", "compact"],
                    "default": "overview"
                },
                "showViolations": {
                    "type": "boolean",
                    "description": "Show compliance violations",
                    "default": True
                },
                "showChecks": {
                    "type": "boolean",
                    "description": "Show compliance check results",
                    "default": True
                },
                "showTrend": {
                    "type": "boolean",
                    "description": "Show compliance trend",
                    "default": True
                },
                "regulations": {
                    "type": "array",
                    "description": "Specific regulations to monitor",
                    "items": {"type": "string"},
                    "default": ["21 CFR Part 11", "ICH E6", "HIPAA"]
                },
                "priorityThreshold": {
                    "type": "string",
                    "description": "Minimum violation severity to display",
                    "enum": ["critical", "high", "medium", "low"],
                    "default": "medium"
                }
            }
        },
        default_config={
            "displayType": "overview",
            "showViolations": True,
            "showChecks": True,
            "showTrend": True,
            "priorityThreshold": "medium"
        },
        size_constraints={
            "min_width": 3,
            "min_height": 3,
            "max_width": 8,
            "max_height": 6,
            "default_width": 4,
            "default_height": 4
        },
        data_requirements={
            "min_datasets": 1,
            "required_fields": ["overallCompliance"],
            "supports_aggregation": False,
            "data_source": "compliance_metrics"
        }
    )
    
    db_widget = crud_widget.create_widget(db, compliance_status, admin_user)
    widgets["compliance_status"] = db_widget
    print(f"  ✓ Created compliance status widget: {db_widget.id}")
    
    # Alert Notification Widget
    alert_notification = WidgetDefinitionCreate(
        code="alert_notification",
        name="Alert Notifications",
        description="Display data alerts and notifications",
        category=WidgetCategory.METRICS,
        config_schema={
            "type": "object",
            "required": ["title"],
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Widget title",
                    "default": "Alerts & Notifications"
                },
                "displayType": {
                    "type": "string",
                    "description": "Display format",
                    "enum": ["list", "grouped", "summary", "timeline"],
                    "default": "list"
                },
                "showResolved": {
                    "type": "boolean",
                    "description": "Show resolved alerts",
                    "default": False
                },
                "maxAlerts": {
                    "type": "number",
                    "description": "Maximum number of alerts to display",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 10
                },
                "severityFilter": {
                    "type": "array",
                    "description": "Filter by alert severity",
                    "items": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low", "info"]
                    },
                    "default": ["critical", "high", "medium"]
                },
                "categoryFilter": {
                    "type": "array",
                    "description": "Filter by alert category",
                    "items": {
                        "type": "string",
                        "enum": ["data_quality", "compliance", "system", "performance", "security"]
                    }
                },
                "autoRefresh": {
                    "type": "boolean",
                    "description": "Automatically refresh alerts",
                    "default": True
                },
                "groupBy": {
                    "type": "string",
                    "description": "Group alerts by property",
                    "enum": ["severity", "category", "date"],
                    "default": "severity"
                }
            }
        },
        default_config={
            "displayType": "list",
            "showResolved": False,
            "maxAlerts": 10,
            "severityFilter": ["critical", "high", "medium"],
            "autoRefresh": True,
            "groupBy": "severity"
        },
        size_constraints={
            "min_width": 3,
            "min_height": 4,
            "max_width": 8,
            "max_height": 8,
            "default_width": 4,
            "default_height": 5
        },
        data_requirements={
            "min_datasets": 1,
            "required_fields": ["alerts"],
            "supports_aggregation": False,
            "data_source": "alerts"
        }
    )
    
    db_widget = crud_widget.create_widget(db, alert_notification, admin_user)
    widgets["alert_notification"] = db_widget
    print(f"  ✓ Created alert notification widget: {db_widget.id}")
    
    # Statistical Summary Widget
    statistical_summary = WidgetDefinitionCreate(
        code="statistical_summary",
        name="Statistical Summary",
        description="Show statistical analysis of datasets",
        category=WidgetCategory.ANALYTICS,
        config_schema={
            "type": "object",
            "required": ["title"],
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Widget title",
                    "default": "Statistical Summary"
                },
                "displayType": {
                    "type": "string",
                    "description": "Display format",
                    "enum": ["overview", "detailed", "comparison", "distribution"],
                    "default": "overview"
                },
                "showOutliers": {
                    "type": "boolean",
                    "description": "Show outlier detection",
                    "default": True
                },
                "showDistribution": {
                    "type": "boolean",
                    "description": "Show data distribution",
                    "default": True
                },
                "showTrend": {
                    "type": "boolean",
                    "description": "Show statistical trends",
                    "default": True
                },
                "variables": {
                    "type": "array",
                    "description": "Specific variables to analyze",
                    "items": {"type": "string"}
                },
                "groupBy": {
                    "type": "string",
                    "description": "Group statistics by field"
                },
                "decimals": {
                    "type": "number",
                    "description": "Number of decimal places",
                    "minimum": 0,
                    "maximum": 6,
                    "default": 2
                }
            }
        },
        default_config={
            "displayType": "overview",
            "showOutliers": True,
            "showDistribution": True,
            "showTrend": True,
            "decimals": 2
        },
        size_constraints={
            "min_width": 4,
            "min_height": 4,
            "max_width": 8,
            "max_height": 8,
            "default_width": 4,
            "default_height": 5
        },
        data_requirements={
            "min_datasets": 1,
            "required_fields": ["variables"],
            "supports_aggregation": True,
            "data_source": "statistical_analysis"
        }
    )
    
    db_widget = crud_widget.create_widget(db, statistical_summary, admin_user)
    widgets["statistical_summary"] = db_widget
    print(f"  ✓ Created statistical summary widget: {db_widget.id}")
    
    return widgets


def get_or_create_admin_user(db: Session) -> User:
    """Get or create admin user for seeding"""
    # Look for existing admin user
    admin_user = db.exec(
        select(User).where(User.email == "admin@sagarmatha.ai")
    ).first()
    
    if not admin_user:
        print("Admin user not found. Please run the main seed script first.")
        sys.exit(1)
    
    return admin_user


def main():
    """Main seeding function"""
    print("🌱 Starting data quality widget seeding...")
    print("=" * 60)
    
    try:
        with Session(engine) as db:
            # Get admin user
            admin_user = get_or_create_admin_user(db)
            print(f"Using admin user: {admin_user.email}")
            
            # Create data quality widgets
            widgets = create_data_quality_widgets(db, admin_user)
            
            # Commit all changes
            db.commit()
            
            print("=" * 60)
            print("✅ Data quality widget seeding completed successfully!")
            print(f"Created {len(widgets)} widget definitions:")
            for widget_code, widget in widgets.items():
                print(f"  - {widget.name} ({widget_code})")
            print()
            print("These widgets are now available for use in dashboards.")
            
    except Exception as e:
        print(f"❌ Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()