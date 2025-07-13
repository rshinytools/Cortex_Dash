// ABOUTME: Edit dashboard template page
// ABOUTME: Allows editing existing dashboard templates with unified designer

"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { UnifiedDashboardDesigner } from "@/components/admin/unified-dashboard-designer";
import { useToast } from "@/components/ui/use-toast";
import { dashboardTemplatesApi, CreateUnifiedDashboardTemplateDto } from "@/lib/api/dashboard-templates";
import type { WidgetDefinition } from "@/types/widget";
import { widgetsApi } from "@/lib/api/widgets";

export default function EditDashboardTemplatePage() {
  const router = useRouter();
  const params = useParams();
  const { toast } = useToast();
  const templateId = params.id as string;
  
  const [widgetDefinitions, setWidgetDefinitions] = useState<WidgetDefinition[]>([]);
  const [template, setTemplate] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch both template and widget definitions
    const loadData = async () => {
      try {
        const [templateData, widgets] = await Promise.all([
          dashboardTemplatesApi.get(templateId),
          widgetsApi.getLibrary({ is_active: true })
        ]);
        
        // Transform backend format to frontend format
        const transformedTemplate: any = {
          id: templateData.id,
          name: templateData.name,
          description: templateData.description,
          tags: templateData.tags || [],
          category: templateData.category,
          version: templateData.version || "1.0.0",
          menuTemplate: {
            items: templateData.template_structure?.menu?.items || []
          },
          dashboardTemplates: []
        };
        
        // Extract dashboards from menu items recursively
        const extractDashboards = (items: any[]): any[] => {
          const dashboards: any[] = [];
          items.forEach(item => {
            if (item.dashboard) {
              dashboards.push({
                ...item.dashboard,
                menuItemId: item.id
              });
            }
            // Recursively extract from children
            if (item.children && item.children.length > 0) {
              dashboards.push(...extractDashboards(item.children));
            }
          });
          return dashboards;
        };
        
        const dashboards = extractDashboards(transformedTemplate.menuTemplate.items);
        transformedTemplate.dashboardTemplates = dashboards;
        
        setTemplate(transformedTemplate);
        setWidgetDefinitions(widgets);
      } catch (error) {
        console.error('Failed to load data:', error);
        toast({
          title: "Error",
          description: "Failed to load dashboard template",
          variant: "destructive",
        });
        router.push("/admin/dashboard-templates");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [templateId, toast, router]);

  const handleSave = async (updatedTemplate: CreateUnifiedDashboardTemplateDto) => {
    try {
      await dashboardTemplatesApi.update(templateId, updatedTemplate);
      toast({
        title: "Success",
        description: "Dashboard template saved successfully",
      });
      // Stay on the same page - don't redirect
      // router.push("/admin/dashboard-templates");
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update dashboard template",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p>Loading dashboard template...</p>
      </div>
    );
  }

  if (!template) {
    return (
      <div className="flex h-full items-center justify-center">
        <p>Template not found</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col">
      {/* Header with breadcrumb */}
      <div className="border-b px-8 py-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
          <Button
            variant="link"
            className="p-0 h-auto font-normal"
            onClick={() => router.push('/admin')}
          >
            Admin
          </Button>
          <span>/</span>
          <Button
            variant="link"
            className="p-0 h-auto font-normal"
            onClick={() => router.push('/admin/dashboard-templates')}
          >
            Dashboard Templates
          </Button>
          <span>/</span>
          <span className="text-foreground">Edit</span>
        </div>
        
        <div className="flex items-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/admin/dashboard-templates')}
            className="mr-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div className="flex-1">
            <h1 className="text-2xl font-bold">Edit Dashboard Template</h1>
            <p className="text-muted-foreground">
              Modify the dashboard template and menu structure
            </p>
          </div>
        </div>
      </div>

      {/* Designer - fills remaining space */}
      <div className="flex-1 overflow-hidden">
        <UnifiedDashboardDesigner
          templateId={templateId}
          initialTemplate={template}
          widgetDefinitions={widgetDefinitions}
          onSave={handleSave}
        />
      </div>
    </div>
  );
}