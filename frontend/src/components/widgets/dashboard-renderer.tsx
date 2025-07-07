// ABOUTME: Dashboard renderer that renders complete dashboards with responsive layout
// ABOUTME: Uses react-grid-layout in view mode for widget positioning

'use client';

import React, { useMemo, useCallback, useState, useEffect } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import { DashboardConfiguration, WidgetInstance } from './base-widget';
import { WidgetRenderer } from './widget-renderer';
import { Card, CardContent } from '@/components/ui/card';
import { AlertCircle, Loader2 } from 'lucide-react';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const ResponsiveGridLayout = WidthProvider(Responsive);

interface DashboardRendererProps {
  configuration: DashboardConfiguration;
  widgetData: Record<string, any>;
  widgetLoading?: Record<string, boolean>;
  widgetErrors?: Record<string, string>;
  onRefreshWidget?: (widgetId: string) => void;
  viewMode?: boolean;
  className?: string;
}

export const DashboardRenderer: React.FC<DashboardRendererProps> = ({
  configuration,
  widgetData,
  widgetLoading = {},
  widgetErrors = {},
  onRefreshWidget,
  viewMode = true,
  className = ''
}) => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const layouts = useMemo(() => {
    // Generate layouts for different breakpoints
    const baseLayout = configuration.widgets.map(widget => ({
      i: widget.id,
      x: widget.layout.x,
      y: widget.layout.y,
      w: widget.layout.w,
      h: widget.layout.h,
      minW: widget.layout.minW || 1,
      minH: widget.layout.minH || 1,
      maxW: widget.layout.maxW,
      maxH: widget.layout.maxH,
      static: viewMode // Make static in view mode
    }));

    // Use provided layouts or generate responsive ones
    if (configuration.layout.layouts) {
      return configuration.layout.layouts;
    }

    // Generate responsive layouts
    return {
      lg: baseLayout,
      md: baseLayout.map(item => ({
        ...item,
        w: Math.min(item.w, 10),
        x: item.x % 10
      })),
      sm: baseLayout.map(item => ({
        ...item,
        w: Math.min(item.w, 6),
        x: item.x % 6
      })),
      xs: baseLayout.map(item => ({
        ...item,
        w: Math.min(item.w, 4),
        x: 0
      })),
      xxs: baseLayout.map(item => ({
        ...item,
        w: 1,
        x: 0
      }))
    };
  }, [configuration, viewMode]);

  const breakpoints = configuration.layout.breakpoints || {
    lg: 1200,
    md: 996,
    sm: 768,
    xs: 480,
    xxs: 0
  };

  const cols = {
    lg: configuration.layout.cols || 12,
    md: 10,
    sm: 6,
    xs: 4,
    xxs: 1
  };

  const handleRefreshWidget = useCallback((widgetId: string) => {
    if (onRefreshWidget) {
      onRefreshWidget(widgetId);
    }
  }, [onRefreshWidget]);

  if (!mounted) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!configuration.widgets || configuration.widgets.length === 0) {
    return (
      <Card className="w-full">
        <CardContent className="flex flex-col items-center justify-center py-12">
          <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Widgets Configured</h3>
          <p className="text-muted-foreground text-center max-w-md">
            This dashboard doesn't have any widgets configured yet. 
            {!viewMode && ' Add widgets to start visualizing your data.'}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`dashboard-renderer ${className}`}>
      <ResponsiveGridLayout
        className="layout"
        layouts={layouts}
        breakpoints={breakpoints}
        cols={cols}
        rowHeight={configuration.layout.rowHeight || 80}
        isDraggable={!viewMode}
        isResizable={!viewMode}
        margin={[16, 16]}
        containerPadding={[0, 0]}
        useCSSTransforms={true}
      >
        {configuration.widgets.map((widget: WidgetInstance) => (
          <div key={widget.id} className="widget-container">
            <WidgetRenderer
              instance={widget}
              data={widgetData[widget.id]}
              loading={widgetLoading[widget.id]}
              error={widgetErrors[widget.id]}
              onRefresh={() => handleRefreshWidget(widget.id)}
              viewMode={viewMode}
            />
          </div>
        ))}
      </ResponsiveGridLayout>

      <style jsx>{`
        .dashboard-renderer :global(.react-grid-layout) {
          position: relative;
        }
        
        .dashboard-renderer :global(.react-grid-item) {
          transition: all 200ms ease;
          transition-property: left, top, width, height;
        }
        
        .dashboard-renderer :global(.react-grid-item.cssTransforms) {
          transition-property: transform, width, height;
        }
        
        .dashboard-renderer :global(.react-grid-item.resizing) {
          opacity: 0.9;
        }
        
        .dashboard-renderer :global(.react-grid-item.static) {
          background: transparent;
        }
        
        .widget-container {
          height: 100%;
          width: 100%;
        }
      `}</style>
    </div>
  );
};

DashboardRenderer.displayName = 'DashboardRenderer';