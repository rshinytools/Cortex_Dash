// ABOUTME: Main dashboard viewer component that renders a complete dashboard with widgets
// ABOUTME: Handles dashboard layout, widget rendering, and coordinated actions

'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { Responsive, WidthProvider, Layout } from 'react-grid-layout';
import { DashboardToolbar } from './dashboard-toolbar';
import { WidgetContainer } from './widget-container';
import { useInvalidateWidgetData } from '@/hooks/use-widget-data';
import { WidgetInstance } from '@/types/widget';
import { FilterManagerProvider } from './filter-manager';
import { ParameterManagerProvider } from '../dashboard/dashboard-parameters';
import { ParameterControls } from '../dashboard/parameter-controls';
import { DrillDownManagerProvider } from './drill-down-manager';
import { RealTimeCursors } from './real-time-cursors';
import { cn } from '@/lib/utils';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const ResponsiveGridLayout = WidthProvider(Responsive);

export interface Dashboard {
  id: string;
  name: string;
  description?: string;
  studyId: string;
  widgets: WidgetInstance[];
  layout?: {
    cols?: number;
    rowHeight?: number;
    breakpoints?: Record<string, number>;
    layouts?: Record<string, Layout[]>;
  };
  createdAt: string;
  updatedAt: string;
}

interface DashboardViewerProps {
  dashboard: Dashboard;
  studyId: string;
  readOnly?: boolean;
  onEdit?: (widgetId: string) => void;
  onDelete?: (widgetId: string) => void;
  onLayoutChange?: (layouts: Record<string, Layout[]>) => void;
  className?: string;
}

export function DashboardViewer({
  dashboard,
  studyId,
  readOnly = false,
  onEdit,
  onDelete,
  onLayoutChange,
  className,
}: DashboardViewerProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [timeRange, setTimeRange] = useState('7d');
  const { invalidateAll } = useInvalidateWidgetData();

  // Convert widget instances to grid layout items
  const layouts = useMemo(() => {
    if (dashboard.layout?.layouts) {
      return dashboard.layout.layouts;
    }

    // Default layout generation
    const defaultLayout: Layout[] = dashboard.widgets.map((widget) => ({
      i: widget.id,
      x: widget.position?.x || 0,
      y: widget.position?.y || 0,
      w: widget.position?.width || widget.widgetDefinition?.size?.defaultWidth || 6,
      h: widget.position?.height || widget.widgetDefinition?.size?.defaultHeight || 4,
      minW: widget.widgetDefinition?.size?.minWidth || 2,
      minH: widget.widgetDefinition?.size?.minHeight || 2,
      static: readOnly,
    }));

    return { lg: defaultLayout };
  }, [dashboard, readOnly]);

  const handleRefreshAll = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await invalidateAll();
    } finally {
      setIsRefreshing(false);
    }
  }, [invalidateAll]);

  const handleToggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  const handleExport = useCallback(async (format: 'pdf' | 'png' | 'excel') => {
    // TODO: Implement dashboard export functionality
    console.log(`Exporting dashboard as ${format}`);
  }, []);

  const handleShare = useCallback(() => {
    // TODO: Implement share functionality
    console.log('Sharing dashboard');
  }, []);

  const handleSettings = useCallback(() => {
    // TODO: Implement settings dialog
    console.log('Opening dashboard settings');
  }, []);

  const handleLayoutChange = useCallback(
    (currentLayout: Layout[], allLayouts: Record<string, Layout[]>) => {
      if (!readOnly && onLayoutChange) {
        onLayoutChange(allLayouts);
      }
    },
    [readOnly, onLayoutChange]
  );

  const breakpoints = dashboard.layout?.breakpoints || {
    lg: 1200,
    md: 996,
    sm: 768,
    xs: 480,
    xxs: 0,
  };

  const cols = typeof dashboard.layout?.cols === 'object' 
    ? dashboard.layout.cols 
    : {
        lg: 12,
        md: 10,
        sm: 6,
        xs: 4,
        xxs: 2,
      };

  return (
    <ParameterManagerProvider
      dashboardId={dashboard.id}
      initialParameters={[
        // Example global parameters - in a real app, load from API
        {
          id: 'study_start_date',
          name: 'study_start_date',
          label: 'Study Start Date',
          type: 'date',
          description: 'Global study start date parameter',
          scope: 'study',
          widget_bindings: [],
          default_value: '2024-01-01',
          current_value: '2024-01-01',
          created_at: new Date(),
          updated_at: new Date(),
        },
        {
          id: 'study_end_date',
          name: 'study_end_date',
          label: 'Study End Date',
          type: 'date',
          description: 'Global study end date parameter',
          scope: 'study',
          widget_bindings: [],
          default_value: '2024-12-31',
          current_value: '2024-12-31',
          created_at: new Date(),
          updated_at: new Date(),
        },
      ]}
      onParametersChange={(parameters) => {
        console.log('Dashboard parameters changed:', parameters);
      }}
      onSave={async (parameters) => {
        // Save parameters to backend
        console.log('Saving parameters:', parameters);
      }}
    >
      <DrillDownManagerProvider
        dashboardId={dashboard.id}
        onDrillDown={(path) => {
          console.log('Drill-down path changed:', path);
        }}
        onNavigate={(level) => {
          console.log('Navigated to level:', level);
        }}
      >
        <FilterManagerProvider 
          dashboardId={dashboard.id}
          onFiltersChange={(filters) => {
            // Optional: Handle dashboard-level filter changes
            console.log('Dashboard filters changed:', filters);
          }}
        >
        <div className={cn("flex flex-col h-full", className)}>
        <DashboardToolbar
        title={dashboard.name}
        description={dashboard.description}
        lastUpdated={new Date(dashboard.updatedAt)}
        isFullscreen={isFullscreen}
        isRefreshing={isRefreshing}
        onRefresh={handleRefreshAll}
        onToggleFullscreen={handleToggleFullscreen}
        onExport={handleExport}
        onShare={handleShare}
        onSettings={!readOnly ? handleSettings : undefined}
        onTimeRangeChange={setTimeRange}
        timeRange={timeRange}
      />

      <div className="flex-1 overflow-auto p-4 bg-muted/10">
        {dashboard.widgets.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <h3 className="text-lg font-medium text-muted-foreground mb-2">
                No widgets configured
              </h3>
              <p className="text-sm text-muted-foreground">
                {readOnly
                  ? 'This dashboard has no widgets.'
                  : 'Add widgets to start building your dashboard.'}
              </p>
            </div>
          </div>
        ) : (
          <RealTimeCursors
            dashboardId={dashboard.id}
            currentUserId="current-user-id" // Would come from auth context
            currentUserName="Current User"   // Would come from auth context
            showPresenceList={!readOnly}
            className="relative"
          >
            <ResponsiveGridLayout
            className="layout"
            layouts={layouts}
            breakpoints={breakpoints}
            cols={cols}
            rowHeight={dashboard.layout?.rowHeight || 60}
            onLayoutChange={handleLayoutChange}
            isDraggable={!readOnly}
            isResizable={!readOnly}
            margin={[16, 16]}
            containerPadding={[0, 0]}
            compactType="vertical"
            preventCollision={false}
          >
            {dashboard.widgets.map((widget) => (
              <div key={widget.id} className="dashboard-widget">
                <WidgetContainer
                  widgetInstance={widget}
                  studyId={studyId}
                  onEdit={onEdit ? () => onEdit(widget.id) : undefined}
                  onDelete={onDelete ? () => onDelete(widget.id) : undefined}
                  readOnly={readOnly}
                  className="h-full"
                />
              </div>
            ))}
            </ResponsiveGridLayout>
          </RealTimeCursors>
        )}
      </div>

      <style jsx global>{`
        .react-grid-layout {
          position: relative;
        }
        
        .react-grid-item {
          transition: all 200ms ease;
          transition-property: left, top, width, height;
        }
        
        .react-grid-item.cssTransforms {
          transition-property: transform, width, height;
        }
        
        .react-grid-item.resizing {
          opacity: 0.9;
          z-index: 1;
        }
        
        .react-grid-item.react-draggable-dragging {
          opacity: 0.8;
          z-index: 2;
        }
        
        .react-grid-item > .react-resizable-handle {
          position: absolute;
          width: 20px;
          height: 20px;
          background: transparent;
        }
        
        .react-grid-item > .react-resizable-handle::after {
          content: "";
          position: absolute;
          right: 3px;
          bottom: 3px;
          width: 5px;
          height: 5px;
          border-right: 2px solid rgba(0, 0, 0, 0.4);
          border-bottom: 2px solid rgba(0, 0, 0, 0.4);
        }
        
        .react-resizable-hide > .react-resizable-handle {
          display: none;
        }
        
        .dashboard-widget {
          height: 100%;
          background: transparent;
        }
      `}</style>
        </div>
        </FilterManagerProvider>
      </DrillDownManagerProvider>
    </ParameterManagerProvider>
  );
}