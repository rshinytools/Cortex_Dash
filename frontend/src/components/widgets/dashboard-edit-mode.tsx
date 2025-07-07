// ABOUTME: Dashboard edit mode component that enables widget configuration and layout editing
// ABOUTME: Provides edit/view toggle, widget selection, and configuration updates

'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { Responsive, WidthProvider, Layout } from 'react-grid-layout';
import { DashboardConfiguration, WidgetInstance } from './base-widget';
import { WidgetRenderer } from './widget-renderer';
import { WidgetConfigDialog } from './widget-config-dialog';
import { WidgetPalette } from './widget-palette';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { useToast } from '@/hooks/use-toast';
import {
  Edit,
  Save,
  X,
  Settings,
  Trash2,
  Plus,
  Eye,
  EyeOff,
  Grid,
  Undo,
  Redo,
} from 'lucide-react';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import { cn } from '@/lib/utils';

const ResponsiveGridLayout = WidthProvider(Responsive);

interface DashboardEditModeProps {
  configuration: DashboardConfiguration;
  widgetData: Record<string, any>;
  widgetLoading?: Record<string, boolean>;
  widgetErrors?: Record<string, string>;
  onSave: (configuration: DashboardConfiguration) => Promise<void>;
  onCancel?: () => void;
  onRefreshWidget?: (widgetId: string) => void;
  className?: string;
}

interface EditHistory {
  past: DashboardConfiguration[];
  present: DashboardConfiguration;
  future: DashboardConfiguration[];
}

export const DashboardEditMode: React.FC<DashboardEditModeProps> = ({
  configuration: initialConfiguration,
  widgetData,
  widgetLoading = {},
  widgetErrors = {},
  onSave,
  onCancel,
  onRefreshWidget,
  className,
}) => {
  const { toast } = useToast();
  const [isEditMode, setIsEditMode] = useState(false);
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);
  const [selectedWidget, setSelectedWidget] = useState<string | null>(null);
  const [configDialogWidget, setConfigDialogWidget] = useState<WidgetInstance | null>(null);
  const [showGrid, setShowGrid] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  // Edit history for undo/redo
  const [history, setHistory] = useState<EditHistory>({
    past: [],
    present: initialConfiguration,
    future: [],
  });

  const configuration = history.present;

  // Update history when initial configuration changes
  useEffect(() => {
    setHistory({
      past: [],
      present: initialConfiguration,
      future: [],
    });
  }, [initialConfiguration]);

  // Add configuration to history
  const addToHistory = useCallback((newConfig: DashboardConfiguration) => {
    setHistory((prev) => ({
      past: [...prev.past, prev.present],
      present: newConfig,
      future: [],
    }));
  }, []);

  // Undo action
  const handleUndo = useCallback(() => {
    if (history.past.length === 0) return;

    const previous = history.past[history.past.length - 1];
    const newPast = history.past.slice(0, -1);

    setHistory({
      past: newPast,
      present: previous,
      future: [configuration, ...history.future],
    });
  }, [configuration, history]);

  // Redo action
  const handleRedo = useCallback(() => {
    if (history.future.length === 0) return;

    const next = history.future[0];
    const newFuture = history.future.slice(1);

    setHistory({
      past: [...history.past, configuration],
      present: next,
      future: newFuture,
    });
  }, [configuration, history]);

  // Handle layout changes
  const handleLayoutChange = useCallback(
    (layout: Layout[], layouts: any) => {
      const updatedWidgets = configuration.widgets.map((widget) => {
        const layoutItem = layout.find((item) => item.i === widget.id);
        if (layoutItem) {
          return {
            ...widget,
            layout: {
              ...widget.layout,
              x: layoutItem.x,
              y: layoutItem.y,
              w: layoutItem.w,
              h: layoutItem.h,
            },
          };
        }
        return widget;
      });

      const newConfig = {
        ...configuration,
        widgets: updatedWidgets,
      };

      addToHistory(newConfig);
    },
    [configuration, addToHistory]
  );

  // Delete widget
  const handleDeleteWidget = useCallback(
    (widgetId: string) => {
      const newConfig = {
        ...configuration,
        widgets: configuration.widgets.filter((w) => w.id !== widgetId),
      };

      addToHistory(newConfig);
      setSelectedWidget(null);
      toast({
        title: 'Widget removed',
        description: 'The widget has been removed from the dashboard.',
      });
    },
    [configuration, addToHistory, toast]
  );

  // Update widget configuration
  const handleUpdateWidget = useCallback(
    (updatedWidget: WidgetInstance) => {
      const newConfig = {
        ...configuration,
        widgets: configuration.widgets.map((w) =>
          w.id === updatedWidget.id ? updatedWidget : w
        ),
      };

      addToHistory(newConfig);
      setConfigDialogWidget(null);
    },
    [configuration, addToHistory]
  );

  // Add new widget
  const handleAddWidget = useCallback(
    (widget: WidgetInstance) => {
      // Find a free position for the new widget
      const occupiedPositions = new Set(
        configuration.widgets.map((w) => `${w.layout.x},${w.layout.y}`)
      );

      let x = 0;
      let y = 0;
      let found = false;

      // Simple algorithm to find free space
      for (let row = 0; row < 20 && !found; row++) {
        for (let col = 0; col < configuration.layout.cols; col++) {
          const canFit = widget.layout.w <= configuration.layout.cols - col;
          let isFree = true;

          if (canFit) {
            for (let dx = 0; dx < widget.layout.w; dx++) {
              for (let dy = 0; dy < widget.layout.h; dy++) {
                if (occupiedPositions.has(`${col + dx},${row + dy}`)) {
                  isFree = false;
                  break;
                }
              }
              if (!isFree) break;
            }
          }

          if (canFit && isFree) {
            x = col;
            y = row;
            found = true;
            break;
          }
        }
      }

      const newWidget = {
        ...widget,
        layout: {
          ...widget.layout,
          x,
          y,
        },
      };

      const newConfig = {
        ...configuration,
        widgets: [...configuration.widgets, newWidget],
      };

      addToHistory(newConfig);
      setIsPaletteOpen(false);
      toast({
        title: 'Widget added',
        description: 'New widget has been added to the dashboard.',
      });
    },
    [configuration, addToHistory, toast]
  );

  // Save dashboard
  const handleSave = useCallback(async () => {
    setIsSaving(true);
    try {
      await onSave(configuration);
      setIsEditMode(false);
      toast({
        title: 'Dashboard saved',
        description: 'Your changes have been saved successfully.',
      });
    } catch (error) {
      toast({
        title: 'Save failed',
        description: 'Failed to save dashboard changes. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  }, [configuration, onSave, toast]);

  // Cancel editing
  const handleCancel = useCallback(() => {
    setHistory({
      past: [],
      present: initialConfiguration,
      future: [],
    });
    setIsEditMode(false);
    setSelectedWidget(null);
    if (onCancel) {
      onCancel();
    }
  }, [initialConfiguration, onCancel]);

  // Widget click handler
  const handleWidgetClick = useCallback(
    (widgetId: string) => {
      if (isEditMode) {
        setSelectedWidget(widgetId === selectedWidget ? null : widgetId);
      }
    },
    [isEditMode, selectedWidget]
  );

  // Generate layouts for responsive grid
  const layouts = React.useMemo(() => {
    const baseLayout = configuration.widgets.map((widget) => ({
      i: widget.id,
      x: widget.layout.x,
      y: widget.layout.y,
      w: widget.layout.w,
      h: widget.layout.h,
      minW: widget.layout.minW || 1,
      minH: widget.layout.minH || 1,
      maxW: widget.layout.maxW,
      maxH: widget.layout.maxH,
      static: !isEditMode,
    }));

    return {
      lg: baseLayout,
      md: baseLayout,
      sm: baseLayout,
      xs: baseLayout,
      xxs: baseLayout,
    };
  }, [configuration.widgets, isEditMode]);

  const breakpoints = configuration.layout.breakpoints || {
    lg: 1200,
    md: 996,
    sm: 768,
    xs: 480,
    xxs: 0,
  };

  const cols = {
    lg: configuration.layout.cols || 12,
    md: configuration.layout.cols || 12,
    sm: configuration.layout.cols || 12,
    xs: configuration.layout.cols || 12,
    xxs: configuration.layout.cols || 12,
  };

  return (
    <div className={cn('dashboard-edit-mode', className)}>
      {/* Toolbar */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={isEditMode ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setIsEditMode(!isEditMode)}
                >
                  {isEditMode ? <Eye className="h-4 w-4" /> : <Edit className="h-4 w-4" />}
                  {isEditMode ? 'View Mode' : 'Edit Mode'}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                {isEditMode ? 'Switch to view mode' : 'Switch to edit mode'}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {isEditMode && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsPaletteOpen(true)}
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Widget
              </Button>

              <div className="flex items-center gap-1 ml-4">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={handleUndo}
                        disabled={history.past.length === 0}
                      >
                        <Undo className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Undo</TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={handleRedo}
                        disabled={history.future.length === 0}
                      >
                        <Redo className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Redo</TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setShowGrid(!showGrid)}
                    >
                      <Grid className={cn('h-4 w-4', showGrid && 'text-primary')} />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Toggle grid</TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </>
          )}
        </div>

        {isEditMode && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCancel}
              disabled={isSaving}
            >
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleSave}
              disabled={isSaving}
            >
              <Save className="h-4 w-4 mr-2" />
              {isSaving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        )}
      </div>

      {/* Dashboard Grid */}
      <div className={cn('dashboard-grid', showGrid && isEditMode && 'show-grid')}>
        <ResponsiveGridLayout
          className="layout"
          layouts={layouts}
          breakpoints={breakpoints}
          cols={cols}
          rowHeight={configuration.layout.rowHeight || 80}
          isDraggable={isEditMode}
          isResizable={isEditMode}
          onLayoutChange={handleLayoutChange}
          margin={[16, 16]}
          containerPadding={[0, 0]}
          useCSSTransforms={true}
        >
          {configuration.widgets.map((widget) => (
            <div
              key={widget.id}
              className={cn(
                'widget-wrapper',
                isEditMode && 'edit-mode',
                selectedWidget === widget.id && 'selected'
              )}
              onClick={() => handleWidgetClick(widget.id)}
            >
              <WidgetRenderer
                instance={widget}
                data={widgetData[widget.id]}
                loading={widgetLoading[widget.id]}
                error={widgetErrors[widget.id]}
                onRefresh={() => onRefreshWidget?.(widget.id)}
                viewMode={true}
              />

              {isEditMode && selectedWidget === widget.id && (
                <div className="widget-actions">
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="secondary"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => {
                            e.stopPropagation();
                            setConfigDialogWidget(widget);
                          }}
                        >
                          <Settings className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Configure widget</TooltipContent>
                    </Tooltip>
                  </TooltipProvider>

                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="destructive"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteWidget(widget.id);
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Delete widget</TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
              )}
            </div>
          ))}
        </ResponsiveGridLayout>
      </div>

      {/* Widget Palette */}
      {isPaletteOpen && (
        <WidgetPalette
          isOpen={isPaletteOpen}
          onClose={() => setIsPaletteOpen(false)}
          onAddWidget={handleAddWidget}
          existingWidgetIds={configuration.widgets.map((w) => w.id)}
        />
      )}

      {/* Widget Configuration Dialog */}
      {configDialogWidget && (
        <WidgetConfigDialog
          isOpen={!!configDialogWidget}
          onClose={() => setConfigDialogWidget(null)}
          widgetInstance={configDialogWidget}
          onSave={handleUpdateWidget}
          previewData={widgetData[configDialogWidget.id]}
        />
      )}

      <style jsx>{`
        .dashboard-grid.show-grid :global(.react-grid-layout) {
          background-image: 
            linear-gradient(to right, hsl(var(--border)) 1px, transparent 1px),
            linear-gradient(to bottom, hsl(var(--border)) 1px, transparent 1px);
          background-size: 16px 16px;
        }

        .widget-wrapper {
          position: relative;
          height: 100%;
          width: 100%;
          transition: all 0.2s;
        }

        .widget-wrapper.edit-mode {
          cursor: move;
        }

        .widget-wrapper.edit-mode:hover {
          outline: 2px dashed hsl(var(--primary) / 0.3);
          outline-offset: 2px;
        }

        .widget-wrapper.selected {
          outline: 2px solid hsl(var(--primary));
          outline-offset: 2px;
        }

        .widget-actions {
          position: absolute;
          top: 8px;
          right: 8px;
          display: flex;
          gap: 4px;
          z-index: 10;
        }

        .dashboard-grid :global(.react-grid-item) {
          transition: all 200ms ease;
          transition-property: left, top, width, height;
        }

        .dashboard-grid :global(.react-grid-item.cssTransforms) {
          transition-property: transform, width, height;
        }

        .dashboard-grid :global(.react-grid-item.resizing) {
          opacity: 0.9;
        }

        .dashboard-grid :global(.react-grid-item > .react-resizable-handle) {
          background-color: hsl(var(--primary));
          opacity: 0;
          transition: opacity 0.2s;
        }

        .widget-wrapper.edit-mode:hover :global(.react-resizable-handle),
        .widget-wrapper.selected :global(.react-resizable-handle) {
          opacity: 1;
        }
      `}</style>
    </div>
  );
};