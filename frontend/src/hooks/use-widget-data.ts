// ABOUTME: Custom hook for fetching and managing widget data
// ABOUTME: Handles data fetching, caching, and real-time updates for dashboard widgets

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';
import { apiClient } from '@/lib/api/client';
import { WidgetInstance } from '@/types/widget';

export interface WidgetDataOptions {
  enabled?: boolean;
  refreshInterval?: number;
  onSuccess?: (data: any) => void;
  onError?: (error: any) => void;
}

export interface WidgetDataResponse {
  data: any;
  metadata?: {
    lastUpdated: string;
    recordCount?: number;
    executionTime?: number;
  };
}

// Query key factory for widget data
const widgetDataKeys = {
  all: ['widget-data'] as const,
  byWidget: (widgetId: string, studyId: string) => 
    [...widgetDataKeys.all, 'widget', widgetId, 'study', studyId] as const,
  byInstance: (instanceId: string, studyId: string) => 
    [...widgetDataKeys.all, 'instance', instanceId, 'study', studyId] as const,
};

// Hook to fetch widget data
export function useWidgetData(
  widgetInstance: WidgetInstance,
  studyId: string,
  options?: WidgetDataOptions
) {
  const queryClient = useQueryClient();
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Determine refresh interval from widget config or options
  const refreshInterval = options?.refreshInterval || 
    (widgetInstance.config as any)?.dataSource?.refreshInterval || 
    widgetInstance.widgetDefinition?.dataRequirements?.refreshInterval;

  // Build the API endpoint based on widget configuration
  const buildEndpoint = () => {
    const baseEndpoint = `/api/v1/studies/${studyId}/widgets/${widgetInstance.id}/data`;
    const params = new URLSearchParams();

    // Add data source parameters
    if (widgetInstance.config?.dataSource?.type === 'dataset') {
      params.append('dataset_id', widgetInstance.config.dataSource.datasetId!);
    }

    // Add any filters from widget config
    if ((widgetInstance.config as any)?.filters) {
      Object.entries((widgetInstance.config as any).filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, String(value));
        }
      });
    }

    // Add time range if specified
    if ((widgetInstance.config as any)?.timeRange) {
      const { start, end } = (widgetInstance.config as any).timeRange;
      if (start) params.append('start_date', start);
      if (end) params.append('end_date', end);
    }

    const queryString = params.toString();
    return queryString ? `${baseEndpoint}?${queryString}` : baseEndpoint;
  };

  const query = useQuery({
    queryKey: widgetDataKeys.byInstance(widgetInstance.id, studyId),
    queryFn: async () => {
      const endpoint = buildEndpoint();
      const { data } = await apiClient.get<WidgetDataResponse>(endpoint);
      
      // Call onSuccess callback if provided
      if (options?.onSuccess) {
        options.onSuccess(data.data);
      }
      
      return data;
    },
    enabled: options?.enabled !== false && !!studyId && !!widgetInstance.id,
    staleTime: refreshInterval ? refreshInterval * 1000 : 5 * 60 * 1000, // Default 5 minutes
    gcTime: refreshInterval ? refreshInterval * 2000 : 10 * 60 * 1000, // Default 10 minutes
    retry: (failureCount, error: any) => {
      // Don't retry on 404 or 403 errors
      if (error?.response?.status === 404 || error?.response?.status === 403) {
        return false;
      }
      return failureCount < 3;
    },
    // @ts-expect-error - onError type mismatch with useQuery expectations
    onError: (error: any) => {
      if (options?.onError) {
        options.onError(error);
      }
    },
  });

  // Set up automatic refresh if interval is specified
  useEffect(() => {
    if (refreshInterval && refreshInterval > 0 && query.isSuccess) {
      refreshIntervalRef.current = setInterval(() => {
        queryClient.invalidateQueries({
          queryKey: widgetDataKeys.byInstance(widgetInstance.id, studyId),
        });
      }, refreshInterval * 1000);

      return () => {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
        }
      };
    }
  }, [refreshInterval, query.isSuccess, queryClient, widgetInstance.id, studyId]);

  // Transform the data based on widget type
  const transformedData = (query.data as any)?.data ? transformData((query.data as any).data, widgetInstance) : null;

  return {
    data: transformedData,
    metadata: (query.data as any)?.metadata,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
    isRefetching: query.isRefetching,
  };
}

// Transform data based on widget type and configuration
function transformData(rawData: any, widgetInstance: WidgetInstance): any {
  const widgetType = widgetInstance.widgetDefinition?.type || (widgetInstance as any).type;
  
  // Handle different data formats
  if (!rawData) return null;

  // If data is already in the expected format, return as is
  if (Array.isArray(rawData)) {
    return rawData;
  }

  // If data has a records property, use that
  if (rawData.records && Array.isArray(rawData.records)) {
    return rawData.records;
  }

  // For metric widgets, ensure data is in the expected format
  if (widgetType === 'METRIC' && typeof rawData === 'object') {
    // If it's a single value, wrap it
    if (rawData.value !== undefined) {
      return rawData;
    }
    // Otherwise, try to extract the value from the first property
    const keys = Object.keys(rawData);
    if (keys.length > 0) {
      return { value: rawData[keys[0]] };
    }
  }

  // For chart widgets, ensure data is an array
  if (['CHART', 'TABLE'].includes(widgetType)) {
    // If it's a single object, wrap in array
    if (typeof rawData === 'object' && !Array.isArray(rawData)) {
      return [rawData];
    }
  }

  return rawData;
}

// Hook to invalidate widget data cache
export function useInvalidateWidgetData() {
  const queryClient = useQueryClient();

  return {
    invalidateAll: () => {
      queryClient.invalidateQueries({ queryKey: widgetDataKeys.all });
    },
    invalidateWidget: (widgetId: string, studyId: string) => {
      queryClient.invalidateQueries({ 
        queryKey: widgetDataKeys.byWidget(widgetId, studyId) 
      });
    },
    invalidateInstance: (instanceId: string, studyId: string) => {
      queryClient.invalidateQueries({ 
        queryKey: widgetDataKeys.byInstance(instanceId, studyId) 
      });
    },
  };
}

// Hook to prefetch widget data
export function usePrefetchWidgetData() {
  const queryClient = useQueryClient();

  return async (widgetInstance: WidgetInstance, studyId: string) => {
    await queryClient.prefetchQuery({
      queryKey: widgetDataKeys.byInstance(widgetInstance.id, studyId),
      queryFn: async () => {
        const endpoint = `/api/v1/studies/${studyId}/widgets/${widgetInstance.id}/data`;
        const { data } = await apiClient.get<WidgetDataResponse>(endpoint);
        return data;
      },
      staleTime: 5 * 60 * 1000, // 5 minutes
    });
  };
}