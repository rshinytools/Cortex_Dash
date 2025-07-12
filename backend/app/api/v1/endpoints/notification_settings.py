# ABOUTME: API endpoints for notification settings and preferences management
# ABOUTME: Handles email templates, notification rules, and user preferences

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlmodel import Session, select
from datetime import datetime
import uuid

from app.api.deps import get_db, get_current_user
from app.models import User, Organization
from app.core.permissions import Permission, require_permission

router = APIRouter()


@router.get("/templates", response_model=List[Dict[str, Any]])
async def get_notification_templates(
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get notification templates for the organization.
    """
    # TODO: Implement actual template retrieval
    templates = [
        {
            "id": "tpl_001",
            "name": "Study Enrollment Update",
            "type": "enrollment",
            "subject": "{{study_name}} - Enrollment Update",
            "body": """
                <h2>Enrollment Update for {{study_name}}</h2>
                <p>Current enrollment: {{current_enrolled}} / {{target_enrollment}}</p>
                <p>Percentage complete: {{enrollment_percentage}}%</p>
                <p>Top performing sites:</p>
                <ul>
                {{#each top_sites}}
                    <li>{{this.name}} - {{this.enrolled}} subjects</li>
                {{/each}}
                </ul>
            """,
            "variables": ["study_name", "current_enrolled", "target_enrollment", "enrollment_percentage", "top_sites"],
            "active": True,
            "created_at": "2024-12-01T00:00:00",
            "updated_at": "2025-01-15T00:00:00"
        },
        {
            "id": "tpl_002",
            "name": "Data Quality Alert",
            "type": "quality",
            "subject": "Data Quality Issue - {{study_name}}",
            "body": """
                <h2>Data Quality Alert</h2>
                <p>Study: {{study_name}}</p>
                <p>Issue Type: {{issue_type}}</p>
                <p>Severity: {{severity}}</p>
                <p>Description: {{description}}</p>
                <p>Affected Records: {{affected_count}}</p>
                <p>Action Required: {{action_required}}</p>
            """,
            "variables": ["study_name", "issue_type", "severity", "description", "affected_count", "action_required"],
            "active": True,
            "created_at": "2024-12-15T00:00:00",
            "updated_at": "2025-01-10T00:00:00"
        },
        {
            "id": "tpl_003",
            "name": "Report Generated",
            "type": "report",
            "subject": "Report Ready - {{report_name}}",
            "body": """
                <h2>Your report is ready</h2>
                <p>Report: {{report_name}}</p>
                <p>Study: {{study_name}}</p>
                <p>Generated at: {{generated_at}}</p>
                <p>Download link: <a href="{{download_url}}">Download Report</a></p>
                <p>This link will expire in 48 hours.</p>
            """,
            "variables": ["report_name", "study_name", "generated_at", "download_url"],
            "active": True,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00"
        },
        {
            "id": "tpl_004",
            "name": "Safety Alert",
            "type": "safety",
            "subject": "URGENT: Safety Alert - {{study_name}}",
            "body": """
                <h2 style="color: red;">Safety Alert</h2>
                <p><strong>Study:</strong> {{study_name}}</p>
                <p><strong>Alert Type:</strong> {{alert_type}}</p>
                <p><strong>Description:</strong> {{description}}</p>
                <p><strong>Sites Affected:</strong> {{affected_sites}}</p>
                <p><strong>Immediate Action Required:</strong> {{action_required}}</p>
                <hr>
                <p>Please log in to the dashboard for more details.</p>
            """,
            "variables": ["study_name", "alert_type", "description", "affected_sites", "action_required"],
            "active": True,
            "created_at": "2024-11-01T00:00:00",
            "updated_at": "2025-01-20T00:00:00"
        }
    ]
    
    if template_type:
        templates = [t for t in templates if t["type"] == template_type]
    
    return templates


@router.post("/templates", response_model=Dict[str, Any])
async def create_notification_template(
    template: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new notification template.
    """
    # Extract template data
    name = template.get("name")
    template_type = template.get("type")
    subject = template.get("subject")
    body = template.get("body")
    variables = template.get("variables", [])
    
    if not all([name, template_type, subject, body]):
        raise HTTPException(
            status_code=400,
            detail="Name, type, subject, and body are required"
        )
    
    # TODO: Implement actual template creation
    
    new_template = {
        "id": f"tpl_{uuid.uuid4().hex[:8]}",
        "name": name,
        "type": template_type,
        "subject": subject,
        "body": body,
        "variables": variables,
        "active": True,
        "org_id": str(current_user.org_id),
        "created_by": current_user.email,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    return new_template


@router.put("/templates/{template_id}", response_model=Dict[str, Any])
async def update_notification_template(
    template_id: str,
    template: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a notification template.
    """
    # TODO: Implement actual template update
    
    updated_template = {
        "id": template_id,
        **template,
        "updated_by": current_user.email,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    return updated_template


@router.get("/rules", response_model=List[Dict[str, Any]])
async def get_notification_rules(
    rule_type: Optional[str] = Query(None, description="Filter by rule type"),
    active_only: bool = Query(True, description="Show only active rules"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get notification rules for the organization.
    """
    # TODO: Implement actual rule retrieval
    rules = [
        {
            "id": "rule_001",
            "name": "Low Enrollment Alert",
            "type": "enrollment",
            "description": "Alert when enrollment falls below target",
            "condition": {
                "type": "threshold",
                "metric": "enrollment_percentage",
                "operator": "less_than",
                "value": 80,
                "check_frequency": "daily"
            },
            "template_id": "tpl_001",
            "recipients": {
                "roles": ["study_manager", "clinical_lead"],
                "users": [],
                "emails": ["alerts@example.com"]
            },
            "active": True,
            "last_triggered": "2025-01-20T10:00:00",
            "created_at": "2024-12-01T00:00:00"
        },
        {
            "id": "rule_002",
            "name": "Critical Data Quality Issue",
            "type": "quality",
            "description": "Alert on critical data quality issues",
            "condition": {
                "type": "event",
                "event_type": "data_quality_issue",
                "severity": ["critical", "high"]
            },
            "template_id": "tpl_002",
            "recipients": {
                "roles": ["data_manager", "study_manager"],
                "users": ["user_123", "user_456"],
                "emails": []
            },
            "active": True,
            "last_triggered": "2025-01-18T14:30:00",
            "created_at": "2024-12-15T00:00:00"
        },
        {
            "id": "rule_003",
            "name": "Weekly Report Generation",
            "type": "report",
            "description": "Notify when weekly reports are generated",
            "condition": {
                "type": "schedule",
                "schedule": "every Monday at 08:00 UTC"
            },
            "template_id": "tpl_003",
            "recipients": {
                "roles": ["study_manager"],
                "users": [],
                "emails": []
            },
            "active": True,
            "last_triggered": "2025-01-21T08:00:00",
            "created_at": "2025-01-01T00:00:00"
        },
        {
            "id": "rule_004",
            "name": "Serious Adverse Event",
            "type": "safety",
            "description": "Immediate notification for SAEs",
            "condition": {
                "type": "event",
                "event_type": "serious_adverse_event",
                "immediate": True
            },
            "template_id": "tpl_004",
            "recipients": {
                "roles": ["safety_officer", "medical_monitor", "study_manager"],
                "users": [],
                "emails": ["safety@example.com", "medical@example.com"],
                "escalation": {
                    "delay_minutes": 30,
                    "recipients": {
                        "roles": ["clinical_director"],
                        "emails": ["director@example.com"]
                    }
                }
            },
            "active": True,
            "last_triggered": "2025-01-15T16:45:00",
            "created_at": "2024-11-01T00:00:00"
        }
    ]
    
    if rule_type:
        rules = [r for r in rules if r["type"] == rule_type]
    
    if active_only:
        rules = [r for r in rules if r["active"]]
    
    return rules


@router.post("/rules", response_model=Dict[str, Any])
async def create_notification_rule(
    rule: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new notification rule.
    """
    # Extract rule data
    name = rule.get("name")
    rule_type = rule.get("type")
    condition = rule.get("condition")
    template_id = rule.get("template_id")
    recipients = rule.get("recipients")
    
    if not all([name, rule_type, condition, template_id, recipients]):
        raise HTTPException(
            status_code=400,
            detail="All fields are required"
        )
    
    # TODO: Implement actual rule creation
    
    new_rule = {
        "id": f"rule_{uuid.uuid4().hex[:8]}",
        "name": name,
        "type": rule_type,
        "description": rule.get("description", ""),
        "condition": condition,
        "template_id": template_id,
        "recipients": recipients,
        "active": True,
        "org_id": str(current_user.org_id),
        "created_by": current_user.email,
        "created_at": datetime.utcnow().isoformat()
    }
    
    return new_rule


@router.get("/preferences", response_model=Dict[str, Any])
async def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get notification preferences for the current user.
    """
    # TODO: Implement actual preference retrieval
    
    preferences = {
        "user_id": str(current_user.id),
        "email_notifications": {
            "enabled": True,
            "frequency": "immediate",  # immediate, hourly, daily, weekly
            "categories": {
                "enrollment": True,
                "safety": True,
                "quality": True,
                "reports": True,
                "system": False
            }
        },
        "in_app_notifications": {
            "enabled": True,
            "categories": {
                "enrollment": True,
                "safety": True,
                "quality": True,
                "reports": True,
                "system": True
            }
        },
        "sms_notifications": {
            "enabled": False,
            "phone_number": None,
            "categories": {
                "safety": True,
                "critical_alerts": True
            }
        },
        "digest_preferences": {
            "enabled": True,
            "schedule": "daily",
            "time": "08:00",
            "timezone": "UTC"
        },
        "quiet_hours": {
            "enabled": True,
            "start_time": "22:00",
            "end_time": "07:00",
            "timezone": "UTC",
            "override_for_critical": True
        },
        "updated_at": datetime.utcnow().isoformat()
    }
    
    return preferences


@router.put("/preferences", response_model=Dict[str, Any])
async def update_notification_preferences(
    preferences: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update notification preferences for the current user.
    """
    # TODO: Implement actual preference update
    
    updated_preferences = {
        "user_id": str(current_user.id),
        **preferences,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    return updated_preferences


@router.post("/test", response_model=Dict[str, Any])
async def test_notification(
    test_config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Test a notification template or rule.
    """
    template_id = test_config.get("template_id")
    rule_id = test_config.get("rule_id")
    test_data = test_config.get("test_data", {})
    recipient_email = test_config.get("recipient_email", current_user.email)
    
    if not template_id and not rule_id:
        raise HTTPException(
            status_code=400,
            detail="Either template_id or rule_id must be provided"
        )
    
    # TODO: Implement actual notification testing
    
    return {
        "status": "sent",
        "template_id": template_id,
        "rule_id": rule_id,
        "recipient": recipient_email,
        "test_data": test_data,
        "sent_at": datetime.utcnow().isoformat(),
        "message": "Test notification sent successfully"
    }