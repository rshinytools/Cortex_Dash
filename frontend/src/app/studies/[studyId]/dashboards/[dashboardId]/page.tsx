// ABOUTME: Dashboard view page for displaying a specific dashboard with its widgets
// ABOUTME: Fetches dashboard configuration and renders the DashboardViewer component

'use client';

import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { DashboardViewer, Dashboard } from '@/components/widgets/dashboard-viewer';
import { Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

// Fetch dashboard data
async function fetchDashboard(studyId: string, dashboardId: string): Promise<Dashboard> {
  const { data } = await apiClient.get(`/api/v1/studies/${studyId}/dashboards/${dashboardId}`);
  return data;
}

export default function DashboardPage() {
  const params = useParams();
  const router = useRouter();
  const studyId = params.studyId as string;
  const dashboardId = params.dashboardId as string;

  const {
    data: dashboard,
    isLoading,
    isError,
    error,
    refetch
  } = useQuery({
    queryKey: ['dashboard', studyId, dashboardId],
    queryFn: () => fetchDashboard(studyId, dashboardId),
    enabled: !!studyId && !!dashboardId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const handleEdit = (widgetId: string) => {
    // Navigate to widget edit page
    router.push(`/studies/${studyId}/dashboards/${dashboardId}/widgets/${widgetId}/edit`);
  };

  const handleDelete = async (widgetId: string) => {
    // TODO: Implement widget deletion with confirmation dialog
    console.log('Delete widget:', widgetId);
  };

  const handleLayoutChange = async (layouts: Record<string, any>) => {
    // TODO: Save layout changes to backend
    console.log('Layout changed:', layouts);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center max-w-md">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Error Loading Dashboard</h2>
          <p className="text-muted-foreground mb-4">
            {error?.message || 'An unexpected error occurred while loading the dashboard.'}
          </p>
          <div className="flex gap-2 justify-center">
            <Button onClick={() => refetch()}>
              Try Again
            </Button>
            <Button variant="outline" onClick={() => router.back()}>
              Go Back
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // No dashboard found
  if (!dashboard) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Dashboard Not Found</h2>
          <p className="text-muted-foreground mb-4">
            The requested dashboard could not be found.
          </p>
          <Button onClick={() => router.back()}>
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  // Render dashboard
  return (
    <div className="h-screen flex flex-col">
      <DashboardViewer
        dashboard={dashboard}
        studyId={studyId}
        readOnly={false}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onLayoutChange={handleLayoutChange}
        className="flex-1"
      />
    </div>
  );
}