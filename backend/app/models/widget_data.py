# ABOUTME: Models for widget data requests and responses
# ABOUTME: Handles data structures for dashboard widget data execution

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class WidgetDataStatus(str, Enum):
    """Status of widget data response"""
    SUCCESS = "success"
    ERROR = "error"
    NO_DATA = "no_data"
    PROCESSING = "processing"


class WidgetDataRequest(BaseModel):
    """Request model for widget data execution"""
    widget_id: str
    widget_config: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None
    pagination: Optional[Dict[str, int]] = None
    refresh: bool = False


class WidgetDataResponse(BaseModel):
    """Response model for widget data"""
    widget_id: str
    status: WidgetDataStatus = WidgetDataStatus.SUCCESS
    data: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    cached: bool = False
    cache_expires_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    error: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }