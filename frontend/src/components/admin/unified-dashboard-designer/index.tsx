// ABOUTME: Main unified dashboard designer component
// ABOUTME: Combines menu designer (left panel) with dashboard designer (right panel)

"use client";

import { useState, useCallback, useMemo } from "react";
import { DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import { v4 as uuidv4 } from "uuid";
import { Plus, Save, Eye, Download, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/use-toast";
import { MenuDesigner } from "./menu-designer";
import { DashboardDesigner } from "./dashboard-designer";
import { DataRequirementsPanel } from "../data-requirements-panel";
import { WidgetPalette } from "./widget-palette";
import { TemplateMetadataForm } from "./template-metadata-form";
import type {
  UnifiedDashboardTemplate,
  DashboardTemplateWithMenu,
  CreateUnifiedDashboardTemplateDto,
} from "@/lib/api/dashboard-templates";
import type { MenuItem, MenuTemplate } from "@/types/menu";
import { MenuItemType, MenuPosition } from "@/types/menu";
import type { DashboardTemplate, DashboardWidget } from "@/types/dashboard";
import { DashboardCategory, LayoutType } from "@/types/dashboard";
import type { WidgetDefinition } from "@/types/widget";

export interface UnifiedDashboardDesignerProps {
  initialTemplate?: UnifiedDashboardTemplate;
  widgetDefinitions: WidgetDefinition[];
  onSave: (template: CreateUnifiedDashboardTemplateDto) => Promise<void>;
  onPreview?: () => void;
  onExport?: () => void;
  onImport?: (file: File) => void;
}

export function UnifiedDashboardDesigner({
  initialTemplate,
  widgetDefinitions,
  onSave,
  onPreview,
  onExport,
  onImport,
}: UnifiedDashboardDesignerProps) {
  const { toast } = useToast();
  
  // Template metadata
  const [name, setName] = useState(initialTemplate?.name || "");
  const [description, setDescription] = useState(initialTemplate?.description || "");
  const [tags, setTags] = useState<string[]>(initialTemplate?.tags || []);
  const [category, setCategory] = useState(initialTemplate?.category || "custom");

  // Menu state
  const [menuItems, setMenuItems] = useState<MenuItem[]>(
    initialTemplate?.menuTemplate?.items || []
  );
  const [selectedMenuItemId, setSelectedMenuItemId] = useState<string | null>(null);

  // Dashboard states (keyed by menu item ID)
  const [dashboards, setDashboards] = useState<Record<string, DashboardTemplateWithMenu>>(
    initialTemplate?.dashboardTemplates?.reduce(
      (acc, dashboard) => ({
        ...acc,
        [dashboard.menuItemId]: dashboard,
      }),
      {}
    ) || {}
  );

  // Currently selected dashboard
  const selectedDashboard = selectedMenuItemId ? dashboards[selectedMenuItemId] : null;

  // Calculate data requirements from all dashboards
  const dataRequirements = useMemo(() => {
    const requirements = new Map<string, Set<string>>();

    Object.values(dashboards).forEach((dashboard) => {
      dashboard.widgets.forEach((widget) => {
        // Extract data requirements from widget configuration
        const widgetDef = widgetDefinitions.find(
          (def) => def.id === widget.widgetInstance?.widgetDefinitionId
        );
        if (widgetDef?.dataRequirements?.requiredFields) {
          widgetDef.dataRequirements.requiredFields.forEach((field) => {
            if (!requirements.has(field)) {
              requirements.set(field, new Set());
            }
            requirements.get(field)?.add(widget.widgetInstanceId);
          });
        }
      });
    });

    return Array.from(requirements.entries()).map(([field, widgetIds]) => ({
      id: uuidv4(),
      fieldName: field,
      fieldType: "string", // Would need to be determined from schema
      dataSource: "unknown", // Would need to be mapped
      required: true,
      widgetIds: Array.from(widgetIds),
    }));
  }, [dashboards, widgetDefinitions]);

  // Add menu item
  const handleAddMenuItem = useCallback((parentId?: string) => {
    const newItem: MenuItem = {
      id: uuidv4(),
      label: "New Item",
      type: MenuItemType.LINK,
      url: "#",
      order: menuItems.length,
      isVisible: true,
      isEnabled: true,
    };

    if (parentId) {
      // Add as child
      const updateItems = (items: MenuItem[]): MenuItem[] =>
        items.map((item) => {
          if (item.id === parentId) {
            return {
              ...item,
              children: [...(item.children || []), newItem],
            };
          }
          if (item.children) {
            return {
              ...item,
              children: updateItems(item.children),
            };
          }
          return item;
        });
      setMenuItems(updateItems(menuItems));
    } else {
      // Add to root
      setMenuItems([...menuItems, newItem]);
    }

    // Create corresponding dashboard
    const newDashboard: DashboardTemplateWithMenu = {
      id: uuidv4(),
      menuItemId: newItem.id,
      name: newItem.label,
      category: DashboardCategory.CUSTOM,
      version: "1.0.0",
      layout: {
        type: LayoutType.GRID,
        columns: 12,
        rowHeight: 80,
        margin: [16, 16],
        containerPadding: [24, 24, 24, 24],
        isResponsive: true,
      },
      widgets: [],
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    setDashboards((prev) => ({
      ...prev,
      [newItem.id]: newDashboard,
    }));

    // Select the new item
    setSelectedMenuItemId(newItem.id);
  }, [menuItems]);

  // Update menu item
  const handleUpdateMenuItem = useCallback((itemId: string, updates: Partial<MenuItem>) => {
    const updateItems = (items: MenuItem[]): MenuItem[] =>
      items.map((item) => {
        if (item.id === itemId) {
          return { ...item, ...updates };
        }
        if (item.children) {
          return {
            ...item,
            children: updateItems(item.children),
          };
        }
        return item;
      });

    setMenuItems(updateItems(menuItems));

    // Update corresponding dashboard name if label changed
    if (updates.label && dashboards[itemId]) {
      setDashboards((prev) => ({
        ...prev,
        [itemId]: {
          ...prev[itemId],
          name: updates.label || prev[itemId].name,
        },
      }));
    }
  }, [menuItems, dashboards]);

  // Delete menu item
  const handleDeleteMenuItem = useCallback((itemId: string) => {
    const deleteItem = (items: MenuItem[]): MenuItem[] =>
      items
        .filter((item) => item.id !== itemId)
        .map((item) => ({
          ...item,
          children: item.children ? deleteItem(item.children) : undefined,
        }));

    setMenuItems(deleteItem(menuItems));

    // Delete corresponding dashboard
    setDashboards((prev) => {
      const { [itemId]: deleted, ...rest } = prev;
      return rest;
    });

    // Clear selection if deleted item was selected
    if (selectedMenuItemId === itemId) {
      setSelectedMenuItemId(null);
    }
  }, [menuItems, selectedMenuItemId]);

  // Add widget to current dashboard
  const handleAddWidget = useCallback((widgetDefId: string) => {
    if (!selectedMenuItemId || !selectedDashboard) return;

    const widgetDef = widgetDefinitions.find((def) => def.id === widgetDefId);
    if (!widgetDef) return;

    const newWidget: DashboardWidget = {
      widgetInstanceId: uuidv4(),
      position: {
        x: 0,
        y: 0,
        width: widgetDef.size.defaultWidth,
        height: widgetDef.size.defaultHeight,
      },
      order: selectedDashboard.widgets.length,
      isVisible: true,
      widgetInstance: {
        id: uuidv4(),
        widgetDefinitionId: widgetDef.id,
        widgetDefinition: widgetDef,
        studyId: "", // Will be set when applied to study
        config: widgetDef.defaultConfig,
        isVisible: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    };

    setDashboards((prev) => ({
      ...prev,
      [selectedMenuItemId]: {
        ...prev[selectedMenuItemId],
        widgets: [...prev[selectedMenuItemId].widgets, newWidget],
      },
    }));
  }, [selectedMenuItemId, selectedDashboard, widgetDefinitions]);

  // Update widget in current dashboard
  const handleUpdateWidget = useCallback(
    (widgetId: string, updates: Partial<DashboardWidget>) => {
      if (!selectedMenuItemId || !selectedDashboard) return;

      setDashboards((prev) => ({
        ...prev,
        [selectedMenuItemId]: {
          ...prev[selectedMenuItemId],
          widgets: prev[selectedMenuItemId].widgets.map((widget) =>
            widget.widgetInstanceId === widgetId ? { ...widget, ...updates } : widget
          ),
        },
      }));
    },
    [selectedMenuItemId, selectedDashboard]
  );

  // Delete widget from current dashboard
  const handleDeleteWidget = useCallback((widgetId: string) => {
    if (!selectedMenuItemId || !selectedDashboard) return;

    setDashboards((prev) => ({
      ...prev,
      [selectedMenuItemId]: {
        ...prev[selectedMenuItemId],
        widgets: prev[selectedMenuItemId].widgets.filter(
          (widget) => widget.widgetInstanceId !== widgetId
        ),
      },
    }));
  }, [selectedMenuItemId, selectedDashboard]);

  // Save template
  const handleSave = async () => {
    if (!name.trim()) {
      toast({
        title: "Error",
        description: "Please provide a template name",
        variant: "destructive",
      });
      return;
    }

    if (menuItems.length === 0) {
      toast({
        title: "Error",
        description: "Please add at least one menu item",
        variant: "destructive",
      });
      return;
    }

    const template: CreateUnifiedDashboardTemplateDto = {
      name,
      description,
      tags,
      category,
      menuTemplate: {
        name: `${name} Menu`,
        position: MenuPosition.SIDEBAR,
        items: menuItems,
        version: "1.0.0",
        isActive: true,
      },
      dashboardTemplates: Object.values(dashboards),
    };

    try {
      await onSave(template);
      toast({
        title: "Success",
        description: "Dashboard template saved successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save dashboard template",
        variant: "destructive",
      });
    }
  };

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="border-b p-4">
          <div className="flex items-center justify-between">
            <TemplateMetadataForm
              name={name}
              description={description}
              tags={tags}
              category={category}
              onNameChange={setName}
              onDescriptionChange={setDescription}
              onTagsChange={setTags}
              onCategoryChange={setCategory}
            />
            <div className="flex items-center gap-2">
              {onPreview && (
                <Button variant="outline" size="sm" onClick={onPreview}>
                  <Eye className="mr-2 h-4 w-4" />
                  Preview
                </Button>
              )}
              {onExport && (
                <Button variant="outline" size="sm" onClick={onExport}>
                  <Download className="mr-2 h-4 w-4" />
                  Export
                </Button>
              )}
              {onImport && (
                <Button variant="outline" size="sm" asChild>
                  <label>
                    <Upload className="mr-2 h-4 w-4" />
                    Import
                    <input
                      type="file"
                      accept=".json"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) onImport(file);
                      }}
                    />
                  </label>
                </Button>
              )}
              <Button onClick={handleSave}>
                <Save className="mr-2 h-4 w-4" />
                Save Template
              </Button>
            </div>
          </div>
        </div>

        {/* Main content */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left panel - Menu Designer */}
          <div className="w-80 border-r bg-muted/20">
            <div className="flex h-full flex-col">
              <div className="border-b p-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">Menu Structure</h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAddMenuItem()}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Add Item
                  </Button>
                </div>
              </div>
              <div className="flex-1 overflow-auto p-4">
                <MenuDesigner
                  items={menuItems}
                  selectedItemId={selectedMenuItemId}
                  onSelectItem={setSelectedMenuItemId}
                  onUpdateItem={handleUpdateMenuItem}
                  onDeleteItem={handleDeleteMenuItem}
                  onAddItem={handleAddMenuItem}
                />
              </div>
            </div>
          </div>

          {/* Right panel - Dashboard Designer */}
          <div className="flex flex-1 flex-col">
            {selectedMenuItemId && selectedDashboard ? (
              <Tabs defaultValue="design" className="flex h-full flex-col">
                <TabsList className="mx-4 mt-4 w-fit">
                  <TabsTrigger value="design">Design</TabsTrigger>
                  <TabsTrigger value="data">Data Requirements</TabsTrigger>
                </TabsList>

                <TabsContent value="design" className="flex-1 overflow-hidden">
                  <div className="flex h-full">
                    {/* Dashboard canvas */}
                    <div className="flex-1 overflow-auto p-4">
                      <DashboardDesigner
                        dashboard={selectedDashboard}
                        widgets={selectedDashboard.widgets}
                        onUpdateWidget={handleUpdateWidget}
                        onDeleteWidget={handleDeleteWidget}
                      />
                    </div>

                    {/* Widget palette */}
                    <div className="w-64 border-l bg-muted/20">
                      <WidgetPalette
                        widgetDefinitions={widgetDefinitions}
                        onAddWidget={handleAddWidget}
                      />
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="data" className="flex-1 overflow-auto p-4">
                  <DataRequirementsPanel requirements={dataRequirements} />
                </TabsContent>
              </Tabs>
            ) : (
              <div className="flex flex-1 items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <p className="mb-2">No menu item selected</p>
                  <p className="text-sm">Select a menu item to design its dashboard</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </DndProvider>
  );
}