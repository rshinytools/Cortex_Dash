# ABOUTME: Background service for automatic template versioning
# ABOUTME: Creates versions based on time, change count, and events

from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import asyncio
import logging
import hashlib
import json

from app.models.dashboard import (
    DashboardTemplate,
    TemplateDraft,
    TemplateVersion,
    TemplateVersionCreate,
    TemplateChangeLog
)
from app.models.user import User
from app.services.template_change_detector import ChangeType
from app.core.config import settings

logger = logging.getLogger(__name__)


class AutoVersioningConfig:
    """Configuration for automatic versioning"""
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        self.enabled = config.get('enabled', True)
        self.strategy = config.get('strategy', 'balanced')  # aggressive, balanced, conservative
        
        # Time-based triggers
        time_config = config.get('time_triggers', {})
        self.draft_age_hours = time_config.get('draft_age_hours', 24)
        self.idle_time_hours = time_config.get('idle_time_hours', 2)
        self.max_draft_age_hours = time_config.get('max_draft_age_hours', 72)
        
        # Change-based triggers
        change_config = config.get('change_triggers', {})
        self.major_changes = change_config.get('major_changes', 1)
        self.minor_changes = change_config.get('minor_changes', 10)
        self.patch_changes = change_config.get('patch_changes', 25)
        
        # Event-based triggers
        event_config = config.get('event_triggers', {})
        self.before_publish = event_config.get('before_publish', True)
        self.user_switch = event_config.get('user_switch', True)
        self.before_deployment = event_config.get('before_deployment', True)
        
        # Storage configuration
        storage_config = config.get('storage', {})
        self.keep_all_major = storage_config.get('keep_all_major', True)
        self.keep_minor_count = storage_config.get('keep_minor_count', 10)
        self.keep_patch_count = storage_config.get('keep_patch_count', 5)
        self.archive_after_days = storage_config.get('archive_after_days', 180)
        self.compress_after_days = storage_config.get('compress_after_days', 90)


class TemplateAutoVersionService:
    """Automatic versioning service for templates"""
    
    def __init__(self, db: Session, config: Optional[Dict[str, Any]] = None):
        self.db = db
        self.config = AutoVersioningConfig(config)
        self.is_running = False
    
    async def start(self):
        """Start the auto-versioning service"""
        if not self.config.enabled:
            logger.info("Auto-versioning is disabled")
            return
        
        self.is_running = True
        logger.info("Starting auto-versioning service")
        
        while self.is_running:
            try:
                await self._check_all_drafts()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in auto-versioning service: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def stop(self):
        """Stop the auto-versioning service"""
        self.is_running = False
        logger.info("Stopping auto-versioning service")
    
    async def _check_all_drafts(self):
        """Check all active drafts for versioning triggers"""
        # Get all active drafts
        active_drafts = self.db.query(TemplateDraft).filter(
            TemplateDraft.is_active == True
        ).all()
        
        for draft in active_drafts:
            try:
                should_version, reason = await self._should_create_version(draft)
                if should_version:
                    await self.create_automatic_version(
                        draft=draft,
                        reason=reason
                    )
            except Exception as e:
                logger.error(f"Error checking draft {draft.id}: {e}")
    
    async def _should_create_version(
        self,
        draft: TemplateDraft
    ) -> tuple[bool, str]:
        """Check if a draft should trigger automatic version creation"""
        now = datetime.utcnow()
        
        # Time-based checks
        draft_age = now - draft.created_at
        idle_time = now - draft.updated_at
        
        # Check max draft age
        if draft_age > timedelta(hours=self.config.max_draft_age_hours):
            return True, f"Draft age exceeded {self.config.max_draft_age_hours} hours"
        
        # Check idle time
        if idle_time > timedelta(hours=self.config.idle_time_hours):
            # Only if there are changes
            if draft.changes_summary:
                return True, f"Draft idle for {self.config.idle_time_hours} hours with changes"
        
        # Change-based checks
        change_counts = await self._count_changes_by_type(draft)
        
        if change_counts.get('major', 0) >= self.config.major_changes:
            return True, f"Major changes threshold reached ({change_counts['major']} changes)"
        
        if change_counts.get('minor', 0) >= self.config.minor_changes:
            return True, f"Minor changes threshold reached ({change_counts['minor']} changes)"
        
        if change_counts.get('patch', 0) >= self.config.patch_changes:
            return True, f"Patch changes threshold reached ({change_counts['patch']} changes)"
        
        return False, ""
    
    async def _count_changes_by_type(
        self,
        draft: TemplateDraft
    ) -> Dict[str, int]:
        """Count changes by type for a draft"""
        change_logs = self.db.query(TemplateChangeLog).filter(
            TemplateChangeLog.draft_id == draft.id
        ).all()
        
        counts = {'major': 0, 'minor': 0, 'patch': 0}
        for log in change_logs:
            counts[log.change_type] = counts.get(log.change_type, 0) + 1
        
        return counts
    
    async def create_automatic_version(
        self,
        draft: TemplateDraft,
        reason: str,
        version_type: Optional[ChangeType] = None
    ) -> TemplateVersion:
        """Create a new version automatically from a draft"""
        # Get template
        template = self.db.query(DashboardTemplate).filter(
            DashboardTemplate.id == draft.template_id
        ).first()
        
        if not template:
            raise ValueError(f"Template {draft.template_id} not found")
        
        # Determine version type if not specified
        if not version_type:
            version_type = await self._determine_version_type(draft)
        
        # Calculate new version numbers
        new_major = template.major_version
        new_minor = template.minor_version
        new_patch = template.patch_version
        
        if version_type == ChangeType.MAJOR:
            new_major += 1
            new_minor = 0
            new_patch = 0
        elif version_type == ChangeType.MINOR:
            new_minor += 1
            new_patch = 0
        else:  # PATCH
            new_patch += 1
        
        # Get user info
        user = self.db.query(User).filter(
            User.id == draft.created_by
        ).first()
        
        # Generate change summary
        change_summary = []
        if draft.changes_summary:
            change_summary = draft.changes_summary
        
        # Create version
        version_data = {
            "template_id": template.id,
            "major_version": new_major,
            "minor_version": new_minor,
            "patch_version": new_patch,
            "template_structure": draft.draft_content,
            "change_description": f"Auto-version: {reason}",
            "version_type": version_type.value,
            "auto_created": True,
            "change_summary": change_summary,
            "created_by_name": user.name if user else "System",
            "comparison_hash": self._generate_hash(draft.draft_content)
        }
        
        version = TemplateVersion(
            **version_data,
            created_by=draft.created_by
        )
        
        self.db.add(version)
        
        # Update template version numbers
        template.major_version = new_major
        template.minor_version = new_minor
        template.patch_version = new_patch
        
        # Update template content from draft
        if draft.draft_content:
            template.name = draft.draft_content.get('name', template.name)
            template.description = draft.draft_content.get('description', template.description)
            template.menu_structure = draft.draft_content.get('menu_structure', template.menu_structure)
            template.dashboard_templates = draft.draft_content.get('dashboardTemplates', template.dashboard_templates)
            template.theme = draft.draft_content.get('theme', template.theme)
            template.settings = draft.draft_content.get('settings', template.settings)
        
        # Mark draft as inactive
        draft.is_active = False
        draft.conflict_status = f"Auto-versioned as {new_major}.{new_minor}.{new_patch}"
        
        self.db.commit()
        self.db.refresh(version)
        
        logger.info(
            f"Auto-created version {version.version_string} for template {template.id} - {reason}"
        )
        
        return version
    
    async def _determine_version_type(
        self,
        draft: TemplateDraft
    ) -> ChangeType:
        """Determine the version type based on changes"""
        change_counts = await self._count_changes_by_type(draft)
        
        if change_counts.get('major', 0) > 0:
            return ChangeType.MAJOR
        elif change_counts.get('minor', 0) > 0:
            return ChangeType.MINOR
        else:
            return ChangeType.PATCH
    
    def _generate_hash(self, content: Dict[str, Any]) -> str:
        """Generate a hash of the content for comparison"""
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    async def cleanup_old_versions(self):
        """Clean up old versions according to retention policy"""
        templates = self.db.query(DashboardTemplate).all()
        
        for template in templates:
            versions = self.db.query(TemplateVersion).filter(
                TemplateVersion.template_id == template.id
            ).order_by(
                TemplateVersion.major_version.desc(),
                TemplateVersion.minor_version.desc(),
                TemplateVersion.patch_version.desc()
            ).all()
            
            # Group versions by type
            major_versions = [v for v in versions if v.version_type == 'major']
            minor_versions = [v for v in versions if v.version_type == 'minor']
            patch_versions = [v for v in versions if v.version_type == 'patch']
            
            # Keep all major versions if configured
            if not self.config.keep_all_major:
                # Keep only recent major versions
                for v in major_versions[10:]:  # Keep last 10
                    if self._can_delete_version(v):
                        self.db.delete(v)
            
            # Keep configured number of minor versions
            for v in minor_versions[self.config.keep_minor_count:]:
                if self._can_delete_version(v):
                    self.db.delete(v)
            
            # Keep configured number of patch versions
            for v in patch_versions[self.config.keep_patch_count:]:
                if self._can_delete_version(v):
                    self.db.delete(v)
        
        self.db.commit()
        logger.info("Completed version cleanup")
    
    def _can_delete_version(self, version: TemplateVersion) -> bool:
        """Check if a version can be safely deleted"""
        # Don't delete if it's the current version
        template = version.template
        if (version.major_version == template.major_version and
            version.minor_version == template.minor_version and
            version.patch_version == template.patch_version):
            return False
        
        # Don't delete recent versions
        if version.created_at > datetime.utcnow() - timedelta(days=30):
            return False
        
        # Don't delete if it has special tags or is referenced
        # Add more checks as needed
        
        return True