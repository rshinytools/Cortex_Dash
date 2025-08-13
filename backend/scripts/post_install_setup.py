#!/usr/bin/env python3
# ABOUTME: Post-installation setup script to ensure database is properly configured
# ABOUTME: Run this after fresh installation to set up organization and admin user

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.core.db import engine
from app.models import Organization, OrganizationCreate, User
from app.crud import organization as crud_org
from app.core.config import settings
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

def main():
    logger.info("Starting post-installation setup...")
    
    # Set up default organization
    org = setup_default_organization()
    logger.info(f"Default organization: {org.name} (ID: {org.id})")
    
    # Verify enum values
    verify_enum_values()
    
    logger.info("Post-installation setup completed successfully!")
    logger.info("\nIMPORTANT: If you see any enum value mismatches, run:")
    logger.info("  docker compose exec backend alembic upgrade head")

if __name__ == "__main__":
    main()