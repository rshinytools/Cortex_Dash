// ABOUTME: Dashboard templates list page for viewing and managing templates
// ABOUTME: Shows unified templates with menu structure and widget count

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Plus, Search, Download, Upload, Eye, Edit, Trash2, Copy, ArrowLeft, Layout, Users, Activity, Settings } from "lucide-react";
import { motion } from "framer-motion";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { UserMenu } from "@/components/user-menu";
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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto py-8 px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="mb-8"
        >
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

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-400 bg-clip-text text-transparent flex items-center gap-3">
                <Layout className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
                Dashboard Templates
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Manage unified dashboard templates with integrated menu structures
              </p>
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <UserMenu />
            </div>
          </div>
        </motion.div>

        {/* Stats Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="grid gap-6 md:grid-cols-4 mb-8"
        >
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Templates</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">{templates.length}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Available</p>
                </div>
                <div className="h-12 w-12 bg-indigo-100 dark:bg-indigo-900/20 rounded-lg flex items-center justify-center">
                  <Layout className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Active Templates</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {templates.filter(t => t.isActive).length}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">In use</p>
                </div>
                <div className="h-12 w-12 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
                  <Activity className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Categories</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">7</p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Template types</p>
                </div>
                <div className="h-12 w-12 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
                  <Settings className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Widgets</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                    {templates.reduce((sum, t) => sum + (t.widgetCount || 0), 0)}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Configured</p>
                </div>
                <div className="h-12 w-12 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                  <Users className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          className="flex justify-end gap-3 mb-6"
        >
          <Button variant="outline" asChild className="border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700">
            <label>
              <Upload className="mr-2 h-4 w-4" />
              Import Template
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
            <Button className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-lg">
              <Plus className="mr-2 h-4 w-4" />
              Create Template
            </Button>
          </Link>
        </motion.div>

        {/* Filters and Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800">
            <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-t-lg">
              <div className="flex gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500 dark:text-gray-400" />
                  <Input
                    placeholder="Search templates..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                  />
                </div>
                <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                  <SelectTrigger className="w-48 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600">
                    <SelectValue placeholder="All Categories" />
                  </SelectTrigger>
                  <SelectContent className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
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
            <CardContent className="p-6">
              {/* Templates Grid */}
              {loading ? (
                <div className="flex h-64 items-center justify-center">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 dark:border-indigo-400 mx-auto mb-4" />
                    <p className="text-gray-600 dark:text-gray-400">Loading templates...</p>
                  </div>
                </div>
              ) : filteredTemplates.length === 0 ? (
                <div className="flex h-64 items-center justify-center">
                  <div className="text-center">
                    <Layout className="h-12 w-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
                    <p className="text-gray-600 dark:text-gray-400">
                      {search || categoryFilter !== "all"
                        ? "No templates found matching your filters"
                        : "No dashboard templates created yet"}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {filteredTemplates.map((template, index) => {
                    // Use counts from backend
                    const menuItemsCount = template.menuItemsCount || 0;
                    const totalWidgets = template.widgetCount || 0;

                    return (
                      <motion.div
                        key={template.id}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.3, delay: index * 0.1 }}
                      >
                        <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 hover:shadow-xl transition-all hover:scale-105">
                          <CardHeader>
                            <div className="flex items-start justify-between">
                              <div className="space-y-1">
                                <CardTitle className="line-clamp-1 text-gray-900 dark:text-gray-100">{template.name}</CardTitle>
                                <CardDescription className="line-clamp-2 text-gray-600 dark:text-gray-400">
                                  {template.description}
                                </CardDescription>
                              </div>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="icon" className="hover:bg-gray-100 dark:hover:bg-gray-700">
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
                                <DropdownMenuContent align="end" className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
                                  <DropdownMenuItem onClick={() => setPreviewTemplateId(template.id)} className="hover:bg-gray-100 dark:hover:bg-gray-700">
                                    <Eye className="mr-2 h-4 w-4" />
                                    Preview
                                  </DropdownMenuItem>
                                  <Link href={`/admin/dashboard-templates/${template.id}/edit`}>
                                    <DropdownMenuItem className="hover:bg-gray-100 dark:hover:bg-gray-700">
                                      <Edit className="mr-2 h-4 w-4" />
                                      Edit
                                    </DropdownMenuItem>
                                  </Link>
                                  <DropdownMenuItem
                                    onClick={() => handleDuplicate(template.id, template.name)}
                                    className="hover:bg-gray-100 dark:hover:bg-gray-700"
                                  >
                                    <Copy className="mr-2 h-4 w-4" />
                                    Duplicate
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => handleExport(template.id)} className="hover:bg-gray-100 dark:hover:bg-gray-700">
                                    <Download className="mr-2 h-4 w-4" />
                                    Export
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator className="bg-gray-200 dark:bg-gray-700" />
                                  <DropdownMenuItem
                                    className="text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
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
                              <div className="p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                                <p className="text-2xl font-semibold text-indigo-900 dark:text-indigo-100">{menuItemsCount}</p>
                                <p className="text-xs text-gray-600 dark:text-gray-400">Menu Items</p>
                              </div>
                              <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                                <p className="text-2xl font-semibold text-purple-900 dark:text-purple-100">{totalWidgets}</p>
                                <p className="text-xs text-gray-600 dark:text-gray-400">Widgets</p>
                              </div>
                            </div>

                            {/* Data Requirements Summary */}
                            <div className="rounded-lg bg-gray-100 dark:bg-gray-700/50 p-3">
                              <p className="mb-1 text-sm font-medium text-gray-900 dark:text-gray-100">Data Requirements</p>
                              <p className="text-xs text-gray-600 dark:text-gray-400">
                                {template.dataRequirements.length} fields from{" "}
                                {new Set(template.dataRequirements.map((r) => r.dataSource)).size} sources
                              </p>
                            </div>

                            {/* Tags */}
                            {template.tags && template.tags.length > 0 && (
                              <div className="flex flex-wrap gap-1">
                                {template.tags.map((tag) => (
                                  <Badge key={tag} variant="secondary" className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                                    {tag}
                                  </Badge>
                                ))}
                              </div>
                            )}
                          </CardContent>
                          <CardFooter className="flex items-center justify-between border-t border-gray-200 dark:border-gray-700">
                            <Badge 
                              variant={template.isActive ? "default" : "secondary"}
                              className={template.isActive 
                                ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400" 
                                : "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400"
                              }
                            >
                              {template.isActive ? "Active" : "Inactive"}
                            </Badge>
                            {template.isDefault && <Badge variant="outline" className="border-gray-300 dark:border-gray-600">Default</Badge>}
                            <span className="text-xs text-gray-500 dark:text-gray-400">v{template.version}</span>
                          </CardFooter>
                        </Card>
                      </motion.div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Delete Confirmation Dialog */}
        <AlertDialog
          open={!!deleteTemplateId}
          onOpenChange={(open) => {
            if (!open) setDeleteTemplateId(null);
          }}
        >
          <AlertDialogContent className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
            <AlertDialogHeader>
              <AlertDialogTitle className="text-gray-900 dark:text-gray-100">Delete Dashboard Template</AlertDialogTitle>
              <AlertDialogDescription className="text-gray-600 dark:text-gray-400">
                Are you sure you want to delete this dashboard template? This action cannot be
                undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel className="border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700">Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={() => {
                  if (deleteTemplateId) {
                    handleDelete(deleteTemplateId);
                    setDeleteTemplateId(null);
                  }
                }}
                className="bg-red-600 hover:bg-red-700 text-white"
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