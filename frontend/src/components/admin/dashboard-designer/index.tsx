// ABOUTME: Main dashboard designer component with drag-and-drop grid layout
// ABOUTME: Orchestrates widget palette, canvas, and property panel for dashboard creation

"use client"

import { useState, useCallback } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { 
  Eye, 
  EyeOff, 
  Undo2, 
  Redo2, 
  Grid3x3,
  Smartphone,
  Tablet,
  Monitor
} from "lucide-react"
import { WidgetPalette } from "./widget-palette"
import { PropertyPanel } from "./property-panel"
import { DesignCanvas } from "./design-canvas"
import { useToast } from "@/hooks/use-toast"

interface DashboardDesignerProps {
  initialLayout?: any[]
  onChange?: (layout: any[]) => void
  mode?: "design" | "preview"
}

interface HistoryState {
  past: any[][]
  present: any[]
  future: any[][]
}

export function DashboardDesigner({ 
  initialLayout = [], 
  onChange,
  mode: initialMode = "design" 
}: DashboardDesignerProps) {
  const { toast } = useToast()
  const [mode, setMode] = useState(initialMode)
  const [showGrid, setShowGrid] = useState(true)
  const [selectedWidget, setSelectedWidget] = useState<string | null>(null)
  const [breakpoint, setBreakpoint] = useState<"lg" | "md" | "sm" | "xs">("lg")
  
  // Layout state with history for undo/redo
  const [history, setHistory] = useState<HistoryState>({
    past: [],
    present: initialLayout,
    future: []
  })

  const layout = history.present

  // Update layout with history tracking
  const updateLayout = useCallback((newLayout: any[], trackHistory = true) => {
    if (trackHistory) {
      setHistory(prev => ({
        past: [...prev.past, prev.present],
        present: newLayout,
        future: []
      }))
    } else {
      setHistory(prev => ({
        ...prev,
        present: newLayout
      }))
    }
    onChange?.(newLayout)
  }, [onChange])

  // Undo/Redo functionality
  const canUndo = history.past.length > 0
  const canRedo = history.future.length > 0

  const undo = () => {
    if (!canUndo) return
    
    const previous = history.past[history.past.length - 1]
    const newPast = history.past.slice(0, -1)
    
    setHistory({
      past: newPast,
      present: previous,
      future: [history.present, ...history.future]
    })
    onChange?.(previous)
  }

  const redo = () => {
    if (!canRedo) return
    
    const next = history.future[0]
    const newFuture = history.future.slice(1)
    
    setHistory({
      past: [...history.past, history.present],
      present: next,
      future: newFuture
    })
    onChange?.(next)
  }

  // Handle widget drop from palette
  const handleWidgetDrop = (widgetType: string, position: { x: number; y: number }) => {
    // Try to get widget data from temporary storage
    const widgetData = (window as any).__tempWidgetData
    delete (window as any).__tempWidgetData
    
    const newWidget = {
      i: `widget-${Date.now()}`,
      x: position.x,
      y: position.y,
      w: getDefaultWidth(widgetData),
      h: getDefaultHeight(widgetData),
      type: widgetType,
      widgetDefinitionId: widgetData?.id,
      config: getDefaultConfig(widgetData),
      widgetData: widgetData // Store full widget data for reference
    }
    
    updateLayout([...layout, newWidget])
    setSelectedWidget(newWidget.i)
    
    toast({
      title: "Widget added",
      description: `${widgetData?.name || widgetType} added to the dashboard`
    })
  }

  // Handle widget selection
  const handleWidgetSelect = (widgetId: string | null) => {
    setSelectedWidget(widgetId)
  }

  // Handle widget deletion
  const handleWidgetDelete = (widgetId: string) => {
    updateLayout(layout.filter(item => item.i !== widgetId))
    if (selectedWidget === widgetId) {
      setSelectedWidget(null)
    }
    
    toast({
      title: "Widget removed",
      description: "Widget has been removed from the dashboard"
    })
  }

  // Handle widget property update
  const handleWidgetUpdate = (widgetId: string, updates: any) => {
    updateLayout(
      layout.map(item => 
        item.i === widgetId 
          ? { ...item, ...updates }
          : item
      )
    )
  }

  // Get selected widget data
  const getSelectedWidget = () => {
    return layout.find(item => item.i === selectedWidget) || null
  }

  return (
    <div className="h-full flex">
      {/* Left Sidebar - Widget Palette */}
      {mode === "design" && (
        <div className="w-64 border-r bg-background overflow-y-auto">
          <WidgetPalette onDragStart={(type) => {}} />
        </div>
      )}

      {/* Main Canvas Area */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="border-b px-4 py-2 flex items-center justify-between bg-background">
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={undo}
              disabled={!canUndo}
              title="Undo"
            >
              <Undo2 className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={redo}
              disabled={!canRedo}
              title="Redo"
            >
              <Redo2 className="h-4 w-4" />
            </Button>
            
            <div className="w-px h-6 bg-border mx-2" />
            
            <Button
              variant={showGrid ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setShowGrid(!showGrid)}
              title="Toggle grid"
            >
              <Grid3x3 className="h-4 w-4" />
            </Button>
            
            <div className="w-px h-6 bg-border mx-2" />
            
            <div className="flex items-center space-x-1">
              <Button
                variant={breakpoint === "lg" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setBreakpoint("lg")}
                title="Desktop view"
              >
                <Monitor className="h-4 w-4" />
              </Button>
              <Button
                variant={breakpoint === "md" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setBreakpoint("md")}
                title="Tablet view"
              >
                <Tablet className="h-4 w-4" />
              </Button>
              <Button
                variant={breakpoint === "sm" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setBreakpoint("sm")}
                title="Mobile view"
              >
                <Smartphone className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <Button
            variant={mode === "preview" ? "default" : "outline"}
            size="sm"
            onClick={() => setMode(mode === "design" ? "preview" : "design")}
          >
            {mode === "design" ? (
              <>
                <Eye className="h-4 w-4 mr-2" />
                Preview
              </>
            ) : (
              <>
                <EyeOff className="h-4 w-4 mr-2" />
                Edit
              </>
            )}
          </Button>
        </div>

        {/* Canvas */}
        <div className="flex-1 overflow-auto bg-muted/30">
          <DesignCanvas
            layout={layout}
            onLayoutChange={(newLayout) => updateLayout(newLayout, false)}
            onWidgetSelect={handleWidgetSelect}
            onWidgetDelete={handleWidgetDelete}
            onWidgetDrop={handleWidgetDrop}
            selectedWidget={selectedWidget}
            showGrid={showGrid}
            mode={mode}
            breakpoint={breakpoint}
          />
        </div>
      </div>

      {/* Right Sidebar - Property Panel */}
      {mode === "design" && selectedWidget && (
        <div className="w-80 border-l bg-background overflow-y-auto">
          <PropertyPanel
            widget={getSelectedWidget()}
            onUpdate={(updates) => handleWidgetUpdate(selectedWidget, updates)}
            onClose={() => setSelectedWidget(null)}
          />
        </div>
      )}
    </div>
  )
}

// Helper functions - now use widget data from backend
function getDefaultWidth(widgetData: any): number {
  if (widgetData?.size_constraints?.defaultWidth) {
    return widgetData.size_constraints.defaultWidth
  }
  // Fallback widths based on widget codes
  const widths: Record<string, number> = {
    "total_screened": 3,
    "screen_failures": 3,
    "total_aes": 3,
    "saes": 3,
    "enrollment_trend": 6,
    "ae_timeline": 8,
    "site_summary_table": 8,
    "subject_listing": 12,
    "site_enrollment_map": 8,
    "subject_flow_diagram": 12
  }
  return widths[widgetData?.code] || 4
}

function getDefaultHeight(widgetData: any): number {
  if (widgetData?.size_constraints?.defaultHeight) {
    return widgetData.size_constraints.defaultHeight
  }
  // Fallback heights based on widget codes
  const heights: Record<string, number> = {
    "total_screened": 2,
    "screen_failures": 2,
    "total_aes": 2,
    "saes": 2,
    "enrollment_trend": 4,
    "ae_timeline": 4,
    "site_summary_table": 4,
    "subject_listing": 6,
    "site_enrollment_map": 6,
    "subject_flow_diagram": 6
  }
  return heights[widgetData?.code] || 4
}

function getDefaultConfig(widgetData: any): any {
  if (widgetData?.config_schema?.properties) {
    // Build default config from schema
    const defaultConfig: any = {}
    Object.entries(widgetData.config_schema.properties).forEach(([key, prop]: [string, any]) => {
      if (prop.default !== undefined) {
        defaultConfig[key] = prop.default
      }
    })
    return defaultConfig
  }
  // Fallback configs
  return {
    title: widgetData?.name || "New Widget"
  }
}