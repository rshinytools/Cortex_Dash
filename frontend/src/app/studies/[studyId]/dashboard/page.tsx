// ABOUTME: Study dashboard page - displays the clinical dashboard based on selected template
// ABOUTME: Uses the dashboard template system with real data from the study's template

'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { 
  AlertTriangle,
  RefreshCw,
  Settings,
  Loader2,
  FileWarning,
  Home,
  BarChart3,
  FileText,
  Shield,
  Activity,
  Users,
  ChevronRight,
  Menu,
  X,
  Database,
  TrendingUp,
  AlertCircle,
  FileSearch
} from 'lucide-react';
import { WidgetRenderer } from '@/components/widgets/widget-renderer';
import { studiesApi } from '@/lib/api/studies';
import { dashboardTemplatesApi } from '@/lib/api/dashboard-templates';
import { useState, useEffect, useMemo } from 'react';
import { useToast } from '@/hooks/use-toast';
import { useTheme } from '@/hooks/use-theme';
import type { MenuItem } from '@/types/menu';
import { MenuItemType } from '@/types/menu';
import Link from 'next/link';
import { Sun, Moon, ChevronDown } from 'lucide-react';

export default function StudyDashboardPage() {
  const params = useParams();
  const studyId = params.studyId as string;
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedMenuId, setSelectedMenuId] = useState<string>('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const { toast } = useToast();
  const { theme, toggleTheme } = useTheme();

  // Fetch study details to get the selected template
  const { data: study, isLoading: isLoadingStudy, error: studyError } = useQuery({
    queryKey: ['study', studyId],
    queryFn: () => studiesApi.getStudy(studyId),
  });

  // Debug logging
  useEffect(() => {
    if (study) {
      console.log('Study loaded:', study.name, 'Template ID:', study.dashboard_template_id);
    }
  }, [study]);

  // Fetch the actual template structure
  const { data: template, isLoading: isLoadingTemplate, error: templateError } = useQuery({
    queryKey: ['dashboard-template', study?.dashboard_template_id],
    queryFn: () => dashboardTemplatesApi.get(study!.dashboard_template_id!),
    enabled: !!study?.dashboard_template_id,
  });

  // Debug template loading
  useEffect(() => {
    if (template) {
      console.log('Template loaded:', template.name, 'Structure:', template.template_structure);
    }
    if (templateError) {
      console.error('Template error:', templateError);
    }
  }, [template, templateError]);

  // Parse menu structure from template
  const dashboardConfig = useMemo(() => {
    if (!template?.template_structure) {
      return null;
    }

    // Extract menu structure from template
    const menuStructure = template.template_structure.menu_structure || 
                          template.template_structure.menu || 
                          { items: [] };
    
    // Extract dashboard templates/pages
    const dashboardTemplates = template.template_structure.dashboardTemplates || [];
    
    // Process menu items to extract widgets from nested dashboard structure
    const menuItems = (menuStructure.items || []).map((item: any) => {
      // Check if item has a dashboard with widgets
      if (item.dashboard && item.dashboard.widgets) {
        return {
          ...item,
          widgets: item.dashboard.widgets.map((w: any) => {
            // Extract widget info from nested structure
            const widgetDef = w.widgetInstance?.widgetDefinition;
            const config = typeof w.widgetInstance?.config === 'string' 
              ? JSON.parse(w.widgetInstance.config) 
              : w.widgetInstance?.config || {};
            
            return {
              id: w.widgetInstanceId || w.id,
              type: widgetDef?.code || 'metric-card',
              title: w.overrides?.title || widgetDef?.name || 'Widget',
              x: w.position?.x || 0,
              y: w.position?.y || 0,
              w: w.position?.width || 3,
              h: w.position?.height || 2,
              config: config
            };
          })
        };
      }
      return item;
    });
    
    // If menu items don't have widgets but dashboard templates exist, 
    // try to match them up by ID or create default menu structure
    if (menuItems.length === 0 && dashboardTemplates.length > 0) {
      // Create a simple menu structure from dashboard templates
      return {
        templateId: template.id,
        menuItems: dashboardTemplates.map((dt: any, index: number) => ({
          id: dt.id || `dashboard-${index}`,
          label: dt.name || dt.title || `Dashboard ${index + 1}`,
          type: MenuItemType.DASHBOARD_PAGE,
          order: index + 1,
          isVisible: true,
          isEnabled: true,
          widgets: (dt.widgets || []).map((w: any) => {
            // Extract widget info from nested structure
            const widgetDef = w.widgetInstance?.widgetDefinition;
            const config = typeof w.widgetInstance?.config === 'string' 
              ? JSON.parse(w.widgetInstance.config) 
              : w.widgetInstance?.config || {};
            
            return {
              id: w.widgetInstanceId || w.id,
              type: widgetDef?.code || 'metric-card',
              title: w.overrides?.title || widgetDef?.name || 'Widget',
              x: w.position?.x || 0,
              y: w.position?.y || 0,
              w: w.position?.width || 3,
              h: w.position?.height || 2,
              config: config
            };
          })
        }))
      };
    }

    return {
      templateId: template.id,
      menuItems: menuItems as MenuItem[]
    };
  }, [template]);

  // Find all dashboard pages recursively
  const findDashboardPages = (items: MenuItem[]): { [key: string]: any } => {
    const pages: { [key: string]: any } = {};
    
    const traverse = (menuItems: any[]) => {
      for (const item of menuItems) {
        let widgets = null;
        
        // Check if item has widgets directly
        if (item.widgets && Array.isArray(item.widgets)) {
          widgets = item.widgets;
        }
        // Check if item has dashboard with widgets
        else if (item.dashboard && item.dashboard.widgets) {
          // Process the widgets from dashboard structure
          widgets = item.dashboard.widgets.map((w: any) => {
            const widgetDef = w.widgetInstance?.widgetDefinition;
            const config = typeof w.widgetInstance?.config === 'string' 
              ? JSON.parse(w.widgetInstance.config) 
              : w.widgetInstance?.config || {};
            
            return {
              id: w.widgetInstanceId || w.id,
              type: widgetDef?.code || 'kpi_card', // Use code from widgetDefinition
              title: w.overrides?.title || widgetDef?.name || 'Widget',
              x: w.position?.x || 0,
              y: w.position?.y || 0,
              w: w.position?.width || 3,
              h: w.position?.height || 2,
              config: config
            };
          });
        }
        
        // If we found widgets, add to pages
        if (widgets) {
          pages[item.id] = {
            ...item,
            widgets: widgets
          };
        }
        
        // Recursively check children
        if (item.children && item.children.length > 0) {
          traverse(item.children);
        }
      }
    };
    
    traverse(items);
    return pages;
  };

  const dashboardPages = useMemo(() => {
    if (!dashboardConfig?.menuItems) return {};
    const pages = findDashboardPages(dashboardConfig.menuItems);
    console.log('Found dashboard pages:', pages);
    return pages;
  }, [dashboardConfig]);

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

  // Get menu icon based on label
  const getMenuIcon = (label: string) => {
    const lowerLabel = label.toLowerCase();
    if (lowerLabel.includes('home') || lowerLabel.includes('overview')) return <Home className="h-4 w-4" />;
    if (lowerLabel.includes('patient') || lowerLabel.includes('subject')) return <Users className="h-4 w-4" />;
    if (lowerLabel.includes('safety') || lowerLabel.includes('adverse')) return <Shield className="h-4 w-4" />;
    if (lowerLabel.includes('efficacy') || lowerLabel.includes('endpoint')) return <Activity className="h-4 w-4" />;
    if (lowerLabel.includes('query') || lowerLabel.includes('data')) return <FileText className="h-4 w-4" />;
    if (lowerLabel.includes('enrollment')) return <TrendingUp className="h-4 w-4" />;
    if (lowerLabel.includes('site')) return <Database className="h-4 w-4" />;
    if (lowerLabel.includes('issue') || lowerLabel.includes('finding')) return <AlertCircle className="h-4 w-4" />;
    if (lowerLabel.includes('analysis')) return <FileSearch className="h-4 w-4" />;
    return <BarChart3 className="h-4 w-4" />;
  };

  // Toggle group expansion
  const toggleGroup = (groupId: string) => {
    setExpandedGroups(prev => {
      const newSet = new Set(prev);
      if (newSet.has(groupId)) {
        newSet.delete(groupId);
      } else {
        newSet.add(groupId);
      }
      return newSet;
    });
  };

  // Render menu items recursively
  const renderMenuItem = (item: any, depth: number = 0) => {
    const hasChildren = item.children && item.children.length > 0;
    const isGroup = item.type === 'group' || item.type === MenuItemType.GROUP || (hasChildren && !item.dashboard);
    const isDashboard = item.type === MenuItemType.DASHBOARD_PAGE || 
                       item.type === 'dashboard' || 
                       item.type === 'dashboard_page' ||
                       (item.dashboard && item.dashboard.widgets) ||
                       (item.widgets && item.widgets.length > 0);
    const isExpanded = expandedGroups.has(item.id);
    
    if (isGroup && hasChildren) {
      // Render group with children
      return (
        <div key={item.id} className="mb-1">
          <button
            onClick={() => toggleGroup(item.id)}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all",
              "text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-800/50",
              depth > 0 && "ml-4"
            )}
          >
            {getMenuIcon(item.label || '')}
            <span className="font-medium flex-1 text-left">{item.label || 'Group'}</span>
            <ChevronDown className={cn(
              "h-4 w-4 transition-transform",
              isExpanded && "rotate-180"
            )} />
          </button>
          {isExpanded && (
            <div className="mt-1">
              {item.children.map((child: any) => renderMenuItem(child, depth + 1))}
            </div>
          )}
        </div>
      );
    }
    
    // Render dashboard page or regular menu item
    return (
      <button
        key={item.id}
        onClick={() => {
          if (isDashboard) {
            setSelectedMenuId(item.id);
          }
        }}
        className={cn(
          "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all mb-1",
          selectedMenuId === item.id
            ? "bg-blue-600/10 dark:bg-blue-600/20 text-blue-600 dark:text-blue-400 border-l-2 border-blue-600 dark:border-blue-400 pl-2.5"
            : "text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-800/50",
          depth > 0 && "ml-6"
        )}
      >
        {getMenuIcon(item.label || '')}
        <span className="font-medium">{item.label || 'Dashboard'}</span>
        {hasChildren && !isGroup && (
          <ChevronRight className="h-3 w-3 ml-auto" />
        )}
      </button>
    );
  };

  const isLoading = isLoadingStudy || isLoadingTemplate;
  const selectedDashboard = dashboardPages[selectedMenuId];
  console.log('Dashboard Debug:', { selectedMenuId, dashboardPages, selectedDashboard });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-slate-950 flex items-center justify-center">
        <div className="space-y-4 text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-blue-500" />
          <p className="text-gray-600 dark:text-slate-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (studyError || !study) {
    return (
      <div className="min-h-screen bg-slate-950 p-6">
        <Alert variant="destructive" className="max-w-2xl mx-auto">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Study not found or you don't have access to view this study.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Check if study is properly initialized
  if (study.status === 'DRAFT' || study.initialization_status !== 'completed') {
    return (
      <div className="min-h-screen bg-slate-950 p-6">
        <Card className="max-w-2xl mx-auto bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <FileWarning className="h-5 w-5 text-yellow-500" />
              Study Not Ready
            </CardTitle>
            <CardDescription className="text-slate-400">
              This study needs to be initialized before the dashboard can be displayed.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-500 mb-4">
              Current status: {study.initialization_status || 'Not initialized'}
            </p>
            {study.initialization_status === 'failed' ? (
              <Link href={`/initialization/${studyId}`}>
                <Button className="bg-blue-600 hover:bg-blue-700">
                  Retry Initialization
                </Button>
              </Link>
            ) : (
              <Link href="/studies">
                <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800">
                  Back to Studies
                </Button>
              </Link>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  // Check if template is loaded
  if (!template || !dashboardConfig) {
    return (
      <div className="min-h-screen bg-slate-950 p-6">
        <Alert className="max-w-2xl mx-auto bg-slate-900 border-slate-800">
          <AlertTriangle className="h-4 w-4 text-yellow-500" />
          <AlertDescription className="text-slate-400">
            No dashboard template configured for this study. Please contact your administrator.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Check if there are any dashboard pages
  if (Object.keys(dashboardPages).length === 0) {
    return (
      <div className="min-h-screen bg-slate-950 p-6">
        <Card className="max-w-2xl mx-auto bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white">Dashboard Configuration Needed</CardTitle>
            <CardDescription className="text-slate-400">
              The template for this study doesn't have any dashboard pages configured yet.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-500 mb-4">
              Template: {template.name}
            </p>
            <div className="flex gap-2">
              <Link href="/admin/dashboard-templates">
                <Button className="bg-blue-600 hover:bg-blue-700">
                  Configure Dashboard
                </Button>
              </Link>
              <Link href="/studies">
                <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800">
                  Back to Studies
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-950">
      {/* Sidebar */}
      <div className={cn(
        "fixed left-0 top-0 h-full bg-white dark:bg-slate-900 border-r border-gray-200 dark:border-slate-800 transition-all duration-300 z-40",
        sidebarOpen ? "w-64" : "w-0 overflow-hidden"
      )}>
        <div className="flex flex-col h-full">
          {/* Sidebar Header */}
          <div className="p-4 border-b border-gray-200 dark:border-slate-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <BarChart3 className="h-5 w-5 text-white" />
                </div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Clinical Dashboard</h2>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-800"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Menu Section Label */}
          <div className="px-4 py-3">
            <p className="text-xs font-semibold text-gray-500 dark:text-slate-500 uppercase tracking-wider">MENU</p>
          </div>

          {/* Menu Items */}
          <nav className="flex-1 overflow-y-auto px-3">
            {dashboardConfig?.menuItems?.map((item) => renderMenuItem(item))}
          </nav>


          {/* Sidebar Footer */}
          <div className="p-4 border-t border-gray-200 dark:border-slate-800">
            <div className="space-y-1">
              <p className="text-xs font-semibold text-gray-500 dark:text-slate-500">STUDY</p>
              <p className="text-sm text-gray-900 dark:text-white">{study?.name}</p>
              {study?.protocol_number && (
                <p className="text-xs text-gray-600 dark:text-slate-400">Protocol: {study.protocol_number}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className={cn(
        "transition-all duration-300",
        sidebarOpen ? "ml-64" : "ml-0"
      )}>
        {/* Top Header Bar */}
        <div className="sticky top-0 z-30 bg-white/95 dark:bg-slate-900/95 backdrop-blur border-b border-gray-200 dark:border-slate-800">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center gap-4">
              {!sidebarOpen && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSidebarOpen(true)}
                  className="text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-800"
                >
                  <Menu className="h-5 w-5" />
                </Button>
              )}
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  {selectedDashboard?.label || 'Dashboard'}
                </h1>
                <p className="text-sm text-gray-600 dark:text-slate-400">
                  EDC Data Extracted: 04APR2025
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleTheme}
                className="text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-800"
                aria-label="Toggle theme"
              >
                {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                className="border-gray-300 dark:border-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800 hover:text-gray-900 dark:hover:text-white"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              <Link href={`/studies/${studyId}/manage`}>
                <Button
                  variant="outline"
                  size="sm"
                  className="border-gray-300 dark:border-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800 hover:text-gray-900 dark:hover:text-white"
                >
                  <Settings className="h-4 w-4 mr-2" />
                  Manage Study
                </Button>
              </Link>
              <Link href="/studies">
                <Button
                  variant="outline"
                  size="sm"
                  className="border-gray-300 dark:border-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800 hover:text-gray-900 dark:hover:text-white"
                >
                  Exit Dashboard
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Dashboard Content */}
        <div className="p-6">
          {/* Dashboard Widgets */}
          {selectedDashboard ? (
            <div className="grid grid-cols-12 gap-4">
              {selectedDashboard.widgets && selectedDashboard.widgets.map((widget: any) => {
                console.log('Rendering widget:', widget);
                return (
                  <div
                    key={widget.id}
                    className={`col-span-${widget.w || 3}`}
                    style={{
                      gridColumn: `span ${widget.w || 3} / span ${widget.w || 3}`,
                    }}
                  >
                    <WidgetRenderer
                      instance={{
                        id: widget.id,
                        type: widget.type || 'kpi_card', // Ensure type is set
                        title: widget.title || widget.type || 'Widget',
                        description: widget.description || '',
                        config: { ...(widget.config || {}), dashboardId: selectedMenuId },
                        configuration: { ...(widget.config || {}), dashboardId: selectedMenuId },
                        x: widget.x || 0,
                        y: widget.y || 0,
                        w: widget.w || 3,
                        h: widget.h || 2,
                      }}
                      loading={false}
                      viewMode={true}
                    />
                  </div>
                );
              })}
              {(!selectedDashboard.widgets || selectedDashboard.widgets.length === 0) && (
                <div className="col-span-12">
                  <Alert className="bg-slate-900 border-slate-800">
                    <AlertDescription className="text-slate-400">
                      No widgets configured for this dashboard page.
                    </AlertDescription>
                  </Alert>
                </div>
              )}
            </div>
          ) : (
            <Alert className="bg-slate-900 border-slate-800">
              <AlertDescription className="text-slate-400">
                Loading dashboard widgets...
              </AlertDescription>
            </Alert>
          )}
        </div>
      </div>
    </div>
  );
}