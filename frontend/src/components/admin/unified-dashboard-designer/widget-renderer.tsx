// ABOUTME: Widget renderer component for displaying widget previews
// ABOUTME: Renders widget content based on widget type and configuration

"use client";

import { BarChart3, TrendingUp, Table, FileText, Image, Globe } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DashboardWidget } from "@/lib/api/dashboard-templates";
import { WidgetType } from "@/types/widget";

interface WidgetRendererProps {
  widget: DashboardWidget;
}

export function WidgetRenderer({ widget }: WidgetRendererProps) {
  const widgetDef = widget.widgetInstance?.widgetDefinition;
  const config = widget.widgetInstance?.config;
  const overrides = widget.overrides;

  if (!widgetDef) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <p className="text-sm">Widget not found</p>
      </div>
    );
  }

  const title = overrides?.title || config?.display?.title || widgetDef.name;

  // Render based on widget type
  switch (widgetDef.type) {
    case WidgetType.METRIC:
      return (
        <Card className="h-full">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <TrendingUp className="h-4 w-4" />
              {title}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {config?.metricConfig?.format?.prefix}
              123,456
              {config?.metricConfig?.format?.suffix}
            </div>
            {config?.metricConfig?.comparison?.enabled && (
              <p className="text-sm text-muted-foreground">
                +12.5% from previous period
              </p>
            )}
          </CardContent>
        </Card>
      );

    case WidgetType.CHART:
      return (
        <Card className="h-full">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3 className="h-4 w-4" />
              {title}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex h-32 items-center justify-center rounded bg-muted/50">
              <p className="text-sm text-muted-foreground">
                {config?.chartConfig?.type || "Chart"} Preview
              </p>
            </div>
          </CardContent>
        </Card>
      );

    case WidgetType.TABLE:
      return (
        <Card className="h-full">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Table className="h-4 w-4" />
              {title}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="h-8 rounded bg-muted/50" />
              <div className="h-8 rounded bg-muted/30" />
              <div className="h-8 rounded bg-muted/30" />
            </div>
          </CardContent>
        </Card>
      );

    case WidgetType.TEXT:
      return (
        <Card className="h-full">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <FileText className="h-4 w-4" />
              {title}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Text content will be displayed here
            </p>
          </CardContent>
        </Card>
      );

    case WidgetType.IMAGE:
      return (
        <Card className="h-full">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Image className="h-4 w-4" />
              {title}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex h-32 items-center justify-center rounded bg-muted/50">
              <Image className="h-12 w-12 text-muted-foreground/50" />
            </div>
          </CardContent>
        </Card>
      );

    case WidgetType.IFRAME:
      return (
        <Card className="h-full">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Globe className="h-4 w-4" />
              {title}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex h-32 items-center justify-center rounded bg-muted/50">
              <p className="text-sm text-muted-foreground">External content</p>
            </div>
          </CardContent>
        </Card>
      );

    default:
      return (
        <Card className="h-full">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">{title}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Widget type: {widgetDef.type}
            </p>
          </CardContent>
        </Card>
      );
  }
}