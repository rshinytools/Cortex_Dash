// ABOUTME: Edit dashboard template page
// ABOUTME: Allows editing existing dashboard templates with unified designer

"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, LayoutDashboard, Loader2 } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { UnifiedDashboardDesigner } from "@/components/admin/unified-dashboard-designer";
import { useToast } from "@/components/ui/use-toast";
import { motion } from "framer-motion";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { UserMenu } from "@/components/user-menu";
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
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    // Only load if we're in loading state and don't have data yet
    if (!loading || template || hasError) {
      return;
    }
    
    // Check sessionStorage to prevent duplicate loads
    const loadKey = `template-loading-${templateId}`;
    const isLoading = sessionStorage.getItem(loadKey);
    if (isLoading === 'true') {
      return;
    }
    
    // Mark as loading in sessionStorage
    sessionStorage.setItem(loadKey, 'true');
    
    // Fetch both template and widget definitions
    const loadData = async () => {
      try {
        const [templateData, widgets] = await Promise.all([
          dashboardTemplatesApi.get(templateId),
          widgetsApi.getLibrary({ is_active: true })
        ]);
        
        // Transform backend format to frontend format
        const menuItems = templateData.template_structure?.menu_structure?.items || [];
        const dashboardTemplates = templateData.template_structure?.dashboardTemplates || [];
        
        const transformedTemplate: any = {
          id: templateData.id,
          name: templateData.name,
          description: templateData.description,
          tags: templateData.tags || [],
          category: templateData.category,
          version: templateData.version || `${templateData.major_version}.${templateData.minor_version}.${templateData.patch_version}`,
          menuTemplate: {
            items: menuItems
          },
          dashboardTemplates: dashboardTemplates
        };
        
        // Debug logging disabled
        
        setTemplate(transformedTemplate);
        setWidgetDefinitions(widgets);
      } catch (error) {
        console.error('Failed to load data:', error);
        setHasError(true);
        toast({
          title: "Error",
          description: "Failed to load dashboard template",
          variant: "destructive",
        });
        router.push("/admin/dashboard-templates");
      } finally {
        setLoading(false);
        // Clear the loading flag from sessionStorage
        sessionStorage.removeItem(loadKey);
      }
    };

    loadData();
    
    // Cleanup function to clear sessionStorage on unmount
    return () => {
      sessionStorage.removeItem(loadKey);
    };
  }, [loading, template, hasError, templateId, toast, router]); // Include all dependencies

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
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="flex h-screen items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600 dark:text-indigo-400" />
            <p className="text-gray-600 dark:text-gray-400">Loading dashboard template...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!template) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="flex h-screen items-center justify-center">
          <Card className="border-0 shadow-lg bg-white dark:bg-gray-800 p-8">
            <p className="text-gray-600 dark:text-gray-400">Template not found</p>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header with breadcrumb */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-8 py-6 shadow-sm"
      >
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
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
        
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push('/admin/dashboard-templates')}
              className="mr-4 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-blue-600 dark:from-indigo-400 dark:to-blue-400 bg-clip-text text-transparent flex items-center gap-3">
                <LayoutDashboard className="h-7 w-7 text-indigo-600 dark:text-indigo-400" />
                Edit Dashboard Template
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Modify the dashboard template and menu structure
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <UserMenu />
          </div>
        </div>
      </motion.div>

      {/* Designer - fills remaining space */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="flex-1 overflow-hidden bg-gray-50 dark:bg-gray-900"
      >
        <UnifiedDashboardDesigner
          templateId={templateId}
          initialTemplate={template}
          widgetDefinitions={widgetDefinitions}
          onSave={handleSave}
        />
      </motion.div>
    </div>
  );
}