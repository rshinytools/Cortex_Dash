// ABOUTME: Property panel for configuring selected widget properties
// ABOUTME: Provides dynamic forms based on widget type for configuration

"use client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { X, Trash2 } from "lucide-react"

interface PropertyPanelProps {
  widget: any | null
  onUpdate: (updates: any) => void
  onClose: () => void
}

export function PropertyPanel({ widget, onUpdate, onClose }: PropertyPanelProps) {
  if (!widget) return null

  const handleConfigUpdate = (key: string, value: any) => {
    onUpdate({
      config: {
        ...widget.config,
        [key]: value
      }
    })
  }

  const handleDelete = () => {
    // This will be handled by parent component
    onClose()
  }

  const renderProperties = () => {
    switch (widget.type) {
      case "metric-card":
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={widget.config.title || ""}
                onChange={(e) => handleConfigUpdate("title", e.target.value)}
                placeholder="Metric title"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="dataSource">Data Source</Label>
              <Select
                value={widget.config.dataSource || ""}
                onValueChange={(value) => handleConfigUpdate("dataSource", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select data source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="enrollmentCount">Enrollment Count</SelectItem>
                  <SelectItem value="adverseEvents">Adverse Events</SelectItem>
                  <SelectItem value="screenFailures">Screen Failures</SelectItem>
                  <SelectItem value="siteActivation">Site Activation</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="unit">Unit</Label>
              <Input
                id="unit"
                value={widget.config.unit || ""}
                onChange={(e) => handleConfigUpdate("unit", e.target.value)}
                placeholder="e.g., patients, %"
              />
            </div>

            <div className="space-y-2">
              <Label>Show Trend</Label>
              <Switch
                checked={widget.config.showTrend || false}
                onCheckedChange={(checked) => handleConfigUpdate("showTrend", checked)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="trendPeriod">Trend Period</Label>
              <Select
                value={widget.config.trendPeriod || "7d"}
                onValueChange={(value) => handleConfigUpdate("trendPeriod", value)}
                disabled={!widget.config.showTrend}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="24h">Last 24 hours</SelectItem>
                  <SelectItem value="7d">Last 7 days</SelectItem>
                  <SelectItem value="30d">Last 30 days</SelectItem>
                  <SelectItem value="90d">Last 90 days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </>
        )

      case "line-chart":
      case "bar-chart":
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="title">Chart Title</Label>
              <Input
                id="title"
                value={widget.config.title || ""}
                onChange={(e) => handleConfigUpdate("title", e.target.value)}
                placeholder="Chart title"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="xAxis">X-Axis Label</Label>
              <Input
                id="xAxis"
                value={widget.config.xAxis || ""}
                onChange={(e) => handleConfigUpdate("xAxis", e.target.value)}
                placeholder="X-axis label"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="yAxis">Y-Axis Label</Label>
              <Input
                id="yAxis"
                value={widget.config.yAxis || ""}
                onChange={(e) => handleConfigUpdate("yAxis", e.target.value)}
                placeholder="Y-axis label"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="dataSource">Data Source</Label>
              <Select
                value={widget.config.dataSource || ""}
                onValueChange={(value) => handleConfigUpdate("dataSource", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select data source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="enrollmentTrend">Enrollment Trend</SelectItem>
                  <SelectItem value="aeByWeek">AEs by Week</SelectItem>
                  <SelectItem value="visitCompliance">Visit Compliance</SelectItem>
                  <SelectItem value="queryResolution">Query Resolution</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Show Legend</Label>
              <Switch
                checked={widget.config.showLegend !== false}
                onCheckedChange={(checked) => handleConfigUpdate("showLegend", checked)}
              />
            </div>

            <div className="space-y-2">
              <Label>Show Grid</Label>
              <Switch
                checked={widget.config.showGrid !== false}
                onCheckedChange={(checked) => handleConfigUpdate("showGrid", checked)}
              />
            </div>
          </>
        )

      case "pie-chart":
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="title">Chart Title</Label>
              <Input
                id="title"
                value={widget.config.title || ""}
                onChange={(e) => handleConfigUpdate("title", e.target.value)}
                placeholder="Chart title"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="dataSource">Data Source</Label>
              <Select
                value={widget.config.dataSource || ""}
                onValueChange={(value) => handleConfigUpdate("dataSource", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select data source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="enrollmentBySite">Enrollment by Site</SelectItem>
                  <SelectItem value="aeByType">AEs by Type</SelectItem>
                  <SelectItem value="patientStatus">Patient Status</SelectItem>
                  <SelectItem value="protocolDeviations">Protocol Deviations</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Show Labels</Label>
              <Switch
                checked={widget.config.showLabels !== false}
                onCheckedChange={(checked) => handleConfigUpdate("showLabels", checked)}
              />
            </div>

            <div className="space-y-2">
              <Label>Show Legend</Label>
              <Switch
                checked={widget.config.showLegend !== false}
                onCheckedChange={(checked) => handleConfigUpdate("showLegend", checked)}
              />
            </div>
          </>
        )

      case "table":
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="title">Table Title</Label>
              <Input
                id="title"
                value={widget.config.title || ""}
                onChange={(e) => handleConfigUpdate("title", e.target.value)}
                placeholder="Table title"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="dataSource">Data Source</Label>
              <Select
                value={widget.config.dataSource || ""}
                onValueChange={(value) => handleConfigUpdate("dataSource", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select data source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="patientList">Patient List</SelectItem>
                  <SelectItem value="sitePerformance">Site Performance</SelectItem>
                  <SelectItem value="recentAEs">Recent Adverse Events</SelectItem>
                  <SelectItem value="upcomingVisits">Upcoming Visits</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="pageSize">Rows per Page</Label>
              <Select
                value={String(widget.config.pageSize || 10)}
                onValueChange={(value) => handleConfigUpdate("pageSize", parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5">5</SelectItem>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="25">25</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Enable Sorting</Label>
              <Switch
                checked={widget.config.enableSorting !== false}
                onCheckedChange={(checked) => handleConfigUpdate("enableSorting", checked)}
              />
            </div>

            <div className="space-y-2">
              <Label>Enable Filtering</Label>
              <Switch
                checked={widget.config.enableFiltering || false}
                onCheckedChange={(checked) => handleConfigUpdate("enableFiltering", checked)}
              />
            </div>
          </>
        )

      case "text":
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={widget.config.title || ""}
                onChange={(e) => handleConfigUpdate("title", e.target.value)}
                placeholder="Widget title"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="content">Content</Label>
              <Textarea
                id="content"
                value={widget.config.content || ""}
                onChange={(e) => handleConfigUpdate("content", e.target.value)}
                placeholder="Enter text content..."
                rows={6}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="fontSize">Font Size</Label>
              <Select
                value={widget.config.fontSize || "medium"}
                onValueChange={(value) => handleConfigUpdate("fontSize", value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="small">Small</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="large">Large</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </>
        )

      default:
        return (
          <p className="text-sm text-muted-foreground">
            No properties available for this widget type
          </p>
        )
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b flex items-center justify-between">
        <h3 className="font-semibold">Widget Properties</h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-6">
          {/* Widget Type Info */}
          <div>
            <Label className="text-xs uppercase text-muted-foreground">Widget Type</Label>
            <p className="text-sm font-medium capitalize mt-1">
              {widget.type.replace(/-/g, " ")}
            </p>
          </div>

          <Separator />

          {/* Widget-specific properties */}
          <div className="space-y-4">
            {renderProperties()}
          </div>

          <Separator />

          {/* Position and Size */}
          <div className="space-y-4">
            <h4 className="text-sm font-medium">Position & Size</h4>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="width">Width</Label>
                <Input
                  id="width"
                  type="number"
                  value={widget.w}
                  onChange={(e) => onUpdate({ w: parseInt(e.target.value) || 1 })}
                  min={1}
                  max={12}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="height">Height</Label>
                <Input
                  id="height"
                  type="number"
                  value={widget.h}
                  onChange={(e) => onUpdate({ h: parseInt(e.target.value) || 1 })}
                  min={1}
                  max={20}
                />
              </div>
            </div>

            <p className="text-xs text-muted-foreground">
              Grid units (12 columns wide)
            </p>
          </div>

          <Separator />

          {/* Danger Zone */}
          <div className="space-y-4">
            <h4 className="text-sm font-medium text-destructive">Danger Zone</h4>
            <Button
              variant="destructive"
              className="w-full"
              onClick={handleDelete}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Widget
            </Button>
          </div>
        </div>
      </ScrollArea>
    </div>
  )
}