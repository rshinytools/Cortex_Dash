// ABOUTME: Widget palette sidebar for dashboard designer
// ABOUTME: Displays available widgets categorized by type with drag functionality

"use client"

import { useState, useEffect } from "react"
import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
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
  Loader2,
  Plus,
  RefreshCw,
  AlertCircle
} from "lucide-react"
import { widgetsApi } from "@/lib/api/widgets"
import { useToast } from "@/hooks/use-toast"

interface Widget {
  id: string
  code: string
  name: string
  description: string
  category: {
    id: number
    name: string
    display_name: string
  }
  size_constraints: {
    minWidth: number
    minHeight: number
    defaultWidth: number
    defaultHeight: number
  }
}

interface WidgetCategory {
  id: number
  name: string
  display_name: string
  widget_count: number
}

// Icon mapping for widget categories
const categoryIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  METRICS: Hash,
  CHARTS: LineChart,
  TABLES: Table2,
  MAPS: Map,
  SPECIALIZED: Activity
}

// Icon mapping for widget codes
const widgetIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  // Flexible metrics card
  metrics_card_flexible: TrendingUp,
  // Metrics
  metric_card: Hash,
  total_screened: Hash,
  screen_failures: TrendingUp,
  total_aes: AlertCircle,
  saes: AlertCircle,
  total_subjects_with_aes: Activity,
  average_age: Type,
  total_sum: BarChart3,
  // Charts
  enrollment_trend: LineChart,
  ae_timeline: Activity,
  // Tables
  site_summary_table: Table2,
  subject_listing: Table2,
  // Maps
  site_enrollment_map: Map,
  // Specialized
  subject_flow_diagram: Activity
}

// Get icon for widget
function getWidgetIcon(widget: Widget): React.ComponentType<{ className?: string }> {
  return widgetIcons[widget.code] || categoryIcons[widget.category.name] || Grid3x3
}


interface WidgetPaletteProps {
  onDragStart: (widgetType: string) => void
}

export function WidgetPalette({ onDragStart }: WidgetPaletteProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("all")
  const [widgets, setWidgets] = useState<Widget[]>([])
  const [categories, setCategories] = useState<WidgetCategory[]>([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  // Load categories and widgets on mount
  useEffect(() => {
    loadCategories()
    loadWidgets()
  }, [])

  // Reload widgets when category changes
  useEffect(() => {
    loadWidgets()
  }, [selectedCategory])

  const loadCategories = async () => {
    try {
      const data = await widgetsApi.getCategories()
      setCategories(data)
    } catch (error) {
      console.error('Failed to load categories:', error)
      toast({
        title: 'Error',
        description: 'Failed to load widget categories',
        variant: 'destructive',
      })
    }
  }

  const loadWidgets = async () => {
    setLoading(true)
    try {
      const params = selectedCategory !== 'all' && selectedCategory !== '0'
        ? { category_id: parseInt(selectedCategory) }
        : undefined
      
      const data = await widgetsApi.getLibrary(params)
      setWidgets(data)
    } catch (error) {
      console.error('Failed to load widgets:', error)
      toast({
        title: 'Error',
        description: 'Failed to load widgets',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const filteredWidgets = widgets.filter(widget => {
    const matchesSearch = widget.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         (widget.description?.toLowerCase() || '').includes(searchQuery.toLowerCase())
    return matchesSearch
  })

  const handleDragStart = (e: React.DragEvent, widget: Widget) => {
    e.dataTransfer.setData("widgetType", widget.code)
    e.dataTransfer.setData("widgetData", JSON.stringify(widget))
    e.dataTransfer.effectAllowed = "copy"
    onDragStart(widget.code)
  }

  // Build categories list with counts
  const allCategories = [
    { id: 0, name: "all", display_name: "All Widgets", widget_count: widgets.length },
    ...categories
  ]

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
          {allCategories.map(category => (
            <button
              key={category.id}
              onClick={() => setSelectedCategory(category.id.toString())}
              className={cn(
                "w-full text-left px-3 py-2 rounded-md text-sm transition-colors",
                "hover:bg-accent hover:text-accent-foreground",
                selectedCategory === category.id.toString() && "bg-accent text-accent-foreground"
              )}
            >
              <div className="flex items-center justify-between">
                <span>{category.display_name}</span>
                <span className="text-xs text-muted-foreground">{category.widget_count}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-2">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : filteredWidgets.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No widgets found matching your search
            </p>
          ) : (
            filteredWidgets.map(widget => {
              const Icon = getWidgetIcon(widget)
              return (
                <div
                  key={widget.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, widget)}
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
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-muted-foreground">
                          {widget.size_constraints.defaultWidth}x{widget.size_constraints.defaultHeight}
                        </span>
                        <span className="text-xs text-muted-foreground">•</span>
                        <span className="text-xs text-muted-foreground">
                          {widget.category.display_name}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })
          )}
        </div>
      </ScrollArea>

      <div className="p-4 border-t bg-muted/50">
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            {widgets.length} widgets available
          </p>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => loadWidgets()}
            disabled={loading}
          >
            <RefreshCw className={cn("h-3 w-3", loading && "animate-spin")} />
          </Button>
        </div>
      </div>
    </div>
  )
}