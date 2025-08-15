# ABOUTME: Performance monitoring service for tracking system metrics and performance
# ABOUTME: Includes query performance, API latency, resource usage, and alerts

import time
import psutil
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import deque, defaultdict
import logging
import json
from dataclasses import dataclass, asdict
from enum import Enum

from app.core.cache import cache_manager
from app.core.config import settings

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class PerformanceMetric:
    """Performance metric data"""
    name: str
    type: MetricType
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    unit: str = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data["type"] = self.type.value
        data["timestamp"] = self.timestamp.isoformat()
        return data


class PerformanceMonitor:
    """Main performance monitoring service"""
    
    def __init__(self):
        """Initialize performance monitor"""
        self.metrics = defaultdict(deque)
        self.max_history = 1000  # Keep last 1000 metrics per type
        self.thresholds = self._load_thresholds()
        self.alerts = deque(maxlen=100)
        self.is_running = False
        self._monitoring_task = None
        
    def _load_thresholds(self) -> Dict[str, Dict]:
        """Load performance thresholds for alerts"""
        return {
            "api_latency": {"warning": 1000, "critical": 3000},  # ms
            "query_time": {"warning": 500, "critical": 2000},  # ms
            "cpu_usage": {"warning": 70, "critical": 90},  # percentage
            "memory_usage": {"warning": 80, "critical": 95},  # percentage
            "cache_hit_rate": {"warning": 50, "critical": 30},  # percentage (inverse)
            "error_rate": {"warning": 1, "critical": 5},  # percentage
        }
    
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None,
        unit: Optional[str] = None
    ):
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            type=metric_type,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            unit=unit
        )
        
        # Store metric
        self.metrics[name].append(metric)
        
        # Trim history if needed
        if len(self.metrics[name]) > self.max_history:
            self.metrics[name].popleft()
        
        # Check thresholds
        self._check_threshold(metric)
    
    def _check_threshold(self, metric: PerformanceMetric):
        """Check if metric exceeds thresholds and create alerts"""
        if metric.name in self.thresholds:
            thresholds = self.thresholds[metric.name]
            
            if metric.value >= thresholds.get("critical", float('inf')):
                self._create_alert(metric, "critical")
            elif metric.value >= thresholds.get("warning", float('inf')):
                self._create_alert(metric, "warning")
    
    def _create_alert(self, metric: PerformanceMetric, severity: str):
        """Create a performance alert"""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "severity": severity,
            "metric": metric.name,
            "value": metric.value,
            "threshold": self.thresholds[metric.name][severity],
            "message": f"{metric.name} exceeded {severity} threshold: {metric.value} > {self.thresholds[metric.name][severity]}"
        }
        
        self.alerts.append(alert)
        logger.warning(f"Performance alert: {alert['message']}")
    
    def get_metrics(
        self,
        name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """Get performance metrics"""
        if name:
            metrics = self.metrics.get(name, [])
        else:
            metrics = []
            for metric_list in self.metrics.values():
                metrics.extend(metric_list)
        
        # Filter by time range
        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]
        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]
        
        return [m.to_dict() for m in metrics]
    
    def get_alerts(
        self,
        severity: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get recent alerts"""
        alerts = list(self.alerts)
        
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        
        return alerts[-limit:]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {},
            "system": self._get_system_stats(),
            "alerts": {
                "total": len(self.alerts),
                "critical": len([a for a in self.alerts if a["severity"] == "critical"]),
                "warning": len([a for a in self.alerts if a["severity"] == "warning"])
            }
        }
        
        # Calculate summary statistics for each metric
        for name, metrics in self.metrics.items():
            if metrics:
                values = [m.value for m in metrics]
                summary["metrics"][name] = {
                    "current": metrics[-1].value,
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
        
        return summary
    
    def _get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_io": {
                "bytes_sent": psutil.net_io_counters().bytes_sent,
                "bytes_recv": psutil.net_io_counters().bytes_recv
            }
        }
    
    async def start_monitoring(self, interval: int = 60):
        """Start background monitoring task"""
        if self.is_running:
            return
        
        self.is_running = True
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(interval)
        )
    
    async def stop_monitoring(self):
        """Stop background monitoring"""
        self.is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitoring_loop(self, interval: int):
        """Background monitoring loop"""
        while self.is_running:
            try:
                # Record system metrics
                self.record_metric(
                    "cpu_usage",
                    psutil.cpu_percent(interval=1),
                    MetricType.GAUGE,
                    unit="percent"
                )
                
                self.record_metric(
                    "memory_usage",
                    psutil.virtual_memory().percent,
                    MetricType.GAUGE,
                    unit="percent"
                )
                
                # Record cache metrics
                cache_stats = cache_manager.get_stats()
                for namespace, stats in cache_stats.items():
                    if "hit_rate" in stats:
                        self.record_metric(
                            f"cache_hit_rate_{namespace}",
                            stats["hit_rate"],
                            MetricType.GAUGE,
                            tags={"namespace": namespace},
                            unit="percent"
                        )
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)


class APILatencyTracker:
    """Track API endpoint latency"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.active_requests = {}
    
    def start_request(self, request_id: str, endpoint: str, method: str):
        """Start tracking a request"""
        self.active_requests[request_id] = {
            "endpoint": endpoint,
            "method": method,
            "start_time": time.time()
        }
    
    def end_request(self, request_id: str, status_code: int):
        """End tracking a request and record latency"""
        if request_id not in self.active_requests:
            return
        
        request_data = self.active_requests.pop(request_id)
        latency = (time.time() - request_data["start_time"]) * 1000  # Convert to ms
        
        self.monitor.record_metric(
            "api_latency",
            latency,
            MetricType.TIMER,
            tags={
                "endpoint": request_data["endpoint"],
                "method": request_data["method"],
                "status": str(status_code)
            },
            unit="ms"
        )
        
        # Record error rate
        if status_code >= 400:
            self.monitor.record_metric(
                "api_errors",
                1,
                MetricType.COUNTER,
                tags={
                    "endpoint": request_data["endpoint"],
                    "status": str(status_code)
                }
            )


class QueryPerformanceTracker:
    """Track database query performance"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.active_queries = {}
    
    def start_query(self, query_id: str, query: str):
        """Start tracking a query"""
        self.active_queries[query_id] = {
            "query": query[:100],  # Store first 100 chars
            "start_time": time.time()
        }
    
    def end_query(self, query_id: str, rows_affected: int = 0):
        """End tracking a query and record performance"""
        if query_id not in self.active_queries:
            return
        
        query_data = self.active_queries.pop(query_id)
        duration = (time.time() - query_data["start_time"]) * 1000  # Convert to ms
        
        self.monitor.record_metric(
            "query_time",
            duration,
            MetricType.TIMER,
            tags={
                "query": query_data["query"],
                "rows": str(rows_affected)
            },
            unit="ms"
        )


class WidgetPerformanceTracker:
    """Track widget execution performance"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.widget_stats = defaultdict(lambda: {"count": 0, "total_time": 0})
    
    def track_widget_execution(
        self,
        widget_id: str,
        widget_type: str,
        execution_time: float,
        data_size: int
    ):
        """Track widget execution metrics"""
        # Record execution time
        self.monitor.record_metric(
            "widget_execution_time",
            execution_time * 1000,  # Convert to ms
            MetricType.TIMER,
            tags={
                "widget_id": widget_id,
                "widget_type": widget_type
            },
            unit="ms"
        )
        
        # Record data size
        self.monitor.record_metric(
            "widget_data_size",
            data_size,
            MetricType.GAUGE,
            tags={
                "widget_id": widget_id,
                "widget_type": widget_type
            },
            unit="bytes"
        )
        
        # Update statistics
        stats = self.widget_stats[widget_id]
        stats["count"] += 1
        stats["total_time"] += execution_time
        stats["avg_time"] = stats["total_time"] / stats["count"]
        stats["last_execution"] = datetime.utcnow()
    
    def get_widget_stats(self, widget_id: Optional[str] = None) -> Dict:
        """Get widget performance statistics"""
        if widget_id:
            return dict(self.widget_stats.get(widget_id, {}))
        return dict(self.widget_stats)


class ResourceMonitor:
    """Monitor system resource usage"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.process = psutil.Process()
    
    def record_resources(self):
        """Record current resource usage"""
        # Process-specific metrics
        self.monitor.record_metric(
            "process_cpu_percent",
            self.process.cpu_percent(),
            MetricType.GAUGE,
            unit="percent"
        )
        
        memory_info = self.process.memory_info()
        self.monitor.record_metric(
            "process_memory_rss",
            memory_info.rss / 1024 / 1024,  # Convert to MB
            MetricType.GAUGE,
            unit="MB"
        )
        
        # Database connection pool metrics (if available)
        # This would need to be integrated with SQLAlchemy pool
        
        # Redis connection metrics
        if cache_manager.is_connected():
            try:
                info = cache_manager.redis_client.info()
                self.monitor.record_metric(
                    "redis_memory_used",
                    info.get("used_memory", 0) / 1024 / 1024,  # Convert to MB
                    MetricType.GAUGE,
                    unit="MB"
                )
                self.monitor.record_metric(
                    "redis_connected_clients",
                    info.get("connected_clients", 0),
                    MetricType.GAUGE
                )
            except Exception as e:
                logger.error(f"Error getting Redis metrics: {e}")


class PerformanceReporter:
    """Generate performance reports"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
    
    def generate_report(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Generate a performance report for a time period"""
        metrics = self.monitor.get_metrics(
            start_time=start_time,
            end_time=end_time
        )
        
        report = {
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "summary": {},
            "top_slow_queries": [],
            "top_slow_apis": [],
            "alerts": self.monitor.get_alerts(),
            "recommendations": []
        }
        
        # Analyze metrics
        api_latencies = [m for m in metrics if m["name"] == "api_latency"]
        query_times = [m for m in metrics if m["name"] == "query_time"]
        
        # Calculate API statistics
        if api_latencies:
            latency_values = [m["value"] for m in api_latencies]
            report["summary"]["api"] = {
                "avg_latency": sum(latency_values) / len(latency_values),
                "max_latency": max(latency_values),
                "min_latency": min(latency_values),
                "total_requests": len(latency_values)
            }
            
            # Find slow APIs
            slow_apis = defaultdict(list)
            for metric in api_latencies:
                if metric["value"] > 1000:  # > 1 second
                    endpoint = metric.get("tags", {}).get("endpoint", "unknown")
                    slow_apis[endpoint].append(metric["value"])
            
            report["top_slow_apis"] = [
                {
                    "endpoint": endpoint,
                    "avg_latency": sum(latencies) / len(latencies),
                    "count": len(latencies)
                }
                for endpoint, latencies in sorted(
                    slow_apis.items(),
                    key=lambda x: sum(x[1]) / len(x[1]),
                    reverse=True
                )[:10]
            ]
        
        # Calculate query statistics
        if query_times:
            query_values = [m["value"] for m in query_times]
            report["summary"]["database"] = {
                "avg_query_time": sum(query_values) / len(query_values),
                "max_query_time": max(query_values),
                "min_query_time": min(query_values),
                "total_queries": len(query_values)
            }
            
            # Find slow queries
            slow_queries = []
            for metric in query_times:
                if metric["value"] > 500:  # > 500ms
                    slow_queries.append({
                        "query": metric.get("tags", {}).get("query", "unknown"),
                        "time": metric["value"],
                        "timestamp": metric["timestamp"]
                    })
            
            report["top_slow_queries"] = sorted(
                slow_queries,
                key=lambda x: x["time"],
                reverse=True
            )[:10]
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)
        
        return report
    
    def _generate_recommendations(self, report: Dict) -> List[str]:
        """Generate performance recommendations based on report"""
        recommendations = []
        
        # API performance recommendations
        if "api" in report["summary"]:
            if report["summary"]["api"]["avg_latency"] > 500:
                recommendations.append(
                    "Average API latency is high. Consider implementing caching or optimizing database queries."
                )
        
        # Database performance recommendations
        if "database" in report["summary"]:
            if report["summary"]["database"]["avg_query_time"] > 200:
                recommendations.append(
                    "Average query time is high. Review slow queries and consider adding indexes."
                )
        
        # Alert-based recommendations
        critical_alerts = [a for a in report["alerts"] if a["severity"] == "critical"]
        if len(critical_alerts) > 5:
            recommendations.append(
                f"Multiple critical alerts detected ({len(critical_alerts)}). Immediate attention required."
            )
        
        return recommendations


# Global instances
performance_monitor = PerformanceMonitor()
api_tracker = APILatencyTracker(performance_monitor)
query_tracker = QueryPerformanceTracker(performance_monitor)
widget_tracker = WidgetPerformanceTracker(performance_monitor)
resource_monitor = ResourceMonitor(performance_monitor)
performance_reporter = PerformanceReporter(performance_monitor)