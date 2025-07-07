# Troubleshooting Guide

## Overview

This comprehensive troubleshooting guide helps developers and system administrators diagnose and resolve common issues with the Clinical Dashboard Platform. It covers frontend, backend, database, deployment, and performance-related problems.

## Table of Contents

1. [General Troubleshooting Approach](#general-troubleshooting-approach)
2. [Frontend Issues](#frontend-issues)
3. [Backend API Issues](#backend-api-issues)
4. [Database Issues](#database-issues)
5. [Authentication and Authorization](#authentication-and-authorization)
6. [Widget and Dashboard Issues](#widget-and-dashboard-issues)
7. [Data Pipeline Issues](#data-pipeline-issues)
8. [Performance Issues](#performance-issues)
9. [Deployment Issues](#deployment-issues)
10. [Infrastructure Issues](#infrastructure-issues)
11. [Monitoring and Logging](#monitoring-and-logging)
12. [Emergency Procedures](#emergency-procedures)

## General Troubleshooting Approach

### Systematic Diagnosis Process

1. **Identify the Scope**
   - Is it affecting all users or specific users?
   - Is it environment-specific (dev/staging/prod)?
   - When did the issue start?

2. **Gather Information**
   - Error messages and stack traces
   - User actions that trigger the issue
   - System logs and metrics
   - Recent changes or deployments

3. **Reproduce the Issue**
   - Create minimal reproduction steps
   - Test in different environments
   - Document exact conditions

4. **Analyze Root Cause**
   - Check logs systematically
   - Review recent changes
   - Analyze system metrics
   - Test hypotheses

5. **Implement and Verify Fix**
   - Test fix in staging first
   - Monitor after deployment
   - Document solution

### Essential Debugging Tools

```bash
# Log aggregation
kubectl logs -f deployment/backend -n cortex-dash
docker-compose logs -f backend

# System monitoring
htop
iotop
netstat -tulpn

# Database debugging
psql -c "SELECT * FROM pg_stat_activity;"
redis-cli monitor

# Network debugging
curl -v http://api.cortexdash.com/health
nslookup api.cortexdash.com
ping api.cortexdash.com

# Container debugging
docker exec -it <container> /bin/bash
kubectl exec -it <pod> -- /bin/bash
```

### Log Analysis Commands

```bash
# Search for errors in logs
grep -i error /var/log/cortex/*.log
journalctl -u cortex-backend -f

# Analyze API response times
awk '$7 > 1000 {print $0}' /var/log/nginx/access.log

# Find memory issues
dmesg | grep -i "killed process"
grep "out of memory" /var/log/syslog

# Database connection issues
grep "connection" /var/log/postgresql/postgresql.log
```

## Frontend Issues

### Common React/Next.js Issues

#### Issue: White Screen of Death
**Symptoms**: Frontend loads but shows blank page

**Diagnosis Steps**:
```bash
# Check browser console for JavaScript errors
# Open Developer Tools > Console

# Check if API is accessible
curl http://localhost:8000/api/v1/health

# Verify environment variables
echo $NEXT_PUBLIC_API_URL

# Check build output
npm run build
```

**Common Causes & Solutions**:

1. **Missing Environment Variables**
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

2. **JavaScript Errors**
```typescript
// Add error boundary
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <h1>Something went wrong.</h1>;
    }
    return this.props.children;
  }
}
```

3. **Build Issues**
```bash
# Clear Next.js cache
rm -rf .next
npm run build

# Check TypeScript errors
npm run type-check
```

#### Issue: Slow Page Loading
**Symptoms**: Pages take a long time to load

**Diagnosis**:
```bash
# Analyze bundle size
npm run analyze

# Check network requests in DevTools
# Open Network tab and reload page

# Monitor React performance
# Install React DevTools Profiler
```

**Solutions**:
```typescript
// Code splitting
const LazyComponent = dynamic(() => import('./Component'), {
  loading: () => <Spinner />,
  ssr: false
});

// Optimize images
import Image from 'next/image';

// Memoize expensive computations
const memoizedValue = useMemo(() => {
  return expensiveCalculation(props);
}, [props]);
```

#### Issue: API Connection Errors
**Symptoms**: "Network Error" or failed API calls

**Diagnosis**:
```bash
# Test API directly
curl -X GET http://localhost:8000/api/v1/health

# Check CORS headers
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     http://localhost:8000/api/v1/health
```

**Solutions**:
```typescript
// Add proper error handling
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 10000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Implement retry logic
import { retry } from 'axios-retry';
retry(apiClient, { retries: 3 });
```

### Widget Rendering Issues

#### Issue: Widget Not Displaying Data
**Symptoms**: Widget shows loading state indefinitely

**Diagnosis**:
```typescript
// Add debug logging
const useWidgetData = (widgetId: string) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log('Fetching data for widget:', widgetId);
    
    fetchWidgetData(widgetId)
      .then(data => {
        console.log('Widget data received:', data);
        setData(data);
      })
      .catch(error => {
        console.error('Widget data error:', error);
        setError(error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [widgetId]);

  return { data, loading, error };
};
```

**Common Solutions**:
```typescript
// Check widget configuration
const validateWidgetConfig = (config) => {
  if (!config.dataset) {
    throw new Error('Dataset is required');
  }
  if (!config.field) {
    throw new Error('Field is required');
  }
};

// Add error boundaries for widgets
const WidgetErrorBoundary = ({ children, widgetId }) => {
  return (
    <ErrorBoundary
      fallback={<div>Error loading widget {widgetId}</div>}
      onError={(error) => {
        logError(`Widget ${widgetId} error:`, error);
      }}
    >
      {children}
    </ErrorBoundary>
  );
};
```

## Backend API Issues

### Common FastAPI Issues

#### Issue: Server Won't Start
**Symptoms**: uvicorn fails to start, import errors

**Diagnosis**:
```bash
# Check Python version
python --version

# Verify dependencies
pip list | grep fastapi
pip check

# Test imports
python -c "import app.main"

# Check syntax
python -m py_compile app/main.py
```

**Common Solutions**:
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Fix import paths
export PYTHONPATH=/app:$PYTHONPATH

# Check for circular imports
python -v -c "import app.main" 2>&1 | grep "import"
```

#### Issue: 500 Internal Server Error
**Symptoms**: API returns 500 errors for valid requests

**Diagnosis**:
```python
# Add detailed error logging
import logging
import traceback

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

# Enable debug mode temporarily
app = FastAPI(debug=True)
```

**Check Common Issues**:
```python
# Database connection
try:
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    print("Database connection OK")
except Exception as e:
    print(f"Database error: {e}")

# Environment variables
import os
required_vars = ["DATABASE_URL", "SECRET_KEY", "JWT_SECRET"]
for var in required_vars:
    if not os.getenv(var):
        print(f"Missing environment variable: {var}")
```

#### Issue: High Memory Usage
**Symptoms**: Backend process consuming excessive memory

**Diagnosis**:
```python
# Memory profiling
import psutil
import os

def log_memory_usage():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    print(f"RSS: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS: {memory_info.vms / 1024 / 1024:.2f} MB")

# Add to endpoints for monitoring
@app.middleware("http")
async def log_memory_middleware(request: Request, call_next):
    response = await call_next(request)
    log_memory_usage()
    return response
```

**Solutions**:
```python
# Implement connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600  # Recycle connections every hour
)

# Add garbage collection
import gc

@app.middleware("http")
async def gc_middleware(request: Request, call_next):
    response = await call_next(request)
    # Force garbage collection after each request in debug mode
    if settings.DEBUG:
        gc.collect()
    return response
```

### API Performance Issues

#### Issue: Slow Response Times
**Symptoms**: API endpoints taking >2 seconds to respond

**Diagnosis**:
```python
# Add timing middleware
import time

@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.url} took {process_time:.2f}s")
    
    return response

# Profile database queries
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

**Optimization Solutions**:
```python
# Add database indexes
from alembic import op

def upgrade():
    op.create_index('idx_widgets_dashboard_id', 'widgets', ['dashboard_id'])
    op.create_index('idx_widget_data_widget_id', 'widget_data', ['widget_id'])

# Implement caching
from functools import lru_cache
import redis

redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

@lru_cache(maxsize=128)
def get_widget_config(widget_id: str):
    # Cache widget configurations
    return db.query(Widget).filter(Widget.id == widget_id).first()

# Use async database operations
from sqlalchemy.ext.asyncio import AsyncSession

async def get_dashboard_widgets(db: AsyncSession, dashboard_id: str):
    result = await db.execute(
        select(Widget).where(Widget.dashboard_id == dashboard_id)
    )
    return result.scalars().all()
```

## Database Issues

### PostgreSQL Connection Issues

#### Issue: "Too Many Connections"
**Symptoms**: `FATAL: too many connections for database`

**Diagnosis**:
```sql
-- Check current connections
SELECT count(*) FROM pg_stat_activity;

-- Show connection limits
SHOW max_connections;

-- Check connections by database
SELECT datname, count(*) 
FROM pg_stat_activity 
GROUP BY datname;

-- Find long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
```

**Solutions**:
```sql
-- Increase connection limit (postgresql.conf)
max_connections = 200

-- Kill long-running connections
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'cortex_dash' 
AND state = 'idle' 
AND state_change < now() - interval '1 hour';
```

```python
# Fix connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,           # Reduce pool size
    max_overflow=10,       # Limit overflow
    pool_timeout=30,       # Add timeout
    pool_recycle=1800,     # Recycle connections
    pool_pre_ping=True     # Validate connections
)

# Properly close sessions
from contextlib import contextmanager

@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

#### Issue: Slow Query Performance
**Symptoms**: Database queries taking >1 second

**Diagnosis**:
```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
SELECT pg_reload_conf();

-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE schemaname = 'public' 
ORDER BY n_distinct DESC;

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM widgets WHERE dashboard_id = 'uuid';

-- Check table statistics
SELECT tablename, n_tup_ins, n_tup_upd, n_tup_del 
FROM pg_stat_user_tables 
WHERE schemaname = 'public';
```

**Solutions**:
```sql
-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_widgets_dashboard_id ON widgets(dashboard_id);
CREATE INDEX CONCURRENTLY idx_widget_data_created_at ON widget_data(created_at);
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- Update table statistics
ANALYZE widgets;
ANALYZE widget_data;

-- Optimize queries
-- Before: Full table scan
SELECT * FROM widget_data WHERE widget_id IN (SELECT id FROM widgets WHERE dashboard_id = $1);

-- After: Optimized with joins
SELECT wd.* 
FROM widget_data wd 
JOIN widgets w ON wd.widget_id = w.id 
WHERE w.dashboard_id = $1;
```

### Database Migration Issues

#### Issue: Migration Fails
**Symptoms**: Alembic migration errors

**Diagnosis**:
```bash
# Check migration status
alembic current
alembic history

# Validate migration
alembic check

# Test migration on copy
pg_dump cortex_dash > backup.sql
createdb cortex_dash_test
psql cortex_dash_test < backup.sql
alembic -x database_url=postgresql://user:pass@localhost/cortex_dash_test upgrade head
```

**Solutions**:
```python
# Fix migration conflicts
# In alembic revision file
def upgrade():
    # Check if column exists before adding
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('widgets')]
    
    if 'new_column' not in columns:
        op.add_column('widgets', sa.Column('new_column', sa.String(255)))

# Handle data migrations safely
def upgrade():
    # Create new table first
    op.create_table('new_widgets', ...)
    
    # Migrate data
    conn = op.get_bind()
    conn.execute(text("""
        INSERT INTO new_widgets (id, name, config)
        SELECT id, name, config::text 
        FROM old_widgets
    """))
    
    # Drop old table
    op.drop_table('old_widgets')
    
    # Rename new table
    op.rename_table('new_widgets', 'widgets')
```

## Authentication and Authorization

### JWT Token Issues

#### Issue: "Token has expired"
**Symptoms**: Users getting logged out frequently

**Diagnosis**:
```python
# Check token expiration
import jwt
from datetime import datetime

def decode_token_debug(token: str):
    try:
        # Decode without verification to see contents
        payload = jwt.decode(token, options={"verify_signature": False})
        exp = datetime.fromtimestamp(payload.get('exp', 0))
        print(f"Token expires at: {exp}")
        print(f"Current time: {datetime.now()}")
        print(f"Is expired: {exp < datetime.now()}")
        return payload
    except Exception as e:
        print(f"Token decode error: {e}")

# Check token in API
@app.middleware("http")
async def token_debug_middleware(request: Request, call_next):
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        decode_token_debug(token)
    
    response = await call_next(request)
    return response
```

**Solutions**:
```python
# Extend token lifetime
from datetime import timedelta

ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Increase from 30 to 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Implement automatic token refresh
@app.middleware("http")
async def auto_refresh_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Check if token is close to expiration
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            exp = payload.get('exp')
            if exp and exp - time.time() < 300:  # Less than 5 minutes
                # Refresh token
                new_token = create_access_token(data={"sub": payload.get("sub")})
                response.headers["X-New-Token"] = new_token
        except jwt.ExpiredSignatureError:
            pass
    
    return response
```

#### Issue: Permission Denied
**Symptoms**: Users can't access resources they should have access to

**Diagnosis**:
```python
# Debug permission checking
def debug_permissions(user_id: str, resource: str, action: str):
    user = get_user(user_id)
    permissions = get_user_permissions(user)
    
    print(f"User: {user.email}")
    print(f"Roles: {[role.name for role in user.roles]}")
    print(f"Permissions: {[p.name for p in permissions]}")
    print(f"Required: {resource}:{action}")
    
    has_permission = check_permission(user, resource, action)
    print(f"Has permission: {has_permission}")
    
    return has_permission

# Add to permission decorator
def require_permission_debug(resource: str, action: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = get_current_user()  # Get from dependency
            
            if not debug_permissions(current_user.id, resource, action):
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions for {resource}:{action}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

**Solutions**:
```python
# Fix role-based access control
class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    resource = Column(String, nullable=False)
    action = Column(String, nullable=False)

class UserRole(Base):
    __tablename__ = "user_roles"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)

def check_permission(user: User, resource: str, action: str) -> bool:
    # Check direct permissions
    for role in user.roles:
        for permission in role.permissions:
            if permission.resource == resource and permission.action == action:
                return True
    
    # Check wildcard permissions
    for role in user.roles:
        for permission in role.permissions:
            if permission.resource == "*" or permission.action == "*":
                return True
    
    return False
```

## Widget and Dashboard Issues

### Widget Configuration Problems

#### Issue: Widget Shows "No Data Available"
**Symptoms**: Widget configured correctly but shows no data

**Diagnosis**:
```python
# Debug widget data pipeline
async def debug_widget_data(widget_id: str, config: dict):
    print(f"Debugging widget: {widget_id}")
    print(f"Configuration: {config}")
    
    # Check data source
    dataset = config.get('dataset')
    if not dataset:
        print("ERROR: No dataset specified")
        return
    
    # Test data source connection
    try:
        data_source = get_data_source(dataset)
        print(f"Data source found: {data_source.name}")
        
        # Test query
        query_builder = QueryBuilder(config)
        sql_query = query_builder.build()
        print(f"Generated SQL: {sql_query}")
        
        # Execute query
        result = await execute_query(sql_query)
        print(f"Query result count: {len(result) if result else 0}")
        
        if result:
            print(f"Sample data: {result[:3]}")
        
    except Exception as e:
        print(f"Error in data pipeline: {e}")
        import traceback
        traceback.print_exc()

# Add debug endpoint
@app.post("/debug/widget-data")
async def debug_widget_endpoint(
    widget_id: str,
    config: dict,
    current_user: User = Depends(get_current_user)
):
    await debug_widget_data(widget_id, config)
    return {"status": "debug_complete"}
```

**Common Solutions**:
```python
# Validate widget configuration
def validate_widget_config(widget_type: str, config: dict):
    validators = {
        'metric': validate_metric_config,
        'chart': validate_chart_config,
        'table': validate_table_config,
    }
    
    validator = validators.get(widget_type)
    if not validator:
        raise ValueError(f"Unknown widget type: {widget_type}")
    
    return validator(config)

def validate_metric_config(config: dict):
    required_fields = ['dataset', 'metric_type']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate dataset exists
    if not dataset_exists(config['dataset']):
        raise ValueError(f"Dataset not found: {config['dataset']}")
    
    return True

# Fix data source mapping
class DataSourceMapper:
    def __init__(self):
        self.source_map = {
            'ADSL': 'subject_level_data',
            'ADAE': 'adverse_events',
            'LB': 'laboratory_data',
        }
    
    def get_table_name(self, dataset: str) -> str:
        return self.source_map.get(dataset, dataset.lower())
    
    def build_query(self, config: dict) -> str:
        table_name = self.get_table_name(config['dataset'])
        
        query = f"SELECT * FROM {table_name}"
        
        # Add filters
        filters = config.get('filters', [])
        if filters:
            where_clauses = []
            for f in filters:
                where_clauses.append(f"{f['field']} {f['operator']} %s")
            query += " WHERE " + " AND ".join(where_clauses)
        
        return query
```

### Dashboard Layout Issues

#### Issue: Widget Overlap or Incorrect Positioning
**Symptoms**: Widgets overlapping or not positioned correctly

**Diagnosis**:
```typescript
// Debug layout configuration
const debugLayout = (layout: Layout[]) => {
  console.log('Layout configuration:', layout);
  
  // Check for overlaps
  const overlaps = findOverlaps(layout);
  if (overlaps.length > 0) {
    console.warn('Layout overlaps detected:', overlaps);
  }
  
  // Check boundaries
  const outOfBounds = layout.filter(item => 
    item.x < 0 || item.y < 0 || 
    item.x + item.w > 12 || // Assuming 12-column grid
    item.y + item.h > 20
  );
  
  if (outOfBounds.length > 0) {
    console.warn('Widgets out of bounds:', outOfBounds);
  }
};

const findOverlaps = (layout: Layout[]): string[] => {
  const overlaps = [];
  
  for (let i = 0; i < layout.length; i++) {
    for (let j = i + 1; j < layout.length; j++) {
      const a = layout[i];
      const b = layout[j];
      
      if (!(a.x + a.w <= b.x || b.x + b.w <= a.x || 
            a.y + a.h <= b.y || b.y + b.h <= a.y)) {
        overlaps.push(`${a.i} overlaps with ${b.i}`);
      }
    }
  }
  
  return overlaps;
};
```

**Solutions**:
```typescript
// Auto-fix layout issues
const fixLayoutIssues = (layout: Layout[]): Layout[] => {
  const fixed = [...layout];
  
  // Sort by position (top to bottom, left to right)
  fixed.sort((a, b) => a.y - b.y || a.x - b.x);
  
  // Fix overlaps by moving conflicting widgets
  for (let i = 0; i < fixed.length; i++) {
    const current = fixed[i];
    
    // Check against all previous widgets
    for (let j = 0; j < i; j++) {
      const existing = fixed[j];
      
      if (isOverlapping(current, existing)) {
        // Move current widget below the existing one
        current.y = existing.y + existing.h;
      }
    }
    
    // Ensure widget is within bounds
    if (current.x + current.w > 12) {
      current.x = 12 - current.w;
    }
    if (current.x < 0) {
      current.x = 0;
    }
  }
  
  return fixed;
};

// Implement responsive layout
const useResponsiveLayout = (layout: Layout[]) => {
  const [currentLayout, setCurrentLayout] = useState(layout);
  
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      
      if (width < 768) {
        // Mobile: stack all widgets
        const mobileLayout = layout.map((item, index) => ({
          ...item,
          x: 0,
          y: index * item.h,
          w: 12,
        }));
        setCurrentLayout(mobileLayout);
      } else if (width < 1024) {
        // Tablet: 2-column layout
        const tabletLayout = layout.map((item, index) => ({
          ...item,
          x: (index % 2) * 6,
          y: Math.floor(index / 2) * item.h,
          w: 6,
        }));
        setCurrentLayout(tabletLayout);
      } else {
        // Desktop: original layout
        setCurrentLayout(layout);
      }
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [layout]);
  
  return currentLayout;
};
```

## Data Pipeline Issues

### ETL Pipeline Failures

#### Issue: Pipeline Jobs Failing
**Symptoms**: Celery tasks failing, data not updating

**Diagnosis**:
```python
# Check Celery worker status
from celery import current_app

def check_celery_health():
    try:
        # Check if workers are responding
        stats = current_app.control.inspect().stats()
        if not stats:
            print("No Celery workers found")
            return False
        
        # Check worker details
        for worker, details in stats.items():
            print(f"Worker: {worker}")
            print(f"Pool: {details.get('pool')}")
            print(f"Processes: {details.get('pool', {}).get('processes')}")
        
        return True
    except Exception as e:
        print(f"Celery health check failed: {e}")
        return False

# Debug task execution
@celery_app.task(bind=True)
def debug_task(self, *args, **kwargs):
    try:
        print(f"Task ID: {self.request.id}")
        print(f"Args: {args}")
        print(f"Kwargs: {kwargs}")
        
        # Your task logic here
        result = perform_data_processing(*args, **kwargs)
        
        print(f"Task completed successfully")
        return result
        
    except Exception as e:
        print(f"Task failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60, max_retries=3)
```

**Solutions**:
```python
# Implement robust error handling
from celery.exceptions import Retry
import time

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def robust_data_pipeline_task(self, pipeline_config: dict):
    try:
        # Add logging
        logger = get_logger(__name__)
        logger.info(f"Starting pipeline task: {self.request.id}")
        
        # Validate configuration
        validate_pipeline_config(pipeline_config)
        
        # Execute pipeline steps
        for step in pipeline_config['steps']:
            logger.info(f"Executing step: {step['name']}")
            
            step_start = time.time()
            result = execute_pipeline_step(step)
            step_duration = time.time() - step_start
            
            logger.info(f"Step completed in {step_duration:.2f}s")
            
            # Store intermediate results
            store_step_result(self.request.id, step['name'], result)
        
        logger.info(f"Pipeline task completed: {self.request.id}")
        return {"status": "success", "task_id": self.request.id}
        
    except Exception as e:
        logger.error(f"Pipeline task failed: {e}")
        
        # Clean up resources
        cleanup_pipeline_resources(self.request.id)
        
        # Don't retry certain types of errors
        if isinstance(e, (ValidationError, ConfigurationError)):
            raise e
        
        # Retry for transient errors
        raise self.retry(exc=e, countdown=2 ** self.request.retries)

# Monitor task queues
def monitor_celery_queues():
    inspect = current_app.control.inspect()
    
    # Check queue lengths
    active_queues = inspect.active_queues()
    for worker, queues in active_queues.items():
        for queue in queues:
            length = len(inspect.reserved().get(worker, []))
            if length > 100:  # Alert if queue is too long
                logger.warning(f"Queue {queue['name']} on {worker} has {length} tasks")
    
    # Check for stuck tasks
    active_tasks = inspect.active()
    for worker, tasks in active_tasks.items():
        for task in tasks:
            # Alert if task has been running for more than 1 hour
            if time.time() - task['time_start'] > 3600:
                logger.warning(f"Long-running task: {task['id']} on {worker}")
```

### Data Quality Issues

#### Issue: Inconsistent or Missing Data
**Symptoms**: Widgets showing incorrect or incomplete data

**Diagnosis**:
```python
# Data quality checks
class DataQualityChecker:
    def __init__(self, db_session):
        self.db = db_session
    
    def check_data_completeness(self, dataset: str, required_fields: list):
        """Check for missing required fields"""
        query = f"""
        SELECT 
            {', '.join([f"COUNT(CASE WHEN {field} IS NULL THEN 1 END) as {field}_nulls" for field in required_fields])},
            COUNT(*) as total_records
        FROM {dataset}
        """
        
        result = self.db.execute(text(query)).fetchone()
        
        issues = []
        for field in required_fields:
            null_count = getattr(result, f"{field}_nulls", 0)
            if null_count > 0:
                percentage = (null_count / result.total_records) * 100
                issues.append(f"{field}: {null_count} nulls ({percentage:.1f}%)")
        
        return issues
    
    def check_data_consistency(self, dataset: str):
        """Check for data consistency issues"""
        checks = [
            # Check for duplicate records
            f"SELECT COUNT(*) - COUNT(DISTINCT id) as duplicates FROM {dataset}",
            
            # Check for invalid dates
            f"""SELECT COUNT(*) as invalid_dates 
                FROM {dataset} 
                WHERE created_at > CURRENT_TIMESTAMP""",
            
            # Check for orphaned references
            f"""SELECT COUNT(*) as orphaned 
                FROM {dataset} d 
                LEFT JOIN studies s ON d.study_id = s.id 
                WHERE s.id IS NULL"""
        ]
        
        issues = []
        for check in checks:
            result = self.db.execute(text(check)).fetchone()
            if result[0] > 0:
                issues.append(f"Query: {check}, Issues: {result[0]}")
        
        return issues

# Automated data validation
@celery_app.task
def validate_data_quality():
    checker = DataQualityChecker(SessionLocal())
    
    datasets = ['widgets', 'dashboards', 'widget_data']
    all_issues = {}
    
    for dataset in datasets:
        # Define required fields per dataset
        required_fields = {
            'widgets': ['id', 'title', 'type', 'dashboard_id'],
            'dashboards': ['id', 'title', 'study_id'],
            'widget_data': ['id', 'widget_id', 'data']
        }
        
        # Check completeness
        completeness_issues = checker.check_data_completeness(
            dataset, 
            required_fields[dataset]
        )
        
        # Check consistency
        consistency_issues = checker.check_data_consistency(dataset)
        
        if completeness_issues or consistency_issues:
            all_issues[dataset] = {
                'completeness': completeness_issues,
                'consistency': consistency_issues
            }
    
    # Alert if issues found
    if all_issues:
        send_data_quality_alert(all_issues)
    
    return all_issues
```

## Performance Issues

### Frontend Performance

#### Issue: Slow Dashboard Loading
**Symptoms**: Dashboard takes >5 seconds to load

**Diagnosis**:
```typescript
// Performance monitoring
const usePerformanceMonitoring = () => {
  useEffect(() => {
    // Measure page load time
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    console.log('Page load time:', navigation.loadEventEnd - navigation.loadEventStart);
    
    // Measure component render time
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        console.log(`${entry.name}: ${entry.duration}ms`);
      });
    });
    observer.observe({ entryTypes: ['measure'] });
    
    return () => observer.disconnect();
  }, []);
};

// Measure widget loading time
const useWidgetPerformance = (widgetId: string) => {
  useEffect(() => {
    performance.mark(`widget-${widgetId}-start`);
    
    return () => {
      performance.mark(`widget-${widgetId}-end`);
      performance.measure(
        `widget-${widgetId}-load`,
        `widget-${widgetId}-start`,
        `widget-${widgetId}-end`
      );
    };
  }, [widgetId]);
};
```

**Optimization Solutions**:
```typescript
// Implement virtual scrolling for large lists
import { FixedSizeList as List } from 'react-window';

const VirtualizedWidgetList = ({ widgets }) => {
  const Row = ({ index, style }) => (
    <div style={style}>
      <Widget widget={widgets[index]} />
    </div>
  );

  return (
    <List
      height={600}
      itemCount={widgets.length}
      itemSize={200}
      width="100%"
    >
      {Row}
    </List>
  );
};

// Optimize API calls with debouncing
const useDebouncedWidgetData = (config, delay = 500) => {
  const [debouncedConfig, setDebouncedConfig] = useState(config);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedConfig(config);
    }, delay);

    return () => clearTimeout(timer);
  }, [config, delay]);

  return useWidgetData(debouncedConfig);
};

// Implement progressive loading
const usePaginatedData = (initialPageSize = 20) => {
  const [data, setData] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const loadMore = useCallback(async () => {
    try {
      const newData = await fetchData({ page, limit: initialPageSize });
      setData(prev => [...prev, ...newData.items]);
      setHasMore(newData.hasMore);
      setPage(prev => prev + 1);
    } catch (error) {
      console.error('Error loading more data:', error);
    }
  }, [page, initialPageSize]);

  return { data, loadMore, hasMore };
};
```

### Backend Performance

#### Issue: High CPU Usage
**Symptoms**: Server CPU consistently >80%

**Diagnosis**:
```python
# CPU profiling
import cProfile
import pstats

def profile_endpoint(func):
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        
        result = func(*args, **kwargs)
        
        pr.disable()
        stats = pstats.Stats(pr)
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # Top 10 functions
        
        return result
    return wrapper

# Monitor CPU usage
import psutil
import threading
import time

class CPUMonitor:
    def __init__(self):
        self.monitoring = False
        
    def start_monitoring(self):
        self.monitoring = True
        thread = threading.Thread(target=self._monitor)
        thread.daemon = True
        thread.start()
        
    def _monitor(self):
        while self.monitoring:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > 80:
                logger.warning(f"High CPU usage: {cpu_percent}%")
                
            if memory_percent > 80:
                logger.warning(f"High memory usage: {memory_percent}%")
                
            time.sleep(5)
```

**Optimization Solutions**:
```python
# Implement async processing
import asyncio
from asyncio import Semaphore

# Limit concurrent operations
semaphore = Semaphore(10)

async def process_widget_data_async(widget_configs):
    async def process_single_widget(config):
        async with semaphore:
            return await fetch_widget_data(config)
    
    tasks = [process_single_widget(config) for config in widget_configs]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return results

# Optimize database queries
from sqlalchemy import and_, or_
from sqlalchemy.orm import selectinload, joinedload

def get_dashboard_with_widgets_optimized(db: Session, dashboard_id: str):
    # Use eager loading to avoid N+1 queries
    return db.query(Dashboard)\
        .options(
            selectinload(Dashboard.widgets),
            joinedload(Dashboard.study)
        )\
        .filter(Dashboard.id == dashboard_id)\
        .first()

# Implement connection pooling for external APIs
import aiohttp
from aiohttp import TCPConnector

class APIClient:
    def __init__(self):
        connector = TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=30,  # Per host connection limit
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
        )
        self.session = aiohttp.ClientSession(connector=connector)
    
    async def fetch_data(self, url: str, **kwargs):
        async with self.session.get(url, **kwargs) as response:
            return await response.json()
```

## Deployment Issues

### Container Issues

#### Issue: Container Won't Start
**Symptoms**: Docker container exits immediately

**Diagnosis**:
```bash
# Check container logs
docker logs <container_name>

# Check exit code
docker inspect <container_name> --format='{{.State.ExitCode}}'

# Run container interactively
docker run -it <image_name> /bin/bash

# Check image layers
docker history <image_name>

# Verify environment variables
docker exec <container_name> env
```

**Common Solutions**:
```dockerfile
# Fix common Dockerfile issues

# Ensure non-root user has proper permissions
FROM python:3.11-slim
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /app
COPY --chown=appuser:appuser . .
USER appuser

# Handle missing dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Proper signal handling
FROM node:18-alpine
# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

### Kubernetes Issues

#### Issue: Pods Crashing
**Symptoms**: Pod restarts frequently, CrashLoopBackOff

**Diagnosis**:
```bash
# Check pod status
kubectl get pods -n cortex-dash

# Describe problematic pod
kubectl describe pod <pod_name> -n cortex-dash

# Check pod logs
kubectl logs <pod_name> -n cortex-dash --previous

# Check resource usage
kubectl top pods -n cortex-dash

# Check events
kubectl get events -n cortex-dash --sort-by=.metadata.creationTimestamp
```

**Solutions**:
```yaml
# Fix resource limits and requests
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  template:
    spec:
      containers:
      - name: backend
        image: cortex-dash/backend:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        
        # Add proper health checks
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        
        # Handle graceful shutdown
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]
```

## Infrastructure Issues

### Load Balancer Issues

#### Issue: 502 Bad Gateway
**Symptoms**: Load balancer returns 502 errors

**Diagnosis**:
```bash
# Check backend service health
curl -I http://backend-service:8000/health

# Check nginx logs
tail -f /var/log/nginx/error.log

# Test upstream connectivity
telnet backend-service 8000

# Check nginx configuration
nginx -t
```

**Solutions**:
```nginx
# Fix nginx upstream configuration
upstream backend {
    least_conn;
    server backend-1:8000 max_fails=3 fail_timeout=30s;
    server backend-2:8000 max_fails=3 fail_timeout=30s;
    server backend-3:8000 max_fails=3 fail_timeout=30s;
}

server {
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Increase timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Enable health checks
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
        proxy_next_upstream_tries 3;
        proxy_next_upstream_timeout 30s;
    }
}
```

### SSL/TLS Issues

#### Issue: Certificate Problems
**Symptoms**: SSL certificate errors, browser warnings

**Diagnosis**:
```bash
# Check certificate expiration
openssl x509 -in certificate.crt -text -noout | grep "Not After"

# Test SSL connection
openssl s_client -connect cortexdash.com:443

# Check certificate chain
curl -vvI https://cortexdash.com

# Verify certificate with CA
openssl verify -CAfile ca-bundle.crt certificate.crt
```

**Solutions**:
```bash
# Renew Let's Encrypt certificates
certbot renew --dry-run
certbot renew

# Update certificate in Kubernetes
kubectl create secret tls cortex-tls \
  --cert=certificate.crt \
  --key=private.key \
  -n cortex-dash

# Configure automatic renewal
# Add to crontab
0 2 * * * certbot renew --quiet && systemctl reload nginx
```

## Monitoring and Logging

### Log Analysis

#### Issue: Unable to Find Error Source
**Symptoms**: Errors occurring but difficult to trace

**Enhanced Logging Setup**:
```python
# Structured logging configuration
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'widget_id'):
            log_entry['widget_id'] = record.widget_id
            
        return json.dumps(log_entry)

# Add request tracking middleware
import uuid

@app.middleware("http")
async def request_tracking_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Add to logging context
    logger = logging.getLogger(__name__)
    logger = logging.LoggerAdapter(logger, {'request_id': request_id})
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        "Request completed",
        extra={
            'method': request.method,
            'url': str(request.url),
            'status_code': response.status_code,
            'process_time': process_time,
        }
    )
    
    return response
```

### Centralized Logging

```yaml
# ELK Stack configuration for centralized logging
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

## Emergency Procedures

### Incident Response

#### Critical System Down
```bash
#!/bin/bash
# emergency-response.sh

echo "Starting emergency response procedure..."

# 1. Assess the situation
echo "Checking system status..."
kubectl get pods -n cortex-dash
curl -I https://cortexdash.com/health

# 2. Scale up resources
echo "Scaling up resources..."
kubectl scale deployment backend --replicas=10 -n cortex-dash
kubectl scale deployment frontend --replicas=6 -n cortex-dash

# 3. Check recent deployments
echo "Checking recent deployments..."
kubectl rollout history deployment/backend -n cortex-dash

# 4. Rollback if necessary
read -p "Rollback to previous version? (y/n): " rollback
if [ "$rollback" = "y" ]; then
    kubectl rollout undo deployment/backend -n cortex-dash
    kubectl rollout undo deployment/frontend -n cortex-dash
fi

# 5. Monitor recovery
echo "Monitoring recovery..."
kubectl get pods -n cortex-dash -w
```

#### Database Recovery
```bash
#!/bin/bash
# database-recovery.sh

echo "Starting database recovery procedure..."

# 1. Stop application to prevent further damage
kubectl scale deployment backend --replicas=0 -n cortex-dash

# 2. Create backup of current state
pg_dump cortex_dash > emergency_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Restore from latest backup
read -p "Enter backup file to restore from: " backup_file
if [ -f "$backup_file" ]; then
    dropdb cortex_dash
    createdb cortex_dash
    psql cortex_dash < "$backup_file"
    echo "Database restored from $backup_file"
else
    echo "Backup file not found: $backup_file"
    exit 1
fi

# 4. Run database migrations
kubectl run migration-job --image=cortex-dash/backend:latest --restart=Never -- alembic upgrade head

# 5. Restart application
kubectl scale deployment backend --replicas=3 -n cortex-dash

echo "Database recovery completed"
```

### Disaster Recovery Checklist

1. **Immediate Response (0-15 minutes)**
   - [ ] Assess impact and affected systems
   - [ ] Notify stakeholders
   - [ ] Scale up healthy resources
   - [ ] Check monitoring dashboards

2. **Short-term Stabilization (15-60 minutes)**
   - [ ] Identify root cause
   - [ ] Implement temporary fixes
   - [ ] Monitor system recovery
   - [ ] Document actions taken

3. **Recovery and Testing (1-4 hours)**
   - [ ] Implement permanent fix
   - [ ] Test all functionality
   - [ ] Verify data integrity
   - [ ] Update monitoring

4. **Post-Incident (4+ hours)**
   - [ ] Conduct post-mortem
   - [ ] Update runbooks
   - [ ] Implement preventive measures
   - [ ] Communicate resolution

---

## Quick Reference

### Common Commands
```bash
# Health checks
curl http://localhost:8000/health
kubectl get pods -n cortex-dash

# Log analysis
kubectl logs -f deployment/backend -n cortex-dash | grep ERROR
docker-compose logs backend | tail -100

# Performance monitoring
kubectl top pods -n cortex-dash
docker stats

# Database debugging
psql -c "SELECT * FROM pg_stat_activity;"
redis-cli monitor
```

### Emergency Contacts
- **Platform Team**: platform-team@sagarmatha.ai
- **Infrastructure**: infra-team@sagarmatha.ai
- **Security Team**: security@sagarmatha.ai
- **On-call Engineer**: +1-555-ONCALL

### Critical URLs
- **Production Monitoring**: https://monitoring.cortexdash.com
- **Status Page**: https://status.cortexdash.com
- **Documentation**: https://docs.cortexdash.com
- **Issue Tracker**: https://github.com/sagarmatha-ai/cortex-dash/issues

---

*This troubleshooting guide provides systematic approaches to common issues. For emergency situations, follow the incident response procedures and contact the appropriate support teams immediately.*