#!/usr/bin/env python3
# ABOUTME: Initialize database with all required tables
# ABOUTME: Creates tables and runs post-installation setup

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import SQLModel
from app.core.db import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database with all tables"""
    try:
        logger.info("Creating all database tables...")
        
        # Import all models to ensure they're registered
        from app.models import (
            User, Organization, Study, 
            DashboardTemplate, WidgetDefinition,
            DataSource, PipelineConfig,
            ActivityLog, StudyDashboard
        )
        # Import RBAC models if they exist
        try:
            from app.models.rbac import (
                Permission, Role, RolePermission, UserRole,
                PermissionPreset, PermissionAuditLog
            )
        except ImportError:
            logger.warning("RBAC models not found, skipping...")
        
        # Import additional models if they exist
        try:
            from app.models.data_mapping import WidgetDataMapping, StudyDataConfiguration
        except ImportError:
            logger.warning("Data mapping models not found, skipping...")
            
        try:
            from app.models.dashboard_audit import DashboardConfigAudit
        except ImportError:
            logger.warning("Dashboard audit models not found, skipping...")
        
        # Create all tables
        SQLModel.metadata.create_all(engine)
        logger.info("All tables created successfully!")
        
        # Now run migrations to update/populate
        import subprocess
        logger.info("Running Alembic migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.warning(f"Migration warning: {result.stderr}")
            # Try to stamp head if tables exist
            subprocess.run(["alembic", "stamp", "head"])
        
        logger.info("Database initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)