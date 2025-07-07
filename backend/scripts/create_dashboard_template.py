#!/usr/bin/env python3
# ABOUTME: Script to create a unified dashboard template using the new model structure
# ABOUTME: Demonstrates how to create templates with embedded menus, dashboards, and data mappings

"""
Create Dashboard Template Script

This script demonstrates how to create a unified dashboard template that includes:
- Complete menu structure
- Multiple dashboards with widgets
- Data mapping requirements
- Permission-based visibility

Usage:
    python scripts/create_dashboard_template.py
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, create_engine, select
from app.models import (
    DashboardTemplate, 
    DashboardTemplateCreate,
    User
)
from app.core.config import settings
from app.crud import dashboard as crud_dashboard


def load_template_from_file(file_path: str) -> dict:
    """Load dashboard template from JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)


def create_dashboard_template(db: Session, template_data: dict, user: User) -> DashboardTemplate:
    """Create a dashboard template in the database"""
    
    # Extract template creation data
    template_create = DashboardTemplateCreate(
        code=template_data["code"],
        name=template_data["name"],
        description=template_data["description"],
        category=template_data["category"],
        template_structure=template_data["template_structure"],
        version=template_data.get("version", 1),
        is_active=template_data.get("is_active", True)
    )
    
    # Check if template already exists
    existing = crud_dashboard.get_dashboard_by_code(db, template_create.code)
    if existing:
        print(f"Template with code '{template_create.code}' already exists")
        return existing
    
    # Create the template
    dashboard_template = crud_dashboard.create_dashboard(
        db=db,
        dashboard_create=template_create,
        current_user=user
    )
    
    print(f"Created dashboard template: {dashboard_template.name} (ID: {dashboard_template.id})")
    
    # Validate the template structure
    validation_errors = crud_dashboard.validate_template_structure(dashboard_template.template_structure)
    if validation_errors:
        print("Warning: Template has validation errors:")
        for error in validation_errors:
            print(f"  - {error}")
    else:
        print("✓ Template structure is valid")
    
    # Extract and display data requirements
    data_requirements = crud_dashboard.extract_data_requirements(dashboard_template)
    print("\nData Requirements:")
    print(f"  Required datasets: {', '.join(data_requirements.required_datasets)}")
    print("  Field mappings:")
    for dataset, fields in data_requirements.field_mappings.items():
        print(f"    {dataset}: {', '.join(fields)}")
    
    print(f"\nTotal widgets: {len(data_requirements.widget_requirements)}")
    
    return dashboard_template


def main():
    """Main function"""
    # Create database engine
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    
    with Session(engine) as db:
        # Get the system admin user
        admin_user = db.exec(
            select(User).where(User.email == settings.FIRST_SUPERUSER)
        ).first()
        
        if not admin_user:
            print("Error: Admin user not found")
            return
        
        # Load template from file
        template_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "app",
            "sample_dashboard_template.json"
        )
        
        if not os.path.exists(template_file):
            print(f"Error: Template file not found: {template_file}")
            return
        
        template_data = load_template_from_file(template_file)
        
        # Create the dashboard template
        dashboard_template = create_dashboard_template(db, template_data, admin_user)
        
        # Display menu structure
        print("\nMenu Structure:")
        menu_items = dashboard_template.template_structure["menu"]["items"]
        
        def print_menu_items(items, indent=0):
            for item in items:
                prefix = "  " * indent + "- "
                item_type = item["type"]
                label = item["label"]
                
                if item_type == "dashboard":
                    dashboard_info = item.get("dashboard", {})
                    widget_count = len(dashboard_info.get("widgets", []))
                    print(f"{prefix}{label} (Dashboard with {widget_count} widgets)")
                elif item_type == "group":
                    print(f"{prefix}{label} (Group)")
                    if "children" in item:
                        print_menu_items(item["children"], indent + 1)
                elif item_type == "divider":
                    print(f"{prefix}---")
                else:
                    print(f"{prefix}{label} ({item_type})")
        
        print_menu_items(menu_items)
        
        print("\n✓ Dashboard template created successfully!")


if __name__ == "__main__":
    main()