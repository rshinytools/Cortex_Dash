# ABOUTME: API endpoints for performance monitoring and metrics
# ABOUTME: Provides access to system performance data, alerts, and reports

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.api.deps import SessionDep, CurrentUser
from app.services.monitoring.performance_monitor import (
    performance_monitor,
    api_tracker,
    query_tracker,
    widget_tracker,
    resource_monitor,
    performance_reporter,
    MetricType
)

router = APIRouter()


class MetricRecord(BaseModel):
    """Request model for recording a metric"""
    name: str
    value: float
    metric_type: str = "gauge"
    tags: Optional[Dict[str, str]] = None
    unit: Optional[str] = None


class PerformanceReport(BaseModel):
    """Response model for performance report"""
    period: Dict[str, str]
    summary: Dict[str, Any]
    top_slow_queries: List[Dict]
    top_slow_apis: List[Dict]
    alerts: List[Dict]
    recommendations: List[str]


@router.get("/metrics")
def get_performance_metrics(
    name: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: CurrentUser = Depends()
) -> List[Dict]:
    """
    Get performance metrics.
    
    Args:
        name: Optional metric name to filter by
        start_time: Start time for filtering
        end_time: End time for filtering
    
    Returns:
        List of performance metrics
    """
    return performance_monitor.get_metrics(name, start_time, end_time)


@router.post("/metrics")
def record_performance_metric(
    metric: MetricRecord,
    current_user: CurrentUser = Depends()
) -> Dict[str, str]:
    """
    Record a custom performance metric.
    
    Args:
        metric: Metric data to record
    
    Returns:
        Success message
    """
    metric_type = MetricType[metric.metric_type.upper()]
    
    performance_monitor.record_metric(
        name=metric.name,
        value=metric.value,
        metric_type=metric_type,
        tags=metric.tags,
        unit=metric.unit
    )
    
    return {"message": "Metric recorded successfully"}


@router.get("/summary")
def get_performance_summary(
    current_user: CurrentUser = Depends()
) -> Dict[str, Any]:
    """
    Get current performance summary.
    
    Returns:
        Performance summary including current metrics and system stats
    """
    # Record current resource usage
    resource_monitor.record_resources()
    
    return performance_monitor.get_summary()


@router.get("/alerts")
def get_performance_alerts(
    severity: Optional[str] = None,
    limit: int = Query(50, le=100),
    current_user: CurrentUser = Depends()
) -> List[Dict]:
    """
    Get recent performance alerts.
    
    Args:
        severity: Optional severity filter (warning/critical)
        limit: Maximum number of alerts to return
    
    Returns:
        List of recent alerts
    """
    return performance_monitor.get_alerts(severity, limit)


@router.get("/report")
def generate_performance_report(
    hours: int = Query(24, description="Number of hours to include in report"),
    current_user: CurrentUser = Depends()
) -> PerformanceReport:
    """
    Generate a performance report for the specified time period.
    
    Args:
        hours: Number of hours to include in the report
    
    Returns:
        Comprehensive performance report
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    report = performance_reporter.generate_report(start_time, end_time)
    
    return PerformanceReport(**report)


@router.get("/widget-stats")
def get_widget_performance_stats(
    widget_id: Optional[str] = None,
    current_user: CurrentUser = Depends()
) -> Dict:
    """
    Get widget performance statistics.
    
    Args:
        widget_id: Optional widget ID to get specific stats
    
    Returns:
        Widget performance statistics
    """
    return widget_tracker.get_widget_stats(widget_id)


@router.get("/cache-stats")
def get_cache_statistics(
    current_user: CurrentUser = Depends()
) -> Dict[str, Any]:
    """
    Get cache performance statistics.
    
    Returns:
        Cache statistics including hit rates and memory usage
    """
    from app.core.cache import cache_manager
    
    stats = cache_manager.get_stats()
    
    # Add cache memory info if available
    if cache_manager.is_connected():
        try:
            info = cache_manager.redis_client.info()
            stats["memory"] = {
                "used": info.get("used_memory_human", "N/A"),
                "peak": info.get("used_memory_peak_human", "N/A"),
                "rss": info.get("used_memory_rss_human", "N/A")
            }
            stats["clients"] = info.get("connected_clients", 0)
            stats["commands_processed": info.get("total_commands_processed", 0)
        except Exception:
            pass
    
    return stats


@router.get("/slow-queries")
def get_slow_queries(
    threshold_ms: float = Query(1000, description="Threshold in milliseconds"),
    limit: int = Query(20, le=100),
    current_user: CurrentUser = Depends()
) -> List[Dict]:
    """
    Get slow database queries.
    
    Args:
        threshold_ms: Minimum query time in milliseconds
        limit: Maximum number of queries to return
    
    Returns:
        List of slow queries with statistics
    """
    from app.services.optimization.query_optimizer import QueryOptimizer
    from app.core.database import engine
    
    optimizer = QueryOptimizer(engine)
    slow_queries = optimizer.get_slow_queries(threshold_ms)
    
    return slow_queries[:limit]


@router.get("/system-health")
def get_system_health(
    current_user: CurrentUser = Depends()
) -> Dict[str, Any]:
    """
    Get current system health status.
    
    Returns:
        System health information including resource usage and service status
    """
    import psutil
    from app.core.cache import cache_manager
    from app.core.database import engine
    
    health = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy",
        "services": {},
        "resources": {}
    }
    
    # Check database connection
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        health["services"]["database"] = "connected"
    except Exception as e:
        health["services"]["database"] = f"error: {str(e)}"
        health["status"] = "degraded"
    
    # Check Redis connection
    if cache_manager.is_connected():
        health["services"]["cache"] = "connected"
    else:
        health["services"]["cache"] = "disconnected"
        health["status"] = "degraded"
    
    # Get resource usage
    health["resources"] = {
        "cpu": {
            "percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count()
        },
        "memory": {
            "percent": psutil.virtual_memory().percent,
            "available_gb": round(psutil.virtual_memory().available / 1024 / 1024 / 1024, 2),
            "total_gb": round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2)
        },
        "disk": {
            "percent": psutil.disk_usage('/').percent,
            "free_gb": round(psutil.disk_usage('/').free / 1024 / 1024 / 1024, 2),
            "total_gb": round(psutil.disk_usage('/').total / 1024 / 1024 / 1024, 2)
        }
    }
    
    # Check for critical conditions
    if health["resources"]["cpu"]["percent"] > 90:
        health["status"] = "critical"
    elif health["resources"]["memory"]["percent"] > 95:
        health["status"] = "critical"
    elif health["resources"]["disk"]["percent"] > 95:
        health["status"] = "critical"
    
    return health


@router.post("/monitoring/start")
async def start_monitoring(
    interval: int = Query(60, description="Monitoring interval in seconds"),
    current_user: CurrentUser = Depends()
) -> Dict[str, str]:
    """
    Start background performance monitoring.
    
    Args:
        interval: Monitoring interval in seconds
    
    Returns:
        Success message
    """
    await performance_monitor.start_monitoring(interval)
    return {"message": "Monitoring started successfully"}


@router.post("/monitoring/stop")
async def stop_monitoring(
    current_user: CurrentUser = Depends()
) -> Dict[str, str]:
    """
    Stop background performance monitoring.
    
    Returns:
        Success message
    """
    await performance_monitor.stop_monitoring()
    return {"message": "Monitoring stopped successfully"}


@router.get("/thresholds")
def get_performance_thresholds(
    current_user: CurrentUser = Depends()
) -> Dict[str, Dict]:
    """
    Get current performance thresholds for alerts.
    
    Returns:
        Dictionary of metric thresholds
    """
    return performance_monitor.thresholds


@router.put("/thresholds/{metric_name}")
def update_performance_threshold(
    metric_name: str,
    warning: Optional[float] = None,
    critical: Optional[float] = None,
    current_user: CurrentUser = Depends()
) -> Dict[str, str]:
    """
    Update performance threshold for a metric.
    
    Args:
        metric_name: Name of the metric
        warning: Warning threshold value
        critical: Critical threshold value
    
    Returns:
        Success message
    """
    if metric_name not in performance_monitor.thresholds:
        raise HTTPException(status_code=404, detail=f"Metric {metric_name} not found")
    
    if warning is not None:
        performance_monitor.thresholds[metric_name]["warning"] = warning
    
    if critical is not None:
        performance_monitor.thresholds[metric_name]["critical"] = critical
    
    return {"message": f"Threshold updated for {metric_name}"}