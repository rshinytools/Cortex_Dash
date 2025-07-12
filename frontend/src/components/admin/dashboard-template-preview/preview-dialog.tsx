// ABOUTME: Dashboard template preview dialog component
// ABOUTME: Shows a preview of the dashboard template with menu and widgets

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
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { MenuItem } from "@/types/menu";
import type { DashboardTemplateWithMenu } from "@/lib/api/dashboard-templates";
import { Layout, Home, BarChart3, Users, FileText, Settings, Shield, Activity, Calendar, Package, Database, Globe, Heart, TrendingUp, AlertCircle, CheckCircle, Info, HelpCircle, FolderOpen, ExternalLink, ChevronRight, ChevronDown } from "lucide-react";

interface PreviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  name: string;
  description?: string;
  category: string;
  menuItems: MenuItem[];
  dashboards: Record<string, DashboardTemplateWithMenu>;
}

// Icon mapping
const iconMap: Record<string, any> = {
  Home, Layout, BarChart3, Users, FileText, Settings, Shield, Activity, Calendar, Package, Database, Globe, Heart, TrendingUp, AlertCircle, CheckCircle, Info, HelpCircle, FolderOpen, ExternalLink
};

function MenuItemPreview({ item, level = 0, selectedId, onSelect, expandedItems, onToggleExpand }: {
  item: MenuItem;
  level?: number;
  selectedId: string | null;
  onSelect: (id: string) => void;
  expandedItems: Set<string>;
  onToggleExpand: (id: string) => void;
}) {
  const Icon = item.icon ? (iconMap[item.icon] || Layout) : null;
  const isSelected = item.id === selectedId;
  const hasChildren = item.children && item.children.length > 0;
  const isExpanded = expandedItems.has(item.id);

  return (
    <>
      <div
        className={cn(
          "flex items-center gap-2 px-3 py-2 cursor-pointer rounded-md transition-colors",
          isSelected && "bg-primary/10 text-primary",
          !isSelected && "hover:bg-muted"
        )}
        style={{ paddingLeft: `${level * 16 + 12}px` }}
        onClick={() => {
          if (item.type === "dashboard_page") {
            onSelect(item.id);
          } else if (hasChildren) {
            onToggleExpand(item.id);
          }
        }}
      >
        {hasChildren && (
          <button
            className="p-0.5 hover:bg-muted rounded"
            onClick={(e) => {
              e.stopPropagation();
              onToggleExpand(item.id);
            }}
          >
            {isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </button>
        )}
        {Icon && <Icon className="h-4 w-4" />}
        <span className="text-sm">{item.label}</span>
        {item.type === "external" && (
          <ExternalLink className="h-3 w-3 ml-auto" />
        )}
      </div>
      {hasChildren && isExpanded && item.children?.map((child) => (
        <MenuItemPreview
          key={child.id}
          item={child}
          level={level + 1}
          selectedId={selectedId}
          onSelect={onSelect}
          expandedItems={expandedItems}
          onToggleExpand={onToggleExpand}
        />
      ))}
    </>
  );
}

export function PreviewDialog({
  open,
  onOpenChange,
  name,
  description,
  category,
  menuItems,
  dashboards,
}: PreviewDialogProps) {
  const [selectedMenuId, setSelectedMenuId] = useState<string | null>(
    menuItems.find(item => item.type === "dashboard_page")?.id || null
  );
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  const handleToggleExpand = (id: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedItems(newExpanded);
  };

  const selectedDashboard = selectedMenuId ? dashboards[selectedMenuId] : null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl h-[80vh] p-0">
        <div className="flex flex-col h-full">
          <DialogHeader className="px-6 py-4 border-b">
            <DialogTitle>Preview: {name}</DialogTitle>
            <DialogDescription>
              {description || "Preview how this dashboard template will look"}
            </DialogDescription>
          </DialogHeader>

          <div className="flex gap-0 flex-1 overflow-hidden">
            {/* Sidebar */}
            <div className="w-64 border-r bg-muted/10">
              <div className="p-4 border-b">
                <h3 className="font-semibold text-sm">Navigation</h3>
              </div>
              <ScrollArea className="h-[calc(100%-60px)]">
                <div className="p-2">
                  {menuItems.map((item) => (
                    <MenuItemPreview
                      key={item.id}
                      item={item}
                      selectedId={selectedMenuId}
                      onSelect={setSelectedMenuId}
                      expandedItems={expandedItems}
                      onToggleExpand={handleToggleExpand}
                    />
                  ))}
                </div>
              </ScrollArea>
            </div>

            {/* Main content */}
            <div className="flex-1 overflow-hidden">
              {selectedDashboard ? (
                <div className="h-full flex flex-col">
                  <div className="p-4 border-b">
                    <h2 className="text-xl font-semibold">{selectedDashboard.name}</h2>
                    <div className="flex gap-2 mt-2">
                      <Badge variant="outline">{selectedDashboard.widgets.length} widgets</Badge>
                      <Badge variant="outline">{selectedDashboard.layout.type} layout</Badge>
                    </div>
                  </div>
                  <div className="flex-1 p-4 overflow-auto bg-muted/20">
                    <div className="grid grid-cols-12 gap-4">
                      {selectedDashboard.widgets.map((widget) => (
                        <div
                          key={widget.widgetInstanceId}
                          className="bg-background border rounded-lg p-4"
                          style={{
                            gridColumn: `span ${widget.position.width}`,
                            gridRow: `span ${widget.position.height}`,
                          }}
                        >
                          <div className="text-sm font-medium mb-2">
                            {widget.widgetInstance?.widgetDefinition?.name || "Widget"}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {widget.widgetInstance?.widgetDefinition?.description || "Widget preview"}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-muted-foreground">
                  Select a menu item to preview its dashboard
                </div>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}