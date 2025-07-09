# Widget System Architecture Plan

## Overview
A flexible widget system that allows dynamic data binding and configuration for clinical dashboards.

## Core Concepts

### 1. Widget Definition
Each widget type has:
- **Base Configuration**: Default settings, layout constraints
- **Data Requirements Schema**: What data the widget needs
- **Render Component**: How to display the data
- **Configuration UI**: How users configure the widget

### 2. Data Requirements Model

```typescript
interface WidgetDataRequirement {
  datasets: DatasetRequirement[];
  parameters: ParameterDefinition[];
  calculations: CalculationDefinition[];
}

interface DatasetRequirement {
  alias: string;           // Internal reference name
  datasetType: string;     // ADSL, ADAE, etc.
  required: boolean;
  fields: FieldRequirement[];
  filters?: FilterCondition[];
  joins?: JoinDefinition[];
}

interface FieldRequirement {
  alias: string;           // Internal reference
  description: string;     // User-friendly description
  dataType: 'numeric' | 'string' | 'date' | 'boolean';
  required: boolean;
  allowMultiple?: boolean;
  defaultAggregation?: 'count' | 'sum' | 'avg' | 'min' | 'max';
}
```

### 3. Widget Instance Configuration

When a widget is added to a dashboard:

```typescript
interface WidgetInstance {
  id: string;
  widgetDefinitionId: string;
  position: LayoutPosition;
  dataMapping: DataMapping;
  displayConfig: DisplayConfig;
}

interface DataMapping {
  datasets: {
    [alias: string]: {
      sourceDataset: string;    // Actual dataset in study
      fieldMappings: {
        [fieldAlias: string]: string;  // Actual field name
      };
    };
  };
  parameters: {
    [paramName: string]: any;
  };
}
```

## Implementation Phases

### Phase 1: Widget Definition System

1. **Widget Definition Model**
   - Store widget types with their data requirements
   - Version control for widget definitions
   - Category and type classification

2. **Widget Builder UI**
   - Define data requirements visually
   - Set up calculation logic
   - Configure display options

### Phase 2: Data Binding Framework

1. **Data Requirement Engine**
   - Parse widget data requirements
   - Validate against available study data
   - Generate data fetching queries

2. **Mapping Interface**
   - Visual field mapping
   - Data preview
   - Validation feedback

### Phase 3: Runtime Execution

1. **Data Fetcher Service**
   - Execute queries based on mappings
   - Cache results
   - Handle real-time updates

2. **Widget Renderer**
   - Receive data from fetcher
   - Apply display configuration
   - Handle interactions

## Example: Enrollment Metric Widget

### Widget Definition
```json
{
  "id": "enrollment-metric",
  "name": "Enrollment Metric",
  "type": "metric",
  "dataRequirements": {
    "datasets": [{
      "alias": "subjects",
      "datasetType": "ADSL",
      "required": true,
      "fields": [{
        "alias": "subjectId",
        "description": "Subject Identifier",
        "dataType": "string",
        "required": true
      }, {
        "alias": "enrollmentDate",
        "description": "Enrollment Date",
        "dataType": "date",
        "required": false
      }]
    }],
    "calculations": [{
      "alias": "totalEnrolled",
      "type": "count",
      "field": "subjects.subjectId"
    }]
  }
}
```

### Instance Configuration
```json
{
  "widgetInstanceId": "widget-123",
  "widgetDefinitionId": "enrollment-metric",
  "dataMapping": {
    "datasets": {
      "subjects": {
        "sourceDataset": "MyStudy_ADSL_v2",
        "fieldMappings": {
          "subjectId": "USUBJID",
          "enrollmentDate": "RFSTDTC"
        }
      }
    }
  },
  "displayConfig": {
    "title": "Total Enrolled Subjects",
    "showTrend": true,
    "trendPeriod": "30days"
  }
}
```

## Benefits

1. **Flexibility**: Widgets can work with any study data structure
2. **Reusability**: Widget definitions can be shared across studies
3. **Maintainability**: Clear separation of concerns
4. **Scalability**: Easy to add new widget types
5. **User-Friendly**: Visual mapping interface

## Technical Stack

### Backend
- FastAPI endpoints for widget definitions
- SQL queries generated from data requirements
- Redis caching for widget data
- WebSocket for real-time updates

### Frontend
- React components for widget rendering
- Zustand for widget state management
- React Query for data fetching
- D3.js/Recharts for visualizations

## Migration Path

1. Create widget definition models
2. Build widget definition UI
3. Implement data requirement parser
4. Create mapping interface
5. Build runtime data fetcher
6. Migrate existing widgets to new system

## Security Considerations

1. Row-level security for data access
2. Widget definition permissions
3. Audit trail for configurations
4. Data masking capabilities

## Performance Optimizations

1. Query optimization based on widget requirements
2. Intelligent caching strategies
3. Lazy loading for dashboard widgets
4. Aggregation at database level

## Next Steps

1. Review and refine data requirement model
2. Create database schema for widget definitions
3. Build prototype of widget builder UI
4. Implement data requirement parser
5. Create proof-of-concept with one widget type