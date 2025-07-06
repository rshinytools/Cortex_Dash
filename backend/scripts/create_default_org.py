#!/usr/bin/env python3
# ABOUTME: Script to create a default organization for testing
# ABOUTME: Run this to create an initial organization for the system admin

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.core.db import engine
from app.models import Organization, OrganizationCreate, User
from app.crud import organization as crud_org
from app.core.config import settings

def create_default_organization():
    """Create a default organization and assign the superuser to it"""
    with Session(engine) as session:
        # Check if any organization exists
        existing_org = session.exec(select(Organization).limit(1)).first()
        if existing_org:
            print(f"Organization already exists: {existing_org.name}")
            return existing_org
        
        # Create default organization
        org_in = OrganizationCreate(
            name="Sagarmatha AI",
            slug="sagarmatha-ai",
            features={}
        )
        
        org = crud_org.create_organization(session, org_create=org_in)
        print(f"Created organization: {org.name}")
        
        # Update superuser to belong to this organization
        superuser = session.exec(
            select(User).where(User.email == settings.FIRST_SUPERUSER)
        ).first()
        
        if superuser and not superuser.org_id:
            superuser.org_id = org.id
            session.add(superuser)
            session.commit()
            print(f"Assigned superuser to organization: {org.name}")
        
        return org

if __name__ == "__main__":
    create_default_organization()