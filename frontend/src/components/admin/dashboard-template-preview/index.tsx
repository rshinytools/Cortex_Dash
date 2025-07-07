// ABOUTME: Dashboard template preview dialog component
// ABOUTME: Shows full preview of unified dashboard template with menu and dashboards

"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MenuPreview } from "@/components/admin/menu-preview";
import { cn } from "@/lib/utils";
import type { UnifiedDashboardTemplate } from "@/lib/api/dashboard-templates";

interface DashboardTemplatePreviewProps {
  template: UnifiedDashboardTemplate;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DashboardTemplatePreview({
  template,
  open,
  onOpenChange,
}: DashboardTemplatePreviewProps) {
  const [selectedMenuItemId, setSelectedMenuItemId] = useState<string | null>(
    template.menuTemplate.items[0]?.id || null
  );

  const selectedDashboard = template.dashboardTemplates.find(
    (dt) => dt.menuItemId === selectedMenuItemId
  );

  const totalWidgets = template.dashboardTemplates.reduce(
    (sum, dt) => sum + dt.widgets.length,
    0
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>{template.name}</DialogTitle>
          <DialogDescription>{template.description}</DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="structure" className="mt-4">
          <TabsList>
            <TabsTrigger value="structure">Structure</TabsTrigger>
            <TabsTrigger value="data">Data Requirements</TabsTrigger>
            <TabsTrigger value="details">Details</TabsTrigger>
          </TabsList>

          <TabsContent value="structure" className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              {/* Menu Structure */}
              <div className="space-y-2">
                <h3 className="font-semibold">Menu Structure</h3>
                <div className="rounded-lg border p-4">
                  <MenuPreview items={template.menuTemplate.items} />
                </div>
              </div>

              {/* Dashboard List */}
              <div className="space-y-2">
                <h3 className="font-semibold">Dashboards</h3>
                <ScrollArea className="h-96 rounded-lg border">
                  <div className="p-4 space-y-2">
                    {template.dashboardTemplates.map((dashboard) => (
                      <div
                        key={dashboard.id}
                        className={cn(
                          "rounded-lg border p-3 cursor-pointer transition-colors hover:bg-muted/50",
                          selectedMenuItemId === dashboard.menuItemId && "bg-muted"
                        )}
                        onClick={() => setSelectedMenuItemId(dashboard.menuItemId)}
                      >
                        <p className="font-medium">{dashboard.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {dashboard.widgets.length} widgets
                        </p>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </div>

              {/* Dashboard Preview */}
              <div className="space-y-2">
                <h3 className="font-semibold">Dashboard Preview</h3>
                {selectedDashboard ? (
                  <div className="rounded-lg border p-4">
                    <h4 className="mb-2 font-medium">{selectedDashboard.name}</h4>
                    <div className="grid grid-cols-2 gap-2">
                      {selectedDashboard.widgets.length === 0 ? (
                        <p className="col-span-2 text-sm text-muted-foreground">
                          No widgets configured
                        </p>
                      ) : (
                        selectedDashboard.widgets.map((widget) => (
                          <div
                            key={widget.widgetInstanceId}
                            className="rounded border bg-muted/20 p-2"
                          >
                            <p className="text-xs font-medium">
                              {widget.overrides?.title ||
                                widget.widgetInstance?.widgetDefinition?.name ||
                                "Widget"}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {widget.position.width}x{widget.position.height}
                            </p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="rounded-lg border p-4">
                    <p className="text-sm text-muted-foreground">
                      Select a dashboard to preview
                    </p>
                  </div>
                )}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="data" className="space-y-4">
            <div className="rounded-lg border p-4">
              <h3 className="mb-4 font-semibold">Required Data Fields</h3>
              {template.dataRequirements.length === 0 ? (
                <p className="text-muted-foreground">No data requirements defined</p>
              ) : (
                <div className="space-y-2">
                  {template.dataRequirements.map((req) => (
                    <div key={req.id} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{req.fieldName}</p>
                        <p className="text-sm text-muted-foreground">
                          {req.dataSource} • {req.fieldType}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {req.required && (
                          <Badge variant="destructive" className="text-xs">
                            Required
                          </Badge>
                        )}
                        <Badge variant="outline" className="text-xs">
                          {req.widgetIds.length} widgets
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="details" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <h3 className="font-semibold">Template Information</h3>
                <dl className="space-y-1">
                  <div>
                    <dt className="text-sm text-muted-foreground">Category</dt>
                    <dd className="text-sm font-medium capitalize">{template.category}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-muted-foreground">Version</dt>
                    <dd className="text-sm font-medium">{template.version}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-muted-foreground">Status</dt>
                    <dd>
                      <Badge variant={template.isActive ? "default" : "secondary"}>
                        {template.isActive ? "Active" : "Inactive"}
                      </Badge>
                    </dd>
                  </div>
                  {template.isDefault && (
                    <div>
                      <dt className="text-sm text-muted-foreground">Default</dt>
                      <dd>
                        <Badge variant="outline">Default Template</Badge>
                      </dd>
                    </div>
                  )}
                </dl>
              </div>

              <div className="space-y-2">
                <h3 className="font-semibold">Statistics</h3>
                <dl className="space-y-1">
                  <div>
                    <dt className="text-sm text-muted-foreground">Total Dashboards</dt>
                    <dd className="text-sm font-medium">
                      {template.dashboardTemplates.length}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-muted-foreground">Total Widgets</dt>
                    <dd className="text-sm font-medium">{totalWidgets}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-muted-foreground">Data Sources</dt>
                    <dd className="text-sm font-medium">
                      {new Set(template.dataRequirements.map((r) => r.dataSource)).size}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-muted-foreground">Created</dt>
                    <dd className="text-sm font-medium">
                      {new Date(template.createdAt).toLocaleDateString()}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>

            {template.tags && template.tags.length > 0 && (
              <div className="space-y-2">
                <h3 className="font-semibold">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {template.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}