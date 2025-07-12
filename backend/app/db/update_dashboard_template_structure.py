# ABOUTME: Script to update dashboard template structure to single dashboard architecture
# ABOUTME: Converts menu items of type 'dashboard' to 'dashboard_page' and restructures template

from sqlmodel import Session, select
from app.core.db import engine
from app.models import DashboardTemplate
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_template_structure(template_structure: dict) -> dict:
    """Update template structure to single dashboard architecture"""
    updated_structure = template_structure.copy()
    
    # Update menu items
    if "menu" in updated_structure and "items" in updated_structure["menu"]:
        for item in updated_structure["menu"]["items"]:
            update_menu_item(item)
    
    return updated_structure


def update_menu_item(item: dict) -> None:
    """Recursively update menu items to use new types"""
    # Convert type mappings
    type_mappings = {
        "dashboard": "dashboard_page",
        "link": "external",
        "dropdown": "group",
        "header": "divider"
    }
    
    if "type" in item:
        item["type"] = type_mappings.get(item["type"], item["type"])
    
    # Add dashboardConfig for dashboard_page items
    if item.get("type") == "dashboard_page":
        if "dashboard" not in item:
            item["dashboard"] = {
                "layout": {"type": "grid", "columns": 12, "rows": 10},
                "widgets": []
            }
        
        # Create dashboardConfig from dashboard data
        item["dashboardConfig"] = {
            "viewId": item.get("id", "view"),
            "layout": item["dashboard"].get("layout", {
                "type": "grid",
                "columns": 12,
                "rows": 10
            })
        }
    
    # Process children recursively
    if "children" in item and item["children"]:
        for child in item["children"]:
            update_menu_item(child)


def main():
    """Update all dashboard templates to single dashboard architecture"""
    db = Session(engine)
    
    try:
        # Get all dashboard templates
        templates = db.exec(select(DashboardTemplate)).all()
        
        logger.info(f"Found {len(templates)} dashboard templates to update")
        
        for template in templates:
            logger.info(f"Updating template: {template.name} ({template.code})")
            
            # Update template structure
            updated_structure = update_template_structure(template.template_structure)
            template.template_structure = updated_structure
            
            # Update version
            template.patch_version += 1
            
            logger.info(f"Updated template {template.code} to version {template.version_string}")
        
        # Commit changes
        db.commit()
        logger.info("Successfully updated all dashboard templates")
        
    except Exception as e:
        logger.error(f"Error updating templates: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()