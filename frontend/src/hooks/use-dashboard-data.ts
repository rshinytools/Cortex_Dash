// ABOUTME: Dashboard data loading hook for fetching dashboard configuration and widget data
// ABOUTME: Handles batch loading, refresh, and cache management

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardConfiguration, WidgetInstance } from '@/components/widgets/base-widget';
import axios from 'axios';

interface DashboardDataOptions {
  studyId: string;
  dashboardId?: string;
  refreshInterval?: number;
  enableAutoRefresh?: boolean;
}

interface WidgetDataRequest {
  widgetId: string;
  endpoint?: string;
  query?: string;
  params?: Record<string, any>;
}

interface DashboardDataResult {
  configuration?: DashboardConfiguration;
  widgetData: Record<string, any>;
  widgetLoading: Record<string, boolean>;
  widgetErrors: Record<string, string>;
  isLoadingConfig: boolean;
  configError: string | null;
  refreshWidget: (widgetId: string) => void;
  refreshAllWidgets: () => void;
  updateConfiguration: (config: DashboardConfiguration) => Promise<void>;
}

// Mock API functions - replace with actual API calls
const fetchDashboardConfiguration = async (studyId: string, dashboardId?: string): Promise<DashboardConfiguration> => {
  // This would be replaced with actual API call
  const response = await axios.get(`/api/v1/studies/${studyId}/dashboards/${dashboardId || 'default'}`);
  return response.data;
};

const fetchWidgetData = async (studyId: string, request: WidgetDataRequest): Promise<any> => {
  // This would be replaced with actual API call
  if (request.endpoint) {
    const response = await axios.get(request.endpoint, { params: request.params });
    return response.data;
  }
  
  // Default data fetching based on widget type
  const response = await axios.post(`/api/v1/studies/${studyId}/widgets/data`, {
    widgetId: request.widgetId,
    query: request.query,
    params: request.params,
  });
  return response.data;
};

const updateDashboardConfiguration = async (
  studyId: string, 
  dashboardId: string, 
  config: DashboardConfiguration
): Promise<void> => {
  await axios.put(`/api/v1/studies/${studyId}/dashboards/${dashboardId}`, config);
};

export function useDashboardData({
  studyId,
  dashboardId,
  refreshInterval,
  enableAutoRefresh = false,
}: DashboardDataOptions): DashboardDataResult {
  const queryClient = useQueryClient();
  const [widgetData, setWidgetData] = useState<Record<string, any>>({});
  const [widgetLoading, setWidgetLoading] = useState<Record<string, boolean>>({});
  const [widgetErrors, setWidgetErrors] = useState<Record<string, string>>({});

  // Fetch dashboard configuration
  const {
    data: configuration,
    isLoading: isLoadingConfig,
    error: configError,
  } = useQuery({
    queryKey: ['dashboard-config', studyId, dashboardId],
    queryFn: () => fetchDashboardConfiguration(studyId, dashboardId),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Update configuration mutation
  const updateConfigMutation = useMutation({
    mutationFn: (config: DashboardConfiguration) => 
      updateDashboardConfiguration(studyId, config.id, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-config', studyId, dashboardId] });
    },
  });

  // Load data for a single widget
  const loadWidgetData = useCallback(async (widget: WidgetInstance) => {
    setWidgetLoading(prev => ({ ...prev, [widget.id]: true }));
    setWidgetErrors(prev => ({ ...prev, [widget.id]: '' }));

    try {
      const request: WidgetDataRequest = {
        widgetId: widget.id,
        endpoint: widget.dataSource?.endpoint,
        query: widget.dataSource?.query,
        params: widget.configuration,
      };

      const data = await fetchWidgetData(studyId, request);
      setWidgetData(prev => ({ ...prev, [widget.id]: data }));
    } catch (error) {
      console.error(`Error loading widget ${widget.id}:`, error);
      setWidgetErrors(prev => ({ 
        ...prev, 
        [widget.id]: error instanceof Error ? error.message : 'Failed to load data'
      }));
    } finally {
      setWidgetLoading(prev => ({ ...prev, [widget.id]: false }));
    }
  }, [studyId]);

  // Load data for all widgets
  const loadAllWidgetData = useCallback(async () => {
    if (!configuration?.widgets) return;

    // Batch load widgets
    const loadPromises = configuration.widgets.map(widget => loadWidgetData(widget));
    await Promise.allSettled(loadPromises);
  }, [configuration, loadWidgetData]);

  // Refresh a single widget
  const refreshWidget = useCallback((widgetId: string) => {
    const widget = configuration?.widgets.find(w => w.id === widgetId);
    if (widget) {
      loadWidgetData(widget);
    }
  }, [configuration, loadWidgetData]);

  // Refresh all widgets
  const refreshAllWidgets = useCallback(() => {
    loadAllWidgetData();
  }, [loadAllWidgetData]);

  // Update configuration
  const updateConfiguration = useCallback(async (config: DashboardConfiguration) => {
    await updateConfigMutation.mutateAsync(config);
  }, [updateConfigMutation]);

  // Load widget data when configuration changes
  useEffect(() => {
    if (configuration) {
      loadAllWidgetData();
    }
  }, [configuration, loadAllWidgetData]);

  // Auto-refresh logic
  useEffect(() => {
    if (!enableAutoRefresh || !refreshInterval || !configuration) return;

    const interval = setInterval(() => {
      configuration.widgets.forEach(widget => {
        const widgetRefreshInterval = widget.dataSource?.refreshInterval || refreshInterval;
        // Only refresh if widget-specific interval matches
        if (widgetRefreshInterval === refreshInterval) {
          loadWidgetData(widget);
        }
      });
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [enableAutoRefresh, refreshInterval, configuration, loadWidgetData]);

  return {
    configuration,
    widgetData,
    widgetLoading,
    widgetErrors,
    isLoadingConfig,
    configError: configError ? (configError as Error).message : null,
    refreshWidget,
    refreshAllWidgets,
    updateConfiguration,
  };
}

// Hook for saving dashboard state (for admin interface)
export function useSaveDashboard(studyId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (config: DashboardConfiguration) => {
      await updateDashboardConfiguration(studyId, config.id, config);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-config', studyId] });
    },
  });
}