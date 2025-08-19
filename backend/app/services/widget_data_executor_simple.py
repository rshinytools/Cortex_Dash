# ABOUTME: Simplified widget data executor for testing
# ABOUTME: Returns mock data for all widget types to enable dashboard visualization

import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from sqlmodel import Session
from pydantic import BaseModel, Field

from app.models.widget import WidgetDefinition
from app.models.study import Study


class WidgetDataRequest(BaseModel):
    """Request model for widget data"""
    widget_id: str
    widget_config: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None
    pagination: Optional[Dict[str, int]] = None
    refresh: bool = False


class WidgetDataResponse(BaseModel):
    """Response model for widget data"""
    widget_id: str
    status: str = "success"
    data: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    cached: bool = False
    cache_expires_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    error: Optional[str] = None


class SimpleWidgetExecutor:
    """Simple executor that returns mock data for any widget"""
    
    def __init__(self, db: Session, study: Study, widget_def: WidgetDefinition):
        self.db = db
        self.study = study
        self.widget_def = widget_def
    
    async def execute(self, request: WidgetDataRequest) -> WidgetDataResponse:
        """Execute widget data request - returns mock data"""
        start_time = time.time()
        
        # Determine widget type from category
        category = self.widget_def.category.lower() if self.widget_def.category else "metrics"
        
        # Generate appropriate mock data
        if category in ["metrics", "kpi"]:
            data = self._generate_kpi_data(request.widget_config)
        elif category == "charts":
            data = self._generate_chart_data(request.widget_config)
        elif category == "tables":
            data = self._generate_table_data(request.widget_config, request.pagination)
        elif category == "statistics":
            data = self._generate_statistics_data(request.widget_config)
        elif category == "timelines":
            data = self._generate_timeline_data(request.widget_config)
        else:
            data = {"value": random.randint(100, 1000), "label": "Sample Metric"}
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return WidgetDataResponse(
            widget_id=request.widget_id,
            status="success",
            data=data,
            metadata={
                "study_id": str(self.study.id),
                "widget_type": category,
                "is_mock_data": True
            },
            execution_time_ms=execution_time,
            cached=False
        )
    
    def _generate_kpi_data(self, config):
        """Generate mock KPI data"""
        metric_type = config.get("metric_type", "general")
        
        if metric_type == "enrollment_rate":
            value = f"{random.randint(75, 95)}%"
            trend = f"+{random.randint(2, 8)}%"
            label = "Enrollment Rate"
        elif metric_type == "sae_count":
            value = random.randint(5, 25)
            trend = f"{random.choice(['+', '-'])}{random.randint(1, 5)}"
            label = "Serious AEs"
        else:
            value = random.randint(100, 999)
            trend = "+12%"
            label = config.get("label", "Metric")
        
        return {
            "value": value,
            "trend": trend,
            "comparison": "vs last period",
            "label": label
        }
    
    def _generate_chart_data(self, config):
        """Generate mock chart data"""
        chart_type = config.get("chart_type", "line")
        
        if chart_type == "line":
            dates = [(datetime.now() - timedelta(days=30-i)).strftime("%m/%d") for i in range(30)]
            return {
                "labels": dates,
                "datasets": [{
                    "label": "Enrolled",
                    "data": [random.randint(10, 50) for _ in range(30)],
                    "borderColor": "rgb(75, 192, 192)"
                }]
            }
        elif chart_type == "bar":
            return {
                "labels": ["Site A", "Site B", "Site C", "Site D", "Site E"],
                "datasets": [{
                    "label": "Enrollment",
                    "data": [random.randint(20, 100) for _ in range(5)],
                    "backgroundColor": "rgba(54, 162, 235, 0.5)"
                }]
            }
        elif chart_type == "pie":
            return {
                "labels": ["Completed", "Active", "Withdrawn", "Screening"],
                "datasets": [{
                    "data": [45, 30, 15, 10],
                    "backgroundColor": [
                        "rgba(75, 192, 192, 0.5)",
                        "rgba(54, 162, 235, 0.5)",
                        "rgba(255, 206, 86, 0.5)",
                        "rgba(255, 99, 132, 0.5)"
                    ]
                }]
            }
        return {}
    
    def _generate_table_data(self, config, pagination):
        """Generate mock table data"""
        page = pagination.get("page", 1) if pagination else 1
        page_size = pagination.get("page_size", 20) if pagination else 20
        
        # Generate rows
        rows = []
        for i in range(page_size):
            row_num = (page - 1) * page_size + i + 1
            rows.append({
                "id": f"SUBJ-{row_num:04d}",
                "site": f"Site {chr(65 + (row_num % 10))}",
                "status": random.choice(["Active", "Completed", "Withdrawn"]),
                "enrollment_date": (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d"),
                "age": random.randint(18, 75),
                "gender": random.choice(["M", "F"])
            })
        
        return {
            "columns": [
                {"key": "id", "label": "Subject ID", "sortable": True},
                {"key": "site", "label": "Site", "sortable": True},
                {"key": "status", "label": "Status", "sortable": True},
                {"key": "enrollment_date", "label": "Enrollment Date", "sortable": True},
                {"key": "age", "label": "Age", "sortable": True},
                {"key": "gender", "label": "Gender", "sortable": True}
            ],
            "rows": rows,
            "total": 500,
            "page": page,
            "pageSize": page_size
        }
    
    def _generate_statistics_data(self, config):
        """Generate mock statistics data"""
        return {
            "summary": {
                "mean": round(random.uniform(50, 100), 2),
                "median": round(random.uniform(45, 95), 2),
                "std_dev": round(random.uniform(10, 25), 2),
                "min": random.randint(10, 30),
                "max": random.randint(120, 200),
                "count": random.randint(100, 500)
            }
        }
    
    def _generate_timeline_data(self, config):
        """Generate mock timeline data"""
        events = []
        milestones = ["Study Start", "First Patient In", "50% Enrolled", "Last Patient In", "Database Lock"]
        base_date = datetime.now() - timedelta(days=180)
        
        for i, milestone in enumerate(milestones):
            event_date = base_date + timedelta(days=i*30)
            events.append({
                "id": f"event-{i}",
                "title": milestone,
                "date": event_date.isoformat(),
                "status": "completed" if i < 3 else "pending"
            })
        
        return {
            "events": events,
            "currentPhase": "Enrollment",
            "progress": 65
        }
    
    def get_cache_ttl(self) -> int:
        """Get cache TTL in seconds"""
        return 300  # 5 minutes


class WidgetDataExecutorFactory:
    """Factory for creating widget data executors"""
    
    @staticmethod
    def create_executor(db: Session, study: Study, widget_def: WidgetDefinition):
        """Create executor - always returns SimpleWidgetExecutor for now"""
        return SimpleWidgetExecutor(db, study, widget_def)