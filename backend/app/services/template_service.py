# ABOUTME: Template service for managing dashboard templates
# ABOUTME: Handles template operations and application to studies

import uuid
from typing import Optional, List, Dict, Any
from sqlmodel import Session, select

from app.models import DashboardTemplate as UnifiedDashboardTemplate


class TemplateService:
    """Service for managing dashboard templates"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_template(self, template_id: uuid.UUID) -> Optional[UnifiedDashboardTemplate]:
        """Get a template by ID"""
        return self.db.get(UnifiedDashboardTemplate, template_id)
    
    def list_templates(self, org_id: Optional[uuid.UUID] = None) -> List[UnifiedDashboardTemplate]:
        """List templates, optionally filtered by organization"""
        query = select(UnifiedDashboardTemplate)
        if org_id:
            query = query.where(UnifiedDashboardTemplate.org_id == org_id)
        
        return self.db.exec(query).all()
    
    def validate_template_structure(self, template_structure: Dict[str, Any]) -> bool:
        """Validate template structure"""
        # Basic validation
        if not isinstance(template_structure, dict):
            return False
        
        # Check required fields
        if "dashboardTemplates" not in template_structure:
            return False
        
        if "menu_structure" not in template_structure:
            return False
        
        return True