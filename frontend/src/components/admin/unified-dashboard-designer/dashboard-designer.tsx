// ABOUTME: Dashboard designer component for laying out widgets on a grid
// ABOUTME: Provides drag-and-drop grid layout with widget configuration

"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useDrop } from "react-dnd";
import { Responsive, WidthProvider } from "react-grid-layout";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";
import { 
  Settings, 
  Trash2, 
  Eye, 
  EyeOff,
  Grid3x3,
  AlignLeft,
  AlignCenterHorizontal,
  AlignRight,
  AlignVerticalJustifyStart,
  AlignCenterVertical,
  AlignVerticalJustifyEnd,
  Columns3,
  Rows3,
  Copy,
  Clipboard,
  Undo2,
  Redo2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Toggle } from "@/components/ui/toggle";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { WidgetRenderer } from "./widget-renderer";
import { WidgetConfigDialog } from "./widget-config-dialog";
import { cn } from "@/lib/utils";
import type { DashboardTemplateWithMenu, DashboardWidget } from "@/lib/api/dashboard-templates";

const ResponsiveGridLayout = WidthProvider(Responsive);

interface DashboardDesignerProps {
  dashboard: DashboardTemplateWithMenu;
  widgets: DashboardWidget[];
  onUpdateWidget: (widgetId: string, updates: Partial<DashboardWidget>) => void;
  onDeleteWidget: (widgetId: string) => void;
}

interface HistoryEntry {
  widgets: DashboardWidget[];
  description: string;
}

export function DashboardDesigner({
  dashboard,
  widgets,
  onUpdateWidget,
  onDeleteWidget,
}: DashboardDesignerProps) {
  const [selectedWidgetId, setSelectedWidgetId] = useState<string | null>(null);
  const [selectedWidgetIds, setSelectedWidgetIds] = useState<Set<string>>(new Set());
  const [configWidgetId, setConfigWidgetId] = useState<string | null>(null);
  const [deleteWidgetId, setDeleteWidgetId] = useState<string | null>(null);
  const [gridSnapping, setGridSnapping] = useState(true);
  const [copiedWidget, setCopiedWidget] = useState<DashboardWidget | null>(null);
  
  // History management for undo/redo
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const isApplyingHistory = useRef(false);

  // Handle drag and drop from palette
  const [{ isOver }, drop] = useDrop({
    accept: "widget",
    drop: (item: { widgetDefId: string }, monitor) => {
      // Widget addition is handled by the parent component
      return { dropped: true };
    },
    collect: (monitor) => ({
      isOver: !!monitor.isOver(),
    }),
  });

  // Initialize history with current state
  useEffect(() => {
    if (history.length === 0 && widgets.length > 0) {
      setHistory([{ widgets: [...widgets], description: "Initial state" }]);
      setHistoryIndex(0);
    }
  }, []);

  // Add to history when widgets change (excluding history-based changes)
  const addToHistory = useCallback((description: string) => {
    if (isApplyingHistory.current) return;
    
    const newEntry: HistoryEntry = {
      widgets: widgets.map(w => ({ ...w })),
      description
    };
    
    // Remove any entries after current index
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(newEntry);
    
    // Limit history to 50 entries
    if (newHistory.length > 50) {
      newHistory.shift();
    }
    
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  }, [widgets, history, historyIndex]);

  // Undo function
  const undo = useCallback(() => {
    if (historyIndex > 0) {
      isApplyingHistory.current = true;
      const newIndex = historyIndex - 1;
      const historyEntry = history[newIndex];
      
      // Apply the historical state
      historyEntry.widgets.forEach(widget => {
        onUpdateWidget(widget.widgetInstanceId, widget);
      });
      
      setHistoryIndex(newIndex);
      toast.success(`Undo: ${historyEntry.description}`);
      
      setTimeout(() => {
        isApplyingHistory.current = false;
      }, 100);
    }
  }, [history, historyIndex, onUpdateWidget]);

  // Redo function
  const redo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      isApplyingHistory.current = true;
      const newIndex = historyIndex + 1;
      const historyEntry = history[newIndex];
      
      // Apply the historical state
      historyEntry.widgets.forEach(widget => {
        onUpdateWidget(widget.widgetInstanceId, widget);
      });
      
      setHistoryIndex(newIndex);
      toast.success(`Redo: ${historyEntry.description}`);
      
      setTimeout(() => {
        isApplyingHistory.current = false;
      }, 100);
    }
  }, [history, historyIndex, onUpdateWidget]);

  // Copy widget
  const copyWidget = useCallback(() => {
    const widget = widgets.find(w => w.widgetInstanceId === selectedWidgetId);
    if (widget) {
      setCopiedWidget(widget);
      toast.success("Widget copied");
    }
  }, [selectedWidgetId, widgets]);

  // Paste widget
  const pasteWidget = useCallback(() => {
    if (copiedWidget) {
      // Generate new widget ID
      const newWidgetId = `widget-${Date.now()}`;
      
      // Calculate paste position (offset from original)
      const newWidget: DashboardWidget = {
        ...copiedWidget,
        widgetInstanceId: newWidgetId,
        position: {
          ...copiedWidget.position,
          x: Math.min(copiedWidget.position.x + 1, 10), // Offset by 1 grid unit
          y: copiedWidget.position.y + 1,
        },
      };
      
      // This would need to be handled by parent component
      // For now, we'll just show a message
      toast.info("Paste functionality requires parent component integration");
      addToHistory("Pasted widget");
    }
  }, [copiedWidget, addToHistory]);

  // Alignment functions
  const alignWidgets = useCallback((alignment: 'left' | 'center' | 'right' | 'top' | 'middle' | 'bottom') => {
    if (selectedWidgetIds.size < 2) {
      toast.warning("Select at least 2 widgets to align");
      return;
    }

    const selectedWidgets = widgets.filter(w => selectedWidgetIds.has(w.widgetInstanceId));
    let updates: Array<{ id: string; position: DashboardWidget['position'] }> = [];

    switch (alignment) {
      case 'left': {
        const minX = Math.min(...selectedWidgets.map(w => w.position.x));
        updates = selectedWidgets.map(w => ({
          id: w.widgetInstanceId,
          position: { ...w.position, x: minX }
        }));
        break;
      }
      case 'center': {
        const minX = Math.min(...selectedWidgets.map(w => w.position.x));
        const maxX = Math.max(...selectedWidgets.map(w => w.position.x + w.position.width));
        const centerX = (minX + maxX) / 2;
        updates = selectedWidgets.map(w => ({
          id: w.widgetInstanceId,
          position: { ...w.position, x: Math.round(centerX - w.position.width / 2) }
        }));
        break;
      }
      case 'right': {
        const maxX = Math.max(...selectedWidgets.map(w => w.position.x + w.position.width));
        updates = selectedWidgets.map(w => ({
          id: w.widgetInstanceId,
          position: { ...w.position, x: maxX - w.position.width }
        }));
        break;
      }
      case 'top': {
        const minY = Math.min(...selectedWidgets.map(w => w.position.y));
        updates = selectedWidgets.map(w => ({
          id: w.widgetInstanceId,
          position: { ...w.position, y: minY }
        }));
        break;
      }
      case 'middle': {
        const minY = Math.min(...selectedWidgets.map(w => w.position.y));
        const maxY = Math.max(...selectedWidgets.map(w => w.position.y + w.position.height));
        const centerY = (minY + maxY) / 2;
        updates = selectedWidgets.map(w => ({
          id: w.widgetInstanceId,
          position: { ...w.position, y: Math.round(centerY - w.position.height / 2) }
        }));
        break;
      }
      case 'bottom': {
        const maxY = Math.max(...selectedWidgets.map(w => w.position.y + w.position.height));
        updates = selectedWidgets.map(w => ({
          id: w.widgetInstanceId,
          position: { ...w.position, y: maxY - w.position.height }
        }));
        break;
      }
    }

    updates.forEach(update => {
      onUpdateWidget(update.id, { position: update.position });
    });
    
    addToHistory(`Aligned widgets ${alignment}`);
    toast.success(`Widgets aligned ${alignment}`);
  }, [selectedWidgetIds, widgets, onUpdateWidget, addToHistory]);

  // Distribute widgets evenly
  const distributeWidgets = useCallback((direction: 'horizontal' | 'vertical') => {
    if (selectedWidgetIds.size < 3) {
      toast.warning("Select at least 3 widgets to distribute");
      return;
    }

    const selectedWidgets = widgets.filter(w => selectedWidgetIds.has(w.widgetInstanceId));
    let updates: Array<{ id: string; position: DashboardWidget['position'] }> = [];

    if (direction === 'horizontal') {
      const sortedWidgets = [...selectedWidgets].sort((a, b) => a.position.x - b.position.x);
      const firstWidget = sortedWidgets[0];
      const lastWidget = sortedWidgets[sortedWidgets.length - 1];
      const totalSpace = lastWidget.position.x - firstWidget.position.x;
      const spacing = totalSpace / (sortedWidgets.length - 1);

      updates = sortedWidgets.map((w, index) => ({
        id: w.widgetInstanceId,
        position: { ...w.position, x: Math.round(firstWidget.position.x + spacing * index) }
      }));
    } else {
      const sortedWidgets = [...selectedWidgets].sort((a, b) => a.position.y - b.position.y);
      const firstWidget = sortedWidgets[0];
      const lastWidget = sortedWidgets[sortedWidgets.length - 1];
      const totalSpace = lastWidget.position.y - firstWidget.position.y;
      const spacing = totalSpace / (sortedWidgets.length - 1);

      updates = sortedWidgets.map((w, index) => ({
        id: w.widgetInstanceId,
        position: { ...w.position, y: Math.round(firstWidget.position.y + spacing * index) }
      }));
    }

    updates.forEach(update => {
      onUpdateWidget(update.id, { position: update.position });
    });
    
    addToHistory(`Distributed widgets ${direction}ly`);
    toast.success(`Widgets distributed ${direction}ly`);
  }, [selectedWidgetIds, widgets, onUpdateWidget, addToHistory]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + C
      if ((e.ctrlKey || e.metaKey) && e.key === 'c' && selectedWidgetId) {
        e.preventDefault();
        copyWidget();
      }
      // Ctrl/Cmd + V
      if ((e.ctrlKey || e.metaKey) && e.key === 'v' && copiedWidget) {
        e.preventDefault();
        pasteWidget();
      }
      // Ctrl/Cmd + Z
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        undo();
      }
      // Ctrl/Cmd + Y or Ctrl/Cmd + Shift + Z
      if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        redo();
      }
      // Delete key
      if (e.key === 'Delete' && selectedWidgetId) {
        e.preventDefault();
        setDeleteWidgetId(selectedWidgetId);
      }
      // Escape key to clear selection
      if (e.key === 'Escape') {
        setSelectedWidgetId(null);
        setSelectedWidgetIds(new Set());
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedWidgetId, copiedWidget, copyWidget, pasteWidget, undo, redo]);

  // Handle widget selection (single and multi-select)
  const handleWidgetClick = useCallback((widgetId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (e.ctrlKey || e.metaKey) {
      // Multi-select
      const newSelection = new Set(selectedWidgetIds);
      if (newSelection.has(widgetId)) {
        newSelection.delete(widgetId);
      } else {
        newSelection.add(widgetId);
      }
      setSelectedWidgetIds(newSelection);
      setSelectedWidgetId(widgetId);
    } else {
      // Single select
      setSelectedWidgetIds(new Set([widgetId]));
      setSelectedWidgetId(widgetId);
    }
  }, [selectedWidgetIds]);

  // Convert widgets to grid layout format
  const layouts = {
    lg: widgets.map((widget) => ({
      i: widget.widgetInstanceId,
      x: widget.position.x,
      y: widget.position.y,
      w: widget.position.width,
      h: widget.position.height,
    })),
  };

  // Handle layout change
  const handleLayoutChange = (currentLayout: any[], allLayouts: any) => {
    let hasChanges = false;
    currentLayout.forEach((item) => {
      const widget = widgets.find((w) => w.widgetInstanceId === item.i);
      if (
        widget &&
        (widget.position.x !== item.x ||
          widget.position.y !== item.y ||
          widget.position.width !== item.w ||
          widget.position.height !== item.h)
      ) {
        hasChanges = true;
        onUpdateWidget(item.i, {
          position: {
            x: item.x,
            y: item.y,
            width: item.w,
            height: item.h,
          },
        });
      }
    });
    
    if (hasChanges && !isApplyingHistory.current) {
      addToHistory("Moved/resized widgets");
    }
  };

  const configWidget = configWidgetId
    ? widgets.find((w) => w.widgetInstanceId === configWidgetId)
    : null;

  return (
    <TooltipProvider>
      <div className="flex flex-col h-full">
        {/* Toolbar */}
        <div className="flex items-center gap-2 p-2 border-b bg-background">
          {/* Grid Snapping */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Toggle
                pressed={gridSnapping}
                onPressedChange={setGridSnapping}
                size="sm"
                aria-label="Toggle grid snapping"
              >
                <Grid3x3 className="h-4 w-4" />
              </Toggle>
            </TooltipTrigger>
            <TooltipContent>
              <p>Grid Snapping {gridSnapping ? "On" : "Off"}</p>
            </TooltipContent>
          </Tooltip>

          <Separator orientation="vertical" className="h-6" />

          {/* Alignment Tools */}
          <div className="flex items-center gap-1">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => alignWidgets('left')}
                  disabled={selectedWidgetIds.size < 2}
                >
                  <AlignLeft className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Align Left</p>
              </TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => alignWidgets('center')}
                  disabled={selectedWidgetIds.size < 2}
                >
                  <AlignCenterHorizontal className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Align Center</p>
              </TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => alignWidgets('right')}
                  disabled={selectedWidgetIds.size < 2}
                >
                  <AlignRight className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Align Right</p>
              </TooltipContent>
            </Tooltip>

            <Separator orientation="vertical" className="h-6 mx-1" />

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => alignWidgets('top')}
                  disabled={selectedWidgetIds.size < 2}
                >
                  <AlignVerticalJustifyStart className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Align Top</p>
              </TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => alignWidgets('middle')}
                  disabled={selectedWidgetIds.size < 2}
                >
                  <AlignCenterVertical className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Align Middle</p>
              </TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => alignWidgets('bottom')}
                  disabled={selectedWidgetIds.size < 2}
                >
                  <AlignVerticalJustifyEnd className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Align Bottom</p>
              </TooltipContent>
            </Tooltip>

            <Separator orientation="vertical" className="h-6 mx-1" />

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => distributeWidgets('horizontal')}
                  disabled={selectedWidgetIds.size < 3}
                >
                  <Columns3 className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Distribute Horizontally</p>
              </TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => distributeWidgets('vertical')}
                  disabled={selectedWidgetIds.size < 3}
                >
                  <Rows3 className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Distribute Vertically</p>
              </TooltipContent>
            </Tooltip>
          </div>

          <Separator orientation="vertical" className="h-6" />

          {/* Copy/Paste */}
          <div className="flex items-center gap-1">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={copyWidget}
                  disabled={!selectedWidgetId}
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Copy Widget (Ctrl+C)</p>
              </TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={pasteWidget}
                  disabled={!copiedWidget}
                >
                  <Clipboard className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Paste Widget (Ctrl+V)</p>
              </TooltipContent>
            </Tooltip>
          </div>

          <Separator orientation="vertical" className="h-6" />

          {/* Undo/Redo */}
          <div className="flex items-center gap-1">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={undo}
                  disabled={historyIndex <= 0}
                >
                  <Undo2 className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Undo (Ctrl+Z)</p>
              </TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={redo}
                  disabled={historyIndex >= history.length - 1}
                >
                  <Redo2 className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Redo (Ctrl+Y)</p>
              </TooltipContent>
            </Tooltip>
          </div>

          <div className="flex-1" />

          {/* Selection info */}
          {selectedWidgetIds.size > 0 && (
            <div className="text-sm text-muted-foreground">
              {selectedWidgetIds.size} widget{selectedWidgetIds.size > 1 ? 's' : ''} selected
            </div>
          )}
        </div>

        <div
        ref={drop as any}
        className={cn(
          "flex-1 min-h-0 w-full rounded-lg border-2 border-dashed p-6 relative overflow-auto",
          "bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-950",
          isOver && "border-primary bg-primary/5"
        )}
        style={{
          backgroundImage: `
            linear-gradient(rgba(156, 163, 175, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(156, 163, 175, 0.1) 1px, transparent 1px),
            linear-gradient(rgba(156, 163, 175, 0.05) 2px, transparent 2px),
            linear-gradient(90deg, rgba(156, 163, 175, 0.05) 2px, transparent 2px)
          `,
          backgroundSize: '20px 20px, 20px 20px, 100px 100px, 100px 100px',
          backgroundPosition: '0 0, 0 0, 0 0, 0 0'
        }}
      >
        {widgets.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center text-muted-foreground">
              <p className="mb-2">No widgets added yet</p>
              <p className="text-sm">
                Drag widgets from the palette to start building your dashboard
              </p>
            </div>
          </div>
        ) : (
          <div className="h-full w-full">
            <ResponsiveGridLayout
              className="layout h-full"
              layouts={layouts}
              breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
              cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
              rowHeight={dashboard.layout.rowHeight || 80}
              margin={dashboard.layout.margin || [16, 16]}
              containerPadding={dashboard.layout.containerPadding ? 
                [dashboard.layout.containerPadding[0], dashboard.layout.containerPadding[1]] as [number, number]
                : [0, 0]}
              onLayoutChange={handleLayoutChange}
              draggableHandle=".widget-drag-handle"
              isDraggable={!isApplyingHistory.current}
              isResizable={!isApplyingHistory.current}
              compactType={gridSnapping ? "vertical" : null}
            >
            {widgets.map((widget) => (
              <div
                key={widget.widgetInstanceId}
                className={cn(
                  "group relative overflow-hidden rounded-lg border bg-background shadow-sm",
                  selectedWidgetIds.has(widget.widgetInstanceId) && "ring-2 ring-primary",
                  selectedWidgetId === widget.widgetInstanceId && "ring-2 ring-primary ring-offset-2"
                )}
                onClick={(e) => handleWidgetClick(widget.widgetInstanceId, e)}
              >
                {/* Widget toolbar */}
                <div className="absolute right-2 top-2 z-10 flex items-center gap-1 opacity-0 group-hover:opacity-100">
                  <Button
                    variant="secondary"
                    size="icon"
                    className="h-6 w-6"
                    onClick={(e) => {
                      e.stopPropagation();
                      onUpdateWidget(widget.widgetInstanceId, {
                        isVisible: !widget.isVisible,
                      });
                    }}
                  >
                    {widget.isVisible ? (
                      <Eye className="h-3 w-3" />
                    ) : (
                      <EyeOff className="h-3 w-3" />
                    )}
                  </Button>
                  <Button
                    variant="secondary"
                    size="icon"
                    className="h-6 w-6"
                    onClick={(e) => {
                      e.stopPropagation();
                      setConfigWidgetId(widget.widgetInstanceId);
                    }}
                  >
                    <Settings className="h-3 w-3" />
                  </Button>
                  <Button
                    variant="destructive"
                    size="icon"
                    className="h-6 w-6"
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteWidgetId(widget.widgetInstanceId);
                    }}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>

                {/* Drag handle */}
                <div className="widget-drag-handle absolute inset-x-0 top-0 h-8 cursor-move" />

                {/* Widget content */}
                <div className={cn("h-full p-4", !widget.isVisible && "opacity-50")}>
                  <WidgetRenderer widget={widget} />
                </div>
              </div>
            ))}
            </ResponsiveGridLayout>
          </div>
        )}
      </div>

      {/* Widget configuration dialog */}
      {configWidget && (
        <WidgetConfigDialog
          widget={configWidget}
          open={!!configWidgetId}
          onOpenChange={(open) => {
            if (!open) setConfigWidgetId(null);
          }}
          onSave={(updates) => {
            onUpdateWidget(configWidget.widgetInstanceId, updates);
            setConfigWidgetId(null);
          }}
        />
      )}

      {/* Delete confirmation dialog */}
      <Dialog
        open={!!deleteWidgetId}
        onOpenChange={(open) => {
          if (!open) setDeleteWidgetId(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Widget</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this widget? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteWidgetId(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (deleteWidgetId) {
                  onDeleteWidget(deleteWidgetId);
                  setDeleteWidgetId(null);
                }
              }}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      </div>
    </TooltipProvider>
  );
}