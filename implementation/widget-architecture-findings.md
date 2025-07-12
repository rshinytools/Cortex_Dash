# Widget Architecture Findings from Old Codebase

## Key Insights

### 1. Data Flow Architecture

The old system uses a sophisticated data pipeline:

```
PyArrow Files → API Endpoints → Frontend Services → Widget Components
```

**Backend Data Processing:**
- Uses PyArrow for efficient data handling with parquet files
- Supports complex filtering with PyArrow expressions
- Handles pagination at the API level
- Provides aggregation endpoints for specific metrics

**API Patterns:**
- `/api/analysis/trends/enrollment_screening` - Returns time series data
- `/api/analysis/adam/adsl/site_screening_summary` - Returns aggregated site data
- `/api/data/adam/{dataset}` - Generic paginated data retrieval
- `/api/data/sdtm/{dataset}` - SDTM data retrieval with filtering

### 2. Widget Data Consumption Patterns

**Metrics Widgets (AnalyticsMetrics.tsx):**
```typescript
// Fetches multiple counts in parallel
const [
  totalScreenedCount,
  aeCount,
  saeCount,
  deathCount,
  // ... more metrics
] = await Promise.all([
  fetchTotalScreenedCount(globalFilter || null),
  fetchTotalAECount(globalFilter || null),
  fetchSAECount(globalFilter || null),
  fetchDeathCount(globalFilter || null),
  // ... more fetches
]);
```

**Chart Widgets (EnrollmentTrendChart.tsx):**
```typescript
// Uses React Query for data fetching and caching
const { data: apiData = [], isLoading, error } = useQuery<TrendDataPoint[]>({
  queryKey: ['enrollmentTrendData', filters],
  queryFn: () => fetchTrendData(filters),
  staleTime: 5 * 60 * 1000, // Cache for 5 minutes
});
```

### 3. Filter Architecture

**Global Filter System:**
- Uses a context-based global filter that applies to all widgets
- Filters are passed as query parameters to API endpoints
- Complex filter expressions support AND/OR operations

```typescript
interface FilterCondition {
  field: string;
  operator: 'eq' | 'ne' | 'in' | 'gt' | 'lt' | 'gte' | 'lte';
  value: any;
}

interface FilterGroup {
  operator: 'AND' | 'OR';
  filters: (FilterCondition | FilterGroup)[];
}
```

### 4. Widget Types and Data Requirements

Based on the old codebase, widgets fall into these categories:

**1. Metric Cards:**
- Single numeric value
- Optional comparison/trend
- Real-time updates via React Query

**2. Time Series Charts:**
- Line charts for trends
- Cumulative calculations
- Date-based x-axis

**3. Aggregated Tables:**
- Group by operations (e.g., by site)
- Multiple metrics per row
- Sortable/filterable

**4. Map Visualizations:**
- Geographic data with coordinates
- Aggregated values per location
- Interactive tooltips

**5. Flow Diagrams:**
- Sankey charts for patient flow
- State transitions
- Multiple interconnected datasets

### 5. Data Requirements Mapping

The old system doesn't have explicit data requirement definitions. Instead:
- Each widget component knows its own data needs
- API services handle the data fetching logic
- Filters are applied at the API level

## Recommendations for New System

### 1. Widget Data Requirements Schema

```typescript
interface WidgetDataRequirement {
  id: string;
  name: string;
  description: string;
  dataType: 'metric' | 'timeseries' | 'table' | 'geographic' | 'flow';
  
  // Required datasets
  datasets: {
    primary: string; // e.g., 'adsl'
    secondary?: string[]; // e.g., ['adae', 'addv']
  };
  
  // Required fields from each dataset
  requiredFields: {
    [dataset: string]: string[];
  };
  
  // Optional fields that enhance the widget
  optionalFields?: {
    [dataset: string]: string[];
  };
  
  // Aggregation requirements
  aggregation?: {
    groupBy?: string[];
    metrics: Array<{
      field: string;
      operation: 'count' | 'sum' | 'avg' | 'min' | 'max' | 'distinct';
      alias: string;
    }>;
  };
  
  // Filter requirements
  filters?: {
    required?: FilterCondition[];
    userConfigurable?: string[]; // Fields user can filter on
  };
  
  // Time series specific
  timeSeries?: {
    dateField: string;
    interval: 'day' | 'week' | 'month';
    cumulative: boolean;
  };
}
```

### 2. Widget Instance Configuration

```typescript
interface WidgetInstance {
  id: string;
  widgetId: string; // References widget definition
  
  // Data mapping from study fields to widget requirements
  fieldMappings: {
    [requiredField: string]: string; // Maps to actual study field
  };
  
  // User-configured filters
  filters?: FilterGroup;
  
  // Display configuration
  display: {
    title?: string;
    size: 'small' | 'medium' | 'large' | 'full';
    refreshInterval?: number; // in seconds
  };
  
  // Cached data strategy
  caching?: {
    enabled: boolean;
    ttl: number; // Time to live in seconds
  };
}
```

### 3. Data Service Architecture

```typescript
class WidgetDataService {
  async fetchWidgetData(
    widgetInstance: WidgetInstance,
    widgetDefinition: WidgetDataRequirement,
    globalFilters?: FilterGroup
  ): Promise<any> {
    // 1. Combine global and widget-specific filters
    const combinedFilters = this.mergeFilters(
      globalFilters,
      widgetInstance.filters
    );
    
    // 2. Apply field mappings
    const mappedFilters = this.applyFieldMappings(
      combinedFilters,
      widgetInstance.fieldMappings
    );
    
    // 3. Fetch data based on widget type
    switch (widgetDefinition.dataType) {
      case 'metric':
        return this.fetchMetricData(widgetDefinition, mappedFilters);
      case 'timeseries':
        return this.fetchTimeSeriesData(widgetDefinition, mappedFilters);
      case 'table':
        return this.fetchTableData(widgetDefinition, mappedFilters);
      // ... other types
    }
  }
}
```

### 4. Widget Component Pattern

```typescript
interface WidgetProps {
  instance: WidgetInstance;
  globalFilters?: FilterGroup;
}

const Widget: React.FC<WidgetProps> = ({ instance, globalFilters }) => {
  // Get widget definition
  const definition = useWidgetDefinition(instance.widgetId);
  
  // Fetch data using React Query
  const { data, isLoading, error } = useQuery({
    queryKey: ['widget', instance.id, globalFilters],
    queryFn: () => widgetDataService.fetchWidgetData(
      instance,
      definition,
      globalFilters
    ),
    staleTime: (instance.caching?.ttl || 300) * 1000,
  });
  
  // Render based on widget type
  if (isLoading) return <WidgetSkeleton type={definition.dataType} />;
  if (error) return <WidgetError error={error} />;
  
  return <WidgetRenderer type={definition.dataType} data={data} />;
};
```

### 5. Implementation Priority

1. **Phase 1: Core Widget Types**
   - Metric cards (simplest)
   - Basic tables
   - Simple line charts

2. **Phase 2: Advanced Visualizations**
   - Geographic maps
   - Sankey/flow diagrams
   - Complex aggregations

3. **Phase 3: Interactivity**
   - Drill-down capabilities
   - Cross-widget filtering
   - Real-time updates

## Next Steps

1. Create seed data for initial widget library based on these patterns
2. Implement the data requirement schema
3. Build the widget data service
4. Create proof-of-concept widgets following the patterns from the old codebase