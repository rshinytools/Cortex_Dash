// ABOUTME: Dashboard page for regular users (non-admin) - shows study selection
// ABOUTME: Users select a study to view its dashboard

'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/main-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Activity, 
  Calendar, 
  FlaskConical,
  ArrowRight
} from 'lucide-react';
import { StudyStatus } from '@/types';
import { studiesApi } from '@/lib/api/studies';
import { format } from 'date-fns';

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  const { data: studies, isLoading } = useQuery({
    queryKey: ['studies'],
    queryFn: studiesApi.getStudies,
    enabled: status === 'authenticated',
  });

  const activeStudies = studies?.filter(s => s.status === StudyStatus.ACTIVE) || [];

  if (status === 'loading' || isLoading) {
    return (
      <MainLayout>
        <div className="space-y-6">
          <Skeleton className="h-8 w-48" />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-48" />
            ))}
          </div>
        </div>
      </MainLayout>
    );
  }

  if (activeStudies.length === 0) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-[calc(100vh-200px)]">
          <Card className="max-w-md">
            <CardContent className="py-12">
              <div className="text-center">
                <FlaskConical className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Active Studies</h3>
                <p className="text-muted-foreground">
                  You don't have access to any active studies yet. Please contact your administrator.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </MainLayout>
    );
  }

  // If user has only one study, redirect directly to it
  if (activeStudies.length === 1) {
    router.push(`/studies/${activeStudies[0].id}/dashboard`);
    return null;
  }

  // Show study selection for users with multiple studies
  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">My Studies</h1>
          <p className="text-muted-foreground">
            Select a study to view its dashboard
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {activeStudies.map((study) => (
            <Card 
              key={study.id} 
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => router.push(`/studies/${study.id}/dashboard`)}
            >
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{study.name}</CardTitle>
                    <CardDescription>{study.code}</CardDescription>
                  </div>
                  <Badge>{study.phase}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span>Started {study.start_date ? format(new Date(study.start_date), 'MMM d, yyyy') : 'Not started'}</span>
                  </div>
                  {study.indication && (
                    <div className="flex items-center gap-2">
                      <Activity className="h-4 w-4 text-muted-foreground" />
                      <span>{study.indication}</span>
                    </div>
                  )}
                </div>
                <Button className="w-full mt-4" variant="outline">
                  View Dashboard
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </MainLayout>
  );
}