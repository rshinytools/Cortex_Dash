# Widget Configuration Guide

## Overview

This comprehensive guide covers everything you need to know about configuring widgets in the Clinical Dashboard Platform. Whether you're creating new widgets, customizing existing ones, or troubleshooting widget issues, this guide provides step-by-step instructions and best practices for effective widget configuration.

## Table of Contents

1. [Widget Configuration Basics](#widget-configuration-basics)
2. [Widget Types and Configuration](#widget-types-and-configuration)
3. [Data Source Configuration](#data-source-configuration)
4. [Advanced Widget Settings](#advanced-widget-settings)
5. [Widget Interactions and Filtering](#widget-interactions-and-filtering)
6. [Performance Optimization](#performance-optimization)
7. [Widget Templates and Reuse](#widget-templates-and-reuse)
8. [Troubleshooting Widget Issues](#troubleshooting-widget-issues)
9. [Best Practices](#best-practices)
10. [Examples and Use Cases](#examples-and-use-cases)

## Widget Configuration Basics

### Understanding Widgets

Widgets are the fundamental building blocks of dashboards in the Clinical Dashboard Platform. Each widget displays specific data in a particular format and can be configured to meet various analytical needs.

#### Widget Components
Every widget consists of:
- **Data Source**: Where the widget gets its data
- **Configuration**: How the data is processed and displayed
- **Visualization**: The visual representation of the data
- **Interactions**: How users can interact with the widget
- **Filters**: What data subset to display

#### Widget Lifecycle
1. **Creation**: Choose widget type and basic settings
2. **Configuration**: Set up data sources and parameters
3. **Customization**: Adjust appearance and behavior
4. **Testing**: Validate with sample data
5. **Deployment**: Add to dashboard and make available to users
6. **Maintenance**: Regular updates and optimization

### Accessing Widget Configuration

#### Dashboard Designer
1. Navigate to **Dashboard Management** → **Dashboard Designer**
2. Select the dashboard you want to modify
3. Enter **Edit Mode** to enable widget configuration
4. Click on a widget to open its configuration panel

#### Widget Configuration Panel
The configuration panel contains several tabs:
- **Data**: Data source and field selection
- **Display**: Visualization settings and appearance
- **Filters**: Data filtering and parameters
- **Interactions**: Cross-filtering and drill-down settings
- **Advanced**: Performance and technical settings

### Configuration Process

#### Step-by-Step Configuration
1. **Select Widget Type**: Choose the appropriate widget type for your data
2. **Configure Data Source**: Connect to the relevant dataset
3. **Map Fields**: Assign data fields to widget properties
4. **Set Filters**: Apply any necessary data filters
5. **Customize Display**: Adjust visual appearance and formatting
6. **Test Configuration**: Preview with sample data
7. **Save and Deploy**: Apply changes to the dashboard

## Widget Types and Configuration

### Metric Widgets

Metric widgets display single values with optional trend indicators and comparisons.

#### Basic Configuration
```json
{
  "type": "metric",
  "title": "Total Enrolled Subjects",
  "data_source": {
    "dataset": "ADSL",
    "metric_type": "count",
    "field": "USUBJID",
    "distinct": true
  },
  "display": {
    "format": "number",
    "unit": "subjects",
    "show_trend": true,
    "trend_period": "previous_month"
  }
}
```

#### Advanced Metric Configuration
1. **Calculation Types**:
   - **Count**: Count of records
   - **Sum**: Sum of numeric values
   - **Average**: Mean of numeric values
   - **Percentage**: Percentage calculations
   - **Custom**: Formula-based calculations

2. **Trend Configuration**:
   - **Comparison Period**: Previous day/week/month/quarter
   - **Trend Direction**: Up/down/stable indicators
   - **Percentage Change**: Show change as percentage
   - **Absolute Change**: Show absolute difference

3. **Conditional Formatting**:
   ```json
   {
     "conditional_formatting": [
       {
         "condition": "> 100",
         "color": "green",
         "icon": "trending-up"
       },
       {
         "condition": "< 50",
         "color": "red",
         "icon": "alert-triangle"
       }
     ]
   }
   ```

#### Use Case Examples
- **Enrollment Metrics**: Total subjects, screening failure rate
- **Safety Metrics**: AE count, SAE rate, discontinuation rate
- **Data Quality Metrics**: Missing data percentage, query rate
- **Operational Metrics**: Site activation rate, monitoring visit completion

### Chart Widgets

Chart widgets provide visual representations of data trends, comparisons, and distributions.

#### Line Chart Configuration
```json
{
  "type": "chart",
  "chart_type": "line",
  "title": "Enrollment Trend Over Time",
  "data_source": {
    "dataset": "ADSL",
    "x_axis": "RFSTDTC",
    "y_axis": "USUBJID",
    "aggregation": "count",
    "group_by": "SITEID"
  },
  "display": {
    "show_legend": true,
    "show_data_points": true,
    "line_style": "smooth",
    "color_scheme": "category10"
  }
}
```

#### Bar Chart Configuration
```json
{
  "type": "chart",
  "chart_type": "bar",
  "title": "Subjects by Treatment Group",
  "data_source": {
    "dataset": "ADSL",
    "x_axis": "TRT01P",
    "y_axis": "USUBJID",
    "aggregation": "count"
  },
  "display": {
    "orientation": "vertical",
    "show_values": true,
    "bar_spacing": 0.1,
    "color_mapping": {
      "Placebo": "#E8F4FD",
      "Drug A 10mg": "#4FC3F7",
      "Drug A 20mg": "#0277BD"
    }
  }
}
```

#### Pie Chart Configuration
```json
{
  "type": "chart",
  "chart_type": "pie",
  "title": "Demographics Distribution",
  "data_source": {
    "dataset": "ADSL",
    "category_field": "SEX",
    "value_field": "USUBJID",
    "aggregation": "count"
  },
  "display": {
    "show_percentages": true,
    "show_legend": true,
    "donut_style": false,
    "label_threshold": 5
  }
}
```

#### Advanced Chart Features
1. **Multiple Series**:
   ```json
   {
     "series": [
       {
         "name": "Enrolled",
         "field": "ENROLLED_COUNT",
         "type": "bar",
         "color": "#2196F3"
       },
       {
         "name": "Target",
         "field": "TARGET_COUNT",
         "type": "line",
         "color": "#FF9800"
       }
     ]
   }
   ```

2. **Dual Y-Axis**:
   ```json
   {
     "y_axis": {
       "primary": {
         "field": "SUBJECT_COUNT",
         "label": "Number of Subjects"
       },
       "secondary": {
         "field": "PERCENTAGE",
         "label": "Percentage (%)"
       }
     }
   }
   ```

3. **Time Series Features**:
   - Date range selection
   - Zoom and pan capabilities
   - Time period aggregation
   - Moving averages

### Table Widgets

Table widgets display detailed data in tabular format with sorting, filtering, and pagination.

#### Basic Table Configuration
```json
{
  "type": "table",
  "title": "Subject Listing",
  "data_source": {
    "dataset": "ADSL",
    "columns": [
      {
        "field": "USUBJID",
        "label": "Subject ID",
        "type": "string",
        "width": 120
      },
      {
        "field": "AGE",
        "label": "Age",
        "type": "number",
        "format": "0"
      },
      {
        "field": "SEX",
        "label": "Sex",
        "type": "categorical"
      },
      {
        "field": "TRT01P",
        "label": "Treatment",
        "type": "categorical"
      }
    ]
  },
  "display": {
    "page_size": 25,
    "show_pagination": true,
    "enable_sorting": true,
    "enable_filtering": true,
    "enable_export": true
  }
}
```

#### Advanced Table Features
1. **Column Formatting**:
   ```json
   {
     "columns": [
       {
         "field": "AGE",
         "format": {
           "type": "number",
           "decimals": 0,
           "thousands_separator": ","
         }
       },
       {
         "field": "RFSTDTC",
         "format": {
           "type": "date",
           "format": "MM/DD/YYYY"
         }
       },
       {
         "field": "STATUS",
         "format": {
           "type": "conditional",
           "conditions": [
             {"value": "Active", "color": "green"},
             {"value": "Completed", "color": "blue"},
             {"value": "Discontinued", "color": "red"}
           ]
         }
       }
     ]
   }
   ```

2. **Row Actions**:
   ```json
   {
     "row_actions": [
       {
         "label": "View Details",
         "action": "drill_down",
         "target": "subject_detail_dashboard"
       },
       {
         "label": "Export Data",
         "action": "export",
         "format": "csv"
       }
     ]
   }
   ```

3. **Summary Rows**:
   ```json
   {
     "summary": {
       "enabled": true,
       "aggregations": [
         {
           "column": "AGE",
           "function": "average",
           "label": "Mean Age"
         },
         {
           "column": "USUBJID",
           "function": "count",
           "label": "Total Subjects"
         }
       ]
     }
   }
   ```

### Specialized Widgets

#### Timeline Widget
Timeline widgets show events and milestones over time.

```json
{
  "type": "timeline",
  "title": "Study Milestones",
  "data_source": {
    "dataset": "MILESTONES",
    "date_field": "MILESTONE_DATE",
    "event_field": "MILESTONE_NAME",
    "description_field": "DESCRIPTION",
    "category_field": "MILESTONE_TYPE"
  },
  "display": {
    "orientation": "horizontal",
    "show_grid": true,
    "group_by_category": true,
    "date_format": "MMM YYYY"
  }
}
```

#### Map Widget
Map widgets display geographic data and distributions.

```json
{
  "type": "map",
  "title": "Site Locations",
  "data_source": {
    "dataset": "SITES",
    "location_field": "COUNTRY",
    "value_field": "ENROLLED_COUNT",
    "label_field": "SITE_NAME"
  },
  "display": {
    "map_type": "world",
    "color_scale": "blues",
    "show_labels": true,
    "marker_size": "proportional"
  }
}
```

#### KPI Grid Widget
KPI Grid widgets display multiple metrics in a grid layout.

```json
{
  "type": "kpi_grid",
  "title": "Study KPIs",
  "data_source": {
    "metrics": [
      {
        "label": "Total Enrolled",
        "dataset": "ADSL",
        "calculation": "count",
        "field": "USUBJID"
      },
      {
        "label": "Completion Rate",
        "dataset": "ADSL",
        "calculation": "percentage",
        "numerator": "COMPLETED_COUNT",
        "denominator": "ENROLLED_COUNT"
      }
    ]
  },
  "display": {
    "grid_columns": 3,
    "show_trends": true,
    "color_coding": true
  }
}
```

## Data Source Configuration

### Connecting to Data Sources

#### Dataset Selection
1. **Available Datasets**: Browse available datasets for the study
2. **Dataset Preview**: View sample data and field descriptions
3. **Field Mapping**: Map dataset fields to widget properties
4. **Data Validation**: Verify data quality and completeness

#### Field Configuration
```json
{
  "field_mapping": {
    "x_axis": {
      "field": "RFSTDTC",
      "label": "Randomization Date",
      "type": "date",
      "format": "YYYY-MM-DD",
      "validation": {
        "required": true,
        "date_range": {
          "min": "2023-01-01",
          "max": "2025-12-31"
        }
      }
    },
    "y_axis": {
      "field": "USUBJID",
      "label": "Subject ID",
      "type": "string",
      "aggregation": "count_distinct"
    }
  }
}
```

### Data Filtering and Parameters

#### Static Filters
Apply fixed filters to limit the data scope:

```json
{
  "static_filters": [
    {
      "field": "RFSTDTC",
      "operator": ">=",
      "value": "2024-01-01"
    },
    {
      "field": "SAFFL",
      "operator": "=",
      "value": "Y"
    },
    {
      "field": "TRT01P",
      "operator": "in",
      "value": ["Drug A 10mg", "Drug A 20mg", "Placebo"]
    }
  ]
}
```

#### Dynamic Parameters
Create user-controllable parameters:

```json
{
  "parameters": [
    {
      "name": "date_range",
      "label": "Date Range",
      "type": "date_range",
      "default": {
        "start": "2024-01-01",
        "end": "2024-12-31"
      }
    },
    {
      "name": "treatment_group",
      "label": "Treatment Group",
      "type": "multi_select",
      "options": ["Drug A 10mg", "Drug A 20mg", "Placebo"],
      "default": ["Drug A 10mg", "Drug A 20mg", "Placebo"]
    }
  ]
}
```

#### Calculated Fields
Create derived fields for analysis:

```json
{
  "calculated_fields": [
    {
      "name": "AGE_GROUP",
      "expression": "CASE WHEN AGE < 65 THEN 'Under 65' ELSE '65 and Over' END",
      "type": "categorical"
    },
    {
      "name": "STUDY_DAY",
      "expression": "DATEDIFF(CURRENT_DATE, RFSTDTC)",
      "type": "numeric"
    }
  ]
}
```

### Data Refresh and Caching

#### Refresh Settings
```json
{
  "refresh_settings": {
    "auto_refresh": true,
    "refresh_interval": "15_minutes",
    "refresh_on_filter_change": true,
    "refresh_on_parameter_change": true
  }
}
```

#### Caching Configuration
```json
{
  "cache_settings": {
    "cache_enabled": true,
    "cache_duration": "1_hour",
    "cache_key_fields": ["study_id", "date_range"],
    "invalidate_on_data_update": true
  }
}
```

## Advanced Widget Settings

### Performance Optimization

#### Query Optimization
1. **Index Usage**: Ensure proper database indexes
2. **Field Selection**: Only request necessary fields
3. **Aggregation**: Perform aggregations at the database level
4. **Pagination**: Implement server-side pagination for large datasets

#### Memory Management
```json
{
  "performance_settings": {
    "max_rows": 10000,
    "streaming_enabled": true,
    "lazy_loading": true,
    "memory_limit_mb": 256
  }
}
```

#### Progressive Loading
```json
{
  "progressive_loading": {
    "enabled": true,
    "initial_rows": 100,
    "increment_size": 50,
    "auto_load_threshold": 10
  }
}
```

### Styling and Theming

#### Custom Styling
```json
{
  "styling": {
    "theme": "custom",
    "colors": {
      "primary": "#1976D2",
      "secondary": "#424242",
      "success": "#4CAF50",
      "warning": "#FF9800",
      "error": "#F44336"
    },
    "fonts": {
      "title": {
        "family": "Roboto",
        "size": "18px",
        "weight": "bold"
      },
      "body": {
        "family": "Roboto",
        "size": "14px",
        "weight": "normal"
      }
    }
  }
}
```

#### Responsive Design
```json
{
  "responsive": {
    "enabled": true,
    "breakpoints": {
      "mobile": {
        "max_width": "768px",
        "layout": "stack",
        "font_scale": 0.9
      },
      "tablet": {
        "max_width": "1024px",
        "layout": "adapt",
        "font_scale": 1.0
      }
    }
  }
}
```

### Security and Access Control

#### Data Security
```json
{
  "security": {
    "data_masking": {
      "enabled": true,
      "mask_pii": true,
      "mask_patterns": ["XXX-XX-****"]
    },
    "row_level_security": {
      "enabled": true,
      "filter_expression": "SITE_ID IN (user.accessible_sites)"
    }
  }
}
```

#### Export Controls
```json
{
  "export_controls": {
    "allow_export": true,
    "allowed_formats": ["csv", "excel"],
    "max_export_rows": 50000,
    "watermark": true,
    "audit_exports": true
  }
}
```

## Widget Interactions and Filtering

### Cross-Widget Filtering

#### Filter Propagation
Configure how widget selections affect other widgets:

```json
{
  "filter_propagation": {
    "enabled": true,
    "target_widgets": ["related_chart", "detail_table"],
    "filter_mappings": [
      {
        "source_field": "TRT01P",
        "target_field": "TRT01P",
        "operation": "equal"
      }
    ]
  }
}
```

#### Global Filters
Set up dashboard-level filters that affect multiple widgets:

```json
{
  "global_filter_bindings": [
    {
      "parameter": "study_date_range",
      "field": "RFSTDTC",
      "operation": "between"
    },
    {
      "parameter": "selected_sites",
      "field": "SITEID",
      "operation": "in"
    }
  ]
}
```

### Drill-Down Configuration

#### Drill-Down Actions
```json
{
  "drill_down": {
    "enabled": true,
    "actions": [
      {
        "trigger": "click",
        "target": "subject_detail_dashboard",
        "parameters": {
          "subject_id": "${USUBJID}",
          "visit_date": "${VISIT_DATE}"
        }
      }
    ]
  }
}
```

#### Detail Views
```json
{
  "detail_views": [
    {
      "trigger": "double_click",
      "type": "modal",
      "content": {
        "widget_type": "table",
        "data_source": "detailed_view_query",
        "filters": {
          "inherited": true,
          "additional": [
            {
              "field": "DETAIL_FLAG",
              "value": "Y"
            }
          ]
        }
      }
    }
  ]
}
```

### Interactive Features

#### User Controls
```json
{
  "user_controls": [
    {
      "type": "date_picker",
      "label": "Select Date Range",
      "parameter": "date_range",
      "position": "top"
    },
    {
      "type": "dropdown",
      "label": "Treatment Group",
      "parameter": "treatment",
      "options": "dynamic",
      "source": "TRT01P_values"
    }
  ]
}
```

#### Widget Actions
```json
{
  "widget_actions": [
    {
      "label": "Refresh Data",
      "action": "refresh",
      "icon": "refresh"
    },
    {
      "label": "Export Chart",
      "action": "export",
      "options": ["png", "svg", "pdf"]
    },
    {
      "label": "Full Screen",
      "action": "fullscreen",
      "icon": "expand"
    }
  ]
}
```

## Performance Optimization

### Query Performance

#### Efficient Data Retrieval
1. **Index Optimization**: Ensure proper indexing on filtered fields
2. **Query Simplification**: Avoid complex joins when possible
3. **Aggregation**: Use database-level aggregations
4. **Partitioning**: Leverage table partitioning for large datasets

#### SQL Query Optimization
```sql
-- Optimized query example
SELECT 
    DATE_TRUNC('month', RFSTDTC) as month,
    TRT01P,
    COUNT(DISTINCT USUBJID) as subject_count
FROM ADSL 
WHERE RFSTDTC >= '2024-01-01'
    AND SAFFL = 'Y'
GROUP BY DATE_TRUNC('month', RFSTDTC), TRT01P
ORDER BY month, TRT01P;
```

### Frontend Performance

#### Data Loading Strategies
```json
{
  "loading_strategy": {
    "type": "progressive",
    "initial_load": 100,
    "chunk_size": 50,
    "prefetch_next": true,
    "virtual_scrolling": true
  }
}
```

#### Rendering Optimization
```json
{
  "rendering": {
    "use_canvas": true,
    "animation_duration": 300,
    "debounce_resize": 250,
    "throttle_updates": 100
  }
}
```

### Memory Management

#### Large Dataset Handling
```json
{
  "large_dataset_config": {
    "streaming": true,
    "buffer_size": 1000,
    "memory_threshold": "100MB",
    "compression": "gzip",
    "partial_loading": true
  }
}
```

## Widget Templates and Reuse

### Creating Widget Templates

#### Template Definition
```json
{
  "template": {
    "name": "Enrollment Trend Chart",
    "description": "Standard enrollment tracking chart",
    "category": "operational",
    "version": "1.0",
    "parameters": [
      {
        "name": "dataset",
        "type": "dataset_selector",
        "required": true,
        "default": "ADSL"
      },
      {
        "name": "date_field",
        "type": "field_selector",
        "field_type": "date",
        "required": true
      }
    ],
    "configuration": {
      "type": "chart",
      "chart_type": "line",
      "data_source": {
        "dataset": "{{dataset}}",
        "x_axis": "{{date_field}}",
        "y_axis": "USUBJID",
        "aggregation": "count"
      }
    }
  }
}
```

#### Template Inheritance
```json
{
  "extends": "base_chart_template",
  "overrides": {
    "chart_type": "bar",
    "display.orientation": "horizontal"
  },
  "additional_config": {
    "custom_colors": true,
    "show_data_labels": true
  }
}
```

### Template Marketplace

#### Publishing Templates
1. **Template Validation**: Ensure template works with sample data
2. **Documentation**: Provide clear usage instructions
3. **Testing**: Test with multiple datasets and scenarios
4. **Versioning**: Implement proper version control
5. **Publishing**: Submit to template marketplace

#### Using Marketplace Templates
1. **Browse Templates**: Search marketplace by category or keyword
2. **Preview**: View template preview and documentation
3. **Install**: Add template to your organization
4. **Customize**: Adapt template to your specific needs
5. **Deploy**: Use template in your dashboards

## Troubleshooting Widget Issues

### Common Configuration Issues

#### Data Connection Problems
**Issue**: Widget shows "No data available"
**Solutions**:
1. Verify data source connection
2. Check field mappings
3. Review applied filters
4. Validate data permissions

**Issue**: Slow widget loading
**Solutions**:
1. Optimize queries
2. Add appropriate filters
3. Increase cache duration
4. Consider data aggregation

#### Display Issues
**Issue**: Chart not rendering correctly
**Solutions**:
1. Check data types and formats
2. Verify chart configuration
3. Review browser compatibility
4. Check for JavaScript errors

**Issue**: Incorrect data aggregation
**Solutions**:
1. Verify aggregation settings
2. Check for duplicate records
3. Review group-by fields
4. Validate calculation logic

### Error Messages and Solutions

#### Configuration Errors
| Error Message | Cause | Solution |
|---------------|-------|----------|
| "Invalid field mapping" | Field doesn't exist in dataset | Check field names and dataset |
| "Aggregation failed" | Invalid aggregation function | Use supported aggregation types |
| "Filter syntax error" | Malformed filter expression | Review filter syntax |
| "Data type mismatch" | Wrong data type for operation | Verify field data types |

#### Runtime Errors
| Error Message | Cause | Solution |
|---------------|-------|----------|
| "Query timeout" | Query taking too long | Optimize query or add filters |
| "Memory limit exceeded" | Dataset too large | Implement pagination or filtering |
| "Permission denied" | Insufficient data access | Check user permissions |
| "Data source unavailable" | Connection issues | Verify data source status |

### Debugging Tools

#### Widget Inspector
1. **Data Preview**: View raw data returned by widget
2. **Query Analysis**: Examine generated SQL queries
3. **Performance Metrics**: Review execution times and resource usage
4. **Error Logs**: Access detailed error information

#### Testing Features
```json
{
  "testing": {
    "mock_data": true,
    "performance_profiling": true,
    "query_logging": true,
    "memory_monitoring": true
  }
}
```

## Best Practices

### Configuration Best Practices

#### Data Source Management
1. **Field Validation**: Always validate field mappings
2. **Performance Testing**: Test with realistic data volumes
3. **Error Handling**: Implement proper error handling
4. **Documentation**: Document custom configurations

#### User Experience
1. **Loading States**: Provide clear loading indicators
2. **Error Messages**: Show user-friendly error messages
3. **Responsive Design**: Ensure widgets work on all devices
4. **Accessibility**: Follow accessibility guidelines

#### Security Considerations
1. **Data Privacy**: Implement appropriate data masking
2. **Access Controls**: Restrict sensitive data access
3. **Audit Trails**: Log all configuration changes
4. **Compliance**: Follow regulatory requirements

### Performance Best Practices

#### Query Optimization
1. **Index Usage**: Leverage database indexes
2. **Filter Early**: Apply filters at the database level
3. **Aggregate Smart**: Use appropriate aggregation levels
4. **Cache Effectively**: Implement intelligent caching

#### Frontend Optimization
1. **Lazy Loading**: Load data only when needed
2. **Virtual Scrolling**: Handle large datasets efficiently
3. **Debouncing**: Prevent excessive API calls
4. **Memory Management**: Clean up unused resources

### Maintenance Best Practices

#### Regular Maintenance
1. **Performance Review**: Regularly review widget performance
2. **User Feedback**: Collect and act on user feedback
3. **Data Quality**: Monitor data quality metrics
4. **Security Updates**: Keep security configurations current

#### Configuration Management
1. **Version Control**: Track configuration changes
2. **Testing**: Test changes in staging environment
3. **Documentation**: Keep documentation up to date
4. **Backup**: Maintain configuration backups

## Examples and Use Cases

### Safety Monitoring Dashboard

#### Adverse Events Summary Widget
```json
{
  "type": "kpi_grid",
  "title": "Safety Summary",
  "data_source": {
    "metrics": [
      {
        "label": "Total AEs",
        "dataset": "ADAE",
        "calculation": "count",
        "field": "AESEQ"
      },
      {
        "label": "SAE Rate",
        "dataset": "ADAE",
        "calculation": "percentage",
        "numerator_filter": "AESER = 'Y'",
        "denominator": "USUBJID",
        "distinct": true
      },
      {
        "label": "Discontinuation Rate",
        "dataset": "ADSL",
        "calculation": "percentage",
        "numerator_filter": "DCSREAS IS NOT NULL",
        "denominator": "USUBJID"
      }
    ]
  },
  "display": {
    "grid_columns": 3,
    "color_coding": {
      "thresholds": [
        {"value": 5, "color": "green"},
        {"value": 10, "color": "yellow"},
        {"value": 15, "color": "red"}
      ]
    }
  }
}
```

#### AE Trend Chart
```json
{
  "type": "chart",
  "chart_type": "line",
  "title": "AE Reporting Trend",
  "data_source": {
    "dataset": "ADAE",
    "x_axis": "ASTDT",
    "y_axis": "AESEQ",
    "aggregation": "count",
    "group_by": "AESOC",
    "date_aggregation": "week"
  },
  "display": {
    "show_legend": true,
    "line_style": "smooth",
    "markers": true,
    "color_scheme": "safety_colors"
  },
  "interactions": {
    "drill_down": {
      "target": "ae_detail_table",
      "parameters": {
        "soc": "${AESOC}",
        "date_range": "${selected_date_range}"
      }
    }
  }
}
```

### Enrollment Dashboard

#### Site Performance Table
```json
{
  "type": "table",
  "title": "Site Enrollment Performance",
  "data_source": {
    "dataset": "ENROLLMENT_SUMMARY",
    "columns": [
      {
        "field": "SITEID",
        "label": "Site",
        "type": "string"
      },
      {
        "field": "ENROLLED_COUNT",
        "label": "Enrolled",
        "type": "number"
      },
      {
        "field": "TARGET_COUNT",
        "label": "Target",
        "type": "number"
      },
      {
        "field": "COMPLETION_RATE",
        "label": "% Complete",
        "type": "percentage",
        "format": "0.1%"
      },
      {
        "field": "LAST_ENROLLMENT",
        "label": "Last Enrollment",
        "type": "date"
      }
    ]
  },
  "display": {
    "conditional_formatting": [
      {
        "column": "COMPLETION_RATE",
        "condition": "> 90%",
        "background_color": "#E8F5E8",
        "text_color": "#2E7D32"
      },
      {
        "column": "COMPLETION_RATE",
        "condition": "< 50%",
        "background_color": "#FFEBEE",
        "text_color": "#C62828"
      }
    ]
  }
}
```

### Efficacy Analysis Dashboard

#### Primary Endpoint Analysis
```json
{
  "type": "chart",
  "chart_type": "box_plot",
  "title": "Primary Endpoint by Treatment Group",
  "data_source": {
    "dataset": "ADEFF",
    "x_axis": "TRT01P",
    "y_axis": "AVAL",
    "category": "PARAMCD",
    "filter": "PARAMCD = 'PRIMARY_ENDPOINT'"
  },
  "display": {
    "show_outliers": true,
    "show_mean": true,
    "color_by_group": true,
    "statistical_annotations": true
  },
  "statistics": {
    "p_value_display": true,
    "confidence_intervals": 95,
    "multiple_comparisons": "tukey"
  }
}
```

---

## Quick Reference

### Widget Configuration Checklist
- [ ] Select appropriate widget type for data
- [ ] Configure data source and field mappings
- [ ] Set up filters and parameters
- [ ] Customize display settings
- [ ] Test with sample data
- [ ] Optimize for performance
- [ ] Document configuration
- [ ] Deploy to dashboard

### Common Configuration Patterns
- **Metric Widget**: Count, percentage, trend comparison
- **Chart Widget**: Time series, category comparison, distribution
- **Table Widget**: Detailed listings, summary tables
- **Filter Widget**: Date range, category selection
- **KPI Grid**: Multiple metrics overview

### Performance Guidelines
- **Query Optimization**: Use indexes, limit data, aggregate efficiently
- **Caching**: Enable appropriate cache settings
- **Loading**: Implement progressive loading for large datasets
- **Rendering**: Use efficient visualization libraries

### Support Resources
- **Widget Documentation**: Detailed widget type documentation
- **API Reference**: Widget configuration API reference
- **Best Practices**: Configuration best practices guide
- **Community Forums**: User community and support forums
- **Training**: Widget configuration training materials

---

*This guide provides comprehensive coverage of widget configuration. For specific technical issues or advanced configurations, consult the developer documentation or contact technical support.*