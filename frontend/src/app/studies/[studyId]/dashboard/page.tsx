// ABOUTME: Study-specific dashboard page for regular users
// ABOUTME: Shows configured widgets and visualizations for the study

'use client';

import { useParams } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useQuery } from '@tanstack/react-query';
import { useState, useCallback } from 'react';
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
  Edit
} from 'lucide-react';
import { studiesApi } from '@/lib/api/studies';
import { format } from 'date-fns';
import { DashboardRenderer } from '@/components/widgets';
import { DashboardEditMode } from '@/components/widgets/dashboard-edit-mode';
import { useDashboardData } from '@/hooks/use-dashboard-data';
import { DashboardConfiguration, WidgetInstance } from '@/components/widgets/base-widget';
import { useToast } from '@/hooks/use-toast';

// Mock dashboard configuration - this would come from the API
const mockDashboardConfig: DashboardConfiguration = {
  id: 'default',
  name: 'Study Dashboard',
  description: 'Main dashboard for study monitoring',
  layout: {
    cols: 12,
    rowHeight: 80,
  },
  widgets: [
    {
      id: 'enrolled-subjects',
      type: 'metric-card',
      title: 'Enrolled Subjects',
      configuration: {
        format: 'number',
        decimals: 0,
        showTrend: true,
        targetValue: 500,
        targetLabel: 'Target',
      },
      layout: { x: 0, y: 0, w: 3, h: 2 },
    },
    {
      id: 'completion-rate',
      type: 'metric-card',
      title: 'Completion Rate',
      configuration: {
        format: 'percentage',
        decimals: 1,
        showTrend: true,
        trendIsGood: true,
      },
      layout: { x: 3, y: 0, w: 3, h: 2 },
    },
    {
      id: 'data-quality',
      type: 'metric-card',
      title: 'Data Quality',
      configuration: {
        format: 'percentage',
        decimals: 1,
        showTrend: true,
        trendIsGood: true,
        thresholds: { good: 90, warning: 80, critical: 70 },
      },
      layout: { x: 6, y: 0, w: 3, h: 2 },
    },
    {
      id: 'days-since-start',
      type: 'metric-card',
      title: 'Days Since Start',
      configuration: {
        format: 'number',
        decimals: 0,
      },
      layout: { x: 9, y: 0, w: 3, h: 2 },
    },
    {
      id: 'enrollment-trend',
      type: 'line-chart',
      title: 'Enrollment Trend',
      description: 'Weekly enrollment numbers',
      configuration: {
        xAxisField: 'week',
        yAxisFields: [
          { field: 'enrolled', label: 'Enrolled', color: '#3b82f6' },
          { field: 'target', label: 'Target', color: '#10b981', strokeDasharray: '5 5' },
        ],
        xAxisLabel: 'Week',
        yAxisLabel: 'Subjects',
        showLegend: true,
      },
      layout: { x: 0, y: 2, w: 6, h: 4 },
    },
    {
      id: 'safety-summary',
      type: 'safety-metrics',
      title: 'Safety Summary',
      configuration: {
        displayType: 'summary',
        showTrends: true,
      },
      layout: { x: 6, y: 2, w: 6, h: 4 },
    },
    {
      id: 'enrollment-map',
      type: 'enrollment-map',
      title: 'Geographic Distribution',
      configuration: {
        mapType: 'world',
        dataField: 'enrolled',
        locationField: 'country',
        showMarkers: true,
      },
      layout: { x: 0, y: 6, w: 8, h: 5 },
    },
    {
      id: 'query-status',
      type: 'query-metrics',
      title: 'Query Status',
      configuration: {
        displayType: 'summary',
        showAverageResolutionTime: true,
      },
      layout: { x: 8, y: 6, w: 4, h: 5 },
    },
  ],
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

  const { data: study, isLoading: studyLoading } = useQuery({
    queryKey: ['study', studyId],
    queryFn: () => studiesApi.getStudy(studyId),
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

  // Use mock data for now
  const dashboardConfig = configuration || mockDashboardConfig;
  const dashboardData = Object.keys(widgetData).length > 0 ? widgetData : mockWidgetData;

  // Check if user has permission to edit (study manager role)
  const canEdit = session?.user?.roles?.some(role => 
    role.name === 'study_manager' || role.name === 'admin'
  ) || true; // Allow editing for demo purposes

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

  if (studyLoading || isLoadingConfig) {
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

  return (
    <div className="container mx-auto py-6">
      {/* Study Header */}
      <div className="mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold">{study.name}</h1>
            <div className="flex items-center gap-4 mt-2">
              <Badge>{study.phase}</Badge>
              <Badge variant={study.status === 'active' ? 'default' : 'secondary'}>
                {study.status}
              </Badge>
              <span className="text-muted-foreground">
                Protocol: {study.protocol_number}
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            {canEdit && !isEditMode && (
              <Button variant="outline" onClick={() => setIsEditMode(true)}>
                <Edit className="h-4 w-4 mr-2" />
                Edit Dashboard
              </Button>
            )}
            <Button variant="outline" onClick={refreshAllWidgets}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export Report
            </Button>
          </div>
        </div>
      </div>

      {/* Dashboard */}
      {isEditMode ? (
        <DashboardEditMode
          configuration={dashboardConfig}
          widgetData={dashboardData}
          widgetLoading={widgetLoading}
          widgetErrors={widgetErrors}
          onSave={handleSaveDashboard}
          onCancel={() => setIsEditMode(false)}
          onRefreshWidget={refreshWidget}
        />
      ) : (
        <DashboardRenderer
          configuration={dashboardConfig}
          widgetData={dashboardData}
          widgetLoading={widgetLoading}
          widgetErrors={widgetErrors}
          viewMode={true}
        />
      )}
    </div>
  );
}