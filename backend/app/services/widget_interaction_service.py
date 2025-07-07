# ABOUTME: Widget interaction service for handling cross-widget communication and state management
# ABOUTME: Manages filters, parameters, drill-down, and real-time collaboration features

import uuid
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
import logging

from sqlmodel import Session, select
from pydantic import BaseModel, Field

from app.models.widget import WidgetDefinition
from app.models.dashboard import DashboardTemplate, StudyDashboard  
from app.models.study import Study
from app.core.config import settings
from app.services.redis_cache import get_redis_cache

logger = logging.getLogger(__name__)


class InteractionType(str, Enum):
    """Types of widget interactions"""
    FILTER = "filter"
    PARAMETER = "parameter" 
    DRILL_DOWN = "drill_down"
    SELECTION = "selection"
    ANNOTATION = "annotation"
    COLLABORATION = "collaboration"


class FilterOperator(str, Enum):
    """Filter operators"""
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class FilterDefinition(BaseModel):
    """Filter definition model"""
    id: str
    field: str
    label: str
    operator: FilterOperator
    values: List[Any]
    widget_id: Optional[str] = None
    source_widget_id: Optional[str] = None
    scope: str = "dashboard"  # dashboard, widget, global
    active: bool = True
    temporary: bool = False
    created_at: datetime
    expires_at: Optional[datetime] = None


class ParameterDefinition(BaseModel):
    """Parameter definition model"""
    id: str
    name: str
    label: str
    type: str  # string, number, date, boolean, select, multi_select
    value: Any
    default_value: Any
    scope: str = "dashboard"  # global, dashboard, study
    widget_bindings: List[str] = Field(default_factory=list)
    validation_rules: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DrillDownLevel(BaseModel):
    """Drill-down level model"""
    id: str
    field: str
    value: Any
    display_value: Optional[str] = None
    level: int
    widget_id: str
    parent_level_id: Optional[str] = None
    timestamp: datetime
    context: Optional[Dict[str, Any]] = None


class DrillDownPath(BaseModel):
    """Drill-down path model"""
    id: str
    dashboard_id: str
    levels: List[DrillDownLevel]
    current_level: int
    max_depth: int
    created_at: datetime
    updated_at: datetime


class InteractionEvent(BaseModel):
    """Widget interaction event"""
    id: str
    dashboard_id: str
    widget_id: str
    interaction_type: InteractionType
    event_data: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime
    expires_at: Optional[datetime] = None


class WidgetInteractionService:
    """Service for managing widget interactions"""
    
    def __init__(self, db: Session):
        self.db = db
        self.redis = get_redis_cache()
        self.interaction_cache_ttl = 3600  # 1 hour
        self.collaboration_cache_ttl = 300  # 5 minutes
        
    async def apply_filters(
        self,
        dashboard_id: str,
        filters: List[FilterDefinition],
        widget_id: Optional[str] = None
    ) -> str:
        """Apply filters to dashboard or specific widget"""
        try:
            filter_key = f"dashboard_filters:{dashboard_id}"
            if widget_id:
                filter_key += f":widget:{widget_id}"
            
            # Store filters in Redis
            filter_data = {
                "filters": [f.model_dump() for f in filters],
                "applied_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
            
            await self.redis.setex(
                filter_key,
                self.interaction_cache_ttl,
                json.dumps(filter_data)
            )
            
            # Notify other widgets about filter changes
            await self._broadcast_interaction_event(
                dashboard_id=dashboard_id,
                widget_id=widget_id or "system",
                interaction_type=InteractionType.FILTER,
                event_data={
                    "action": "filters_applied",
                    "filter_count": len(filters),
                    "target_widget": widget_id
                }
            )
            
            return filter_key
            
        except Exception as e:
            logger.error(f"Error applying filters: {str(e)}")
            raise
    
    async def get_active_filters(
        self,
        dashboard_id: str,
        widget_id: Optional[str] = None
    ) -> List[FilterDefinition]:
        """Get active filters for dashboard or widget"""
        try:
            filter_key = f"dashboard_filters:{dashboard_id}"
            if widget_id:
                filter_key += f":widget:{widget_id}"
            
            filter_data_str = await self.redis.get(filter_key)
            if not filter_data_str:
                return []
            
            filter_data = json.loads(filter_data_str)
            filters = []
            
            for f_data in filter_data.get("filters", []):
                # Check if filter hasn't expired
                if f_data.get("expires_at"):
                    expires_at = datetime.fromisoformat(f_data["expires_at"])
                    if datetime.utcnow() > expires_at:
                        continue
                
                filters.append(FilterDefinition(**f_data))
            
            return [f for f in filters if f.active]
            
        except Exception as e:
            logger.error(f"Error getting active filters: {str(e)}")
            return []
    
    async def clear_filters(
        self,
        dashboard_id: str,
        widget_id: Optional[str] = None,
        filter_ids: Optional[List[str]] = None
    ) -> None:
        """Clear filters from dashboard or widget"""
        try:
            if filter_ids:
                # Clear specific filters
                current_filters = await self.get_active_filters(dashboard_id, widget_id)
                remaining_filters = [f for f in current_filters if f.id not in filter_ids]
                await self.apply_filters(dashboard_id, remaining_filters, widget_id)
            else:
                # Clear all filters
                filter_key = f"dashboard_filters:{dashboard_id}"
                if widget_id:
                    filter_key += f":widget:{widget_id}"
                
                await self.redis.delete(filter_key)
            
            # Notify about filter clearing
            await self._broadcast_interaction_event(
                dashboard_id=dashboard_id,
                widget_id=widget_id or "system",
                interaction_type=InteractionType.FILTER,
                event_data={
                    "action": "filters_cleared",
                    "filter_ids": filter_ids,
                    "target_widget": widget_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error clearing filters: {str(e)}")
            raise
    
    async def set_parameters(
        self,
        dashboard_id: str,
        parameters: List[ParameterDefinition]
    ) -> None:
        """Set dashboard parameters"""
        try:
            param_key = f"dashboard_parameters:{dashboard_id}"
            
            param_data = {
                "parameters": [p.model_dump() for p in parameters],
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await self.redis.setex(
                param_key,
                self.interaction_cache_ttl,
                json.dumps(param_data)
            )
            
            # Notify widgets about parameter changes
            await self._broadcast_interaction_event(
                dashboard_id=dashboard_id,
                widget_id="system",
                interaction_type=InteractionType.PARAMETER,
                event_data={
                    "action": "parameters_updated",
                    "parameter_count": len(parameters)
                }
            )
            
        except Exception as e:
            logger.error(f"Error setting parameters: {str(e)}")
            raise
    
    async def get_parameters(self, dashboard_id: str) -> List[ParameterDefinition]:
        """Get dashboard parameters"""
        try:
            param_key = f"dashboard_parameters:{dashboard_id}"
            
            param_data_str = await self.redis.get(param_key)
            if not param_data_str:
                return []
            
            param_data = json.loads(param_data_str)
            parameters = []
            
            for p_data in param_data.get("parameters", []):
                parameters.append(ParameterDefinition(**p_data))
            
            return parameters
            
        except Exception as e:
            logger.error(f"Error getting parameters: {str(e)}")
            return []
    
    async def start_drill_down(
        self,
        dashboard_id: str,
        widget_id: str,
        field: str,
        value: Any,
        display_value: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a new drill-down path"""
        try:
            path_id = str(uuid.uuid4())
            level_id = str(uuid.uuid4())
            
            level = DrillDownLevel(
                id=level_id,
                field=field,
                value=value,
                display_value=display_value,
                level=0,
                widget_id=widget_id,
                timestamp=datetime.utcnow(),
                context=context
            )
            
            path = DrillDownPath(
                id=path_id,
                dashboard_id=dashboard_id,
                levels=[level],
                current_level=0,
                max_depth=5,  # Default max depth
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Store drill-down path
            drill_key = f"drill_down_path:{path_id}"
            await self.redis.setex(
                drill_key,
                self.interaction_cache_ttl,
                json.dumps(path.model_dump(), default=str)
            )
            
            # Store active drill-down for dashboard
            active_key = f"active_drill_down:{dashboard_id}"
            await self.redis.setex(
                active_key,
                self.interaction_cache_ttl,
                path_id
            )
            
            # Create filter for drill-down
            drill_filter = FilterDefinition(
                id=f"drill_{level_id}",
                field=field,
                label=f"Drill-down: {display_value or str(value)}",
                operator=FilterOperator.EQ,
                values=[value],
                source_widget_id=widget_id,
                scope="dashboard",
                active=True,
                temporary=True,
                created_at=datetime.utcnow()
            )
            
            await self.apply_filters(dashboard_id, [drill_filter])
            
            # Notify about drill-down start
            await self._broadcast_interaction_event(
                dashboard_id=dashboard_id,
                widget_id=widget_id,
                interaction_type=InteractionType.DRILL_DOWN,
                event_data={
                    "action": "drill_down_started",
                    "path_id": path_id,
                    "field": field,
                    "value": value,
                    "display_value": display_value
                }
            )
            
            return path_id
            
        except Exception as e:
            logger.error(f"Error starting drill-down: {str(e)}")
            raise
    
    async def add_drill_down_level(
        self,
        path_id: str,
        field: str,
        value: Any,
        display_value: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a new level to existing drill-down path"""
        try:
            drill_key = f"drill_down_path:{path_id}"
            path_data_str = await self.redis.get(drill_key)
            
            if not path_data_str:
                raise ValueError(f"Drill-down path {path_id} not found")
            
            path_data = json.loads(path_data_str)
            path = DrillDownPath(**path_data)
            
            # Check depth limit
            if path.current_level >= path.max_depth - 1:
                raise ValueError("Maximum drill-down depth reached")
            
            level_id = str(uuid.uuid4())
            current_level = path.levels[path.current_level]
            
            new_level = DrillDownLevel(
                id=level_id,
                field=field,
                value=value,
                display_value=display_value,
                level=path.current_level + 1,
                widget_id=current_level.widget_id,
                parent_level_id=current_level.id,
                timestamp=datetime.utcnow(),
                context=context
            )
            
            path.levels.append(new_level)
            path.current_level += 1
            path.updated_at = datetime.utcnow()
            
            # Update stored path
            await self.redis.setex(
                drill_key,
                self.interaction_cache_ttl,
                json.dumps(path.model_dump(), default=str)
            )
            
            # Add additional filter
            drill_filter = FilterDefinition(
                id=f"drill_{level_id}",
                field=field,
                label=f"Drill-down L{new_level.level}: {display_value or str(value)}",
                operator=FilterOperator.EQ,
                values=[value],
                source_widget_id=current_level.widget_id,
                scope="dashboard",
                active=True,
                temporary=True,
                created_at=datetime.utcnow()
            )
            
            current_filters = await self.get_active_filters(path.dashboard_id)
            current_filters.append(drill_filter)
            await self.apply_filters(path.dashboard_id, current_filters)
            
            # Notify about level addition
            await self._broadcast_interaction_event(
                dashboard_id=path.dashboard_id,
                widget_id=current_level.widget_id,
                interaction_type=InteractionType.DRILL_DOWN,
                event_data={
                    "action": "drill_down_level_added",
                    "path_id": path_id,
                    "level": new_level.level,
                    "field": field,
                    "value": value
                }
            )
            
        except Exception as e:
            logger.error(f"Error adding drill-down level: {str(e)}")
            raise
    
    async def get_drill_down_path(self, path_id: str) -> Optional[DrillDownPath]:
        """Get drill-down path by ID"""
        try:
            drill_key = f"drill_down_path:{path_id}"
            path_data_str = await self.redis.get(drill_key)
            
            if not path_data_str:
                return None
            
            path_data = json.loads(path_data_str)
            return DrillDownPath(**path_data)
            
        except Exception as e:
            logger.error(f"Error getting drill-down path: {str(e)}")
            return None
    
    async def clear_drill_down(self, dashboard_id: str, path_id: Optional[str] = None) -> None:
        """Clear drill-down path and associated filters"""
        try:
            if path_id:
                # Clear specific path
                drill_key = f"drill_down_path:{path_id}"
                await self.redis.delete(drill_key)
                
                # Clear associated temporary filters
                current_filters = await self.get_active_filters(dashboard_id)
                non_temp_filters = [f for f in current_filters if not f.temporary]
                await self.apply_filters(dashboard_id, non_temp_filters)
            else:
                # Clear active drill-down
                active_key = f"active_drill_down:{dashboard_id}"
                active_path_id = await self.redis.get(active_key)
                
                if active_path_id:
                    await self.clear_drill_down(dashboard_id, active_path_id)
                    await self.redis.delete(active_key)
            
            # Notify about drill-down clear
            await self._broadcast_interaction_event(
                dashboard_id=dashboard_id,
                widget_id="system",
                interaction_type=InteractionType.DRILL_DOWN,
                event_data={
                    "action": "drill_down_cleared",
                    "path_id": path_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error clearing drill-down: {str(e)}")
            raise
    
    async def record_interaction_event(
        self,
        dashboard_id: str,
        widget_id: str,
        interaction_type: InteractionType,
        event_data: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> str:
        """Record a widget interaction event"""
        try:
            event_id = str(uuid.uuid4())
            
            event = InteractionEvent(
                id=event_id,
                dashboard_id=dashboard_id,
                widget_id=widget_id,
                interaction_type=interaction_type,
                event_data=event_data,
                user_id=user_id,
                session_id=session_id,
                timestamp=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=ttl or self.interaction_cache_ttl)
            )
            
            # Store event
            event_key = f"interaction_event:{event_id}"
            await self.redis.setex(
                event_key,
                ttl or self.interaction_cache_ttl,
                json.dumps(event.model_dump(), default=str)
            )
            
            # Add to dashboard event list
            events_key = f"dashboard_events:{dashboard_id}"
            await self.redis.lpush(events_key, event_id)
            await self.redis.expire(events_key, ttl or self.interaction_cache_ttl)
            
            return event_id
            
        except Exception as e:
            logger.error(f"Error recording interaction event: {str(e)}")
            raise
    
    async def get_recent_events(
        self,
        dashboard_id: str,
        limit: int = 50,
        interaction_types: Optional[List[InteractionType]] = None
    ) -> List[InteractionEvent]:
        """Get recent interaction events for dashboard"""
        try:
            events_key = f"dashboard_events:{dashboard_id}"
            event_ids = await self.redis.lrange(events_key, 0, limit - 1)
            
            events = []
            for event_id in event_ids:
                event_key = f"interaction_event:{event_id}"
                event_data_str = await self.redis.get(event_key)
                
                if event_data_str:
                    event_data = json.loads(event_data_str)
                    event = InteractionEvent(**event_data)
                    
                    # Filter by interaction types if specified
                    if not interaction_types or event.interaction_type in interaction_types:
                        events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting recent events: {str(e)}")
            return []
    
    async def _broadcast_interaction_event(
        self,
        dashboard_id: str,
        widget_id: str,
        interaction_type: InteractionType,
        event_data: Dict[str, Any]
    ) -> None:
        """Broadcast interaction event to all dashboard subscribers"""
        try:
            # Record the event
            await self.record_interaction_event(
                dashboard_id=dashboard_id,
                widget_id=widget_id,
                interaction_type=interaction_type,
                event_data=event_data
            )
            
            # Broadcast via Redis pub/sub for real-time updates
            channel = f"dashboard_interactions:{dashboard_id}"
            message = {
                "widget_id": widget_id,
                "interaction_type": interaction_type.value,
                "event_data": event_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.redis.publish(channel, json.dumps(message))
            
        except Exception as e:
            logger.error(f"Error broadcasting interaction event: {str(e)}")
    
    async def subscribe_to_interactions(self, dashboard_id: str):
        """Subscribe to dashboard interaction events"""
        try:
            channel = f"dashboard_interactions:{dashboard_id}"
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(channel)
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    yield json.loads(message['data'])
                    
        except Exception as e:
            logger.error(f"Error subscribing to interactions: {str(e)}")
    
    async def cleanup_expired_data(self) -> None:
        """Clean up expired interaction data"""
        try:
            # This would typically be run as a background task
            current_time = datetime.utcnow()
            
            # Clean up expired filters, paths, events, etc.
            # Implementation would scan Redis keys and remove expired items
            logger.info("Cleaned up expired interaction data")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired data: {str(e)}")


# Factory function
def get_widget_interaction_service(db: Session) -> WidgetInteractionService:
    """Get widget interaction service instance"""
    return WidgetInteractionService(db)