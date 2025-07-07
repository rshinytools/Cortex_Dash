# Widget Data Execution Engine

This document describes the Widget Data Execution Engine implemented for the Clinical Dashboard Platform.

## Overview

The Widget Data Execution Engine is responsible for fetching and processing data for dashboard widgets. It supports different widget types (metrics, charts, tables) and includes caching for performance optimization.

## Architecture

### Components

1. **Widget Data Executor** (`app/services/widget_data_executor.py`)
   - Base class: `BaseWidgetDataExecutor`
   - Implementations:
     - `MetricWidgetDataExecutor`: For single-value metrics
     - `ChartWidgetDataExecutor`: For line, bar, pie charts
     - `TableWidgetDataExecutor`: For paginated data tables
   - Factory: `WidgetDataExecutorFactory`

2. **Query Builder** (`app/services/query_builder.py`)
   - Builds SQL queries based on widget configuration
   - Applies field mappings from template to study fields
   - Supports filters, sorting, and pagination
   - Prevents SQL injection with parameterized queries

3. **Redis Cache** (`app/services/redis_cache.py`)
   - Async Redis client for caching widget data
   - TTL-based cache expiration
   - Cache invalidation by study or widget
   - Cache statistics tracking

4. **API Endpoints** (`app/api/v1/endpoints/studies.py`)
   - `GET /studies/{study_id}/dashboards/{dashboard_id}/widgets/{widget_id}/data`
   - `POST /studies/{study_id}/dashboards/{dashboard_id}/widgets/{widget_id}/refresh`
   - `POST /studies/{study_id}/refresh-all-widgets`
   - `GET /studies/{study_id}/cache-stats`

## Widget Types

### Metric Widgets
- Display single values (count, sum, avg, min, max)
- Support trend indicators and change percentages
- Example: Total enrolled subjects, average age

### Chart Widgets
- Line charts: Time series data
- Bar charts: Categorical comparisons
- Pie charts: Distribution visualization
- Scatter plots: Correlation analysis
- Support grouping and multiple series

### Table Widgets
- Paginated data display
- Configurable columns
- Sorting and filtering support
- Export capabilities (future enhancement)

## Data Flow

1. **Request Processing**
   - API endpoint receives widget data request
   - Validates study and dashboard access permissions
   - Retrieves widget configuration from dashboard

2. **Cache Check**
   - Generates cache key based on study, widget, and filters
   - Checks Redis for cached data
   - Returns cached data if available and not expired

3. **Data Execution**
   - Creates appropriate executor based on widget type
   - Applies field mappings from study configuration
   - Generates mock data (temporary implementation)
   - Future: Execute SQL queries against actual data sources

4. **Response Caching**
   - Caches response with appropriate TTL
   - TTL based on study refresh frequency and widget config
   - Background task to avoid blocking response

5. **Activity Logging**
   - Logs widget data access for audit trail
   - Tracks cache hits/misses
   - Records execution time

## Field Mapping

The system supports mapping template fields to study-specific fields:

```json
{
  "field_mappings": {
    "ADSL.USUBJID": "subject_id",
    "ADSL.AGE": "age_at_enrollment",
    "ADAE.AETERM": "adverse_event_term"
  }
}
```

## Caching Strategy

### Cache Keys
Format: `widget_data:{study_id}:{widget_id}:{dashboard_id}`

### TTL Calculation
- Real-time data: 1 minute
- Hourly refresh: 1 hour
- Daily refresh: 24 hours
- Weekly refresh: 7 days
- Widget-specific TTL overrides supported

### Cache Invalidation
- Manual refresh: Single widget or all study widgets
- Automatic invalidation on data updates (future)
- Pattern-based deletion for study-wide invalidation

## Security Considerations

1. **Access Control**
   - Study-level permissions checked
   - Dashboard view permissions required
   - Organization isolation enforced

2. **SQL Injection Prevention**
   - Parameterized queries only
   - Identifier quoting for table/column names
   - Input validation and sanitization

3. **Data Isolation**
   - Multi-tenant architecture respected
   - Cache keys include study ID for isolation
   - Field mappings validated against study schema

## Performance Optimizations

1. **Caching**
   - Redis for sub-millisecond cache lookups
   - Background cache population
   - Cache warming strategies (future)

2. **Query Optimization**
   - Indexed fields for common filters
   - Query result limiting
   - Aggregation push-down to database

3. **Async Processing**
   - Non-blocking Redis operations
   - Background tasks for logging
   - Concurrent widget data fetching (future)

## Testing

Run the test script to verify the implementation:

```bash
cd backend
python scripts/test_widget_data.py
```

This will:
- Create sample widget definitions
- Test each executor type
- Verify caching functionality
- Display execution metrics

## Future Enhancements

1. **Real Data Integration**
   - Replace mock data with actual database queries
   - Support for multiple data source types (PostgreSQL, Parquet, APIs)
   - Data transformation pipelines

2. **Advanced Caching**
   - Cache warming on study activation
   - Predictive cache invalidation
   - Distributed caching for scalability

3. **Performance Monitoring**
   - Widget execution metrics dashboard
   - Slow query detection and alerting
   - Cache hit rate optimization

4. **Additional Widget Types**
   - Map widgets for geographical data
   - Specialized clinical trial widgets
   - Custom widget plugin system

## Configuration

### Environment Variables
- `REDIS_URL`: Redis connection string
- `DASHBOARD_CACHE_TTL`: Default cache TTL in seconds

### Widget Definition Schema
Widgets must define:
- `config_schema`: JSON Schema for configuration validation
- `data_contract`: Required fields and data sources
- `size_constraints`: Dashboard layout constraints
- `data_requirements`: Datasets and fields needed