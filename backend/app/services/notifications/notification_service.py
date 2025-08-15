# ABOUTME: Notification service for alerts and messaging
# ABOUTME: Handles in-app notifications, email alerts, and system messages

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from sqlmodel import Session

from app.core.logging import logger

class NotificationType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    ALERT = "alert"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationService:
    """Notification and alert service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        action_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new notification"""
        
        notification = {
            "id": f"notif_{datetime.utcnow().timestamp()}",
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": notification_type,
            "priority": priority,
            "action_url": action_url,
            "metadata": metadata or {},
            "is_read": False,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Broadcast via WebSocket
        from app.services.realtime.websocket_manager import manager
        await manager.broadcast_notification(user_id, notification)
        
        logger.info(f"Notification created for user {user_id}: {title}")
        
        return notification
    
    async def send_data_refresh_alert(
        self,
        study_id: str,
        status: str,
        details: Dict[str, Any]
    ):
        """Send data refresh status notification"""
        
        # Get study users
        users = await self._get_study_users(study_id)
        
        for user_id in users:
            if status == "completed":
                await self.create_notification(
                    user_id=user_id,
                    title="Data Refresh Complete",
                    message=f"Study data has been successfully refreshed",
                    notification_type=NotificationType.SUCCESS,
                    metadata=details
                )
            elif status == "failed":
                await self.create_notification(
                    user_id=user_id,
                    title="Data Refresh Failed",
                    message=f"Data refresh encountered an error",
                    notification_type=NotificationType.ERROR,
                    priority=NotificationPriority.HIGH,
                    metadata=details
                )
    
    async def send_threshold_alert(
        self,
        widget_id: str,
        metric_name: str,
        current_value: float,
        threshold: float,
        threshold_type: str
    ):
        """Send alert when metric crosses threshold"""
        
        # Get widget owners
        users = await self._get_widget_users(widget_id)
        
        for user_id in users:
            await self.create_notification(
                user_id=user_id,
                title=f"Threshold Alert: {metric_name}",
                message=f"{metric_name} has {threshold_type} threshold: {current_value} (threshold: {threshold})",
                notification_type=NotificationType.ALERT,
                priority=NotificationPriority.HIGH,
                action_url=f"/dashboard/widget/{widget_id}"
            )
    
    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        
        # This would query the database
        # For now, return example data
        return [
            {
                "id": "notif_1",
                "title": "Data Upload Complete",
                "message": "Your data upload has been processed",
                "type": "success",
                "priority": "medium",
                "is_read": False,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
    
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as read"""
        
        # Update in database
        logger.info(f"Notification {notification_id} marked as read by {user_id}")
        return True
    
    async def _get_study_users(self, study_id: str) -> List[str]:
        """Get users associated with a study"""
        # This would query the database
        return ["user_123", "user_456"]
    
    async def _get_widget_users(self, widget_id: str) -> List[str]:
        """Get users who own or subscribe to a widget"""
        # This would query the database
        return ["user_123"]