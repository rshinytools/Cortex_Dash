// ABOUTME: New unified dashboard template designer page
// ABOUTME: Allows creating complete dashboard templates with integrated menus

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { UnifiedDashboardDesigner } from "@/components/admin/unified-dashboard-designer";
import { useToast } from "@/components/ui/use-toast";
import { dashboardTemplatesApi, CreateUnifiedDashboardTemplateDto } from "@/lib/api/dashboard-templates";
import type { WidgetDefinition } from "@/types/widget";
import { WidgetCategory, WidgetType } from "@/types/widget";
import { widgetsApi } from "@/lib/api/widgets";

export default function NewDashboardTemplatePage() {
  const router = useRouter();
  const { toast } = useToast();
  const [widgetDefinitions, setWidgetDefinitions] = useState<WidgetDefinition[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch widget definitions from API
    const loadWidgets = async () => {
      try {
        const widgets = await widgetsApi.getLibrary({ is_active: true });
        setWidgetDefinitions(widgets);
      } catch (error) {
        console.error('Failed to load widget definitions:', error);
        toast({
          title: "Error",
          description: "Failed to load widget definitions",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    loadWidgets();
  }, [toast]);

  const handleSave = async (template: CreateUnifiedDashboardTemplateDto) => {
    try {
      console.log("Creating template:", template);
      const createdTemplate = await dashboardTemplatesApi.create(template);
      toast({
        title: "Success",
        description: "Dashboard template created successfully",
      });
      // After creating, navigate to the edit page for the new template
      if (createdTemplate?.id) {
        router.push(`/admin/dashboard-templates/${createdTemplate.id}/edit`);
      }
    } catch (error) {
      console.error("Failed to create template:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create dashboard template",
        variant: "destructive",
      });
      throw error; // Re-throw to let the UnifiedDashboardDesigner handle it
    }
  };


  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p>Loading widget definitions...</p>
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
          <span className="text-foreground">Create</span>
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
            <h1 className="text-2xl font-bold">Create Dashboard Template</h1>
            <p className="text-muted-foreground">
              Design a complete dashboard template with integrated menu structure
            </p>
          </div>
        </div>
      </div>

      {/* Designer - fills remaining space */}
      <div className="flex-1 overflow-hidden">
        <UnifiedDashboardDesigner
          widgetDefinitions={widgetDefinitions}
          onSave={handleSave}
        />
      </div>
    </div>
  );
}