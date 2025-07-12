# Widget Data Caching Strategy

## Overview
Caching strategy to ensure widget performance while maintaining real-time updates when data changes.

## Cache Architecture

### 1. Cache Layers

```
┌─────────────────────────┐
│   Browser Cache (5min)  │ ← Quick repeated views
├─────────────────────────┤
│   Redis Cache (1hr)     │ ← Shared across users
├─────────────────────────┤
│   Parquet Files         │ ← Source of truth
└─────────────────────────┘
```

### 2. Cache Key Structure
```
widget:{study_id}:{widget_instance_id}:{data_version}:{filter_hash}
```

Example:
```
widget:STUDY-001:metric-card-123:2024-01-10-143000:a1b2c3d4
```

## Cache Invalidation Strategy

### Automatic Invalidation Triggers

1. **New Data Upload**
   - When new source data is uploaded
   - All widget caches for that study are invalidated
   - New data_version in cache key ensures fresh data

2. **Widget Configuration Change**
   - When admin changes widget mapping
   - Only that specific widget cache is invalidated

3. **Pipeline Script Execution**
   - When transformation scripts run
   - Invalidate caches for widgets using transformed data

### Cache Flow

```
User requests widget data
         │
         ▼
Check browser cache (5 min)
         │
     Found? ──Yes──→ Return cached data
         │
        No
         │
         ▼
Check Redis cache (1 hr)
         │
     Found? ──Yes──→ Return cached data
         │             Update browser cache
        No
         │
         ▼
Query parquet files
         │
         ▼
Calculate aggregation
         │
         ▼
Store in Redis cache
Store in browser cache
         │
         ▼
Return data to widget
```

## Implementation Details

### Redis Cache Structure

```python
# Cache entry
{
  "key": "widget:STUDY-001:metric-123:2024-01-10-143000:a1b2c3",
  "value": {
    "data": {
      "value": 4332,
      "previousValue": 4250,
      "change": 82,
      "changePercent": 1.93
    },
    "metadata": {
      "calculatedAt": "2024-01-10T14:35:00Z",
      "dataVersion": "2024-01-10-143000",
      "queryTime": 145,  # milliseconds
      "rowsProcessed": 15000
    }
  },
  "ttl": 3600  # 1 hour
}
```

### Data Version Tracking

```python
# Version manifest stored with data
{
  "study_id": "STUDY-001",
  "current_version": {
    "source_data": "2024-01-10-143000",
    "transformed_data": "2024-01-10-145000"
  },
  "previous_version": {
    "source_data": "2024-01-09-143000",
    "transformed_data": "2024-01-09-145000"
  }
}
```

### Cache Warming

On data update completion:
1. Identify all active widgets for the study
2. Pre-calculate common aggregations
3. Store in cache before users access
4. Notify dashboard of fresh data availability

```python
# Cache warming job
def warm_widget_caches(study_id, new_data_version):
    widgets = get_study_widgets(study_id)
    
    for widget in widgets:
        # Calculate in background
        data = calculate_widget_data(widget, new_data_version)
        
        # Store in cache
        cache_key = build_cache_key(widget, new_data_version)
        redis.setex(cache_key, 3600, data)
```

## Performance Optimizations

### 1. Partial Aggregations
For large datasets, pre-calculate partial aggregations:

```python
# Daily aggregations stored
{
  "date": "2024-01-10",
  "dataset": "AE",
  "aggregations": {
    "total_count": 1543,
    "by_severity": {
      "MILD": 823,
      "MODERATE": 567,
      "SEVERE": 153
    },
    "unique_subjects": 234
  }
}
```

### 2. Smart Cache TTL
Different TTLs based on widget type:
- Real-time metrics: 5 minutes
- Daily summaries: 1 hour
- Historical trends: 6 hours

### 3. Comparison Data Caching
Store previous period data separately:

```python
# Current and previous cached separately
current_key = "widget:STUDY-001:metric-123:current"
previous_key = "widget:STUDY-001:metric-123:previous"

# Allows independent updates
```

## Cache Monitoring

### Metrics to Track
1. **Cache hit rate** - Should be >80%
2. **Cache miss latency** - Time to calculate
3. **Cache size** - Memory usage
4. **Invalidation frequency** - How often cleared

### Admin Dashboard
```
Cache Statistics - STUDY-001
────────────────────────────
Hit Rate: 87%
Avg Response Time: 45ms (cached) / 450ms (uncached)
Cache Size: 12.4 MB
Last Invalidation: 2 hours ago
Active Cached Widgets: 24
```

## Configuration Options

```python
CACHE_CONFIG = {
    "enabled": True,
    "redis_url": "redis://localhost:6379",
    "default_ttl": 3600,  # 1 hour
    "browser_cache_ttl": 300,  # 5 minutes
    "max_cache_size_mb": 100,
    "cache_warming_enabled": True,
    "cache_warming_workers": 4
}
```

## Benefits

1. **Fast Response**: Most requests served from cache (<50ms)
2. **Reduced Load**: Parquet files read less frequently
3. **Scalability**: Multiple users see same cached data
4. **Fresh Data**: Automatic invalidation ensures accuracy
5. **Cost Effective**: Less compute needed for repeated queries