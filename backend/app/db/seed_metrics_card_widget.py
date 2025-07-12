#!/usr/bin/env python3

# ABOUTME: Seed script to add the flexible Metrics Card widget to the database
# ABOUTME: This widget supports any data format with flexible aggregations and filters

"""
Seed script for the flexible Metrics Card widget.

This script creates a widget definition that:
- Works with any dataset/column names (not limited to SDTM/ADaM)
- Supports multiple aggregation methods
- Allows complex filter logic
- Provides comparison capabilities
"""

from sqlmodel import Session, select
from datetime import datetime
import uuid
import json

from app.core.db import engine
from app.models import WidgetDefinition, User
from app.models.widget import WidgetCategory


def create_metrics_card_widget():
    """Create and insert the flexible Metrics Card widget definition"""
    
    with Session(engine) as session:
        # Check if widget already exists
        existing = session.exec(
            select(WidgetDefinition).where(WidgetDefinition.code == "metrics_card_flexible")
        ).first()
        
        if existing:
            print(f"Metrics Card widget already exists with ID: {existing.id}")
            return
        
        # Get admin user for created_by
        admin_user = session.exec(
            select(User).where(User.email == "admin@sagarmatha.ai")
        ).first()
        
        if not admin_user:
            print("Admin user not found. Please create an admin user first.")
            return
        
        # Create the widget definition
        metrics_card = WidgetDefinition(
            id=str(uuid.uuid4()),
            code="metrics_card_flexible",
            name="Metrics Card",
            description="Display a single metric with flexible aggregation, filters, and optional comparison",
            category=WidgetCategory.METRICS,
            tags=["metric", "kpi", "aggregation", "comparison"],
            created_by=admin_user.id,
            config_schema={
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Display title for the metric",
                        "minLength": 1,
                        "maxLength": 100
                    },
                    "subtitle": {
                        "type": "string",
                        "description": "Optional subtitle or description",
                        "maxLength": 200
                    },
                    "dataMode": {
                        "type": "string",
                        "enum": ["dynamic", "static"],
                        "description": "Whether to use dynamic data aggregation or static value",
                        "default": "dynamic"
                    },
                    "staticValue": {
                        "type": "object",
                        "description": "Static value configuration (when dataMode is 'static')",
                        "properties": {
                            "value": {
                                "type": "number",
                                "description": "The static numeric value to display"
                            },
                            "comparisonValue": {
                                "type": "number",
                                "description": "Optional static comparison value"
                            }
                        }
                    },
                    "aggregation": {
                        "type": "object",
                        "description": "Aggregation configuration (when dataMode is 'dynamic')",
                        "required": ["method"],
                        "properties": {
                            "method": {
                                "type": "string",
                                "enum": ["COUNT", "COUNT_DISTINCT", "SUM", "AVG", "MIN", "MAX", "MEDIAN"],
                                "description": "Aggregation method to apply"
                            },
                            "field": {
                                "type": "string",
                                "description": "Field to aggregate (optional for COUNT)"
                            },
                            "distinctField": {
                                "type": "string",
                                "description": "Field for COUNT_DISTINCT operation"
                            }
                        }
                    },
                    "filters": {
                        "type": "array",
                        "description": "Filter conditions",
                        "items": {
                            "type": "object",
                            "required": ["logic"],
                            "properties": {
                                "logic": {
                                    "type": "string",
                                    "enum": ["AND", "OR"],
                                    "description": "Logical operator for combining conditions"
                                },
                                "conditions": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "required": ["field", "operator", "value"],
                                        "properties": {
                                            "field": {
                                                "type": "string",
                                                "description": "Field to filter on"
                                            },
                                            "operator": {
                                                "type": "string",
                                                "enum": ["=", "!=", ">", ">=", "<", "<=", "IN", "NOT IN", "CONTAINS", "NOT CONTAINS", "IS NULL", "IS NOT NULL"],
                                                "description": "Comparison operator"
                                            },
                                            "value": {
                                                "description": "Value to compare against"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "comparison": {
                        "type": "object",
                        "description": "Comparison settings",
                        "properties": {
                            "enabled": {
                                "type": "boolean",
                                "description": "Enable comparison with previous period",
                                "default": False
                            },
                            "type": {
                                "type": "string",
                                "enum": ["previous_extract", "previous_period", "baseline"],
                                "description": "Type of comparison",
                                "default": "previous_extract"
                            },
                            "showPercentChange": {
                                "type": "boolean",
                                "description": "Show percentage change",
                                "default": True
                            },
                            "showAbsoluteChange": {
                                "type": "boolean",
                                "description": "Show absolute change",
                                "default": False
                            }
                        }
                    },
                    "display": {
                        "type": "object",
                        "description": "Display configuration",
                        "properties": {
                            "format": {
                                "type": "string",
                                "enum": ["number", "percentage", "currency", "decimal"],
                                "description": "Number format",
                                "default": "number"
                            },
                            "decimals": {
                                "type": "integer",
                                "description": "Number of decimal places",
                                "minimum": 0,
                                "maximum": 6,
                                "default": 0
                            },
                            "prefix": {
                                "type": "string",
                                "description": "Prefix for the value (e.g., '$')",
                                "maxLength": 10
                            },
                            "suffix": {
                                "type": "string",
                                "description": "Suffix for the value (e.g., '%')",
                                "maxLength": 10
                            },
                            "thousandsSeparator": {
                                "type": "boolean",
                                "description": "Use thousands separator",
                                "default": True
                            },
                            "trend": {
                                "type": "object",
                                "description": "Trend indicator configuration",
                                "properties": {
                                    "show": {
                                        "type": "boolean",
                                        "description": "Show trend indicator",
                                        "default": True
                                    },
                                    "inverted": {
                                        "type": "boolean",
                                        "description": "Invert trend colors (good when lower is better)",
                                        "default": False
                                    }
                                }
                            },
                            "icon": {
                                "type": "string",
                                "description": "Optional icon to display",
                                "enum": ["users", "activity", "trending-up", "trending-down", "alert-circle", "check-circle", "info", "bar-chart", "pie-chart", "calendar", "clock", "database", "file-text", "heart", "shield", "star", "target", "zap"]
                            },
                            "color": {
                                "type": "string",
                                "description": "Color scheme",
                                "enum": ["default", "primary", "success", "warning", "danger", "info"],
                                "default": "default"
                            }
                        }
                    }
                }
            },
            default_config={
                "title": "New Metric",
                "dataMode": "dynamic",
                "aggregation": {
                    "method": "COUNT"
                },
                "comparison": {
                    "enabled": False,
                    "type": "previous_extract",
                    "showPercentChange": True,
                    "showAbsoluteChange": False
                },
                "display": {
                    "format": "number",
                    "decimals": 0,
                    "thousandsSeparator": True,
                    "trend": {
                        "show": True,
                        "inverted": False
                    },
                    "color": "default"
                }
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
                "max_datasets": 1,
                "supports_aggregation": True,
                "supports_filters": True,
                "supports_comparison": True,
                "required_capabilities": ["query", "aggregate"]
            },
            is_active=True,
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(metrics_card)
        session.commit()
        
        print(f"✅ Created Metrics Card widget: {metrics_card.id}")
        print(f"   Code: {metrics_card.code}")
        print(f"   Category: {metrics_card.category}")
        print(f"   Version: {metrics_card.version}")


if __name__ == "__main__":
    print("🌱 Seeding Metrics Card widget...")
    create_metrics_card_widget()
    print("✨ Done!")