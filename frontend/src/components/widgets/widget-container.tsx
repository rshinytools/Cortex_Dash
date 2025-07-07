// ABOUTME: Container component that wraps widgets with data fetching and error handling
// ABOUTME: Provides consistent loading states, error boundaries, and data refresh capabilities

'use client';

import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  RefreshCw, 
  Download, 
  Maximize2, 
  MoreVertical,
  AlertCircle,
  Loader2 
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useWidgetData } from '@/hooks/use-widget-data';
import { WidgetInstance } from '@/types/widget';
import { WidgetRenderer } from './widget-renderer';
import { WidgetFilterConnector } from './widget-filter-connector';
import { useWidgetFilters } from './filter-manager';
import { DashboardAnnotations } from './dashboard-annotations';
import { useWidgetDrillDown } from './drill-down-manager';
import { cn } from '@/lib/utils';
import { exportWidgetAsImage, exportWidgetDataAsCSV, exportWidgetDataAsJSON } from './base-widget';
import { format } from 'date-fns';

interface WidgetContainerProps {
  widgetInstance: WidgetInstance;
  studyId: string;
  className?: string;
  onEdit?: () => void;
  onDelete?: () => void;
  onFullscreen?: () => void;
  readOnly?: boolean;
}

export function WidgetContainer({
  widgetInstance,
  studyId,
  className,
  onEdit,
  onDelete,
  onFullscreen,
  readOnly = false,
}: WidgetContainerProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const widgetId = `widget-${widgetInstance.id}`;

  // Get filter context for this widget
  const { filterQuery, hasFilters } = useWidgetFilters(widgetInstance.id);
  
  // Get drill-down context for this widget
  const { canDrillDown, handleDataPointClick } = useWidgetDrillDown(widgetInstance.id);

  const {
    data,
    metadata,
    isLoading,
    isError,
    error,
    refetch,
    isRefetching,
  } = useWidgetData(widgetInstance, studyId, {
    filters: filterQuery, // Pass filters to data hook
    onError: (err) => {
      console.error(`Error loading widget ${widgetInstance.id}:`, err);
    },
  });

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await refetch();
    } finally {
      setIsRefreshing(false);
    }
  }, [refetch]);

  const handleExport = useCallback((format: 'png' | 'csv' | 'json') => {
    const timestamp = format(new Date(), 'yyyy-MM-dd-HHmmss');
    const filename = `${widgetInstance.config?.display?.title || widgetInstance.widgetDefinition?.name || 'widget'}-${timestamp}`;

    switch (format) {
      case 'png':
        exportWidgetAsImage(widgetId, `${filename}.png`);
        break;
      case 'csv':
        if (Array.isArray(data)) {
          exportWidgetDataAsCSV(data, `${filename}.csv`);
        }
        break;
      case 'json':
        exportWidgetDataAsJSON(data, `${filename}.json`);
        break;
    }
  }, [widgetId, widgetInstance, data]);

  // Get supported export formats from widget definition
  const supportedFormats = widgetInstance.widgetDefinition?.componentPath
    ? ['png', 'csv', 'json'] // Default formats
    : ['json'];

  const showActions = !readOnly && (onEdit || onDelete || supportedFormats.length > 0);

  // Mock available fields for filtering - in a real app, get from widget definition
  const availableFields = [
    { field: 'USUBJID', label: 'Subject ID', type: 'string' as const },
    { field: 'SITEID', label: 'Site ID', type: 'string' as const },
    { field: 'AGE', label: 'Age', type: 'number' as const },
    { field: 'SEX', label: 'Sex', type: 'select' as const, options: [
      { value: 'M', label: 'Male' },
      { value: 'F', label: 'Female' }
    ]},
    { field: 'RACE', label: 'Race', type: 'select' as const, options: [
      { value: 'White', label: 'White' },
      { value: 'Black', label: 'Black' },
      { value: 'Asian', label: 'Asian' },
      { value: 'Hispanic', label: 'Hispanic' },
      { value: 'Other', label: 'Other' }
    ]},
    { field: 'VISITDT', label: 'Visit Date', type: 'date' as const },
  ];

  return (
    <WidgetFilterConnector
      widgetId={widgetInstance.id}
      widgetType={widgetInstance.widgetDefinition?.componentPath || 'unknown'}
      availableFields={availableFields}
      onDataRefresh={refetch}
      className={cn("relative h-full", className)}
    >
      <DashboardAnnotations
        widgetId={widgetInstance.id}
        dashboardId="current-dashboard-id" // Would come from context
        currentUserId="current-user-id"   // Would come from auth context
        currentUserName="Current User"    // Would come from auth context
        className="absolute inset-0"
      >
        <div id={widgetId} className="h-full">
        {/* Loading overlay */}
      {isRefreshing && (
        <div className="absolute inset-0 bg-background/50 backdrop-blur-sm z-10 flex items-center justify-center rounded-lg">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      )}

      {/* Error state */}
      {isError && !isLoading && (
        <Card className="h-full">
          <CardContent className="flex flex-col items-center justify-center h-full p-6">
            <AlertCircle className="h-12 w-12 text-destructive mb-4" />
            <h3 className="text-lg font-semibold mb-2">Error Loading Widget</h3>
            <p className="text-sm text-muted-foreground text-center mb-4">
              {error?.message || 'An unexpected error occurred'}
            </p>
            <Button onClick={handleRefresh} variant="outline" size="sm">
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Widget content */}
      {!isError && (
        <div className="relative h-full">
          {/* Action buttons */}
          {showActions && (
            <div className="absolute top-2 right-2 z-20 flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={handleRefresh}
                disabled={isRefreshing}
              >
                <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
              </Button>
              
              {onFullscreen && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={onFullscreen}
                >
                  <Maximize2 className="h-4 w-4" />
                </Button>
              )}

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {supportedFormats.includes('png') && (
                    <DropdownMenuItem onClick={() => handleExport('png')}>
                      <Download className="mr-2 h-4 w-4" />
                      Export as Image
                    </DropdownMenuItem>
                  )}
                  {supportedFormats.includes('csv') && (
                    <DropdownMenuItem onClick={() => handleExport('csv')}>
                      <Download className="mr-2 h-4 w-4" />
                      Export as CSV
                    </DropdownMenuItem>
                  )}
                  {supportedFormats.includes('json') && (
                    <DropdownMenuItem onClick={() => handleExport('json')}>
                      <Download className="mr-2 h-4 w-4" />
                      Export as JSON
                    </DropdownMenuItem>
                  )}
                  
                  {(onEdit || onDelete) && supportedFormats.length > 0 && (
                    <DropdownMenuSeparator />
                  )}
                  
                  {onEdit && (
                    <DropdownMenuItem onClick={onEdit}>
                      Edit Widget
                    </DropdownMenuItem>
                  )}
                  {onDelete && (
                    <DropdownMenuItem 
                      onClick={onDelete}
                      className="text-destructive focus:text-destructive"
                    >
                      Delete Widget
                    </DropdownMenuItem>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )}

          {/* Render widget */}
          <WidgetRenderer
            widgetInstance={widgetInstance}
            data={data}
            loading={isLoading}
            error={isError ? error?.message : undefined}
            onRefresh={handleRefresh}
            onExport={handleExport}
            onDataPointClick={canDrillDown ? handleDataPointClick : undefined}
          />

          {/* Last updated timestamp */}
          {metadata?.lastUpdated && !isLoading && (
            <div className="absolute bottom-1 right-2 text-xs text-muted-foreground">
              Updated {format(new Date(metadata.lastUpdated), 'HH:mm:ss')}
            </div>
          )}
        </div>
      )}
        </div>
      </DashboardAnnotations>
    </WidgetFilterConnector>
  );
}