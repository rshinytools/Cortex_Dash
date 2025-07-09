// ABOUTME: Study-specific dashboard page for regular users
// ABOUTME: Shows configured widgets and visualizations for the study

'use client';

import { useParams } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useQuery } from '@tanstack/react-query';
import { useState, useCallback, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Activity,
  AlertCircle,
  BarChart3,
  Calendar,
  Download,
  FileText,
  TrendingUp,
  Users,
  RefreshCw,
  Loader2,
  Edit,
  LayoutDashboard,
  ChevronRight,
  Menu as MenuIcon,
  Shield,
  FlaskConical,
  ClipboardList,
  UserCheck,
  MapPin,
  LineChart
} from 'lucide-react';
import { studiesApi } from '@/lib/api/studies';
import { format } from 'date-fns';
import { DashboardRenderer } from '@/components/widgets';
import { DashboardEditMode } from '@/components/widgets/dashboard-edit-mode';
import { useDashboardData } from '@/hooks/use-dashboard-data';
import { DashboardConfiguration, WidgetInstance } from '@/components/widgets/base-widget';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import { StudyStatus } from '@/types';

// Icon mapping function
const getMenuIcon = (iconName?: string) => {
  const iconMap: Record<string, any> = {
    'LayoutDashboard': LayoutDashboard,
    'Shield': Shield,
    'FlaskConical': FlaskConical,
    'Activity': Activity,
    'BarChart3': BarChart3,
    'ClipboardList': ClipboardList,
    'UserCheck': UserCheck,
    'MapPin': MapPin,
    'LineChart': LineChart,
    'Users': Users,
    'FileText': FileText,
  };
  
  const Icon = iconName ? iconMap[iconName] : LayoutDashboard;
  return Icon || LayoutDashboard;
};

// Mock widget data - this would come from the API
const mockWidgetData = {
  'enrolled-subjects': {
    value: 324,
    previousValue: 310,
    trend: 4.5,
    trendDirection: 'up',
  },
  'completion-rate': {
    value: 0.785,
    previousValue: 0.762,
    trend: 2.3,
    trendDirection: 'up',
  },
  'data-quality': {
    value: 0.942,
    previousValue: 0.938,
    trend: 0.4,
    trendDirection: 'up',
  },
  'days-since-start': {
    value: 142,
  },
  'enrollment-trend': [
    { week: 'W1', enrolled: 12, target: 15 },
    { week: 'W2', enrolled: 28, target: 30 },
    { week: 'W3', enrolled: 45, target: 45 },
    { week: 'W4', enrolled: 68, target: 60 },
    { week: 'W5', enrolled: 92, target: 75 },
    { week: 'W6', enrolled: 115, target: 90 },
    { week: 'W7', enrolled: 142, target: 105 },
    { week: 'W8', enrolled: 168, target: 120 },
  ],
  'safety-summary': {
    totalAEs: 45,
    totalSAEs: 3,
    totalSubjectsWithAE: 28,
    totalSubjects: 324,
    aesBySeverity: [
      { severity: 'Mild', count: 32, percentage: 71.1 },
      { severity: 'Moderate', count: 10, percentage: 22.2 },
      { severity: 'Severe', count: 3, percentage: 6.7 },
    ],
    trends: {
      aeRate: 8.6,
      saeRate: 0.9,
      rateChange: -0.3,
    },
  },
  'enrollment-map': [
    { country: 'US', enrolled: 124, label: 'United States' },
    { country: 'CA', enrolled: 45, label: 'Canada' },
    { country: 'GB', enrolled: 38, label: 'United Kingdom' },
    { country: 'DE', enrolled: 32, label: 'Germany' },
    { country: 'FR', enrolled: 28, label: 'France' },
    { country: 'ES', enrolled: 22, label: 'Spain' },
    { country: 'IT', enrolled: 18, label: 'Italy' },
    { country: 'AU', enrolled: 17, label: 'Australia' },
  ],
  'query-status': {
    totalQueries: 156,
    openQueries: 23,
    closedQueries: 133,
    avgResolutionTime: 4.2,
    queryRate: 0.48,
    trends: {
      newQueriesThisWeek: 8,
      closedQueriesThisWeek: 12,
      resolutionRate: 85.3,
    },
  },
};

export default function StudyDashboardPage() {
  const params = useParams();
  const { data: session } = useSession();
  const { toast } = useToast();
  const studyId = params.studyId as string;
  const [isEditMode, setIsEditMode] = useState(false);
  const [selectedMenuItem, setSelectedMenuItem] = useState<string>('overview');
  const [collapsedSidebar, setCollapsedSidebar] = useState(false);
  const [menuLayouts, setMenuLayouts] = useState<Record<string, any[]>>({});
  const [defaultLayout, setDefaultLayout] = useState<any[]>([]);

  const { data: study, isLoading: studyLoading, error: studyError } = useQuery({
    queryKey: ['study', studyId],
    queryFn: () => studiesApi.getStudy(studyId),
    retry: 1,
  });

  const { data: studyMenu, isLoading: menuLoading, error: menuError } = useQuery({
    queryKey: ['study-menu', studyId],
    queryFn: () => studiesApi.getStudyMenu(studyId),
    enabled: !!study,
    retry: 1,
  });

  const { data: dashboardConfig, isLoading: configLoading, error: configError } = useQuery({
    queryKey: ['study-dashboard-config', studyId],
    queryFn: () => studiesApi.getStudyDashboardConfig(studyId),
    enabled: !!study,
    retry: 1,
  });

  const {
    configuration,
    widgetData,
    widgetLoading,
    widgetErrors,
    isLoadingConfig,
    refreshAllWidgets,
    refreshWidget,
    updateConfiguration,
  } = useDashboardData({
    studyId,
    enableAutoRefresh: true,
    refreshInterval: 5 * 60 * 1000, // 5 minutes
  });

  // Update layouts when dashboard config loads
  useEffect(() => {
    if (dashboardConfig) {
      setMenuLayouts(dashboardConfig.menu_layouts || {});
      setDefaultLayout(dashboardConfig.default_layout || []);
      
      // Set initial selected menu item if not already set
      if (selectedMenuItem === 'overview' && studyMenu?.menu_structure?.items && studyMenu.menu_structure.items.length > 0) {
        const firstMenuItem = studyMenu.menu_structure.items.find(item => item.type === 'dashboard');
        if (firstMenuItem) {
          setSelectedMenuItem(firstMenuItem.id);
        }
      }
    }
  }, [dashboardConfig, studyMenu]);

  // Get current layout based on selected menu item
  const getCurrentLayout = () => {
    if (selectedMenuItem && menuLayouts[selectedMenuItem]) {
      return menuLayouts[selectedMenuItem];
    }
    return defaultLayout;
  };

  // Get current layout based on selected menu item
  const currentLayout = getCurrentLayout();
  
  // Transform layout data to include proper widget structure
  const transformedLayout = currentLayout.map((item: any) => {
    // If item already has proper structure, return it
    if (item.type && (item.x !== undefined || item.position)) {
      return {
        i: item.i || item.id || `widget-${Date.now()}-${Math.random()}`,
        type: item.type,
        x: item.x ?? item.position?.x ?? 0,
        y: item.y ?? item.position?.y ?? 0,
        w: item.w ?? item.position?.w ?? 4,
        h: item.h ?? item.position?.h ?? 2,
        config: item.config || item.instance_config || item.configuration || {},
        title: item.config?.title || item.title || '',
      };
    }
    // Handle legacy format
    return item;
  });
  
  // Use real widget data or fall back to mock
  const dashboardData = Object.keys(widgetData).length > 0 ? widgetData : mockWidgetData;

  // Check if user has permission to edit (study manager role)
  const canEdit = true; // Allow editing for demo purposes

  const handleSaveDashboard = useCallback(async (config: DashboardConfiguration) => {
    try {
      await updateConfiguration(config);
      setIsEditMode(false);
      toast({
        title: 'Dashboard saved',
        description: 'Your dashboard configuration has been saved successfully.',
      });
    } catch (error) {
      toast({
        title: 'Save failed',
        description: 'Failed to save dashboard configuration. Please try again.',
        variant: 'destructive',
      });
      throw error; // Re-throw to let the edit mode component handle it
    }
  }, [updateConfiguration, toast]);

  if (studyLoading || isLoadingConfig || menuLoading || configLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-200px)]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!study) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Study Not Found</h3>
              <p className="text-muted-foreground">
                The study you're looking for doesn't exist or you don't have access to it.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Check if study needs initialization
  if (study.status === StudyStatus.SETUP || study.status === StudyStatus.PLANNING || (!studyMenu && !menuError) || (!dashboardConfig && !configError)) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <Activity className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Study Not Initialized</h3>
              <p className="text-muted-foreground mb-4">
                This study needs to be configured before you can view the dashboard.
              </p>
              <Button 
                onClick={() => window.location.href = `/studies/${studyId}/initialize`}
              >
                Initialize Study
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-background">
      {/* Left Sidebar Menu */}
      <div className={cn(
        "border-r bg-slate-50 dark:bg-slate-900 transition-all duration-300 shadow-sm",
        collapsedSidebar ? "w-16" : "w-64"
      )}>
        <div className="p-4 border-b bg-white dark:bg-slate-800">
          <div className="flex items-center justify-between">
            <div className={cn(
              "transition-opacity",
              collapsedSidebar && "opacity-0"
            )}>
              <h2 className="font-semibold text-lg">Clinical Dashboard</h2>
              <p className="text-xs text-muted-foreground">{study?.code || 'Study'}</p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setCollapsedSidebar(!collapsedSidebar)}
            >
              <MenuIcon className="h-4 w-4" />
            </Button>
          </div>
        </div>
        
        <nav className="p-3 space-y-2">
          {!studyMenu?.menu_structure?.items && (
            <div className="text-center py-4">
              <Loader2 className="h-5 w-5 animate-spin mx-auto text-muted-foreground" />
            </div>
          )}
          {studyMenu?.menu_structure?.items?.map((item) => {
            if (item.type === 'group') {
              return (
                <div key={item.id} className="mb-6">
                  {!collapsedSidebar && (
                    <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider px-3 mb-3">
                      {item.label}
                    </h3>
                  )}
                  <div className="space-y-1">
                    {item.children?.map((child: any) => {
                      const Icon = getMenuIcon(child.icon);
                      return (
                        <Button
                          key={child.id}
                          variant={selectedMenuItem === child.id ? "secondary" : "ghost"}
                          size="sm"
                          className={cn(
                            "w-full justify-start h-10 px-3 font-normal",
                            selectedMenuItem === child.id && "bg-slate-200 dark:bg-slate-700 font-medium",
                            collapsedSidebar && "px-0 justify-center"
                          )}
                          onClick={() => setSelectedMenuItem(child.id)}
                        >
                          <Icon className={cn(
                            "h-4 w-4",
                            !collapsedSidebar && "mr-3"
                          )} />
                          {!collapsedSidebar && <span>{child.label}</span>}
                        </Button>
                      );
                    })}
                  </div>
                </div>
              );
            } else if (item.type === 'dashboard') {
              const Icon = getMenuIcon(item.icon);
              return (
                <Button
                  key={item.id}
                  variant={selectedMenuItem === item.id ? "secondary" : "ghost"}
                  size="sm"
                  className={cn(
                    "w-full justify-start h-10 px-3 font-normal mb-1",
                    selectedMenuItem === item.id && "bg-slate-200 dark:bg-slate-700 font-medium",
                    collapsedSidebar && "px-0 justify-center"
                  )}
                  onClick={() => setSelectedMenuItem(item.id)}
                >
                  <Icon className={cn(
                    "h-4 w-4",
                    !collapsedSidebar && "mr-3"
                  )} />
                  {!collapsedSidebar && <span>{item.label}</span>}
                </Button>
              );
            }
            return null;
          })}
        </nav>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Study Header */}
        <div className="border-b px-6 py-4 bg-white dark:bg-slate-800">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold">{study.name}</h1>
              <div className="flex items-center gap-4 mt-1">
                <Badge className="bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">{study.phase}</Badge>
                <Badge variant={study.status === 'active' ? 'default' : 'secondary'}>
                  {study.status}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Protocol: {study.protocol_number}
                </span>
              </div>
            </div>
            <div className="flex gap-2">
              {canEdit && !isEditMode && (
                <Button variant="outline" size="sm" onClick={() => setIsEditMode(true)}>
                  <Edit className="h-4 w-4 mr-2" />
                  Edit Dashboard
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={refreshAllWidgets}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </div>

        {/* Dashboard Content */}
        <div className="flex-1 overflow-auto p-6 bg-gray-50 dark:bg-gray-900">
          {isEditMode ? (
            <DashboardEditMode
              configuration={dashboardConfig as any}
              widgetData={dashboardData}
              widgetLoading={widgetLoading}
              widgetErrors={widgetErrors}
              onSave={handleSaveDashboard}
              onCancel={() => setIsEditMode(false)}
              onRefreshWidget={refreshWidget}
            />
          ) : (
            <DashboardRenderer
              key={selectedMenuItem}
              configuration={{
                id: dashboardConfig?.dashboard_code || 'default',
                name: dashboardConfig?.dashboard_name || 'Dashboard',
                description: '',
                layout: {
                  cols: 12,
                  rowHeight: 80,
                },
                widgets: transformedLayout.map((widget: any) => ({
                  id: widget.i || widget.id,
                  type: widget.type,
                  title: widget.config?.title || widget.title || '',
                  description: widget.config?.description || '',
                  configuration: widget.config || widget.configuration || {},
                  layout: {
                    x: widget.x || 0,
                    y: widget.y || 0,
                    w: widget.w || 4,
                    h: widget.h || 4,
                  }
                }))
              }}
              widgetData={dashboardData}
              widgetLoading={widgetLoading}
              widgetErrors={widgetErrors}
              viewMode={true}
            />
          )}
        </div>
      </div>
    </div>
  );
}