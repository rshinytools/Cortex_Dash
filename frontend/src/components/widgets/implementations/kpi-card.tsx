// ABOUTME: KPI Card widget implementation for displaying key performance indicators
// ABOUTME: Supports trends, comparisons, and various data formats with audit trail

'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  ArrowUp, 
  ArrowDown,
  Target,
  AlertCircle 
} from 'lucide-react';
import { BaseWidgetProps, WidgetComponent } from '../base-widget';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { useAuth } from '@/lib/auth-context';
import { cn } from '@/lib/utils';

interface KPICardConfig {
  // Data source configuration
  dataset?: string;
  field?: string;
  aggregation?: 'sum' | 'count' | 'average' | 'min' | 'max';
  filters?: Record<string, any>;
  
  // Display configuration
  format?: 'number' | 'percentage' | 'currency' | 'decimal';
  decimals?: number;
  prefix?: string;
  suffix?: string;
  
  // Comparison configuration
  showComparison?: boolean;
  comparisonType?: 'previous_period' | 'target' | 'baseline';
  comparisonValue?: number;
  targetValue?: number;
  
  // Trend configuration
  showTrend?: boolean;
  trendPeriod?: 'day' | 'week' | 'month' | 'quarter' | 'year';
  
  // Visual configuration
  color?: 'default' | 'success' | 'warning' | 'danger';
  icon?: string;
  goodDirection?: 'up' | 'down' | 'neutral';
}

interface KPIData {
  value: number;
  formatted_value: string;
  comparison?: {
    value: number;
    percentage: number;
    direction: 'up' | 'down' | 'neutral';
  };
  trend?: {
    values: number[];
    dates: string[];
    direction: 'up' | 'down' | 'neutral';
    percentage: number;
  };
  metadata?: {
    last_updated: string;
    data_quality: 'good' | 'warning' | 'poor';
    records_count: number;
  };
}

const KPICard: WidgetComponent<KPICardConfig> = ({
  id,
  title,
  description,
  configuration = {},
  data: propData,
  loading: propLoading,
  error: propError,
  onRefresh,
  height,
  width
}) => {
  const { user } = useAuth();
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Debug logging
  console.log('KPICard rendering:', { 
    id, 
    title, 
    configuration, 
    propData,
    dashboardId: configuration?.dashboardId 
  });

  // Fetch data from backend using the actual widget data endpoint
  const { data: fetchedData, isLoading: fetchLoading, error: fetchError, refetch } = useQuery({
    queryKey: ['widget-data', id, configuration],
    queryFn: async () => {
      // Get study ID and dashboard ID from URL or config
      const pathParts = window.location.pathname.split('/');
      const studyIndex = pathParts.indexOf('studies');
      const studyId = studyIndex >= 0 ? pathParts[studyIndex + 1] : null;
      
      if (!studyId) {
        throw new Error('Study ID not found');
      }

      // Get dashboard ID from configuration
      const dashboardId = configuration.dashboardId;
      
      if (!dashboardId) {
        console.log('Widget config missing dashboardId:', { id, configuration });
        throw new Error('Dashboard ID not provided in configuration');
      }
      
      console.log('Fetching widget data:', {
        studyId,
        dashboardId,
        widgetId: id,
        url: `/studies/${studyId}/dashboards/${dashboardId}/widgets/${id}/data`
      });
      
      // Call the actual backend endpoint
      // Format: /studies/{study_id}/dashboards/{dashboard_id}/widgets/{widget_id}/data
      const response = await apiClient.get(
        `/studies/${studyId}/dashboards/${dashboardId}/widgets/${id}/data`
      );
      
      console.log('Widget data response:', response.data);
      return response.data;
    },
    enabled: !propData, // Enable if no data provided via props
    refetchInterval: configuration.autoRefresh ? 60000 : false,
  });

  // Use provided data or fetched data
  // The backend returns data wrapped in a response object with a 'data' field
  const data = propData || fetchedData?.data || fetchedData;
  const loading = propLoading || fetchLoading;
  const error = propError || fetchError?.message;

  const handleRefresh = async () => {
    setIsRefreshing(true);
    if (onRefresh) {
      await onRefresh();
    } else {
      await refetch();
    }
    setIsRefreshing(false);
  };

  // Format value based on configuration
  const formatValue = (value: number): string => {
    if (!value && value !== 0) return '--';
    
    const { format = 'number', decimals = 0, prefix = '', suffix = '' } = configuration;
    
    let formatted: string;
    switch (format) {
      case 'percentage':
        formatted = `${(value * 100).toFixed(decimals)}%`;
        break;
      case 'currency':
        formatted = new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals
        }).format(value);
        break;
      case 'decimal':
        formatted = value.toFixed(decimals);
        break;
      default:
        formatted = new Intl.NumberFormat('en-US', {
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals
        }).format(value);
    }
    
    return `${prefix}${formatted}${suffix}`;
  };

  // Determine color based on value and configuration
  const getColorClass = (): string => {
    if (configuration.color) {
      switch (configuration.color) {
        case 'success': return 'text-green-400';
        case 'warning': return 'text-yellow-400';
        case 'danger': return 'text-red-400';
        default: return '';
      }
    }
    
    // Don't auto-color based on comparison unless explicitly configured
    // Keep the main value neutral (default text color)
    return '';
  };

  const getTrendIcon = () => {
    if (!data?.trend) return null;
    
    switch (data.trend.direction) {
      case 'up':
        return <TrendingUp className="h-4 w-4" />;
      case 'down':
        return <TrendingDown className="h-4 w-4" />;
      default:
        return <Minus className="h-4 w-4" />;
    }
  };

  if (loading) {
    return (
      <Card className="h-full bg-[#252b42] dark:bg-[#1a1f36] border-[#2a2f4a] shadow-lg">
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-24 bg-[#2a2f4a]" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-32 mb-2 bg-[#2a2f4a]" />
          <Skeleton className="h-3 w-20 bg-[#2a2f4a]" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="h-full bg-[#252b42] dark:bg-[#1a1f36] border-[#2a2f4a] shadow-lg">
        <CardContent className="flex flex-col items-center justify-center h-full">
          <AlertCircle className="h-8 w-8 text-red-500 mb-2" />
          <p className="text-sm text-gray-400">{error}</p>
        </CardContent>
      </Card>
    );
  }

  // Use data from backend or show loading/error state
  // NO MOCK DATA - everything must come from proper mappings
  const displayData: KPIData = data || null;

  console.log('KPICard display state:', {
    id,
    title,
    loading,
    error,
    hasData: !!displayData,
    displayData
  });

  // If no data, show message
  if (!displayData) {
    return (
      <Card className="h-full bg-[#252b42] dark:bg-[#1a1f36] border-[#2a2f4a] shadow-lg">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-gray-400">
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-[calc(100%-60px)]">
          <AlertCircle className="h-6 w-6 text-gray-500 mb-2" />
          <p className="text-sm text-gray-400 text-center">
            No data mapping configured
          </p>
          <p className="text-xs text-gray-500 text-center mt-1">
            Configure field mappings in study settings
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full relative overflow-hidden bg-[#252b42] dark:bg-[#1a1f36] border-[#2a2f4a] shadow-lg">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-gray-400">
            {title || displayData.label}
          </CardTitle>
          {displayData.metadata?.data_quality && (
            <Badge 
              variant={displayData.metadata.data_quality === 'good' ? 'default' : 'secondary'}
              className="text-xs"
            >
              {displayData.metadata.data_quality}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {/* Main Value */}
          <div className="flex items-baseline gap-2">
            <span className={cn("text-2xl font-bold text-white", getColorClass())}>
              {displayData.formatted_value || formatValue(displayData.value)}
            </span>
            {configuration.showTrend && displayData.trend && (
              <div className={cn(
                "flex items-center gap-1 text-sm text-gray-400"
              )}>
                {getTrendIcon()}
                <span>{displayData.trend.percentage?.toFixed(1) || displayData.trend}%</span>
              </div>
            )}
          </div>

          {/* Comparison */}
          {configuration.showComparison && displayData.comparison && (
            <div className="flex items-center gap-2 text-sm text-gray-400">
              {configuration.comparisonType === 'target' && (
                <>
                  <Target className="h-3 w-3" />
                  <span>Target: {formatValue(configuration.targetValue || 0)}</span>
                </>
              )}
              <span className="flex items-center gap-1 text-gray-400">
                {displayData.comparison.direction === 'up' ? 
                  <ArrowUp className="h-3 w-3" /> : 
                  displayData.comparison.direction === 'down' ?
                  <ArrowDown className="h-3 w-3" /> :
                  <Minus className="h-3 w-3" />
                }
                {displayData.comparison.percentage?.toFixed(1) || displayData.comparison}%
              </span>
            </div>
          )}

          {/* Description */}
          {description && (
            <p className="text-xs text-gray-400">{description}</p>
          )}

          {/* Last Updated */}
          {displayData.metadata?.last_updated && (
            <p className="text-xs text-gray-400">
              Updated: {new Date(displayData.metadata.last_updated).toLocaleString()}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Widget metadata for registration
KPICard.displayName = 'KPICard';
KPICard.defaultConfiguration = {
  format: 'number',
  decimals: 0,
  showTrend: true,
  showComparison: false,
  aggregation: 'sum'
};
KPICard.supportedExportFormats = ['json', 'png'];
KPICard.validateConfiguration = (config: KPICardConfig) => {
  // Validate required fields
  if (config.showComparison && config.comparisonType === 'target' && !config.targetValue) {
    return false;
  }
  return true;
};

export default KPICard;