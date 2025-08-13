#!/usr/bin/env python3
# ABOUTME: Script to fix the admin user's role
# ABOUTME: Updates admin@sagarmatha.ai to have system_admin role

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.core.db import engine
from app.models import User
from app.core.config import settings

def fix_admin_role():
    """Fix the admin user's role to system_admin"""
    with Session(engine) as session:
        # Find the admin user
        admin_user = session.exec(
            select(User).where(User.email == settings.FIRST_SUPERUSER)
        ).first()
        
        if not admin_user:
            print(f"Admin user {settings.FIRST_SUPERUSER} not found!")
            return
        
        print(f"Current role for {admin_user.email}: {admin_user.role}")
        print(f"Is superuser: {admin_user.is_superuser}")
        
        # Update the role
        if admin_user.role != "system_admin":
            admin_user.role = "system_admin"
            session.add(admin_user)
            session.commit()
            print(f"✓ Updated role to: system_admin")
        else:
            print("Role is already system_admin")
        
        # Also remove org_id for system_admin (optional - system admins don't need to belong to an org)
        if admin_user.org_id:
            print(f"Current org_id: {admin_user.org_id}")
            print("System admins typically don't belong to a specific organization.")
            # Uncomment the next lines if you want to remove org_id
            # admin_user.org_id = None
            # session.add(admin_user)
            # session.commit()
            # print("✓ Removed org_id")

if __name__ == "__main__":
    fix_admin_role()