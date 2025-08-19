// ABOUTME: Hook for fetching and managing widget data from the backend
// ABOUTME: Supports real-time updates, caching, and automatic refresh intervals

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

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

// Specific hook for KPI data
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