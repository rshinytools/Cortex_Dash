// ABOUTME: Dashboard designer component for laying out widgets on a grid
// ABOUTME: Provides drag-and-drop grid layout with widget configuration

"use client";

import { useState } from "react";
import { useDrop } from "react-dnd";
import { Responsive, WidthProvider } from "react-grid-layout";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";
import { Settings, Trash2, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
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

export function DashboardDesigner({
  dashboard,
  widgets,
  onUpdateWidget,
  onDeleteWidget,
}: DashboardDesignerProps) {
  const [selectedWidgetId, setSelectedWidgetId] = useState<string | null>(null);
  const [configWidgetId, setConfigWidgetId] = useState<string | null>(null);
  const [deleteWidgetId, setDeleteWidgetId] = useState<string | null>(null);

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
    currentLayout.forEach((item) => {
      const widget = widgets.find((w) => w.widgetInstanceId === item.i);
      if (
        widget &&
        (widget.position.x !== item.x ||
          widget.position.y !== item.y ||
          widget.position.width !== item.w ||
          widget.position.height !== item.h)
      ) {
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
  };

  const configWidget = configWidgetId
    ? widgets.find((w) => w.widgetInstanceId === configWidgetId)
    : null;

  return (
    <>
      <div
        ref={drop as any}
        className={cn(
          "h-full rounded-lg border-2 border-dashed bg-muted/20 p-4",
          isOver && "border-primary bg-primary/5"
        )}
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
          <ResponsiveGridLayout
            className="layout"
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
          >
            {widgets.map((widget) => (
              <div
                key={widget.widgetInstanceId}
                className={cn(
                  "group relative overflow-hidden rounded-lg border bg-background shadow-sm",
                  selectedWidgetId === widget.widgetInstanceId && "ring-2 ring-primary"
                )}
                onClick={() => setSelectedWidgetId(widget.widgetInstanceId)}
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
    </>
  );
}