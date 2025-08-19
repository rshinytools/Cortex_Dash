// ABOUTME: Study Management Center - System admin interface for editing study configurations
// ABOUTME: Provides tabbed interface for study info, data source, mappings, and template management

'use client';

import { use, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { useQuery } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  ArrowLeft,
  Settings,
  Database,
  GitBranch,
  Layout,
  Shield,
  Loader2,
  AlertCircle
} from 'lucide-react';
import Link from 'next/link';
import { studiesApi } from '@/lib/api/studies';
import { useToast } from '@/hooks/use-toast';

// Import tab components (to be created)
import { StudyInfoTab } from './components/study-info-tab';
import { DataSourceTab } from './components/data-source-tab';
import { MappingsTab } from './components/mappings-tab';
import { TemplateTab } from './components/template-tab';

interface ManageStudyPageProps {
  params: Promise<{
    studyId: string;
  }>;
}

export default function ManageStudyPage({ params }: ManageStudyPageProps) {
  const router = useRouter();
  const { user } = useAuth();
  const { toast } = useToast();
  const { studyId } = use(params);
  const [activeTab, setActiveTab] = useState('info');

  // Check if user is system admin
  const isSystemAdmin = user?.is_superuser || user?.role === 'system_admin';

  // Redirect non-admins
  useEffect(() => {
    if (user && !isSystemAdmin) {
      toast({
        title: 'Access Denied',
        description: 'Only system administrators can access study management.',
        variant: 'destructive',
      });
      router.push(`/studies/${studyId}/dashboard`);
    }
  }, [user, isSystemAdmin, router, studyId, toast]);

  // Fetch study data
  const { 
    data: study, 
    isLoading, 
    error,
    refetch 
  } = useQuery({
    queryKey: ['study', studyId],
    queryFn: () => studiesApi.getStudy(studyId),
    enabled: !!studyId && isSystemAdmin,
  });

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-slate-950 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-6">
            <Skeleton className="h-8 w-64 mb-2" />
            <Skeleton className="h-4 w-96" />
          </div>
          <Card className="bg-white dark:bg-slate-900">
            <CardContent className="p-12">
              <div className="flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !study) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-slate-950 p-6">
        <div className="max-w-7xl mx-auto">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load study. Please try again or contact support.
            </AlertDescription>
          </Alert>
        </div>
      </div>
    );
  }

  // Access denied for non-admins (fallback)
  if (!isSystemAdmin) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-slate-950 p-6">
        <div className="max-w-7xl mx-auto">
          <Alert>
            <Shield className="h-4 w-4" />
            <AlertDescription>
              Only system administrators can access this page.
            </AlertDescription>
          </Alert>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-950">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href={`/studies/${studyId}/dashboard`}>
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Dashboard
                </Button>
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <Settings className="h-6 w-6" />
                  Study Management
                </h1>
                <p className="text-sm text-gray-600 dark:text-slate-400">
                  {study.name} • {study.protocol_number}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 dark:text-slate-500">
                System Admin Mode
              </span>
              <Shield className="h-4 w-4 text-yellow-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 h-auto p-1 bg-white dark:bg-slate-900">
            <TabsTrigger 
              value="info" 
              className="flex items-center gap-2 py-3 data-[state=active]:bg-blue-50 dark:data-[state=active]:bg-slate-800"
            >
              <Settings className="h-4 w-4" />
              <span>Study Info</span>
            </TabsTrigger>
            <TabsTrigger 
              value="data" 
              className="flex items-center gap-2 py-3 data-[state=active]:bg-blue-50 dark:data-[state=active]:bg-slate-800"
            >
              <Database className="h-4 w-4" />
              <span>Data Source</span>
            </TabsTrigger>
            <TabsTrigger 
              value="mappings" 
              className="flex items-center gap-2 py-3 data-[state=active]:bg-blue-50 dark:data-[state=active]:bg-slate-800"
            >
              <GitBranch className="h-4 w-4" />
              <span>Field Mappings</span>
            </TabsTrigger>
            <TabsTrigger 
              value="template" 
              className="flex items-center gap-2 py-3 data-[state=active]:bg-blue-50 dark:data-[state=active]:bg-slate-800"
            >
              <Layout className="h-4 w-4" />
              <span>Dashboard Template</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="info">
            <StudyInfoTab 
              study={study} 
              onUpdate={() => refetch()} 
            />
          </TabsContent>

          <TabsContent value="data">
            <DataSourceTab 
              study={study} 
              onUpdate={() => refetch()} 
            />
          </TabsContent>

          <TabsContent value="mappings">
            <MappingsTab 
              study={study} 
              onUpdate={() => refetch()} 
            />
          </TabsContent>

          <TabsContent value="template">
            <TemplateTab 
              study={study} 
              onUpdate={() => refetch()} 
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}