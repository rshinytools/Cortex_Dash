// ABOUTME: Dynamic widget renderer that selects the appropriate widget component based on widget type
// ABOUTME: Central component for rendering any widget instance with proper data fetching and error handling

import React from 'react';
import { useWidgetData } from '@/hooks/useWidgetData';
import { MetricWidget } from './MetricWidget';
import { MetricsCard } from './MetricsCard';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface WidgetRendererProps {
  instance: {
    id: string;
    type: string;
    widgetDefinitionId?: string | number;
    config: any;
    widgetData?: any; // Full widget definition data
    fieldMappings?: Record<string, string>;
    filters?: any;
  };
  globalFilters?: any;
  className?: string;
  mode?: 'view' | 'preview' | 'design';
}

export function WidgetRenderer({
  instance,
  globalFilters,
  className,
  mode = 'view'
}: WidgetRendererProps) {
  // Get widget definition from instance data
  const widgetDefinition = instance.widgetData;
  const widgetType = instance.type;
  
  // Fetch widget data using the custom hook (only in view mode)
  const { data, isLoading, error } = useWidgetData({
    instance,
    dataRequirements: widgetDefinition?.data_requirements,
    globalFilters,
    enabled: mode === 'view' && !!widgetDefinition
  });

  // Get the title from instance config or widget name
  const title = instance.config?.title || widgetDefinition?.name || 'Widget';

  // Design mode - show placeholder
  if (mode === 'design') {
    return (
      <div className={cn("flex items-center justify-center h-full p-4", className)}>
        <div className="text-center">
          <p className="text-sm text-muted-foreground">
            {widgetDefinition?.name || widgetType}
          </p>
          {widgetDefinition?.description && (
            <p className="text-xs text-muted-foreground mt-1">
              {widgetDefinition.description}
            </p>
          )}
        </div>
      </div>
    );
  }

  // Preview mode - show sample data
  if (mode === 'preview') {
    return renderWidget(widgetType, title, getSampleData(widgetType), className, instance.config);
  }

  // Handle loading state (view mode)
  if (isLoading) {
    return <WidgetSkeleton type={widgetType} className={className} />;
  }

  // Handle error state (view mode)
  if (error) {
    return (
      <WidgetError
        title={title}
        error={error instanceof Error ? error.message : 'Failed to load widget data'}
        className={className}
      />
    );
  }

  // Render widget with data (view mode)
  return renderWidget(widgetType, title, data, className, instance.config);
}

// Helper function to render widget based on type
function renderWidget(type: string, title: string, data: any, className?: string, config?: any) {
  // Map widget codes to categories for rendering
  const widgetCategoryMap: Record<string, string> = {
    // Flexible metrics card widget
    'metrics_card_flexible': 'metrics_card',
    // Core metric widget
    'metric_card': 'metric',
    // Metrics
    'total_screened': 'metric',
    'screen_failures': 'metric',
    'total_aes': 'metric',
    'saes': 'metric',
    'total_subjects_with_aes': 'metric',
    'average_age': 'metric',
    'total_sum': 'metric',
    // Charts
    'enrollment_trend': 'line_chart',
    'ae_timeline': 'timeline',
    // Tables
    'site_summary_table': 'table',
    'subject_listing': 'table',
    // Maps
    'site_enrollment_map': 'map',
    // Specialized
    'subject_flow_diagram': 'sankey'
  };

  const widgetCategory = widgetCategoryMap[type] || type;

  switch (widgetCategory) {
    case 'metrics_card':
      return (
        <MetricsCard
          config={config || {}}
          data={data}
          loading={false}
          error={undefined}
        />
      );

    case 'metric':
      return (
        <MetricWidget
          title={title}
          subtitle={config?.subtitle}
          value={data?.value || 0}
          comparison={data?.comparison}
          format={data?.displayConfig?.format || config?.format || 'number'}
          decimalPlaces={data?.displayConfig?.decimalPlaces ?? config?.decimalPlaces ?? 0}
          prefix={data?.displayConfig?.prefix || config?.prefix || ''}
          suffix={data?.displayConfig?.suffix || config?.suffix || ''}
          aggregationType={data?.aggregationType}
          lastUpdated={data?.lastUpdated}
          className={className}
        />
      );

    case 'line_chart':
    case 'timeline':
      // TODO: Implement LineChartWidget
      return <PlaceholderWidget type="chart" title={title} className={className} />;

    case 'table':
      // TODO: Implement TableWidget
      return <PlaceholderWidget type="table" title={title} className={className} />;

    case 'map':
      // TODO: Implement MapWidget
      return <PlaceholderWidget type="map" title={title} className={className} />;

    case 'sankey':
      // TODO: Implement SankeyWidget
      return <PlaceholderWidget type="flow diagram" title={title} className={className} />;

    default:
      return (
        <WidgetError
          title={title}
          error={`Unknown widget type: ${type}`}
          className={className}
        />
      );
  }
}

// Widget skeleton component for loading state
function WidgetSkeleton({ type, className }: { type: string; className?: string }) {
  return (
    <div className={cn("p-4 border rounded-lg", className)}>
      <Skeleton className="h-5 w-32 mb-4" />
      <Skeleton className="h-8 w-24 mb-2" />
      <Skeleton className="h-4 w-16" />
    </div>
  );
}

// Widget error component
function WidgetError({ title, error, className }: { title: string; error: string; className?: string }) {
  return (
    <div className={cn("p-4", className)}>
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <strong>{title}:</strong> {error}
        </AlertDescription>
      </Alert>
    </div>
  );
}

// Placeholder component for unimplemented widget types
function PlaceholderWidget({ type, title, className }: { type: string; title: string; className?: string }) {
  return (
    <div className={cn("p-4 border rounded-lg bg-gray-50 flex items-center justify-center", className)}>
      <div className="text-center">
        <h3 className="font-medium text-gray-900">{title}</h3>
        <p className="text-sm text-gray-500 mt-1">
          {type} widget (coming soon)
        </p>
      </div>
    </div>
  );
}

// Get sample data for preview mode
function getSampleData(widgetType: string): any {
  const sampleData: Record<string, any> = {
    // Flexible metrics card
    metrics_card_flexible: {
      value: 1234,
      comparison: {
        previousValue: 1150,
        percentChange: 7.3,
        absoluteChange: 84
      },
      lastUpdated: new Date().toISOString()
    },
    // Static metrics card example
    metrics_card_static: {
      value: 505,
      comparison: null,
      lastUpdated: null
    },
    // Core metric card
    metric_card: {
      value: 1000,
      comparison: {
        value: 950,
        period: 'last extract',
        change: 5.3,
        type: 'previous_extract'
      },
      aggregationType: 'COUNT',
      displayConfig: {
        format: 'number',
        decimalPlaces: 0
      }
    },
    // Metrics
    total_screened: {
      value: 1234,
      comparison: {
        value: 1150,
        period: 'last month',
        change: 7.3
      }
    },
    screen_failures: {
      value: 89,
      comparison: {
        value: 95,
        period: 'last month',
        change: -6.3
      }
    },
    total_aes: {
      value: 456,
      comparison: {
        value: 423,
        period: 'last month',
        change: 7.8
      }
    },
    saes: {
      value: 12,
      comparison: {
        value: 15,
        period: 'last month',
        change: -20.0
      }
    },
    total_subjects_with_aes: {
      value: 234,
      comparison: {
        value: 218,
        period: 'last extract',
        change: 7.3
      },
      aggregationType: 'COUNT DISTINCT'
    },
    average_age: {
      value: 54.7,
      displayConfig: {
        format: 'number',
        decimalPlaces: 1,
        suffix: ' years'
      },
      aggregationType: 'AVG'
    },
    total_sum: {
      value: 125430.50,
      displayConfig: {
        format: 'currency',
        decimalPlaces: 2
      },
      aggregationType: 'SUM'
    }
  };

  return sampleData[widgetType] || { value: 0 };
}