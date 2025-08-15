# ABOUTME: RBAC permission service for managing permissions and role assignments
# ABOUTME: Handles permission checking, granting, revoking, and audit logging

from typing import List, Optional, Dict, Any, Set
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select, and_, or_
from fastapi import HTTPException, status
import logging

from app.models.rbac import (
    Permission, Role, RolePermission, UserRole,
    PermissionPreset, PermissionAuditLog,
    DEFAULT_PERMISSIONS, DEFAULT_ROLE_PERMISSIONS
)
from app.models.user import User

logger = logging.getLogger(__name__)


class PermissionService:
    """Service for managing RBAC permissions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def initialize_default_permissions(self):
        """Initialize default permissions and roles"""
        # Create default permissions
        for perm_data in DEFAULT_PERMISSIONS:
            existing = self.db.exec(
                select(Permission).where(Permission.name == perm_data["name"])
            ).first()
            
            if not existing:
                permission = Permission(
                    **perm_data,
                    is_system=True
                )
                self.db.add(permission)
        
        # Create default roles
        default_roles = [
            {"name": "system_admin", "display_name": "System Administrator", 
             "description": "Full system access and control"},
            {"name": "org_admin", "display_name": "Organization Administrator",
             "description": "Manage organization users and settings"},
            {"name": "study_manager", "display_name": "Study Manager",
             "description": "Manage study teams and monitor progress"},
            {"name": "data_analyst", "display_name": "Data Analyst",
             "description": "Analyze data and create reports"},
            {"name": "viewer", "display_name": "Viewer",
             "description": "Read-only access to dashboards"}
        ]
        
        for role_data in default_roles:
            existing = self.db.exec(
                select(Role).where(Role.name == role_data["name"])
            ).first()
            
            if not existing:
                role = Role(
                    **role_data,
                    is_system=True
                )
                self.db.add(role)
        
        self.db.commit()
        
        # Assign default permissions to roles
        self._assign_default_role_permissions()
    
    def _assign_default_role_permissions(self):
        """Assign default permissions to roles"""
        for role_name, permission_names in DEFAULT_ROLE_PERMISSIONS.items():
            role = self.db.exec(
                select(Role).where(Role.name == role_name)
            ).first()
            
            if not role:
                continue
            
            if permission_names == ["*"]:
                # Grant all permissions to system_admin
                permissions = self.db.exec(select(Permission)).all()
            else:
                # Grant specific permissions
                permissions = self.db.exec(
                    select(Permission).where(Permission.name.in_(permission_names))
                ).all()
            
            for permission in permissions:
                # Check if already assigned
                existing = self.db.exec(
                    select(RolePermission).where(
                        and_(
                            RolePermission.role_id == role.id,
                            RolePermission.permission_id == permission.id
                        )
                    )
                ).first()
                
                if not existing:
                    role_permission = RolePermission(
                        role_id=role.id,
                        permission_id=permission.id,
                        granted_by=UUID("00000000-0000-0000-0000-000000000000"),  # System
                        is_active=True
                    )
                    self.db.add(role_permission)
            
        self.db.commit()
    
    def check_permission(
        self,
        user: User,
        permission_name: str,
        organization_id: Optional[UUID] = None,
        study_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user: User object
            permission_name: Permission name (e.g., "study.create")
            organization_id: Optional organization scope
            study_id: Optional study scope
            
        Returns:
            True if user has permission, False otherwise
        """
        # System admins have all permissions
        if self.is_system_admin(user):
            return True
        
        # Get user's roles
        user_roles = self.get_user_roles(user.id, organization_id, study_id)
        
        # Check each role for the permission
        for user_role in user_roles:
            if self.role_has_permission(user_role.role_id, permission_name):
                return True
        
        return False
    
    def is_system_admin(self, user: User) -> bool:
        """Check if user is a system admin"""
        user_role = self.db.exec(
            select(UserRole).join(Role).where(
                and_(
                    UserRole.user_id == user.id,
                    Role.name == "system_admin",
                    UserRole.is_active == True
                )
            )
        ).first()
        
        return user_role is not None
    
    def get_user_roles(
        self,
        user_id: UUID,
        organization_id: Optional[UUID] = None,
        study_id: Optional[UUID] = None
    ) -> List[UserRole]:
        """Get user's active roles with optional scope filtering"""
        query = select(UserRole).where(
            and_(
                UserRole.user_id == user_id,
                UserRole.is_active == True,
                or_(
                    UserRole.expires_at == None,
                    UserRole.expires_at > datetime.utcnow()
                )
            )
        )
        
        # Filter by scope if provided
        if study_id:
            query = query.where(
                or_(
                    UserRole.study_id == study_id,
                    UserRole.study_id == None  # Global roles
                )
            )
        
        if organization_id:
            query = query.where(
                or_(
                    UserRole.organization_id == organization_id,
                    UserRole.organization_id == None  # Global roles
                )
            )
        
        return self.db.exec(query).all()
    
    def role_has_permission(self, role_id: UUID, permission_name: str) -> bool:
        """Check if a role has a specific permission"""
        # Check for wildcard permission (system_admin)
        wildcard = self.db.exec(
            select(RolePermission).join(Permission).where(
                and_(
                    RolePermission.role_id == role_id,
                    Permission.name == "*",
                    RolePermission.is_active == True
                )
            )
        ).first()
        
        if wildcard:
            return True
        
        # Check for specific permission
        role_permission = self.db.exec(
            select(RolePermission).join(Permission).where(
                and_(
                    RolePermission.role_id == role_id,
                    Permission.name == permission_name,
                    RolePermission.is_active == True
                )
            )
        ).first()
        
        return role_permission is not None
    
    def grant_permission_to_role(
        self,
        role_id: UUID,
        permission_name: str,
        granted_by: UUID,
        conditions: Optional[Dict] = None
    ) -> RolePermission:
        """Grant a permission to a role"""
        # Get permission
        permission = self.db.exec(
            select(Permission).where(Permission.name == permission_name)
        ).first()
        
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission '{permission_name}' not found"
            )
        
        # Check if already granted
        existing = self.db.exec(
            select(RolePermission).where(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission.id
                )
            )
        ).first()
        
        if existing:
            if not existing.is_active:
                # Reactivate if inactive
                existing.is_active = True
                existing.granted_by = granted_by
                existing.granted_at = datetime.utcnow()
                self.db.commit()
                self._log_permission_change("reactivate", role_id, permission.id, granted_by)
                return existing
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Permission already granted to this role"
                )
        
        # Create new role permission
        role_permission = RolePermission(
            role_id=role_id,
            permission_id=permission.id,
            granted_by=granted_by,
            conditions=conditions,  # Already a dict/JSON field
            is_active=True
        )
        
        self.db.add(role_permission)
        self.db.commit()
        
        self._log_permission_change("grant", role_id, permission.id, granted_by)
        
        return role_permission
    
    def revoke_permission_from_role(
        self,
        role_id: UUID,
        permission_name: str,
        revoked_by: UUID
    ) -> bool:
        """Revoke a permission from a role"""
        # Get permission
        permission = self.db.exec(
            select(Permission).where(Permission.name == permission_name)
        ).first()
        
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission '{permission_name}' not found"
            )
        
        # Find role permission
        role_permission = self.db.exec(
            select(RolePermission).where(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission.id,
                    RolePermission.is_active == True
                )
            )
        ).first()
        
        if not role_permission:
            return False
        
        # Deactivate permission
        role_permission.is_active = False
        self.db.commit()
        
        self._log_permission_change("revoke", role_id, permission.id, revoked_by)
        
        return True
    
    def get_role_permissions(self, role_id: UUID) -> List[Permission]:
        """Get all active permissions for a role"""
        permissions = self.db.exec(
            select(Permission).join(RolePermission).where(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.is_active == True
                )
            )
        ).all()
        
        return permissions
    
    def get_user_permissions(self, user_id: UUID) -> Set[str]:
        """Get all unique permissions for a user across all their roles"""
        permissions = set()
        
        # Get user's roles
        user_roles = self.get_user_roles(user_id)
        
        for user_role in user_roles:
            # Get permissions for each role
            role_permissions = self.get_role_permissions(user_role.role_id)
            for permission in role_permissions:
                permissions.add(permission.name)
        
        return permissions
    
    def assign_role_to_user(
        self,
        user_id: UUID,
        role_name: str,
        assigned_by: UUID,
        organization_id: Optional[UUID] = None,
        study_id: Optional[UUID] = None,
        expires_at: Optional[datetime] = None
    ) -> UserRole:
        """Assign a role to a user"""
        # Get role
        role = self.db.exec(
            select(Role).where(Role.name == role_name)
        ).first()
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_name}' not found"
            )
        
        # Check if already assigned with same scope
        existing = self.db.exec(
            select(UserRole).where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role.id,
                    UserRole.organization_id == organization_id,
                    UserRole.study_id == study_id,
                    UserRole.is_active == True
                )
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role already assigned to user with this scope"
            )
        
        # Create user role
        user_role = UserRole(
            user_id=user_id,
            role_id=role.id,
            assigned_by=assigned_by,
            organization_id=organization_id,
            study_id=study_id,
            expires_at=expires_at,
            is_active=True
        )
        
        self.db.add(user_role)
        self.db.commit()
        
        self._log_role_assignment("assign", user_id, role.id, assigned_by)
        
        return user_role
    
    def remove_role_from_user(
        self,
        user_id: UUID,
        role_name: str,
        removed_by: UUID,
        organization_id: Optional[UUID] = None,
        study_id: Optional[UUID] = None
    ) -> bool:
        """Remove a role from a user"""
        # Get role
        role = self.db.exec(
            select(Role).where(Role.name == role_name)
        ).first()
        
        if not role:
            return False
        
        # Find user role
        user_role = self.db.exec(
            select(UserRole).where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role.id,
                    UserRole.organization_id == organization_id,
                    UserRole.study_id == study_id,
                    UserRole.is_active == True
                )
            )
        ).first()
        
        if not user_role:
            return False
        
        # Deactivate role
        user_role.is_active = False
        self.db.commit()
        
        self._log_role_assignment("remove", user_id, role.id, removed_by)
        
        return True
    
    def _log_permission_change(
        self,
        action: str,
        role_id: UUID,
        permission_id: UUID,
        user_id: UUID
    ):
        """Log permission changes for audit"""
        log_entry = PermissionAuditLog(
            action=action,
            resource_type="permission",
            resource_id=permission_id,
            user_id=user_id,
            details={
                "role_id": str(role_id),
                "permission_id": str(permission_id)
            }  # Pass as dict for JSON field
        )
        self.db.add(log_entry)
        self.db.commit()
    
    def _log_role_assignment(
        self,
        action: str,
        user_id: UUID,
        role_id: UUID,
        assigned_by: UUID
    ):
        """Log role assignments for audit"""
        log_entry = PermissionAuditLog(
            action=action,
            resource_type="user_role",
            resource_id=user_id,
            user_id=assigned_by,
            details={
                "user_id": str(user_id),
                "role_id": str(role_id)
            }  # Pass as dict for JSON field
        )
        self.db.add(log_entry)
        self.db.commit()
    
    def create_custom_permission(
        self,
        name: str,
        resource: str,
        action: str,
        description: Optional[str] = None,
        created_by: UUID = None
    ) -> Permission:
        """Create a custom permission"""
        # Check if permission already exists
        existing = self.db.exec(
            select(Permission).where(Permission.name == name)
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Permission '{name}' already exists"
            )
        
        permission = Permission(
            name=name,
            resource=resource,
            action=action,
            description=description,
            is_system=False
        )
        
        self.db.add(permission)
        self.db.commit()
        
        if created_by:
            self._log_permission_change("create", UUID("00000000-0000-0000-0000-000000000000"), permission.id, created_by)
        
        return permission