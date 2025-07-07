// ABOUTME: Admin dashboard - system_admin sees full overview, org_admin sees limited view
// ABOUTME: System admin gets system overview with metrics, org admin only gets user management

'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Users,
  Shield,
  Building2,
  FileText,
  Settings,
  Activity,
  ArrowRight,
  BarChart3,
  Calendar,
  FlaskConical,
  Plus,
  TrendingUp,
  Database,
  Server,
  AlertCircle,
  CheckCircle2,
  Package,
  Zap,
  Bell,
  Lock,
  GitBranch,
  LayoutDashboard,
  Menu,
  Palette
} from 'lucide-react';
import { UserRole } from '@/types';
import { apiClient } from '@/lib/api/client';
import { format } from 'date-fns';
import { UserMenu } from '@/components/user-menu';
import { MainLayout } from '@/components/layout/main-layout';

interface SystemMetrics {
  organizations: number;
  activeStudies: number;
  totalEnrollment: number;
  dataQualityScore: number;
  completionRate: number;
  organizationsTrend: number;
  studiesTrend: number;
  enrollmentTrend: number;
  qualityTrend: number;
}

interface ActivityItem {
  id: string;
  type: 'pipeline' | 'enrollment' | 'quality' | 'report';
  title: string;
  studyName: string;
  timestamp: string;
  status?: 'completed' | 'pending' | 'error';
}

interface Milestone {
  id: string;
  type: 'database_lock' | 'analysis' | 'report';
  title: string;
  studyName: string;
  date: string;
}

export default function AdminPage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  const isSystemAdmin = session?.user?.role === UserRole.SYSTEM_ADMIN;

  // Fetch organizations count
  const { data: organizationsData } = useQuery({
    queryKey: ['organizations'],
    queryFn: async () => {
      const response = await apiClient.get('/organizations/');
      return response.data;
    },
    enabled: status === 'authenticated' && isSystemAdmin,
  });

  // Fetch studies count
  const { data: studiesData } = useQuery({
    queryKey: ['studies'],
    queryFn: async () => {
      const response = await apiClient.get('/studies/');
      return response.data;
    },
    enabled: status === 'authenticated' && isSystemAdmin,
  });

  // Calculate metrics from real data
  const metrics: SystemMetrics = {
    organizations: organizationsData?.length || 0,
    activeStudies: studiesData?.filter((s: any) => s.status === 'active').length || 0,
    totalEnrollment: 2845, // TODO: Get from studies data
    dataQualityScore: 94.2, // TODO: Calculate from actual data
    completionRate: 78.5, // TODO: Calculate from actual data
    organizationsTrend: 1, // TODO: Calculate trend
    studiesTrend: 2, // TODO: Calculate trend
    enrollmentTrend: 180, // TODO: Calculate trend
    qualityTrend: 2.1, // TODO: Calculate trend
  };

  const metricsLoading = !organizationsData || !studiesData;

  // Fetch recent activity
  const { data: recentActivity } = useQuery({
    queryKey: ['recent-activity'],
    queryFn: async () => {
      // TODO: Replace with actual API call to activity logs
      return [
        {
          id: '1',
          type: 'pipeline',
          title: 'Data pipeline completed',
          studyName: 'Study ABC-123',
          timestamp: '2 hours ago',
          status: 'completed',
        },
        {
          id: '2',
          type: 'enrollment',
          title: 'New enrollment milestone',
          studyName: 'Study XYZ-789',
          timestamp: '5 hours ago',
          status: 'completed',
        },
        {
          id: '3',
          type: 'quality',
          title: 'Quality check pending',
          studyName: 'Study DEF-456',
          timestamp: '1 day ago',
          status: 'pending',
        },
      ] as ActivityItem[];
    },
    enabled: status === 'authenticated' && isSystemAdmin,
  });

  // Fetch upcoming milestones
  const { data: milestones } = useQuery({
    queryKey: ['upcoming-milestones'],
    queryFn: async () => {
      // TODO: Replace with actual API call
      return [
        {
          id: '1',
          type: 'database_lock',
          title: 'Database Lock',
          studyName: 'Study ABC-123',
          date: '2024-03-15',
        },
        {
          id: '2',
          type: 'analysis',
          title: 'Interim Analysis',
          studyName: 'Study XYZ-789',
          date: '2024-03-22',
        },
        {
          id: '3',
          type: 'report',
          title: 'Final Report Due',
          studyName: 'Study DEF-456',
          date: '2024-04-01',
        },
      ] as Milestone[];
    },
    enabled: status === 'authenticated' && isSystemAdmin,
  });

  // Session loading is handled by the layout AuthCheck component

  // Check if user has admin access - after all hooks and loading check
  const canAccessPage = session?.user?.role && 
    [UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN].includes(session.user.role as UserRole);

  if (!canAccessPage) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <Shield className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Access Denied</h3>
              <p className="text-muted-foreground">
                You don't have permission to access the admin panel.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Org Admin View - Limited to user management
  if (!isSystemAdmin) {
    return (
      <div className="container mx-auto py-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold">Admin Panel</h1>
            <p className="text-muted-foreground mt-1">
              Organization Administration
            </p>
          </div>
          <UserMenu />
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card 
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => router.push('/admin/users')}
          >
            <CardHeader>
              <Users className="h-10 w-10 text-primary mb-2" />
              <CardTitle>User Management</CardTitle>
              <CardDescription>
                Add, edit, and manage user accounts in your organization
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full" variant="outline">
                Manage Users
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>

          <Card 
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => router.push('/admin/roles')}
          >
            <CardHeader>
              <Shield className="h-10 w-10 text-primary mb-2" />
              <CardTitle>Roles & Permissions</CardTitle>
              <CardDescription>
                View available roles and their permissions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full" variant="outline">
                View Roles
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>

          <Card 
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => router.push('/admin/audit')}
          >
            <CardHeader>
              <FileText className="h-10 w-10 text-primary mb-2" />
              <CardTitle>Activity Logs</CardTitle>
              <CardDescription>
                View activity logs for your organization
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full" variant="outline">
                View Logs
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // System Admin View - Full system overview
  return (
    <div className="container mx-auto py-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Cortex Clinical Dashboard</h1>
            <p className="text-muted-foreground">
              Complete system administration and monitoring
            </p>
          </div>
          <div className="flex items-center gap-4">
            <Button onClick={() => router.push('/studies/new')}>
              <Plus className="h-4 w-4 mr-2" />
              New Study
            </Button>
            <UserMenu />
          </div>
        </div>

        {/* Metrics Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Organizations</CardTitle>
              <Building2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics?.organizations || 0}</div>
              <p className="text-xs text-muted-foreground">
                +{metrics?.organizationsTrend || 0} from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Studies</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics?.activeStudies || 0}</div>
              <p className="text-xs text-muted-foreground">
                +{metrics?.studiesTrend || 0} from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Enrollment</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics?.totalEnrollment?.toLocaleString() || 0}</div>
              <p className="text-xs text-muted-foreground">
                +{metrics?.enrollmentTrend || 0} this week
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Data Quality Score</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics?.dataQualityScore || 0}%</div>
              <p className="text-xs text-muted-foreground">
                +{metrics?.qualityTrend || 0}% from last check
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completion Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics?.completionRate || 0}%</div>
              <p className="text-xs text-muted-foreground">
                On track for targets
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recent Activity</CardTitle>
              <CardDescription>
                Latest updates from your studies
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentActivity?.map((activity) => (
                  <div key={activity.id} className="flex items-start gap-4">
                    <div className={`rounded-full p-2 ${
                      activity.type === 'pipeline' ? 'bg-primary/10' :
                      activity.type === 'enrollment' ? 'bg-green-500/10' :
                      activity.type === 'quality' ? 'bg-orange-500/10' :
                      'bg-blue-500/10'
                    }`}>
                      {activity.type === 'pipeline' && <Activity className="h-4 w-4 text-primary" />}
                      {activity.type === 'enrollment' && <Users className="h-4 w-4 text-green-500" />}
                      {activity.type === 'quality' && <AlertCircle className="h-4 w-4 text-orange-500" />}
                      {activity.type === 'report' && <FileText className="h-4 w-4 text-blue-500" />}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{activity.title}</p>
                      <p className="text-xs text-muted-foreground">{activity.studyName} - {activity.timestamp}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Upcoming Milestones */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Upcoming Milestones</CardTitle>
              <CardDescription>
                Important dates and deadlines
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {milestones?.map((milestone) => (
                  <div key={milestone.id} className="flex items-start gap-4">
                    <div className={`rounded-full p-2 ${
                      milestone.type === 'database_lock' ? 'bg-blue-500/10' :
                      milestone.type === 'analysis' ? 'bg-purple-500/10' :
                      'bg-red-500/10'
                    }`}>
                      {milestone.type === 'database_lock' && <Database className="h-4 w-4 text-blue-500" />}
                      {milestone.type === 'analysis' && <BarChart3 className="h-4 w-4 text-purple-500" />}
                      {milestone.type === 'report' && <FileText className="h-4 w-4 text-red-500" />}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{milestone.title}</p>
                      <p className="text-xs text-muted-foreground">{milestone.studyName}</p>
                      <p className="text-xs text-muted-foreground">{format(new Date(milestone.date), 'MMM d, yyyy')}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Admin Actions Grid */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Administration</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/organizations')}>
              <CardContent className="p-6">
                <Building2 className="h-8 w-8 text-primary mb-2" />
                <p className="font-semibold">Organizations</p>
                <p className="text-sm text-muted-foreground">Manage organizations</p>
              </CardContent>
            </Card>
            
            <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/studies')}>
              <CardContent className="p-6">
                <FlaskConical className="h-8 w-8 text-primary mb-2" />
                <p className="font-semibold">Studies</p>
                <p className="text-sm text-muted-foreground">Manage clinical studies</p>
              </CardContent>
            </Card>
            
            <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/admin/users')}>
              <CardContent className="p-6">
                <Users className="h-8 w-8 text-primary mb-2" />
                <p className="font-semibold">Users</p>
                <p className="text-sm text-muted-foreground">Manage all users</p>
              </CardContent>
            </Card>
            
            <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/admin/roles')}>
              <CardContent className="p-6">
                <Shield className="h-8 w-8 text-primary mb-2" />
                <p className="font-semibold">Roles</p>
                <p className="text-sm text-muted-foreground">View roles & permissions</p>
              </CardContent>
            </Card>
            
            <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/analytics/reports')}>
              <CardContent className="p-6">
                <BarChart3 className="h-8 w-8 text-primary mb-2" />
                <p className="font-semibold">Analytics</p>
                <p className="text-sm text-muted-foreground">Reports & visualizations</p>
              </CardContent>
            </Card>
            
            <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/admin/settings')}>
              <CardContent className="p-6">
                <Settings className="h-8 w-8 text-primary mb-2" />
                <p className="font-semibold">Settings</p>
                <p className="text-sm text-muted-foreground">System configuration</p>
              </CardContent>
            </Card>
            
            <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/admin/health')}>
              <CardContent className="p-6">
                <Server className="h-8 w-8 text-primary mb-2" />
                <p className="font-semibold">System Health</p>
                <p className="text-sm text-muted-foreground">Monitor performance</p>
              </CardContent>
            </Card>
            
            <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/admin/audit')}>
              <CardContent className="p-6">
                <Activity className="h-8 w-8 text-primary mb-2" />
                <p className="font-semibold">Audit Logs</p>
                <p className="text-sm text-muted-foreground">System activity logs</p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Dashboard Configuration */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Dashboard Configuration</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/admin/widgets')}>
              <CardContent className="p-6">
                <Palette className="h-8 w-8 text-primary mb-2" />
                <p className="font-semibold">Widget Library</p>
                <p className="text-sm text-muted-foreground">Manage dashboard widgets</p>
              </CardContent>
            </Card>
            
            <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/admin/dashboards')}>
              <CardContent className="p-6">
                <LayoutDashboard className="h-8 w-8 text-primary mb-2" />
                <p className="font-semibold">Dashboard Templates</p>
                <p className="text-sm text-muted-foreground">Create & manage templates</p>
              </CardContent>
            </Card>
            
            <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/admin/menus')}>
              <CardContent className="p-6">
                <Menu className="h-8 w-8 text-primary mb-2" />
                <p className="font-semibold">Menu Templates</p>
                <p className="text-sm text-muted-foreground">Configure navigation menus</p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* System Features */}
        <div>
          <h2 className="text-xl font-semibold mb-4">System Management</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/integrations')}>
              <CardContent className="p-6">
                <Package className="h-8 w-8 text-primary mb-2" />
                <p className="font-semibold">Integrations</p>
                <p className="text-sm text-muted-foreground">External connections</p>
              </CardContent>
            </Card>
            
            <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/notification-settings')}>
              <CardContent className="p-6">
                <Bell className="h-8 w-8 text-primary mb-2" />
                <p className="font-semibold">Notifications</p>
                <p className="text-sm text-muted-foreground">Alert configuration</p>
              </CardContent>
            </Card>
            
            <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/backup-recovery')}>
              <CardContent className="p-6">
                <Database className="h-8 w-8 text-primary mb-2" />
                <p className="font-semibold">Backup & Recovery</p>
                <p className="text-sm text-muted-foreground">Data protection</p>
              </CardContent>
            </Card>
            
            <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/regulatory-compliance')}>
              <CardContent className="p-6">
                <Lock className="h-8 w-8 text-primary mb-2" />
                <p className="font-semibold">Compliance</p>
                <p className="text-sm text-muted-foreground">Regulatory settings</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}