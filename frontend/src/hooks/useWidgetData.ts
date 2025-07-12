// ABOUTME: Custom hook for fetching widget data based on widget configuration and data requirements
// ABOUTME: Implements the data fetching pattern found in the old codebase using React Query

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { widgetsApi } from '@/lib/api/widgets';

interface WidgetDataRequirement {
  dataType: 'metric' | 'timeseries' | 'table' | 'geographic' | 'flow';
  datasets: {
    primary: string;
    secondary?: string[];
  };
  requiredFields: {
    [dataset: string]: string[];
  };
  aggregation?: {
    groupBy?: string[];
    metrics: Array<{
      field: string;
      operation: 'count' | 'sum' | 'avg' | 'min' | 'max' | 'distinct';
      alias: string;
    }>;
  };
  filters?: {
    required?: Array<{
      field: string;
      operator: string;
      value: any;
    }>;
    userConfigurable?: string[];
  };
  timeSeries?: {
    dateField: string;
    interval: 'day' | 'week' | 'month';
    cumulative: boolean;
  };
}

interface WidgetInstance {
  id: string;
  type: string;
  widgetDefinitionId?: string | number;
  config: any;
  widgetData?: any;
  fieldMappings?: Record<string, string>;
  filters?: any;
}

interface UseWidgetDataOptions {
  instance: WidgetInstance;
  dataRequirements: WidgetDataRequirement;
  globalFilters?: any;
  enabled?: boolean;
}

export function useWidgetData({
  instance,
  dataRequirements,
  globalFilters,
  enabled = true
}: UseWidgetDataOptions) {
  // Build the query key including all dependencies
  const queryKey = [
    'widget-data',
    instance.id,
    dataRequirements?.dataType,
    globalFilters,
    instance.filters
  ];

  // Determine the stale time based on refresh interval or default
  const staleTime = (instance.config?.refreshInterval || 300) * 1000;

  return useQuery({
    queryKey,
    queryFn: async () => {
      // Combine filters
      const combinedFilters = combineFilters(
        globalFilters,
        instance.filters,
        dataRequirements.filters?.required
      );

      // Apply field mappings to filters
      const mappedFilters = applyFieldMappings(
        combinedFilters,
        instance.fieldMappings || {}
      );

      // If no data requirements, return empty data
      if (!dataRequirements) {
        return { value: 0 };
      }

      // For now, use the widget API to fetch data
      // In the future, this will be replaced with actual data fetching based on data requirements
      return widgetsApi.fetchWidgetData({
        widget_instance_id: instance.id,
        widget_id: Number(instance.widgetDefinitionId) || 0,
        field_mappings: instance.fieldMappings || {},
        filters: mappedFilters,
        global_filters: globalFilters,
        config: instance.config
      });
    },
    staleTime,
    enabled
  });
}

// Helper functions
function combineFilters(...filterGroups: any[]): any {
  const validFilters = filterGroups.filter(f => f != null);
  
  if (validFilters.length === 0) return null;
  if (validFilters.length === 1) return validFilters[0];
  
  return {
    operator: 'AND',
    filters: validFilters
  };
}

function applyFieldMappings(filters: any, mappings: Record<string, string>): any {
  if (!filters) return filters;
  
  // Recursively apply mappings to filter fields
  if (filters.field && mappings[filters.field]) {
    return { ...filters, field: mappings[filters.field] };
  }
  
  if (filters.filters && Array.isArray(filters.filters)) {
    return {
      ...filters,
      filters: filters.filters.map((f: any) => applyFieldMappings(f, mappings))
    };
  }
  
  return filters;
}

// Data fetching functions for each widget type
async function fetchMetricData(
  requirements: WidgetDataRequirement,
  filters: any,
  mappings: Record<string, string>
): Promise<any> {
  const { primary } = requirements.datasets;
  const { metrics } = requirements.aggregation || {};
  
  if (!metrics || metrics.length === 0) {
    throw new Error('No aggregation metrics defined for metric widget');
  }
  
  // For simple count metrics, use the count endpoint
  const metric = metrics[0];
  const mappedField = mappings[metric.field] || metric.field;
  
  // Construct the appropriate API call based on the metric operation
  if (metric.operation === 'count' || metric.operation === 'distinct') {
    const response = await apiClient.post(`/api/v1/analysis/count`, {
      dataset: primary,
      field: mappedField,
      filters,
      distinct: metric.operation === 'distinct'
    });
    
    return {
      value: response.data.count,
      field: metric.alias
    };
  }
  
  // For other aggregations, use a different endpoint
  // This would need to be implemented in the backend
  throw new Error(`Aggregation operation ${metric.operation} not yet implemented`);
}

async function fetchTimeSeriesData(
  requirements: WidgetDataRequirement,
  filters: any,
  mappings: Record<string, string>
): Promise<any> {
  const { primary } = requirements.datasets;
  const { timeSeries } = requirements;
  
  if (!timeSeries) {
    throw new Error('No time series configuration defined');
  }
  
  const mappedDateField = mappings[timeSeries.dateField] || timeSeries.dateField;
  
  // Call a time series endpoint (would need backend implementation)
  const response = await apiClient.post(`/api/v1/analysis/timeseries`, {
    dataset: primary,
    dateField: mappedDateField,
    interval: timeSeries.interval,
    cumulative: timeSeries.cumulative,
    filters
  });
  
  return response.data;
}

async function fetchTableData(
  requirements: WidgetDataRequirement,
  filters: any,
  mappings: Record<string, string>
): Promise<any> {
  const { primary } = requirements.datasets;
  const { requiredFields } = requirements;
  
  // Get all fields needed
  const allFields = [
    ...(requiredFields[primary] || [])
  ];
  
  // Map field names
  const mappedFields = allFields.map(field => mappings[field] || field);
  
  // Fetch paginated data
  const response = await apiClient.get(`/api/v1/data/${primary}`, {
    params: {
      columns: mappedFields.join(','),
      filters: JSON.stringify(filters),
      page: 1,
      page_size: 100
    }
  });
  
  return response.data;
}

async function fetchGeographicData(
  requirements: WidgetDataRequirement,
  filters: any,
  mappings: Record<string, string>
): Promise<any> {
  // Similar pattern to other data types
  // Would need specific geographic aggregation endpoint
  throw new Error('Geographic data fetching not yet implemented');
}

async function fetchFlowData(
  requirements: WidgetDataRequirement,
  filters: any,
  mappings: Record<string, string>
): Promise<any> {
  // Similar pattern to other data types
  // Would need specific flow analysis endpoint
  throw new Error('Flow data fetching not yet implemented');
}