// ABOUTME: Widget configuration dialog for editing widget settings
// ABOUTME: Provides form for customizing widget data sources and display options

"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { DashboardWidget } from "@/lib/api/dashboard-templates";
import { WidgetType } from "@/types/widget";

interface WidgetConfigDialogProps {
  widget: DashboardWidget;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (updates: Partial<DashboardWidget>) => void;
}

export function WidgetConfigDialog({
  widget,
  open,
  onOpenChange,
  onSave,
}: WidgetConfigDialogProps) {
  const [overrideTitle, setOverrideTitle] = useState(widget.overrides?.title || "");
  const [config, setConfig] = useState(widget.widgetInstance?.config || {});

  const widgetDef = widget.widgetInstance?.widgetDefinition;
  if (!widgetDef) return null;

  const handleSave = () => {
    onSave({
      overrides: {
        ...widget.overrides,
        title: overrideTitle || undefined,
      },
      widgetInstance: {
        ...widget.widgetInstance!,
        config,
      },
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Configure {widgetDef.name}</DialogTitle>
          <DialogDescription>
            Customize the widget settings and data source
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="general" className="mt-4">
          <TabsList>
            <TabsTrigger value="general">General</TabsTrigger>
            <TabsTrigger value="data">Data Source</TabsTrigger>
            {widgetDef.type === WidgetType.CHART && (
              <TabsTrigger value="chart">Chart Options</TabsTrigger>
            )}
            {widgetDef.type === WidgetType.TABLE && (
              <TabsTrigger value="table">Table Options</TabsTrigger>
            )}
            {widgetDef.type === WidgetType.METRIC && (
              <TabsTrigger value="metric">Metric Options</TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="general" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">Title Override</Label>
              <Input
                id="title"
                value={overrideTitle}
                onChange={(e) => setOverrideTitle(e.target.value)}
                placeholder={widgetDef.name}
              />
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="show-title"
                checked={config.display?.showTitle !== false}
                onCheckedChange={(checked) =>
                  setConfig({
                    ...config,
                    display: { ...config.display, showTitle: checked },
                  })
                }
              />
              <Label htmlFor="show-title">Show Title</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="show-border"
                checked={config.display?.showBorder !== false}
                onCheckedChange={(checked) =>
                  setConfig({
                    ...config,
                    display: { ...config.display, showBorder: checked },
                  })
                }
              />
              <Label htmlFor="show-border">Show Border</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="show-refresh"
                checked={config.display?.showRefreshTime !== false}
                onCheckedChange={(checked) =>
                  setConfig({
                    ...config,
                    display: { ...config.display, showRefreshTime: checked },
                  })
                }
              />
              <Label htmlFor="show-refresh">Show Refresh Time</Label>
            </div>
          </TabsContent>

          <TabsContent value="data" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="data-source-type">Data Source Type</Label>
              <Select
                value={config.dataSource?.type || "dataset"}
                onValueChange={(value) =>
                  setConfig({
                    ...config,
                    dataSource: { ...config.dataSource, type: value as any },
                  })
                }
              >
                <SelectTrigger id="data-source-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="dataset">Dataset</SelectItem>
                  <SelectItem value="api">API</SelectItem>
                  <SelectItem value="static">Static Data</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {config.dataSource?.type === "dataset" && (
              <div className="space-y-2">
                <Label htmlFor="dataset-id">Dataset ID</Label>
                <Input
                  id="dataset-id"
                  value={config.dataSource?.datasetId || ""}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      dataSource: {
                        ...config.dataSource,
                        datasetId: e.target.value,
                      },
                    })
                  }
                  placeholder="Select dataset..."
                />
              </div>
            )}

            {config.dataSource?.type === "api" && (
              <div className="space-y-2">
                <Label htmlFor="api-endpoint">API Endpoint</Label>
                <Input
                  id="api-endpoint"
                  value={config.dataSource?.endpoint || ""}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      dataSource: {
                        ...config.dataSource,
                        endpoint: e.target.value,
                      },
                    })
                  }
                  placeholder="https://api.example.com/data"
                />
              </div>
            )}

            {config.dataSource?.type === "static" && (
              <div className="space-y-2">
                <Label htmlFor="static-data">Static Data (JSON)</Label>
                <Textarea
                  id="static-data"
                  value={
                    config.dataSource?.staticData
                      ? JSON.stringify(config.dataSource.staticData, null, 2)
                      : ""
                  }
                  onChange={(e) => {
                    try {
                      const data = JSON.parse(e.target.value);
                      setConfig({
                        ...config,
                        dataSource: {
                          ...config.dataSource,
                          staticData: data,
                        },
                      });
                    } catch (error) {
                      // Invalid JSON, ignore
                    }
                  }}
                  placeholder='{"value": 123}'
                  rows={5}
                />
              </div>
            )}
          </TabsContent>

          {widgetDef.type === WidgetType.CHART && (
            <TabsContent value="chart" className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="chart-type">Chart Type</Label>
                <Select
                  value={config.chartConfig?.type || "line"}
                  onValueChange={(value) =>
                    setConfig({
                      ...config,
                      chartConfig: { ...config.chartConfig, type: value as any },
                    })
                  }
                >
                  <SelectTrigger id="chart-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="line">Line Chart</SelectItem>
                    <SelectItem value="bar">Bar Chart</SelectItem>
                    <SelectItem value="pie">Pie Chart</SelectItem>
                    <SelectItem value="scatter">Scatter Plot</SelectItem>
                    <SelectItem value="area">Area Chart</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </TabsContent>
          )}

          {widgetDef.type === WidgetType.TABLE && (
            <TabsContent value="table" className="space-y-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="pagination"
                  checked={config.tableConfig?.pagination !== false}
                  onCheckedChange={(checked) =>
                    setConfig({
                      ...config,
                      tableConfig: { ...config.tableConfig, pagination: checked },
                    })
                  }
                />
                <Label htmlFor="pagination">Enable Pagination</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="sortable"
                  checked={config.tableConfig?.sortable !== false}
                  onCheckedChange={(checked) =>
                    setConfig({
                      ...config,
                      tableConfig: { ...config.tableConfig, sortable: checked },
                    })
                  }
                />
                <Label htmlFor="sortable">Enable Sorting</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="filterable"
                  checked={config.tableConfig?.filterable !== false}
                  onCheckedChange={(checked) =>
                    setConfig({
                      ...config,
                      tableConfig: { ...config.tableConfig, filterable: checked },
                    })
                  }
                />
                <Label htmlFor="filterable">Enable Filtering</Label>
              </div>
            </TabsContent>
          )}

          {widgetDef.type === WidgetType.METRIC && (
            <TabsContent value="metric" className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="value-field">Value Field</Label>
                <Input
                  id="value-field"
                  value={config.metricConfig?.valueField || ""}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      metricConfig: {
                        ...config.metricConfig,
                        valueField: e.target.value,
                      },
                    })
                  }
                  placeholder="Field name containing the metric value"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="format-type">Format Type</Label>
                <Select
                  value={config.metricConfig?.format?.type || "number"}
                  onValueChange={(value) =>
                    setConfig({
                      ...config,
                      metricConfig: {
                        ...config.metricConfig,
                        format: {
                          ...config.metricConfig?.format,
                          type: value as any,
                        },
                      },
                    })
                  }
                >
                  <SelectTrigger id="format-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="number">Number</SelectItem>
                    <SelectItem value="percentage">Percentage</SelectItem>
                    <SelectItem value="currency">Currency</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="comparison"
                  checked={config.metricConfig?.comparison?.enabled || false}
                  onCheckedChange={(checked) =>
                    setConfig({
                      ...config,
                      metricConfig: {
                        ...config.metricConfig,
                        comparison: {
                          ...config.metricConfig?.comparison,
                          enabled: checked,
                          type: config.metricConfig?.comparison?.type || "previous",
                        },
                      },
                    })
                  }
                />
                <Label htmlFor="comparison">Show Comparison</Label>
              </div>
            </TabsContent>
          )}
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave}>Save Changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}