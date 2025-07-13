# ABOUTME: Service for managing template drafts with auto-save and conflict detection
# ABOUTME: Handles draft creation, updates, change tracking, and conflict resolution

from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging

from app.models.dashboard import (
    TemplateDraft, TemplateDraftCreate, TemplateDraftUpdate,
    TemplateChangeLog, TemplateChangeLogCreate,
    DashboardTemplate
)
from app.models.user import User
from app.services.template_change_detector import (
    TemplateChangeDetector, ChangeType, ChangeCategory
)
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class TemplateDraftService:
    """Manages template drafts and change tracking"""
    
    def __init__(self, db: Session):
        self.db = db
        self.change_detector = TemplateChangeDetector()
    
    async def get_or_create_draft(
        self,
        template_id: UUID,
        user_id: UUID
    ) -> TemplateDraft:
        """Get existing active draft or create new one"""
        # Check for existing active draft by this user
        draft = self.db.query(TemplateDraft).filter(
            and_(
                TemplateDraft.template_id == template_id,
                TemplateDraft.created_by == user_id,
                TemplateDraft.is_active == True
            )
        ).first()
        
        if draft:
            # Update auto_save_at
            draft.auto_save_at = datetime.utcnow()
            draft.updated_at = datetime.utcnow()
            self.db.commit()
            return draft
        
        # Get template
        template = self.db.query(DashboardTemplate).filter(
            DashboardTemplate.id == template_id
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
        
        # Get latest version if exists
        latest_version = None
        if template.template_versions:
            latest_version = max(
                template.template_versions,
                key=lambda v: (v.major_version, v.minor_version, v.patch_version)
            )
        
        # Create new draft
        # Extract data from template_structure
        template_data = template.template_structure or {}
        draft_data = TemplateDraftCreate(
            template_id=template_id,
            base_version_id=latest_version.id if latest_version else None,
            draft_content={
                "name": template.name,
                "description": template.description,
                "menu_structure": template_data.get("menu_structure", template_data.get("menu", {"items": []})),
                "dashboardTemplates": template_data.get("dashboardTemplates", template_data.get("dashboards", [])),
                "theme": template_data.get("theme", {}),
                "settings": template_data.get("settings", {}),
                "data_mappings": template_data.get("data_mappings", {})
            },
            changes_summary=[],
            is_active=True
        )
        
        draft = TemplateDraft(
            **draft_data.dict(),
            created_by=user_id
        )
        
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)
        
        return draft
    
    async def update_draft(
        self,
        draft_id: UUID,
        user_id: UUID,
        content: Dict[str, Any],
        track_changes: bool = True
    ) -> TemplateDraft:
        """Update draft content and track changes"""
        draft = self.db.query(TemplateDraft).filter(
            TemplateDraft.id == draft_id
        ).first()
        
        if not draft:
            raise HTTPException(status_code=404, detail=f"Draft {draft_id} not found")
        
        # Check for conflicts if another user is editing
        if draft.created_by != user_id:
            await self._check_conflicts(draft, user_id)
        
        # Track changes if requested
        if track_changes and draft.draft_content:
            change_type, changes = self.change_detector.detect_changes(
                draft.draft_content,
                content
            )
            
            # Log each change
            for change in changes:
                change_log = TemplateChangeLog(
                    template_id=draft.template_id,
                    draft_id=draft.id,
                    change_type=change_type.value,
                    change_category=change.get('category', ChangeCategory.METADATA).value,
                    change_description=change.get('description', ''),
                    change_data=change,
                    created_by=user_id
                )
                self.db.add(change_log)
            
            # Update changes summary
            draft.changes_summary = draft.changes_summary or []
            draft.changes_summary.extend([{
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": str(user_id),
                "change_type": change_type.value,
                "summary": self.change_detector.generate_change_summary(changes)
            }])
        
        # Update draft
        draft.draft_content = content
        draft.auto_save_at = datetime.utcnow()
        draft.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(draft)
        
        return draft
    
    async def get_active_drafts(
        self,
        template_id: UUID
    ) -> List[TemplateDraft]:
        """Get all active drafts for a template"""
        return self.db.query(TemplateDraft).filter(
            and_(
                TemplateDraft.template_id == template_id,
                TemplateDraft.is_active == True
            )
        ).all()
    
    async def _check_conflicts(
        self,
        draft: TemplateDraft,
        user_id: UUID
    ) -> None:
        """Check for editing conflicts"""
        # Check if draft was recently updated by another user
        if draft.updated_at > datetime.utcnow() - timedelta(minutes=5):
            other_user = self.db.query(User).filter(
                User.id == draft.created_by
            ).first()
            
            raise HTTPException(status_code=409, detail=
                f"This template is currently being edited by {other_user.name if other_user else 'another user'}. "
                f"Last update was {draft.updated_at}"
            )
    
    async def merge_drafts(
        self,
        draft1_id: UUID,
        draft2_id: UUID,
        strategy: str = "prefer_recent"
    ) -> TemplateDraft:
        """Merge two drafts with conflict resolution"""
        draft1 = self.db.query(TemplateDraft).filter(
            TemplateDraft.id == draft1_id
        ).first()
        draft2 = self.db.query(TemplateDraft).filter(
            TemplateDraft.id == draft2_id
        ).first()
        
        if not draft1 or not draft2:
            raise HTTPException(status_code=404, detail="One or both drafts not found")
        
        if draft1.template_id != draft2.template_id:
            raise HTTPException(status_code=409, detail="Cannot merge drafts from different templates")
        
        # Simple merge strategy for now - prefer more recent
        if strategy == "prefer_recent":
            primary = draft1 if draft1.updated_at > draft2.updated_at else draft2
            secondary = draft2 if primary == draft1 else draft1
        else:
            primary = draft1
            secondary = draft2
        
        # Mark secondary as inactive
        secondary.is_active = False
        secondary.conflict_status = f"Merged into {primary.id}"
        
        # Combine changes summary
        primary.changes_summary = (primary.changes_summary or []) + (secondary.changes_summary or [])
        
        self.db.commit()
        self.db.refresh(primary)
        
        return primary
    
    async def discard_draft(
        self,
        draft_id: UUID,
        user_id: UUID
    ) -> None:
        """Discard a draft"""
        draft = self.db.query(TemplateDraft).filter(
            and_(
                TemplateDraft.id == draft_id,
                TemplateDraft.created_by == user_id
            )
        ).first()
        
        if not draft:
            raise HTTPException(status_code=404, detail=f"Draft {draft_id} not found or access denied")
        
        draft.is_active = False
        draft.conflict_status = "Discarded by user"
        
        self.db.commit()
    
    async def cleanup_old_drafts(
        self,
        days_old: int = 7
    ) -> int:
        """Clean up old inactive drafts"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        old_drafts = self.db.query(TemplateDraft).filter(
            and_(
                TemplateDraft.updated_at < cutoff_date,
                or_(
                    TemplateDraft.is_active == False,
                    TemplateDraft.auto_save_at < cutoff_date
                )
            )
        ).all()
        
        count = len(old_drafts)
        
        for draft in old_drafts:
            self.db.delete(draft)
        
        self.db.commit()
        
        logger.info(f"Cleaned up {count} old drafts")
        return count
    
    async def get_recent_changes(
        self,
        template_id: UUID,
        limit: int = 50
    ) -> List[TemplateChangeLog]:
        """Get recent changes for a template"""
        return self.db.query(TemplateChangeLog).filter(
            TemplateChangeLog.template_id == template_id
        ).order_by(
            TemplateChangeLog.created_at.desc()
        ).limit(limit).all()