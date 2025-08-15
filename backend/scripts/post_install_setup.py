#!/usr/bin/env python3
# ABOUTME: Post-installation setup script to ensure database is properly configured
# ABOUTME: Sets up organization, admin user, RBAC system, and widget definitions

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.core.db import engine
from app.models import Organization, OrganizationCreate, User
from app.crud import organization as crud_org
from app.core.config import settings
from app.services.rbac.permission_service import PermissionService
from app.models.widget import WidgetDefinition
from app.models.rbac import Permission, Role
from uuid import uuid4
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_default_organization():
    """Create default organization and assign admin user"""
    with Session(engine) as session:
        # Check if any organization exists
        existing_org = session.exec(select(Organization).limit(1)).first()
        
        if existing_org:
            logger.info(f"Organization already exists: {existing_org.name}")
            # Ensure JSON fields are not NULL
            if existing_org.features is None:
                existing_org.features = {}
            if hasattr(existing_org, 'compliance_settings') and existing_org.compliance_settings is None:
                existing_org.compliance_settings = {}
            session.add(existing_org)
            session.commit()
        else:
            # Create default organization
            org_in = OrganizationCreate(
                name="Sagarmatha AI",
                slug="sagarmatha-ai",
                type="pharmaceutical" if hasattr(OrganizationCreate, 'type') else None,
                features={}
            )
            
            org = crud_org.create_organization(session, org_create=org_in)
            logger.info(f"Created organization: {org.name}")
            existing_org = org
        
        # Check and update admin user
        admin_email = settings.FIRST_SUPERUSER
        admin_user = session.exec(
            select(User).where(User.email == admin_email)
        ).first()
        
        if admin_user:
            if not admin_user.org_id:
                admin_user.org_id = existing_org.id
                session.add(admin_user)
            # Ensure admin has correct role
            if admin_user.role != 'system_admin':
                admin_user.role = 'system_admin'
                session.add(admin_user)
                logger.info(f"Updated {admin_email} role to system_admin")
            session.commit()
            logger.info(f"Admin user {admin_email} configured correctly")
        else:
            # Create admin user if not exists
            from app.core.security import get_password_hash
            admin_user = User(
                email=admin_email,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                full_name="System Administrator",
                is_active=True,
                is_superuser=True,
                org_id=existing_org.id,
                role='system_admin'
            )
            session.add(admin_user)
            session.commit()
            logger.info(f"Created admin user {admin_email}")
        
        # Check all superusers
        superusers = session.exec(
            select(User).where(User.is_superuser == True)
        ).all()
        
        for user in superusers:
            if not user.org_id:
                user.org_id = existing_org.id
                session.add(user)
                logger.info(f"Assigned superuser {user.email} to organization")
        
        session.commit()
        
        return existing_org

def verify_enum_values():
    """Verify that enum values in database match Python models"""
    with Session(engine) as session:
        # Check StudyStatus enum
        result = session.execute(
            "SELECT enum_range(NULL::studystatus)"
        ).scalar()
        logger.info(f"StudyStatus enum values in database: {result}")
        
        # Check TemplateStatus enum
        try:
            result = session.execute(
                "SELECT enum_range(NULL::templatestatus)"
            ).scalar()
            logger.info(f"TemplateStatus enum values in database: {result}")
        except Exception as e:
            logger.info("TemplateStatus enum not found (might not be created yet)")
        
        # Verify templates are published
        from app.models import DashboardTemplate
        templates = session.exec(select(DashboardTemplate)).all()
        for template in templates:
            if template.status != 'PUBLISHED':
                logger.info(f"Updating template {template.name} from {template.status} to PUBLISHED")
                template.status = 'PUBLISHED'
                session.add(template)
        
        session.commit()

def setup_rbac():
    """Initialize RBAC system with default roles and permissions"""
    try:
        with Session(engine) as db:
            service = PermissionService(db)
            
            # Initialize default permissions
            logger.info("Initializing RBAC system...")
            service.initialize_default_permissions()
            
            # Count results
            permissions = db.exec(select(Permission)).all()
            roles = db.exec(select(Role)).all()
            
            logger.info(f"RBAC initialized with {len(permissions)} permissions and {len(roles)} roles")
    except Exception as e:
        logger.warning(f"RBAC initialization warning: {e}")
        logger.info("RBAC may already be initialized or will be initialized by migrations")

def setup_widgets():
    """Initialize widget definitions"""
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
    
    try:
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
                        is_active=widget_data["is_active"]
                    )
                    db.add(widget)
                    created_count += 1
            
            db.commit()
            logger.info(f"Created {created_count} widget definitions")
    except Exception as e:
        logger.warning(f"Widget initialization warning: {e}")
        logger.info("Widgets may already be initialized or will be initialized by migrations")

def main():
    logger.info("Starting post-installation setup...")
    
    # Set up default organization
    org = setup_default_organization()
    # Store org data before session closes
    org_name = org.name if org else "Unknown"
    org_id = str(org.id) if org else "Unknown"
    logger.info(f"Default organization: {org_name} (ID: {org_id})")
    
    # Verify enum values
    verify_enum_values()
    
    # Setup RBAC system
    logger.info("Setting up RBAC system...")
    setup_rbac()
    
    # Setup widget definitions
    logger.info("Setting up widget definitions...")
    setup_widgets()
    
    logger.info("Post-installation setup completed successfully!")
    logger.info("\n=" * 60)
    logger.info("System initialized with:")
    logger.info("- Organization: Sagarmatha AI")
    logger.info("- Admin: admin@sagarmatha.ai")
    logger.info("- RBAC: Default roles and permissions")
    logger.info("- Widgets: 5 core widget types")
    logger.info("=" * 60)
    logger.info("\nIMPORTANT: If you see any enum value mismatches, run:")
    logger.info("  docker compose exec backend alembic upgrade head")

if __name__ == "__main__":
    main()