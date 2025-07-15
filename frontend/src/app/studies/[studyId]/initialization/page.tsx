// ABOUTME: Study initialization progress page
// ABOUTME: Shows real-time progress of study initialization

'use client';

import React, { use } from 'react';
import { useRouter } from 'next/navigation';
import { useStudyInitialization } from '@/hooks/use-study-initialization';
import { InitializationProgress } from '@/components/study/initialization-progress';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ArrowLeft, CheckCircle2, Rocket } from 'lucide-react';
import Link from 'next/link';

interface InitializationPageProps {
  params: Promise<{
    studyId: string;
  }>;
}

export default function InitializationPage({ params }: InitializationPageProps) {
  const router = useRouter();
  const { studyId } = use(params);
  
  const {
    state,
    isConnected,
    retryInitialization,
    cancelInitialization,
  } = useStudyInitialization(studyId);

  const handleRetry = async () => {
    try {
      await retryInitialization();
    } catch (error) {
      console.error('Failed to retry:', error);
    }
  };

  const handleCancel = async () => {
    try {
      await cancelInitialization();
      router.push(`/studies/${studyId}`);
    } catch (error) {
      console.error('Failed to cancel:', error);
    }
  };

  const handleViewStudy = () => {
    router.push(`/studies/${studyId}`);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Study Initialization</h1>
          <p className="text-muted-foreground">
            Monitor the progress of your study setup
          </p>
        </div>
        <Link href="/studies">
          <Button variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Studies
          </Button>
        </Link>
      </div>

      <div className="grid gap-6">
        {/* Progress Card */}
        <InitializationProgress
          state={state}
          isConnected={isConnected}
          onRetry={handleRetry}
          onCancel={handleCancel}
        />

        {/* Success Card */}
        {state.status === 'completed' && (
          <Card className="border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-700">
                <CheckCircle2 className="h-6 w-6" />
                Initialization Complete!
              </CardTitle>
              <CardDescription className="text-green-600">
                Your study has been successfully initialized and is ready to use
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                <Button onClick={handleViewStudy} className="gap-2">
                  <Rocket className="h-4 w-4" />
                  View Study Dashboard
                </Button>
                <Link href={`/studies/${studyId}/data-mapping`}>
                  <Button variant="outline">
                    Configure Field Mappings
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Info Alert */}
        <Alert>
          <AlertDescription>
            This process may take several minutes depending on the size of your data files. 
            You can safely leave this page and return later - the initialization will continue in the background.
          </AlertDescription>
        </Alert>
      </div>
    </div>
  );
}