# ABOUTME: Database optimization utilities for query performance and connection pooling
# ABOUTME: Provides query optimization, caching strategies, and performance monitoring

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import asyncio
import logging
from functools import wraps
import time

from sqlalchemy import event, Engine, text
from sqlalchemy.engine import Engine as SQLAlchemyEngine
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.orm import Query
from prometheus_client import Counter, Histogram, Gauge
import redis

logger = logging.getLogger(__name__)

# Metrics
query_counter = Counter('db_queries_total', 'Total database queries', ['operation', 'table'])
query_duration = Histogram('db_query_duration_seconds', 'Database query duration', ['operation', 'table'])
connection_pool_size = Gauge('db_connection_pool_size', 'Database connection pool size')
connection_pool_checked_out = Gauge('db_connection_pool_checked_out', 'Checked out connections')


class DatabaseOptimizer:
    """Database optimization utilities"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self._query_cache: Dict[str, Any] = {}
        self._slow_query_threshold = 1.0  # seconds
        
    def configure_connection_pool(self, engine: Engine) -> None:
        """Configure optimized connection pooling"""
        # Set pool configuration
        engine.pool._recycle = 3600  # Recycle connections after 1 hour
        engine.pool._timeout = 30    # Connection timeout
        engine.pool._pre_ping = True # Test connections before use
        
        # Monitor pool metrics
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            connection_pool_size.inc()
            
        @event.listens_for(engine, "close")
        def receive_close(dbapi_connection, connection_record):
            connection_pool_size.dec()
            
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            connection_pool_checked_out.inc()
            
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            connection_pool_checked_out.dec()
    
    def add_query_monitoring(self, engine: Engine) -> None:
        """Add query monitoring and slow query logging"""
        
        @event.listens_for(engine, "before_execute")
        def before_execute(conn, clauseelement, multiparams, params, execution_options):
            conn.info['query_start_time'] = time.time()
            conn.info['query'] = str(clauseelement)
            
        @event.listens_for(engine, "after_execute")
        def after_execute(conn, clauseelement, multiparams, params, execution_options, result):
            duration = time.time() - conn.info.get('query_start_time', time.time())
            
            # Extract table name from query (simplified)
            query_str = str(clauseelement)
            table = "unknown"
            if "FROM" in query_str:
                parts = query_str.split("FROM")
                if len(parts) > 1:
                    table = parts[1].split()[0].strip()
            
            # Update metrics
            query_counter.labels(operation="select", table=table).inc()
            query_duration.labels(operation="select", table=table).observe(duration)
            
            # Log slow queries
            if duration > self._slow_query_threshold:
                logger.warning(
                    f"Slow query detected ({duration:.2f}s): {query_str[:200]}..."
                )
    
    def create_indexes_script(self) -> str:
        """Generate SQL script for creating optimized indexes"""
        return """
        -- Performance indexes for widget system
        
        -- Widget data retrieval
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_widget_study_active 
        ON study_dashboards(study_id, is_active) 
        WHERE is_active = true;
        
        -- Dashboard template lookups
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dashboard_code_version 
        ON dashboard_templates(code, version DESC) 
        WHERE is_active = true;
        
        -- Activity log queries
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_activity_log_user_timestamp 
        ON activity_log(user_id, timestamp DESC);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_activity_log_org_timestamp 
        ON activity_log(org_id, timestamp DESC);
        
        -- Data source queries
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_data_source_study_type 
        ON data_source(study_id, source_type) 
        WHERE is_active = true;
        
        -- Widget definition lookups
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_widget_def_category 
        ON widget_definitions(category, is_active) 
        WHERE is_active = true;
        
        -- Study dashboard widget access
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_study_dashboard_widgets 
        ON study_dashboards(study_id, dashboard_template_id) 
        INCLUDE (customizations, data_mappings) 
        WHERE is_active = true;
        
        -- Refresh schedule queries
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_refresh_schedule_next_run 
        ON refresh_schedule(next_run_at) 
        WHERE is_active = true AND next_run_at IS NOT NULL;
        
        -- User organization access
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_org_active 
        ON user_org_association(user_id, org_id) 
        WHERE is_active = true;
        
        -- Analyze tables for query planner
        ANALYZE dashboard_templates;
        ANALYZE study_dashboards;
        ANALYZE widget_definitions;
        ANALYZE activity_log;
        ANALYZE study;
        ANALYZE data_source;
        """
    
    def cached_query(self, cache_key: str, ttl: int = 300):
        """Decorator for caching query results"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Try to get from cache
                if self.redis_client:
                    cached = await self.redis_client.get(cache_key)
                    if cached:
                        return json.loads(cached)
                
                # Execute query
                result = await func(*args, **kwargs)
                
                # Cache result
                if self.redis_client and result is not None:
                    await self.redis_client.setex(
                        cache_key,
                        ttl,
                        json.dumps(result, default=str)
                    )
                
                return result
            return wrapper
        return decorator
    
    def optimize_query_for_dashboard(self, query: Query) -> Query:
        """Optimize a query for dashboard data retrieval"""
        # Add query hints
        query = query.execution_options(
            synchronize_session=False,
            stream_results=True
        )
        
        # Enable statement caching
        query = query.options(
            # Cache the compiled query
            query.enable_eagerloads(False)
        )
        
        return query
    
    def get_query_plan(self, engine: Engine, query: str) -> List[Dict[str, Any]]:
        """Get the execution plan for a query"""
        with engine.connect() as conn:
            result = conn.execute(text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"))
            plan = result.scalar()
            return plan
    
    def vacuum_analyze_tables(self, engine: Engine, tables: List[str]) -> None:
        """Run VACUUM ANALYZE on specified tables"""
        with engine.connect() as conn:
            for table in tables:
                logger.info(f"Running VACUUM ANALYZE on {table}")
                conn.execute(text(f"VACUUM ANALYZE {table}"))
                conn.commit()


# Query optimization patterns
class QueryPatterns:
    """Common query optimization patterns"""
    
    @staticmethod
    def batch_insert_pattern(table_name: str, records: List[Dict[str, Any]]) -> str:
        """Generate optimized batch insert query"""
        if not records:
            return ""
        
        columns = list(records[0].keys())
        values_template = f"({','.join(['%s' for _ in columns])})"
        values_list = []
        
        for record in records:
            values_list.append(values_template % tuple(record.get(col) for col in columns))
        
        return f"""
        INSERT INTO {table_name} ({','.join(columns)})
        VALUES {','.join(values_list)}
        ON CONFLICT DO NOTHING
        """
    
    @staticmethod
    def windowed_query_pattern(base_query: str, window_size: int = 1000) -> str:
        """Generate windowed query for large result sets"""
        return f"""
        WITH windowed AS (
            SELECT *, ROW_NUMBER() OVER (ORDER BY id) as rn
            FROM ({base_query}) base
        )
        SELECT * FROM windowed
        WHERE rn BETWEEN %s AND %s
        """
    
    @staticmethod
    def recursive_hierarchy_pattern(table_name: str, parent_column: str) -> str:
        """Generate recursive CTE for hierarchical data"""
        return f"""
        WITH RECURSIVE hierarchy AS (
            -- Base case: root items
            SELECT * FROM {table_name}
            WHERE {parent_column} IS NULL
            
            UNION ALL
            
            -- Recursive case: children
            SELECT t.* FROM {table_name} t
            INNER JOIN hierarchy h ON t.{parent_column} = h.id
        )
        SELECT * FROM hierarchy
        """


# Connection pool configuration for different environments
def get_pool_config(environment: str) -> Dict[str, Any]:
    """Get connection pool configuration based on environment"""
    configs = {
        "development": {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 3600,
            "pool_pre_ping": True,
        },
        "production": {
            "pool_size": 20,
            "max_overflow": 40,
            "pool_timeout": 30,
            "pool_recycle": 1800,
            "pool_pre_ping": True,
            "pool_use_lifo": True,  # Use LIFO to keep connections warm
        },
        "testing": {
            "poolclass": NullPool,  # No pooling for tests
        }
    }
    return configs.get(environment, configs["development"])