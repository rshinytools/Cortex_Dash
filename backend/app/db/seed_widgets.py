# ABOUTME: Seed data script for populating the widget library with standard clinical trial widgets
# ABOUTME: Based on patterns found in the old codebase, creates metric, chart, table, and map widgets

from typing import Dict, List, Any
from sqlalchemy.orm import Session
from app.models import WidgetDefinition, WidgetCategory
from app.models.user import User
from app.core.config import settings
import json
import logging
import uuid

logger = logging.getLogger(__name__)

# Widget definitions based on the new flexible widget system
WIDGET_DEFINITIONS: List[Dict[str, Any]] = [
    # Core MetricCard Widget - flexible aggregation widget for any data
    {
        "code": "metric_card",
        "name": "Metric Card",
        "description": "Flexible metric widget that can aggregate any numeric or count data",
        "category": WidgetCategory.METRICS,
        "config_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Widget title"},
                "subtitle": {"type": "string", "description": "Optional subtitle"},
                "icon": {"type": "string", "description": "Optional icon name"},
                "showComparison": {"type": "boolean", "default": True},
                "comparisonLabel": {"type": "string", "default": "vs last extract"}
            },
            "required": ["title"]
        },
        "size_constraints": {
            "minWidth": 2, "minHeight": 2,
            "maxWidth": 4, "maxHeight": 3,
            "defaultWidth": 3, "defaultHeight": 2
        },
        "data_requirements": {
            "dataType": "metric",
            "supportsFiltering": True,
            "supportsComparison": True,
            "supportsGrouping": True
        },
        "data_contract": {
            "aggregation_options": {
                "methods": ["COUNT", "COUNT_DISTINCT", "SUM", "AVG", "MIN", "MAX", "MEDIAN"],
                "supports_grouping": True,
                "supports_unique_by": True
            },
            "filter_options": {
                "supports_complex_logic": True,
                "operators": {
                    "string": ["equals", "not_equals", "contains", "not_contains", "is_null", "not_null", "in_list", "not_in_list"],
                    "numeric": ["equals", "not_equals", "greater_than", "less_than", "greater_than_or_equal", "less_than_or_equal", "between", "is_null", "not_null"],
                    "date": ["equals", "before", "after", "between", "is_null", "not_null"]
                }
            },
            "comparison_options": {
                "types": ["previous_extract", "target_value", "previous_period"],
                "default": "previous_extract"
            },
            "display_options": {
                "formats": ["number", "percentage", "currency"],
                "decimal_places": [0, 1, 2],
                "show_trend": True
            }
        },
        "is_active": True
    },
    
    # Example pre-configured metric widgets (using metric_card as base)
    {
        "code": "total_screened",
        "name": "Total Screened",
        "description": "Shows total number of subjects screened in the study",
        "category": WidgetCategory.METRICS,
        "config_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "default": "Total Screened"},
                "showComparison": {"type": "boolean", "default": True}
            }
        },
        "size_constraints": {
            "minWidth": 2, "minHeight": 2,
            "maxWidth": 4, "maxHeight": 3,
            "defaultWidth": 3, "defaultHeight": 2
        },
        "data_requirements": {
            "dataType": "metric",
            "supportsFiltering": True,
            "supportsComparison": True
        },
        "data_contract": {
            "aggregation_options": {
                "methods": ["COUNT", "COUNT_DISTINCT"],
                "supports_grouping": True,
                "supports_unique_by": True
            },
            "filter_options": {
                "supports_complex_logic": True
            },
            "comparison_options": {
                "types": ["previous_extract"],
                "default": "previous_extract"
            },
            "display_options": {
                "formats": ["number"],
                "decimal_places": [0],
                "show_trend": True
            }
        },
        "is_active": True
    },
    {
        "code": "screen_failures",
        "name": "Screen Failures",
        "description": "Shows number of subjects who failed screening",
        "category": WidgetCategory.METRICS,
        "config_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "default": "Screen Failures"},
                "showPercentage": {"type": "boolean", "default": True}
            }
        },
        "size_constraints": {
            "minWidth": 2, "minHeight": 2,
            "maxWidth": 4, "maxHeight": 3,
            "defaultWidth": 3, "defaultHeight": 2
        },
        "data_requirements": {
            "dataType": "metric",
            "supportsFiltering": True,
            "supportsComparison": True
        },
        "data_contract": {
            "aggregation_options": {
                "methods": ["COUNT", "COUNT_DISTINCT"],
                "supports_grouping": True,
                "supports_unique_by": True
            },
            "filter_options": {
                "supports_complex_logic": True
            },
            "comparison_options": {
                "types": ["previous_extract"],
                "default": "previous_extract"
            },
            "display_options": {
                "formats": ["number", "percentage"],
                "decimal_places": [0],
                "show_trend": True
            }
        },
        "is_active": True
    },
    {
        "code": "total_aes",
        "name": "Total AEs",
        "description": "Shows total number of adverse events",
        "category": WidgetCategory.METRICS,
        "config_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "default": "Total AEs"},
                "showComparison": {"type": "boolean", "default": True}
            }
        },
        "size_constraints": {
            "minWidth": 2, "minHeight": 2,
            "maxWidth": 4, "maxHeight": 3,
            "defaultWidth": 3, "defaultHeight": 2
        },
        "data_requirements": {
            "dataType": "metric",
            "supportsFiltering": True,
            "supportsComparison": True
        },
        "data_contract": {
            "aggregation_options": {
                "methods": ["COUNT", "COUNT_DISTINCT"],
                "supports_grouping": True,
                "supports_unique_by": True
            },
            "filter_options": {
                "supports_complex_logic": True
            },
            "comparison_options": {
                "types": ["previous_extract"],
                "default": "previous_extract"
            },
            "display_options": {
                "formats": ["number"],
                "decimal_places": [0],
                "show_trend": True
            }
        },
        "is_active": True
    },
    {
        "code": "saes",
        "name": "SAEs",
        "description": "Shows number of serious adverse events",
        "category": WidgetCategory.METRICS,
        "config_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "default": "SAEs"},
                "showComparison": {"type": "boolean", "default": True}
            }
        },
        "size_constraints": {
            "minWidth": 2, "minHeight": 2,
            "maxWidth": 4, "maxHeight": 3,
            "defaultWidth": 3, "defaultHeight": 2
        },
        "data_requirements": {
            "dataType": "metric",
            "supportsFiltering": True,
            "supportsComparison": True
        },
        "data_contract": {
            "aggregation_options": {
                "methods": ["COUNT", "COUNT_DISTINCT"],
                "supports_grouping": True,
                "supports_unique_by": True
            },
            "filter_options": {
                "supports_complex_logic": True
            },
            "comparison_options": {
                "types": ["previous_extract"],
                "default": "previous_extract"
            },
            "display_options": {
                "formats": ["number"],
                "decimal_places": [0],
                "show_trend": True
            }
        },
        "is_active": True
    },
    
    # Additional example metric widgets
    {
        "code": "total_subjects_with_aes",
        "name": "Total Subjects with AEs",
        "description": "Shows number of unique subjects who experienced adverse events",
        "category": WidgetCategory.METRICS,
        "config_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "default": "Total Subjects with AEs"},
                "showComparison": {"type": "boolean", "default": True}
            }
        },
        "size_constraints": {
            "minWidth": 2, "minHeight": 2,
            "maxWidth": 4, "maxHeight": 3,
            "defaultWidth": 3, "defaultHeight": 2
        },
        "data_requirements": {
            "dataType": "metric",
            "supportsFiltering": True,
            "supportsComparison": True
        },
        "data_contract": {
            "aggregation_options": {
                "methods": ["COUNT_DISTINCT"],
                "supports_grouping": True,
                "supports_unique_by": True
            },
            "filter_options": {
                "supports_complex_logic": True
            },
            "comparison_options": {
                "types": ["previous_extract"],
                "default": "previous_extract"
            },
            "display_options": {
                "formats": ["number"],
                "decimal_places": [0],
                "show_trend": True
            }
        },
        "is_active": True
    },
    {
        "code": "average_age",
        "name": "Average Age",
        "description": "Shows average age of subjects in the study",
        "category": WidgetCategory.METRICS,
        "config_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "default": "Average Age"},
                "showComparison": {"type": "boolean", "default": False},
                "decimalPlaces": {"type": "number", "default": 1}
            }
        },
        "size_constraints": {
            "minWidth": 2, "minHeight": 2,
            "maxWidth": 4, "maxHeight": 3,
            "defaultWidth": 3, "defaultHeight": 2
        },
        "data_requirements": {
            "dataType": "metric",
            "supportsFiltering": True,
            "supportsComparison": True
        },
        "data_contract": {
            "aggregation_options": {
                "methods": ["AVG", "MIN", "MAX", "MEDIAN"],
                "supports_grouping": True
            },
            "filter_options": {
                "supports_complex_logic": True
            },
            "comparison_options": {
                "types": ["previous_extract", "target_value"],
                "default": "previous_extract"
            },
            "display_options": {
                "formats": ["number"],
                "decimal_places": [0, 1, 2],
                "show_trend": False
            }
        },
        "is_active": True
    },
    {
        "code": "total_sum",
        "name": "Total Sum",
        "description": "Shows sum of any numeric value",
        "category": WidgetCategory.METRICS,
        "config_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "default": "Total"},
                "showComparison": {"type": "boolean", "default": True},
                "format": {"type": "string", "enum": ["number", "currency"], "default": "number"}
            }
        },
        "size_constraints": {
            "minWidth": 2, "minHeight": 2,
            "maxWidth": 4, "maxHeight": 3,
            "defaultWidth": 3, "defaultHeight": 2
        },
        "data_requirements": {
            "dataType": "metric",
            "supportsFiltering": True,
            "supportsComparison": True
        },
        "data_contract": {
            "aggregation_options": {
                "methods": ["SUM"],
                "supports_grouping": True
            },
            "filter_options": {
                "supports_complex_logic": True
            },
            "comparison_options": {
                "types": ["previous_extract", "target_value"],
                "default": "previous_extract"
            },
            "display_options": {
                "formats": ["number", "currency"],
                "decimal_places": [0, 1, 2],
                "show_trend": True
            }
        },
        "is_active": True
    }
]


def seed_widgets(db: Session, user_id: uuid.UUID) -> None:
    """Seed the database with widget definitions"""
    try:
        created_count = 0
        updated_count = 0
        
        for widget_data in WIDGET_DEFINITIONS:
            # Check if widget exists
            existing_widget = db.query(WidgetDefinition).filter(
                WidgetDefinition.code == widget_data["code"]
            ).first()
            
            if existing_widget:
                # Update existing widget
                for key, value in widget_data.items():
                    setattr(existing_widget, key, value)
                updated_count += 1
                logger.info(f"Updated widget: {widget_data['name']}")
            else:
                # Create new widget
                widget = WidgetDefinition(
                    created_by=user_id,
                    **widget_data
                )
                db.add(widget)
                created_count += 1
                logger.info(f"Created widget: {widget_data['name']}")
        
        db.commit()
        logger.info(f"Widget seeding completed. Created: {created_count}, Updated: {updated_count}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding widgets: {str(e)}")
        raise


def main():
    """Run the widget seeding script"""
    from sqlmodel import Session
    from app.core.db import engine
    
    db = Session(engine)
    try:
        # Get or create a system user for seeding
        system_user = db.query(User).filter(User.email == "admin@sagarmatha.ai").first()
        if not system_user:
            logger.error("Admin user not found. Please create a user first.")
            return
        
        logger.info("Starting widget seeding...")
        seed_widgets(db, system_user.id)
        
        # Also run the new metrics card widget seeding
        from app.db.seed_metrics_card_widget import create_metrics_card_widget
        logger.info("Seeding flexible metrics card widget...")
        create_metrics_card_widget()
        
        logger.info("Widget seeding completed successfully")
    except Exception as e:
        logger.error(f"Widget seeding failed: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()