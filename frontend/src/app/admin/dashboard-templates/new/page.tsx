// ABOUTME: New unified dashboard template designer page
// ABOUTME: Allows creating complete dashboard templates with integrated menus

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { UnifiedDashboardDesigner } from "@/components/admin/unified-dashboard-designer";
import { toast } from "@/components/ui/use-toast";
import { dashboardTemplatesApi, CreateUnifiedDashboardTemplateDto } from "@/lib/api/dashboard-templates";
import type { WidgetDefinition } from "@/types/widget";

// Mock widget definitions - in production these would come from the API
const mockWidgetDefinitions: WidgetDefinition[] = [
  {
    id: "1",
    name: "Enrollment Metric",
    description: "Shows current enrollment numbers",
    category: "enrollment",
    type: "metric",
    version: "1.0.0",
    componentPath: "widgets/EnrollmentMetric",
    defaultConfig: {
      metricConfig: {
        format: {
          type: "number",
          suffix: " subjects",
        },
        comparison: {
          enabled: true,
          type: "target",
        },
      },
    },
    size: {
      minWidth: 2,
      minHeight: 2,
      defaultWidth: 3,
      defaultHeight: 2,
    },
    dataRequirements: {
      sourceType: "dataset",
      requiredFields: ["subject_id", "enrollment_date"],
    },
    tags: ["enrollment", "metric"],
    isActive: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: "2",
    name: "Safety Events Chart",
    description: "Displays safety events over time",
    category: "safety",
    type: "chart",
    version: "1.0.0",
    componentPath: "widgets/SafetyEventsChart",
    defaultConfig: {
      chartConfig: {
        type: "line",
      },
    },
    size: {
      minWidth: 4,
      minHeight: 3,
      defaultWidth: 6,
      defaultHeight: 4,
    },
    dataRequirements: {
      sourceType: "dataset",
      requiredFields: ["event_date", "event_type", "severity"],
      optionalFields: ["subject_id", "site_id"],
    },
    tags: ["safety", "chart", "timeline"],
    isActive: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: "3",
    name: "Site Performance Table",
    description: "Shows performance metrics by site",
    category: "operations",
    type: "table",
    version: "1.0.0",
    componentPath: "widgets/SitePerformanceTable",
    defaultConfig: {
      tableConfig: {
        pagination: true,
        sortable: true,
        filterable: true,
      },
    },
    size: {
      minWidth: 6,
      minHeight: 4,
      defaultWidth: 8,
      defaultHeight: 6,
    },
    dataRequirements: {
      sourceType: "dataset",
      requiredFields: ["site_id", "site_name", "enrollment_count", "query_count"],
    },
    tags: ["operations", "table", "sites"],
    isActive: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: "4",
    name: "Study Progress",
    description: "Overall study completion percentage",
    category: "operations",
    type: "metric",
    version: "1.0.0",
    componentPath: "widgets/StudyProgress",
    defaultConfig: {
      metricConfig: {
        format: {
          type: "percentage",
          decimals: 1,
        },
      },
    },
    size: {
      minWidth: 2,
      minHeight: 2,
      defaultWidth: 3,
      defaultHeight: 2,
    },
    dataRequirements: {
      sourceType: "dataset",
      requiredFields: ["completed_visits", "total_visits"],
    },
    tags: ["operations", "metric", "progress"],
    isActive: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
];

export default function NewDashboardTemplatePage() {
  const router = useRouter();
  const [widgetDefinitions, setWidgetDefinitions] = useState<WidgetDefinition[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In production, fetch widget definitions from API
    // For now, use mock data
    setWidgetDefinitions(mockWidgetDefinitions);
    setLoading(false);
  }, []);

  const handleSave = async (template: CreateUnifiedDashboardTemplateDto) => {
    try {
      await dashboardTemplatesApi.create(template);
      toast({
        title: "Success",
        description: "Dashboard template created successfully",
      });
      router.push("/admin/dashboard-templates");
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create dashboard template",
        variant: "destructive",
      });
    }
  };

  const handlePreview = () => {
    toast({
      title: "Preview",
      description: "Preview functionality coming soon",
    });
  };

  const handleExport = () => {
    toast({
      title: "Export",
      description: "Export functionality coming soon",
    });
  };

  const handleImport = (file: File) => {
    toast({
      title: "Import",
      description: `Importing ${file.name}...`,
    });
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p>Loading widget definitions...</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b px-6 py-4">
        <div className="flex items-center gap-4">
          <Link href="/admin/dashboard-templates">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">Create Dashboard Template</h1>
            <p className="text-muted-foreground">
              Design a complete dashboard template with integrated menu structure
            </p>
          </div>
        </div>
      </div>

      {/* Designer */}
      <div className="flex-1 overflow-hidden">
        <UnifiedDashboardDesigner
          widgetDefinitions={widgetDefinitions}
          onSave={handleSave}
          onPreview={handlePreview}
          onExport={handleExport}
          onImport={handleImport}
        />
      </div>
    </div>
  );
}