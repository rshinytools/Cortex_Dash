// ABOUTME: Study detail page - redirects to the study dashboard
// ABOUTME: Serves as the main entry point for viewing a specific study

'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { Loader2 } from 'lucide-react';

export default function StudyPage() {
  const params = useParams();
  const router = useRouter();
  const studyId = params.studyId as string;

  useEffect(() => {
    // Redirect to the dashboard page
    router.replace(`/studies/${studyId}/dashboard`);
  }, [studyId, router]);

  // Show loading state while redirecting
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="flex flex-col items-center gap-2">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">Loading study...</p>
      </div>
    </div>
  );
}