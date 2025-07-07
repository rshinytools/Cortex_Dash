// ABOUTME: Main widget renderer that loads appropriate widget component
// ABOUTME: Handles data loading, error boundaries, and loading states

'use client';

import React, { Suspense, useMemo, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RefreshCw, Download, AlertCircle, Loader2 } from 'lucide-react';
import { WidgetRegistry } from './widget-registry';
import { BaseWidgetProps, WidgetInstance, exportWidgetDataAsCSV, exportWidgetDataAsJSON, exportWidgetAsImage } from './base-widget';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface WidgetRendererProps {
  instance: WidgetInstance;
  data?: any;
  loading?: boolean;
  error?: string;
  onRefresh?: () => void;
  viewMode?: boolean;
}

class WidgetErrorBoundary extends React.Component<
  { children: React.ReactNode; widgetId: string },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode; widgetId: string }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error(`Widget ${this.props.widgetId} error:`, error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Card className="h-full">
          <CardContent className="flex flex-col items-center justify-center h-full p-6">
            <AlertCircle className="h-8 w-8 text-destructive mb-2" />
            <p className="text-sm font-medium">Widget Error</p>
            <p className="text-xs text-muted-foreground mt-1">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
          </CardContent>
        </Card>
      );
    }

    return this.props.children;
  }
}

export const WidgetRenderer: React.FC<WidgetRendererProps> = React.memo(({
  instance,
  data,
  loading = false,
  error,
  onRefresh,
  viewMode = true
}) => {
  const WidgetComponent = useMemo(() => {
    return WidgetRegistry.getComponent(instance.type);
  }, [instance.type]);

  const handleExport = useCallback((format: 'png' | 'csv' | 'json') => {
    const filename = `${instance.title.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}`;
    
    switch (format) {
      case 'png':
        exportWidgetAsImage(`widget-${instance.id}`, `${filename}.png`);
        break;
      case 'csv':
        if (Array.isArray(data)) {
          exportWidgetDataAsCSV(data, `${filename}.csv`);
        } else if (data?.records && Array.isArray(data.records)) {
          exportWidgetDataAsCSV(data.records, `${filename}.csv`);
        } else {
          console.warn('Data format not suitable for CSV export');
        }
        break;
      case 'json':
        exportWidgetDataAsJSON(data, `${filename}.json`);
        break;
    }
  }, [instance.id, instance.title, data]);

  if (!WidgetComponent) {
    return (
      <Card className="h-full">
        <CardContent className="flex flex-col items-center justify-center h-full">
          <AlertCircle className="h-8 w-8 text-muted-foreground mb-2" />
          <p className="text-sm font-medium">Unknown Widget Type</p>
          <p className="text-xs text-muted-foreground">Widget type "{instance.type}" is not registered</p>
        </CardContent>
      </Card>
    );
  }

  const widgetProps: BaseWidgetProps = {
    id: instance.id,
    title: instance.title,
    description: instance.description,
    configuration: instance.configuration,
    data,
    loading,
    error,
    onRefresh,
    onExport: handleExport,
    height: instance.layout.h * 80, // Assuming 80px per grid unit
    width: instance.layout.w * 100, // Assuming 100px per grid unit
  };

  const supportedFormats = WidgetComponent.supportedExportFormats || ['json'];

  return (
    <WidgetErrorBoundary widgetId={instance.id}>
      <div id={`widget-${instance.id}`} className="h-full relative group">
        {!viewMode && (
          <div className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
            {onRefresh && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={onRefresh}
                disabled={loading}
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            )}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Download className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {supportedFormats.includes('png') && (
                  <DropdownMenuItem onClick={() => handleExport('png')}>
                    Export as PNG
                  </DropdownMenuItem>
                )}
                {supportedFormats.includes('csv') && (
                  <DropdownMenuItem onClick={() => handleExport('csv')}>
                    Export as CSV
                  </DropdownMenuItem>
                )}
                {supportedFormats.includes('json') && (
                  <DropdownMenuItem onClick={() => handleExport('json')}>
                    Export as JSON
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
        
        <Suspense
          fallback={
            <Card className="h-full">
              <CardContent className="flex items-center justify-center h-full">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </CardContent>
            </Card>
          }
        >
          <WidgetComponent {...widgetProps} />
        </Suspense>
      </div>
    </WidgetErrorBoundary>
  );
});

WidgetRenderer.displayName = 'WidgetRenderer';