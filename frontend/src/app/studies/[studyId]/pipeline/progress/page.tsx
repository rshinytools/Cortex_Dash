// ABOUTME: Pipeline execution progress monitoring page
// ABOUTME: Shows real-time transformation progress for study data pipelines

'use client';

import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { TransformationProgress } from '@/components/study/transformation-progress';

export default function PipelineProgressPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const studyId = params.studyId as string;
  const executionId = searchParams.get('executionId') || undefined;

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push(`/studies/${studyId}/pipeline`)}
          className="mr-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Pipeline
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold">Pipeline Execution Progress</h1>
          <p className="text-muted-foreground mt-1">
            Monitor the real-time progress of your data transformation pipeline
          </p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto">
        <TransformationProgress
          studyId={studyId}
          executionId={executionId}
          onComplete={() => {
            // Optionally navigate back or show a success message
            router.push(`/studies/${studyId}/pipeline/history`);
          }}
        />
      </div>
    </div>
  );
}