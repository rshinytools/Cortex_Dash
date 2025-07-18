// ABOUTME: Dashboard templates list page for viewing and managing templates
// ABOUTME: Shows unified templates with menu structure and widget count

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Plus, Search, Download, Upload, Eye, Edit, Trash2, Copy, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import { useToast } from "@/components/ui/use-toast";
import { dashboardTemplatesApi, UnifiedDashboardTemplate } from "@/lib/api/dashboard-templates";
import { DashboardCategory, LayoutType } from "@/types/dashboard";
import { MenuPosition, MenuItemType } from "@/types/menu";
import { PreviewDialog } from "@/components/admin/dashboard-template-preview/preview-dialog";

// Mock data - in production this would come from the API
const mockTemplates: UnifiedDashboardTemplate[] = [
  {
    id: "1",
    name: "Clinical Trial Executive Dashboard",
    description: "Comprehensive executive view with safety, efficacy, and enrollment metrics",
    tags: ["executive", "comprehensive", "clinical"],
    category: DashboardCategory.EXECUTIVE,
    version: "1.0.0",
    menuTemplate: {
      id: "1",
      name: "Executive Menu",
      position: MenuPosition.SIDEBAR,
      items: [
        {
          id: "1-1",
          label: "Overview",
          type: MenuItemType.DASHBOARD_PAGE,
          icon: "Home",
          order: 0,
          isVisible: true,
          isEnabled: true,
          dashboardConfig: {
            viewId: "overview",
            layout: {
              type: "grid",
              columns: 12,
              rows: 10,
            },
          },
        },
        {
          id: "1-2",
          label: "Safety",
          type: MenuItemType.GROUP,
          order: 1,
          isVisible: true,
          isEnabled: true,
          icon: "Shield",
          children: [
            {
              id: "1-2-1",
              label: "Adverse Events",
              type: MenuItemType.DASHBOARD_PAGE,
              order: 0,
              isVisible: true,
              isEnabled: true,
              dashboardConfig: {
                viewId: "safety-ae",
                layout: {
                  type: "grid",
                  columns: 12,
                  rows: 10,
                },
              },
            },
            {
              id: "1-2-2",
              label: "SAE Summary",
              type: MenuItemType.DASHBOARD_PAGE,
              order: 1,
              isVisible: true,
              isEnabled: true,
              dashboardConfig: {
                viewId: "safety-sae",
                layout: {
                  type: "grid",
                  columns: 12,
                  rows: 10,
                },
              },
            },
          ],
        },
        {
          id: "1-3",
          label: "Enrollment",
          type: MenuItemType.DASHBOARD_PAGE,
          icon: "Users",
          order: 2,
          isVisible: true,
          isEnabled: true,
          dashboardConfig: {
            viewId: "enrollment",
            layout: {
              type: "grid",
              columns: 12,
              rows: 10,
            },
          },
        },
      ],
      version: "1.0.0",
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    dashboardTemplates: [
      {
        id: "dt-1",
        menuItemId: "1-1",
        name: "Overview",
        category: DashboardCategory.EXECUTIVE,
        version: "1.0.0",
        layout: {
          type: LayoutType.GRID,
          columns: 12,
          rowHeight: 80,
        },
        widgets: [],
        isActive: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ],
    dataRequirements: [
      {
        id: "dr-1",
        fieldName: "subject_id",
        fieldType: "string",
        dataSource: "demographics",
        required: true,
        widgetIds: ["w1", "w2"],
      },
      {
        id: "dr-2",
        fieldName: "enrollment_date",
        fieldType: "date",
        dataSource: "demographics",
        required: true,
        widgetIds: ["w1"],
      },
    ],
    isActive: true,
    isDefault: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
];

export default function DashboardTemplatesPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [templates, setTemplates] = useState<UnifiedDashboardTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [deleteTemplateId, setDeleteTemplateId] = useState<string | null>(null);
  const [previewTemplateId, setPreviewTemplateId] = useState<string | null>(null);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await dashboardTemplatesApi.list();
      
      // Transform backend format to frontend format
      const transformedTemplates = response.data.map((template: any) => {
        // Extract menu items and dashboards from template structure
        const menuItems = template.template_structure?.menu_structure?.items || [];
        const dashboardTemplates: any[] = template.template_structure?.dashboardTemplates || [];
        
        // No need to extract dashboards - they're already in dashboardTemplates
        
        return {
          id: template.id,
          name: template.name,
          description: template.description,
          tags: template.tags || [],
          category: template.category,
          version: `${template.major_version}.${template.minor_version}.${template.patch_version}`,
          // Add backend-calculated counts
          widgetCount: template.widget_count || 0,
          dashboardCount: template.dashboard_count || 0,
          menuItemsCount: menuItems.length || 0,  // Count menu items from structure
          menuTemplate: {
            id: `mt-${template.id}`,
            name: `${template.name} Menu`,
            position: MenuPosition.SIDEBAR,
            items: menuItems,
            version: "1.0.0",
            isActive: template.is_active,
            createdAt: template.created_at,
            updatedAt: template.updated_at,
          },
          dashboardTemplates,
          dataRequirements: [],
          isActive: template.is_active,
          isDefault: false,
          createdAt: template.created_at,
          updatedAt: template.updated_at,
        };
      });
      
      setTemplates(transformedTemplates);
    } catch (error) {
      console.error('Failed to load templates:', error);
      toast({
        title: "Error",
        description: "Failed to load dashboard templates",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await dashboardTemplatesApi.delete(id);
      toast({
        title: "Success",
        description: "Dashboard template deleted successfully",
      });
      loadTemplates();
    } catch {
      toast({
        title: "Error",
        description: "Failed to delete dashboard template",
        variant: "destructive",
      });
    }
  };

  const handleDuplicate = async (id: string, name: string) => {
    try {
      await dashboardTemplatesApi.duplicate(id, `${name} (Copy)`);
      toast({
        title: "Success",
        description: "Dashboard template duplicated successfully",
      });
      loadTemplates();
    } catch {
      toast({
        title: "Error",
        description: "Failed to duplicate dashboard template",
        variant: "destructive",
      });
    }
  };

  const handleExport = async (id: string) => {
    try {
      const blob = await dashboardTemplatesApi.export(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `dashboard-template-${id}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast({
        title: "Success",
        description: "Dashboard template exported successfully",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to export dashboard template",
        variant: "destructive",
      });
    }
  };

  const filteredTemplates = templates.filter((template) => {
    const matchesSearch =
      template.name.toLowerCase().includes(search.toLowerCase()) ||
      template.description?.toLowerCase().includes(search.toLowerCase()) ||
      template.tags?.some((tag) => tag.toLowerCase().includes(search.toLowerCase()));
    
    const matchesCategory = categoryFilter === "all" || template.category === categoryFilter;
    
    return matchesSearch && matchesCategory;
  });

  const previewTemplate = previewTemplateId
    ? templates.find((t) => t.id === previewTemplateId)
    : null;

  return (
    <div className="container mx-auto py-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
        <Button
          variant="link"
          className="p-0 h-auto font-normal"
          onClick={() => router.push('/admin')}
        >
          Admin
        </Button>
        <span>/</span>
        <span className="text-foreground">Dashboard Templates</span>
      </div>

      {/* Header */}
      <div className="flex items-center mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/admin')}
          className="mr-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Admin
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">Dashboard Templates</h1>
          <p className="text-muted-foreground mt-1">
            Manage unified dashboard templates with integrated menu structures
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" asChild>
            <label>
              <Upload className="mr-2 h-4 w-4" />
              Import
              <input
                type="file"
                accept=".json"
                className="hidden"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    try {
                      await dashboardTemplatesApi.import(file);
                      toast({
                        title: "Success",
                        description: "Dashboard template imported successfully",
                      });
                      loadTemplates();
                    } catch {
                      toast({
                        title: "Error",
                        description: "Failed to import dashboard template",
                        variant: "destructive",
                      });
                    }
                  }
                }}
              />
            </label>
          </Button>
          <Link href="/admin/dashboard-templates/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Template
            </Button>
          </Link>
        </div>
      </div>

      {/* Filters and Grid in Card */}
      <Card>
        <CardHeader>
          <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search templates..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            <SelectItem value={DashboardCategory.EXECUTIVE}>Executive</SelectItem>
            <SelectItem value={DashboardCategory.OPERATIONAL}>Operational</SelectItem>
            <SelectItem value={DashboardCategory.SAFETY}>Safety</SelectItem>
            <SelectItem value={DashboardCategory.EFFICACY}>Efficacy</SelectItem>
            <SelectItem value={DashboardCategory.QUALITY}>Quality</SelectItem>
            <SelectItem value={DashboardCategory.REGULATORY}>Regulatory</SelectItem>
            <SelectItem value={DashboardCategory.CUSTOM}>Custom</SelectItem>
          </SelectContent>
        </Select>
          </div>
        </CardHeader>
        <CardContent>
          {/* Templates Grid */}
          {loading ? (
        <div className="flex h-64 items-center justify-center">
          <p className="text-muted-foreground">Loading templates...</p>
        </div>
      ) : filteredTemplates.length === 0 ? (
        <Card className="flex h-64 items-center justify-center">
          <CardContent>
            <p className="text-muted-foreground">
              {search || categoryFilter !== "all"
                ? "No templates found matching your filters"
                : "No dashboard templates created yet"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredTemplates.map((template) => {
            // Use counts from backend
            const menuItemsCount = template.menuItemsCount || 0;
            const totalWidgets = template.widgetCount || 0;

            return (
              <Card key={template.id} className="flex flex-col">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="line-clamp-1">{template.name}</CardTitle>
                      <CardDescription className="line-clamp-2">
                        {template.description}
                      </CardDescription>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <svg
                            className="h-4 w-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
                            />
                          </svg>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => setPreviewTemplateId(template.id)}>
                          <Eye className="mr-2 h-4 w-4" />
                          Preview
                        </DropdownMenuItem>
                        <Link href={`/admin/dashboard-templates/${template.id}/edit`}>
                          <DropdownMenuItem>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                        </Link>
                        <DropdownMenuItem
                          onClick={() => handleDuplicate(template.id, template.name)}
                        >
                          <Copy className="mr-2 h-4 w-4" />
                          Duplicate
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleExport(template.id)}>
                          <Download className="mr-2 h-4 w-4" />
                          Export
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => setDeleteTemplateId(template.id)}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 space-y-4">
                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-semibold">{menuItemsCount}</p>
                      <p className="text-xs text-muted-foreground">Menu Items</p>
                    </div>
                    <div>
                      <p className="text-2xl font-semibold">{totalWidgets}</p>
                      <p className="text-xs text-muted-foreground">Widgets</p>
                    </div>
                  </div>

                  {/* Data Requirements Summary */}
                  <div className="rounded-lg bg-muted/50 p-3">
                    <p className="mb-1 text-sm font-medium">Data Requirements</p>
                    <p className="text-xs text-muted-foreground">
                      {template.dataRequirements.length} fields from{" "}
                      {new Set(template.dataRequirements.map((r) => r.dataSource)).size} sources
                    </p>
                  </div>

                  {/* Tags */}
                  {template.tags && template.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {template.tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                </CardContent>
                <CardFooter className="flex items-center justify-between">
                  <Badge variant={template.isActive ? "default" : "secondary"}>
                    {template.isActive ? "Active" : "Inactive"}
                  </Badge>
                  {template.isDefault && <Badge variant="outline">Default</Badge>}
                  <span className="text-xs text-muted-foreground">v{template.version}</span>
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        open={!!deleteTemplateId}
        onOpenChange={(open) => {
          if (!open) setDeleteTemplateId(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Dashboard Template</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this dashboard template? This action cannot be
              undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (deleteTemplateId) {
                  handleDelete(deleteTemplateId);
                  setDeleteTemplateId(null);
                }
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Preview Dialog */}
      {previewTemplate && (
        <PreviewDialog
          open={!!previewTemplateId}
          onOpenChange={(open) => {
            if (!open) setPreviewTemplateId(null);
          }}
          name={previewTemplate.name}
          description={previewTemplate.description}
          category={previewTemplate.category}
          menuItems={previewTemplate.menuTemplate.items}
          dashboards={previewTemplate.dashboardTemplates.reduce((acc, dt) => {
            acc[dt.menuItemId] = dt;
            return acc;
          }, {} as Record<string, any>)}
        />
      )}
    </div>
  );
}

// Helper function to count menu items including children
interface MenuItemCount {
  id: string;
  children?: MenuItemCount[];
  dashboard?: {
    widgets?: any[];
  };
}

function countMenuItems(items: MenuItemCount[]): number {
  return items.reduce((count, item) => {
    return count + 1 + (item.children ? countMenuItems(item.children) : 0);
  }, 0);
}

// Helper function to count total widgets across all menu items
function countTotalWidgets(items: MenuItemCount[]): number {
  return items.reduce((count, item) => {
    const widgetCount = item.dashboard?.widgets?.length || 0;
    const childrenWidgetCount = item.children ? countTotalWidgets(item.children) : 0;
    return count + widgetCount + childrenWidgetCount;
  }, 0);
}