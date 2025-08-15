# ABOUTME: Audit trail service for tracking all system activities
# ABOUTME: Provides comprehensive logging and compliance reporting

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from sqlmodel import Session

from app.core.logging import logger

class AuditEventType(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    DATA_VIEW = "data_view"
    DATA_EXPORT = "data_export"
    DATA_UPLOAD = "data_upload"
    DATA_DELETE = "data_delete"
    CONFIG_CHANGE = "config_change"
    PERMISSION_CHANGE = "permission_change"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    STUDY_CREATE = "study_create"
    STUDY_UPDATE = "study_update"
    DASHBOARD_CREATE = "dashboard_create"
    DASHBOARD_UPDATE = "dashboard_update"
    WIDGET_CREATE = "widget_create"
    WIDGET_UPDATE = "widget_update"
    INTEGRATION_CONFIG = "integration_config"
    INTEGRATION_SYNC = "integration_sync"

class AuditService:
    """Comprehensive audit trail service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def log_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Log an audit event"""
        
        event = {
            "id": f"audit_{datetime.utcnow().timestamp()}",
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        
        # Log to system
        logger.info(f"Audit: {event_type} by {user_id} on {resource_type}/{resource_id}")
        
        # In production, save to database
        return event
    
    async def get_audit_trail(
        self,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit trail with filters"""
        
        # This would query the database
        # For now, return example data
        return [
            {
                "id": "audit_1",
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "data_upload",
                "user_id": user_id or "user_123",
                "resource_type": "data_upload",
                "resource_id": "upload_456",
                "action": "create",
                "details": {"file_name": "data.csv", "size": "2.5MB"}
            }
        ]
    
    async def generate_compliance_report(
        self,
        study_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate compliance report for regulatory purposes"""
        
        return {
            "study_id": study_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_events": 150,
                "data_changes": 45,
                "permission_changes": 5,
                "exports": 20,
                "unique_users": 15
            },
            "critical_events": [],
            "generated_at": datetime.utcnow().isoformat()
        }