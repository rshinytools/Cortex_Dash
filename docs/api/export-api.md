# Export API Documentation

## Overview

The Export API provides comprehensive functionality for exporting dashboard data, reports, and visualizations from the Clinical Dashboard Platform. This API supports multiple export formats and delivery methods optimized for clinical trial reporting requirements.

## Table of Contents

1. [Authentication](#authentication)
2. [Export Types](#export-types)
3. [Dashboard Exports](#dashboard-exports)
4. [Scheduled Exports](#scheduled-exports)
5. [Data Exports](#data-exports)
6. [Report Generation](#report-generation)
7. [Export Management](#export-management)
8. [Delivery Options](#delivery-options)
9. [Examples](#examples)

## Authentication

All Export API endpoints require authentication using Bearer tokens:

```http
Authorization: Bearer <your-jwt-token>
```

## Export Types

### Supported Export Formats

| Format | Description | Use Cases | File Extension |
|--------|-------------|-----------|----------------|
| `pdf` | High-quality PDF reports | Executive reports, regulatory submissions | `.pdf` |
| `excel` | Excel workbooks with multiple sheets | Data analysis, further processing | `.xlsx` |
| `csv` | Comma-separated values | Data import, statistical analysis | `.csv` |
| `json` | JSON data format | API integration, data exchange | `.json` |
| `png` | High-resolution images | Presentations, documentation | `.png` |
| `svg` | Scalable vector graphics | Print publications, scalable visuals | `.svg` |
| `powerpoint` | PowerPoint presentations | Executive presentations | `.pptx` |

### Export Categories

- **Dashboard Exports**: Complete dashboard snapshots with data and visualizations
- **Data Exports**: Raw or processed data from specific datasets
- **Widget Exports**: Individual widget data and visualizations
- **Report Exports**: Formatted reports with multiple dashboard views
- **Template Exports**: Dashboard template configurations

## Dashboard Exports

### Export Dashboard

Export a complete dashboard with all widgets and data.

**Endpoint:** `POST /api/v1/dashboards/{dashboard_id}/export`

**Parameters:**
- `dashboard_id` (path): Dashboard UUID

**Request Body:**
```json
{
  "format": "pdf|excel|powerpoint|json",
  "options": {
    "include_data": true,
    "include_metadata": true,
    "page_orientation": "portrait|landscape",
    "page_size": "A4|letter|A3",
    "resolution": "standard|high|print",
    "theme": "light|dark|auto"
  },
  "filters": {
    "date_range": {
      "start_date": "2024-01-01",
      "end_date": "2024-03-31"
    },
    "site_ids": ["SITE001", "SITE002"],
    "treatment_groups": ["Placebo", "Drug A"]
  },
  "widgets": {
    "include_all": true,
    "exclude_widgets": ["widget-uuid-1"],
    "widget_specific_filters": {
      "widget-uuid-2": {
        "top_n": 10
      }
    }
  },
  "delivery": {
    "method": "download|email|api_callback",
    "email_recipients": ["user@organization.com"],
    "callback_url": "https://your-app.com/export-complete"
  }
}
```

**Response:**
```json
{
  "export_id": "export-uuid",
  "status": "queued|processing|completed|failed",
  "dashboard_id": "dashboard-uuid",
  "format": "pdf",
  "created_at": "2024-01-15T10:30:00Z",
  "estimated_completion": "2024-01-15T10:32:00Z",
  "download_url": null,
  "file_info": {
    "estimated_size_mb": 12.5,
    "page_count": 8,
    "widget_count": 15
  },
  "progress": {
    "percentage": 0,
    "current_step": "Preparing export",
    "steps_total": 5
  }
}
```

### Export Dashboard Widget

Export a specific widget from a dashboard.

**Endpoint:** `POST /api/v1/dashboards/{dashboard_id}/widgets/{widget_id}/export`

**Request Body:**
```json
{
  "format": "png|svg|pdf|excel|csv|json",
  "options": {
    "width": 800,
    "height": 600,
    "dpi": 300,
    "background": "transparent|white|theme",
    "include_title": true,
    "include_legend": true,
    "include_data_table": false
  },
  "data_options": {
    "include_raw_data": true,
    "max_rows": 10000,
    "date_format": "ISO|US|EU"
  }
}
```

**Response:**
```json
{
  "export_id": "widget-export-uuid",
  "widget_id": "widget-uuid",
  "status": "completed",
  "download_url": "https://exports.cortexdash.com/widget-export-uuid.png",
  "file_info": {
    "format": "png",
    "size_bytes": 245760,
    "dimensions": "800x600",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

## Scheduled Exports

### Create Scheduled Export

Set up automatic exports on a recurring schedule.

**Endpoint:** `POST /api/v1/scheduled-exports`

**Request Body:**
```json
{
  "name": "Weekly Safety Report",
  "description": "Automated weekly safety dashboard export",
  "dashboard_id": "dashboard-uuid",
  "schedule": {
    "frequency": "daily|weekly|monthly|quarterly",
    "day_of_week": "monday",
    "time": "09:00",
    "timezone": "UTC"
  },
  "export_config": {
    "format": "pdf",
    "options": {
      "include_data": true,
      "page_orientation": "landscape"
    },
    "filters": {
      "date_range": {
        "type": "relative",
        "period": "last_7_days"
      }
    }
  },
  "delivery": {
    "method": "email",
    "email_recipients": [
      "safety@organization.com",
      "dm@organization.com"
    ],
    "email_subject": "Weekly Safety Report - {{date}}",
    "email_body": "Please find attached the weekly safety report."
  },
  "retention": {
    "keep_exports": 12,
    "delete_after_days": 90
  }
}
```

**Response:**
```json
{
  "scheduled_export_id": "schedule-uuid",
  "name": "Weekly Safety Report",
  "status": "active",
  "next_execution": "2024-01-22T09:00:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "execution_history": []
}
```

### List Scheduled Exports

Get all scheduled exports for the current user or organization.

**Endpoint:** `GET /api/v1/scheduled-exports`

**Parameters:**
- `dashboard_id` (optional): Filter by dashboard
- `status` (optional): Filter by status (`active`, `paused`, `expired`)
- `frequency` (optional): Filter by frequency

**Response:**
```json
{
  "scheduled_exports": [
    {
      "scheduled_export_id": "schedule-uuid",
      "name": "Weekly Safety Report",
      "dashboard_name": "Safety Dashboard",
      "frequency": "weekly",
      "status": "active",
      "next_execution": "2024-01-22T09:00:00Z",
      "last_execution": {
        "executed_at": "2024-01-15T09:00:00Z",
        "status": "completed",
        "export_id": "export-uuid"
      },
      "recipients": 2,
      "retention_days": 90
    }
  ],
  "pagination": {
    "total": 15,
    "page": 1,
    "limit": 20
  }
}
```

### Update Scheduled Export

Modify an existing scheduled export.

**Endpoint:** `PUT /api/v1/scheduled-exports/{schedule_id}`

**Request Body:** Same structure as create scheduled export

### Pause/Resume Scheduled Export

**Endpoint:** `POST /api/v1/scheduled-exports/{schedule_id}/pause`
**Endpoint:** `POST /api/v1/scheduled-exports/{schedule_id}/resume`

**Response:**
```json
{
  "scheduled_export_id": "schedule-uuid",
  "status": "paused|active",
  "updated_at": "2024-01-15T10:30:00Z",
  "next_execution": "2024-01-22T09:00:00Z"
}
```

## Data Exports

### Export Dataset

Export raw or processed data from specific datasets.

**Endpoint:** `POST /api/v1/studies/{study_id}/datasets/{dataset_name}/export`

**Request Body:**
```json
{
  "format": "csv|excel|json|sas|parquet",
  "options": {
    "include_labels": true,
    "include_metadata": true,
    "date_format": "ISO|SAS",
    "missing_value_representation": ".|NULL|blank"
  },
  "filters": {
    "columns": ["USUBJID", "AGE", "SEX", "TRT01P"],
    "where_clause": "AGE >= 18 AND SEX = 'F'",
    "date_range": {
      "column": "RFSTDTC",
      "start_date": "2024-01-01",
      "end_date": "2024-03-31"
    }
  },
  "processing": {
    "derive_variables": [
      {
        "name": "AGECAT",
        "expression": "CASE WHEN AGE < 65 THEN '<65' ELSE '>=65' END"
      }
    ],
    "sort_by": ["USUBJID", "VISITNUM"],
    "limit": 50000
  }
}
```

**Response:**
```json
{
  "export_id": "data-export-uuid",
  "dataset": "ADSL",
  "study_id": "study-uuid",
  "status": "processing",
  "record_count": 1245,
  "column_count": 45,
  "estimated_completion": "2024-01-15T10:31:00Z",
  "file_info": {
    "estimated_size_mb": 8.2,
    "format": "csv"
  }
}
```

### Export Query Results

Export results from a custom data query.

**Endpoint:** `POST /api/v1/studies/{study_id}/query/export`

**Request Body:**
```json
{
  "query": {
    "sql": "SELECT USUBJID, AGE, SEX FROM ADSL WHERE AGE > 65",
    "parameters": {
      "min_age": 65
    }
  },
  "format": "csv|excel|json",
  "options": {
    "include_headers": true,
    "chunk_size": 10000
  }
}
```

## Report Generation

### Generate Dashboard Report

Create a formatted report with multiple dashboard views.

**Endpoint:** `POST /api/v1/reports/dashboard`

**Request Body:**
```json
{
  "report_config": {
    "title": "Monthly Safety Report",
    "subtitle": "Study ABC-123 Safety Review",
    "template": "safety_report_template",
    "cover_page": true,
    "table_of_contents": true,
    "executive_summary": true
  },
  "dashboards": [
    {
      "dashboard_id": "safety-dashboard-uuid",
      "title": "Safety Overview",
      "filters": {
        "date_range": {
          "start_date": "2024-01-01",
          "end_date": "2024-01-31"
        }
      },
      "widget_layout": "grid|list",
      "page_break_after": true
    },
    {
      "dashboard_id": "ae-dashboard-uuid",
      "title": "Adverse Events Detail",
      "include_data_tables": true
    }
  ],
  "format": "pdf|powerpoint",
  "styling": {
    "theme": "corporate",
    "logo_url": "https://organization.com/logo.png",
    "color_scheme": "blue",
    "font_family": "Arial"
  },
  "metadata": {
    "author": "Clinical Data Team",
    "organization": "Organization Name",
    "report_date": "2024-01-15",
    "confidentiality": "Confidential"
  }
}
```

**Response:**
```json
{
  "report_id": "report-uuid",
  "title": "Monthly Safety Report",
  "status": "generating",
  "dashboard_count": 2,
  "estimated_pages": 25,
  "estimated_completion": "2024-01-15T10:35:00Z",
  "progress": {
    "percentage": 10,
    "current_step": "Rendering dashboard 1 of 2"
  }
}
```

### Generate Regulatory Report

Create reports formatted for regulatory submissions.

**Endpoint:** `POST /api/v1/reports/regulatory`

**Request Body:**
```json
{
  "submission_type": "IND|NDA|BLA|CTD",
  "section": "5.3.5.1|5.3.5.2|5.3.5.3",
  "study_id": "study-uuid",
  "data_cut_date": "2024-01-31",
  "report_components": [
    "demographics",
    "disposition",
    "exposure",
    "efficacy",
    "safety"
  ],
  "compliance": {
    "validate_21cfr11": true,
    "include_audit_trail": true,
    "electronic_signature": true
  },
  "format": "pdf",
  "delivery": {
    "method": "secure_download",
    "encryption": true,
    "password_protected": true
  }
}
```

## Export Management

### Get Export Status

Check the status of an export operation.

**Endpoint:** `GET /api/v1/exports/{export_id}/status`

**Response:**
```json
{
  "export_id": "export-uuid",
  "status": "queued|processing|completed|failed|cancelled",
  "progress": {
    "percentage": 75,
    "current_step": "Generating visualizations",
    "steps_completed": 3,
    "steps_total": 4,
    "estimated_time_remaining": "30 seconds"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:15Z",
  "completed_at": null,
  "error_message": null,
  "file_info": {
    "format": "pdf",
    "size_bytes": 2453760,
    "page_count": 12
  }
}
```

### Download Export

Download a completed export file.

**Endpoint:** `GET /api/v1/exports/{export_id}/download`

**Parameters:**
- `inline` (optional): Display inline instead of download (`true`/`false`)

**Response:** Binary file download with appropriate headers

### List User Exports

Get all exports for the current user.

**Endpoint:** `GET /api/v1/exports`

**Parameters:**
- `status` (optional): Filter by status
- `format` (optional): Filter by format
- `created_after` (optional): Filter by creation date
- `page`, `limit`: Pagination

**Response:**
```json
{
  "exports": [
    {
      "export_id": "export-uuid",
      "type": "dashboard",
      "name": "Safety Dashboard Export",
      "format": "pdf",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:32:15Z",
      "file_size_mb": 2.4,
      "download_url": "https://exports.cortexdash.com/export-uuid.pdf",
      "expires_at": "2024-01-22T10:30:00Z"
    }
  ],
  "pagination": {
    "total": 45,
    "page": 1,
    "limit": 20
  }
}
```

### Cancel Export

Cancel a running export operation.

**Endpoint:** `POST /api/v1/exports/{export_id}/cancel`

**Response:**
```json
{
  "export_id": "export-uuid",
  "status": "cancelled",
  "cancelled_at": "2024-01-15T10:31:00Z",
  "cleanup_completed": true
}
```

### Delete Export

Delete an export file and its metadata.

**Endpoint:** `DELETE /api/v1/exports/{export_id}`

**Response:**
```json
{
  "export_id": "export-uuid",
  "deleted_at": "2024-01-15T10:35:00Z",
  "file_removed": true
}
```

## Delivery Options

### Email Delivery

Configure email delivery for exports.

```json
{
  "delivery": {
    "method": "email",
    "email_config": {
      "recipients": [
        {
          "email": "user@organization.com",
          "name": "John Doe",
          "type": "to|cc|bcc"
        }
      ],
      "subject": "Dashboard Export - {{dashboard_name}} - {{date}}",
      "body": "Please find attached the requested dashboard export.",
      "send_notifications": true,
      "compress_attachments": true,
      "password_protect": true
    }
  }
}
```

### API Callback

Configure callback for programmatic delivery.

```json
{
  "delivery": {
    "method": "api_callback",
    "callback_config": {
      "url": "https://your-app.com/api/export-complete",
      "method": "POST",
      "headers": {
        "Authorization": "Bearer your-api-key",
        "Content-Type": "application/json"
      },
      "payload_template": {
        "export_id": "{{export_id}}",
        "download_url": "{{download_url}}",
        "status": "{{status}}"
      },
      "retry_policy": {
        "max_retries": 3,
        "retry_delay": 30
      }
    }
  }
}
```

### Secure Download

Configure secure download with access controls.

```json
{
  "delivery": {
    "method": "secure_download",
    "security_config": {
      "expiry_hours": 24,
      "max_downloads": 5,
      "ip_restrictions": ["192.168.1.0/24"],
      "password_protection": true,
      "audit_downloads": true
    }
  }
}
```

## Examples

### Export Dashboard as PDF

```javascript
// Create dashboard export
const exportRequest = await fetch(`/api/v1/dashboards/${dashboardId}/export`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    format: 'pdf',
    options: {
      include_data: true,
      page_orientation: 'landscape',
      resolution: 'high'
    },
    filters: {
      date_range: {
        start_date: '2024-01-01',
        end_date: '2024-03-31'
      }
    },
    delivery: {
      method: 'download'
    }
  })
});

const exportResult = await exportRequest.json();
const exportId = exportResult.export_id;

// Poll for completion
const pollExport = async (exportId) => {
  const status = await fetch(`/api/v1/exports/${exportId}/status`);
  const result = await status.json();
  
  if (result.status === 'completed') {
    window.location.href = `/api/v1/exports/${exportId}/download`;
  } else if (result.status === 'failed') {
    console.error('Export failed:', result.error_message);
  } else {
    setTimeout(() => pollExport(exportId), 2000);
  }
};

pollExport(exportId);
```

### Schedule Weekly Report

```javascript
// Create scheduled export
const scheduleRequest = await fetch('/api/v1/scheduled-exports', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Weekly Safety Report',
    dashboard_id: dashboardId,
    schedule: {
      frequency: 'weekly',
      day_of_week: 'monday',
      time: '09:00',
      timezone: 'UTC'
    },
    export_config: {
      format: 'pdf',
      options: {
        include_data: true,
        page_orientation: 'landscape'
      },
      filters: {
        date_range: {
          type: 'relative',
          period: 'last_7_days'
        }
      }
    },
    delivery: {
      method: 'email',
      email_recipients: ['team@organization.com'],
      email_subject: 'Weekly Safety Report - {{date}}'
    }
  })
});

const schedule = await scheduleRequest.json();
console.log(`Scheduled export created: ${schedule.scheduled_export_id}`);
```

### Export Data as Excel

```javascript
// Export dataset
const dataExport = await fetch(`/api/v1/studies/${studyId}/datasets/ADSL/export`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    format: 'excel',
    options: {
      include_labels: true,
      include_metadata: true
    },
    filters: {
      columns: ['USUBJID', 'AGE', 'SEX', 'TRT01P'],
      where_clause: 'AGE >= 18'
    },
    processing: {
      sort_by: ['USUBJID']
    }
  })
});

const dataResult = await dataExport.json();
const exportId = dataResult.export_id;

// Monitor progress and download
const monitorDataExport = async (exportId) => {
  const status = await fetch(`/api/v1/exports/${exportId}/status`);
  const result = await status.json();
  
  if (result.status === 'completed') {
    const downloadLink = document.createElement('a');
    downloadLink.href = `/api/v1/exports/${exportId}/download`;
    downloadLink.download = 'ADSL_export.xlsx';
    downloadLink.click();
  }
};
```

## Error Handling

### Common Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `EXPORT_TIMEOUT` | Export operation timed out | Reduce data scope or retry |
| `INSUFFICIENT_MEMORY` | Not enough memory for export | Use smaller page sizes or filters |
| `INVALID_FORMAT` | Unsupported export format | Use supported format |
| `DATA_ACCESS_ERROR` | Cannot access required data | Check data source availability |
| `TEMPLATE_ERROR` | Report template error | Verify template configuration |

### Error Response Format

```json
{
  "error": {
    "code": "EXPORT_TIMEOUT",
    "message": "Export operation exceeded maximum time limit",
    "details": {
      "timeout_seconds": 300,
      "records_processed": 50000,
      "suggestion": "Apply filters to reduce data volume"
    }
  }
}
```

## Rate Limits

- **Export requests**: 20 per hour per user
- **Scheduled exports**: 50 active schedules per organization
- **Download requests**: 100 per hour per user
- **Status checks**: 300 per hour per user

## Best Practices

### Performance

1. **Use Filters**: Apply appropriate filters to reduce data volume
2. **Choose Format Wisely**: Select the most efficient format for your use case
3. **Batch Operations**: Combine multiple exports when possible
4. **Schedule Off-Peak**: Schedule large exports during off-peak hours

### Security

1. **Access Controls**: Ensure proper user permissions
2. **Data Sensitivity**: Use encryption for sensitive data
3. **Secure Delivery**: Use secure delivery methods for confidential reports
4. **Audit Trail**: Maintain audit trails for regulatory compliance

### Reliability

1. **Monitor Progress**: Always monitor export progress
2. **Handle Failures**: Implement proper error handling
3. **Cleanup**: Delete unnecessary exports to save storage
4. **Backup Important**: Keep backups of critical reports

## Support

For Export API support:

- **Documentation**: Full API docs at `/docs/exports`
- **Troubleshooting**: Export troubleshooting guide
- **Performance**: Export optimization guide
- **Contact**: exports@sagarmatha.ai