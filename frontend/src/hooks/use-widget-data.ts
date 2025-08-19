// ABOUTME: Consolidated hook for fetching and managing widget data from the backend
// ABOUTME: Combines React Query for caching with support for multiple data types and real-time updates

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { apiClient } from '@/lib/api/client';
import { widgetsApi } from '@/lib/api/widgets';

// ============= Main Widget Data Hook =============
interface WidgetDataConfig {
  studyId: string;
  widgetType: string;
  widgetConfig: any;
  refreshInterval?: number; // in seconds
  useCache?: boolean;
}

interface WidgetDataState {
  data: any;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

export function useWidgetData({
  studyId,
  widgetType,
  widgetConfig,
  refreshInterval = 0,
  useCache = true
}: WidgetDataConfig) {
  const [state, setState] = useState<WidgetDataState>({
    data: null,
    loading: true,
    error: null,
    lastUpdated: null
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));

      const token = localStorage.getItem('auth_token');
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/widget-data/query`,
        {
          study_id: studyId,
          widget_type: widgetType,
          widget_config: widgetConfig,
          use_cache: useCache
        },
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      setState({
        data: response.data.data,
        loading: false,
        error: response.data.error || null,
        lastUpdated: new Date()
      });
    } catch (error: any) {
      setState({
        data: null,
        loading: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch widget data',
        lastUpdated: null
      });
    }
  }, [studyId, widgetType, widgetConfig, useCache]);

  // Initial fetch
  useEffect(() => {
    if (studyId && widgetType) {
      fetchData();
    }
  }, [studyId, widgetType]);

  // Set up refresh interval
  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(fetchData, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [refreshInterval, fetchData]);

  return {
    ...state,
    refresh: fetchData
  };
}

// ============= Advanced Widget Data Hook with React Query =============
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

interface UseAdvancedWidgetDataOptions {
  instance: WidgetInstance;
  dataRequirements: WidgetDataRequirement;
  globalFilters?: any;
  enabled?: boolean;
}

export function useAdvancedWidgetData({
  instance,
  dataRequirements,
  globalFilters,
  enabled = true
}: UseAdvancedWidgetDataOptions) {
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

      // Use the widget API to fetch data
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

// ============= Hook to invalidate widget data cache =============
export function useInvalidateWidgetData() {
  const queryClient = useQueryClient();

  return useCallback((widgetId?: string) => {
    if (widgetId) {
      // Invalidate specific widget
      queryClient.invalidateQueries({ queryKey: ['widget-data', widgetId] });
    } else {
      // Invalidate all widget data
      queryClient.invalidateQueries({ queryKey: ['widget-data'] });
    }
  }, [queryClient]);
}

// ============= Specific Hooks =============

// Hook for KPI data
export function useKPIData(studyId: string, kpiType: string, refreshInterval = 30) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchKPI = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('auth_token');
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/widget-data/kpi/${studyId}/${kpiType}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      setData(response.data);
      setLoading(false);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to fetch KPI data');
      setLoading(false);
    }
  }, [studyId, kpiType]);

  useEffect(() => {
    if (studyId && kpiType) {
      fetchKPI();
    }
  }, [studyId, kpiType]);

  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(fetchKPI, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [refreshInterval, fetchKPI]);

  return { data, loading, error, refresh: fetchKPI };
}

// Hook for dataset preview
export function useDatasetPreview(studyId: string, datasetName: string, limit = 100) {
  const [preview, setPreview] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPreview = useCallback(async () => {
    if (!studyId || !datasetName) return;

    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('auth_token');
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/widget-data/preview/${studyId}/${datasetName}`,
        {
          params: { limit },
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      setPreview(response.data);
      setLoading(false);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to fetch dataset preview');
      setLoading(false);
    }
  }, [studyId, datasetName, limit]);

  useEffect(() => {
    fetchPreview();
  }, [fetchPreview]);

  return { preview, loading, error, refresh: fetchPreview };
}

// Hook for auto-mapping
export function useAutoMapping(studyId: string, datasetName: string, targetWidget: string) {
  const [mappings, setMappings] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateMappings = useCallback(async () => {
    if (!studyId || !datasetName || !targetWidget) return;

    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('auth_token');
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/widget-data/auto-map`,
        {
          study_id: studyId,
          dataset_name: datasetName,
          target_widget: targetWidget
        },
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      setMappings(response.data);
      setLoading(false);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to generate mappings');
      setLoading(false);
    }
  }, [studyId, datasetName, targetWidget]);

  return { mappings, loading, error, generateMappings };
}

// ============= Helper Functions =============
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