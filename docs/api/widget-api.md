# Widget API Documentation

## Overview

The Widget API provides comprehensive functionality for managing and configuring dashboard widgets in the Clinical Dashboard Platform. This API enables creation, configuration, data retrieval, and management of various widget types optimized for clinical trial data visualization.

## Table of Contents

1. [Authentication](#authentication)
2. [Widget Types](#widget-types)
3. [Widget Configuration](#widget-configuration)
4. [Data Retrieval](#data-retrieval)
5. [Batch Operations](#batch-operations)
6. [Preview and Validation](#preview-and-validation)
7. [Error Handling](#error-handling)
8. [Examples](#examples)

## Authentication

All Widget API endpoints require authentication using Bearer tokens:

```http
Authorization: Bearer <your-jwt-token>
```

## Widget Types

### List Available Widget Types

Retrieve all available widget types with their configuration schemas.

**Endpoint:** `GET /api/v1/widget-types`

**Parameters:**
- `category` (optional): Filter by widget category (`basic`, `visualization`, `data`, `composite`, `specialized`)

**Response:**
```json
[
  {
    "id": "metric",
    "name": "Metric Card",
    "description": "Display a single metric with trend",
    "category": "basic",
    "icon": "chart-bar",
    "default_size": {"w": 3, "h": 2},
    "min_size": {"w": 2, "h": 2},
    "max_size": {"w": 6, "h": 4},
    "configurable_properties": [
      {
        "name": "metric",
        "type": "select",
        "label": "Metric",
        "required": true,
        "options": ["count", "sum", "average", "percentage"]
      }
    ]
  }
]
```

### Available Widget Categories

- **Basic**: Simple metrics and indicators
- **Visualization**: Charts, graphs, and visual representations
- **Data**: Tables and data grids
- **Composite**: Complex widgets combining multiple data sources
- **Specialized**: Domain-specific widgets for clinical trials

### Supported Widget Types

| Widget Type | Category | Description | Use Cases |
|-------------|----------|-------------|-----------|
| `metric` | basic | Single metric with trend | KPIs, enrollment counts, safety metrics |
| `chart` | visualization | Various chart types | Trends, comparisons, distributions |
| `table` | data | Tabular data display | Patient listings, adverse events |
| `kpi_grid` | composite | Grid of multiple KPIs | Executive dashboards |
| `timeline` | specialized | Event timeline | Study milestones, patient journey |
| `map` | specialized | Geographic visualization | Site locations, enrollment by region |

## Widget Configuration

### Validate Widget Configuration

Validate a widget configuration before saving to ensure it meets all requirements.

**Endpoint:** `POST /api/v1/widgets/validate-config`

**Request Body:**
```json
{
  "type": "chart",
  "config": {
    "chart_type": "line",
    "dataset": "ADSL",
    "x_axis": "VISITNUM",
    "y_axis": "AGE",
    "group_by": "TRT01P"
  }
}
```

**Response:**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [
    {
      "field": "config.chart_type",
      "message": "Line charts work best with continuous data"
    }
  ],
  "suggestions": [
    {
      "field": "config.show_legend",
      "message": "Consider enabling legend for grouped data"
    }
  ]
}
```

### Configuration Properties by Widget Type

#### Metric Widget
```json
{
  "type": "metric",
  "config": {
    "metric": "count|sum|average|percentage",
    "dataset": "string",
    "field": "string (optional)",
    "show_trend": "boolean",
    "comparison_period": "string (optional)",
    "unit": "string (optional)"
  }
}
```

#### Chart Widget
```json
{
  "type": "chart",
  "config": {
    "chart_type": "line|bar|scatter|pie|area|heatmap",
    "dataset": "string",
    "x_axis": "string",
    "y_axis": "string",
    "group_by": "string (optional)",
    "aggregation": "count|sum|avg|min|max",
    "color_scheme": "string (optional)"
  }
}
```

#### Table Widget
```json
{
  "type": "table",
  "config": {
    "dataset": "string",
    "columns": ["string"],
    "page_size": "number (5-100)",
    "enable_export": "boolean",
    "enable_sorting": "boolean",
    "enable_filtering": "boolean"
  }
}
```

## Data Retrieval

### Get Widget Data

Retrieve data for a specific widget.

**Endpoint:** `GET /api/v1/widgets/{widget_id}/data`

**Parameters:**
- `widget_id` (path): Widget UUID
- `dashboard_id` (query): Dashboard UUID
- `refresh` (query, optional): Force refresh from source (`true`/`false`)
- `filters` (query, optional): JSON-encoded filters

**Response:**
```json
{
  "widget_id": "uuid",
  "dashboard_id": "uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "cache_status": "hit",
  "data_version": "v5.0",
  "data": {
    "value": 1234,
    "previous_value": 1189,
    "change": 45,
    "change_percent": 3.78,
    "trend": "up",
    "unit": "subjects"
  },
  "metadata": {
    "execution_time_ms": 150,
    "row_count": 1000,
    "filters_applied": true
  }
}
```

### Refresh Widget Data

Force refresh data for a specific widget, clearing cache and fetching fresh data.

**Endpoint:** `POST /api/v1/widgets/{widget_id}/refresh`

**Request Body:**
```json
{
  "dashboard_id": "uuid"
}
```

**Response:**
```json
{
  "widget_id": "uuid",
  "dashboard_id": "uuid",
  "status": "refreshing",
  "job_id": "uuid",
  "estimated_completion": "2024-01-15T10:30:05Z",
  "cache_cleared": true
}
```

## Batch Operations

### Batch Data Retrieval

Retrieve data for multiple widgets in a single request for better performance.

**Endpoint:** `POST /api/v1/widgets/batch-data`

**Request Body:**
```json
{
  "widget_ids": ["uuid1", "uuid2", "uuid3"],
  "dashboard_id": "uuid",
  "filters": {
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    },
    "treatment_group": "Drug A"
  }
}
```

**Response:**
```json
{
  "dashboard_id": "uuid",
  "requested_widgets": 3,
  "successful": 2,
  "failed": 1,
  "results": {
    "uuid1": {
      "data": {"value": 100, "trend": "up"},
      "timestamp": "2024-01-15T10:30:00Z",
      "status": "success"
    },
    "uuid2": {
      "data": {"value": 200, "trend": "stable"},
      "timestamp": "2024-01-15T10:30:00Z",
      "status": "success"
    }
  },
  "errors": {
    "uuid3": {
      "error": "Data source unavailable",
      "message": "Unable to connect to source database",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  },
  "execution_time_ms": 350
}
```

## Preview and Validation

### Preview Widget

Generate a preview of a widget with sample data before saving.

**Endpoint:** `POST /api/v1/widgets/preview`

**Parameters:**
- `sample_size` (query, optional): Number of sample records (1-100, default: 10)

**Request Body:**
```json
{
  "type": "chart",
  "config": {
    "chart_type": "bar",
    "dataset": "ADSL",
    "x_axis": "TRT01P",
    "y_axis": "AGE",
    "aggregation": "avg"
  }
}
```

**Response:**
```json
{
  "widget_type": "chart",
  "config": {...},
  "preview_generated_at": "2024-01-15T10:30:00Z",
  "sample_data": {
    "labels": ["Placebo", "Drug A 10mg", "Drug A 20mg"],
    "datasets": [{
      "label": "Average Age",
      "data": [65.2, 67.1, 64.8]
    }]
  },
  "render_info": {
    "estimated_render_time_ms": 150,
    "recommended_size": {"w": 6, "h": 4},
    "responsive": true
  }
}
```

### Get Data Sources

Retrieve available data sources for widgets in a study.

**Endpoint:** `GET /api/v1/widgets/data-sources`

**Parameters:**
- `study_id` (query): Study UUID
- `widget_type` (query, optional): Filter by widget type compatibility

**Response:**
```json
[
  {
    "dataset": "ADSL",
    "name": "Subject Level Analysis Dataset",
    "type": "ADaM",
    "fields": [
      {
        "name": "USUBJID",
        "label": "Unique Subject ID",
        "type": "string",
        "is_identifier": true
      },
      {
        "name": "AGE",
        "label": "Age",
        "type": "numeric",
        "is_continuous": true
      }
    ],
    "compatible_widgets": ["metric", "chart", "table"]
  }
]
```

## Error Handling

The Widget API uses standard HTTP status codes and provides detailed error messages:

### Common Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters or body
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Widget or resource not found
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Widget configuration is invalid",
  "details": {
    "field": "config.dataset",
    "error": "Dataset 'INVALID' not found in study"
  }
}
```

### Common Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `INVALID_WIDGET_TYPE` | Unknown widget type | Use valid widget type from `/widget-types` |
| `VALIDATION_ERROR` | Configuration validation failed | Check required fields and valid values |
| `DATA_SOURCE_ERROR` | Data source unavailable | Verify data source connection |
| `PERMISSION_DENIED` | Insufficient permissions | Contact administrator |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Implement request throttling |

## Examples

### Create a Metric Widget

```javascript
// 1. Get available widget types
const widgetTypes = await fetch('/api/v1/widget-types?category=basic');

// 2. Validate configuration
const validation = await fetch('/api/v1/widgets/validate-config', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    type: 'metric',
    config: {
      metric: 'count',
      dataset: 'ADSL',
      field: 'USUBJID',
      show_trend: true
    }
  })
});

// 3. Preview widget
const preview = await fetch('/api/v1/widgets/preview', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    type: 'metric',
    config: {
      metric: 'count',
      dataset: 'ADSL',
      field: 'USUBJID',
      show_trend: true
    }
  })
});
```

### Create a Chart Widget

```javascript
// Configuration for enrollment trend chart
const chartConfig = {
  type: 'chart',
  config: {
    chart_type: 'line',
    dataset: 'ADSL',
    x_axis: 'RFSTDTC',
    y_axis: 'USUBJID',
    aggregation: 'count',
    group_by: 'SITEID',
    title: 'Enrollment Trend by Site'
  }
};

// Validate and preview
const validation = await fetch('/api/v1/widgets/validate-config', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(chartConfig)
});

if (validation.is_valid) {
  const preview = await fetch('/api/v1/widgets/preview', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(chartConfig)
  });
}
```

### Load Dashboard Data

```javascript
// Get data for all widgets in a dashboard
const widgetIds = ['uuid1', 'uuid2', 'uuid3'];
const dashboardData = await fetch('/api/v1/widgets/batch-data', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    widget_ids: widgetIds,
    dashboard_id: 'dashboard-uuid',
    filters: {
      date_range: {
        start: '2024-01-01',
        end: '2024-03-31'
      }
    }
  })
});

const results = await dashboardData.json();
console.log(`Loaded ${results.successful}/${results.requested_widgets} widgets`);
```

### Refresh Stale Data

```javascript
// Refresh specific widget
const refreshResponse = await fetch(`/api/v1/widgets/${widgetId}/refresh`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    dashboard_id: 'dashboard-uuid'
  })
});

const refresh = await refreshResponse.json();
console.log(`Refresh job ${refresh.job_id} started`);

// Poll for completion
const checkStatus = async (jobId) => {
  const status = await fetch(`/api/v1/jobs/${jobId}/status`);
  return status.json();
};
```

## Best Practices

### Performance Optimization

1. **Use Batch Requests**: Load multiple widgets at once using `/widgets/batch-data`
2. **Cache Management**: Use cache-friendly requests and only refresh when necessary
3. **Pagination**: Use appropriate page sizes for table widgets
4. **Filtering**: Apply filters to reduce data volume

### Configuration Validation

1. **Always Validate**: Use `/widgets/validate-config` before saving
2. **Preview First**: Use `/widgets/preview` to verify appearance
3. **Check Data Sources**: Verify datasets exist using `/widgets/data-sources`

### Error Handling

1. **Handle Partial Failures**: Process successful widgets even if some fail
2. **Retry Logic**: Implement exponential backoff for transient errors
3. **User Feedback**: Show meaningful error messages to users

### Security

1. **Authentication**: Always include valid Bearer tokens
2. **Authorization**: Respect user permissions and study access
3. **Input Validation**: Validate all configuration inputs
4. **Rate Limiting**: Implement client-side request throttling

## Rate Limits

- **Standard requests**: 100 requests per minute per user
- **Batch requests**: 20 requests per minute per user
- **Preview requests**: 50 requests per minute per user
- **Refresh requests**: 10 requests per minute per widget

## Support

For additional support with the Widget API:

- **Documentation**: Check the full API documentation at `/docs`
- **Examples**: See the examples repository
- **Issues**: Report bugs or request features
- **Contact**: support@sagarmatha.ai