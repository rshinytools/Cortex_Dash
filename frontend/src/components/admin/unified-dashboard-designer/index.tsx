// ABOUTME: Main unified dashboard designer component
// ABOUTME: Combines menu designer (left panel) with dashboard designer (right panel)

"use client";

import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import { DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import { v4 as uuidv4 } from "uuid";
import { Plus, Save, Eye, Download, Upload, Settings, HelpCircle } from "lucide-react";
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
import { PreviewDialog } from "../dashboard-template-preview/preview-dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

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
  const [showPreview, setShowPreview] = useState(false);
  const [typeChangeWarning, setTypeChangeWarning] = useState<{
    itemId: string;
    newType: MenuItemType;
    oldType: MenuItemType;
  } | null>(null);

  // Menu state
  const [menuItems, setMenuItems] = useState<MenuItem[]>(
    initialTemplate?.menuTemplate?.items || []
  );
  const [selectedMenuItemId, setSelectedMenuItemId] = useState<string | null>(null);
  
  // TODO: Add autosave tracking
  // Track changes for autosave
  const trackChange = useCallback(() => {
    // setHasUnsavedChanges(true);
    // lastChangeRef.current = new Date();
  }, []);

  // Dashboard states (keyed by menu item ID)
  const [dashboards, setDashboards] = useState<Record<string, DashboardTemplateWithMenu>>(() => {
    // Initialize from template
    const initialDashboards: Record<string, DashboardTemplateWithMenu> = initialTemplate?.dashboardTemplates?.reduce(
      (acc, dashboard) => ({
        ...acc,
        [dashboard.menuItemId]: dashboard,
      }),
      {} as Record<string, DashboardTemplateWithMenu>
    ) || {};
    
    // Create dashboards for any dashboard pages that don't have one
    const ensureAllDashboards = (items: MenuItem[]): void => {
      for (const item of items) {
        if (item.type === MenuItemType.DASHBOARD_PAGE && !initialDashboards[item.id]) {
          initialDashboards[item.id] = {
            id: uuidv4(),
            menuItemId: item.id,
            name: item.label,
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
        }
        if (item.children) {
          ensureAllDashboards(item.children);
        }
      }
    };
    
    if (initialTemplate?.menuTemplate?.items) {
      ensureAllDashboards(initialTemplate.menuTemplate.items);
    }
    
    return initialDashboards;
  });

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
        // Handle both old and new widget definition formats
        const dataReqs = widgetDef?.data_requirements || widgetDef?.dataRequirements;
        const requiredFields = dataReqs?.requiredFields || dataReqs?.required_fields;
        if (requiredFields) {
          requiredFields.forEach((field: string) => {
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

  // Helper function to check if a menu item can have a dashboard
  const canHaveDashboard = (item: MenuItem): boolean => {
    // Dashboard pages can have dashboards regardless of their parent
    return item.type === MenuItemType.DASHBOARD_PAGE;
  };

  // Handle type change for menu items
  const handleTypeChange = useCallback((itemId: string, currentItem: MenuItem, newType: MenuItemType) => {
    const updateItems = (items: MenuItem[]): MenuItem[] =>
      items.map((item) => {
        if (item.id === itemId) {
          return { ...item, type: newType };
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
    trackChange();

    const oldCanHaveDashboard = canHaveDashboard(currentItem);
    const newCanHaveDashboard = newType === MenuItemType.DASHBOARD_PAGE;

    if (oldCanHaveDashboard && !newCanHaveDashboard) {
      // Remove dashboard if changing from dashboard page to other type
      setDashboards((prev) => {
        const { [itemId]: deleted, ...rest } = prev;
        return rest;
      });
      // Clear selection if this was selected
      if (selectedMenuItemId === itemId) {
        setSelectedMenuItemId(null);
      }
    } else if (!oldCanHaveDashboard && newCanHaveDashboard) {
      // Create dashboard if changing to dashboard page type
      const newDashboard: DashboardTemplateWithMenu = {
        id: uuidv4(),
        menuItemId: itemId,
        name: currentItem.label,
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
        [itemId]: newDashboard,
      }));
    }
  }, [menuItems, selectedMenuItemId, trackChange]);

  // Add menu item
  const handleAddMenuItem = useCallback((parentId?: string) => {
    const newItem: MenuItem = {
      id: uuidv4(),
      label: "New Item",
      type: MenuItemType.DASHBOARD_PAGE, // Default to dashboard page
      order: menuItems.length,
      isVisible: true,
      isEnabled: true,
      dashboardConfig: {
        viewId: uuidv4(),
        layout: {
          type: "grid",
          columns: 12,
          rows: 10,
        },
      },
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
    
    trackChange();

    // Only create corresponding dashboard if it's a dashboard page
    if (canHaveDashboard(newItem)) {
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
    }

    // Select the new item
    setSelectedMenuItemId(newItem.id);
  }, [menuItems, trackChange]);

  // Update menu item
  const handleUpdateMenuItem = useCallback((itemId: string, updates: Partial<MenuItem>) => {
    // Find the current item to check type changes
    const findItem = (items: MenuItem[]): MenuItem | null => {
      for (const item of items) {
        if (item.id === itemId) return item;
        if (item.children) {
          const found = findItem(item.children);
          if (found) return found;
        }
      }
      return null;
    };

    const currentItem = findItem(menuItems);
    if (!currentItem) return;

    // Check if type is changing
    if (updates.type && updates.type !== currentItem.type) {
      const oldType = currentItem.type;
      const newType = updates.type;
      
      // Check if changing from dashboard page to something else (would lose widgets)
      if (oldType === MenuItemType.DASHBOARD_PAGE && newType !== MenuItemType.DASHBOARD_PAGE && dashboards[itemId]?.widgets.length > 0) {
        setTypeChangeWarning({ itemId, newType, oldType });
        return;
      }
      
      // Otherwise proceed with the type change
      handleTypeChange(itemId, currentItem, newType);
      return;
    }

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
    trackChange();

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
  }, [menuItems, dashboards, selectedMenuItemId, handleTypeChange, trackChange]);

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
    trackChange();

    // Delete corresponding dashboard
    setDashboards((prev) => {
      const { [itemId]: deleted, ...rest } = prev;
      return rest;
    });

    // Clear selection if deleted item was selected
    if (selectedMenuItemId === itemId) {
      setSelectedMenuItemId(null);
    }
  }, [menuItems, selectedMenuItemId, trackChange]);

  // Add widget to current dashboard
  const handleAddWidget = useCallback((widgetDefId: string) => {
    if (!selectedMenuItemId || !selectedDashboard) return;

    const widgetDef = widgetDefinitions.find((def) => def.id === widgetDefId);
    if (!widgetDef) return;

    // Handle both old and new widget definition formats
    const sizeConstraints = widgetDef.size_constraints || widgetDef.size;
    const defaultWidth = sizeConstraints?.defaultWidth || 4;
    const defaultHeight = sizeConstraints?.defaultHeight || 3;
    const defaultConfig = widgetDef.default_config || widgetDef.defaultConfig || {};

    const newWidget: DashboardWidget = {
      widgetInstanceId: uuidv4(),
      position: {
        x: 0,
        y: 0,
        width: defaultWidth,
        height: defaultHeight,
      },
      order: selectedDashboard.widgets.length,
      isVisible: true,
      widgetInstance: {
        id: uuidv4(),
        widgetDefinitionId: widgetDef.id,
        widgetDefinition: widgetDef,
        studyId: "", // Will be set when applied to study
        config: defaultConfig,
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
      // TODO: Add theme support
      // theme,
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
      console.log("Saving template:", template);
      console.log("Menu items:", JSON.stringify(menuItems, null, 2));
      console.log("Dashboards:", JSON.stringify(dashboards, null, 2));
      console.log("Dashboard count:", Object.keys(dashboards).length);
      
      // Log all dashboard page menu items
      const getAllDashboardPages = (items: MenuItem[]): MenuItem[] => {
        const result: MenuItem[] = [];
        for (const item of items) {
          if (item.type === MenuItemType.DASHBOARD_PAGE) {
            result.push(item);
          }
          if (item.children) {
            result.push(...getAllDashboardPages(item.children));
          }
        }
        return result;
      };
      
      const dashboardPages = getAllDashboardPages(menuItems);
      console.log("Dashboard pages found:", dashboardPages.map(p => ({ id: p.id, label: p.label })));
      console.log("Dashboards for pages:", dashboardPages.map(p => ({ 
        id: p.id, 
        label: p.label, 
        hasDashboard: !!dashboards[p.id],
        widgetCount: dashboards[p.id]?.widgets?.length || 0
      })));
      
      // Log the actual template being sent
      console.log("Template being sent to API:", JSON.stringify(template, null, 2));
      
      await onSave(template);
      
      // TODO: Add save state tracking
      // setIsSaving(false);
      // setHasUnsavedChanges(false);
      // setLastSaved(new Date());
      
      // if (!isAutosave) {
      //   setNotificationProps({
      //     type: "success",
      //     message: "Template saved successfully",
      //     detail: `Your dashboard template "${name}" has been saved.`,
      //   });
      //   setShowNotification(true);
      // }
      
      toast({
        title: "Success",
        description: "Dashboard template saved successfully",
      });
    } catch (error) {
      console.error("Failed to save template:", error);
      // setIsSaving(false);
      
      // const errorMessage = error instanceof Error ? error.message : "Failed to save dashboard template";
      // setNotificationProps({
      //   type: "error",
      //   message: isAutosave ? "Autosave failed" : "Save failed",
      //   detail: errorMessage,
      // });
      // setShowNotification(true);
      
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to save dashboard template",
        variant: "destructive",
      });
    }
  };

  const handleExport = () => {
    const template = {
      name,
      description,
      tags,
      category,
      // TODO: Add theme support
      // theme,
      menuTemplate: {
        name: `${name} Menu`,
        position: MenuPosition.SIDEBAR,
        items: menuItems,
        version: "1.0.0",
        isActive: true,
      },
      dashboardTemplates: Object.values(dashboards),
      exportedAt: new Date().toISOString(),
      version: "1.0.0"
    };

    const blob = new Blob([JSON.stringify(template, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${name.toLowerCase().replace(/\s+/g, "-")}-template.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: "Success",
      description: "Dashboard template exported successfully",
    });
  };

  const handleImport = async (file: File) => {
    try {
      const text = await file.text();
      const imported = JSON.parse(text);

      // Validate the imported structure
      if (!imported.name || !imported.menuTemplate || !imported.dashboardTemplates) {
        throw new Error("Invalid template format");
      }

      // Set the imported values
      setName(imported.name);
      setDescription(imported.description || "");
      setTags(imported.tags || []);
      setCategory(imported.category || "custom");
      // TODO: Add theme support
      // setTheme(imported.theme || defaultThemes[0]);
      setMenuItems(imported.menuTemplate.items || []);
      
      // Convert dashboards array to object keyed by menuItemId
      const dashboardsObj: Record<string, DashboardTemplateWithMenu> = {};
      imported.dashboardTemplates.forEach((dashboard: DashboardTemplateWithMenu) => {
        dashboardsObj[dashboard.menuItemId] = dashboard;
      });
      setDashboards(dashboardsObj);
      
      trackChange();

      toast({
        title: "Success",
        description: "Dashboard template imported successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to import dashboard template. Please check the file format.",
        variant: "destructive",
      });
    }
  };
  
  // TODO: Add autosave functionality
  // Autosave effect
  // useEffect(() => {
  //   if (autosaveEnabled && hasUnsavedChanges) {
  //     const timer = setTimeout(() => {
  //       handleSave(true);
  //     }, 30000); // 30 seconds
      
  //     return () => clearTimeout(timer);
  //   }
  // }, [hasUnsavedChanges, autosaveEnabled, name, menuItems, dashboards, tags, description, category, theme]);
  
  // Cleanup autosave timer on unmount
  // useEffect(() => {
  //   return () => {
  //     if (autosaveTimerRef.current) {
  //       clearTimeout(autosaveTimerRef.current);
  //     }
  //   };
  // }, []);

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex-shrink-0 border-b p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <TemplateMetadataForm
              name={name}
              description={description}
              tags={tags}
              category={category}
              onNameChange={(value) => {
                setName(value);
                trackChange();
              }}
              onDescriptionChange={(value) => {
                setDescription(value);
                trackChange();
              }}
              onTagsChange={(value) => {
                setTags(value);
                trackChange();
              }}
              onCategoryChange={(value) => {
                setCategory(value);
                trackChange();
              }}
            />
            {/* TODO: Add AutosaveIndicator component */}
            {/* <AutosaveIndicator
                lastSaved={lastSaved}
                isUnsaved={hasUnsavedChanges}
                isSaving={isSaving}
              /> */}
            </div>
            <div className="flex items-center gap-2">
              {/* TODO: Add ThemeEditor component */}
              {/* <ThemeEditor
                theme={theme}
                onChange={(newTheme) => {
                  setTheme(newTheme);
                  trackChange();
                }}
              /> */}
              {/* TODO: Add Settings popover */}
              {/* <Popover open={showSettings} onOpenChange={setShowSettings}>
                <PopoverTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Settings className="h-4 w-4" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-64" align="end">
                  <div className="space-y-4">
                    <h3 className="font-semibold">Settings</h3>
                    <div className="flex items-center justify-between">
                      <Label htmlFor="autosave" className="text-sm">
                        Autosave
                        <HelpIcon
                          content="Automatically save changes every 30 seconds"
                          side="right"
                        />
                      </Label>
                      <Switch
                        id="autosave"
                        checked={autosaveEnabled}
                        onCheckedChange={setAutosaveEnabled}
                      />
                    </div>
                  </div>
                </PopoverContent>
              </Popover> */}
              <Button variant="outline" size="sm" onClick={() => setShowPreview(true)}>
                <Eye className="mr-2 h-4 w-4" />
                Preview
              </Button>
              <Button variant="outline" size="sm" onClick={handleExport}>
                <Download className="mr-2 h-4 w-4" />
                Export
              </Button>
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
                      if (file) handleImport(file);
                    }}
                  />
                </label>
              </Button>
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
          <div className="w-80 flex-shrink-0 border-r bg-muted/20">
            <div className="flex h-full flex-col">
              <div className="border-b p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">Menu Structure</h3>
                    {/* TODO: Add HelpIcon component */}
                    {/* <HelpIcon
                      content="Design the navigation menu for your dashboard. Add pages, groups, and links."
                    /> */}
                  </div>
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
                  onSelectItem={(itemId) => {
                    // Only allow selecting items that can have dashboards
                    const findItem = (items: MenuItem[]): MenuItem | null => {
                      for (const item of items) {
                        if (item.id === itemId) return item;
                        if (item.children) {
                          const found = findItem(item.children);
                          if (found) return found;
                        }
                      }
                      return null;
                    };
                    
                    const item = findItem(menuItems);
                    console.log("Selected item:", item);
                    console.log("Can have dashboard:", item ? canHaveDashboard(item) : false);
                    console.log("Dashboard exists:", dashboards[itemId]);
                    
                    if (item) {
                      // Always allow selection - we'll show appropriate UI based on type
                      setSelectedMenuItemId(itemId);
                      
                      // Create dashboard if it's a dashboard page and doesn't exist
                      if (canHaveDashboard(item) && !dashboards[itemId]) {
                        const newDashboard: DashboardTemplateWithMenu = {
                          id: uuidv4(),
                          menuItemId: itemId,
                          name: item.label,
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
                          [itemId]: newDashboard,
                        }));
                      }
                    }
                  }}
                  onUpdateItem={handleUpdateMenuItem}
                  onDeleteItem={handleDeleteMenuItem}
                  onAddItem={handleAddMenuItem}
                  onReorderItems={setMenuItems}
                />
              </div>
            </div>
          </div>

          {/* Right panel - Dashboard Designer */}
          <div className="flex flex-1 flex-col">
            {selectedMenuItemId ? (
              selectedDashboard ? (
                // Show dashboard designer for dashboard pages
                <Tabs defaultValue="design" className="flex h-full flex-col">
                  <TabsList className="mx-4 mt-4 w-fit">
                    <TabsTrigger value="design">Design</TabsTrigger>
                    <TabsTrigger value="data">Data Requirements</TabsTrigger>
                  </TabsList>

                  <TabsContent value="design" className="flex-1 overflow-hidden p-0">
                    <div className="flex h-full">
                      {/* Dashboard canvas */}
                      <div className="flex-1 flex flex-col overflow-hidden p-4">
                        <DashboardDesigner
                          dashboard={selectedDashboard}
                          widgets={selectedDashboard.widgets}
                          onUpdateWidget={handleUpdateWidget}
                          onDeleteWidget={handleDeleteWidget}
                        />
                      </div>

                      {/* Widget palette */}
                      <div className="w-64 flex-shrink-0 border-l bg-muted/20">
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
                // Show info for non-dashboard pages (groups, external links, etc.)
                <div className="flex flex-1 items-center justify-center text-muted-foreground">
                  <div className="text-center max-w-md">
                    <p className="mb-2 text-lg font-medium">Menu Item Settings</p>
                    <p className="text-sm mb-4">
                      This menu item is set to "{findMenuItem(menuItems, selectedMenuItemId)?.type?.replace('_', ' ')}" type.
                    </p>
                    <p className="text-sm">
                      To add widgets, change the type to "Dashboard Page" in the menu settings on the left.
                    </p>
                  </div>
                </div>
              )
            ) : (
              <div className="flex flex-1 items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <p className="mb-2">No menu item selected</p>
                  <p className="text-sm">Select a menu item from the menu structure</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Preview Dialog */}
      <PreviewDialog
        open={showPreview}
        onOpenChange={setShowPreview}
        name={name}
        description={description}
        category={category}
        menuItems={menuItems}
        dashboards={dashboards}
      />
      
      {/* TODO: Add Notification component */}
      {/* <Notification
        show={showNotification}
        type={notificationProps.type}
        message={notificationProps.message}
        detail={notificationProps.detail}
        onClose={() => setShowNotification(false)}
      /> */}
      
      {/* TODO: Add HelpPanel component */}
      {/* <HelpPanel sections={helpSections} /> */}
      
      {/* Type change warning dialog */}
      <AlertDialog
        open={!!typeChangeWarning}
        onOpenChange={(open) => {
          if (!open) setTypeChangeWarning(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Warning: Dashboard Content Will Be Deleted</AlertDialogTitle>
            <AlertDialogDescription>
              Changing this menu item from "Dashboard Page" to another type will permanently delete all widgets 
              on this dashboard. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setTypeChangeWarning(null)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => {
                if (typeChangeWarning) {
                  const { itemId, newType } = typeChangeWarning;
                  const item = findMenuItem(menuItems, itemId);
                  if (item) {
                    handleTypeChange(itemId, item, newType);
                  }
                  setTypeChangeWarning(null);
                }
              }}
            >
              Delete Dashboard & Continue
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </DndProvider>
  );
  
  function findMenuItem(items: MenuItem[], id: string): MenuItem | null {
    for (const item of items) {
      if (item.id === id) return item;
      if (item.children) {
        const found = findMenuItem(item.children, id);
        if (found) return found;
      }
    }
    return null;
  }
}