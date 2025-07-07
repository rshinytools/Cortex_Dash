// ABOUTME: Widget palette sidebar for dashboard designer
// ABOUTME: Displays available widgets categorized by type with drag functionality

"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { 
  Search,
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

interface Widget {
  id: string
  name: string
  icon: React.ComponentType<{ className?: string }>
  category: string
  description: string
}

const widgets: Widget[] = [
  // Metrics
  {
    id: "metric-card",
    name: "Metric Card",
    icon: Hash,
    category: "metrics",
    description: "Display a single metric with trend"
  },
  {
    id: "progress",
    name: "Progress Bar",
    icon: Loader2,
    category: "metrics",
    description: "Show progress towards a goal"
  },
  
  // Charts
  {
    id: "line-chart",
    name: "Line Chart",
    icon: LineChart,
    category: "charts",
    description: "Time series and trend visualization"
  },
  {
    id: "bar-chart",
    name: "Bar Chart",
    icon: BarChart3,
    category: "charts",
    description: "Compare values across categories"
  },
  {
    id: "pie-chart",
    name: "Pie Chart",
    icon: PieChart,
    category: "charts",
    description: "Show proportions and percentages"
  },
  {
    id: "scatter-plot",
    name: "Scatter Plot",
    icon: Activity,
    category: "charts",
    description: "Visualize correlations between variables"
  },
  {
    id: "heatmap",
    name: "Heatmap",
    icon: Grid3x3,
    category: "charts",
    description: "Display data density and patterns"
  },
  
  // Data
  {
    id: "table",
    name: "Data Table",
    icon: Table2,
    category: "data",
    description: "Display tabular data with sorting"
  },
  
  // Geographic
  {
    id: "geo-map",
    name: "Geographic Map",
    icon: Map,
    category: "geographic",
    description: "Visualize data on a map"
  },
  
  // Text
  {
    id: "text",
    name: "Text Widget",
    icon: Type,
    category: "text",
    description: "Add custom text and descriptions"
  }
]

const categories = [
  { id: "all", name: "All Widgets", count: widgets.length },
  { id: "metrics", name: "Metrics", count: widgets.filter(w => w.category === "metrics").length },
  { id: "charts", name: "Charts", count: widgets.filter(w => w.category === "charts").length },
  { id: "data", name: "Data", count: widgets.filter(w => w.category === "data").length },
  { id: "geographic", name: "Geographic", count: widgets.filter(w => w.category === "geographic").length },
  { id: "text", name: "Text", count: widgets.filter(w => w.category === "text").length }
]

interface WidgetPaletteProps {
  onDragStart: (widgetType: string) => void
}

export function WidgetPalette({ onDragStart }: WidgetPaletteProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("all")

  const filteredWidgets = widgets.filter(widget => {
    const matchesSearch = widget.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         widget.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === "all" || widget.category === selectedCategory
    
    return matchesSearch && matchesCategory
  })

  const handleDragStart = (e: React.DragEvent, widgetId: string) => {
    e.dataTransfer.setData("widgetType", widgetId)
    e.dataTransfer.effectAllowed = "copy"
    onDragStart(widgetId)
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b">
        <h3 className="font-semibold mb-3">Widget Library</h3>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            placeholder="Search widgets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9"
          />
        </div>
      </div>

      <div className="border-b">
        <div className="p-2">
          {categories.map(category => (
            <button
              key={category.id}
              onClick={() => setSelectedCategory(category.id)}
              className={cn(
                "w-full text-left px-3 py-2 rounded-md text-sm transition-colors",
                "hover:bg-accent hover:text-accent-foreground",
                selectedCategory === category.id && "bg-accent text-accent-foreground"
              )}
            >
              <div className="flex items-center justify-between">
                <span>{category.name}</span>
                <span className="text-xs text-muted-foreground">{category.count}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-2">
          {filteredWidgets.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No widgets found matching your search
            </p>
          ) : (
            filteredWidgets.map(widget => {
              const Icon = widget.icon
              return (
                <div
                  key={widget.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, widget.id)}
                  className={cn(
                    "p-3 rounded-lg border bg-card cursor-move",
                    "hover:bg-accent hover:border-accent-foreground/20",
                    "transition-colors group"
                  )}
                >
                  <div className="flex items-start space-x-3">
                    <div className="p-2 rounded-md bg-background border">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <h4 className="text-sm font-medium group-hover:text-accent-foreground">
                        {widget.name}
                      </h4>
                      <p className="text-xs text-muted-foreground mt-1">
                        {widget.description}
                      </p>
                    </div>
                  </div>
                </div>
              )
            })
          )}
        </div>
      </ScrollArea>

      <div className="p-4 border-t bg-muted/50">
        <p className="text-xs text-muted-foreground text-center">
          Drag widgets to the canvas to add them
        </p>
      </div>
    </div>
  )
}