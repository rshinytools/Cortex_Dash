# ABOUTME: Role management service for handling role operations
# ABOUTME: Provides methods for creating, updating, and managing roles

from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select, and_
from fastapi import HTTPException, status
import logging

from app.models.rbac import (
    Role, RolePermission, UserRole,
    DEFAULT_ROLE_PERMISSIONS
)

logger = logging.getLogger(__name__)


class RoleService:
    """Service for managing roles"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def initialize_default_roles(self):
        """Initialize default roles with descriptions"""
        default_roles = [
            {
                "name": "system_admin",
                "display_name": "System Administrator",
                "description": "Full system access with ability to manage all aspects of the platform"
            },
            {
                "name": "org_admin",
                "display_name": "Organization Administrator",
                "description": "Manage organization users, settings, and view all organization data"
            },
            {
                "name": "study_manager",
                "display_name": "Study Manager",
                "description": "Manage study teams, configure dashboards, and monitor study progress"
            },
            {
                "name": "data_analyst",
                "display_name": "Data Analyst",
                "description": "Analyze data, create reports, and export study data"
            },
            {
                "name": "viewer",
                "display_name": "Viewer",
                "description": "Read-only access to dashboards and reports"
            }
        ]
        
        for role_data in default_roles:
            existing = self.db.exec(
                select(Role).where(Role.name == role_data["name"])
            ).first()
            
            if not existing:
                role = Role(
                    **role_data,
                    is_system=True,
                    is_active=True
                )
                self.db.add(role)
                logger.info(f"Created role: {role_data['name']}")
        
        self.db.commit()
    
    def create_role(
        self,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        is_system: bool = False
    ) -> Role:
        """Create a new role"""
        # Check if role already exists
        existing = self.db.exec(
            select(Role).where(Role.name == name)
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role '{name}' already exists"
            )
        
        role = Role(
            name=name,
            display_name=display_name,
            description=description,
            is_system=is_system,
            is_active=True
        )
        
        self.db.add(role)
        self.db.commit()
        
        return role
    
    def update_role(
        self,
        role_id: UUID,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Role:
        """Update an existing role"""
        role = self.db.get(Role, role_id)
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        if role.is_system:
            # Limited updates for system roles
            if is_active is not None and not is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot deactivate system roles"
                )
        
        if display_name is not None:
            role.display_name = display_name
        
        if description is not None:
            role.description = description
        
        if is_active is not None:
            role.is_active = is_active
        
        role.updated_at = datetime.utcnow()
        
        self.db.add(role)
        self.db.commit()
        
        return role
    
    def delete_role(self, role_id: UUID) -> bool:
        """Delete a role (only non-system roles)"""
        role = self.db.get(Role, role_id)
        
        if not role:
            return False
        
        if role.is_system:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete system roles"
            )
        
        # Check if role is assigned to any users
        user_roles = self.db.exec(
            select(UserRole).where(
                and_(
                    UserRole.role_id == role_id,
                    UserRole.is_active == True
                )
            )
        ).first()
        
        if user_roles:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete role that is assigned to users"
            )
        
        # Deactivate associated permissions
        role_permissions = self.db.exec(
            select(RolePermission).where(
                RolePermission.role_id == role_id
            )
        ).all()
        
        for rp in role_permissions:
            rp.is_active = False
            self.db.add(rp)
        
        # Delete the role
        self.db.delete(role)
        self.db.commit()
        
        return True
    
    def get_role(self, role_id: UUID) -> Optional[Role]:
        """Get a role by ID"""
        return self.db.get(Role, role_id)
    
    def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get a role by name"""
        return self.db.exec(
            select(Role).where(Role.name == name)
        ).first()
    
    def list_roles(self, include_inactive: bool = False) -> List[Role]:
        """List all roles"""
        query = select(Role)
        
        if not include_inactive:
            query = query.where(Role.is_active == True)
        
        return self.db.exec(query.order_by(Role.name)).all()
    
    def get_role_statistics(self, role_id: UUID) -> Dict:
        """Get statistics for a role"""
        role = self.db.get(Role, role_id)
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        # Count permissions
        permission_count = self.db.exec(
            select(RolePermission).where(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.is_active == True
                )
            )
        ).all()
        
        # Count users
        user_count = self.db.exec(
            select(UserRole).where(
                and_(
                    UserRole.role_id == role_id,
                    UserRole.is_active == True
                )
            )
        ).all()
        
        return {
            "role": role,
            "permission_count": len(permission_count),
            "user_count": len(user_count)
        }