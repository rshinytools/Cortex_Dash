# ABOUTME: CRUD operations for dashboard configuration audit logging and permissions
# ABOUTME: Tracks all changes to widgets, dashboards, menus and manages org admin permissions

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy import and_, or_, desc
import uuid
import json

from app.models import (
    DashboardConfigAudit,
    OrgAdminPermission,
    OrgAdminPermissionBase,
    EntityType,
    AuditAction,
    User,
    Organization
)


def create_dashboard_audit_log(
    db: Session,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    action: AuditAction,
    changes: Optional[Dict[str, Any]],
    user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> DashboardConfigAudit:
    """Create an audit log entry for dashboard configuration changes"""
    audit_log = DashboardConfigAudit(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        changes=changes,
        performed_by=user.id,
        performed_at=datetime.utcnow(),
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def get_audit_logs(
    db: Session,
    entity_type: Optional[EntityType] = None,
    entity_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    action: Optional[AuditAction] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[DashboardConfigAudit]:
    """Get audit logs with optional filters"""
    query = select(DashboardConfigAudit)
    
    conditions = []
    if entity_type:
        conditions.append(DashboardConfigAudit.entity_type == entity_type)
    if entity_id:
        conditions.append(DashboardConfigAudit.entity_id == entity_id)
    if user_id:
        conditions.append(DashboardConfigAudit.performed_by == user_id)
    if action:
        conditions.append(DashboardConfigAudit.action == action)
    if start_date:
        conditions.append(DashboardConfigAudit.performed_at >= start_date)
    if end_date:
        conditions.append(DashboardConfigAudit.performed_at <= end_date)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(desc(DashboardConfigAudit.performed_at))
    query = query.offset(skip).limit(limit)
    
    return list(db.exec(query).all())


def get_entity_history(
    db: Session,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    limit: int = 50
) -> List[DashboardConfigAudit]:
    """Get the complete audit history for a specific entity"""
    return get_audit_logs(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit
    )


def create_audit_log_for_create(
    db: Session,
    entity_type: EntityType,
    entity: Any,
    user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> DashboardConfigAudit:
    """Create audit log for entity creation"""
    # Extract relevant fields for the audit log
    entity_dict = entity.model_dump() if hasattr(entity, 'model_dump') else entity.__dict__
    
    # Remove internal fields
    fields_to_remove = ['id', 'created_at', 'updated_at', 'created_by']
    changes = {k: v for k, v in entity_dict.items() if k not in fields_to_remove}
    
    return create_dashboard_audit_log(
        db=db,
        entity_type=entity_type,
        entity_id=entity.id,
        action=AuditAction.CREATE,
        changes={"created": changes},
        user=user,
        ip_address=ip_address,
        user_agent=user_agent
    )


def create_audit_log_for_update(
    db: Session,
    entity_type: EntityType,
    entity_id: uuid.UUID,
    before: Dict[str, Any],
    after: Dict[str, Any],
    user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> DashboardConfigAudit:
    """Create audit log for entity update with before/after comparison"""
    # Find what actually changed
    changed_fields = {}
    for key in after:
        if key in before and before[key] != after[key]:
            changed_fields[key] = {
                "before": before[key],
                "after": after[key]
            }
    
    if not changed_fields:
        return None  # No actual changes
    
    return create_dashboard_audit_log(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        action=AuditAction.UPDATE,
        changes=changed_fields,
        user=user,
        ip_address=ip_address,
        user_agent=user_agent
    )


# Organization Admin Permission CRUD

def grant_org_admin_permission(
    db: Session,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    permission_set: Dict[str, Any],
    granted_by: User,
    expires_at: Optional[datetime] = None
) -> OrgAdminPermission:
    """Grant organization admin permissions to a user"""
    # Check if permission already exists
    existing = db.exec(
        select(OrgAdminPermission).where(
            and_(
                OrgAdminPermission.org_id == org_id,
                OrgAdminPermission.user_id == user_id
            )
        )
    ).first()
    
    if existing:
        # Update existing permission
        existing.permission_set = permission_set
        existing.granted_by = granted_by.id
        existing.granted_at = datetime.utcnow()
        existing.expires_at = expires_at
        existing.is_active = True
        db.add(existing)
    else:
        # Create new permission
        permission = OrgAdminPermission(
            org_id=org_id,
            user_id=user_id,
            permission_set=permission_set,
            granted_by=granted_by.id,
            granted_at=datetime.utcnow(),
            expires_at=expires_at,
            is_active=True
        )
        db.add(permission)
        existing = permission
    
    db.commit()
    db.refresh(existing)
    
    # Create audit log
    create_dashboard_audit_log(
        db=db,
        entity_type=EntityType.PERMISSION,
        entity_id=existing.id,
        action=AuditAction.ASSIGN if existing else AuditAction.CREATE,
        changes={"permission_set": permission_set, "user_id": str(user_id)},
        user=granted_by
    )
    
    return existing


def revoke_org_admin_permission(
    db: Session,
    permission_id: uuid.UUID,
    revoked_by: User
) -> bool:
    """Revoke organization admin permissions"""
    permission = db.get(OrgAdminPermission, permission_id)
    if not permission:
        return False
    
    permission.is_active = False
    db.add(permission)
    db.commit()
    
    # Create audit log
    create_dashboard_audit_log(
        db=db,
        entity_type=EntityType.PERMISSION,
        entity_id=permission_id,
        action=AuditAction.DEACTIVATE,
        changes={"user_id": str(permission.user_id)},
        user=revoked_by
    )
    
    return True


def get_user_org_permissions(
    db: Session,
    user_id: uuid.UUID,
    org_id: Optional[uuid.UUID] = None,
    active_only: bool = True
) -> List[OrgAdminPermission]:
    """Get all organization permissions for a user"""
    query = select(OrgAdminPermission).where(
        OrgAdminPermission.user_id == user_id
    )
    
    conditions = [OrgAdminPermission.user_id == user_id]
    
    if org_id:
        conditions.append(OrgAdminPermission.org_id == org_id)
    
    if active_only:
        conditions.append(OrgAdminPermission.is_active == True)
        conditions.append(
            or_(
                OrgAdminPermission.expires_at == None,
                OrgAdminPermission.expires_at > datetime.utcnow()
            )
        )
    
    query = query.where(and_(*conditions))
    
    return list(db.exec(query).all())


def get_org_admin_permissions(
    db: Session,
    org_id: uuid.UUID,
    active_only: bool = True
) -> List[OrgAdminPermission]:
    """Get all admin permissions for an organization"""
    query = select(OrgAdminPermission).where(
        OrgAdminPermission.org_id == org_id
    )
    
    if active_only:
        query = query.where(
            and_(
                OrgAdminPermission.is_active == True,
                or_(
                    OrgAdminPermission.expires_at == None,
                    OrgAdminPermission.expires_at > datetime.utcnow()
                )
            )
        )
    
    return list(db.exec(query).all())


def check_user_permission(
    db: Session,
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    permission_path: str
) -> bool:
    """Check if user has a specific permission for an organization
    
    Args:
        user_id: User to check
        org_id: Organization context
        permission_path: Dot-notation path like 'dashboard_management.can_create_dashboards'
    """
    permissions = get_user_org_permissions(
        db=db,
        user_id=user_id,
        org_id=org_id,
        active_only=True
    )
    
    if not permissions:
        return False
    
    # Check the permission path in the permission set
    for perm in permissions:
        permission_set = perm.permission_set
        
        # Navigate the permission path
        parts = permission_path.split('.')
        current = permission_set
        
        try:
            for part in parts:
                current = current[part]
            return bool(current)
        except (KeyError, TypeError):
            continue
    
    return False


def get_audit_summary(
    db: Session,
    org_id: Optional[uuid.UUID] = None,
    days: int = 30
) -> Dict[str, Any]:
    """Get summary statistics of audit logs"""
    start_date = datetime.utcnow() - datetime.timedelta(days=days)
    
    query = select(DashboardConfigAudit).where(
        DashboardConfigAudit.performed_at >= start_date
    )
    
    # If org_id provided, filter by users in that org
    if org_id:
        # Get users in the organization
        user_query = select(User.id).where(User.org_id == org_id)
        user_ids = [uid for (uid,) in db.exec(user_query).all()]
        query = query.where(DashboardConfigAudit.performed_by.in_(user_ids))
    
    logs = list(db.exec(query).all())
    
    # Calculate summary statistics
    summary = {
        "total_actions": len(logs),
        "period_days": days,
        "actions_by_type": {},
        "actions_by_entity": {},
        "most_active_users": {},
        "recent_actions": []
    }
    
    # Count by action type
    for log in logs:
        action = str(log.action)
        summary["actions_by_type"][action] = summary["actions_by_type"].get(action, 0) + 1
        
        entity = str(log.entity_type)
        summary["actions_by_entity"][entity] = summary["actions_by_entity"].get(entity, 0) + 1
        
        user_id = str(log.performed_by)
        summary["most_active_users"][user_id] = summary["most_active_users"].get(user_id, 0) + 1
    
    # Get most recent actions
    recent_logs = sorted(logs, key=lambda x: x.performed_at, reverse=True)[:10]
    summary["recent_actions"] = [
        {
            "entity_type": str(log.entity_type),
            "action": str(log.action),
            "performed_by": str(log.performed_by),
            "performed_at": log.performed_at.isoformat()
        }
        for log in recent_logs
    ]
    
    # Sort most active users and limit to top 5
    summary["most_active_users"] = dict(
        sorted(
            summary["most_active_users"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
    )
    
    return summary