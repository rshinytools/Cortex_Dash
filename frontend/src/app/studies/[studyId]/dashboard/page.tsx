// ABOUTME: Study dashboard page - displays the clinical dashboard based on selected template
// ABOUTME: Uses the new dashboard template system with hierarchical navigation and dynamic widget loading

'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  AlertTriangle,
  RefreshCw,
  Settings,
  Loader2
} from 'lucide-react';
import { WidgetRenderer } from '@/components/widgets/WidgetRenderer';
import { DashboardNavigation } from '@/components/dashboard/DashboardNavigation';
import { studiesApi } from '@/lib/api/studies';
import { dashboardTemplatesApi } from '@/lib/api/dashboard-templates';
import { useState, useEffect, useMemo } from 'react';
import { useToast } from '@/hooks/use-toast';
import type { MenuItem } from '@/types/menu';
import { MenuItemType } from '@/types/menu';

export default function StudyDashboardPage() {
  const params = useParams();
  const studyId = params.studyId as string;
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedMenuId, setSelectedMenuId] = useState<string>('');
  const { toast } = useToast();

  // Fetch study details to get the selected template
  const { data: study, isLoading: isLoadingStudy } = useQuery({
    queryKey: ['study', studyId],
    queryFn: () => studiesApi.getStudy(studyId),
  });

  // Mock dashboard configuration with hierarchical menu structure
  const dashboardConfig = {
    templateId: 'safety-dashboard',
    menuItems: [
      {
        id: 'overview',
        label: 'Overview',
        type: MenuItemType.DASHBOARD_PAGE,
        order: 1,
        isVisible: true,
        isEnabled: true,
        widgets: [
          { id: 'w1', type: 'total_screened', x: 0, y: 0, w: 3, h: 2 },
          { id: 'w2', type: 'screen_failures', x: 3, y: 0, w: 3, h: 2 },
          { id: 'w3', type: 'total_aes', x: 6, y: 0, w: 3, h: 2 },
          { id: 'w4', type: 'saes', x: 9, y: 0, w: 3, h: 2 },
        ]
      },
      {
        id: 'divider-1',
        label: '',
        type: MenuItemType.DIVIDER,
        order: 2,
        isVisible: true,
        isEnabled: true,
      },
      {
        id: 'safety-group',
        label: 'Safety Monitoring',
        type: MenuItemType.GROUP,
        order: 3,
        isVisible: true,
        isEnabled: true,
        children: [
          {
            id: 'ae-overview',
            label: 'AE Overview',
            type: MenuItemType.DASHBOARD_PAGE,
            order: 1,
            isVisible: true,
            isEnabled: true,
            widgets: [
              { id: 'w5', type: 'total_aes', x: 0, y: 0, w: 6, h: 3 },
              { id: 'w6', type: 'ae_timeline', x: 6, y: 0, w: 6, h: 3 },
            ]
          },
          {
            id: 'sae-details',
            label: 'SAE Details',
            type: MenuItemType.DASHBOARD_PAGE,
            order: 2,
            isVisible: true,
            isEnabled: true,
            widgets: [
              { id: 'w7', type: 'saes', x: 0, y: 0, w: 12, h: 4 },
            ]
          },
        ]
      },
      {
        id: 'enrollment-group',
        label: 'Enrollment',
        type: MenuItemType.GROUP,
        order: 4,
        isVisible: true,
        isEnabled: true,
        children: [
          {
            id: 'screening',
            label: 'Screening',
            type: MenuItemType.DASHBOARD_PAGE,
            order: 1,
            isVisible: true,
            isEnabled: true,
            widgets: [
              { id: 'w8', type: 'total_screened', x: 0, y: 0, w: 6, h: 3 },
              { id: 'w9', type: 'screen_failures', x: 6, y: 0, w: 6, h: 3 },
            ]
          },
          {
            id: 'enrollment-trend',
            label: 'Enrollment Trend',
            type: MenuItemType.DASHBOARD_PAGE,
            order: 2,
            isVisible: true,
            isEnabled: true,
            widgets: [
              { id: 'w10', type: 'enrollment_trend', x: 0, y: 0, w: 12, h: 6 },
            ]
          },
        ]
      },
      {
        id: 'divider-2',
        label: '',
        type: MenuItemType.DIVIDER,
        order: 5,
        isVisible: true,
        isEnabled: true,
      },
      {
        id: 'external-resources',
        label: 'Resources',
        type: MenuItemType.GROUP,
        order: 6,
        isVisible: true,
        isEnabled: true,
        children: [
          {
            id: 'protocol',
            label: 'Study Protocol',
            type: MenuItemType.EXTERNAL,
            url: 'https://example.com/protocol',
            order: 1,
            isVisible: true,
            isEnabled: true,
          },
          {
            id: 'investigator-brochure',
            label: 'Investigator Brochure',
            type: MenuItemType.EXTERNAL,
            url: 'https://example.com/ib',
            order: 2,
            isVisible: true,
            isEnabled: true,
          },
        ]
      },
    ] as MenuItem[]
  };

  // Find all dashboard pages recursively
  const findDashboardPages = (items: MenuItem[]): { [key: string]: any } => {
    const pages: { [key: string]: any } = {};
    
    const traverse = (menuItems: MenuItem[]) => {
      for (const item of menuItems) {
        if (item.type === MenuItemType.DASHBOARD_PAGE && (item as any).widgets) {
          pages[item.id] = item;
        }
        if (item.children && item.children.length > 0) {
          traverse(item.children);
        }
      }
    };
    
    traverse(items);
    return pages;
  };

  const dashboardPages = useMemo(() => {
    return findDashboardPages(dashboardConfig.menuItems);
  }, []);

  // Set default menu when config loads - find first dashboard page
  useEffect(() => {
    if (!selectedMenuId && Object.keys(dashboardPages).length > 0) {
      setSelectedMenuId(Object.keys(dashboardPages)[0]);
    }
  }, [dashboardPages, selectedMenuId]);

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
    toast({
      title: "Dashboard refreshed",
      description: "All widgets have been updated with latest data.",
    });
  };

  const isLoading = isLoadingStudy;
  const selectedDashboard = dashboardPages[selectedMenuId];

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="space-y-6">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (!study) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Study not found or you don't have access to view this study.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {/* Sidebar Navigation */}
      <div className="w-64 border-r bg-muted/10 p-4">
        <div className="mb-4">
          <h2 className="text-lg font-semibold">{study.name}</h2>
          <p className="text-sm text-muted-foreground">Clinical Dashboard</p>
        </div>
        <DashboardNavigation
          items={dashboardConfig.menuItems}
          selectedItemId={selectedMenuId}
          onSelectItem={setSelectedMenuId}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="container mx-auto p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">
                {selectedDashboard?.label || 'Dashboard'}
              </h1>
              <p className="text-muted-foreground mt-1">
                Clinical trial metrics and insights
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              <Button
                variant="outline"
                size="sm"
              >
                <Settings className="h-4 w-4 mr-2" />
                Configure
              </Button>
            </div>
          </div>

          {/* Dashboard Content */}
          {selectedDashboard ? (
            <div className="grid grid-cols-12 gap-4">
              {selectedDashboard.widgets.map((widget: any) => (
                <div
                  key={widget.id}
                  className={`col-span-${widget.w} row-span-${widget.h}`}
                  style={{
                    gridColumn: `span ${widget.w}`,
                    minHeight: `${widget.h * 100}px`
                  }}
                >
                  <WidgetRenderer
                    key={`${widget.id}-${refreshKey}`}
                    instance={{
                      id: widget.id,
                      type: widget.type,
                      widgetDefinitionId: widget.type,
                      config: {
                        title: widget.type.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())
                      }
                    }}
                    mode="preview"
                    className="h-full"
                  />
                </div>
              ))}
            </div>
          ) : (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                {selectedMenuId 
                  ? "This menu item does not have a dashboard view. Select a Dashboard Page from the navigation."
                  : "No dashboard selected. Please select a page from the navigation menu."}
              </AlertDescription>
            </Alert>
          )}
        </div>
      </div>
    </div>
  );
}