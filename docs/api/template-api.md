# Template API Documentation

## Overview

The Template API provides comprehensive functionality for managing dashboard templates in the Clinical Dashboard Platform. Templates enable rapid deployment of standardized dashboards across studies, therapeutic areas, and organizations.

## Table of Contents

1. [Authentication](#authentication)
2. [Template Management](#template-management)
3. [Template Categories](#template-categories)
4. [Template Publishing](#template-publishing)
5. [Template Import/Export](#template-importexport)
6. [Version Management](#version-management)
7. [Template Marketplace](#template-marketplace)
8. [Examples](#examples)

## Authentication

All Template API endpoints require authentication using Bearer tokens:

```http
Authorization: Bearer <your-jwt-token>
```

## Template Management

### List Dashboard Templates

Retrieve available dashboard templates with filtering options.

**Endpoint:** `GET /api/v1/dashboard-templates`

**Parameters:**
- `category` (optional): Filter by template category
- `therapeutic_area` (optional): Filter by therapeutic area
- `study_phase` (optional): Filter by study phase (`phase-1`, `phase-2`, `phase-3`, `phase-4`)
- `is_public` (optional): Filter public/private templates
- `organization_id` (optional): Filter by organization
- `page` (optional): Page number for pagination (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Response:**
```json
{
  "templates": [
    {
      "id": "uuid",
      "name": "Phase 2 Safety Dashboard",
      "description": "Comprehensive safety monitoring for Phase 2 studies",
      "category": "safety",
      "therapeutic_area": "oncology",
      "study_phase": "phase-2",
      "version": "1.2.0",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-02-01T14:20:00Z",
      "is_public": true,
      "usage_count": 245,
      "rating": 4.8,
      "preview_image": "https://cdn.cortexdash.com/templates/phase2-safety.png",
      "author": {
        "name": "Clinical Template Team",
        "organization": "Sagarmatha AI"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "pages": 3
  }
}
```

### Get Template Details

Retrieve detailed information about a specific template including full configuration.

**Endpoint:** `GET /api/v1/dashboard-templates/{template_id}`

**Parameters:**
- `template_id` (path): Template UUID
- `include_widgets` (query, optional): Include widget configurations (`true`/`false`, default: `true`)
- `include_data_requirements` (query, optional): Include data requirements (`true`/`false`, default: `true`)

**Response:**
```json
{
  "id": "uuid",
  "name": "Phase 2 Safety Dashboard",
  "description": "Comprehensive safety monitoring dashboard...",
  "category": "safety",
  "therapeutic_area": "oncology",
  "study_phase": "phase-2",
  "version": "1.2.0",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-02-01T14:20:00Z",
  "is_public": true,
  "widgets": [
    {
      "id": "widget-uuid-1",
      "type": "metric",
      "title": "Total AEs",
      "config": {
        "metric": "count",
        "dataset": "ADAE",
        "field": "AESEQ"
      },
      "position": {
        "x": 0,
        "y": 0,
        "w": 3,
        "h": 2
      }
    }
  ],
  "layout": {
    "type": "grid",
    "grid_settings": {
      "cols": 12,
      "row_height": 60,
      "margin": [10, 10],
      "container_padding": [10, 10]
    }
  },
  "data_requirements": [
    {
      "dataset": "ADAE",
      "required_fields": ["USUBJID", "AESEQ", "AEDECOD"],
      "optional_fields": ["AESOC", "AESER", "ASTDT"]
    }
  ],
  "metadata": {
    "documentation_url": "https://docs.cortexdash.com/templates/phase2-safety",
    "changelog": "Added new SAE tracking widget",
    "tags": ["safety", "phase-2", "monitoring"]
  }
}
```

### Create Template

Create a new dashboard template.

**Endpoint:** `POST /api/v1/dashboard-templates`

**Request Body:**
```json
{
  "name": "Custom Safety Dashboard",
  "description": "Custom safety monitoring dashboard for oncology studies",
  "category": "safety",
  "therapeutic_area": "oncology",
  "study_phase": "phase-2",
  "is_public": false,
  "widgets": [
    {
      "type": "metric",
      "title": "Total AEs",
      "config": {
        "metric": "count",
        "dataset": "ADAE",
        "field": "AESEQ"
      },
      "position": {
        "x": 0,
        "y": 0,
        "w": 3,
        "h": 2
      }
    }
  ],
  "layout": {
    "type": "grid",
    "grid_settings": {
      "cols": 12,
      "row_height": 60
    }
  },
  "data_requirements": [
    {
      "dataset": "ADAE",
      "required_fields": ["USUBJID", "AESEQ", "AEDECOD"]
    }
  ]
}
```

**Response:**
```json
{
  "id": "new-template-uuid",
  "name": "Custom Safety Dashboard",
  "version": "1.0.0",
  "created_at": "2024-01-15T10:30:00Z",
  "status": "draft",
  "validation": {
    "is_valid": true,
    "errors": [],
    "warnings": []
  }
}
```

### Update Template

Update an existing template.

**Endpoint:** `PUT /api/v1/dashboard-templates/{template_id}`

**Request Body:** Same as create template

**Response:**
```json
{
  "id": "template-uuid",
  "name": "Updated Template Name",
  "version": "1.1.0",
  "updated_at": "2024-01-15T10:30:00Z",
  "status": "draft",
  "changes": [
    "Added new widget: Patient Timeline",
    "Updated layout configuration",
    "Modified data requirements"
  ]
}
```

### Delete Template

Delete a template (soft delete for published templates).

**Endpoint:** `DELETE /api/v1/dashboard-templates/{template_id}`

**Response:**
```json
{
  "id": "template-uuid",
  "status": "deleted",
  "deleted_at": "2024-01-15T10:30:00Z",
  "can_restore": true
}
```

## Template Categories

### Standard Categories

| Category | Description | Common Use Cases |
|----------|-------------|------------------|
| `safety` | Safety monitoring | AE tracking, SAE alerts, safety run-in |
| `efficacy` | Efficacy analysis | Primary endpoints, biomarkers |
| `enrollment` | Enrollment tracking | Site performance, recruitment |
| `operational` | Study operations | Site monitoring, data quality |
| `regulatory` | Regulatory reporting | Submission-ready reports |
| `executive` | Executive overview | High-level KPIs, study status |

### Get Categories

Retrieve available template categories with counts.

**Endpoint:** `GET /api/v1/dashboard-templates/categories`

**Response:**
```json
{
  "categories": [
    {
      "name": "safety",
      "display_name": "Safety Monitoring",
      "description": "Templates for safety data monitoring",
      "template_count": 15,
      "icon": "shield-check"
    },
    {
      "name": "efficacy",
      "display_name": "Efficacy Analysis",
      "description": "Templates for efficacy endpoint analysis",
      "template_count": 12,
      "icon": "trending-up"
    }
  ]
}
```

## Template Publishing

### Validate Template

Validate a template before publishing.

**Endpoint:** `POST /api/v1/dashboard-templates/{template_id}/validate`

**Response:**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [
    {
      "widget_id": "widget-uuid",
      "message": "Chart widget may perform slowly with large datasets"
    }
  ],
  "suggestions": [
    {
      "field": "layout.grid_settings.row_height",
      "message": "Consider increasing row height for better readability"
    }
  ],
  "data_validation": {
    "required_datasets": ["ADAE", "ADSL"],
    "missing_fields": [],
    "field_compatibility": "100%"
  }
}
```

### Publish Template

Publish a template to make it available to other users.

**Endpoint:** `POST /api/v1/dashboard-templates/{template_id}/publish`

**Request Body:**
```json
{
  "is_public": true,
  "marketplace_metadata": {
    "tags": ["safety", "monitoring", "phase-2"],
    "documentation_url": "https://docs.example.com/template",
    "support_contact": "support@organization.com"
  },
  "version_notes": "Initial public release with enhanced safety widgets"
}
```

**Response:**
```json
{
  "id": "template-uuid",
  "status": "published",
  "published_at": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "marketplace_url": "https://marketplace.cortexdash.com/templates/template-uuid"
}
```

### Unpublish Template

Remove a template from public availability.

**Endpoint:** `POST /api/v1/dashboard-templates/{template_id}/unpublish`

**Request Body:**
```json
{
  "reason": "Template needs updates for regulatory compliance"
}
```

## Template Import/Export

### Export Template

Export a template for backup or sharing.

**Endpoint:** `GET /api/v1/dashboard-templates/{template_id}/export`

**Parameters:**
- `format` (query): Export format (`json`, `yaml`) - default: `json`
- `include_metadata` (query): Include export metadata (`true`/`false`) - default: `true`
- `include_preview` (query): Include preview images (`true`/`false`) - default: `false`

**Response:**
```json
{
  "template": {
    "metadata": {
      "name": "Phase 2 Safety Dashboard",
      "description": "...",
      "version": "1.2.0"
    },
    "configuration": {
      "widgets": [...],
      "layout": {...},
      "data_requirements": [...]
    }
  },
  "export_metadata": {
    "exported_at": "2024-01-15T10:30:00Z",
    "exported_by": "user@organization.com",
    "format": "json",
    "version": "1.0",
    "compatibility": {
      "min_platform_version": "5.0.0",
      "max_platform_version": null
    }
  }
}
```

### Import Template

Import a template from a file or URL.

**Endpoint:** `POST /api/v1/dashboard-templates/import`

**Request Body:**
```json
{
  "source": "file|url",
  "data": "base64-encoded-template-data",
  "url": "https://example.com/template.json",
  "import_options": {
    "overwrite_existing": false,
    "create_copy": true,
    "prefix_name": "Imported: "
  },
  "validation_mode": "strict|lenient"
}
```

**Response:**
```json
{
  "import_id": "import-uuid",
  "status": "processing",
  "template_id": "new-template-uuid",
  "validation": {
    "is_valid": true,
    "errors": [],
    "warnings": [
      "Template references widget types not available in this version"
    ]
  },
  "estimated_completion": "2024-01-15T10:30:30Z"
}
```

### Get Import Status

Check the status of a template import operation.

**Endpoint:** `GET /api/v1/dashboard-templates/import/{import_id}/status`

**Response:**
```json
{
  "import_id": "import-uuid",
  "status": "completed|processing|failed",
  "progress": 100,
  "template_id": "new-template-uuid",
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:30:30Z",
  "errors": [],
  "result": {
    "widgets_imported": 8,
    "widgets_skipped": 1,
    "data_sources_mapped": 3
  }
}
```

## Version Management

### List Template Versions

Get version history for a template.

**Endpoint:** `GET /api/v1/dashboard-templates/{template_id}/versions`

**Response:**
```json
{
  "template_id": "template-uuid",
  "current_version": "1.2.0",
  "versions": [
    {
      "version": "1.2.0",
      "created_at": "2024-02-01T14:20:00Z",
      "created_by": "user@organization.com",
      "changes": [
        "Added new SAE tracking widget",
        "Updated chart color scheme",
        "Fixed data filtering bug"
      ],
      "is_published": true,
      "download_count": 45
    },
    {
      "version": "1.1.0",
      "created_at": "2024-01-20T09:15:00Z",
      "created_by": "user@organization.com",
      "changes": [
        "Added enrollment trend chart",
        "Improved responsive layout"
      ],
      "is_published": false,
      "download_count": 12
    }
  ]
}
```

### Create Version

Create a new version of a template.

**Endpoint:** `POST /api/v1/dashboard-templates/{template_id}/versions`

**Request Body:**
```json
{
  "version_type": "major|minor|patch",
  "changes": [
    "Added new safety metrics",
    "Updated chart configurations"
  ],
  "template_data": {
    "widgets": [...],
    "layout": {...}
  }
}
```

**Response:**
```json
{
  "template_id": "template-uuid",
  "version": "1.3.0",
  "created_at": "2024-01-15T10:30:00Z",
  "status": "draft"
}
```

### Revert to Version

Revert a template to a previous version.

**Endpoint:** `POST /api/v1/dashboard-templates/{template_id}/versions/{version}/revert`

**Response:**
```json
{
  "template_id": "template-uuid",
  "reverted_to": "1.1.0",
  "new_version": "1.3.1",
  "reverted_at": "2024-01-15T10:30:00Z"
}
```

## Template Marketplace

### Browse Marketplace

Browse public templates in the marketplace.

**Endpoint:** `GET /api/v1/template-marketplace`

**Parameters:**
- `category` (optional): Filter by category
- `therapeutic_area` (optional): Filter by therapeutic area
- `rating_min` (optional): Minimum rating (1-5)
- `sort` (optional): Sort by (`popularity`, `rating`, `recent`, `name`)
- `search` (optional): Search query

**Response:**
```json
{
  "templates": [
    {
      "id": "marketplace-template-uuid",
      "name": "FDA Submission Dashboard",
      "description": "Regulatory-ready dashboard for FDA submissions",
      "category": "regulatory",
      "therapeutic_area": "general",
      "rating": 4.9,
      "download_count": 1250,
      "last_updated": "2024-01-15T10:30:00Z",
      "author": {
        "name": "Regulatory Solutions Inc.",
        "verified": true,
        "rating": 4.8
      },
      "preview_images": [
        "https://cdn.cortexdash.com/marketplace/fda-dashboard-1.png"
      ],
      "price": {
        "type": "free|premium",
        "amount": 0,
        "currency": "USD"
      }
    }
  ],
  "featured": ["template-uuid-1", "template-uuid-2"],
  "categories": ["safety", "efficacy", "regulatory"],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 156
  }
}
```

### Install Template

Install a template from the marketplace.

**Endpoint:** `POST /api/v1/template-marketplace/{template_id}/install`

**Request Body:**
```json
{
  "install_options": {
    "customize_name": "My Custom FDA Dashboard",
    "organization_private": true,
    "auto_update": false
  }
}
```

**Response:**
```json
{
  "installation_id": "install-uuid",
  "template_id": "new-template-uuid",
  "status": "installing",
  "estimated_completion": "2024-01-15T10:30:15Z"
}
```

### Rate Template

Rate and review a marketplace template.

**Endpoint:** `POST /api/v1/template-marketplace/{template_id}/rate`

**Request Body:**
```json
{
  "rating": 5,
  "review": "Excellent template, saved us weeks of development time!",
  "recommend": true
}
```

**Response:**
```json
{
  "rating_id": "rating-uuid",
  "submitted_at": "2024-01-15T10:30:00Z",
  "status": "published"
}
```

## Examples

### Create and Publish a Template

```javascript
// 1. Create template
const template = await fetch('/api/v1/dashboard-templates', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Safety Monitoring Dashboard',
    description: 'Comprehensive safety monitoring for Phase 2 studies',
    category: 'safety',
    therapeutic_area: 'oncology',
    study_phase: 'phase-2',
    widgets: [
      {
        type: 'metric',
        title: 'Total AEs',
        config: {
          metric: 'count',
          dataset: 'ADAE',
          field: 'AESEQ'
        },
        position: { x: 0, y: 0, w: 3, h: 2 }
      }
    ],
    layout: {
      type: 'grid',
      grid_settings: {
        cols: 12,
        row_height: 60
      }
    }
  })
});

const templateResult = await template.json();
const templateId = templateResult.id;

// 2. Validate template
const validation = await fetch(`/api/v1/dashboard-templates/${templateId}/validate`, {
  method: 'POST'
});

const validationResult = await validation.json();
if (validationResult.is_valid) {
  // 3. Publish template
  const publish = await fetch(`/api/v1/dashboard-templates/${templateId}/publish`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      is_public: true,
      marketplace_metadata: {
        tags: ['safety', 'monitoring', 'phase-2']
      }
    })
  });
}
```

### Import and Customize Template

```javascript
// 1. Import template from file
const importData = new FormData();
importData.append('file', templateFile);
importData.append('import_options', JSON.stringify({
  create_copy: true,
  prefix_name: 'Custom: '
}));

const importResponse = await fetch('/api/v1/dashboard-templates/import', {
  method: 'POST',
  body: importData
});

const importResult = await importResponse.json();

// 2. Monitor import progress
const checkImport = async (importId) => {
  const status = await fetch(`/api/v1/dashboard-templates/import/${importId}/status`);
  return status.json();
};

// 3. Customize imported template
const templateId = importResult.template_id;
const customization = await fetch(`/api/v1/dashboard-templates/${templateId}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Customized Safety Dashboard',
    widgets: [
      // Add custom widgets
    ]
  })
});
```

### Browse and Install from Marketplace

```javascript
// 1. Browse marketplace
const marketplace = await fetch('/api/v1/template-marketplace?category=safety&sort=popularity');
const templates = await marketplace.json();

// 2. Get template details
const templateId = templates.templates[0].id;
const details = await fetch(`/api/v1/template-marketplace/${templateId}`);
const templateDetails = await details.json();

// 3. Install template
const install = await fetch(`/api/v1/template-marketplace/${templateId}/install`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    install_options: {
      customize_name: 'My Safety Dashboard',
      organization_private: true
    }
  })
});

const installation = await install.json();

// 4. Rate template after use
const rating = await fetch(`/api/v1/template-marketplace/${templateId}/rate`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    rating: 5,
    review: 'Great template for safety monitoring!'
  })
});
```

## Best Practices

### Template Design

1. **Modular Widgets**: Design widgets to be independently functional
2. **Responsive Layout**: Ensure templates work on different screen sizes
3. **Data Flexibility**: Use parameterized data sources when possible
4. **Documentation**: Provide clear documentation and usage instructions

### Version Management

1. **Semantic Versioning**: Use semantic versioning (major.minor.patch)
2. **Change Documentation**: Document all changes between versions
3. **Backward Compatibility**: Maintain compatibility when possible
4. **Testing**: Test templates thoroughly before publishing

### Performance

1. **Widget Optimization**: Optimize widgets for expected data volumes
2. **Layout Efficiency**: Use efficient layout configurations
3. **Data Requirements**: Minimize required data sources
4. **Caching**: Design for effective caching strategies

### Security and Compliance

1. **Access Controls**: Respect organization and study permissions
2. **Data Privacy**: Ensure templates don't expose sensitive data
3. **Validation**: Validate all template configurations
4. **Audit Trail**: Maintain audit trails for template changes

## Rate Limits

- **Template operations**: 60 requests per minute per user
- **Import/Export**: 10 operations per minute per user
- **Marketplace browse**: 120 requests per minute per user
- **Publishing**: 5 operations per minute per user

## Support

For Template API support:

- **Documentation**: Full API docs at `/docs/templates`
- **Examples**: Template examples repository
- **Community**: Template marketplace community forum
- **Contact**: templates@sagarmatha.ai