// ABOUTME: Main canvas component using React Grid Layout for dashboard designer
// ABOUTME: Handles drag, drop, resize, and widget rendering with responsive layouts

"use client"

import { useCallback, useState } from "react"
import { Responsive, WidthProvider, Layout } from "react-grid-layout"
import { cn } from "@/lib/utils"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { 
  X, 
  GripVertical,
  BarChart3,
  LineChart,
  PieChart,
  Table2,
  Hash,
  Type,
  Activity,
  TrendingUp,
  Map,
  Grid3x3,
  Loader2
} from "lucide-react"

// Import react-grid-layout CSS
import "react-grid-layout/css/styles.css"
import "react-resizable/css/styles.css"

const ResponsiveGridLayout = WidthProvider(Responsive)

interface DesignCanvasProps {
  layout: any[]
  onLayoutChange: (layout: any[]) => void
  onWidgetSelect: (widgetId: string | null) => void
  onWidgetDelete: (widgetId: string) => void
  onWidgetDrop: (widgetType: string, position: { x: number; y: number }) => void
  selectedWidget: string | null
  showGrid: boolean
  mode: "design" | "preview"
  breakpoint: "lg" | "md" | "sm" | "xs"
}

// Widget icon mapping
const widgetIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  "metric-card": Hash,
  "line-chart": LineChart,
  "bar-chart": BarChart3,
  "pie-chart": PieChart,
  "table": Table2,
  "text": Type,
  "scatter-plot": Activity,
  "heatmap": Grid3x3,
  "geo-map": Map,
  "progress": Loader2
}

export function DesignCanvas({
  layout,
  onLayoutChange,
  onWidgetSelect,
  onWidgetDelete,
  onWidgetDrop,
  selectedWidget,
  showGrid,
  mode,
  breakpoint
}: DesignCanvasProps) {
  const [isDraggingOver, setIsDraggingOver] = useState(false)

  // Handle layout changes from grid
  const handleLayoutChange = useCallback((newLayout: Layout[]) => {
    // Update layout with new positions
    const updatedLayout = layout.map(item => {
      const gridItem = newLayout.find(l => l.i === item.i)
      if (gridItem) {
        return {
          ...item,
          x: gridItem.x,
          y: gridItem.y,
          w: gridItem.w,
          h: gridItem.h
        }
      }
      return item
    })
    onLayoutChange(updatedLayout)
  }, [layout, onLayoutChange])

  // Handle drag over canvas
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = "copy"
    setIsDraggingOver(true)
  }

  // Handle drag leave
  const handleDragLeave = () => {
    setIsDraggingOver(false)
  }

  // Handle drop on canvas
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDraggingOver(false)

    const widgetType = e.dataTransfer.getData("widgetType")
    if (!widgetType) return

    // Calculate grid position from mouse position
    const rect = e.currentTarget.getBoundingClientRect()
    const x = Math.floor((e.clientX - rect.left) / (rect.width / 12))
    const y = Math.floor((e.clientY - rect.top) / 50) // Assuming row height of 50px

    onWidgetDrop(widgetType, { x: Math.min(x, 11), y: Math.max(y, 0) })
  }

  // Render individual widget
  const renderWidget = (item: any) => {
    const Icon = widgetIcons[item.type] || Grid3x3
    const isSelected = selectedWidget === item.i
    const isDesignMode = mode === "design"

    return (
      <Card
        key={item.i}
        className={cn(
          "h-full overflow-hidden transition-all",
          isDesignMode && "cursor-move",
          isSelected && "ring-2 ring-primary",
          !isDesignMode && "cursor-default"
        )}
        onClick={(e) => {
          e.stopPropagation()
          if (isDesignMode) {
            onWidgetSelect(item.i)
          }
        }}
      >
        {/* Widget Header */}
        <div className="px-4 py-3 border-b bg-muted/50 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {isDesignMode && (
              <GripVertical className="h-4 w-4 text-muted-foreground drag-handle" />
            )}
            <Icon className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">
              {item.config?.title || "Untitled Widget"}
            </span>
          </div>
          {isDesignMode && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={(e) => {
                e.stopPropagation()
                onWidgetDelete(item.i)
              }}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>

        {/* Widget Content */}
        <div className="p-4 h-[calc(100%-49px)] flex items-center justify-center">
          {mode === "preview" ? (
            <div className="text-center">
              <Icon className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">
                Widget preview will appear here
              </p>
            </div>
          ) : (
            <div className="text-center">
              <p className="text-xs text-muted-foreground">
                {item.type.replace(/-/g, " ")}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {item.w} × {item.h}
              </p>
            </div>
          )}
        </div>
      </Card>
    )
  }

  // Define responsive breakpoints
  const breakpoints = { lg: 1200, md: 996, sm: 768, xs: 480 }
  const cols = { lg: 12, md: 10, sm: 6, xs: 4 }

  // Convert layout for different breakpoints
  const layouts = {
    lg: layout,
    md: layout,
    sm: layout,
    xs: layout
  }

  return (
    <div
      className={cn(
        "h-full w-full p-6",
        showGrid && "design-canvas-grid",
        isDraggingOver && "bg-accent/10"
      )}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => onWidgetSelect(null)}
    >
      {layout.length === 0 && mode === "design" ? (
        <div className="h-full flex items-center justify-center">
          <div className="text-center">
            <Grid3x3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">Start Building Your Dashboard</h3>
            <p className="text-sm text-muted-foreground max-w-md">
              Drag widgets from the left panel and drop them here to begin creating your dashboard
            </p>
          </div>
        </div>
      ) : (
        <ResponsiveGridLayout
          className="layout"
          layouts={layouts}
          breakpoints={breakpoints}
          cols={cols}
          rowHeight={50}
          isDraggable={mode === "design"}
          isResizable={mode === "design"}
          onLayoutChange={handleLayoutChange}
          draggableHandle=".drag-handle"
          margin={[16, 16]}
          containerPadding={[0, 0]}
        >
          {layout.map(renderWidget)}
        </ResponsiveGridLayout>
      )}
    </div>
  )
}