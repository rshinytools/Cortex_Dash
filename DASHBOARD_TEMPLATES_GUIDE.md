# Dashboard Templates Guide

## Overview

Dashboard Templates in the Clinical Dashboard Platform are comprehensive configurations that combine:
- Complete menu structures with navigation hierarchy
- Multiple dashboard configurations with embedded widgets
- Data mapping requirements for automatic field detection
- Permission-based visibility rules
- Reusability across multiple studies

## Unified Template Structure

Each dashboard template contains:

### 1. Template Metadata
```json
{
  "code": "oncology_phase3_standard",
  "name": "Oncology Phase 3 Standard",
  "description": "Complete template for Phase 3 oncology studies",
  "category": "overview",
  "version": 1,
  "is_active": true
}
```

### 2. Template Structure
```json
{
  "template_structure": {
    "menu": {
      "items": [...]
    },
    "data_mappings": {
      "required_datasets": [...],
      "field_mappings": {...}
    }
  }
}
```

## Menu Configuration

### Menu Item Types

1. **Dashboard** - Links to a dashboard with embedded configuration
```json
{
  "id": "overview",
  "type": "dashboard",
  "label": "Study Overview",
  "icon": "LayoutDashboard",
  "order": 1,
  "dashboard": {
    "layout": {...},
    "widgets": [...]
  }
}
```

2. **Group** - Container for nested menu items
```json
{
  "id": "safety",
  "type": "group",
  "label": "Safety",
  "icon": "Shield",
  "order": 2,
  "permissions": ["view_safety_data"],
  "children": [...]
}
```

3. **Static Page** - Links to built-in pages
```json
{
  "id": "reports",
  "type": "static_page",
  "label": "Reports",
  "icon": "FileText",
  "page_component": "reports_page",
  "order": 3
}
```

4. **External Link** - Links to external resources
```json
{
  "id": "study_docs",
  "type": "external_link",
  "label": "Study Documents",
  "icon": "ExternalLink",
  "url": "https://docs.example.com",
  "order": 4
}
```

5. **Divider** - Visual separator
```json
{
  "id": "divider1",
  "type": "divider",
  "order": 5
}
```

## Dashboard Configuration

Each dashboard within a menu item includes:

### Layout Configuration
```json
{
  "layout": {
    "type": "grid",
    "columns": 12,
    "rows": 10,
    "gap": 16,
    "breakpoints": {
      "lg": 1200,
      "md": 996,
      "sm": 768,
      "xs": 480
    }
  }
}
```

### Widget Configuration
```json
{
  "widgets": [
    {
      "widget_code": "metric_card",
      "instance_config": {
        "title": "Total Enrolled",
        "icon": "Users"
      },
      "position": {"x": 0, "y": 0, "w": 3, "h": 2},
      "data_requirements": {
        "dataset": "ADSL",
        "fields": ["USUBJID"],
        "calculation": "count_distinct"
      }
    }
  ]
}
```

## Data Requirements

### Data Mappings Structure
```json
{
  "data_mappings": {
    "required_datasets": ["ADSL", "ADAE", "ADLB", "ADRS"],
    "field_mappings": {
      "ADSL": ["USUBJID", "SITEID", "SAFFL", "SCRNFL"],
      "ADAE": ["USUBJID", "AETERM", "AESER"],
      "ADLB": ["USUBJID", "PARAM", "AVAL", "VISITNUM"],
      "ADRS": ["USUBJID", "PARAMCD", "PCHG", "AVALC"]
    }
  }
}
```

### Widget Data Requirements
```json
{
  "data_requirements": {
    "dataset": "ADAE",
    "fields": ["USUBJID", "AETERM"],
    "calculation": "count",
    "filters": [
      {"field": "AESER", "operator": "=", "value": "Y"}
    ]
  }
}
```

## API Endpoints

### Create Template
```http
POST /api/v1/admin/dashboard-templates
Content-Type: application/json

{
  "code": "template_code",
  "name": "Template Name",
  "description": "Template description",
  "category": "overview",
  "template_structure": {...}
}
```

### List Templates
```http
GET /api/v1/admin/dashboard-templates?category=safety&is_active=true
```

### Get Template
```http
GET /api/v1/admin/dashboard-templates/{template_id}
```

### Update Template
```http
PUT /api/v1/admin/dashboard-templates/{template_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "template_structure": {...}
}
```

### Clone Template
```http
POST /api/v1/admin/dashboard-templates/{template_id}/clone
Content-Type: application/json

{
  "new_code": "cloned_template",
  "new_name": "Cloned Template",
  "modifications": {...}
}
```

### Validate Template
```http
POST /api/v1/admin/dashboard-templates/{template_id}/validate
```

### Get Data Requirements
```http
GET /api/v1/admin/dashboard-templates/{template_id}/data-requirements
```

Response:
```json
{
  "template_id": "...",
  "template_code": "oncology_phase3_standard",
  "required_datasets": ["ADSL", "ADAE", "ADLB"],
  "field_mappings": {
    "ADSL": ["USUBJID", "SITEID", "SAFFL"],
    "ADAE": ["USUBJID", "AETERM", "AESER"]
  },
  "widget_requirements": [
    {
      "widget_code": "metric_card",
      "menu_item_id": "overview",
      "requirements": {
        "dataset": "ADSL",
        "fields": ["USUBJID"],
        "calculation": "count"
      }
    }
  ]
}
```

## Study Assignment

### Assign Template to Study
```http
POST /api/v1/studies/{study_id}/dashboard
Content-Type: application/json

{
  "dashboard_template_id": "template_uuid",
  "customizations": {
    "widget_overrides": {...}
  },
  "data_mappings": {
    "dataset_paths": {
      "ADSL": "/data/study_123/adsl.sas7bdat",
      "ADAE": "/data/study_123/adae.sas7bdat"
    }
  }
}
```

## Example: Complete Oncology Template

```json
{
  "code": "oncology_phase3_standard",
  "name": "Oncology Phase 3 Standard",
  "description": "Complete dashboard template for Phase 3 oncology studies",
  "category": "overview",
  "template_structure": {
    "menu": {
      "items": [
        {
          "id": "overview",
          "type": "dashboard",
          "label": "Study Overview",
          "icon": "LayoutDashboard",
          "order": 1,
          "dashboard": {
            "layout": {
              "type": "grid",
              "columns": 12,
              "rows": 10
            },
            "widgets": [
              {
                "widget_code": "metric_card",
                "instance_config": {
                  "title": "Total Enrolled"
                },
                "position": {"x": 0, "y": 0, "w": 3, "h": 2},
                "data_requirements": {
                  "dataset": "ADSL",
                  "fields": ["USUBJID"],
                  "calculation": "count_distinct"
                }
              }
            ]
          }
        },
        {
          "id": "safety",
          "type": "group",
          "label": "Safety",
          "icon": "Shield",
          "order": 2,
          "children": [
            {
              "id": "adverse_events",
              "type": "dashboard",
              "label": "Adverse Events",
              "icon": "AlertTriangle",
              "dashboard": {
                "layout": {
                  "type": "grid",
                  "columns": 12,
                  "rows": 10
                },
                "widgets": [
                  {
                    "widget_code": "data_table",
                    "instance_config": {
                      "title": "Most Common AEs"
                    },
                    "position": {"x": 0, "y": 0, "w": 12, "h": 6},
                    "data_requirements": {
                      "dataset": "ADAE",
                      "fields": ["AETERM", "USUBJID"],
                      "calculation": "frequency_table"
                    }
                  }
                ]
              }
            }
          ]
        }
      ]
    },
    "data_mappings": {
      "required_datasets": ["ADSL", "ADAE"],
      "field_mappings": {
        "ADSL": ["USUBJID", "SITEID"],
        "ADAE": ["USUBJID", "AETERM", "AESER"]
      }
    }
  }
}
```

## Best Practices

1. **Template Organization**
   - Use consistent naming conventions
   - Group related dashboards in menu groups
   - Limit menu depth to 3 levels maximum

2. **Data Requirements**
   - Document all required fields
   - Use standard CDISC naming conventions
   - Include clear calculation specifications

3. **Performance**
   - Limit widgets per dashboard (10-15 max)
   - Use appropriate data aggregations
   - Consider refresh intervals

4. **Reusability**
   - Design templates for common study types
   - Use meaningful codes and descriptions
   - Document customization points

5. **Validation**
   - Always validate templates before use
   - Test with sample data
   - Verify permission requirements