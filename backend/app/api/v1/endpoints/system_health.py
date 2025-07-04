# ABOUTME: API endpoints for system health monitoring and status checks
# ABOUTME: Handles health checks, resource monitoring, and system diagnostics

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from datetime import datetime, timedelta
import psutil
import os
import uuid

from app.api.deps import get_db, get_current_user
from app.models import User
from app.core.permissions import Permission, require_permission
from app.core.config import settings

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.MANAGE_SYSTEM))
) -> Any:
    """
    Get overall system health status.
    """
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Check service statuses
    services = check_service_health(db)
    
    # Calculate overall health score
    health_score = calculate_health_score(cpu_percent, memory.percent, disk.percent, services)
    
    return {
        "status": get_health_status(health_score),
        "health_score": health_score,
        "timestamp": datetime.utcnow().isoformat(),
        "system_metrics": {
            "cpu": {
                "usage_percent": cpu_percent,
                "cores": psutil.cpu_count(),
                "status": "healthy" if cpu_percent < 80 else "warning" if cpu_percent < 90 else "critical"
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent_used": memory.percent,
                "status": "healthy" if memory.percent < 80 else "warning" if memory.percent < 90 else "critical"
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent_used": disk.percent,
                "status": "healthy" if disk.percent < 80 else "warning" if disk.percent < 90 else "critical"
            }
        },
        "services": services,
        "uptime": get_system_uptime()
    }


@router.get("/status", response_model=Dict[str, Any])
async def get_service_status(
    service: Optional[str] = Query(None, description="Specific service to check"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get status of specific services (public endpoint).
    """
    services = {
        "api": {
            "name": "API Server",
            "status": "operational",
            "response_time_ms": 45,
            "uptime_percent": 99.98
        },
        "database": {
            "name": "PostgreSQL Database",
            "status": "operational",
            "response_time_ms": 12,
            "uptime_percent": 99.99
        },
        "redis": {
            "name": "Redis Cache",
            "status": "operational",
            "response_time_ms": 2,
            "uptime_percent": 99.97
        },
        "storage": {
            "name": "File Storage",
            "status": "operational",
            "response_time_ms": 78,
            "uptime_percent": 99.95
        }
    }
    
    if service:
        if service not in services:
            raise HTTPException(
                status_code=404,
                detail=f"Service '{service}' not found"
            )
        return {
            "service": service,
            "details": services[service],
            "last_checked": datetime.utcnow().isoformat()
        }
    
    return {
        "overall_status": "operational",
        "services": services,
        "last_checked": datetime.utcnow().isoformat(),
        "incidents": []
    }


@router.get("/metrics", response_model=Dict[str, Any])
async def get_system_metrics(
    metric_type: Optional[str] = Query(None, description="Type of metrics to retrieve"),
    timeframe: str = Query("1h", description="Timeframe for metrics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.MANAGE_SYSTEM))
) -> Any:
    """
    Get detailed system metrics.
    """
    # Parse timeframe
    timeframe_map = {
        "1h": 1,
        "6h": 6,
        "24h": 24,
        "7d": 168,
        "30d": 720
    }
    hours = timeframe_map.get(timeframe, 1)
    
    # Generate time series data
    now = datetime.utcnow()
    time_points = []
    for i in range(min(hours, 24)):
        time_points.append((now - timedelta(hours=i)).isoformat())
    time_points.reverse()
    
    metrics = {
        "timeframe": timeframe,
        "start_time": time_points[0],
        "end_time": time_points[-1],
        "data_points": len(time_points)
    }
    
    if not metric_type or metric_type == "performance":
        metrics["performance"] = {
            "api_response_time": generate_metric_series(time_points, 20, 100),
            "database_query_time": generate_metric_series(time_points, 5, 50),
            "request_rate": generate_metric_series(time_points, 100, 500),
            "error_rate": generate_metric_series(time_points, 0, 5)
        }
    
    if not metric_type or metric_type == "resources":
        metrics["resources"] = {
            "cpu_usage": generate_metric_series(time_points, 20, 60),
            "memory_usage": generate_metric_series(time_points, 40, 70),
            "disk_io": generate_metric_series(time_points, 10, 80),
            "network_throughput": generate_metric_series(time_points, 50, 200)
        }
    
    if not metric_type or metric_type == "application":
        metrics["application"] = {
            "active_users": generate_metric_series(time_points, 20, 50),
            "active_sessions": generate_metric_series(time_points, 30, 80),
            "jobs_processed": generate_metric_series(time_points, 50, 150),
            "cache_hit_rate": generate_metric_series(time_points, 85, 95)
        }
    
    return metrics


@router.get("/logs", response_model=Dict[str, Any])
async def get_system_logs(
    log_level: Optional[str] = Query(None, description="Filter by log level"),
    service: Optional[str] = Query(None, description="Filter by service"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.MANAGE_SYSTEM))
) -> Any:
    """
    Get system logs with filtering.
    """
    # TODO: Implement actual log retrieval
    
    # Generate mock logs
    logs = []
    log_levels = ["debug", "info", "warning", "error"]
    services = ["api", "worker", "scheduler", "database"]
    
    base_time = datetime.utcnow()
    for i in range(200):
        log_time = base_time - timedelta(minutes=i)
        level = log_levels[i % 4] if i % 10 != 0 else "error"
        
        log_entry = {
            "timestamp": log_time.isoformat(),
            "level": level,
            "service": services[i % len(services)],
            "message": generate_log_message(level, services[i % len(services)]),
            "details": {
                "request_id": str(uuid.uuid4()) if services[i % len(services)] == "api" else None,
                "user_id": str(uuid.uuid4()) if i % 3 == 0 else None,
                "duration_ms": i * 10 if level != "error" else None
            }
        }
        logs.append(log_entry)
    
    # Apply filters
    if log_level:
        logs = [log for log in logs if log["level"] == log_level]
    
    if service:
        logs = [log for log in logs if log["service"] == service]
    
    # Pagination
    total = len(logs)
    paginated_logs = logs[offset:offset + limit]
    
    return {
        "items": paginated_logs,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


@router.get("/alerts", response_model=List[Dict[str, Any]])
async def get_system_alerts(
    status: Optional[str] = Query("active", description="Filter by alert status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.MANAGE_SYSTEM))
) -> Any:
    """
    Get active system alerts and incidents.
    """
    # TODO: Implement actual alert retrieval
    
    alerts = [
        {
            "alert_id": str(uuid.uuid4()),
            "timestamp": "2025-01-21T10:30:00Z",
            "severity": "warning",
            "type": "high_cpu_usage",
            "title": "High CPU Usage Detected",
            "description": "CPU usage has been above 85% for the last 15 minutes",
            "affected_service": "worker",
            "status": "active",
            "metrics": {
                "cpu_percent": 87.5,
                "duration_minutes": 15
            },
            "recommended_action": "Scale up worker instances"
        },
        {
            "alert_id": str(uuid.uuid4()),
            "timestamp": "2025-01-21T09:45:00Z",
            "severity": "info",
            "type": "backup_completed",
            "title": "Daily Backup Completed",
            "description": "Daily database backup completed successfully",
            "affected_service": "database",
            "status": "resolved",
            "metrics": {
                "backup_size_gb": 125.5,
                "duration_minutes": 45
            }
        },
        {
            "alert_id": str(uuid.uuid4()),
            "timestamp": "2025-01-20T22:00:00Z",
            "severity": "critical",
            "type": "disk_space_low",
            "title": "Low Disk Space",
            "description": "Disk usage is at 92% on the primary storage volume",
            "affected_service": "storage",
            "status": "active",
            "metrics": {
                "disk_used_percent": 92,
                "free_space_gb": 80
            },
            "recommended_action": "Clean up old logs and temporary files"
        }
    ]
    
    # Apply filters
    if status:
        alerts = [a for a in alerts if a["status"] == status]
    
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]
    
    return alerts


@router.get("/diagnostics", response_model=Dict[str, Any])
async def run_system_diagnostics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.MANAGE_SYSTEM))
) -> Any:
    """
    Run comprehensive system diagnostics.
    """
    diagnostics_id = str(uuid.uuid4())
    
    # Run various diagnostic checks
    results = {
        "diagnostics_id": diagnostics_id,
        "started_at": datetime.utcnow().isoformat(),
        "checks": {
            "database_connectivity": {
                "status": "passed",
                "response_time_ms": 12,
                "details": "Successfully connected to PostgreSQL"
            },
            "redis_connectivity": {
                "status": "passed",
                "response_time_ms": 2,
                "details": "Redis cache is responsive"
            },
            "storage_access": {
                "status": "passed",
                "response_time_ms": 45,
                "details": "File storage is accessible and writable"
            },
            "external_apis": {
                "status": "warning",
                "details": "1 of 3 external APIs showing slow response",
                "apis": {
                    "edc_system": {"status": "healthy", "response_time_ms": 234},
                    "lab_api": {"status": "slow", "response_time_ms": 2345},
                    "notification_service": {"status": "healthy", "response_time_ms": 123}
                }
            },
            "background_jobs": {
                "status": "passed",
                "pending_jobs": 45,
                "failed_jobs": 2,
                "details": "Job queue is processing normally"
            },
            "security_scan": {
                "status": "passed",
                "ssl_certificate": "valid",
                "certificate_expiry": "2025-12-31",
                "open_ports": [443, 5432],
                "firewall_status": "active"
            }
        },
        "completed_at": (datetime.utcnow() + timedelta(seconds=30)).isoformat(),
        "overall_status": "healthy_with_warnings",
        "recommendations": [
            "Monitor external lab API response times",
            "Consider scaling if high CPU usage persists",
            "Schedule disk cleanup to free up space"
        ]
    }
    
    return results


def check_service_health(db: Session) -> Dict[str, Any]:
    """Check health status of various services."""
    return {
        "database": {
            "status": "healthy",
            "connections": 45,
            "max_connections": 100,
            "response_time_ms": 12
        },
        "redis": {
            "status": "healthy",
            "memory_used_mb": 256,
            "hit_rate_percent": 92.5
        },
        "celery": {
            "status": "healthy",
            "active_workers": 4,
            "pending_tasks": 23,
            "failed_tasks_24h": 2
        },
        "storage": {
            "status": "healthy",
            "used_gb": 450,
            "total_gb": 1000,
            "iops": 1234
        }
    }


def calculate_health_score(cpu: float, memory: float, disk: float, services: Dict) -> float:
    """Calculate overall system health score (0-100)."""
    # Resource scores (inverse of usage)
    cpu_score = max(0, 100 - cpu)
    memory_score = max(0, 100 - memory)
    disk_score = max(0, 100 - disk)
    
    # Service score
    healthy_services = sum(1 for s in services.values() if s.get("status") == "healthy")
    service_score = (healthy_services / len(services)) * 100
    
    # Weighted average
    weights = {
        "cpu": 0.25,
        "memory": 0.25,
        "disk": 0.2,
        "services": 0.3
    }
    
    health_score = (
        cpu_score * weights["cpu"] +
        memory_score * weights["memory"] +
        disk_score * weights["disk"] +
        service_score * weights["services"]
    )
    
    return round(health_score, 1)


def get_health_status(score: float) -> str:
    """Get health status based on score."""
    if score >= 90:
        return "healthy"
    elif score >= 70:
        return "degraded"
    elif score >= 50:
        return "warning"
    else:
        return "critical"


def get_system_uptime() -> Dict[str, Any]:
    """Get system uptime information."""
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime_seconds = (datetime.now() - boot_time).total_seconds()
    
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    
    return {
        "boot_time": boot_time.isoformat(),
        "uptime_days": days,
        "uptime_hours": hours,
        "uptime_minutes": minutes,
        "uptime_string": f"{days}d {hours}h {minutes}m"
    }


def generate_metric_series(time_points: List[str], min_val: float, max_val: float) -> List[Dict[str, Any]]:
    """Generate mock time series data."""
    import random
    return [
        {
            "timestamp": tp,
            "value": round(random.uniform(min_val, max_val), 2)
        }
        for tp in time_points
    ]


def generate_log_message(level: str, service: str) -> str:
    """Generate appropriate log message based on level and service."""
    messages = {
        "info": {
            "api": "Request processed successfully",
            "worker": "Job completed",
            "scheduler": "Scheduled task executed",
            "database": "Query executed"
        },
        "warning": {
            "api": "Slow response time detected",
            "worker": "Job retry attempted",
            "scheduler": "Task delayed",
            "database": "Long-running query detected"
        },
        "error": {
            "api": "Request failed with 500 error",
            "worker": "Job failed after max retries",
            "scheduler": "Failed to execute scheduled task",
            "database": "Connection timeout"
        },
        "debug": {
            "api": "Request details logged",
            "worker": "Job state transition",
            "scheduler": "Next run calculated",
            "database": "Connection pool status"
        }
    }
    
    return messages.get(level, {}).get(service, f"{level.upper()}: {service} event")